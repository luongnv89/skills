# Herdr recipes for agent fleets

Read this when you need layout variants, spawn mechanics, multi-line prompts, human steer/focus, scrollback recovery, or troubleshooting. Delivery and waiting live in `references/delivery-and-waiting.md`; status, badges and reporting live in `references/fleet-monitoring.md`.

## Default fleet layout (this skill)

**Root + sub-agents as equal-width columns in one tab:**

```
Session (default)
└── Workspace: <project>
    └── Tab: <root's tab>                          ← single row of columns
        ┌───────────┬───────────┬───────────┐
        │ root (you)│ reviewer  │ tests      │
        └───────────┴───────────┴───────────┘
```

(`next_grid_split.py` always targets the current rightmost column for the
split, then its `--equalize` pass re-converges every column to the same
width no matter how many are spawned — never a wide root next to narrow
workers, or vice versa. Columns end equal within ~1 terminal cell.)

Why this default: the human sees the **root agent and every sub-agent at the
same size**; the orchestrator is never displaced into a side tab or left
oddly wide/narrow; sidebar still rolls status per workspace.

### Spawn N sub-agents into an equal-width grid

Use `scripts/next_grid_split.py` for every spawn: the default run emits the
split line targeting the **current rightmost column** (`--ratio 1/N`, so the
new right pane lands on the `1/N` equal target — see "Split ratio" below),
and `--equalize` runs the live iterative equalizer that re-converges every
column (including root) to the same width. `--equalize` is a **hard gate**:
it exits non-zero on a resize failure or non-convergence, and the spawn
helper below aborts rather than launch a worker into an uneven layout.

