# Final Report — examples and fill rules

Read this when writing the Final Report (SKILL.md → *Final Report*). SKILL.md owns the status rules; this file shows filled examples and how to fill each line. The report is compact text in chat; the `.drawio` file is the artifact.

## Examples

`COMPLETE`:

```
Result: COMPLETE. Wrote system-architecture.drawio (3 pages, 24 shapes, 31 edges, 4 containers).
Evidence: /Users/me/project/docs/system-architecture.drawio. Validation 9/9 checks passed
  (subagent loop, 2 cycles: cycle 1 fixed 2 overlaps, check 6). sync: pulled origin/main, clean tree.
Uncertainty: Not opened in draw.io; rendering is untested. Inferred that Redis is a cache,
  not a queue, from "used by Auth"; it is drawn as a cache.
Decision: No approval needed.
```

`PARTIAL`:

```
Result: PARTIAL. Wrote ci-pipeline.drawio (1 page, 14 shapes, 13 edges, 3 lanes); check 9 failed.
Evidence: /Users/me/ci-pipeline.drawio. Validation 8/9 checks passed after 3 cycles.
  Failed: 9 (node-run-integration-tests label overflows at 160x40).
Uncertainty: The overflowing label may wrap acceptably in draw.io; not opened to confirm.
Decision: No approval needed. Optional: shorten the label or say "widen it" to run one more cycle.
```

`BLOCKED`:

```
Result: BLOCKED. No file written; check 1 (XML structure) still failed after 3 cycles.
Evidence: Validation 4/9 checks passed. Check 1: page "Container" is missing system cell id="1".
Uncertainty: Checks 2-9 were run on a partly invalid model; their results may change after the fix.
Decision: Choose one: retry generation from the confirmed plan, or simplify the plan
  (for example, one page per C4 level instead of one 60-element page).
```

## Fill rules

| Line | Fill rule |
|------|-----------|
| `Result:` | Status first. For `COMPLETE` and `PARTIAL`, the file name and the page, shape, edge and container counts from the last validation report. For `PARTIAL`, the failed check numbers. For `BLOCKED`, the phase or check that stopped the run, and `No file written`. |
| `Evidence:` | The absolute path of the written file. The `N/9` count from the last check run, the mode (inline or subagent loop) and the cycle count. Each failed check with the element ID it names. The Repo Sync outcome (pulled, or `skipped` with the reason). |
| `Uncertainty:` | Always: whether the file was opened in draw.io (normally untested). Every layout, style or entity choice the request did not state, labeled as an assumption or inference. Write `none beyond the untested rendering` only when nothing else applies. |
| `Decision:` | `No approval needed.` when the file is written. On `BLOCKED` or a Phase 1–2 stop, the exact question the run is waiting on. Name an optional follow-up separately. |

Match each claim to the scope of its evidence. A passing check 1 supports "the XML parses", not "it renders correctly in draw.io". Check 8 is the agent's own comparison against the request; it is not the user's confirmation that nothing is missing.

## Reader checks

Use these when reviewing a run's Final Report, in addition to the correctness items in SKILL.md → *Acceptance Criteria*:

| Check | Pass when |
|-------|-----------|
| Result is findable | The first line states the status and the file name (or `No file written`) without reading the XML. |
| Facts and assumptions are separated | Verified claims name a check that ran; inferred layout or entity choices and untested rendering are on the `Uncertainty:` line. |
| Claims are traceable | The file path, the `N/9` count and each failed check's element ID support the `Result:` line. |
| Next decision is clear | The `Decision:` line names the pending question or says `No approval needed.` |

A heading's presence alone does not pass a check. Ask a human reviewer the same four questions. If no reviewer answers, record human understanding as unconfirmed; agent inspection cannot confirm it. Negative-trigger cases in `evals/evals.json` are excluded from these checks.
