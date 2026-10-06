# Output format

What the run prints in chat: a Step Completion Report after each phase, then one final report. The
two files the run writes follow `report-template.md` and `plan-template.md`.

## Step Completion Reports

Use the block in SKILL.md (*Step Completion Reports*) with these per-phase check names:

- **Baseline:** `Build probed`, `Tests probed`, `Coverage probed`, `CI probed`, `Verdict recorded`
- **Inventory:** `Stack detected`, `Ecosystems listed`, `UI branch resolved`, `Worklist complete`
- **Audits:** `DEP complete`, `Delegated dims complete`, `Evidence cited`, `IDs unique`
- **Report:** `File written`, `Coverage table complete`, `Counts reconcile`
- **Plan:** `All Critical/High closed`, `Task format valid`, `No circular deps`, `Critical path stated`, `Milestones measurable`
- **Validation:** `Citations resolve`, `No orphan findings`, `Must-fix count 0`

A phase's `Result: PASS` is not the run's result. The run's result is the final report's `Result:`
line, set by the rules in SKILL.md (*Final report*).

## Final report fields

The first four lines are fixed and appear in this order. Keep each to one or two lines.

| Line | Must contain | Never |
|---|---|---|
| `Result:` | `COMPLETE`, `PARTIAL — <reason>`, or `BLOCKED — <reason>`, then the finding count and whether both files were written | a status the SKILL.md rules do not produce |
| `Evidence:` | checks that actually ran and what they showed: the before/after `git status --porcelain` and `git diff` comparison, the baseline commands and their results, the Summary-count reconciliation, the validator rounds and `must-fix` count | a check that did not run, or a delegate's claim restated as a fact |
| `Uncertainty:` | every **Not Assessed** row with its reason, every degraded path, a failed dependency release, and what was not executed (no plan task runs during the audit). Label inferences `inferred` and assumptions `assumed` | a guess presented as a measured value |
| `Decision:` | `No approval needed.` for a finished audit, because the skill changed nothing. Otherwise name the approval (for example, committing the reports, which happens only on request). Then `Next:` names the user's next action | an invented approval gate |

For a `BLOCKED` run, `Decision:` names what the user must decide before a re-run: resolve the sync
conflict, review the file the run changed or restored, or confirm a re-run after stale citations.

## Outcome to status

These examples apply the SKILL.md rules. If an example and the rules disagree, the rules win.

| Outcome | Status |
|---|---|
| Both files written, every acceptance criterion holds, 0 `must-fix` | `COMPLETE` |
| Baseline RED, audit continued, Sprint 0 restores green | `COMPLETE` |
| UX Not Assessed — no UI detected; DEP Not Assessed — no manifest | `COMPLETE` |
| User narrowed the dimensions; the rest Not Assessed — out of requested scope | `COMPLETE` |
| `code-review` or `dont-make-me-think` unavailable; its dimensions Not Assessed — skill unavailable | `PARTIAL` |
| Offline: DEP currency Not Assessed — offline | `PARTIAL` |
| No shell: whole baseline Not Assessed — no shell | `PARTIAL` |
| Skill tool unavailable: `BUG`, `PERF`, or `UX` ran inline | `PARTIAL` |
| Huge repo: paths left unscanned and listed in Limitations | `PARTIAL` |
| Not a git repo: the read-only snapshot could not be taken | `PARTIAL` |
| A `must-fix` still open after validator round 2 | `PARTIAL` |
| A tracked file changed during the run, even if restored | `BLOCKED` |
| Repo Sync conflict, or citations stale after a requested sync | `BLOCKED` |
| The run stopped before both files were written | `BLOCKED` |

## Format rule

The two output files are Markdown, because `tasks-generator` and `plan-to-issues` read them. The
report groups findings by dimension and ranks them by severity, and finding IDs link each plan task
to its evidence, so a reader can inspect them without filters. The chat output is concise text.

If the user asks for another format (HTML, CSV, a dashboard), write the two Markdown files anyway.
Then say in `Uncertainty:` that the other format was not produced, because any extra file would be
an undeclared artifact under the read-only contract.

## Full example

```text
Result: COMPLETE — 47 findings; Pre + P0–P4 plan; 0 must-fix
Evidence: git status --porcelain and git diff match the pre-run snapshot; validator ran 1 round
Uncertainty: coverage Not Assessed (no coverage tool); no plan task was executed
Decision: No approval needed. Next: review MODERNIZATION_PLAN.md, then run Task Pre.1
Target: /path/to/repo
Baseline: AMBER — builds; 41/58 tests pass; no coverage tool; CI absent
Dimensions: 8 audited, 2 Not Assessed (UX — no UI detected; PERF — out of requested scope)
Findings: 3 critical, 11 high, 24 medium, 9 low
Outputs: MODERNIZATION_REPORT.md, MODERNIZATION_PLAN.md
Plan: Pre + P0–P4, 10 sprints, 50 tasks — critical path Pre.1 → Pre.2 → 0.1 → 2.4
Validation: plan-validator PASS, 0 must-fix
Source files changed: 0
```

A `PARTIAL` run opens the same way, with the reason on the first line:

```text
Result: PARTIAL — BUG and PERF Not Assessed (code-review unavailable); 31 findings; both files written
Evidence: git status --porcelain and git diff match the pre-run snapshot; validator ran 2 rounds, 0 must-fix left
Uncertainty: BUG and PERF Not Assessed — skill unavailable; DEP currency Not Assessed — offline
Decision: No approval needed. Next: install code-review, then re-run for BUG and PERF
```