```bash
root_pane="${HERDR_PANE_ID:?}"
root_tab="${HERDR_TAB_ID:?}"
ws="${HERDR_WORKSPACE_ID:?}"
project_dir=$(pwd)
# Resolve scripts/ by probing known install locations. Don't derive from
# $0/BASH_SOURCE here — unreliable when an agent runs this inline rather
# than as a saved script file. Repo-local copies win over global installs
# so a pinned repo checkout isn't silently overridden by whatever version
# happens to be installed globally.
here=""
for cand in \
  "skills/herdr-agent-comms/scripts" \
  ".agents/skills/herdr-agent-comms/scripts" \
  ".claude/skills/herdr-agent-comms/scripts" \
  "$HOME/.claude/skills/herdr-agent-comms/scripts" \
  "$HOME/.agents/skills/herdr-agent-comms/scripts"; do
  if [ -f "$cand/next_grid_split.py" ]; then here="$cand"; break; fi
done
[ -n "$here" ] || { echo "Error: next_grid_split.py not found in any known install location (repo, .agents/, .claude/, \$HOME). Fix the install or set \$here manually before retrying." >&2; exit 1; }

# Canonical guarded spawn: every critical step is checked, the pane id is
# printed ONLY after `herdr agent start` reports the agent ready, and any
# failure returns non-zero (naming the orphan split pane) so the caller can
# abort. Note the `local` declarations are separate from the assignments —
# `local pane=$(...)` would mask the substitution's exit status.
#
# `agent start` is the readiness gate. It returns only once Herdr has detected
# the expected agent in that pane and considers it ready for interactive input,
# so there is no separate readiness pass and no boot polling. A trust/auth
# dialog during startup returns `agent_not_ready` immediately rather than
# burning the whole timeout, and the name still resolves for `agent read` and
# `agent send-keys` so you can show the human what it is asking.
spawn_sub() {
  local name=$1 kind=$2; shift 2   # remaining args, if any, are native agent args
  local plan split_from ratio j pane
  herdr agent list | grep -q "\"name\":\"$name\"" && name="${name}-$(date +%s)"
  # plan line: "split <rightmost> right --ratio <1/N>" (new right pane -> 1/N target)
  plan=$(python3 "$here/next_grid_split.py" --root-pane "$root_pane") || {
    echo "Error: planning split failed for '$name' (bad/unsupported layout?)." >&2; return 1; }
  read -r _ split_from _ _ ratio < <(head -1 <<<"$plan")
  [ -n "$split_from" ] && [ -n "$ratio" ] || {
    echo "Error: empty plan for '$name'; refusing to split." >&2; return 1; }
  # --env stamps the worker's own role into its pane environment, so the agent
  # can read $HERDR_ROLE rather than being told who it is in every prompt.
  j=$(herdr pane split "$split_from" --direction right --ratio "$ratio" \
        --cwd "$project_dir" --env "HERDR_ROLE=$name" --no-focus) || {
    echo "Error: 'herdr pane split $split_from' failed for '$name'." >&2; return 1; }
  pane=$(printf '%s' "$j" | python3 -c 'import sys,json; d=json.load(sys.stdin); r=d["result"]; print((r.get("pane") or r)["pane_id"])') || {
    echo "Error: could not parse pane id from split output for '$name'." >&2; return 1; }
  [ -n "$pane" ] || { echo "Error: empty pane id for '$name'." >&2; return 1; }
  # Equalize all columns — HARD GATE: on failure return non-zero WITHOUT
  # launching or printing a pane id, so the caller aborts (no `|| true`).
  if ! python3 "$here/next_grid_split.py" --equalize --root-pane "$root_pane" >&2; then
    echo "Error: equalize failed for '$name'; orphan split pane $pane not launched. 'herdr pane close $pane' to undo." >&2
    return 1
  fi
  herdr pane rename "$pane" "$name" >/dev/null || { echo "Error: rename failed; orphan $pane." >&2; return 1; }
  # `agent start` names the agent itself — no separate `agent rename` — and
  # blocks until it is interactive-ready. Native agent flags go after `--`;
  # never fold the task itself into argv.
  local extra=()
  [ "$#" -gt 0 ] && extra=(-- "$@")
  herdr agent start "$name" --kind "$kind" --pane "$pane" --timeout 60000 \
    ${extra[@]+"${extra[@]}"} >/dev/null \
    || { echo "Error: agent start failed for '$name'; orphan $pane." >&2; return 1; }
  printf '%s\n' "$pane"   # ONLY after the agent reported ready
}

# Caller MUST check the status — `$(...)` hides spawn_sub's non-zero exit, so a
# failed equalize or a failed `agent start` would otherwise be ignored and the
# next spawn would build on a broken layout. Each call places the pane AND waits
# for readiness, so a failure means the fleet is not up: abort rather than
# assign work into a half-built grid.
p_reviewer=$(spawn_sub reviewer claude) || { echo "reviewer failed; aborting" >&2; exit 1; }
p_tests=$(spawn_sub tests pi --thinking low) || { echo "tests failed; aborting" >&2; exit 1; }
# optional third: p_docs=$(spawn_sub docs claude) || { echo "docs failed; aborting" >&2; exit 1; }

# Badge each worker so the human can read the fleet from the sidebar without
# opening a single pane (see references/fleet-monitoring.md).
python3 "$here/badge.py" reviewer --title "Review the diff" --token role=review
python3 "$here/badge.py" tests --title "Run and triage the suite" --token role=tests

# Confirm the whole fleet in one call before assigning work.
python3 "$here/fleet_status.py" --tab "$root_tab" --fail-on-blocked \
  || { echo "Fleet not clean; resolve before assigning work." >&2; exit 1; }
```

Kinds Herdr 0.9 can start: `pi`, `claude`, `codex`, `gemini`, `cursor`, `devin`,
`agy`, `cline`, `omp`, `mastracode`, `opencode`, `copilot`, `kimi`, `kiro`,
`droid`, `amp`, `grok`, `hermes`, `kilo`, `qodercli`, `qwen`, `maki`, `muse`.
Run `herdr agent` for the list the installed binary actually supports.

Agent names must match `[a-z][a-z0-9_-]{0,31}` and be unique among live agents.
A name follows the pane's current occupant and clears when that agent exits, is
released, or is replaced.

### Grid heuristics

| Step | Rule |
|---|---|
| Target pane | current rightmost column (`rect.x` order) |
| Direction | always `right` — one row of columns, never `down` |
| Split ratio | `1/N` (the planner emits it) — `--ratio R` is the existing/left child's share, so the new right pane gets `1-R = (N-1)/N` of the split column = the `1/N` equal target of the tab |
| After each spawn | run `--equalize` — a split alone can't shrink the pre-existing columns |
| Re-run per spawn | never hardcode a fixed ratio — it shrinks every time |
| Focus | always `--no-focus` |

```bash
# $here from the resolver above (or re-probe if starting fresh in this shell)
python3 "$here/next_grid_split.py" --equalize --root-pane "$root_pane"
herdr pane layout --pane "$root_pane"   # verify near-equal-width rects
```

