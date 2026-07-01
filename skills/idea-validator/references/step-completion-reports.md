# Step Completion Reports — phase-specific checks

Read this file when emitting the Step Completion Report for a given phase (see SKILL.md → Step Completion Reports for the generic template and symbol legend). Use the block matching the phase you just completed.

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
  Web searches executed:  √ pass ([N] live queries run)
  Commercial coverage:    √ pass ([N] tools/services found)
  Open-source coverage:   √ pass ([N] OSS options found or no credible result documented)
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
  Market assessed:    √ pass | × fail — [gaps in analysis]
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
