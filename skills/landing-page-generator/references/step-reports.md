# Step Completion Reports — Mode A

After completing each major Mode A step, output a status report in this format (Mode B
uses `references/readme-step-reports.md` instead). The five reports match the five Mode A
workflow steps in `SKILL.md`:

```
◆ [Step Name] (step N of 5 — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          √ pass (note if relevant)
  [Check 3]:          × fail — [reason]
  [Check 4]:          √ pass
  Criteria:           √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Adapt the check names to match what the step actually validates. Use `√` for pass, `×`
for fail, and `—` to add brief context. The `Criteria` line summarizes how many of the
step's checks passed. A step is `PASS` when every check passes, `PARTIAL` when it ends
with a recorded gap, `FAIL` when a check is blocked and the run cannot continue.

## Per-step checks

### Step 1 — Gather Product/Service Information

```
◆ Gather Information (step 1 of 5 — Mode A inputs)
··································································
  Core inputs present:     √ pass (name, audience, problem, CTA) | × fail — asked the user
  Proof points:            √ pass | — [proof needed] markers planned
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

### Step 2 — Choose Copywriting Framework

```
◆ Framework Selection (step 2 of 5 — PAS | AIDA | StoryBrand)
··································································
  Framework chosen:        √ pass (framework named)
  User told:               √ pass (override offered)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

### Step 3 — Generate Landing Page Sections

```
◆ Generate Sections (step 3 of 5 — [framework] template)
··································································
  Template sections:       √ pass (every section of the template populated)
  Headline rule:           √ pass (hero headline <= 10 words)
  Proof handling:          √ pass ([proof needed] where unsupported)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

### Step 4 — Format Output

```
◆ Format Output (step 4 of 5 — deliverable assembly)
··································································
  Template order:          √ pass (section names and order match the template)
  Optimization notes:      √ pass (A/B test ideas + conversion tips)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

### Step 5 — Copywriting Best Practices

```
◆ Best-Practices Review (step 5 of 5 — quality gate)
··································································
  CTA Button Rules:        √ pass (every CTA starts with an action verb, states the outcome)
  Anti-slop check:         √ pass (references/anti-slop-rules.md)
  Default Quality Bar:     √ pass (professional, production-ready, elegant, premium)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```
