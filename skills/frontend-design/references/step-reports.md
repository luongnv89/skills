# Step Completion Reports

After completing each major step in the frontend-design skill, output a status report in this format:

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

### Design Thinking

```
◆ Design Thinking (step 1 of 2 — [component/page type])
··································································
  Purpose understood:       √ pass (problem and audience identified)
  Tone identified:          √ pass ([aesthetic direction] chosen)
  Differentiation clear:    √ pass | × fail — [what's missing]
  Style source:             √ explicit brief | √ Default Style Guide
  Files listed:             √ pass ([N] files) | — not applicable (new project)
  Interaction source:       √ [native element | existing library | UI SDK <version> (beta) | hand-written APG], per part when they differ (e.g. menu: UI SDK 0.1.0-beta.2; FAQ: native) | — no interactive part
  ____________________________
  Result:                   PASS | FAIL | PARTIAL
```

### Implementation

```
◆ Implementation (step 2 of 2 — [component/page type])
··································································
  Style guide applied:      √ pass | × fail — [deviations noted]
  Responsive check:         √ pass (375/768/1280 px) | × fail — [width, element] | — untested (no browser)
  Contrast check:           √ pass (lowest [ratio]) | × fail — [pair, ratio, file:line]
  Quality + usability:      √ pass | × fail — [which item failed]
  Keyboard walk:            √ pass ([N] interactive parts) | × fail — [part, key] | — untested (no browser) | — no interactive part
  Build:                    √ pass ([command]) | × fail — [first error line] | — not run (no command)
  ____________________________
  Result:                   PASS | FAIL | PARTIAL
```

`Result: PASS` when no check failed, `PARTIAL` when a check still fails after the second fix cycle, `FAIL` when no code was written. The Final Report (`references/final-report.md`) follows this report and closes the run.
