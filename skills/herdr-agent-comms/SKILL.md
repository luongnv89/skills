---
name: herdr-agent-comms
description: "Manage AI agent fleets in Herdr: one project workspace, split panes in one view, message/wait/read via herdr CLI, steer any pane. Use for Herdr multi-agent fleets. Don't use for tmux, screen, or non-Herdr terminals."
license: MIT
effort: medium
metadata:
  version: 1.1.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
compatibility: "Requires `herdr` on PATH and a running Herdr server (`herdr status`)."
---

# Herdr Agent Comms

Manage and talk to AI agents (Claude Code, pi, Codex, OpenCode, or any CLI) as **split panes in one fleet view**: **create** a project workspace, **spawn** agents into a shared tab via splits, **send** tasks, **wait** on agent status, **capture** replies, and **tear down** when done.

Mental model (Herdr concepts, not tmux):

| Concept | Role in this skill |
|---|---|
| **Workspace** | One per project/repo — all agents for that project live here |
| **Fleet tab** | One shared tab (label e.g. `fleet`) holding the whole multi-agent view |
| **Pane** | One agent = one split pane; primary control target (`wN:pM`) |
| **Agent name** | Stable handle for send/wait/read (`reviewer`, `tests`, …) |

You orchestrate from outside (or from another Herdr pane) with the `herdr` CLI. Prefer Herdr's agent-status waits over polling scrollback. Relay each agent's answer, not its whole screen.

This skill is the **Herdr counterpart** of `tmux-agent-comms`. Use this when agents should live in Herdr; use `tmux-agent-comms` for plain tmux.

## When to Use

Spinning up a multi-agent fleet in Herdr, putting every agent for a project in one workspace as **side-by-side / tiled panes**, messaging or steering any pane, broadcasting to a fleet, or reading what an agent replied. Don't use for tmux/screen sessions or GUI apps.

## Workflow

Six phases, in order: ensure server + resolve workspace, spawn split-pane fleet, resolve targets, send, wait + read, continue or tear down.

**Jump straight to the phase for your task** — don't read the rest:

| Your task | Start at |
|---|---|
| Spin up N agents for a project (agent/model/thinking/skill + task) | Phase 1 → Phase 2 |
| Message an agent that's already running | Phase 3 |
| Just read a running agent's pane (no send) | Phase 5 |
| Broadcast the same message to a fleet | Phase 6 ("Broadcast") |
| Shut agents / fleet tab down | Phase 6 ("Tear down") |

## Prerequisites

1. **`herdr` installed**: `command -v herdr` must succeed. If missing, install (`curl -fsSL https://herdr.dev/install.sh | sh` or `brew install herdr`) and stop.
2. **Server reachable**: `herdr status` must show a running server. If not, tell the user to attach once with `herdr` from a real terminal (do **not** run bare `herdr` from a non-TTY agent shell — it tries to launch the TUI).
3. **Never nest tmux** inside a Herdr pane if you need agent detection — run agents directly in panes.
4. **Installed binary is authority** for flags: when unsure, run `herdr <group>` with no subcommand (e.g. `herdr agent`, `herdr pane`) — never bare `herdr` for discovery.

## Critical Rules

1. **Confirm before destructive actions.** Closing panes/tabs/workspaces or `herdr server stop` can lose agent work — never without explicit user go-ahead. Reading panes is always safe.
2. **Parse IDs from JSON.** Workspace/tab/pane IDs are opaque (`w26`, `w26:t2`, `w26:p4`). Never invent them from sidebar order.
3. **One workspace per project; one fleet tab; split pane per agent.** Default spawn path puts **all fleet agents in a single tab** as tiled splits so the human sees everyone at once. Create a **new tab per agent only** when the user explicitly asks for full-viewport isolation.
4. **Prefer `--no-focus` while spawning** so layout churn doesn't steal the keyboard from the human. After the fleet is up, `herdr tab focus <fleet_tab>` (or click the fleet tab) shows the whole board; `herdr agent focus <name>` zooms to one pane to type.
5. **Wait on agent status, don't race.** After send, wait for `working` then `idle`/`done` (Phase 4). Don't send a follow-up while status is `working`.
6. **`pane run` submits text + Enter.** Prefer it over separate `send-text`/`send-keys` for prompts. `agent send` is literal text only (no Enter) — use when you must type without submitting.
7. **Blocked agents need humans.** Status `blocked` means a trust/auth/permission dialog — surface it; don't type the next task into the dialog.

## Phase 1: Ensure Server and Project Workspace

```bash
command -v herdr >/dev/null || { echo "herdr missing"; exit 1; }
herdr status
herdr workspace list
```

