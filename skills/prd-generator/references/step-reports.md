# Step Completion Reports — per-phase check names

Moved verbatim out of `SKILL.md` to keep the body inside the context budget. The generic
report format and its `√` / `×` / `—` legend stay in `SKILL.md` under
`## Step Completion Reports`; this file holds the phase-specific check names.

Emit one block after each of the seven workflow phases. The `step N of 7` label is fixed —
the workflow has seven phases, and a run that stops after Phase 5 has skipped README
maintenance and commit/push.

### Phase-specific checks

**Phase 1 — Validate Input**
```
◆ Validate Input (step 1 of 7 — input resolution)
··································································
  Input files found:        √ pass
  Dependencies resolved:    √ pass (PROJECT_DIR confirmed)
  Backup created:           √ pass | — skipped (no existing prd.md)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Phase 2 — Extract Context**
```
◆ Extract Context (step 2 of 7 — context extraction)
··································································
  idea.md parsed:           √ pass (concept + technical context read)
  validate.md parsed:       √ pass (verdict + ratings extracted)
  Context extracted:        √ pass (idea.md + validate.md read)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Phase 3 — Clarify Requirements**
```
◆ Clarify Requirements (step 3 of 7 — requirements gathering)
··································································
  Questions answered:       √ pass
  Scope defined:            √ pass (MVP timeframe confirmed)
  Stakeholders identified:  √ pass (team size, compliance noted)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Phase 4 — Generate PRD**
```
◆ Generate PRD (step 4 of 7 — document generation)
··································································
  10 sections written:      √ pass
  prd.md created:           √ pass
  Cross-references valid:   √ pass (mermaid diagrams render)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Phase 5 — Output**
```
◆ Output (step 5 of 7 — delivery)
··································································
  File written:             √ pass
  Summary presented:        √ pass
  Next steps suggested:     √ pass
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```
**Phase 6 — README Maintenance (ideas repo)**
```
◆ README Maintenance (step 6 of 7 — ideas index)
··································································
  Ideas repo detected:      √ pass | — skipped (not an ideas repo)
  Index updated:            √ pass (update_readme_ideas_index.py) | √ pass (manual)
  PRD status now ✅:         √ pass
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Phase 7 — Commit and push**
```
◆ Commit and push (step 7 of 7 — delivery to remote)
··································································
  Changes committed:        √ pass
  Push confirmed by user:   √ pass
  Push succeeded:           √ pass (rebased on origin/main if rejected)
  GitHub links reported:    √ pass (prd.md, README.md, commit hash)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```
