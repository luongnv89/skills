# Delivery, waiting, and monitoring (Herdr desktop app)

Rationale for Phases 4–6 of `hc-agent`. hc tracks what each program says it is doing (OSC 7501 status), but the app has no agent registry and no prompt-and-wait call. `scripts/agent.py` adds both. This file explains what it guarantees, and what to do when it reports anything other than `settled`.

## Status comes from the agent itself

An agent CLI reports its state with an OSC 7501 escape sequence, and hc keeps the latest one: `hc get <t> --json` → `.status` = `{app, state, msg}`, with `status_ms` (when it last changed) and `turn` (a turn counter). On Unix, hc clears the status when the terminal's root shell returns to the foreground, so an agent that exited does not leave a stale `done` behind. A nested shell is not detected, so `agent.py` treats a status reported while a shell is in the foreground as unverifiable.

| Status | Meaning | Ready for a prompt |
|---|---|---|
| `idle` | At rest, waiting for input | yes — sent with `hc send --if idle` |
| `done` | Finished a turn; the result is unseen | yes — plain `hc send` |
| `error` | Failed and stopped | yes, after you read why |
| `working` | A turn is in flight | no — refused, exit 6 |
| `blocked` | A person is needed (permission, question, auth; `msg` says what) | no — refused, exit 3 |
| `unverified` | An agent process with no status, or a status left at a shell | no — refused, exit 4 |
| `no-agent` | A shell, or nothing, in the foreground | no — refused, exit 5 |
| `exited` | The terminal is finished | no — exit 9 |

Kind detection uses `.status.app` (`claude-code` → `claude`), then the foreground process's argv0 (or the script `node`/`bun` runs). A plain program reports no status at all: never guess it from screen text.

## The prompt contract

```bash
python3 "$here/agent.py" prompt "$target" - --timeout 180 <<'EOF2'
<task text>
EOF2
```

1. **Resolve** the exact `hc-agent.name` label (or a `t…` address) among the terminals `herdr-app ls` shows in the root's tab. Your own terminal is refused.
2. **Check the text**: control characters are stripped (an embedded `ESC[201~` would end a paste early), an empty task is refused, and a task starting with `!` is refused, because Claude Code runs `!…` as a shell command.
3. **Preflight** with `hc get`. Anything but `idle`, `done` or `error` is refused, and nothing is typed.
4. **Baseline**: record the target's `turn` and `status_ms`.
5. **Send**: append the turn tag `(hc-agent turn <id>)` after a space on the task's last line (so a one-line task stays one line even if the paste is not bracketed), then `hc send --json --if idle -- <t> <text>` for an `idle` target, so hc itself refuses if the state changed since the preflight (exit 10, reported as the new state with `sent: false`). hc's `--if` accepts only `idle` and `working`, so a `done` or `error` target gets a plain `hc send` right after its fresh preflight; that leaves a short race. hc refuses a `blocked` target on its own (exit 9); `agent.py` never passes `--force`. The text goes after `--`, so a task starting with `-` stays text.
6. **Activity gate**: within `--activity-timeout` (15 s), `hc get` must show a status newer than the baseline. `working` marks the turn active.
7. **Settle**: a newer `done` or `error` ends the wait; `idle` ends it once `working` was seen or `turn` moved past the baseline, so a fast turn that went `working` → `idle` between polls still settles. A newer `blocked` ends it at once; a status that disappears mid-turn ends it as `unverifiable`; a finished terminal as `exited`. While the agent works, the script blocks in `hc wait <t> --timeout …` instead of polling, then re-reads `hc get` to decide.

So the turn you read back is the one you caused: an older `done` cannot satisfy the wait. `--raw` sends the text exactly (for a slash command such as `/compact`): no tag and no `!` check.

**Shell timeouts.** `hc send` waits up to 60 seconds for a person's unfinished draft before it types, and the turn wait runs after that inside the same call. Give the shell call a timeout above `--timeout` plus 60 seconds (Claude Code's Bash default is 2 minutes and its maximum 10). A killed call loses the outcome; then run `agent.py wait <name>` before anything else, because the worker is probably still working.

## Exit codes and responses

| Exit | Outcome | Do this |
|---|---|---|
| 0 | `settled` | Read the reply (below) |
| 1 | error | Read the message: missing tool, missing or ambiguous target, own terminal, bad text |
| 2 | usage | Fix the command line |
| 3 | `blocked` | `agent.py focus <name>`, tell the human; never answer the dialog. If `sent` is false, nothing was typed |
| 4 | `unverifiable` | No status, or it vanished mid-turn. Read the screen before anything else; a dialog may be up |
| 5 | `no_agent` | Start one with `launch_profile.py --start`, or ask |
| 6 | `working` | Wait (`agent.py wait`), then prompt |
| 7 | `stalled` | Sent, but no newer status: read the screen. Never blindly resend, which can double-submit |
| 8 | `timeout` | `agent.py get`, read the screen, then re-wait within a bounded budget |
| 9 | `exited` | The terminal finished; read the screen for why |

