# Herdr desktop app vs Herdr TUI — hc-agent and herdr-agent

Read this to answer "what differs from herdr-agent", or before relying on an operation that behaves differently in the desktop app. **herdr-agent** drives the Herdr TUI through the `herdr` CLI (`HERDR_ENV=1`). **hc-agent** drives the Herdr desktop app through `hc` (herdr-core) and `herdr-app` (`HC_TERMINAL_ID` set, `HERDR_ENV` unset). Both are supported; each refuses the other's environment.

Never call `herdr` from an app terminal. It is on PATH there, but it talks to the separate TUI server: from an app terminal, `herdr pane current --current` returned a pane of another project.

## Observed versions

Checked live on 2026-11-11 with hc 0.1.20 and Herdr.app 0.1.15 on macOS: first single commands one at a time, then one end-to-end run of the scripts with a Claude Code worker started through the `mcc run --` wrapper. The unit tests use fakes built from those captures. Linux and Windows were not tested.

## Operation by operation

| Operation | herdr-agent (TUI) | hc-agent (app) | Verdict |
|---|---|---|---|
| `help` | Answers from `references/help-request.md`, runs nothing | Same | same |
| Route to the right skill | Stops when `HC_TERMINAL_ID` is set without `HERDR_ENV` | Stops when `HERDR_ENV=1` | same rule, mirrored |
| Resolve root | `herdr status`, `HERDR_PANE_ID` / `TAB_ID` / `WORKSPACE_ID` | `agent.py check`: `hc get $HC_TERMINAL_ID` labels `herdr.space` / `herdr.tab`, pane from `herdr-app ls` | different |
| Spawn beside root | `next_grid_split.py`, `herdr pane split --no-focus`, `herdr agent start` | `launch_profile.py --start`: `herdr-app do pane.split --direction right --pane <explicit> --argv <json>` | different |
| Tab per agent | `herdr tab create … --no-focus`, then `launch_profile.py --start` in its root pane | — `herdr-app do tab.new` exists, but `fleet`, `prompt` and `close` only see the root's tab and refuse anything outside it | unavailable |
| Log or shell pane in the grid | `next_grid_split.py`, `herdr pane split`, `herdr pane run <pane> "tail -f …"` | No script: `herdr-app do pane.split --direction right --pane <p> --argv '["tail","-f","<log>"]'` starts the program as the pane's own process (nothing is typed), then `herdr-app do pane.focus --pane <saved>`. It carries no `hc-agent.*` label, so `fleet` lists it as `other` and `close` never closes it. Not run live | different |
| Keep focus on root while spawning | `--no-focus` on the split | The split takes focus; `--start` snapshots `focused_pane` from `herdr-app status` first and restores it with `herdr-app do pane.focus` | different |
| Which pane to split | The current rightmost pane, from layout geometry | The newest hc-agent pane in the tab, else root: the app reports no geometry | different |
| Equal column widths | `next_grid_split.py --equalize` over `herdr pane layout` / `herdr pane resize`, to within one cell | App-managed: no pane resize or split ratio exists. Two columns came out equal (155 → 75/75); three or more are unverified | different (weaker) |
| Worker identity | `herdr pane rename`, agent name, `HERDR_ROLE` env | `hc label <t> hc-agent.role=worker hc-agent.name=<name> hc-agent.space=… hc-agent.tab=…`; no rename, no env (pane.split takes neither) | different |
| Worker folder | `--cwd` on the split | `/bin/sh -c 'cd "$0" && exec "$@"' <dir> …` around the argv; `--start` reports the folder hc sees | different |
| Readiness | `herdr agent start` returns when the agent is interactive | `--start` polls `hc get` until `idle` or `done` (exit 3 on `blocked`) | different |
| Launch-profile inheritance | Root argv from `herdr pane process-info` | Root argv from `hc get` `foreground.argv`; a wrapper such as `mcc run --` is kept as the worker's prefix | different |
| Badges | `badge.py` → `herdr pane report-metadata`; fleet rollups via `herdr workspace report-metadata` | — no metadata or badge command in the app | unavailable |
| Notifications | `herdr notification show … --sound` | — no notification command; tell the user in chat | unavailable |
| Resolve one target | `herdr agent get <name>`, `herdr agent list`, `herdr pane get <pane>` | `agent.py get <name>`: the exact `hc-agent.name` label in the root's tab, then its `t…` address | different |
| Prompt with preflight | `preflight_send.py` + `herdr agent prompt --wait` | `agent.py prompt`: `hc get` preflight, `hc send --if idle` (plain send for `done`/`error`), then waits for this turn | different |
| Multi-line prompt | `herdr agent prompt` honors the pane's bracketed-paste mode | `agent.py prompt <t> -` reads the task from stdin; `hc send` pastes it, per its help, and the turn tag goes on the last line. Multi-line paste was not run live | different |
| Error names | `agent_blocked`, `agent_prompt_stalled`, `timeout` | outcomes `blocked`, `stalled`, `timeout` with exit codes 3, 7, 8 | different names, same meaning |
| Wait without sending | `herdr agent wait`, `herdr wait agent-status`, `wait_for_idle.py` | `agent.py wait [--until blocked]`, which blocks in `hc wait` while the agent works | different |
| Read reply deltas | `herdr agent read` / `herdr pane read --source recent-unwrapped --lines 80` | `agent.py read --turn <id>` over `hc read --lines 400` | different |
| Long-reply file fallback | Ask for a file, read the path | Same | same |
| Fleet status | `fleet_status.py` over one `herdr api snapshot` (atomic) | `agent.py fleet`: `herdr-app ls` for the tab, one `hc get` per terminal (polled, not atomic) | different |
| Broadcast | `broadcast.sh` | `agent.py broadcast`, plus `agent.py dispatch` for a task per worker | different |
| Focus / steer | `herdr agent focus <name>`, which also marks the completion seen | `agent.py focus <name>` → `herdr-app do agent.focus --terminal <t>`; whether the app marks anything seen is unverified | different |
| Raw UI keys | `herdr agent send-keys <name> esc` | `hc keys <t> esc` on the terminal address; never into a dialog that needs the human. From `hc keys --help`, not run live | different |
| Interrupt a turn | `herdr agent send-keys <name> ctrl+c` | `hc interrupt <t>` presses the stop key and reports what happened; ask before interrupting someone else's agent. From `hc interrupt --help`, not run live | different |
| Human takeover | Focus the pane, or `herdr agent attach <name>` (`--takeover`); prefix + q detaches | Focus the pane, or `hc attach <t>` in the user's own terminal; ctrl+\ detaches | different |
| No-agent pane fallback | Pane-surface `pane run` / `send-keys` | — refused: a terminal without OSC 7501 status is unverifiable, never typed into | unavailable |
| Wait on a plain program's output | `herdr pane wait-output <pane> --match <text>`, which also matches text already on screen | No script. `hc wait <t> --output <text>` is for programs, not agents, takes plain text only, and matches only output printed after the wait starts. From `hc wait --help`, not run live | different |
| Unknown-status diagnosis | `herdr agent explain`, `herdr integration status`, `herdr integration install <agent>` | — not in the app; read the screen with `hc read <t> --lines 40` | unavailable |
| Teardown | `herdr pane close` on worker panes after confirmation | `agent.py close <names> --confirmed` → `herdr-app do pane.close`, only `hc-agent.role=worker` terminals in the root's tab | different |
| Never stop the server | `herdr server stop` forbidden | Never stop or restart the hc core or quit the app | same rule |
| HANDOFF | Successor `main-g<N>` via the spawn path, brief, ack | Same contract, plus a `GO` after the ack (as rex-agent); the successor is a `pane.split` terminal with no parent, so it outlives the old root; labeled `hc-agent.role=main` so teardown skips it | same contract |
| Context gate | Three gate points, 50% default, UNKNOWN counters | Same | same |
| Final report | Result / Evidence / Uncertainty / Decision | Same | same |
| Timeouts | Milliseconds | Seconds (hc's unit) | different |

## Verified live

- App terminals set `HC_TERMINAL_ID`, `HC_SCOPE` and `HC_TERMINAL_SOCKET`, and none of `HERDR_ENV`, `HERDR_PANE_ID`, `HERDR_TAB_ID` or `HERDR_WORKSPACE_ID`.
- The shapes of `hc get --json`, `hc ls --json` (no labels in its rows), `herdr-app ls` and `herdr-app status`, and errors as `{"error": {kind, message, hint}}` on stderr. Exit codes 3 (`not_found`) and 10 (`status_mismatch`) were observed; 7, 9 and 11 are per hc's documentation.
- `herdr-app do pane.split --direction right --pane <p> --argv '<json>'` returns `{"pane", "terminal"}`, moves focus to the new pane, and `herdr-app do pane.focus --pane <p>` moves it back.
- A `pane.split` terminal has `parent: null` and `die_with_parent: false`.
- `hc send <t> <text>` replies `{"started", "status", "turn"}`; `hc send --if idle` on a terminal with no status exits 10 (`status_mismatch`) and types nothing.
- `hc read --lines N` prints screen plus history; `herdr-app do pane.close --pane <p>` returns `{"ok": true}` and the terminal finishes.
- One end-to-end run of the scripts, root and one Claude Code worker, both through `mcc run --`:
  - `agent.py check` exited 0.
  - `launch_profile.py` kept the wrapper. The worker's argv was the folder wrapper around `mcc run -- --model <m> --effort <e>`, its foreground process was the harness with those flags once each, and the root's prompt was dropped.
  - `--start` split with an explicit `--pane`. The new terminal carried `herdr.space` / `herdr.tab` plus the four `hc-agent.*` labels (so `hc label --json <t> k=v…` works), had `parent: null` and `die_with_parent: false`, and reached `ready` with focus back on root.
  - `agent.py fleet` and `agent.py get <name>` found the worker by its label; `get` and `close` resolved it through `hc ls --json --label …`, so `hc ls --label` matches labels set by `hc label`.
  - `agent.py prompt` with a one-line task on stdin: `hc send --json --if idle -- <t> <text>` was accepted, the worker went `working` → `done`, `turn` moved 0 → 1, and `agent.py read --turn` returned the reply.
  - `agent.py close <name> --confirmed` closed only the worker, and the fleet was back to root alone.

## Unverified

- Anything the end-to-end run did not do: `broadcast` and `dispatch` to several live workers, a live HANDOFF successor, and `close` refusing root (unit-tested only).
- Worker kinds other than Claude Code, and wrappers other than `mcc run --`, including one that injects a flag the worker also carries.
- The output shapes of `hc wait` and `hc send --wait` (the scripts decide from `hc get` and ignore both).
- Column sizing with three or more columns, and splitting a worker pane instead of root.
- Linux and Windows: the environment variables, `/bin/sh` for the folder wrapper, and install paths.
- `hc` and `herdr-app` on PATH by default (observed in `~/.local/bin` only).
- Whether the window renders `hc-agent.*` labels anywhere.
- Multi-line text through `hc send` (it pastes, per its help; bracketed paste was not observed). The turn tag goes on the task's last line, so a one-line task stays one line.
- `herdr-app do agent.focus` on a terminal without agent status (the script falls back to `pane.focus`).
- The terminal address format: every address seen was `t` plus a digit and base-36 characters (`t7`, `t2x`, `t999`).
