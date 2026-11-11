# hc recipes for agent fleets

Read this for the scripts resolver, spawn waves, what `--start` runs, steering, teardown, multi-line prompts, and edge cases. Delivery, waiting, and monitoring live in `references/delivery-and-waiting.md`; the operation-by-operation comparison with herdr-agent lives in `references/app-vs-tui.md`. For everyday app tasks outside fleet work, `hc --skill` and `herdr-app --skill` print the guides that match the installed CLIs.

## Default fleet layout

**Root + workers as splits to the right, in the root's tab:**

```
Space: <root's space>
└── Tab: <root's tab>                      ← one row of panes
    ┌───────────┬───────────┬───────────┐
    │ root (you)│ reviewer  │ tests     │
    └───────────┴───────────┴───────────┘
```

The app sizes the columns. Two columns were observed at equal widths; three or more are unverified, and there is no command to resize a pane or set a split ratio. `layout.resize` sizes window layout nodes, not terminal panes: never use it for the fleet.

## Find the scripts

Set `here` to the `scripts/` directory beside SKILL.md. When the harness does not show the skill's base directory, probe the install locations, repo-local first so a pinned checkout wins over a global install:

```bash
here=""
for cand in "skills/hc-agent/scripts" ".agents/skills/hc-agent/scripts" \
  ".claude/skills/hc-agent/scripts" "$HOME/.claude/skills/hc-agent/scripts" \
  "$HOME/.agents/skills/hc-agent/scripts"; do
  [ -f "$cand/agent.py" ] && { here="$cand"; break; }
done
[ -n "$here" ] || { echo "Error: hc-agent scripts not found; set \$here to the skill's scripts/ directory" >&2; exit 1; }
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

A failed start stops the wave instead of building on a half-made row. Each start prints one JSON line: `name` (with a suffix if the name was taken), `terminal`, `pane`, `split_from`, `kind`, `outcome`, `cwd`, and `focus_restored`. Use that `name` and `terminal` from then on. Give the wave's first tasks with `agent.py dispatch` (one task per worker, each opening with its own worker preamble), or with one `agent.py prompt` per worker.

Overrides, one field each, only when the user named it:

```bash
python3 "$here/launch_profile.py" … --start tests --thinking low          # one field named
python3 "$here/launch_profile.py" … --start critic --kind codex           # another kind inherits nothing
python3 "$here/launch_profile.py" … --start docs --without bypass         # no inherited permission bypass
python3 "$here/launch_profile.py" … --start lint -- --add-dir ../shared   # native flags after --
```

### What `--start` runs

1. Resolves the profile and the worker argv (`references/launch-profile.md`), and refuses a bad name with exit 2.
2. Reads `focused_pane` from `herdr-app status`, the pane to give focus back to. It is root's pane only if the user was there; restoring root unconditionally could switch the user's view to another space.
3. Picks the pane to split: the newest terminal in the root's tab labeled by this skill, else root's own pane.
4. Runs `herdr-app do pane.split --direction right --pane <that pane> --argv '["/bin/sh","-c","cd \"$0\" && exec \"$@\"","<dir>", <worker argv>…]'`. The argv is a JSON array, so no value passes through a shell prompt or its history; the `sh` wrapper only changes folder and then replaces itself with the worker.
5. Labels the new terminal at once with `hc label --json <t> hc-agent.role=<worker|main> hc-agent.name=<name> hc-agent.space=<space> hc-agent.tab=<tab>`, before anything is sent to it.
6. Always (even when the split or the labeling failed) runs `herdr-app do pane.focus --pane <saved pane>` and re-reads `herdr-app status` to report `focus_restored`.
7. Polls `hc get <t>` until the worker reports `idle` or `done` (`--timeout`, default 60 seconds). `blocked` exits 3, `error` or a finished terminal exits 1, and no status before the timeout exits 1.

Exit codes: `0` ready, `1` failed (the message names any orphan terminal and pane), `2` usage, `3` booted into a dialog. Never retry a failed start blindly: read the orphan with `hc read <t> --lines 40` and ask before closing it.

It never calls `terminal.open` or `terminal.keep` (they place relative to the focused pane) or `hc run` (its terminals end with their parent unless `--outlive-parent`, and an unlabeled one stays hidden from the window).

## Multi-line and code-heavy prompts

`hc send` pastes the text and then presses Enter, per its help, so pass the whole task through `agent.py prompt … -` with a quoted heredoc. Multi-line paste was not exercised live; for a very long input, write the material to a file and send one line naming its path.

## Steer and take over

- `python3 "$here/agent.py" focus <name>` runs `herdr-app do agent.focus --terminal <t>`, falling back to `herdr-app do pane.focus --pane <p>`. It changes what the person sees: use it when they asked, or when a worker is blocked.
- For UI keys, such as dismissing a menu the user asked you to dismiss, use `hc keys <t> esc` on the terminal address. Never press keys into a dialog that needs the human.
- To type into a worker directly, the user can run `hc attach <t>` in a terminal of their own and press ctrl+\ to detach. `hc attach --observe` watches without typing.
- Interrupting a runaway turn: `hc interrupt <t>` presses the stop key and reports what happened. Ask before interrupting someone else's agent.

## Tear down

```bash
python3 "$here/agent.py" fleet                                  # candidates: role worker
python3 "$here/agent.py" close reviewer tests --confirmed       # only after the user said yes
```

`close` refuses the root terminal, a `main` successor, the user's own panes, and anything outside the root's tab, and prints one JSON line per target. To close a pane the user explicitly names that is not a worker, run `herdr-app do pane.close --pane <p>` yourself after their confirmation. Never `hc kill` a terminal you did not start, and never `hc server stop`.

## Edge cases

- **`blocked` target:** `agent.py focus <name>`, tell the user, never answer the dialog, never send with `--force`.
- **Unverifiable target (no status):** read the screen with `hc read <t> --lines 40`. A dialog that reports nothing looks exactly like an idle agent; never type into it.
- **Finished target:** its program exited; read why with `hc read`, then ask before closing the pane.
- **Name collision:** `--start` suffixes the name with an epoch. A name that looks like an address (`t7`, `t2x`) is refused, because hc treats such words as addresses.
- **Ambiguous name:** two terminals in the tab carry the same `hc-agent.name`; pass the `t…` address instead.
- **Focus did not come back after a split:** `--start` warns and reports `focus_restored: false`. Tell the user before they type, because keystrokes now go to the new worker; run `herdr-app do pane.focus --pane <their pane>` once.
- **Worker started in the wrong folder:** `--start` warns when `hc get` reports another folder. Prompts can still name absolute paths; ask before closing and respawning it.
- **Wrapper without `--`:** the profile aborts. Ask the user; `--without wrapper` launches the harness binary directly and may use another account.
- **Successor never acks:** the HANDOFF failed. Stay main, keep the fleet, report the orphan terminal, and ask before closing it.
- **Both `HERDR_ENV=1` and `HC_TERMINAL_ID` set:** a Herdr TUI runs inside an app terminal, and this agent is in a TUI pane. Use herdr-agent.
- **Neither set:** not a Herdr terminal. Stop, `BLOCKED`.
- **More than four columns:** warn that they get cramped; add more only with the user's approval.