Resolve the project directory (`project_dir`) and a short workspace label (default: basename of `project_dir`).

**Reuse** an existing workspace whose label or cwd matches the project when possible:

```bash
herdr workspace list   # JSON: workspaces[].workspace_id, label, ...
```

**Create** only when none matches:

```bash
herdr workspace create --cwd "$project_dir" --label "$label" --no-focus
# read result.workspace.workspace_id (or equivalent) from JSON
```

Optional: install the integration for agents you resume often (`herdr integration install pi|claude|codex|opencode|hermes`) so status is authoritative. Not required for every run.

**Done when:** you have a concrete `workspace_id` for the project and the server is running.

## Phase 2: Spawn Split-Pane Fleet

Put **all agents in one fleet tab** as tiled splits so the human sees every agent in a single view.

### 2a — Create one fleet tab, then split per agent

```bash
project_dir=/path/to/project
ws="$workspace_id"          # from Phase 1
fleet_label=fleet           # or "${label}-fleet"

# One shared tab for the whole fleet
tab_json="$(herdr tab create --workspace "$ws" --cwd "$project_dir" --label "$fleet_label" --no-focus)"
fleet_tab="$(printf '%s' "$tab_json" | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["tab"]["tab_id"])')"
root_pane="$(printf '%s' "$tab_json" | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["root_pane"]["pane_id"])')"

# --- agent 1: use the tab's root pane ---
name=reviewer
agent_cmd='pi --thinking medium'
herdr agent list | grep -q "\"name\":\"$name\"" && name="${name}-$(date +%s)"
herdr pane rename "$root_pane" "$name"
herdr agent rename "$root_pane" "$name"
herdr pane run "$root_pane" "$agent_cmd"
# record: pane_id=$root_pane

# --- agents 2..N: split inside the same fleet tab ---
# Alternate right/down for a usable tile (2-up: right; 3+: right then down…).
# Always --no-focus so the human keeps their keyboard.
name=tests
herdr agent list | grep -q "\"name\":\"$name\"" && name="${name}-$(date +%s)"
start_json="$(herdr agent start "$name" \
  --cwd "$project_dir" --workspace "$ws" --tab "$fleet_tab" \
  --split right --no-focus -- pi --thinking low)"
pane_id="$(printf '%s' "$start_json" | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["agent"]["pane_id"])')"
# if argv after -- is only the launcher, boot is done; else still wait idle before task

name=docs
herdr agent list | grep -q "\"name\":\"$name\"" && name="${name}-$(date +%s)"
herdr agent start "$name" \
  --cwd "$project_dir" --workspace "$ws" --tab "$fleet_tab" \
  --split down --no-focus -- pi --thinking low
```

**Split direction rule:** prefer `right` when the target pane is wider than tall; prefer `down` when it is tall/narrow. If you cannot inspect layout, **alternate** `right`, `down`, `right`, … Avoid stacking every split in the same direction (creates unusable slivers).

**Optional (user asked for full-viewport isolation):** one tab per agent via `herdr tab create` per name — see `references/herdr-recipes.md` ("Tab-per-agent layout"). Not the default.

### 2b — Build `agent_cmd` (common CLIs)

| Agent | Executable | Model / thinking / skill knobs |
|---|---|---|
| **pi** | `pi` | `--model <provider/id>`, `--thinking <off\|…\|max>`, `--skill <path>` (repeatable) |
| **Claude Code** | `claude` | model via settings/`--model` if available; skills via project/plugin — don't invent flags |
| **Codex** | `codex` | interactive default; verify flags with `codex --help` |
| **OpenCode** | `opencode` | verify with `opencode --help` |

