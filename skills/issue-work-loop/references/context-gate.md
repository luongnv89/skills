# Context Gate — /issue-work-loop

Best-effort gate: if a worker is already ≥ **50%** context (configurable via `work_loop.context_threshold`) at the **start of a new ROUND**, **FRESHEN** it before assigning work.

This is not a perfect token meter. Herdr does not expose a normalized context percentage for every CLI. Prefer an explicit agent report; fall back to conservative heuristics when the report is `UNKNOWN`.

## When to run

| Role | When |
|------|------|
| Implementer | Start of every fix ROUND (Phase 5a). Skip on first initial resolve if the pane just booted. |
| Reviewer | Start of every review ROUND (including ROUND 1 after spawn — usually pass; still probe if the pane is reused). |

Never skip the gate after a long prior ROUND on the same pane.

## Probe

Send the **Context probe** from `references/agent-prompts.md` via herdr Phase 4→5 (short timeout is fine — e.g. 60s). Parse the first matching line:

```
CONTEXT: 42%
CONTEXT: UNKNOWN
```

Accept minor variants: `Context: 42%`, `CONTEXT 42%`, `context usage: 42%` → normalize to integer percent.

## Decision table

| Report | Action |
|--------|--------|
| Integer `P` where `P ≥ threshold` (default 50) | **FRESHEN** |
| Integer `P` where `P < threshold` | Reuse pane |
| `UNKNOWN` | Apply **UNKNOWN fallback** below |
| Unparseable / timeout | Treat as `UNKNOWN` |

## FRESHEN procedure

1. Record compact state: `issue_number`, `pr_number`, `pr_url`, `branch_name`, `head_sha`, current FINDINGS (if any), role name.
2. Confirm teardown of that worker only (orchestrator may auto-close workers it spawned — do not close root). Prefer:

   ```bash
   herdr pane close "$worker_pane"
   ```

3. Re-spawn the same role name (if name still taken, append `-<epoch>` and update the handle) using `herdr-agent-comms` Phase 2.
4. Wait for readiness (`--ready`).
5. Send the **compact handoff** prompt for that role from `references/agent-prompts.md`.
6. Proceed with the ROUND task (review or fix).

Do **not** paste full prior transcripts, full diffs, or entire issue bodies into the handoff — only identifiers + FINDINGS list.

## UNKNOWN fallback

When the agent cannot report context %:

| Role | Fallback |
|------|----------|
| **Reviewer** | FRESHEN every ROUND after ROUND 1 (independent eyes preferred). ROUND 1 after a fresh spawn: reuse. |
| **Implementer** | If the last task was a full resolve (Phase 3), **FRESHEN before the first fix**. Otherwise reuse the first fix ROUND, then FRESHEN before `round >= 3`. Also FRESHEN when the last implementer reply was truncated or the agent reports confusion about prior state. |

**Cap thrash:** at most **2 consecutive UNKNOWN-driven FRESHENs** per role per loop. After the cap, reuse the pane, print `⚠ Context UNKNOWN — freshen cap reached; reusing {role}`, and proceed.

Log every fallback choice:

```
⚠ Context UNKNOWN for {role} — fallback: {reuse|freshen} ({reason})
```

## Threshold override

- Config: `work_loop.context_threshold` (integer 1–99, default 50)
- Do not treat 0 or 100 as special beyond the comparison
- If config is invalid, use 50 and print a `⚠` once

## What FRESHEN is not

- Not `/compact` inside the same session (optional extra if the CLI supports it, but the skill's required path is pane restart)
- Not a reason to re-run full `/issue-resolver`
- Not a reason to open a new PR
- Not applied to the root orchestrator pane
