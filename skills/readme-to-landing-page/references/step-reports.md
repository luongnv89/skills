# Step Completion Reports

After completing each major step, output a status report in this format:

```
[diamond] [Step Name] ([step N of M] — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          √ pass (note if relevant)
  [Check 3]:          × fail — [reason]
  [Check 4]:          √ pass
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Adapt the check names to match what the step actually validates. Use `√` for pass, `×` for fail, and `—` to add brief context. The "Criteria" line summarizes how many acceptance criteria were met.

## Phase-specific checks

### Steps 1-2 — Context Gathering

```
[diamond] Context Gathering (step 1 of 7 — project analysis)
··································································
  Project files read:       √ pass
  Value prop identified:    √ pass (one-sentence benefit drafted)
  Audience defined:         √ pass (primary audience named)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

### Step 3 — Framework Selection

```
[diamond] Framework Selection (step 3 of 7 — copywriting framework)
··································································
  Framework chosen:         √ pass (PAS | AIDA | StoryBrand)
  Sections mapped:          √ pass (section flow planned)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

### Steps 4-5 — Rewrite

```
[diamond] Rewrite (step 5 of 7 — README transformation)
··································································
  Backup created:           √ pass (README.backup.md written)
  Sections written:         √ pass (hero -> CTA flow complete)
  CTAs placed:              √ pass (primary CTA in hero + footer)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

### Steps 6-7 — Review

```
[diamond] Review (step 6 of 7 — quality gate)
··································································
  Checklist passed:         √ pass (13/13 checks green)
  User approved:            √ pass
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```