Launch the **interactive** TUI (no `-p`/`exec` non-interactive mode) unless the user asked for fire-and-exit. Do **not** pass the long task as argv on first launch by default — boot first, then `pane run` the task (matches Herdr's own agent guide).

When using `herdr agent start … -- <argv>`, put only the launcher (+ model/thinking/skill flags) after `--`, not the long task prompt.

### 2c — Ready, then assign work

```bash
# boot → idle (or blocked on trust) — per pane
herdr wait agent-status "$pane_id" --status idle --timeout 60000
# if timeout: herdr pane get / herdr agent explain "$pane_id"
# if blocked: surface to user (Rule 7)

herdr pane run "$pane_id" "Review the open PR diff and report only actionable findings."
herdr wait agent-status "$pane_id" --status working --timeout 30000 || true
```

**Fleet spawn:** create the fleet tab once, spawn every split (`--no-focus`), launch every agent, then wait/read concurrently — don't fully serialize spawn→wait→read per agent when the user wants parallel work. `scripts/broadcast.sh` fans messages after spawn.

**Human visibility:** after spawn, focus the fleet tab so all panes are on screen:

```bash
herdr tab focus "$fleet_tab"
# or zoom one agent: herdr agent focus reviewer
```

Detach the Herdr client with `prefix+q` (`ctrl+b` then `q`); agents keep running.

**Done when:** each requested agent has `pane_id` + shared `fleet_tab` + agent `name`, all panes are in that tab, status is not stuck on `unknown` after boot wait, and initial tasks (if any) have been submitted.

## Phase 3: Resolve the Exact Target

Prefer the **agent name** when unique; fall back to `pane_id`:

```bash
herdr agent list
herdr agent get reviewer          # or: herdr pane get w26:p4
```

If the name is missing, list agents and surface the closest match — don't silently retarget. Record both `name` and `pane_id` for later steps (`wait agent-status` wants a pane id; `agent send`/`agent wait` accept names).

**Done when:** one concrete target id is chosen and exists in `agent list` / `pane get`.

## Phase 4: Send a Message

```bash
# preferred — text + Enter
herdr pane run "$pane_id" "summarize the changes in src/"

# by name (literal text only — add Enter yourself if needed)
herdr agent send reviewer "summarize the changes in src/"
herdr pane send-keys "$pane_id" enter
```

**Escaping:** pass the message as a single argv to `herdr` (quoted for the shell). For multi-line or code-heavy payloads, write a temp file and send a short instruction that reads it — see `references/herdr-recipes.md`.

**Verify delivery:** after send, status should leave `idle` for `working` (or stay `blocked` if a dialog ate the input):

```bash
herdr wait agent-status "$pane_id" --status working --timeout 15000 \
  && echo delivered || echo NOT-DELIVERED
```

`NOT-DELIVERED` → lone Enter via `herdr pane send-keys "$pane_id" enter`, re-check; if still idle with no new output, re-send. Inspect with `herdr pane read "$pane_id" --source recent-unwrapped --lines 40`.

## Phase 5: Wait for the Reply, Then Read It

Use Herdr status waits (not fixed `sleep`). Completion may be **`done`** (unseen, usually background) **or `idle`** (seen / focused tab) — wait for either:

```bash
# After delivery verified (Phase 4). Poll until idle|done|blocked or budget spent.
deadline=$((SECONDS + 180))
while (( SECONDS < deadline )); do
  st=$(herdr pane get "$pane_id" | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["pane"].get("agent_status",""))')
  case "$st" in
    done|idle) echo "settled:$st"; break ;;
    blocked) echo "blocked"; break ;;
    working) herdr wait agent-status "$pane_id" --status done --timeout 15000 \
               || herdr wait agent-status "$pane_id" --status idle --timeout 15000 || true ;;
    *) sleep 2 ;;
  esac
done
# Or: python3 scripts/wait_for_idle.py "$pane_id" --timeout 180
```

Treat **either `idle` or `done` as completed** — difference is only whether the result was seen. Never wait only on `done` for the full budget: a focused-tab finish stays `idle` and will time out.

Then read a capped recent transcript:

```bash
herdr pane read "$pane_id" --source recent-unwrapped --lines 80
# or: herdr agent read reviewer --source recent-unwrapped --lines 80
```

Sources: `visible` (viewport), `recent` (rendered scrollback), `recent-unwrapped` (preferred for transcripts), `detection` (bottom buffer for debug).

**Branch on outcomes:**

| Signal | Action |
|---|---|
| status `done`/`idle` after work | Relay the read output |
| status `blocked` | Surface dialog; don't send more |
| wait timeout | `pane get` + `pane read` + `agent explain`; escalate — don't poll forever |
| status still `working` | Keep waiting under a hard overall budget (e.g. 2–3 re-waits) |

Optional helper when status stays `unknown` (no integration / undetected CLI): `python3 scripts/wait_for_idle.py <pane_id>` polls `pane read` for content stability — see script `--help`.

**Done when:** you either relay a reply delta or report blocked/timeout with evidence.

## Phase 6: Continue, Broadcast, or Tear Down

**Continue (steer):** focus if the human wants the live TUI, or keep messaging from the CLI:

```bash
herdr agent focus reviewer          # jump UI to that agent
herdr pane run "$pane_id" "Also check the failing test."
# then Phase 5 again
```

**Broadcast to a fleet:** send to every target first, then wait concurrently:

```bash
scripts/broadcast.sh "pull latest main and report status" reviewer tests docs
# or pane ids: scripts/broadcast.sh "..." w26:p4 w26:p6
```

**Fleet status (read-only):**

```bash
herdr agent list
herdr workspace list
```

**Tear down (confirmation required):**

```bash
herdr pane close "$pane_id"         # one agent pane
herdr tab close "$fleet_tab"        # preferred — whole fleet view at once
herdr workspace close "$ws"         # whole project workspace — confirm
# herdr server stop                 # kills everything — last resort, confirm
```

Never `server stop` from inside an active session unless the user explicitly wants the server and all panes dead.

## Example

Spin two agents side-by-side in one fleet tab and collect answers:

```bash
project_dir="$(pwd)"
label="$(basename "$project_dir")"
export L="$label"
ws="$(herdr workspace list | python3 -c "
import sys,json,os
d=json.load(sys.stdin); label=os.environ['L']
for w in d['result']['workspaces']:
    if w.get('label')==label: print(w['workspace_id']); break
" )"
# if empty: create with herdr workspace create --cwd "$project_dir" --label "$label" --no-focus

tab_json="$(herdr tab create --workspace "$ws" --cwd "$project_dir" --label fleet --no-focus)"
fleet_tab="$(printf '%s' "$tab_json" | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["tab"]["tab_id"])')"
p1="$(printf '%s' "$tab_json" | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["root_pane"]["pane_id"])')"

herdr pane rename "$p1" reviewer
herdr agent rename "$p1" reviewer
herdr pane run "$p1" 'pi --thinking medium'

j2="$(herdr agent start tests --cwd "$project_dir" --workspace "$ws" --tab "$fleet_tab" \
  --split right --no-focus -- pi --thinking low)"
p2="$(printf '%s' "$j2" | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["agent"]["pane_id"])')"

for p in "$p1" "$p2"; do
  herdr wait agent-status "$p" --status idle --timeout 60000
done
herdr pane run "$p1" 'Review recent commits for risk; bullet findings only.'
herdr pane run "$p2" 'Outline a minimal test plan for the last change.'

herdr tab focus "$fleet_tab"   # show both panes in one view
python3 scripts/wait_for_idle.py "$p1" --timeout 180
herdr pane read "$p1" --source recent-unwrapped --lines 80
herdr agent focus reviewer     # optional: zoom to type into one pane
```

## Edge Cases

- **Not inside Herdr / no server** — CLI still talks to the socket if the server runs; if `herdr status` fails, user must start `herdr` once in a real terminal.
- **Nested `herdr` launch** — if `HERDR_ENV=1`, never run bare `herdr` (blocked by design). Use CLI subcommands only.
- **Trust/auth dialog** — status `blocked`; surface it, don't submit the task.
- **`idle` vs `done`** — both mean "finished or waiting for input"; `done` = unseen completion in background. Accept either after work.
- **Name collision** — `agent rename` / `agent start` names must be unique; suffix with epoch if taken.
- **Wrong workspace** — never spawn project B agents into project A's workspace; re-resolve Phase 1.
- **Status `unknown`** — install integration or use `scripts/wait_for_idle.py` + `pane read`.
- **Too many splits** — more than ~4 panes in one tab gets cramped; still default to splits unless the user asks for tab-per-agent, or create a second fleet tab for overflow.
- **User wants to steer** — `herdr tab focus` for the whole board, `herdr agent focus <name>` for one pane; keep sending CLI follow-ups only when not fighting their keyboard.
- **Closing the wrong pane/tab** — only close panes/tabs this skill created, unless the user names the target.

## Reference

- `references/herdr-recipes.md` — fleet layouts, multi-line sends, focus/steer, scrollback, troubleshooting.
- `references/delivery-and-waiting.md` — delivery checks, idle/done/blocked, budgets.
- Official concepts: https://herdr.dev/docs/concepts/ · CLI: https://herdr.dev/docs/cli-reference/ · cheatsheet: https://luongnv.com/awesome-cheatsheets/cheatsheets/herdr/

## Step Completion Report

After a messaging or lifecycle operation, emit:

```
◆ Herdr Agent Comms ([what you did])
··································································
  Server:              √ pass (herdr status)
  Workspace:           √ pass (w26 · project label)
  Target resolved:     √ pass (name: reviewer · pane: w26:p4 · fleet tab: w26:t2)
  Message sent:        √ pass (pane run)
  Message delivered:   √ pass (status → working)
  Reply settled:       √ pass (status done|idle)
  Reply captured:      √ pass (recent-unwrapped, not truncated)
  Destructive action:  — none (or: confirmed by user)
  ____________________________
  Result:              PASS
```

Adapt rows to the operation — a spawn reports `Fleet tab + splits created`; a teardown reports `Confirmed` and `Panes/tab closed`. Use `⚠` for dropped delivery or escalated stall.
