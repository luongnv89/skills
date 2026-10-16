# Rex recipes for agent fleets

Read this for the layout, spawn variants, equal-width semantics, multi-line prompts, human steer and focus, troubleshooting, and edge cases. Delivery, waiting, and monitoring live in `references/delivery-and-waiting.md`. For everyday Rex commands outside fleet work (a diff tab, a dev server, a test run), `rex skill show` prints the guide that matches the installed CLI.

## Default fleet layout

**Root + workers as equal-width columns in one window:**

```
Session: <session label>
└── Window: <root's window>                ← one row of columns
    ┌───────────┬───────────┬───────────┐
    │ root (you)│ reviewer  │ tests     │
    └───────────┴───────────┴───────────┘
```

The human sees the root agent and every worker at the same size, the orchestrator never moves to a side tab, and Rex's tab header shows the fleet's spinner and blocked symbols.

## Find the scripts

Set `here` to the `scripts/` directory beside SKILL.md. When the harness does not show the skill's base directory, probe the install locations, repo-local first so a pinned checkout wins over a global install:

```bash
here=""
for cand in "skills/rex-agent/scripts" ".agents/skills/rex-agent/scripts" \
  ".claude/skills/rex-agent/scripts" "$HOME/.claude/skills/rex-agent/scripts" \
  "$HOME/.agents/skills/rex-agent/scripts"; do
  [ -f "$cand/agent.py" ] && { here="$cand"; break; }
done
[ -n "$here" ] || { echo "Error: rex-agent scripts not found; set \$here to the skill's scripts/ directory" >&2; exit 1; }
```

## Spawn a wave

```bash
main_model=""      # your exact model ID, e.g. claude-opus-5-5; empty if unknown
main_thinking=""   # empty on Claude Code: the script reads CLAUDE_EFFORT
python3 "$here/launch_profile.py" --main-model "$main_model" --main-thinking "$main_thinking" >/dev/null
# Relay the summary line (and any ⚠ or warning: line) before the next call.

for name in reviewer tests; do
  python3 "$here/launch_profile.py" --main-model "$main_model" --main-thinking "$main_thinking" \
    --start "$name" --cwd "$project_dir" || { echo "Error: $name did not start; stopping the wave" >&2; exit 1; }
done
python3 "$here/agent.py" fleet --fail-on-blocked || { echo "Fleet not clean; resolve before assigning work" >&2; exit 1; }
```

A failed start stops the wave instead of building on a half-made grid. Each start prints one JSON line: `name` (with a suffix if the name was taken), `block_id`, `window_id`, `kind`, `outcome`, and the column `widths`. Use that `name` and `block_id` from then on. Give the wave's first tasks with `agent.py dispatch` (one task per worker, each opening with its own worker preamble), or with one `agent.py prompt` per worker.

Overrides, one field each, only when the user named it:

```bash
python3 "$here/launch_profile.py" … --start tests --thinking low          # one field named
python3 "$here/launch_profile.py" … --start critic --kind codex           # another kind inherits nothing
python3 "$here/launch_profile.py" … --start docs --without bypass         # no inherited permission bypass
python3 "$here/launch_profile.py" … --start lint -- --add-dir ../shared   # native flags after --
```

### What `--start` runs

```text
rex split -s S -b <rightmost> --split=right --focus=false --label NAME -c DIR --keep-open --json \
  -- "$SHELL" -ic 'exec "$0" "$@"' env REX_AGENT_ROLE=NAME <binary> <profile argv…>
```

- **Through the interactive shell.** A split command gets the login environment but not the shell's rc file. A live check found an rc-only export (`PI_9ROUTER_FREE_ONLY`) and an MCP API key missing without the wrapper. `exec "$0" "$@"` then replaces the shell with the agent and passes every argument as its own word. Nothing is quoted or retyped, and nothing reaches shell history. Shells other than sh, bash, zsh, dash, ksh, or mksh start the worker directly, with a warning.
- **The same install as main.** A same-kind worker runs the root process's `invoked_path`, so it gets the same binary and version.
- **Fail fast.** A flag the CLI rejects exits at once. `child_exited` ends the readiness wait, and `--keep-open` keeps the error on screen; the start prints its last lines.
- **Readiness.** The worker counts as ready only on an `idle` or `done` record from its own process. A dialog at boot that reports `blocked` exits 3. A dialog that reports nothing times out, and the start never types into it.

