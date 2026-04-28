# Step Completion Reports

After completing each major step in the frontend-design skill, output a status report in this format:

```
◆ [Step Name] ([step N of M] — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          √ pass (note if relevant)
  [Check 3]:          × fail — [reason]
  [Check 4]:          √ pass
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Adapt the check names to match what the step actually validates. Use `√` for pass, `×` for fail, and `—` to add brief context. The "Criteria" line summarizes how many acceptance criteria were met. The "Result" line gives the overall verdict.

## Phase-specific checks

### Design Thinking

```
◆ Design Thinking (step 1 of 2 — [component/page type])
··································································
  Purpose understood:       √ pass (problem and audience identified)
  Tone identified:          √ pass ([aesthetic direction] chosen)
  Differentiation clear:    √ pass | × fail — [what's missing]
  ____________________________
  Result:                   PASS | FAIL | PARTIAL
```

### Implementation

```
◆ Implementation (step 2 of 2 — [component/page type])
··································································
  Style guide applied:      √ pass | × fail — [deviations noted]
  Usability principles met: √ pass | × fail — [which principle failed]
  Aesthetics polished:      √ pass | × fail — [what needs refinement]
  ____________________________
  Result:                   PASS | FAIL | PARTIAL
```
