# Loop Protocol — /issue-work-loop

State machine and parse rules for the implementer/reviewer ROUND loop. SKILL.md holds the phase spine; this file is the detail.

## State machine

```
PREFLIGHT
  → SPAWN_IMPL
  → RESOLVE          (implementer initial; ROUND 0 conceptually)
  → SPAWN_REV
  → LOOP:
       CONTEXT_GATE (reviewer)          ← start of every ROUND, ROUND 1 included
       REVIEW
       if CLEAN → SWEEP
       if FINDINGS and rounds left → CONTEXT_GATE (implementer) → FIX → LOOP
       if FINDINGS and no rounds left → SWEEP (MAX_ROUNDS)
  → SWEEP            (panes + worktrees + default branch; default on)
  → HANDOFF (USER-MERGE)
```

The two context gates sit at different points and are **not** interchangeable (see `references/context-gate.md`):

- **Reviewer** — gated at ROUND start, before every REVIEW, ROUND 1 included.
- **Implementer** — gated immediately before **each** fix dispatch, after the FINDINGS verdict — not at ROUND start. The first fix is included (the pane still carries the whole Phase 3 resolve). Gating on the fix edge also avoids freshening the implementer right before a CLEAN exit.

Terminal outcomes: `CLEAN` | `MAX_ROUNDS` | `FAILED` | `ALREADY_RESOLVED`

SWEEP is mandatory before HANDOFF when `work_loop.auto_cleanup` is true (default). Full steps in `references/cleanup.md`.

## ROUND counter

- `round` starts at **1** for the first review after the PR exists.
- Initial resolve is **not** counted as a review ROUND (it is Phase 3).
- Each full REVIEW (+ optional FIX that follows FINDINGS) consumes one ROUND when FINDINGS are returned and a fix is requested; a CLEAN review on ROUND `r` ends with `rounds_used = r`.
- Default `max_rounds = 5`. CLI `--max-rounds` and config `work_loop.max_rounds` override.

## PR detection (after implementer)

1. Prefer structured fields from the implementer report (`pr_number`, `pr_url`).
2. Validate with:

   ```bash
   gh pr view {pr_number} --json number,url,state,title,body,headRefName,commits
   ```

3. If implementer omitted the number, search:

   ```bash
   gh pr list --state open --search "{issue_number}" --json number,title,url,body,headRefName
   ```

   Keep PRs whose title/body match (case-insensitive) any of:
   - `(closes|fixes|resolves|closed|fixed|resolved)\s+#?{N}\b`
   - `#\s?{N}\b`

   When the implementer reported `branch_name`, **prefer** the PR whose `headRefName` equals that branch among matches.

4. **Zero matches** → FAILED (implementer did not open a PR).
5. **One match** → use it.
6. **Multiple matches** → stop; list them; do not pick silently.

The same match rules apply to Phase 1's linked-open-PR precheck (before spawn).

Record `branch_name` from `headRefName` and `head_sha` from the latest commit when the implementer did not supply them.

## CLEAN definition (strict)

CLEAN only when **all** hold:

1. Reviewer ends with `VERDICT: CLEAN`
2. Numbered FINDINGS list is empty / absent
3. Reviewer did not list remaining note-level items as open work

If the underlying `/issue-pr-review --review-only` report says soft-pass with notes, the orchestrator **overrides** to FINDINGS: extract the notes into the FINDINGS list and send a fix ROUND. Notes count.

Contradiction rules (no re-prompt needed):
- `VERDICT: CLEAN` + any list items → FINDINGS
- both `VERDICT: CLEAN` and `VERDICT: FINDINGS` present → FINDINGS

Do not invent CLEAN when the VERDICT line is missing.

## FINDINGS extraction

Prefer the numbered list under `VERDICT: FINDINGS`. Normalize each line to:

```
{i}. [severity:fix|note] [dimension] description (area)
```

If severity is missing, default:

- words like crash, security, wrong, fail, broken → `fix`
- otherwise → `note` (still actionable)

If VERDICT is FINDINGS but the list is empty, re-prompt once for the list; still empty → treat as one synthetic FINDING: `Reviewer reported FINDINGS without details — re-review after implementer asks for clarification` and fail the ROUND if a second empty list appears.

## Implementer fix success

Require:

- `status: success`
- `head_sha` different from pre-fix SHA **or** explicit proof findings were non-code (e.g. PR body `Closes #N` only) with `gh pr view` confirming the body change
- `tests_passed: true` when the project has a test command the implementer ran; if no tests exist, `tests_passed: true` with `tests_run: none` is acceptable only when the implementer states no test harness

On fix failure: one automatic retry of the same FINDINGS on a FRESHEN'd implementer if context was high; otherwise stop with FAILED and remaining FINDINGS.

## Herdr send/wait contract

Every task (probe, resolve, review, fix, re-prompt):

1. Capture baseline (`herdr pane read … --source recent-unwrapped`)
2. Mint a fresh completion marker
3. `preflight_send.py` immediately before `pane run`
4. `wait_for_idle.py` with baseline + marker
5. Read reply delta only — do not dump full scrollback into orchestrator context

Blocked status → surface to user; never send the next task into a trust dialog.

## Autonomy

Workers run autonomously. The orchestrator only:

- asks the human on multiple-PR ambiguity
- surfaces blocked dialogs
- runs SWEEP automatically (no teardown confirmation)
- hands off merge

No mid-loop "approve this fix plan" prompts.

## Max rounds handoff

When FINDINGS remain after `max_rounds`:

- Outcome: `MAX_ROUNDS`
- PR stays open
- Print remaining FINDINGS verbatim
- Still run SWEEP (clean local workspace)
- Still USER-MERGE (human may merge, continue manually, or close)

## SWEEP (end of every successful path to handoff)

Order: snapshot facts → close worker panes → remove loop worktrees → checkout default branch + clean tree → report. Never delete the remote PR branch. Never close root. See `references/cleanup.md`.

## Already resolved

If implementer returns `already_resolved` (no optional branch):

| Open PRs linking `#{N}` | Action |
|-------------------------|--------|
| Zero | Outcome `ALREADY_RESOLVED`; hand off; no reviewer |
| Exactly one | Run **one** review ROUND only (report CLEAN/FINDINGS). Do **not** enter the multi-round fix loop unless the user re-invokes the skill on that issue/PR |
| Multiple | Stop with ambiguous-PR error |

## Pre-existing open PR (preflight)

Checked in Phase 1 before spawn:

| Open PRs linking `#{N}` | Action |
|-------------------------|--------|
| Zero | Proceed with full resolve → review loop |
| Exactly one | Ask user: (a) review-only + fix loop on that PR (skip implementer resolve), or (b) abort. Never silently re-resolve |
| Multiple | Stop with ambiguous-PR error; do not spawn |
