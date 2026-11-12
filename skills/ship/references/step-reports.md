# Step Completion Reports

After completing each step, output a status report in this format:

```
◆ [Step Name] ([step N of 9] — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          √ pass (note if relevant)
  [Check 3]:          × fail — [reason]
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Adapt the check names to what the step actually validated. Use `√` for pass, `×` for fail, and `—` to add brief context. The `Criteria` line counts the acceptance checks met. The `Result` line gives the verdict. A step that auto mode decided, rather than the user, says so in its context note (for example `— auto: minor bump`).

## Step-specific checks

### Step 1 — Pre-flight
```
◆ Pre-flight (step 1 of 9 — repo state)
··································································
  Mode:                     — auto | interactive (--no-auto)
  Scope:                    — full release | notes | bump
  Working tree clean:       √ pass (git status --porcelain empty)
  Default branch:           √ pass (main)
  Resume:                   — no | yes (HEAD carries v1.3.0)
  Synced with origin:       √ pass (git pull --rebase clean)
  Release tool / monorepo:  — none detected | <tool> (auto: BLOCKED; interactive: ask)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

### Step 2 — Version
```
◆ Version (step 2 of 9 — next release)
··································································
  Last tag:                 — v1.2.3
  Version chosen:           √ v1.3.0 (rule: feat commits → minor | argument | version file ahead)
  Tag free:                 √ pass (no local or remote v1.3.0)
  Registries:               √ npm: publish (1.3.0 not yet published) | — PyPI: not a published package
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

### Steps 3-4 — Prepare and Review
```
◆ Prepare and Review (steps 3-4 of 9 — proposals)
··································································
  Version sources found:    √ N files (D drifted)
  Changelog + user notes:   √ pass (N commits categorized; Unreleased promoted | new entry)
  Docs proposals:           √ N files
  Landing page:             — version updated · changelog updated · features current · docs not on page | none
  Reviewer:                 √ PASS | × NEEDS_FIX (fixed, re-review PASS)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

### Step 5 — Apply and Sweep
```
◆ Apply and Sweep (step 5 of 9 — every place)
··································································
  Proposals applied:        √ N edits (S skipped: old line no longer matched)
  Version sources:          √ all N read 1.3.0
  Old-version sweep:        √ 0 missed (H historical, D dependency, F fixture)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

### Steps 6-9 — Build and Deliver
```
◆ Build and Deliver (steps 6-9 of 9 — release delivery)
··································································
  Build:                    √ pass | — no build step
  Release commit:           √ pass (git status --porcelain --untracked-files=no empty)
  Tag pushed:               √ pass (git ls-remote shows v1.3.0)
  GitHub release:           √ pass (URL: ...) | — skipped: <reason>
  Package published:        √ pass (npm view returned 1.3.0) | — skipped: <reason>
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```
