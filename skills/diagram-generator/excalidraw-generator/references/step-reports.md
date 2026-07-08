# Step Completion Report Format

After each major step, output a status report in this template:

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
  User approved:          √ pass | × fail — awaiting confirmation
  ____________________________
  Result:                 PASS | FAIL | PARTIAL
```

### Phase 3 — Generate
```
◆ Generate (step 3 of 4 — [diagram type])
··································································
  JSON valid:             √ pass
  File written:           √ pass ([filename].excalidraw)
  ____________________________
  Result:                 PASS | FAIL | PARTIAL
```

### Phase 4 — Validate
```
◆ Validate (step 4 of 4 — [diagram type])
··································································
  Quality checks 10/10:   √ pass | × fail — [checks failed]
  Text sizing correct:    √ pass | × fail — [elements affected]
  ____________________________
  Result:                 PASS | FAIL | PARTIAL
```
