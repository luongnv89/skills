# Herdr recipes for agent fleets

Read this when you need layout variants, multi-line sends, human steer/focus, scrollback recovery, or troubleshooting.

## Default fleet layout (this skill)

**One fleet tab, split pane per agent** — all agents visible in a single view:

```
Session (default)
└── Workspace: <project>                 ← one per repo
    └── Tab: fleet
        ├── pane wN:pA  agent "reviewer"
        ├── pane wN:pB  agent "tests"     (split right)
        └── pane wN:pC  agent "docs"      (split down)
```

Why splits by default: the human sees the whole fleet without switching tabs; sidebar still rolls status up per workspace. Use tab-per-agent only when the user wants a full viewport per agent.

### Create workspace + three-agent fleet (splits)

```bash
project_dir=/path/to/project
label=$(basename "$project_dir")
ws=$(herdr workspace create --cwd "$project_dir" --label "$label" --no-focus \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["workspace"]["workspace_id"])')

tab_json=$(herdr tab create --workspace "$ws" --cwd "$project_dir" --label fleet --no-focus)
fleet_tab=$(printf '%s' "$tab_json" | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["tab"]["tab_id"])')
root=$(printf '%s' "$tab_json" | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["root_pane"]["pane_id"])')

# Agent 1 on root pane
herdr pane rename "$root" reviewer
herdr agent rename "$root" reviewer
herdr pane run "$root" "pi --thinking medium"

# Agent 2 / 3 via agent start + split (same tab)
herdr agent start tests --cwd "$project_dir" --workspace "$ws" --tab "$fleet_tab" \
  --split right --no-focus -- pi --thinking low
herdr agent start docs --cwd "$project_dir" --workspace "$ws" --tab "$fleet_tab" \
  --split down --no-focus -- pi --thinking low

herdr tab focus "$fleet_tab"   # show the whole board
```

### Split direction heuristics

| Situation | Direction |
|---|---|
| 2 agents | first extra: `right` |
| 3 agents | `right` then `down` |
| Wide pane | prefer `right` |
| Tall/narrow pane | prefer `down` |
| Unknown geometry | alternate `right`, `down`, `right`, … |

Inspect geometry when available:

```bash
herdr pane layout --pane "$pane_id"
```

Avoid repeating the same direction for every split (creates unusable slivers).

### When to use tab-per-agent instead

- User asks for "full screen per agent" / "own tab each"
- Agent TUIs need a wide viewport (diff-heavy review)
- More agents than fit usefully in one tile (~5+)

```bash
for name in reviewer tests docs; do
  j=$(herdr tab create --workspace "$ws" --cwd "$project_dir" --label "$name" --no-focus)
  pane=$(printf '%s' "$j" | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["root_pane"]["pane_id"])')
  herdr pane rename "$pane" "$name"
  herdr agent rename "$pane" "$name"
  herdr pane run "$pane" "pi --thinking medium"
done
```

### Adding a log / shell pane beside the fleet

```bash
herdr agent start logs --cwd "$project_dir" --workspace "$ws" --tab "$fleet_tab" \
  --split down --no-focus -- bash -lc 'tail -f /tmp/app.log'
```

## Sending multi-line or code-heavy messages

`herdr pane run <pane> <command>` takes one shell-quoted string. Nested quotes and newlines break easily.

**Pattern A — short instruction that reads a file:**

```bash
task_file=$(mktemp)
cat >"$task_file" <<'EOF'
Review these files:
- src/a.ts
- src/b.ts

Return only:
1. bugs
2. missing tests
EOF
herdr pane run "$pane_id" "Read $task_file and follow its instructions. Delete the file when done."
```

**Pattern B — `send-text` then Enter** (when you must avoid shell expansion inside `pane run`):

```bash
herdr pane send-text "$pane_id" "line one"
# For multi-line, prefer Pattern A. send-text is literal; then:
herdr pane send-keys "$pane_id" enter
```

**Pattern C — agent name:**

```bash
herdr agent send reviewer "summarize src/"
herdr pane send-keys "$pane_id" enter
```

Remember: `agent send` does **not** append Enter; `pane run` does.

