# Final Report — example and fill rules

Read this when writing the Final Report (SKILL.md → *Final Report*). SKILL.md owns the status rules and the required lines; this file shows filled examples and how to fill each line.

## Example (COMPLETE, create mode)

```
Result: COMPLETE. create mode, /Users/me/ideas/2026_10_06_habit_tracker_for_nurses/prd.md (10/10 sections)
Evidence: verification 6/6 passed (check 7 n/a, no prior prd.md): 12 '## ' headings, 6 Given/When/Then lines, 2 mermaid blocks,
          9 MoSCoW lines, idea.md cited. Backup: no prior prd.md. Commit 9c41e2d.
  prd.md:    https://github.com/me/ideas/blob/main/2026_10_06_habit_tracker_for_nurses/prd.md
  README.md: https://github.com/me/ideas/blob/main/README.md (PRD status ✅)
Uncertainty: §6 hosting is TBD (idea.md names no provider). Compliance answered "unknown", recorded in §9.
             The p95 latency target (300 ms) is an assumption, not taken from validate.md.
Decision: No approval needed.
Next step: Review §3 Feature Requirements with two night-shift nurses, then run tad-generator.
```

## Example (PARTIAL, push declined)

```
Result: PARTIAL. modify mode, /Users/me/ideas/2026_10_06_habit_tracker_for_nurses/prd.md. Stopped in Phase 7: user declined the push.
Evidence: verification 7/7 passed. Backup: prd.backup.20261006_141502.md (18 KB). Commit 4b7d0aa (local only).
Uncertainty: The remote does not have this commit; the GitHub links are omitted until it is pushed.
Decision: No approval needed.
Next step: Run `git push origin main` in /Users/me/ideas when ready.
```

## Example (BLOCKED, negative verdict)

```
Result: BLOCKED. No prd.md written. Stopped in Phase 1 step 5: validate.md verdict is "Skip it" and the user did not confirm.
Evidence: idea.md and validate.md found in /Users/me/ideas/2026_10_06_ai_meal_planner/. No files changed.
Uncertainty: none within the checks run.
Decision: Generate a PRD despite the "Skip it" verdict? Reply yes to continue.
Next step: Address the top concern in validate.md, or confirm to proceed.
```

## Fill rules

| Line | Fill rule |
|------|-----------|
| `Result:` | Status first, then the run mode and the absolute `prd.md` path. For `PARTIAL` or `BLOCKED`, name the phase and step where the run stopped and the `references/edge-cases.md` row or status rule that stopped it. A `BLOCKED` run writes `No prd.md written`. |
| `Evidence:` | Each check from `references/verification-steps.md` that ran, with its observed count. The backup file name and size, or `no prior prd.md`. The commit hash, marked `local only` when not pushed. One GitHub link per pushed file, built from the current branch. Omit a link or hash that does not exist and say why. |
| `Uncertainty:` | Every `TBD` placeholder and its section. Every Phase 3 question left unanswered. Every number or claim inferred instead of read from `idea.md`, `validate.md` or a user answer, labeled as an assumption. Every skipped phase (for example, Phases 6-7 outside an ideas repo). Write `none within the checks run` only when the list is empty. |
| `Decision:` | `No approval needed.` when nothing waits on the user. Otherwise the exact question the run is waiting on (a negative verdict, a missing `validate.md`, a requirements conflict, a push confirmation). |
| `Next step:` | One action for the user, tied to the stop reason or to the PRD's weakest section. |

Match each claim to the scope of its evidence. A passing `grep -c '^## '` supports "10 headings present", not "the PRD is complete". A successful `git commit` supports "committed", not "pushed".

## Reader checks

Use these when reviewing a run's Final Report, in addition to the correctness items in SKILL.md → *Acceptance Criteria*:

| Check | Pass when |
|-------|-----------|
| Result is findable | The first line states the status, the run mode and the `prd.md` path, without opening `prd.md`. |
| Facts and assumptions are separated | Verified claims name the check or input file behind them; assumptions, inferences and `TBD` values are labeled on the `Uncertainty:` line. |
| Claims are traceable | Each material claim points to a verification count, a backup file, a commit hash, a link, or a `prd.md` section that supports its scope. |
| Next decision is clear | The `Decision:` line names the pending question or says `No approval needed.`, and the `Next step:` line names the user's action. |

A heading's presence alone does not pass a check. Ask a human reviewer the same four questions. If no reviewer answers, record human understanding as unconfirmed; agent inspection cannot confirm it. Negative-trigger cases in `evals/evals.json` are excluded from these checks.
