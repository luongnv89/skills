# Final Report — example and fill rules

Read this when writing the Final Report (SKILL.md → *Final Report*). SKILL.md owns the status rules and the required lines; this file shows a filled example and how to fill each line.

## Example (COMPLETE)

```
Result: COMPLETE. Verdict: Maybe (rule 2: a maintained OSS project covers most of the idea with no chosen build-on path).
  Ratings: Creativity 7/10, Feasibility 8/10, Market Impact 6/10, Technical Execution 8/10.
Evidence: /Users/me/workspace/ideas/2026_10_06_habit_tracker_for_nurses/
  idea.md:     https://github.com/me/ideas/blob/main/2026_10_06_habit_tracker_for_nurses/idea.md
  validate.md: https://github.com/me/ideas/blob/main/2026_10_06_habit_tracker_for_nurses/validate.md
  README.md:   https://github.com/me/ideas/blob/main/README.md
  Commit: 3f2a9c1. 6 live queries run; 5 competitors found (3 commercial, 1 OSS, 1 failed).
Strengths: 1. A narrow, reachable audience  2. Low infrastructure cost  3. Shift-work scheduling is a real gap
Concerns:  1. Three direct competitors already exist with significant traction
           2. Monetization path unclear — target users expect free tools
           3. MVP scope likely exceeds 2-4 week estimate
Uncertainty: Budget answered "unknown". Market size is inferred from one hospital-staffing report, not measured.
Decision: No approval needed.
Next step: Interview five night-shift nurses about how they track habits today.
```

The same ratings appear in `validate.md` → `## Ratings`, with one reason per score.

## Fill rules

| Line | Fill rule |
|------|-----------|
| `Result:` | Status first, then the verdict and the number of the verdict rule that produced it. For `PARTIAL` or `BLOCKED`, name the step where the run stopped and the Edge Cases row or rule that stopped it. A `BLOCKED` run has no verdict or ratings; write `no verdict`. |
| `Evidence:` | The absolute project folder path. One GitHub link per file the run wrote, built from the current branch. The commit hash. The counts of live queries and competitors, taken from `validate.md`. Omit a link or hash that does not exist (for example, no git repository) and say why. |
| `Strengths:` / `Concerns:` | The top 3 of each from `validate.md`. Each concern names its source: a competitor, a rating, or a user answer. |
| `Uncertainty:` | Every `unknown` answer from Phases 1-2. Every market, pricing or traction claim not backed by a Phase 3 source, labeled as an assumption or inference. Every skipped check (no live search, no push). Write `none within the checks run` only when the list is empty. |
| `Decision:` | `No approval needed.` on a normal run, because invoking the skill authorizes the commit and push. On a stop, the exact question the run is waiting on. |
| `Next step:` | One action for the user, tied to the top concern or the verdict rule. |

Match each claim to the scope of its evidence. A successful `git commit` supports "committed", not "pushed". A search result page supports "competitor exists", not "competitor has traction"; traction needs a number from a source.

## Reader checks

Use these when reviewing a run's Final Report, in addition to the correctness items in SKILL.md → *Acceptance Criteria*:

| Check | Pass when |
|-------|-----------|
| Result is findable | The first line states the status and the verdict, without opening `validate.md`. |
| Facts and assumptions are separated | Sourced claims cite a competitor URL or a user answer; assumptions and inferences are labeled on the `Uncertainty:` line. |
| Claims are traceable | Each material claim points to a link, a commit hash, or a `validate.md` section that supports its scope. |
| Next decision is clear | The `Decision:` line names the pending question or says `No approval needed.`, and the `Next step:` line names the user's action. |

A heading's presence alone does not pass a check. Ask a human reviewer the same four questions. If no reviewer answers, record human understanding as unconfirmed; agent inspection cannot confirm it. Negative-trigger cases in `evals/evals.json` are excluded from these checks.
