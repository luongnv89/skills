# Herdr recipes for agent fleets

Read this when you need layouts beyond the default tab-per-agent spawn, multi-line sends, human steer/focus, scrollback recovery, or troubleshooting.

## Default fleet layout (this skill)

```
Session (default)
└── Workspace: <project>          ← one per repo
    ├── Tab: reviewer  → pane wN:pA  (agent "reviewer")
    ├── Tab: tests     → pane wN:pB  (agent "tests")
    └── Tab: docs      → pane wN:pC  (agent "docs")
```

Why tabs not splits: each agent gets a full viewport; the human jumps with a click or `herdr agent focus <name>`; sidebar status rolls up per workspace.

### Create workspace + three agent tabs

```bash
project_dir=/path/to/project
label=$(basename "$project_dir")
ws=$(herdr workspace create --cwd "$project_dir" --label "$label" --no-focus \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["workspace"]["workspace_id"])')
# If the create payload nests differently on your herdr version, print the JSON once and pick the workspace_id field.

for name in reviewer tests docs; do
  j=$(herdr tab create --workspace "$ws" --cwd "$project_dir" --label "$name" --no-focus)
  pane=$(printf '%s' "$j" | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["root_pane"]["pane_id"])')
  herdr pane rename "$pane" "$name"
  herdr agent rename "$pane" "$name"
  herdr pane run "$pane" "pi --thinking medium"
done
```

### When to use splits instead

- User asks for "side by side" / "split pane"
- Comparing two agents' output in one view
- Logs + agent in the same tab

```bash
herdr agent start logs --cwd "$project_dir" --workspace "$ws" --tab "$tab_id" \
  --split right --no-focus -- bash -lc 'tail -f /tmp/app.log'
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
| Jump UI to agent | `herdr agent focus reviewer` |
| Jump to tab | `herdr tab focus w26:t2` |
| Jump to workspace | `herdr workspace focus w26` |
| Attach/takeover terminal | `herdr agent attach reviewer` (optional `--takeover`) |
| Read without stealing focus | `herdr agent read reviewer --source recent-unwrapped --lines 80` |

Orchestrator rule: use `--no-focus` on create/split/start so fleet spawn doesn't yank the human away. Focus only when they ask to steer or when you need them to dismiss a `blocked` dialog.

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

Same idea as `scripts/broadcast.sh`:

```bash
targets=(reviewer tests docs)
msg="Pull latest main and report branch + dirty state."

for t in "${targets[@]}"; do
  herdr agent send "$t" "$msg"
  # resolve pane for Enter if needed — agent send is text-only
done
# Better: map names → pane_ids once, then pane run each.

for pane in "${panes[@]}"; do
  herdr pane run "$pane" "$msg" &
done
wait

for pane in "${panes[@]}"; do
  herdr wait agent-status "$pane" --status done --timeout 180000 &
done
wait
```

## Troubleshooting

| Symptom | Check |
|---|---|
| CLI errors "server not running" | `herdr status`; user starts `herdr` once in a real TTY |
| Agent always `unknown` | `herdr integration install <agent>`; `herdr agent explain <target>` |
| Nested tmux breaks detection | Don't run tmux inside Herdr panes |
| `pane run` typed but agent idle | Send `herdr pane send-keys $pane enter`; re-wait `working` |
| Status stuck `working` | `pane read`; overall wait budget; escalate stall |
| `blocked` | Human must answer dialog; `agent focus` to show it |
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
| `tmux new-session -s name` | `herdr tab create` (+ `agent rename`) or `herdr agent start` |
| session name | agent `name` + `pane_id` |
| `tmux send-keys … Enter` | `herdr pane run` |
| `tmux capture-pane -p -S -40` | `herdr pane read … --source recent-unwrapped --lines 40` |
| `tmux has-session` | `herdr agent get` / `herdr pane get` |
| `tmux kill-session` | `herdr tab close` / `herdr pane close` |
| `tmux kill-server` | `herdr server stop` (confirm!) |
| app terminal tab | Herdr tab (already visible in workspace UI) |
