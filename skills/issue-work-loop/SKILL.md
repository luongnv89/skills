---
name: issue-work-loop
description: "Resolve one open GitHub issue with a Herdr implementer→reviewer fix loop until CLEAN (notes count). Use when independent review is required. Don't use for plain resolve without review, backlog automation, review-only of an existing PR, or merging."
license: MIT
compatibility: "Requires herdr, git, gh auth, plus separately installed skills issue-resolver and issue-pr-review, and herdr-agent-comms (in this catalog)."
effort: max
metadata:
  version: 1.1.4
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# /issue-work-loop N

Resolve one GitHub issue through a Herdr-pane **implementer → reviewer → fix** loop until the PR is **CLEAN**. You are the lightweight orchestrator: spawn, message, gate, hand off. You never merge.

## Contract

| Rule | Meaning |
|------|---------|
| One issue | Argument is a single GitHub issue number |
| Herdr panes | Spawn and talk via `herdr-agent-comms` — not Agent-tool subagents |
| Role split | Implementer writes; reviewer only reviews (`--review-only`) |
| Notes count | Every FINDING (fix **and** note) must be fixed |
| No merge | USER-MERGE only — leave PR open for the human |
| Fresh when fat | FRESHEN reviewer at ROUND start; implementer before each fix (≥ 50%) |
| Clean workspace | SWEEP worker panes + worktrees before handoff |

## Leading Words

- **ROUND** — one implement/fix pass + one review pass
- **FINDING** — any reviewer item, including notes and partials
- **CLEAN** — zero FINDINGS; tests/CI acceptable per reviewer report
- **FRESHEN** — clear session and restart that role with a compact handoff
- **SWEEP** — tear down worker panes, remove loop worktrees, return main repo to default branch
- **USER-MERGE** — final state: PR ready, workspace clean, human merges

## Invocation

| Invocation | What happens |
|------------|--------------|
| `/issue-work-loop <N>` | Resolve issue #N through the loop (max 5 ROUNDs) |
| `/issue-work-loop <N> --max-rounds K` | Cap ROUNDs at K (default 5, min 1) |
| `/issue-work-loop <N> --agent-cli <cmd>` | Override worker CLI (default: `claude`) |
| `/issue-work-loop <N> --no-cleanup` | Skip Phase 6 SWEEP (debug only — leaves panes/worktrees) |

## Prerequisites

On failure, print the matching error from `references/error-messages.md` and stop.