Manual fallback without the helper: read `herdr pane layout`, order panes by `rect.x`, split the rightmost one `right`, then hand-run the equalizer — see "Equal-width columns — verified semantics" below.

### Split first, then `agent start`

`herdr agent start` never creates, splits, or moves layout — it requires an
existing **available shell pane**, meaning one sitting at its interactive prompt
with no foreground command, editor, or agent running. So placement and launch
are always two steps in this order:

| Step | Command |
|---|---|
| 1. Place | `next_grid_split.py` plan → `herdr pane split … --ratio R --no-focus` → `--equalize` |
| 2. Launch | `herdr agent start <name> --kind KIND --pane <id> --timeout 60000 [-- <agent-args>]` |

Never `herdr pane run <pane> "claude"` to launch an agent. That works, but you
then own detection and readiness yourself; `agent start` returns only when Herdr
has confirmed both.

### Equal-width columns — verified semantics

These were confirmed **live against herdr 0.7.4**; the CLI has no `--help`, so
run experiments in a throwaway `herdr tab create` and read `herdr pane layout`
before/after (close the probe tab when done — never probe the session's own
tab). Results:

- **`pane split <p> --direction right --ratio R`** — `R` is the fraction the
  **existing (left) child** keeps of the pane `p`; the new (right) pane gets
  `1 - R`. It resizes only `p`; the other columns are untouched. So a single
  split can never equalize `N >= 3` columns. (`--ratio 0.5` on a 210-cell tab
  → 105/105.) To add column N we split the rightmost column at **`R = 1/N`**:
  when the N-1 existing columns are equal, the rightmost is `1/(N-1)` of the
  tab, so the new pane's `(1-R) = (N-1)/N` share of it equals `1/N` of the
  whole tab — the equal target. Verified live: from 105/105, splitting the
  rightmost at `--ratio 0.333` (=1/3) gives a new pane of 70 (= 210/3), i.e.
  the equal target — NOT 35, which is what the earlier inverted `(N-1)/N`
  value produced. The equalizer then fixes the disturbed inner columns.
- **`pane resize --pane P --direction D --amount A`** — `A` is a **delta**, a
  fraction of the whole tab area width (`A * area_width` cells), *not* an
  absolute target width. `--direction D` moves the edge on side `D`: a pane
  with a neighbor on side `D` **grows** toward it; against a wall it shrinks.
  The freed/absorbed cells redistribute **proportionally** among the panes on
  the far side of the moved boundary. (Verified: a leftmost pane resized
  `left 0.1` on a 210 tab shrank by exactly 21 cells, distributed to its
  right neighbors by their prior widths.)
- **Consequence:** one left-to-right resize sweep does not land equal (each
  resize perturbs downstream columns), but the sweep is a *contraction* —
  iterating it converges. Observed 4-column decay: spread 25 → 13 → 5 → 3 → 1.

**Equalizer algorithm** (`next_grid_split.py --equalize`): compute equal
integer targets summing to `area_width` (remainder onto the leftmost
columns); each pass, sweep internal boundaries left to right and move each
toward its target cumulative position by **growing the neighbor-bearing pane**
(boundary must move right → `resize left_col right`; must move left →
`resize right_col left`), re-reading the layout after every resize; repeat
until the width spread is ≤1 cell (cap 12 passes). Verified end-to-end via the
script: 2 cols → 105/105, 3 → 70/70/70, 4 → 53/53/52/52, 5 → 42×5. A failed
`herdr pane resize` (nonzero exit) or non-convergence within the pass cap is a
**hard error**: `--equalize` exits non-zero with an actionable message naming
the pane/direction/amount (or the final widths), and the spawn recipes abort
instead of launching a worker into an uneven layout.

**Manual equalize** (helper unavailable): for a tab of width `W` with `N`
columns, target each column ≈ `W/N`. Repeat this sweep until widths stop
changing: for each internal boundary `i` (left to right), if the cumulative
width left of it is below `(i+1)*W/N`, `herdr pane resize --pane <col i>
--direction right --amount <deficit/W>`; if above, `herdr pane resize --pane
<col i+1> --direction left --amount <excess/W>`. Because widths are whole
cells, columns end equal within ±1 cell (exact only when `W` divides by `N`).

### When to use tab-per-agent instead

- User asks for "full screen per agent" / "own tab each"
- Agent TUIs need a wide viewport (diff-heavy review)
- More agents than fit usefully in one tile (~5+)

