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

### Step 1 — Pre-flight
```
◆ Pre-flight (step 1 of 10 — repo state)
··································································
  Working tree clean:       √ pass (git status --porcelain empty)
  Synced with origin:       √ pass (git status -sb not behind)
  Release tool:             — none detected | <tool> (deferring)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

### Steps 2-3 — Version Bump
```
◆ Version Bump (step 3 of 10 — version consistency)
··································································
  Files updated:            √ pass (N files changed)
  Version consistent:       √ pass (all files match vX.Y.Z)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

### Step 4 — Changelog
```
◆ Changelog (step 4 of 10 — release notes)
··································································
  Changes extracted:        √ pass (N commits categorized)
  Notes formatted:          √ pass (conventional commit format)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

### Steps 7-10 — Build & Publish
```
◆ Build & Publish (step 7-10 of 10 — release delivery)
··································································
  Build success:            √ pass
  Tag created:              √ pass (vX.Y.Z annotated tag)
  Tag pushed:               √ pass (git ls-remote shows vX.Y.Z)
  Package published:        √ pass (PyPI | npm | skipped)
  GitHub release created:   √ pass (URL: ...)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```
