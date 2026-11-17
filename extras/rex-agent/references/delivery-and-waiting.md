# Delivery, waiting, and monitoring (Rex)

Rationale for Phases 4–6 of `rex-agent`. Rex tracks what each program says it is doing (OSC 7501 program status), but it has no agent registry and no prompt-and-wait call. `scripts/agent.py` adds both. This file explains what it guarantees, and what to do when it reports anything other than `settled`.

## Status comes from the agent itself

An agent CLI reports its state with an OSC 7501 escape sequence. Rex keeps the latest report as the block's **root record**, readable with `rex block call -s S -b B program_status`. `agent.py` trusts a record only while its `owner.pid` equals the block's foreground process. A `done` record survives the agent exiting to its shell, and a new agent in the block does not inherit the old one's state.

| Status | Meaning | Ready for a prompt |
|---|---|---|
| `idle` | At rest, waiting for input | yes |
| `done` | Finished a turn; the result is unseen | yes |
| `error` | Failed and stopped | yes, after you read why |
| `working` | A turn is in flight | no — refused, exit 6 |
| `blocked` | A dialog needs a human (`kind`: permission, question, auth; `msg` says what) | no — refused, exit 3 |
| `unverified` | An agent process with no fresh record | no — refused, exit 4 |
| `no-agent` | A shell, or nothing, in the foreground | no — refused, exit 5 |
| `exited` | The block's program ended (kept open) | no — exit 9 |

Kinds observed live on 2026-10-16 (Rex build g7a93ec, 2026-10-15):

| Kind (`app`) | At rest | One turn | Dialog |
|---|---|---|---|
| claude (`claude-code`) 2.1.301 | `idle` at boot | `working` → `done` | `blocked`, `kind=permission`, `msg` "approve Bash: …" |
| codex (`codex`) 0.163.0 | `idle` | `working` → `idle` | not observed (the test config auto-approved) |
| codex 0.162.1 | removes its record | `working` → removed | the update prompt reported **nothing** |
| pi (`pi`) 1.3.0 | `idle` at boot | not observed | not observed |
| gemini (`gemini`) | `idle` at boot | not observed | not observed |
| opencode 2.0.28 | no record | no record | — |