## Equal-width columns — verified semantics

Confirmed live against Rex build g7a93ec (2026-10-15) in a throwaway session:

- A window's tiled layout is a binary tree. Each split has a `direction` (`horizontal` for side-by-side), a `ratio`, and `before`/`after` children. `rex session inspect S --json` reports each node's `rect` as fractions of the window.
- `rex split --ratio 30` gives the **new** block 30% of the anchor. `session.resize_pane` sets the ratio of the split between two adjacent blocks to the **before** side's share. The two run in opposite directions, so `--start` splits with the default and sets every ratio through the API.
- For a row of N columns, `grid.py equalize` sets each horizontal split to `leaves(before) / leaves(split)`. One pass lands every column on exactly `1/N` (verified: 3 → 1/3 each, 5 → 0.2 each), and it works for left- or right-nested trees.
- `grid.py` refuses a window with a vertical split anywhere, because equal columns would reshape the user's stacked panes. Ask the user to close or move that pane, or use `--new-window`.

```bash
python3 "$here/grid.py" plan        # the rightmost column's block ID
python3 "$here/grid.py" equalize    # set every ratio, verify within 0.2%, print widths
```

### Tab-per-agent

Use it when the user asks for a full tab per agent, when a TUI needs width (diff-heavy review), or when more than four columns would be cramped:

```bash
python3 "$here/launch_profile.py" … --start reviewer --cwd "$project_dir" --new-window
```

It runs `rex window new` (labelled with the name, `--focus=false`) and labels the block too, so `agent.py` resolves it the same way.

### A log or shell pane in the grid

```bash
anchor=$(python3 "$here/grid.py" plan) || exit 1
rex split -s "$session" -b "$anchor" --split=right --focus=false --label logs -c "$project_dir" --json -- tail -n 100 -f app.log
python3 "$here/grid.py" equalize || echo "Error: equalize failed; the logs block is in place but columns are uneven" >&2
```

## Sending multi-line or code-heavy messages

`agent.py prompt` sends the text as one bracketed paste when the block has that mode on (Claude Code, Codex, and zsh do), so newlines, fences, and quotes arrive as text rather than as Enter presses. Pass long text on stdin:

```bash
python3 "$here/agent.py" prompt reviewer - --timeout 180 <<'EOF'
Review these files:
- src/a.ts
- src/b.ts

Return only:
1. bugs
2. missing tests
EOF
```

Always pass task text through a quoted heredoc (`<<'EOF'`): inside double quotes, the orchestrator's own shell would expand `$` and backticks before the worker sees them. For material the agent should read rather than be told, write it to a file and send one line naming the path. To relay one worker's reply to another (a review debate), ask the first to write its answer to a file under `$TMPDIR` and send the second one line naming that path, instead of pasting screens between agents.

Raw keys for interactive UI controls use Rex key syntax: `rex send-key -s "$session" -b <block_id> escape`, `ctrl+c`, `shift+tab`. Letter names are case-insensitive; use `rex send` for exact text. Never send keys to a block in an unverified state.

## Human steer and focus

| Goal | Command |
|---|---|
| See the whole fleet | Already one window (root + workers) |
| Move focus to one worker | `rex focus -s "$session" <block_id>` |
| Maximize a worker, then restore | `rex zoom -s "$session" <block_id> --on`, then `--off` |
| Show this session in a connected app | `rex -C <client> do session.select session_id="$session"` |
| Read without stealing focus | `python3 "$here/agent.py" read <block_id> --turn <turn>` |

New blocks and windows take focus by default; the scripts always pass `--focus=false`. Focus a worker only when the human wants to type into it or answer a `blocked` dialog.

## Troubleshooting

