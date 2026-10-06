# Context Gate — /issue-work-loop

Best-effort gate: FRESHEN a reusable worker when its probed context-window usage is at or above `work_loop.context_threshold` (default 50%). Herdr does not expose normalized usage for every CLI, so use the worker probe and conservative UNKNOWN fallback.

## Gate points

| Mode / role | When |
|---|---|
| Both — reviewer | Start of every review ROUND, including ROUND 1 |
| ISSUE — implementer | Immediately before every fix; skip fresh initial resolve |
| PR — FIXER | Immediately before every fix after it exists; its first lazy spawn is already fresh |

Never gate or spawn a writer before a CLEAN exit. In PR mode, never gate/spawn FIXER before FINDINGS plus push-safety PASS.

## Probe and decision

Send the Context probe from `agent-prompts.md`. Parse `CONTEXT: P%` or `CONTEXT: UNKNOWN`; minor case/spacing variants are acceptable.

| Result | Action |
|---|---|
| Integer `P >= threshold` | FRESHEN |
| Integer `P < threshold` | Reuse |
| UNKNOWN, unparseable, or timeout | Apply role fallback below |

Invalid threshold uses 50 and prints one warning. Threshold must be 1–99.

## FRESHEN procedure

1. Record compact state: `mode`, `issue_context`, `pr_number`, `pr_url`, `head_ref`, current `head_sha`, FINDINGS, role, isolated FIXER worktree path if any.
2. Close only that worker pane; never close the root orchestrator pane.
3. Re-spawn the same configured role name; if occupied, append an epoch and update tracked pane state.
4. Wait for readiness.
5. Send the matching compact handoff from `agent-prompts.md`.
6. Re-verify current PR head before review/fix.

Do not paste transcripts, full diffs, or issue/PR bodies. FRESHEN never authorizes a new PR, merge, force-push, primary-checkout mutation, or `/issue-resolver` during a fix.

## UNKNOWN fallback

| Role | Fallback |
|---|---|
| Reviewer | Fresh spawn on ROUND 1 may be reused; FRESHEN before every later ROUND |
| ISSUE implementer | After initial full resolve, FRESHEN before first fix; otherwise reuse first short fix, then FRESHEN before ROUND 3+ |
| PR FIXER | Initial lazy spawn is fresh; reuse first fix; FRESHEN before each later fix when usage remains UNKNOWN |

Also FRESHEN after truncated/confused output. Cap UNKNOWN-driven churn at two consecutive FRESHENs per role; after that, reuse and print:

```text
⚠ Context UNKNOWN — freshen cap reached; reusing {role}
```

Log every UNKNOWN choice:

```text
⚠ Context UNKNOWN for {role} — fallback: {reuse|freshen} ({reason})
```

## Done when

Before work dispatch, the report records a parsed percentage or explicit UNKNOWN fallback; any FRESHEN has a new ready pane id and compact state; current GitHub head still matches the task SHA.
