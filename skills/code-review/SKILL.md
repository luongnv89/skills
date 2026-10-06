---
name: code-review
description: "Review or improve code — one skill, four modes: bug/security review (default), performance, clean-code audit, slop cleanup. Pass mode:review|perf|clean|cleanup or infer. Don't use for writing features or generating tests (use test-coverage)."
license: MIT
effort: high
metadata:
  version: 2.2.1
  author: "Luong NGUYEN <luongnv89@gmail.com>"
  architecture: "router (4 modes, each a self-contained workflow in references/)"
---

# Code Review

One skill for reviewing and improving code quality. Pick a **mode** by intent (or pass an explicit
`mode:` parameter); each mode is a full, self-contained workflow in `references/`. Load only the
mode you need — this protects the agent's context budget.

## Modes

| Mode | Use when the user wants to... | Reads / writes | Output | Workflow |
|---|---|---|---|---|
| **review** (default) | find bugs, security holes, quality issues in a diff/PR | read-only | prioritized findings report | `references/review-mode.md` |
| **perf** | make code faster — bottlenecks, leaks, algorithmic waste | read-only | performance findings report | `references/perf-mode.md` |
| **clean** | audit readability/standards vs the bbv Clean Code cheat sheet | read-only | `CLEAN_CODE_AUDIT.md` | `references/clean-mode.md` |
| **cleanup** | actually refactor out AI slop, dead code, duplication, cruft | **WRITES CODE** | modified source files | `references/cleanup-mode.md` |

## Selecting the mode

1. **Explicit wins.** If the request carries `mode:review|perf|clean|cleanup` (or `--mode <name>`), use it.
2. **Otherwise infer** from the request. The longest matching phrase wins: a phrase that sits inside
   a longer matched phrase does not count, so "clean code review" is a **clean** phrase only, not
   also a **review** phrase.
   - "review", "find bugs", "security", "is this correct", "look for vulnerabilities" → **review**
   - "slow", "faster", "optimize", "bottleneck", "memory leak", "performance" → **perf**
   - "clean code audit" (or "clean-code audit"), "clean code review", "check this against clean code" → **clean**
     (user-invoked only — a bare "readability" or "audit against standards" ask is ambiguous: use step 3)
   - "remove slop", "clean up the codebase", "refactor out cruft / dead code / duplication" → **cleanup**
3. **No match, or phrases from more than one mode?** Ask which mode, naming the four options. For
   example, "review and optimize" matches **review** and **perf**, so ask. Use **review** without
   asking only when the request contains a review phrase and no other mode's phrase.

## Safety: cleanup writes code — the other three do not

`review`, `perf`, and `clean` are **source-read-only**: they analyze and report without touching
source files. Review and perf may write only the named report artifact their mode specifies
(`CODE_REVIEW.md` for review; perf returns its report in the response). During review/perf analysis,
they must not otherwise mutate the index, refs, stash, branch, worktree, or remote state.
`clean` retains its own report-writing and sync contract. `cleanup` **modifies files**. Therefore:

- **Never enter `cleanup` by weak inference.** Run it only when the user explicitly asks to
  refactor / clean up the codebase (or passes `mode:cleanup`). A plain "review my code" must never
  rewrite files — stay in a read-only mode.
- Review and perf analysis record `git rev-parse HEAD`, `git status`, and local tracking
  observations without claiming remote freshness. They do not fetch, stash, pull, rebase,
  checkout/switch, create or delete branches/worktrees, or apply source fixes. A separately
  approved mutation workflow owns its own freshness and stash-first sync contract.
- **Confirm before the first write** in `cleanup`, and follow that mode's own gating.

## Repo Sync Before Edits (mandatory)

