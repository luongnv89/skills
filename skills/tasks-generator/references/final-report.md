# Final Report — examples and fill rules

Read this when writing the Final Report (SKILL.md → *Final Report*). SKILL.md owns the status rules and the required lines; this file shows filled examples and how to fill each line.

## Example (COMPLETE, first run)

```
Result: COMPLETE. /Users/me/ideas/2026_10_06_habit_tracker_for_nurses/tasks.md: 4 sprints, 26 tasks (5/8/7/6).
        MVP = sprints 1-3 (shift check-in, streaks, team dashboard); sprint 4 = Full Features.
Evidence: self-test 7/7 passed (26 task headings, 0 dangling IDs, 0 missing labels). Acceptance Criteria 12/12.
          analyze_dependencies.py: 26 tasks, 31 edges, critical path 1.1 → 2.1 → 2.4 → 3.2 → 3.6 (12 days),
          bottleneck 1.1 (5 direct dependents). Backup: no prior tasks.md. Commit a1b2c3d.
  tasks.md:  https://github.com/me/ideas/blob/main/2026_10_06_habit_tracker_for_nurses/tasks.md
  README.md: https://github.com/me/ideas/blob/main/README.md (Tasks status ✅)
Uncertainty: PRD §4.1 rate limit unspecified (assumed 60 req/min); PRD §5 "social login" providers unnamed
             (assumed Google + GitHub). Both are flagged in tasks.md. No tad.md, so the stack follows the PRD only.
Decision: No approval needed.
Next step: Review Sprint 1 and Wave 1 tasks before kickoff.
```

## Example (PARTIAL, regenerated with push declined)

```
Result: PARTIAL. /Users/me/ideas/2026_10_06_habit_tracker_for_nurses/tasks.md regenerated: 4 sprints, 28 tasks.
        Stopped in Phase 8 step 5: user declined the push.
Evidence: self-test 7/7 passed. Backup: tasks_backup_2026_10_06_141502.md (14 KB). Critical path 6 tasks (14 days).
          Commit 4b7d0aa (local only).
Uncertainty: The remote does not have this commit; GitHub links are omitted until it is pushed.
Decision: No approval needed.
Next step: Run `git -C /Users/me/ideas push origin main` when ready.
```

## Example (BLOCKED, cyclic graph)

```
Result: BLOCKED. No new tasks.md written. Stopped in Phase 5 step 3: analyze_dependencies.py rejected the graph twice.
Evidence: error[graph-input]: directed cycle: 2.3 -> 2.5 -> 2.3. Sprint files 4/4 valid. No files changed in the repo.
Uncertainty: The cycle comes from the sprint 2 worker; the PRD may describe two features that need each other.
Decision: Which of PRD §3.4 (export) and §3.5 (sharing) ships first?
Next step: Answer the decision, then re-run tasks-generator.
```

## Fill rules

| Line | Fill rule |
|------|-----------|
| `Result:` | Status first, then the absolute `tasks.md` path, the sprint count, the task count per sprint and the MVP scope as written in `tasks.md`. For `PARTIAL` or `BLOCKED`, name the phase and step where the run stopped and the `references/edge-cases.md` row or status rule that stopped it. A `BLOCKED` run writes `No new tasks.md written`. |
| `Evidence:` | Each Phase 6 check that ran, with its observed count. The task count, edge count, critical path, `effort_days` and bottlenecks copied from the script's JSON, never recomputed. The backup file name and size, or `no prior tasks.md`. The commit hash, marked `local only` when not pushed. One GitHub link per pushed file, built from the current branch. Omit a link or hash that does not exist and say why. |
| `Uncertainty:` | Every ambiguity flagged in `tasks.md` and the assumption behind it. Every missing supporting document that would have changed the plan (for example, no `tad.md`). Every agent that ran inline or was re-run. Every skipped phase. Write `none within the checks run` only when the list is empty. |
| `Decision:` | `No approval needed.` when nothing waits on the user. Otherwise the exact question the run waits on (an input choice, a Repo Sync conflict, a push confirmation, a dependency the PRD leaves open). |
| `Next step:` | One action for the user, tied to the stop reason or to the first wave of tasks. |

Match each claim to the scope of its evidence. A passing self-test supports "the file is well-formed", not "the plan is realistic". A successful `git commit` supports "committed", not "pushed". An effort total is the sum of the workers' estimates, not a delivery date.

## Reader checks

Use these when reviewing a run's Final Report, in addition to the correctness items in SKILL.md → *Acceptance Criteria*:

| Check | Pass when |
|-------|-----------|
| Result is findable | The first line states the status, the `tasks.md` path and the sprint and task counts, without opening `tasks.md`. |
| Facts and assumptions are separated | Verified claims name the check, script output or input file behind them; assumptions and ambiguities are labeled on the `Uncertainty:` line. |
| Claims are traceable | Each material claim points to a self-test count, the script's JSON, a backup file, a commit hash, a link, or a `tasks.md` section. |
| Next decision is clear | The `Decision:` line names the pending question or says `No approval needed.`, and the `Next step:` line names the user's action. |

A heading's presence alone does not pass a check. Ask a human reviewer the same four questions. If no reviewer answers, record human understanding as unconfirmed; agent inspection cannot confirm it. Negative-trigger cases in `evals/evals.json` are excluded from these checks.
