# Final Report — example and fill rules

Read this when writing the Final Report (SKILL.md → *Final Report*). SKILL.md owns the status rules and the order of the lines; this file shows a filled example and how to fill each line.

## Example (COMPLETE)

```
Result: COMPLETE. Verdict: Maybe (rule 2: a maintained OSS project covers most of the idea with no chosen build-on path).
  Ratings: Creativity 7/10, Feasibility 8/10, Market Impact 6/10, Technical Execution 8/10.
Evidence: /Users/me/workspace/ideas/2026_10_06_habit_tracker_for_nurses/
  idea.md:     https://github.com/me/ideas/blob/main/2026_10_06_habit_tracker_for_nurses/idea.md
  validate.md: https://github.com/me/ideas/blob/main/2026_10_06_habit_tracker_for_nurses/validate.md
  README.md:   https://github.com/me/ideas/blob/main/README.md
  Commit: 3f2a9c1. 7 live queries (open source 2, paid & market 3, adjacent 1, failed 1); 5 competitors found (3 paid, 1 OSS, 1 failed).
Strengths: 1. A narrow, reachable audience  2. Low infrastructure cost  3. Shift-work scheduling is a real gap
Concerns:  1. Three direct competitors already exist with significant traction
           2. Monetization path unclear — target users expect free tools
           3. MVP scope likely exceeds 2-4 week estimate
Uncertainty: Budget answered "unknown". Market size is a bottom-up proxy (nurse headcount × app price), low confidence;
  the leader's share is derived from app-store review counts, low confidence.
Decision: No approval needed.
Next step: Interview five night-shift nurses about how they track habits today.
```

The same ratings appear in `validate.md` → `## Ratings`, with one reason per score.

## Fill rules

| Line | Fill rule |
|------|-----------|
| `Result:` | Status first, then the verdict and the number of the verdict rule that produced it, then the four ratings when Phase 4 ran. For `PARTIAL` or `BLOCKED`, name the step where the run stopped and the Edge Cases row or rule that stopped it. A run that stopped before Phase 4, `BLOCKED` included, has no verdict or ratings; write `no verdict`. |
| `Evidence:` | The absolute project folder path. One GitHub link per file the run wrote (`idea.md`, `validate.md`, and `README.md` when changed), built from `git remote get-url origin` (SSH or HTTPS form) and the current branch: `https://github.com/<owner>/<repo>/blob/<branch>/<relative-path>`, where `<relative-path>` is the file's path from the repository root. When the ideas root is in a git repository whose `origin` is not on `github.com`, or that has no `origin`, give each file's repo-relative path instead and say why there are no links: `no GitHub links: origin is <host>` or `no GitHub links: no origin remote`. The commit hash. The live query count per side (open source, paid & market, adjacent, failed, plus any Phase 4 gap-fill) taken from `validate.md` → *Research Log*, and the competitors found, counting unique players across the competitors and Market Players & Share tables (a player in both counts once). Cite only checks that ran; omit a link or hash that does not exist (for example, no git repository) and say why. |
| `Strengths:` / `Concerns:` | The top 3 of each from `validate.md`. Each concern names its source: a competitor, a rating, or a user answer. |
| `Uncertainty:` | Every `unknown` answer from Phases 1-2; an unknown charging plan reads `charging plan unknown, treated as charging`, and an unknown team, budget or timeline names the default assumed for the risk labels. Willingness to pay with no evidence, for an idea that plans to charge. Every market, pricing or traction claim not backed by a Phase 3 source, labeled as an assumption or inference. Every share or market-size figure with `low` confidence, and a bottom-up market-size proxy. `shares not comparable` when the market structure rests on relative size only. Every skipped check (no live search, no push). Write `none within the checks run` only when the list is empty. |
| `Decision:` | `No approval needed.` on a normal run, because invoking the skill authorizes the commit and push. On a stop, the exact question the run is waiting on. |
| `Next step:` | One action for the user, tied to the top concern or the verdict rule. |

Match each claim to the scope of its evidence. A successful `git commit` supports "committed", not "pushed". A search result page supports "competitor exists", not "competitor has traction"; traction needs a number from a source. A share derived from listed players' figures supports "share of listed players", not "market share".

## Reader checks

Use these when reviewing a run's Final Report, in addition to the correctness items in SKILL.md → *Acceptance Criteria*:

| Check | Pass when |
|-------|-----------|
| Result is findable | The first line states the status and the verdict, without opening `validate.md`. |
| Facts and assumptions are separated | Sourced claims cite a competitor URL or a user answer; share and market-size figures carry a source, a year and a confidence label; assumptions and inferences are labeled on the `Uncertainty:` line. |
| Claims are traceable | Each material claim points to a link, a commit hash, or a `validate.md` section that supports its scope. |
| Next decision is clear | The `Decision:` line names the pending question or says `No approval needed.`, and the `Next step:` line names the user's action. |

A heading's presence alone does not pass a check. Ask a human reviewer the same four questions. If no reviewer answers, record human understanding as unconfirmed; agent inspection cannot confirm it. Negative-trigger cases in `meta/idea-validator/evals/evals.json` are excluded from these checks.
