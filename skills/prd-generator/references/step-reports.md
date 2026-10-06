# Step Completion Reports — per-phase check names

The generic report format and its `√` / `×` / `—` legend stay in `SKILL.md` under
`## Step Completion Reports`; this file holds the phase-specific check names.

Emit one block after each workflow phase that ran. The `step N of 7` label is fixed:
the workflow has seven phases. A `modify` run emits no blocks for Phases 2-4 (Modification
Mode replaces them) and reports its changes in the Phase 5 block. A run outside an ideas
repo emits Phases 6-7 as `— skipped` lines with the reason.

### Phase-specific checks

**Phase 1 — Validate Input**
```
◆ Validate Input (step 1 of 7 — input resolution)
··································································
  Input files found:        √ pass
  Dependencies resolved:    √ pass (PROJECT_DIR confirmed)
  Repo synced:              √ pass | — skipped (not a git repository)
  Verdict checked:          √ pass (verdict: <token>) | × fail — user did not confirm
  Run mode:                 √ create | √ modify
  Backup created:           √ pass (non-empty) | — skipped (no existing prd.md)
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
  Questions asked:          √ pass (N asked, M skipped as answered by inputs)
  Unanswered recorded:      √ pass (K recorded as TBD in §9) | — none
  Compliance stated:        √ pass (named by user or inputs) | — TBD
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

**Phase 5 — Verify and Output**
```
◆ Verify and Output (step 5 of 7 — verification)
··································································
  File written:             √ pass
  Verification checks:      √ N/N passed | × fail — <check> after one regeneration
  Modifications applied:    √ pass (modify mode) | — n/a (create mode)
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
  Staged by path:           √ pass (git diff --cached --name-only matches)
  Changes committed:        √ pass (<hash>)
  Push confirmed by user:   √ pass | × fail — user declined
  Push succeeded:           √ pass (rebased on origin/<branch> if rejected) | × fail — rejected twice
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```
