# Step Completion Report Templates

After completing each major step, output a status report in this format. Use `√` for pass, `×` for fail, and `—` to add brief context. The "Criteria" line summarizes how many acceptance criteria were met. The "Result" line gives the overall verdict.

## General Template

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

## Social Media Check (step 1 of 6)

```
◆ Social Media Check (step 1 of 6 — handle availability)
··································································
  Twitter available:      √ pass
  GitHub available:       √ pass
  Discord available:      × fail — server exists with exact name
  [Criteria]:             √ 2/3 met
  ____________________________
  Result:                 PARTIAL
```

## Package Registry (step 2 of 6)

```
◆ Package Registry (step 2 of 6 — namespace availability)
··································································
  npm clear:              √ pass
  PyPI clear:             × fail — package exists (owner: example)
  Homebrew clear:         √ pass
  [Criteria]:             √ 2/3 met
  ____________________________
  Result:                 PARTIAL
```

## Domain Check (step 3 of 6)

```
◆ Domain Check (step 3 of 6 — domain availability)
··································································
  .com available:         × fail — active site in same industry
  .dev available:         √ pass
  .io available:          √ pass
  [Criteria]:             √ 2/3 met
  ____________________________
  Result:                 PARTIAL
```

## Trademark Check (step 4 of 6)

```
◆ Trademark Check (step 4 of 6 — trademark conflicts)
··································································
  WIPO clear:              √ pass — no conflicts in classes 9/35/42
  EUIPO clear:             √ pass
  INPI clear:              × fail — similar mark in class 42
  [Criteria]:              √ 2/3 met
  ____________________________
  Result:                  PARTIAL
```

## Risk Assessment (step 5 of 6)

```
◆ Risk Assessment (step 5 of 6 — risk level)
··································································
  Trademark risk level:   √ pass — Low, no conflicts in classes 9/35/42
  Overall risk score:     √ pass — Moderate
  [Criteria]:             √ 2/2 met
  ____________________________
  Result:                 PASS
```

## Recommendation (step 6 of 6)

```
◆ Recommendation (step 6 of 6 — final verdict)
··································································
  Verdict issued:         √ pass — Modify
  Variants suggested:     √ pass — "acme-cli"
  [Criteria]:             √ 2/2 met
  ____________________________
  Result:                 PASS
```

On an Early-Exit run, steps 2-4 are skipped: emit reports for step 1 and step 6 only.