## Human steer / focus

| Goal | Command |
|---|---|
| Show whole fleet board | `herdr tab focus "$fleet_tab"` |
| Jump UI to one agent pane | `herdr agent focus reviewer` |
| Jump to workspace | `herdr workspace focus w26` |
| Attach/takeover terminal | `herdr agent attach reviewer` (optional `--takeover`) |
| Read without stealing focus | `herdr agent read reviewer --source recent-unwrapped --lines 80` |

Orchestrator rule: use `--no-focus` on create/split/start so fleet spawn doesn't yank the human away mid-layout. After spawn, **focus the fleet tab once** so all panes are visible. Focus a single agent only when they ask to type into it or to dismiss a `blocked` dialog.

Detach Herdr client (leave agents running): `prefix+q` (`ctrl+b` then `q`). Reattach: `herdr` in a terminal.

## Reading scrollback robustly

```bash
herdr pane read "$pane_id" --source recent-unwrapped --lines 80
herdr pane read "$pane_id" --source recent-unwrapped --lines 200   # widen if truncated
herdr pane read "$pane_id" --source visible --lines 50             # viewport only
herdr pane read "$pane_id" --source detection                      # detector bottom buffer
```

Prefer `recent-unwrapped` for agent transcripts (soft wraps joined). Use `--format ansi` only when colors are evidence.

If the answer clearly started above the window, increase `--lines` stepwise (80 → 160 → 300). There is no unbounded dump flag — widen deliberately.

## Broadcast pattern (manual)

Same idea as `scripts/broadcast.sh` (preferred one-liner: `scripts/broadcast.sh "$msg" reviewer tests docs`):

```bash
targets=(reviewer tests docs)
msg="Pull latest main and report branch + dirty state."

# Resolve names → pane ids once (agent send is text-only; pane run submits Enter)
panes=()
for t in "${targets[@]}"; do
  p=$(herdr agent get "$t" | python3 -c 'import sys,json; d=json.load(sys.stdin); a=d.get("result",{}).get("agent") or d.get("result",{}); print(a["pane_id"])')
  panes+=("$p")
done

# Send once per pane (do NOT also agent-send the same message)
for pane in "${panes[@]}"; do
  herdr pane run "$pane" "$msg"
done

# Concurrent completion: idle OR done (focused fleet tabs finish as idle)
for pane in "${panes[@]}"; do
  python3 scripts/wait_for_idle.py "$pane" --timeout 180 &
done
wait
```

Never wait only on `done` for the full budget after `herdr tab focus` — the fleet view is focused, so agents settle as `idle`.

## Troubleshooting

| Symptom | Check |
|---|---|
| CLI errors "server not running" | `herdr status`; user starts `herdr` once in a real TTY |
| Agent always `unknown` | `herdr integration install <agent>`; `herdr agent explain <target>` |
| Nested tmux breaks detection | Don't run tmux inside Herdr panes |
| `pane run` typed but agent idle | Send `herdr pane send-keys $pane enter`; re-wait `working` |
| Status stuck `working` | `pane read`; overall wait budget; escalate stall |
| `blocked` | Human must answer dialog; `agent focus` to show it |
| Panes too narrow | Fewer agents per tab, or tab-per-agent layout; alternate split directions |
| Wrong project files | Confirm `--cwd` and workspace label before spawn |
| Name not found | `herdr agent list`; names are unique session-wide |
| Accidentally focused spawn | Pass `--no-focus` on `tab create` / `agent start` / `pane split` |

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
| `tmux new-session -s name` | `herdr agent start … --split …` (or root pane of fleet tab) |
| session name | agent `name` + `pane_id` |
| `tmux send-keys … Enter` | `herdr pane run` |
| `tmux capture-pane -p -S -40` | `herdr pane read … --source recent-unwrapped --lines 40` |
| `tmux has-session` | `herdr agent get` / `herdr pane get` |
| `tmux kill-session` | `herdr pane close` / `herdr tab close` (fleet tab) |
| `tmux kill-server` | `herdr server stop` (confirm!) |
| multiple app terminal tabs | one fleet tab with tiled panes (default) |
