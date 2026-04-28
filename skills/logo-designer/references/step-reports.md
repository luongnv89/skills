# Step Completion Reports

After completing each major step, output a status report in this format:

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

**Phase 1 — Analysis**
```
◆ Analysis (step 1 of 4 — [project name])
··································································
  Product identity detected:  √ pass ([name and purpose found])
  Brand colors found:         √ pass ([hex codes]) | × fail — using defaults
  Project type identified:    √ pass ([Developer/SaaS/Startup/etc.])
  ____________________________
  Result:                     PASS | FAIL | PARTIAL
```

**Phase 2 — Design**
```
◆ Design (step 2 of 4 — [project name])
··································································
  Style selected:             √ pass ([aesthetic direction])
  Typography chosen:          √ pass ([font name and weight])
  SVG valid:                  √ pass | × fail — [validation errors]
  ____________________________
  Result:                     PASS | FAIL | PARTIAL
```

**Phase 3 — Deliverables**
```
◆ Deliverables (step 3 of 4 — [project name])
··································································
  7 variants generated:       √ pass | × fail — [missing files]
  Files written:              √ pass (/assets/logo/ populated)
  ____________________________
  Result:                     PASS | FAIL | PARTIAL
```

**Phase 4 — Documentation**
```
◆ Documentation (step 4 of 4 — [project name])
··································································
  Rationale documented:       √ pass | × fail — [missing sections]
  Colors specified:           √ pass ([N] hex codes documented)
  Showcase created:           √ pass (brand-showcase.html written)
  ____________________________
  Result:                     PASS | FAIL | PARTIAL
```

## Example Console Output

For the same "fastbuild" example, the analysis and design rationale presented to the user:

```
## Analysis Summary
Product: fastbuild
Type: Developer/CLI Tool
Purpose: Fast incremental build system for large codebases
Audience: Software developers, DevOps engineers
Existing colors: None detected
Assets found: None

## Design Rationale
- **Symbol**: Abstract "F" formed by stacked horizontal bars suggesting speed and layered builds
- **Colors**: Default style guide — dark base with Neon Green highlight on the speed bars
- **Typography**: Inter for clean, modern readability

## Colors
Primary: #0A0A0A
Surface: #111111
Border: #262626
Muted: #A1A1A1
Text: #FAFAFA
Accent: #00FF41 (highlights only — borders, lines, CTAs)
Background Light: #FAFAFA
Background Dark: #0A0A0A
```
