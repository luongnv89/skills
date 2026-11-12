# Phase-specific Step Completion Reports

Worked examples of the generic template (SKILL.md → *Step Completion Reports*) for each phase. Use these check names, and report only the checks the phase actually ran.

`M` is 8 in `create` mode. In `modify` mode, Phases 2-4 do not run and Phase 5 runs from step 2; number the reports in run order and write `modify` in the context. A skipped phase (for example, Phase 6 outside an ideas repo) gets one line, `Skipped: — [reason]`, and `Result: PASS`.

**Phase 1 — Setup & Validation**
```
◆ Setup (step 1 of 8 — environment validation)
··································································
  Repo Sync:                    √ pass (or — skipped, not a git repo)
  prd.md found:                 √ pass (1,840 words)
  Supporting docs:              √ pass (idea.md, validate.md)
  Web tools:                    √ pass (WebSearch, WebFetch)
  Run mode:                     √ create
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Phase 2 — Extract Context**
```
◆ Extract (step 2 of 8 — prd-reader)
··································································
  prd_extracted returned:       √ pass
  NFRs and constraints read:    √ pass (budget, timeline, team)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Phase 3 — Clarify Architecture**
```
◆ Clarify (step 3 of 8 — architecture decisions)
··································································
  Decisions answered by PRD:    √ 2/4 (deployment, database)
  Decisions asked:              √ 2/4 (auth, budget)
  Unanswered (TBD):             — 0
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Phase 4 — Research & Validation**
```
◆ Research (step 4 of 8 — validation rounds)
··································································
  Rounds returned:              √ 5/5 (tech, infra, security, risk, holistic)
  Rounds re-run:                — 0
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Phase 5 — Generate TAD**
```
◆ Generation (step 5 of 8 — TAD authoring)
··································································
  tad.md written:               √ pass
  Verification checks:          √ 6/6 (check 7 n/a)
  Sections regenerated:         — 0
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Phase 6 — README Maintenance**
```
◆ README (step 6 of 8 — ideas repo index)
··································································
  Index script:                 √ pass (or — absent, edited by hand)
  TAD status ✅:                √ pass
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Phase 7 — Commit and push**
```
◆ Commit (step 7 of 8 — git)
··································································
  Staged by path:               √ pass (tad.md, README.md)
  Committed:                    √ pass (a1b2c3d)
  Pushed:                       √ pass (or × fail — user declined)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Phase 8 — Output**
```
◆ Output (step 8 of 8 — Final Report)
··································································
  Final Report lines:           √ pass (Result, Evidence, Uncertainty, Decision, Next step)
  GitHub links:                 √ pass (or — omitted, not pushed)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```