A timeout or stall does **not** prove the prompt was never delivered. Read before you resend. Re-wait at most 2–3 times, then escalate to the human.

## Waiting without prompting

```bash
python3 "$here/agent.py" wait reviewer --timeout 180                 # until settled
python3 "$here/agent.py" wait reviewer --until blocked --timeout 120 # until a dialog appears
```

`wait` returns at once for an already settled agent. With `--until blocked`, reaching `blocked` exits 0. Never `sleep` in a loop to wait for an agent.

## Reading the reply without burning context

```bash
python3 "$here/agent.py" read "$target" --turn "$turn"
```

It runs `hc read <t> --lines 400` (screen plus 400 history lines) and prints the lines below that turn's tag, which sits at the end of the echoed task, right above the reply. The tag is unique per turn, so a reply that quotes the task cannot move the anchor; matching ignores whitespace across lines, because TUIs hard-wrap prompts. For a task sent without a tag (by the human, or with `--raw`), `--after "<task's last line>"` anchors on its last 24 non-space characters instead. `--tail N` keeps only the last N lines. Relay the delta the user asked for, never the whole screen. Per hc's guide, history reads of a `working`, `blocked` or `error` terminal return only the screen.

### When the reply is longer than the window

`read --turn` exits 4 when the tag is not in the lines read. Raise `--lines` once; if that still misses, ask for a file:

```bash
python3 "$here/agent.py" prompt reviewer "Write your complete previous answer as Markdown to a new file under \$TMPDIR and reply with only its path." --timeout 60
python3 "$here/agent.py" read reviewer --turn <the new turn ID>
```

Read the path from that output, then read the file. For long *inputs*, write the material to a file and send one line naming its path.

## Concurrent fleet waits

```bash
python3 "$here/agent.py" broadcast "pull latest main and report status" reviewer tests docs
python3 "$here/agent.py" dispatch - <<'EOF2'
{"reviewer": "You are reviewer, a worker in an hc-agent fleet. … Review the last commit.",
 "tests": "You are tests, a worker in an hc-agent fleet. … Propose a minimal test plan."}
EOF2
```

`broadcast` sends one task to every target; `dispatch` sends each target its own task. Both resolve every target from one listing, dedupe, refuse unsafe targets, and prompt the rest in parallel threads, so wall clock is the slowest agent. They print `name: outcome (state) · turn <id>` per target (`--json` prints each full result) and exit 0 only when every target settled.

## Blocked is not success

Typical causes: workspace trust, a missing API key, a permission prompt, a plan-mode confirmation.

- Never send the next task while blocked; `agent.py prompt` refuses it, and so does `hc send` without `--force`.
- `agent.py focus <name>` brings the agent in front of the human. After they resolve it, re-check with `agent.py get`, then continue.

## Monitoring the fleet

```bash
python3 "$here/agent.py" fleet                       # root's tab, most urgent first
python3 "$here/agent.py" fleet --json                # machine-readable
python3 "$here/agent.py" fleet --fail-on-blocked     # exit 3 when any worker is blocked
```

The rows are the terminals `herdr-app ls` lists in the root's tab: terminals in other tabs and spaces, and background `hc run` terminals, never appear. Each row has a role: `worker` (labeled `hc-agent.role=worker` by `--start`), `main` (a HANDOFF successor), `other` (the user's own panes), or `root`. Workers come first, root last, and within a role rows sort by attention: `blocked`, `error`, `done`, `working`, `idle`, then `unverified`, `no-agent`, `exited`. Teardown closes only `worker` rows. Each row costs one `hc get`, so the table is polled, not an atomic snapshot: report it as "polled at <time>".

The app has no badge metadata and no notification command for agents, so there is nothing to add to the window. Tell the user in chat when a worker needs them.

## The run report

Report every target, including the ones that did not run. An agent missing from the report reads as success.

```text
Fleet: PARTIAL
Root kept: t2x (pane p…3b)
Workers: reviewer=settled, tests=settled, docs=BLOCKED (permission)
Layout: 4 panes in the root's tab · focus restored after each split
Replies: 2 read, 1 blocked, 0 timed out
```

Take each outcome from the `prompt` or `broadcast` output and the closing `agent.py fleet` call, not from memory of what you sent.
