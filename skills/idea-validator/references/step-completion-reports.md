# Step Completion Reports — phase-specific checks

Read this file when emitting the Step Completion Report for a given step (SKILL.md → Step Completion Reports). Use the block matching the step you just completed. Every block follows this generic template: `√` pass, `×` fail, `○` skipped, `—` before the reason or brief context.

```
◆ [Step Name] ([step N of 8] — [idea name])
··································································
  [Check 1]:          √ pass
  [Check 2]:          × fail — [reason]
  [Check 3]:          ○ skip — [reason]
  ____________________________
  Result:             PASS | PARTIAL | FAIL | SKIPPED
```

**Numbering.** Every run has the same 8 steps, numbered in the order their reports print: 1 Repo Sync, 2 Setup, 3 Clarify, 4 Gather Technical Context, 5 Competitive Landscape, 6 Evaluate, 7 Improve, 8 Commit and Push. Repo Sync is step 1 even though it runs between Setup steps 2 and 3, because the Setup report prints only when Setup ends, after Repo Sync. A step keeps its number when an earlier step was skipped or the run stopped early, so `M` is always 8. A step that never started because the run stopped before it (for example, BLOCKED in Setup step 1) prints no block. A step skipped by rule (for example, Repo Sync and Commit and Push when the ideas root is not a git repository) still prints its block, with `○` and the reason.

**Result.** Take the first that matches:
- `SKIPPED`: the whole step did not run; its first check line gives the reason.
- `FAIL`: a check failed and the step did not recover.
- `PARTIAL`: a check the step needed was skipped or stopped, such as a push that did not happen.
- `PASS`: every needed check passed. A `○` on a check this run did not need (no stash on a clean tree) still allows `PASS`.

A sync or push that did not happen (skipped, blocked, or waiting on the user) is `○` with its reason, never `√`. A push is `√` only when the remote branch is confirmed at the local commit (`git ls-remote origin refs/heads/<branch>` prints the hash of `HEAD`).

**Repo Sync**
```
◆ Repo Sync (step 1 of 8 — [idea name])
··································································
  Git repository:     √ pass ([ideas root]) | ○ skip — not a git repository
  Working tree:       √ pass (clean) | √ pass ([N] changes stashed as pre-sync)
  Fetch and rebase:   √ pass ([branch] at [short hash]; [N] new commits | already up to date) | ○ skip — [no origin / pull failed / rebase conflict]; asked the user
  Stash restored:     √ pass | ○ skip — nothing stashed | × fail — stash pop conflict; asked the user
  ____________________________
  Result:             PASS | PARTIAL | FAIL | SKIPPED
```

**Setup**
```
◆ Setup (step 2 of 8 — [idea name])
··································································
  Storage resolved:   √ pass ([path])
  Folder created:     √ pass ([YYYY_MM_DD_name/])
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Phase 1 — Clarify**
```
◆ Clarify (step 3 of 8 — [idea name])
··································································
  Questions answered: √ pass ([N] responses collected)
  idea.md updated:    √ pass | × fail — [missing sections]
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Phase 2 — Gather Technical Context**
```
◆ Gather Technical Context (step 4 of 8 — [idea name])
··································································
  Context sources identified: √ pass ([N] inputs collected)
  Technical constraints recorded: √ pass (stack, timeline and team, budget, assets: [N] answered, [M] unknown) | × fail — [item neither answered nor marked unknown]
  idea.md technical section updated: √ pass | × fail — [missing fields]
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Phase 3 — Competitive Landscape**
```
◆ Competitive Landscape (step 5 of 8 — [idea name])
··································································
  Web searches executed:  √ pass ([N] live queries: [a] open source, [b] paid & market ([p] players + [s] share/size), [c] adjacent, [d] failed)
  Per-side minimums met:  √ pass | × fail — [side below its minimum]
  Open-source coverage:   √ pass ([N] OSS options found or no credible result documented)
  Paid players mapped:    √ pass (leader, [N] challengers, long tail) | √ pass (none found, queries logged)
  Share & structure:      √ pass ([structure], confidence [label]) | ○ skip — no paid players | × fail — [share stated without a source]
  Pricing tiers compared: √ pass ([N] players) | ○ skip — no paid players | × fail — [pricing pages not checked]
  Market size:            √ pass ([figure], [source], [year]) | √ pass (bottom-up proxy) | × fail — [no figure]
  Competitors found:      √ pass ([N] direct + [N] adjacent)
  Near-identical check:   √ pass (none found; closest: [Name] misses [element], one per product missing only one element) | √ pass ([Name] is near-identical; showed it and asked the user)
  Failed attempts checked:√ pass | × fail — [no results or skipped]
  Reuse potential assessed: √ pass | × fail — [OSS build-on/fork path missing]
  validate.md updated:    √ pass | × fail — [missing sections]
  ____________________________
  Result:                 PASS | FAIL | PARTIAL
```

**Phase 4 — Evaluate**
```
◆ Evaluate (step 6 of 8 — [idea name])
··································································
  Feasibility scored: √ pass ([score]/10)
  Market assessed:    √ pass (reused Phase 3 evidence; [N] gap-fill queries) | × fail — [gaps in analysis]
  Verdict rule:       √ pass ([verdict], rule [1-3])
  Phase 4 shape:      √ pass (6 area headings, Plans to charge line, risks labelled hard or soft, ratings table with reasons, rule line under ## Why) | × fail — [missing part]
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Phase 5 — Improve**
```
◆ Improve (step 7 of 8 — [idea name])
··································································
  Enhancements identified:    √ pass ([N] improvements listed) | ○ skip — [Edge Cases row that skips Phase 5]
  Recommendations added:      √ pass | × fail — [what's missing] | ○ skip — [Edge Cases row that skips Phase 5]
  ____________________________
  Result:                     PASS | FAIL | PARTIAL | SKIPPED
```

**Commit and Push**
```
◆ Commit and Push (step 8 of 8 — [idea name])
··································································
  Git repository:     √ pass | ○ skip — not a git repository
  Staged files:       √ pass ([N]: idea.md, validate.md[, README.md]; [M] others unstaged) | × fail — [unexpected file still staged]
  Commit:             √ pass ([short hash] docs(ideas): validate [name]) | × fail — [error]
  Push:               √ pass ([branch] → origin at [short hash of HEAD]) | √ pass (after one rebase retry; origin at [new short hash]) | ○ skip — no origin remote; asked the user | ○ skip — blocked: [rejected after one retry / rebase conflict]; asked the user
  ____________________________
  Result:             PASS | PARTIAL | FAIL | SKIPPED
```

A rebase retry rewrites the commit, so report the hash after the rebase, and use that hash in the Final Report.