```bash
for name in reviewer tests docs; do
  j=$(herdr tab create --workspace "$ws" --cwd "$project_dir" --label "$name" --no-focus)
  pane=$(printf '%s' "$j" | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["root_pane"]["pane_id"])')
  herdr pane rename "$pane" "$name"
  herdr agent start "$name" --kind claude --pane "$pane" --timeout 60000 >/dev/null \
    || { echo "Error: agent start failed for $name (pane $pane)." >&2; exit 1; }
done
```

### Adding a log / shell pane into the grid

```bash
# $here from the resolver above (or re-probe if starting fresh in this shell)
plan=$(python3 "$here/next_grid_split.py" --root-pane "$root_pane") || { echo "Error: split planning failed." >&2; exit 1; }
read -r _ split_from _ _ ratio < <(head -1 <<<"$plan")
[ -n "$split_from" ] && [ -n "$ratio" ] || { echo "Error: empty split plan." >&2; exit 1; }
j=$(herdr pane split "$split_from" --direction right --ratio "$ratio" --cwd "$project_dir" --no-focus) || { echo "Error: pane split failed." >&2; exit 1; }
pane=$(printf '%s' "$j" | python3 -c 'import sys,json; d=json.load(sys.stdin); r=d["result"]; print((r.get("pane") or r)["pane_id"])') || { echo "Error: could not parse pane id." >&2; exit 1; }
[ -n "$pane" ] || { echo "Error: empty pane id." >&2; exit 1; }
# Equalize all columns — HARD GATE: abort (and close the orphan pane) rather
# than run the log tail into an uneven layout.
if ! python3 "$here/next_grid_split.py" --equalize --root-pane "$root_pane"; then
  echo "Error: equalize failed; not launching log pane. Orphan: $pane (herdr pane close $pane to undo)." >&2
  herdr pane close "$pane" >/dev/null 2>&1 || true
  exit 1
fi
herdr pane rename "$pane" logs || { echo "Error: rename failed; orphan $pane." >&2; exit 1; }
herdr pane run "$pane" "bash -lc 'tail -f /tmp/app.log'" || { echo "Error: launch failed; orphan $pane." >&2; exit 1; }
```

## Sending multi-line or code-heavy messages

`herdr agent prompt <target> "<text>"` takes the payload as one argument and
honors the pane's live bracketed-paste mode, so newlines, code fences, and
quotes go in as text rather than as a stream of Enter presses. Pass the whole
task directly; the old type-then-Enter dance is no longer needed.

```bash
task=$(cat <<'EOF'
Review these files:
- src/a.ts
- src/b.ts

Return only:
1. bugs
2. missing tests
EOF
)
python3 "$here/preflight_send.py" reviewer >/dev/null || exit $?
herdr agent prompt reviewer "$task" --wait --timeout 180000
```

Two payload sizes still deserve care:

- **Very large prompts.** Submit delay grows with prompt size for Codex on
  Windows. Prefer writing the material to a file and prompting the agent to read
  that path.
- **Content the agent should read, not be told.** Write it to a file and send a
  short instruction naming the path. That keeps the prompt small and the file
  reviewable.

Raw keystrokes remain available for interactive UI controls, validated before
any bytes are written:

```bash
herdr agent send-keys reviewer esc
herdr agent send-keys reviewer ctrl+c
```

Keys are Herdr key-combo strings: printable keys, named keys like `enter` and
`esc`, chords like `ctrl+h` or `shift+tab`, function keys like `f1`, and named
punctuation like `minus`. `prefix+` bindings are not accepted.

## Human steer / focus

| Goal | Command |
|---|---|
| Stay on whole board | already one tab (root + subs) |
| Jump UI to one sub-agent | `herdr agent focus reviewer` |
| Jump back toward root | click root pane / focus root pane id |
| Attach/takeover terminal | `herdr agent attach reviewer` (optional `--takeover`) |
| Read without stealing focus | `herdr agent read reviewer --source recent-unwrapped --lines 80` |

Orchestrator rule: use `--no-focus` on every split/start so fleet spawn doesn't yank focus off the root agent. Focus a sub-agent only when the human wants to type or dismiss a `blocked` dialog.

Detach Herdr client (leave agents running): `prefix+q` (`ctrl+b` then `q`). Reattach: `herdr` in a terminal.

