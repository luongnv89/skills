# Step Completion Reports

Emit one after each phase. Use `√` pass, `×` fail, `—` for context.

## Phase 1 — Resolve & Gather Evidence

```
◆ Gather Evidence (step 1 of 3)
··································································
  Landing page resolved:   √ pass — <url | file path | auto-detected>
  Landing page fetched:    √ pass (via /browse) | × fail — <reason>
  Codebase located:        √ pass — <path>
  Pricing evidence found:  √ pass — <Stripe | Paddle | config | none>
  Extra instructions:      √ noted | — none
  ____________________________
  Result:                  PASS | PARTIAL | FAIL
```

## Phase 2 — Evaluate Against 32 Principles

```
◆ Evaluate (step 2 of 3)
··································································
  Principles scored:       √ 32/32
  Evidence cited per item: √ pass
  Low-confidence flagged:  √ <n> items tagged ⚠
  Virality Score:          — <NN>/100 (<Tier>)
  PASS/PART/FAIL:          — <a>/<b>/<c>
  ____________________________
  Result:                  PASS | PARTIAL | FAIL
```

## Phase 3 — Prioritize & Report

```
◆ Prioritize & Report (step 3 of 3)
··································································
  Fixes ordered by impact: √ pass
  Each fix is actionable:  √ pass — quotes current + proposed
  Strengths listed:        √ pass
  Caveats listed:          √ pass
  Report written:          √ pass — <file path> (always written, also printed inline)
  ____________________________
  Result:                  PASS | PARTIAL | FAIL
```
