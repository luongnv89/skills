# Herdr desktop app vs Herdr TUI — hc-agent and herdr-agent

Read this to answer "what differs from herdr-agent", or before relying on an operation that behaves differently in the desktop app. **herdr-agent** drives the Herdr TUI through the `herdr` CLI (`HERDR_ENV=1`). **hc-agent** drives the Herdr desktop app through `hc` (herdr-core) and `herdr-app` (`HC_TERMINAL_ID` set, `HERDR_ENV` unset). Both are supported; each refuses the other's environment.

Never call `herdr` from an app terminal. It is on PATH there, but it talks to the separate TUI server: from an app terminal, `herdr pane current --current` returned a pane of another project.

## Observed versions

Checked live on 2026-11-11 with hc 0.1.20 and Herdr.app 0.1.15 on macOS, one command at a time. The hc-agent scripts themselves have not been run against a live app: their tests use fakes built from those captures. Linux and Windows were not tested.

## Operation by operation

| Operation | herdr-agent (TUI) | hc-agent (app) | Verdict |
|---|---|---|---|
| `help` | Answers from `references/help-request.md`, runs nothing | Same | same |
| Route to the right skill | Stops when `HC_TERMINAL_ID` is set without `HERDR_ENV` | Stops when `HERDR_ENV=1` | same rule, mirrored |
| Resolve root | `herdr status`, `HERDR_PANE_ID` / `TAB_ID` / `WORKSPACE_ID` | `agent.py check`: `hc get $HC_TERMINAL_ID` labels `herdr.space` / `herdr.tab`, pane from `herdr-app ls` | different |
| Spawn beside root | `next_grid_split.py`, `herdr pane split --no-focus`, `herdr agent start` | `launch_profile.py --start`: `herdr-app do pane.split --direction right --pane <explicit> --argv <json>` | different |
| Keep focus on root while spawning | `--no-focus` on the split | The split takes focus; `--start` snapshots `focused_pane` from `herdr-app status` first and restores it with `herdr-app do pane.focus` | different |
| Which pane to split | The current rightmost pane, from layout geometry | The newest hc-agent pane in the tab, else root: the app reports no geometry | different |
| Equal column widths | Resized by the equalizer to within one cell | App-managed: no pane resize or split ratio exists. Two columns came out equal (155 → 75/75); three or more are unverified | different (weaker) |
| Worker identity | Pane rename, agent name, `HERDR_ROLE` env | `hc label <t> hc-agent.role=worker hc-agent.name=<name> hc-agent.space=… hc-agent.tab=…`; no rename, no env (pane.split takes neither) | different |
| Worker folder | `--cwd` on the split | `/bin/sh -c 'cd "$0" && exec "$@"' <dir> …` around the argv; `--start` reports the folder hc sees | different |
| Readiness | `herdr agent start` returns when the agent is interactive | `--start` polls `hc get` until `idle` or `done` (exit 3 on `blocked`) | different |
| Launch-profile inheritance | Root argv from `herdr pane process-info` | Root argv from `hc get` `foreground.argv`; a wrapper such as `mcc run --` is kept as the worker's prefix | different |
| Badges | `badge.py` → `herdr pane report-metadata` | — no metadata or badge command in the app | unavailable |
| Notifications | `herdr notification show … --sound` | — no notification command; tell the user in chat | unavailable |
| Resolve one target | `herdr agent get <name>` | `agent.py get <name>`: the exact `hc-agent.name` label in the root's tab, then its `t…` address | different |
| Prompt with preflight | `preflight_send.py` + `herdr agent prompt --wait` | `agent.py prompt`: `hc get` preflight, `hc send --if idle` (plain send for `done`/`error`), then waits for this turn | different |
| Error names | `agent_blocked`, `agent_prompt_stalled`, `timeout` | outcomes `blocked`, `stalled`, `timeout` with exit codes 3, 7, 8 | different names, same meaning |
| Wait without sending | `herdr agent wait`, `wait_for_idle.py` | `agent.py wait [--until blocked]`, which blocks in `hc wait` while the agent works | different |
| Read reply deltas | `herdr agent read --source recent-unwrapped --lines 80` | `agent.py read --turn <id>` over `hc read --lines 400` | different |
| Long-reply file fallback | Ask for a file, read the path | Same | same |
| Fleet status | `fleet_status.py` over one `herdr api snapshot` (atomic) | `agent.py fleet`: `herdr-app ls` for the tab, one `hc get` per terminal (polled, not atomic) | different |
| Broadcast | `broadcast.sh` | `agent.py broadcast`, plus `agent.py dispatch` for a task per worker | different |
| Focus / steer | `herdr agent focus <name>`, which also marks the completion seen | `agent.py focus <name>` → `herdr-app do agent.focus --terminal <t>`; whether the app marks anything seen is unverified | different |
| Human takeover | Focus the pane; prefix + q detaches | Focus the pane, or `hc attach <t>` in the user's own terminal; ctrl+\ detaches | different |
| No-agent pane fallback | Pane-surface `pane run` / `send-keys` | — refused: a terminal without OSC 7501 status is unverifiable, never typed into | unavailable |
| Unknown-status diagnosis | `herdr agent explain`, `herdr integration status` | — not in the app; read the screen with `hc read <t> --lines 40` | unavailable |
| Teardown | `herdr pane close` on worker panes after confirmation | `agent.py close <names> --confirmed` → `herdr-app do pane.close`, only `hc-agent.role=worker` terminals in the root's tab | different |
| Never stop the server | `herdr server stop` forbidden | Never stop or restart the hc core or quit the app | same rule |
| HANDOFF | Successor `main-g<N>` via the spawn path, brief, ack | Same contract, plus a `GO` after the ack (as rex-agent); the successor is a `pane.split` terminal with no parent, so it outlives the old root; labeled `hc-agent.role=main` so teardown skips it | same contract |
| Context gate | Three gate points, 50% default, UNKNOWN counters | Same | same |
| Final report | Result / Evidence / Uncertainty / Decision | Same | same |
| Timeouts | Milliseconds | Seconds (hc's unit) | different |

## Verified live

- App terminals set `HC_TERMINAL_ID`, `HC_SCOPE` and `HC_TERMINAL_SOCKET`, and none of `HERDR_ENV`, `HERDR_PANE_ID`, `HERDR_TAB_ID` or `HERDR_WORKSPACE_ID`.
- The shapes of `hc get --json`, `hc ls --json` (no labels in its rows), `herdr-app ls` and `herdr-app status`, and errors as `{"error": {kind, message, hint}}` on stderr with exit codes 3, 7, 9, 10 and 11.
- `herdr-app do pane.split --direction right --pane <p> --argv '<json>'` returns `{"pane", "terminal"}`, moves focus to the new pane, and `herdr-app do pane.focus --pane <p>` moves it back.
- A `pane.split` terminal has `parent: null` and `die_with_parent: false`.
- `hc send <t> <text>` replies `{"started", "status", "turn"}`; `hc send --if idle` on a terminal with no status exits 10 (`status_mismatch`) and types nothing.
- `hc read --lines N` prints screen plus history; `herdr-app do pane.close --pane <p>` returns `{"ok": true}` and the terminal finishes.

## Unverified

- End to end: no hc-agent script has run against the live app. Every row above marked different rests on the single commands listed under *Verified live* plus the fakes.
- `herdr.space` / `herdr.tab` labels on a `pane.split` terminal. `agent.py check` requires them on root, so a HANDOFF successor, which becomes root, depends on them. Fleet membership itself comes from `herdr-app ls`, not from these labels.
- Argument order: `hc send --json --if idle -- <t> <text>` (the `--` separator) and `hc label --json <t> k=v…` were not run; the smoke test used `hc send <t> <text>`.
- A full prompt cycle on a live agent through `hc send`: the `working` → `done` transition, when `turn` increments, and the output shapes of `hc wait` and `hc send --wait` (the scripts decide from `hc get` and ignore both).
- Column sizing with three or more columns, and splitting a worker pane instead of root.
- The `mcc run --` wrapper as a worker prefix: whether the wrapper re-adds flags the worker also carries, and whether a doubled `--model` is accepted.
- Linux and Windows: the environment variables, `/bin/sh` for the folder wrapper, and install paths.
- `hc` and `herdr-app` on PATH by default (observed in `~/.local/bin` only).
- Whether the window renders `hc-agent.*` labels anywhere, and whether `hc ls --label` matches labels set by `hc label` (documented by `hc ls --help`, not exercised).
- Multi-line text through `hc send` (it pastes, per its help; bracketed paste was not observed). The turn tag goes on the task's last line, so a one-line task stays one line.
- `herdr-app do agent.focus` on a terminal without agent status (the script falls back to `pane.focus`).
- The terminal address format: every address seen was `t` plus a digit and base-36 characters (`t7`, `t2x`, `t999`).