## Reading scrollback robustly

```bash
herdr pane read "$pane_id" --source recent-unwrapped --lines 80
herdr pane read "$pane_id" --source recent-unwrapped --lines 200
herdr pane read "$pane_id" --source visible --lines 50
herdr pane read "$pane_id" --source detection
```

Prefer `recent-unwrapped` for agent transcripts. Widen `--lines` stepwise if truncated.

## Broadcast pattern (manual)

Use `scripts/broadcast.sh "<msg>" reviewer tests docs`. It resolves every target
from one `herdr agent list` call, dedupes, refuses `working` and `blocked`
targets, dispatches `herdr agent prompt --wait` concurrently, maps Herdr's error
codes to reasons, and optionally badges each row with its phase (`HAC_BADGE=1`).

The hand-rolled equivalent, and why each safeguard exists, is in
`references/delivery-and-waiting.md` under "Concurrent fleet waits".

## Troubleshooting

| Symptom | Check |
|---|---|
| CLI errors "server not running" | `herdr status`; user starts `herdr` once in a real TTY |
| Sub-agent on a new tab | You used `tab create` — use grid split in the root tab instead |
| Root pane taken by worker | Never `pane run` the worker CLI on `$HERDR_PANE_ID` |
| Unequal-width columns | Always split the current rightmost column and apply the full resize plan from `next_grid_split.py` |
| Agent always `unknown` | `herdr integration status`, then `herdr integration install <agent>`; `herdr agent explain <target> --json` shows the matched rule and manifest version |
| Nested tmux breaks detection | Don't run tmux inside Herdr panes |
| `agent prompt` returns `agent_prompt_stalled` | Submitted but no activity followed; `agent get` + `agent read` before any resend — a resend can double-submit |
| `agent prompt` returns `agent_blocked` | Nothing was sent; `agent focus` and let the human answer |
| `agent get` returns `agent_not_found` | The pane hosts no detected agent; `agent start` it, or use the pane fallback in `references/delivery-and-waiting.md` |
| Status stuck `working` | `agent read`; overall wait budget; escalate the stall |
| Fleet state unclear | `python3 scripts/fleet_status.py --tab "$root_tab"` — one call, whole fleet |
| Human missed a blocked agent | `herdr notification show "Agent blocked" --body "<name>" --sound request` |
| Server/client version skew after an update | `herdr status` before relying on a new method; a missing method is not permission to stop or upgrade the server |
| `blocked` | Human must answer dialog; `agent focus` to show it |
| Panes too narrow | Fewer agents (equal-width columns shrink every time); tab-per-agent only if user asks |
| Wrong project files | Confirm `--cwd` before spawn |
| Name not found | `herdr agent list`; names are unique session-wide |
| Accidentally focused spawn | Pass `--no-focus` on `pane split` / `agent start` |

### Debug one pane

```bash
herdr pane get "$pane_id"
herdr agent explain "$pane_id"
herdr agent explain "$pane_id" --json
herdr pane process-info --pane "$pane_id"
```

### Logs

```
~/.config/herdr/herdr.log
~/.config/herdr/herdr-client.log
~/.config/herdr/herdr-server.log
HERDR_LOG=herdr=debug herdr   # human client only
```

## Mapping from tmux-agent-comms

| tmux | Herdr |
|---|---|
| `tmux split-window` from current | `next_grid_split.py` + `herdr pane split <rightmost> --direction right --no-focus` + `herdr pane resize` on every column |
| session name | agent `name` + `pane_id` |
| `tmux send-keys … Enter` | `herdr agent prompt <target> "<task>" --wait` (agents) / `herdr pane run` (plain commands) |
| `tmux capture-pane -p -S -40` | `herdr agent read … --source recent-unwrapped --lines 40` |
| `tmux has-session` | `herdr agent get` / `herdr pane get` |
| polling `capture-pane` for quiescence | `herdr agent wait <target> [--until STATUS]` (event-driven, server-side) |
| `tmux list-panes` across a fleet | `herdr api snapshot` via `scripts/fleet_status.py` |
| no equivalent | `herdr pane report-metadata` sidebar badges, `herdr notification show` |
| `tmux kill-pane` (worker) | `herdr pane close` (sub-agent only) |
| `tmux kill-server` | `herdr server stop` (confirm!) |
| multiple app terminal tabs | **one** tab grid: root + tiled sub-agents |
