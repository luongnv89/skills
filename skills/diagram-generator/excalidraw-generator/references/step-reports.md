# Step Completion Report Format

Read this when printing a phase report (SKILL.md → *Step Completion Reports*). After each phase, output a status report in this template:

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

Use `√` for pass, `×` for fail, `—` for brief context. The "Criteria" line summarises how many acceptance criteria were met. The "Result" line gives the overall verdict.

## Phase-specific checks

### Phase 1 — Understand
```
◆ Understand (step 1 of 4 — [diagram type])
··································································
  Requirements clarity:   √ pass
  Scope confirmed:        √ pass (entities and relationships identified)
  ____________________________
  Result:                 PASS | FAIL | PARTIAL
```

### Phase 2 — Propose
```
◆ Propose (step 2 of 4 — [diagram type])
··································································
  Type selected:          √ pass ([diagram type] chosen)
  User approved:          √ pass | √ defaults stated | × fail — awaiting confirmation
  ____________________________
  Result:                 PASS | FAIL | PARTIAL
```

### Phase 3 — Generate
```
◆ Generate (step 3 of 4 — [diagram type])
··································································
  JSON valid:             √ pass
  Output path chosen:     √ pass ([filename].excalidraw, new | update | overwrite confirmed)
  Requirements covered:   √ pass
  ____________________________
  Result:                 PASS | FAIL | PARTIAL
```

### Phase 4 — Validate
```
◆ Validate (step 4 of 4 — [diagram type])
··································································
  Fix cycles:             √ N/3
  Quality checks N/10:    √ pass | × fail — [checks failed]
  Text sizing correct:    √ pass | × fail — [elements affected]
  File written:           √ pass ([filename].excalidraw) | × not written (BLOCKED)
  ____________________________
  Result:                 PASS | FAIL | PARTIAL
```

The Validate report precedes the Final Report (`final-report.md`); it does not replace it.