| Symptom | Check |
|---|---|
| `rex` exits 4 | The server is unreachable: ask the user to open the Rex app. Never pass `--autostart` to start one |
| `agent.py check` says not this terminal | `REX_BLOCK` is inherited from a closed block: open a new Rex terminal |
| Worker landed in a new tab | `--new-window` was passed; the default is a column in root's window |
| Unequal columns | `python3 "$here/grid.py" equalize`; a vertical split makes it refuse |
| `unverified` worker | Its CLI reports no program status, or a silent dialog is up: capture the screen |
| Worker shows the wrong model or effort | Read its launch-profile summary: an `UNKNOWN` field fell back to config; pass `--main-model` / `--main-thinking` |
| `prompt` stalled | Submitted, no activity: capture before any resend |
| Start timed out | Capture the block: a dialog, a login screen, or an update prompt that reports nothing |
| A worker renamed the session or split a pane | Rex's session-start hook tells every new agent to name the session and use rex; the worker preamble in SKILL.md Phase 4 tells workers not to. A worker's stacked pane makes later starts refuse the layout |
| `prompt` refused a task starting with `!` | Claude Code would run it as a shell command; reword it, or pass `--raw` |
| A shell call died before `prompt` printed | Its timeout was shorter than `--timeout`; run `agent.py wait <block>` before anything else |
| Name not found | `agent.py fleet --all`; names are block labels, matched exactly |
| A teardown closed the wrong thing | Close only full block IDs this run created; never a label |

### Debug one block

```bash
rex block inspect -s "$session" <block_id> --json
rex block call -s "$session" -b <block_id> process
rex block call -s "$session" -b <block_id> program_status
rex capture -s "$session" -b <block_id> --unwrap
```

## Edge cases

- `blocked`: focus the block, tell the human, and request their action.
- `unverified`: capture the screen before anything else. Use `--settle screen` only after the capture shows the agent at its input prompt. A CLI without program status (opencode) cannot pass `--start` readiness: start it by hand and say the wait is weaker.
- `exited`: read the kept-open screen for the CLI's own message; start a new worker rather than typing into a shell.
- Name collision: the start suffixes the name with an epoch; use the printed `name` and `block_id`, and never reuse an existing worker by accident.
- A block left from an earlier run: `agent.py fleet` marks it `worker` when its process carries `REX_AGENT_ROLE`; ask before reusing or closing it.
- A name made only of hex letters (`beef`, `cafe`): safe through `agent.py`, which matches labels exactly; never pass one to `-b` yourself.
- More than four columns: warn that columns become cramped; change the layout only with user approval.
- The window is not one row: stop and ask. Never reshape the user's panes.
- Wrong session or window: stop, preserve work, and ask before moving or closing blocks.
- Successor never acks: the HANDOFF failed. Stay main, keep the fleet, and report the orphan block before asking to close it.
- Root argv unreadable, or the server is remote: same-kind setup flags cannot be inherited. Abort, or use `--without flags` only when reduced inheritance is intentional.
- A start exits at once after inheriting a flag: the CLI rejected it. Read the printed screen lines before retrying.

## Mapping from herdr-agent and tmux

| herdr-agent | rex-agent |
|---|---|
| workspace / tab / pane | session / window / block |
| `HERDR_PANE_ID`, `HERDR_TAB_ID` | `REX_BLOCK`; window from `agent.py check` |
| `herdr status` | `agent.py check` (`rex whoami --autostart=false` + capability probe) |
| `next_grid_split.py` + iterative `--equalize` | `grid.py equalize` (exact ratios, one pass) |
| `herdr agent start` | `launch_profile.py --start` (split + launch + equalize + readiness) |
| `herdr agent prompt --wait` | `agent.py prompt` |
| `herdr agent read --source recent-unwrapped` | `agent.py read --turn` (visible screen only) |
| `herdr api snapshot` | `agent.py fleet` (polled) |
| badges, `herdr notification show` | block labels; Rex's own tab and session indicators |
| `herdr pane close` | `rex block close -s S <block_id>` |

From tmux-agent-comms: `tmux split-window` becomes `launch_profile.py --start`, `send-keys … Enter` becomes `agent.py prompt`, `capture-pane` becomes `agent.py read`, and `kill-pane` becomes `rex block close` after confirmation.
