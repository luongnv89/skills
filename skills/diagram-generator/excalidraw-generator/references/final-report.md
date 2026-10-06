# Final Report — examples and fill rules

Read this when writing the Final Report (SKILL.md → *Final Report*). SKILL.md owns the status rules; this file shows filled examples and how to fill each line. The report is compact text in chat; the `.excalidraw` file is the artifact.

## Examples

`COMPLETE`:

```
Result: COMPLETE. Wrote microservices-architecture.excalidraw (9 shapes, 9 text labels, 11 arrows).
Evidence: /Users/me/project/docs/microservices-architecture.excalidraw. Validation 10/10 checks passed
  (inline, 2 cycles: cycle 1 grew svc-payment height 50 -> 76, check 10). sync: pulled origin/main, clean tree.
Uncertainty: Not opened in Excalidraw; rendering is untested. Inferred that the gateway calls every
  service from "API Gateway in front"; drawn as gateway -> each service.
Decision: No approval needed.
```

`PARTIAL`:

```
Result: PARTIAL. Wrote ml-mind-map.excalidraw (13 shapes, 13 text labels, 12 arrows); check 7 failed.
Evidence: /Users/me/ml-mind-map.excalidraw. Validation 9/10 checks passed after 3 cycles.
  Failed: 7 (node-transformer overlaps node-rnn by 18px). sync: failed (fetch: Could not resolve host).
Uncertainty: The overlap may be acceptable once opened in Excalidraw; not opened to confirm.
  The repo was not synced before the write.
Decision: No approval needed. Optional: say "spread the Deep Learning branch" to run one more cycle.
```

`BLOCKED`:

```
Result: BLOCKED. No file written; check 5 (two-way arrow bindings) still failed after 3 cycles.
Evidence: Validation 7/10 checks passed. Check 5: arrow arr-auth-redis binds to svc-redis,
  which has no matching boundElements entry; checks 6 and 10 also failed.
Uncertainty: Checks 7-10 ran on a partly invalid model; their results may change after the fix.
Decision: Choose one: retry generation from the confirmed plan, or simplify the plan
  (for example, split the 60-element canvas into one file per subsystem).
```

## Fill rules

| Line | Fill rule |
|------|-----------|
| `Result:` | Status first. For `COMPLETE` and `PARTIAL`, the file name and the shape, text-label and arrow counts from the last validation report; add the companion `.md` name when one was written. For `PARTIAL`, the failed check numbers. For `BLOCKED`, the phase or check that stopped the run, and `No file written`. |
| `Evidence:` | The absolute path of the written file. The `N/10` count from the last check run, the mode (inline or subagent loop) and the cycle count. Each failed check with the element ID it names. The Repo Sync outcome (pulled, `skipped` with the reason, or `failed` with the first error line). |
| `Uncertainty:` | Always: whether the file was opened in Excalidraw (normally untested). Every layout, style or entity choice the request did not state, labeled as an assumption or inference. A `sync: failed` outcome. Write `none beyond the untested rendering` only when nothing else applies. |
| `Decision:` | `No approval needed.` when the file is written. On `BLOCKED` or a Phase 1–2 stop, the exact question the run is waiting on. Name an optional follow-up separately. |

Match each claim to the scope of its evidence. A passing check 1 supports "the JSON parses", not "it renders correctly in Excalidraw". Check 10 uses an approximate pixel width per character, so a pass does not prove text never wraps. Check 8 is the agent's own comparison against the request; it is not the user's confirmation that nothing is missing.

## Reader checks

Use these when reviewing a run's Final Report, in addition to the correctness items in SKILL.md → *Acceptance Criteria*:

| Check | Pass when |
|-------|-----------|
| Result is findable | The first line states the status and the file name (or `No file written`) without reading the JSON. |
| Facts and assumptions are separated | Verified claims name a check that ran; inferred layout or entity choices, a failed sync, and untested rendering are on the `Uncertainty:` line. |
| Claims are traceable | The file path, the `N/10` count and each failed check's element ID support the `Result:` line. |
| Next decision is clear | The `Decision:` line names the pending question or says `No approval needed.` |

A heading's presence alone does not pass a check. Ask a human reviewer the same four questions. If no reviewer answers, record human understanding as unconfirmed; agent inspection cannot confirm it. Negative-trigger cases in `evals/evals.json` are excluded from these checks.
