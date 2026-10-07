# Step Completion Reports

Emit one report after each phase, so pass/fail is scannable without reading the
transcript.

## Format

```
◆ Phase <N> — <name> (step <N> of 4 — <resolved-url>[ · orchestrated-by: <name>])
··································································
  <check>:            √ pass
  <check>:            × fail — <reason>
  <check>:            — n/a (<reason>)
  Criteria:           √ <n>/<n> met
  ____________________________
  Result:             PASS | PARTIAL | FAIL
```

- `√` is pass, `×` is fail, `—` is not applicable with a reason.
- The header names the resolved URL. In an orchestrated run it also names the
  orchestrator from the `orchestrated-by` line, per `orchestrated-runs.md`.
- Every check is tied to a command, a file state, or a count — never an adjective.

## Result words

- `PASS` — every check of that phase's Acceptance Criteria row holds.
- `PARTIAL` — the phase ended with a recorded gap, such as an empty `fixes.md` leaving
  checks with only the `nextLevel` prompt.
- `FAIL` — a check is blocked and the run cannot continue; the run then closes
  `BLOCKED` when nothing was produced (see `final-report.md`).

## Example

```
◆ Phase 2 — Triage (step 2 of 4 — https://example.com)
··································································
  Scan parsed:        √ pass
  Fix prose joined:   √ pass (17/17 by position)
  Phases assigned:    √ pass — P0:1 P1:3 P3:8 P4:5
  Commerce deferred:  — n/a (isCommerce true)
  Criteria:           √ 2/2 met
  ____________________________
  Result:             PASS
```