Kind detection uses the record's `app`, then the process's `argv0` or `script`, never the process `name` (Claude Code's is its version, `2.1.301`; pi and gemini run as `node`).

## The prompt contract

```bash
python3 "$here/agent.py" prompt "$target_block" - --timeout 180 <<'EOF'
<task text>
EOF
```

1. **Resolve** the exact label (or full `block:` ID) from one `rex block ls --json`. Your own block is refused.
2. **Check the text**: a task starting with `!` is refused, because Claude Code runs `!…` as a shell command instead of a prompt.
3. **Preflight** with `process` and `program_status`. Anything not `idle`, `done`, or `error` is refused, and nothing is written.
4. **Baseline**: record the current root record's `updated_at`, and start `rex events -s S --json` (read by a thread, so events that arrive together are never stuck in a pipe buffer) before writing anything.
5. **Write**: strip control characters (an embedded `ESC[201~` would end the paste and turn the rest into keystrokes), append the turn tag `(rex-agent turn <id>)` on its own line, wrap the text in `ESC[200~ … ESC[201~` when the block's VT modes show `?2004h`, and send it with `rex send`. Then `rex send-key … enter`. Multi-line text into a block with bracketed paste off is refused, because each newline would submit early.
6. **Activity gate**: within `--activity-timeout` (10 s), a record newer than the baseline must appear; `working` marks the turn active.
7. **Settle**: a newer `done` or `error` ends the wait, even when `working` fell between polls, because only a finished turn writes them. A newer `idle` ends it only after `working` was seen. A newer `blocked` ends it at once; a removed record ends it as `unverifiable`. Events drive the wait; a poll every 0.5 s backs up a stream that attached late.

So the turn you read back is the one you caused: an older `done` cannot satisfy the wait, and a record from a previous process is ignored. `--raw` sends the text exactly (for a slash command such as `/compact`): no tag and no `!` check.

**Shell timeouts.** The wait runs inside your shell call. Give that call a timeout above `--timeout`: Claude Code's Bash default is 2 minutes and its maximum 10, so `--timeout 180` needs at least 210000 ms. For a turn that may run longer, start the prompt in the background and collect its JSON when it ends. A killed call loses the outcome; then run `agent.py wait <block>` before anything else, because the worker is probably still working.

## Exit codes and responses

| Exit | Outcome | Do this |
|---|---|---|
| 0 | `settled` | Read the reply (below) |
| 1 | error | Read the message: unreachable server, missing or ambiguous target, own block, bad text |
| 2 | usage | Fix the command line |
| 3 | `blocked` | `rex focus -s S <block>`, tell the human; never answer the dialog. If `sent` is false, nothing was written |
| 4 | `unverifiable` | No fresh record, or the record was removed mid-turn. Capture the screen before anything else; a dialog may be up |
| 5 | `no_agent` | Start one with `launch_profile.py --start`, or ask |
| 6 | `working` | Wait (`agent.py wait`), then prompt |
| 7 | `stalled` | Submitted, but no activity: capture the screen. Never blindly resend, which can double-submit |
| 8 | `timeout` | `agent.py get`, capture, then re-wait within a bounded budget |
| 9 | `exited` | The agent quit; read the screen for why |

A timeout or stall does **not** prove the prompt was never delivered. Read before you resend. Re-wait at most 2–3 times, then escalate to the human.

## Waiting without prompting

```bash
python3 "$here/agent.py" wait reviewer --timeout 180                 # until settled
python3 "$here/agent.py" wait reviewer --until blocked --timeout 120 # until a dialog appears
```

`wait` returns at once for an already settled agent, and otherwise waits on the same event stream as `prompt`. With `--until blocked`, reaching `blocked` exits 0.

## Reading the reply without burning context

```bash
python3 "$here/agent.py" read "$target_block" --turn "$turn"
```

`rex capture` returns only the visible screen, and agent TUIs run on the alternate screen, so no scrollback exists to widen. `--turn` prints the rows below that turn's tag, which sits at the end of the echoed task, right above the reply, even when the start of a long task has scrolled off. The tag is unique per turn, so a reply that quotes the task cannot move the anchor; matching ignores whitespace across rows, because TUIs hard-wrap prompts. For a task sent without a tag (by the human, or with `--raw`), `--after "<task's last line>"` anchors on its last 24 non-space characters instead, and a reply that repeats them can fool it. Runs of blank rows collapse to one. Relay the delta the user asked for, never the whole screen.

### When the reply is longer than the screen

`read --turn` exits 4 when the tag is no longer on screen. Only then, ask for a file:

```bash
python3 "$here/agent.py" prompt reviewer "Write your complete previous answer as Markdown to a new file under \$TMPDIR and reply with only its path." --timeout 60
python3 "$here/agent.py" read reviewer --turn <the new turn ID>
```

Read the path from that output, then read the file. For long *inputs*, write the material to a file and send one line naming its path.

## Concurrent fleet waits

```bash
python3 "$here/agent.py" broadcast "pull latest main and report status" reviewer tests docs
python3 "$here/agent.py" dispatch - <<'EOF'
{"reviewer": "You are reviewer, a worker in a Rex agent fleet. … Review the last commit.",
 "tests": "You are tests, a worker in a Rex agent fleet. … Propose a minimal test plan."}
EOF
```

`broadcast` sends one task to every target; `dispatch` sends each target its own task, which is how first tasks carry each worker's own preamble. Both resolve every target from one listing, dedupe, refuse unsafe targets, and prompt the rest in parallel threads, so wall clock is the slowest agent. They print `name: outcome (state) · turn <id>` per target (`--json` prints each full result) and exit 0 only when every target settled.

## Agents without program status

An agent that reports nothing (opencode 2.0.28) is `unverified`, and `prompt` refuses it. `launch_profile.py --start` cannot start one either, because readiness needs an `idle` record: start it by hand with `rex split … -- opencode`, then drive it with the fallback below. `--settle screen` is the explicit, weaker fallback: it waits for the screen to change and then hold still for `--quiet` seconds. A dialog that reports nothing looks exactly like an idle agent, and Enter picks its default option: a test sent a prompt into Codex 0.162.1's update screen, and that Enter installed an update. So before `--settle screen`, capture the screen and confirm the agent sits at its input prompt.

## Blocked is not success

Typical causes: workspace trust, a missing API key, a permission prompt, a plan-mode confirmation.

- Never send the next task while blocked; `agent.py prompt` refuses it anyway.
- `rex focus -s "$session" <block_id>` brings the dialog in front of the human. When they look at another session, `rex -C <client> do session.select session_id="$session"` switches a connected app to it. Check `rex -C <client> actions` first; `rex skill show` documents client actions.
- After they resolve it, re-check with `agent.py get`, then continue.

## Monitoring the fleet

```bash
python3 "$here/agent.py" fleet                       # root window, most urgent first
python3 "$here/agent.py" fleet --all --json          # every window, machine-readable
python3 "$here/agent.py" fleet --fail-on-blocked     # exit 3 when any worker is blocked
```

Each row has a role: `worker` (started by `--start`: its process carries `REX_AGENT_ROLE`), `other` (a readable process without it, such as the user's own shell or agent), `unknown` (the process environment is unreadable, for example on a remote server), or `root`. Workers come first, root last, and within a role rows sort by attention: `blocked`, `error`, `done`, `working`, `idle`, then `unverified`, `unknown`, `no-agent`, `exited`. Teardown closes only `worker` rows unless the user names another block. Each row costs two calls (`process` and `program_status`), so the table is polled, not an atomic snapshot: report it as "polled at <time>".

Rex's own interface carries the human's view. Unfocused tab headers show a spinner or a blocked symbol, the session picker marks sessions with finished or blocked work, and each worker's label names its job. Rex has no notification command and no badge metadata, so there is nothing to add.

## The run report

Report every target, including the ones that did not run. An agent missing from the report reads as success.

```text
Fleet: PARTIAL
Root kept: block:…3f21
Workers: reviewer=settled, tests=settled, docs=BLOCKED (permission)
Layout: 4 columns at 25.0%
Replies: 2 read, 1 blocked, 0 timed out
```

Take each outcome from the `prompt` or `broadcast` output and the closing `agent.py fleet` call, not from memory of what you sent.
