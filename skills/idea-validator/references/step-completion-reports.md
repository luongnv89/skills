# Step Completion Reports — phase-specific checks

Read this file when emitting the Step Completion Report for a given phase (SKILL.md → Step Completion Reports). Use the block matching the phase you just completed. Every block follows this generic template: `√` pass, `×` fail, `—` brief context.

```
◆ [Step Name] ([step N of 6] — [idea name])
··································································
  [Check 1]:          √ pass
  [Check 2]:          × fail — [reason]
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Setup**
```
◆ Setup (step 1 of 6 — [idea name])
··································································
  Storage resolved:   √ pass ([path])
  Folder created:     √ pass ([YYYY_MM_DD_name/])
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Phase 1 — Clarify**
```
◆ Clarify (step 2 of 6 — [idea name])
··································································
  Questions answered: √ pass ([N] responses collected)
  idea.md updated:    √ pass | × fail — [missing sections]
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Phase 2 — Gather Technical Context**
```
◆ Gather Technical Context (step 3 of 6 — [idea name])
··································································
  Context sources identified: √ pass ([N] inputs collected)
  Technical feasibility assessed: √ pass | × fail — [gaps noted]
  idea.md technical section updated: √ pass | × fail — [missing fields]
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Phase 3 — Competitive Landscape**
```
◆ Competitive Landscape (step 4 of 6 — [idea name])
··································································
  Web searches executed:  √ pass ([N] live queries: [a] open source, [b] paid & market ([p] players + [s] share/size), [c] adjacent, [d] failed)
  Per-side minimums met:  √ pass | × fail — [side below its minimum]
  Open-source coverage:   √ pass ([N] OSS options found or no credible result documented)
  Paid players mapped:    √ pass (leader, [N] challengers, long tail) | √ pass (none found, queries logged)
  Share & structure:      √ pass ([structure], confidence [label]) | √ pass (skipped — no paid players) | × fail — [share stated without a source]
  Pricing tiers compared: √ pass ([N] players) | √ pass (skipped — no paid players) | × fail — [pricing pages not checked]
  Market size:            √ pass ([figure], [source], [year]) | √ pass (bottom-up proxy) | × fail — [no figure]
  Competitors found:      √ pass ([N] direct + [N] adjacent)
  Failed attempts checked:√ pass | × fail — [no results or skipped]
  Reuse potential assessed: √ pass | × fail — [OSS build-on/fork path missing]
  validate.md updated:    √ pass | × fail — [missing sections]
  ____________________________
  Result:                 PASS | FAIL | PARTIAL
```

**Phase 4 — Evaluate**
```
◆ Evaluate (step 5 of 6 — [idea name])
··································································
  Feasibility scored: √ pass ([score]/10)
  Market assessed:    √ pass (reused Phase 3 evidence; [N] gap-fill queries) | × fail — [gaps in analysis]
  Verdict rule:       √ pass ([verdict], rule [1-3])
  validate.md updated:√ pass | × fail — [missing sections]
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Phase 5 — Improve**
```
◆ Improve (step 6 of 6 — [idea name])
··································································
  Enhancements identified:    √ pass ([N] improvements listed)
  Recommendations added:      √ pass | × fail — [what's missing]
  ____________________________
  Result:                     PASS | FAIL | PARTIAL
```