Applies to `clean` (writes `CLEAN_CODE_AUDIT.md`) and `cleanup` (writes source) only. `review` and
`perf` never sync (see the Safety section). Before the first write in either mode:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin && git pull --rebase origin "$branch"
```

- If the working tree is dirty in `clean`, stash first, sync, then pop the stash.
- If the working tree is dirty in `cleanup`, stop and ask the user to commit or stash first.
- If `origin` is missing, or the pull or stash pop conflicts, stop and ask the user. Do not write any file.
- If the target is not a git repo, `clean` skips the sync and notes that in its report.

The full step, with recovery commands, is in `references/clean-mode.md` and `references/cleanup-mode.md`.

## Run the mode's workflow

Read the selected mode's reference file and execute its steps exactly. Supporting files each mode
uses (already colocated under this skill):

- **review** → `references/review-mode.md` — agents `agents/reviewer.md`, `agents/file-reviewer.md`, `agents/report-assembler.md`; refs `references/subagent-architecture.md`, `references/code-smells.md`
- **perf** → `references/perf-mode.md` — ref `references/language-checks.md`
- **clean** → `references/clean-mode.md` — refs `references/clean-code-checklist.md`, `references/tdd-checklist.md`, `references/html-report-guide.md`, `references/report-template.html`
- **cleanup** → `references/cleanup-mode.md` — the 8 cleaner agents in `agents/` (`deduplicator.md`, `type-consolidator.md`, `unused-code-killer.md`, `circular-dep-untangler.md`, `weak-type-strengthener.md`, `defensive-programming-remover.md`, `legacy-code-remover.md`, `slop-comment-cleaner.md`)

## Environment Check

If the Agent tool is available, modes that use subagents (**review**, **cleanup**) spawn them per
their workflow — fresh-context validation and parallel work. If it is unavailable (e.g., Claude.ai),
execute each mode's phases inline (less rigorous, but functional).

## Chaining modes

Modes compose: a common flow is **clean** (audit → `CLEAN_CODE_AUDIT.md`) then **cleanup** (apply the
refactors), or **review**/**perf** to find issues before fixing. Run one mode at a time; confirm with
the user before switching into the code-writing `cleanup` mode.

## Prerequisites

- If no target diff, PR, file set, or repository is named, ask for the scope before starting.
- If a reference or agent file listed for the selected mode is missing, stop and name the missing path.
- For `clean` or `cleanup`, follow that mode's sync, backup, dry-run, confirmation, and rollback steps
  in order. If a sync or safety check fails, stop before the first write.

## Acceptance Criteria

Verify every run against the selected mode's own acceptance criteria, then assert all of these router
criteria:

- Exactly one mode was selected and its reference workflow was followed end to end.
- Read-only modes changed no source files; verify with a path-scoped `git diff` when applicable.
- Every finding cites concrete evidence and the expected output artifact or report was produced.
- Tests or validation commands required by the selected mode completed with their expected result.
- Edge cases, limitations, skipped files, and degraded subagent coverage are disclosed.

Also check that a reader can use the final response:

- **Result is findable:** the first line after `Mode:` states the result and PASS, PARTIAL, or FAIL.
- **Facts and assumptions are separate:** verified claims name the check that was run; inferences,
  skipped scope, and untested behavior are labeled under `Uncertainty`.
- **Claims are traceable:** each finding points to a `file:line`, a command output, or a report section.
  An intermediate step passing does not count as the whole run passing.
- **Next decision is clear:** `Decision` names the approval needed (for example, starting `cleanup`),
  or says "No approval needed", and lists any remaining user action.

Agent inspection cannot confirm that a human understood the output. If no human feedback was given,
report human understanding as unconfirmed; do not count it as a failure or a pass.

## Expected Output

Every mode's final response carries these five items, in this order. Keep each item to one or two
lines; the mode's report artifact holds the detail.

```text
Mode: review
Result: PARTIAL — 1 critical, 2 major, 0 minor findings; reviewer pass incomplete for 3 files
Evidence: CODE_REVIEW.md written; reviewer agent validated 41/44 files; `git diff --stat -- src/` empty
Uncertainty: 3 generated files skipped (listed in CODE_REVIEW.md); no tests were run
Decision: No approval needed. To apply fixes, ask for a separate `cleanup` run.
```

## Step Completion Reports

After routing and after the selected workflow, emit a compact report:

```text
◆ Code Review ([mode])
  Mode selection:      √ pass
  Workflow criteria:   √ pass
  Output verified:     √ pass
  Safety boundary:     √ pass
  Result:              PASS | FAIL | PARTIAL
```

Use `× fail — reason` for any unmet check. Never report PASS while a selected-mode acceptance
criterion, expected output, required test, or safety guardrail is unresolved.

## Edge Cases

- Unknown `mode:` value → reject it and list the four valid modes.
- Mixed intents across modes → ask which mode to run first; never merge workflows implicitly.
- Missing target or inaccessible files → stop and request a concrete scope instead of guessing.
- Agent tool unavailable → use the selected reference's inline fallback and disclose reduced coverage.
- A read-only mode requests edits mid-run → finish the report, then require explicit approval before
  starting a separate `cleanup` run.