1. Git repo: `git rev-parse --git-dir`
2. `gh` installed and authenticated: `which gh && gh auth status`
3. GitHub remote: `git remote -v`
4. Herdr: `command -v herdr && herdr status` (server running; never bare `herdr` from a non-TTY shell)
5. Skills available: `issue-resolver`, `issue-pr-review`, `herdr-agent-comms` — confirm each skill's `SKILL.md` is loadable in this session (any install root on the agent skill list). `herdr-agent-comms` ships in this catalog; `issue-resolver` and `issue-pr-review` are installed separately and may come from another distribution. If any missing → `Missing required skill(s)` error.
6. Bundled files present (relative to this skill's directory):
   - `references/agent-prompts.md`
   - `references/context-gate.md`
   - `references/loop-protocol.md`
   - `references/cleanup.md`
   - `references/error-messages.md`
   - `references/output-format.md`

## Repo Sync Before Edits (mandatory)

This skill does not edit repo code itself, but workers do. Sync the orchestrator cwd first:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
dirty=0
if [ -n "$(git status --porcelain)" ]; then
  git stash push -u -m "pre-sync: ${branch}"
  dirty=1
fi
git fetch origin
if git pull --rebase origin "$branch"; then
  if [ "$dirty" -eq 1 ]; then
    git stash pop || {
      echo "✗ Stash pop failed — recover with: git stash list && git stash show -p stash@{0}"
      exit 1
    }
  fi
else
  # Never pop onto a half-finished rebase — leave the stash intact and stop.
  echo "✗ Rebase failed — your changes are safe in: git stash list"
  echo "  Resolve or 'git rebase --abort', then 'git stash pop' manually."
  exit 1
fi
```

If `origin` is missing or rebase conflicts, stop and ask the user — do not pop the stash.

## Configuration

Optional keys under `.gitissue.yml` (defaults if missing):

| Key | Default | Role |
|-----|---------|------|
| `work_loop.max_rounds` | `5` | Max ROUNDs before stop |
| `work_loop.agent_cli` | `"claude"` | Worker launcher (e.g. `claude`, `pi --thinking high`) |
| `work_loop.context_threshold` | `50` | FRESHEN when reported context % ≥ this |
| `work_loop.implementer_name` | `"impl-{N}"` | Herdr agent name for implementer |
| `work_loop.reviewer_name` | `"rev-{N}"` | Herdr agent name for reviewer |
| `work_loop.auto_cleanup` | `true` | Run SWEEP at end (panes + worktrees + default branch) |

CLI flags override config. `--no-cleanup` sets `auto_cleanup: false` (debug only — leaves panes/worktrees). Print `○ First run — using default config` when `.gitissue.yml` is absent (do not invent keys into the file).

---

## Workflow Overview

```
  ◆ Issue Work Loop — #{N}
  ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
  [1] Preflight     ✓ env, skills, herdr
  [2] Spawn impl    ✓ impl-{N}
  [3] Resolve       ✓ PR #{M} created
  [4] Spawn rev     ✓ rev-{N}
  [5] Loop          ● ROUND 1..K until CLEAN or max
  [6] SWEEP         ✓ panes closed, worktrees gone, on default branch
  [7] Handoff       ✓ USER-MERGE — clean workspace, PR ready
```

Full send/wait mechanics: load `herdr-agent-comms` and follow its phases. Full ROUND state machine: `references/loop-protocol.md`. Prompts: `references/agent-prompts.md`. Context gate: `references/context-gate.md`. Cleanup: `references/cleanup.md`.

---

## Phase 1 — Preflight

1. Run Prerequisites above.
2. Parse `{issue_number}` (required positive integer). Parse optional `--max-rounds`, `--agent-cli`, and `--no-cleanup`. Presence of `--no-cleanup` sets `work_loop.auto_cleanup = false` for this run (skips Phase 6 SWEEP).
3. Confirm issue exists and is open:

   ```bash
   gh issue view {N} --json number,title,state,url
   ```

   Closed → stop with the closed-issue error. Missing → not-found error.
4. **Linked open PR precheck** (before any spawn) — see `references/loop-protocol.md` → *PR detection*. If one or more open PRs already link to `#{N}`:
   - **One PR** → stop and ask: review-only loop on that PR (skip Phase 3 resolve; spawn reviewer + fix loop only), or abort. Do not silently re-resolve.
   - **Multiple PRs** → stop with the ambiguous-PR error; do not spawn implementer.
5. Resolve `project_dir` (repo root) and Herdr root context (`HERDR_PANE_ID` / `HERDR_TAB_ID` / `HERDR_WORKSPACE_ID`, or `herdr pane current --current`).
6. Emit Step Completion Report for preflight (see `references/output-format.md`).

**Done when:** issue is open, PR graph is unambiguous (or user chose review-only on one PR), Herdr root resolved, skills present.

## Phase 2 — Spawn Implementer

Using `herdr-agent-comms` Phases 1–2:

1. Split a sub-agent pane named `{implementer_name}` (default `impl-{N}`) into the root tab grid.
2. Launch `{agent_cli}` in that pane (`--no-focus`).
3. Concurrent readiness wait (`wait_for_idle.py --ready`). Abort on blocked/timeout.

Do **not** put the long task on the launch argv — boot first, then Phase 3 send.

**Done when:** implementer pane idle/ready with stable name + `pane_id`.

## Phase 3 — Resolve (Implementer ROUND 0)

1. Context gate on implementer (`references/context-gate.md`) — usually fresh, so pass.
2. Send the **Implementer — initial** prompt from `references/agent-prompts.md` via herdr Phase 4 (baseline + completion marker + preflight + `pane run`).
3. Wait and read (herdr Phase 5). Parse structured report fields: `status`, `pr_number`, `pr_url`, `branch_name`, `head_sha`.
4. Validate PR:

   ```bash
   gh pr view {pr_number} --json number,url,state,headRefName,commits
   ```

   Prefer the PR that closes/links `#{N}` if the implementer omitted the number.

**Gates:**
- `status: success` + open PR → continue
- `status: already_resolved` → branch on open PRs linking `#{N}` per `references/loop-protocol.md` → *Already resolved* (authoritative): **zero** → outcome `ALREADY_RESOLVED`, hand off, no reviewer; **exactly one** → run **one** review ROUND only (report the verdict; no multi-round fix loop); **multiple** → stop with the ambiguous-PR error
- failure / no PR / multiple ambiguous PRs → stop with error (do not invent a PR)

**Done when:** one open PR number is known and recorded as `{pr_number}`.

## Phase 4 — Spawn Reviewer

Same grid pattern as Phase 2 with name `{reviewer_name}` (default `rev-{N}`).

**Done when:** reviewer pane idle/ready.

## Phase 5 — Review / Fix Loop

Initialize `round = 1`. While `round ≤ max_rounds`:

### 5a — Context gate (reviewer, start of every ROUND)

Run the context probe in `references/context-gate.md` on the **reviewer** at the start of every ROUND, including ROUND 1. If ≥ threshold or fallback says restart → **FRESHEN** that role (close worker pane, re-spawn, compact handoff only — issue #, PR #, branch, head SHA, current FINDINGS). Never paste full prior transcript.

The implementer is gated separately in 5c, immediately before **every** fix dispatch — including the first fix after the Phase 3 resolve, when the pane is still fat with resolve context.

### 5b — Review

1. Send **Reviewer — review** prompt (`--review-only` on `/issue-pr-review {pr_number}`).
2. Wait/read. Require an explicit line:
   - `VERDICT: CLEAN` or
   - `VERDICT: FINDINGS`
3. Normalize the verdict (strict):
   - Notes are FINDINGS — no soft-pass override. Soft-pass-with-notes → FINDINGS.
   - If `VERDICT: CLEAN` but any note/fix list items exist → treat as **FINDINGS** (do not re-prompt).
   - If both CLEAN and FINDINGS lines appear → prefer **FINDINGS**.
   - Missing VERDICT → one VERDICT-only re-prompt; still missing → fail ROUND.
4. If FINDINGS, extract the numbered list (fix **and** note).

`round` counts completed REVIEWs (CLEAN or FINDINGS). Fix work belongs to the ROUND that produced FINDINGS; the next review after a fix is the next `round` value.

### 5c — Exit or fix

| Reviewer verdict | Action |
|------------------|--------|
| CLEAN | Exit loop → Phase 6 SWEEP |
| FINDINGS and `round < max_rounds` | **Context-gate the implementer first** (every fix, first one included — see below), then send **Implementer — fix** prompt with the FINDINGS list; wait for push + new `head_sha`; then `round += 1` and go to 5a for the next review |
| FINDINGS and `round == max_rounds` | Exit loop → Phase 6 SWEEP; PR stays open for human decision |

**Implementer gate before every fix:** run the `references/context-gate.md` probe on the implementer pane before each fix dispatch. On the **first** fix the pane still carries the whole Phase 3 resolve, so the UNKNOWN fallback is *FRESHEN before the first fix* — never reuse it unheard. Gating here (not at ROUND start) also avoids freshening the implementer right before a CLEAN exit.

Implementer fix rounds **must not** re-run full `/issue-resolver` or open a second PR — only fix on the existing branch and push.

Blocked agent (trust dialog) → surface to user; do not type into the dialog.

**Done when:** CLEAN, or max rounds exhausted, or unrecoverable failure — then always Phase 6 (unless `--no-cleanup`).

## Phase 6 — SWEEP (clean workspace)

Mandatory when `work_loop.auto_cleanup` is true (default). Full procedure: `references/cleanup.md`.

1. **Snapshot handoff facts** first: `pr_number`, `pr_url`, `branch_name`, `head_sha`, verdict, FINDINGS, spawned pane ids.
2. **Close worker panes** this run spawned (`impl-*`, `rev-*` for `{N}`). Never close the root pane / `$HERDR_PANE_ID`. No confirmation prompt — SWEEP is automatic.
3. **Remove loop worktrees** for the PR branch (sibling `*-worktrees/*`, `wt-{N}`, or any non-primary worktree on `{branch_name}`). Never `git worktree remove` the primary repo root. Never delete `origin/{branch}` while the PR is open.
4. **Reset main repo:** checkout default branch, `fetch` + `pull --rebase`, leave working tree clean (stash residual worker dirt; never `reset --hard` user work without stashing).
5. Emit the SWEEP Step Completion Report from `references/cleanup.md` / `references/output-format.md`.

**Done when (checkable):**

```bash
# Fallback must sit outside the pipeline — sed exits 0 on empty input,
# so `... | sed ... || echo main` would never yield main.
default_branch="$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##')"
[ -n "$default_branch" ] || default_branch=main

test -z "$(git status --porcelain)"
test "$(git rev-parse --abbrev-ref HEAD)" = "$default_branch"
# worker pane ids from this run no longer appear in: herdr agent list
# no non-primary worktree still checks out {pr_branch}
```

If any sub-step fails, mark SWEEP `PARTIAL`, print recovery from `references/error-messages.md`, and continue to Phase 7 so the user still gets the PR URL.

## Phase 7 — Handoff (USER-MERGE)

Never run `gh pr merge`. Print the final summary from `references/output-format.md` (includes cleanup status).

The human should only need to open the PR and merge — local workspace is already clean.

```
  ✓ Issue #{N} ready for human merge
    PR: {pr_url}
    Rounds: {r}
    Verdict: CLEAN | MAX_ROUNDS | FAILED
    Workspace: clean on {default_branch}
```

---

## Failure Handling

| Situation | Response |
|-----------|----------|
| Implementer fails to open PR | Stop; report failure_reason; no reviewer spawn |
| Reviewer output missing VERDICT | One re-prompt for VERDICT only; still missing → fail ROUND |
| Multiple PRs for issue | Stop; list URLs; ask user which PR |
| Worker blocked | Print Worker blocked error; poll status every 30s up to 15m or until user says `resume`/`abort`; never send new tasks while blocked |
| Max rounds | Report remaining FINDINGS; PR stays open |
| Context UNKNOWN | Apply fallback in `references/context-gate.md` (not silent ignore) |
| Already resolved | See `references/loop-protocol.md` — no optional branch |

## What You Must Not Do

- Merge the PR or enable auto-merge
- Use Agent-tool subagents instead of Herdr panes for implementer/reviewer
- Let the reviewer fix code or commit
- Soft-pass notes as CLEAN
- Re-run full issue-resolver on fix rounds
- Close the root orchestrator pane when tearing down workers
- Force-push or delete the remote PR branch during SWEEP
- Leave worker panes or loop worktrees behind when `auto_cleanup` is true

## Step Completion Reports

After each phase and each ROUND, emit a report in this shape:

```
◆ {Phase or ROUND name}
··································································
  {Check}:            √ pass | × fail — {reason}
  Criteria:           √ N/M met
  Result:             PASS | FAIL | PARTIAL
```

## Additional Resources

- `references/loop-protocol.md` — ROUND state machine, PR detection, parse rules
- `references/agent-prompts.md` — implementer/reviewer/context prompts
- `references/context-gate.md` — 50% gate, FRESHEN, UNKNOWN fallback
- `references/cleanup.md` — SWEEP: panes, worktrees, default-branch reset
- `references/output-format.md` — preview, per-round, final summary templates
- `references/error-messages.md` — exact error blocks
- Sibling skills: `herdr-agent-comms`, `issue-resolver`, `issue-pr-review`
- Adjacent (do not use here): `auto-pilot` (multi-issue + merge), bare `issue-pr-review` (single PR without implementer loop)
