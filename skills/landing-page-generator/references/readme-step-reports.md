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
[diamond] Context Gathering (step 1 of 9 — project analysis)
··································································
  Project files read:       √ pass
  Value prop identified:    √ pass (one-sentence benefit drafted)
  Audience defined:         √ pass (primary audience named)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

### Step 3 — Framework Selection

```
[diamond] Framework Selection (step 3 of 9 — copywriting framework)
··································································
  Framework chosen:         √ pass (PAS | AIDA | StoryBrand)
  Sections mapped:          √ pass (section flow planned)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

### Steps 4-5 — Rewrite

```
[diamond] Rewrite (step 5 of 9 — README transformation)
··································································
  Backup created:           √ pass (README.backup.md written)
  Sections written:         √ pass (hero -> CTA flow complete)
  CTAs placed:              √ pass (primary CTA in hero + footer)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

### Step 6 — Review

```
[diamond] Review (step 6 of 9 — quality gate)
··································································
  Checklist passed:         √ pass (13/13 checks green)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

### Step 7 — Companion Pages

```
[diamond] Companion Pages (step 7 of 9 — PRIVACY.md, TERMS.md, CHANGELOG.md, docs)
··································································
  Pages decided:            √ pass (written / linked / skipped, each with a reason)
  Facts traced:             √ pass (each fact from a project file or a [placeholder] marker)
  Links resolve:            √ pass (test -e on each README link to a companion page)
  Nothing overwritten:      √ pass (only README.md changed; README.backup.md holds the original)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

### Step 8 — Build the Final Page

```
[diamond] Build the Final Page (step 8 of 9 — frontend-design)
··································································
  Build decided:            √ pass (page: built (landing-page/: index.html, ...)) | — page: skipped — <reason>
  frontend-design:          √ pass (acquired) | × fail — page: not built — <reason>; copy only
  Page checks:              √ pass (sections, CTAs, [placeholder] markers carried; nothing added)
  Links resolve:            √ pass (test -e on each local link; each #id found)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

### Step 9 — Present

```
[diamond] Present (step 9 of 9 — handoff)
··································································
  Summary given:            √ pass (framework, backup location, companion page decisions, page folder)
  User approved:            √ pass | — feedback requested
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```
