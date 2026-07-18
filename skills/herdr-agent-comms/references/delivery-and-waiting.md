# Delivery and waiting (Herdr)

Rationale for Phase 4–5 of `herdr-agent-comms`. Prefer Herdr agent-status waits over scrollback polling.

## Why status beats sleep

A fixed `sleep N` either wastes time or reads a half-written reply. Herdr already classifies panes:

| Status | Meaning |
|---|---|
| `working` | Agent is busy (spinner / tools) |
| `blocked` | Needs human input (trust, auth, permissions) |
| `done` | Finished; result not yet "seen" (usually background tab) |
| `idle` | Waiting for input; result considered seen or never worked |
| `unknown` | Not detected / no integration |

`herdr wait agent-status <pane_id> --status <state> [--timeout MS]` returns when the pane **is already** in that state or **transitions** into it. Timeouts exit non-zero (typically `1`).

## Delivery verification

After `pane run` / send:

1. Expect transition toward `working` within ~15s for a real task.
2. If still `idle`/`done` with no new transcript lines → likely not submitted → lone `enter`, then re-check.
3. If `blocked` → dialog ate focus; do not treat as delivered task.

```bash
herdr pane run "$pane" "do the thing"
if herdr wait agent-status "$pane" --status working --timeout 15000; then
  echo delivered
else
  herdr pane send-keys "$pane" enter
  herdr wait agent-status "$pane" --status working --timeout 10000 || echo NOT-DELIVERED
fi
```

On-screen text alone does not prove submission (typed but not Enter'd looks the same). Status `working` (or new output while leaving idle) is the reliable signal.

## Completion: idle vs done

Both mean "not working anymore." After a task:

- Background tab/workspace → often **`done`**
- Active tab with focused client → often **`idle`**
- Focusing the pane turns `done` → `idle`

Orchestrator pattern:

```bash
# Prefer done for background fleets; fall back to idle
herdr wait agent-status "$pane" --status done --timeout 180000 \
  || herdr wait agent-status "$pane" --status idle --timeout 5000
```

Or poll `herdr pane get` / `herdr agent get` and accept either terminal status when `agent_status` ∈ {`idle`,`done`} after you observed `working`.

## Blocked

`blocked` is **not** success. Typical causes: workspace trust, API key, permission prompt, plan-mode confirmation.

Rules:

- Never send the next task while blocked (it becomes menu input).
- `herdr agent focus <name>` so the human sees the dialog.
- After the human resolves it, re-check status, then continue.

## Timeouts and anti-deadloop

Set budgets before waiting:

| Budget | Suggested default |
|---|---|
| Boot to idle | 60s |
| Delivery → working | 15s |
| Task completion | 180s (tune per task) |
| Re-waits after timeout | max 2–3, then escalate |

On timeout:

1. `herdr pane get "$pane"`
2. `herdr pane read "$pane" --source recent-unwrapped --lines 80`
3. `herdr agent explain "$pane"` if status looks wrong
4. Report stall to the user — do **not** loop forever

## When status is `unknown`

Integrations missing or exotic CLI:

1. `herdr integration install <agent>` when supported
2. Fall back to content stability: `python3 scripts/wait_for_idle.py <pane_id>`
3. Still use capped `pane read` for the reply

The helper mirrors tmux-agent-comms' wait semantics (exit 0 idle / 2 timeout / 3 blocked markers) but reads via `herdr pane read` instead of `tmux capture-pane`.

## Concurrent fleet waits

Send all first, wait all second:

```bash
for p in "${panes[@]}"; do herdr pane run "$p" "$msg"; done
for p in "${panes[@]}"; do
  herdr wait agent-status "$p" --status done --timeout 180000 &
done
wait
```

Serializing full send→wait→read per agent makes total time the sum of agents; concurrent waits make it the max.

## Manual verify before high-stakes relay

Status is advisory relative to your goal. Before the user acts on a result:

```bash
herdr pane read "$pane" --source recent-unwrapped --lines 40 > /tmp/a.txt
sleep 3
herdr pane read "$pane" --source recent-unwrapped --lines 40 > /tmp/b.txt
cmp -s /tmp/a.txt /tmp/b.txt && echo stable || echo still-changing
```

Still-changing or spinner chrome → keep waiting. Stable + no blocked markers → safe to relay.
