# Delivery and waiting (Herdr)

Rationale for Phase 4–5 of `herdr-agent`. Herdr 0.9 submits a prompt and
starts the wait in **one** server-side request. Use that. Everything below is
about the cases it does not cover.

## The one-call contract

```bash
herdr agent prompt <target> "<task>" --wait --timeout 180000
```

That single call does all of this server-side:

| Step | What Herdr guarantees |
|---|---|
| Refusal | A `blocked` target is rejected with `agent_blocked` **before any input is written** |
| Submission | Text plus encoded Enter as one ordered write, honoring the pane's live bracketed-paste mode |
| Activity gate | Waits up to 5s for observed `working` or `blocked`; unrelated state changes do not satisfy it |
| Settle | Then waits for the first settled `idle`, `done`, or `blocked` |

`--wait` already defaults to those settled states. Do **not** add `--until idle
--until done`; pass `--until` only for a state-specific wait such as
`--until blocked`.

This is why the old pre-send transcript baseline and `HERDR_DONE_` completion
marker are gone. They existed to tell "this reply" from "the reply already on
screen" across two separate calls. One request has no gap to race.

Exit status is 1 for a server error, 2 for a CLI syntax error, and the error
body is JSON on stderr:

| Error code | Meaning | Do this |
|---|---|---|
| `agent_blocked` | A dialog is up; nothing was sent | `herdr agent focus <target>`, ask the human |
| `agent_prompt_stalled` | Submitted, but no activity followed within 5s | Inspect with `agent get` / `agent read`; do **not** blindly resend |
| `timeout` | No settled state inside your budget | Inspect, then retry within a bounded budget |
| `agent_not_found` | The pane hosts no detected agent | Use the pane-surface fallback below |
| `agent_not_ready` | Returned by `agent start` when the agent booted into a dialog | The name still works for `read` and `send-keys` |

A timeout or stall does **not** prove the prompt was never delivered. Read
before you resend.

## What the server does not check

`agent prompt` refuses `blocked`. It does **not** refuse `working`, and its wait
tracks **lifecycle state, not one turn**: if the target is already working, the
turn already in flight can satisfy your wait, and you read back the wrong reply.

So the fail-closed `working` check stays yours:

```bash
python3 "$here/preflight_send.py" reviewer || exit $?   # 2 working, 3 blocked,
                                                        # 4 unverifiable, 5 no agent
herdr agent prompt reviewer "$task" --wait --timeout 180000
herdr agent read reviewer --source recent-unwrapped --lines 80
```

`$here` is the skill's `scripts/` directory, resolved by probing install
locations (repo-local first) rather than from `$0`:

```bash
here=""
for cand in "skills/herdr-agent/scripts" ".agents/skills/herdr-agent/scripts" \
  ".claude/skills/herdr-agent/scripts" "$HOME/.claude/skills/herdr-agent/scripts" \
  "$HOME/.agents/skills/herdr-agent/scripts"; do
  [ -f "$cand/preflight_send.py" ] && { here="$cand"; break; }
done
[ -n "$here" ] || { echo "Error: skill scripts not found in any install location" >&2; exit 1; }
```

## Status meanings

| Status | Meaning |
|---|---|
| `working` | A turn is in flight |
| `blocked` | Herdr recognized an approval or question UI; a human is needed |
| `done` | Settled, and the completion has not been seen yet |
| `idle` | Settled and seen, or never worked |
| `unknown` | An agent is present but Herdr cannot classify it — **not** proof of completion |

`idle` and `done` both mean ready for input; the difference is only whether the
server has marked the completion seen. Explicit focus commands mark it seen,
reads do not, and each TUI client tracks that independently. Accept either.

## Waiting without prompting

For an agent someone else started, or to watch for a dialog:

```bash
herdr agent wait reviewer --timeout 180000                 # settled: idle|done|blocked
herdr agent wait reviewer --until blocked --timeout 120000 # state-specific
```

`agent wait` is server-owned and event-driven. It pins the resolved pane
occupant, so a replacement agent in that pane cannot satisfy the wait. Prefer it
over any polling loop.

## Concurrent fleet waits

Each `agent prompt --wait` is self-contained, so a fleet is just N background
jobs. Wall clock is the slowest agent, not the sum.

```bash
pids=()
for name in reviewer tests docs; do
  python3 "$here/preflight_send.py" "$name" >/dev/null || { echo "skip $name" >&2; continue; }
  herdr agent prompt "$name" "$msg" --wait --timeout 180000 >"/tmp/$name.out" 2>"/tmp/$name.err" &
  pids+=("$!:$name")
done
overall=0
for e in ${pids[@]+"${pids[@]}"}; do
  jp="${e%%:*}"; name="${e#*:}"
  if wait "$jp"; then
    echo "$name: settled"
  else
    code="$(sed -n 's/.*"code"[[:space:]]*:[[:space:]]*"\([a-z_]*\)".*/\1/p' "/tmp/$name.err" | head -1)"
    echo "$name: failed (${code:-unknown})" >&2
    overall=1
  fi
done
exit "$overall"
```

Prefer `scripts/broadcast.sh "$msg" reviewer tests docs` — it does exactly this,
plus one-call target resolution, dedupe, the `working` refusal, error-code
mapping, and optional sidebar badging.

## Reading the reply without burning context

```bash
herdr agent read <target> --source recent-unwrapped --lines 80
```

Sources: `visible` (rendered viewport), `recent` (recent output with soft
wraps), `recent-unwrapped` (soft wraps joined — use this for transcripts),
`detection` (the bottom-buffer snapshot the detector reads). Add
`--format ansi` only when color is evidence.

Relay the delta the user asked for, never the whole pane.

### When the reply is longer than the pane can show

If raising `--lines` reveals no more output, the agent is running on the
terminal's **alternate screen**. Rows that scroll off it never enter Herdr's
host scrollback, so no line count recovers them.

Fallback, only after that read failed — do not ask for it up front:

```bash
herdr agent prompt reviewer "Write your complete previous answer as Markdown to a file under \$TMPDIR and reply with only that path." --wait --timeout 60000
path="$(herdr agent read reviewer --source recent-unwrapped --lines 10 | tail -3 | grep -o '/[^ ]*\.md' | tail -1)"
cat "$path"
```

## Blocked is not success

Typical causes: workspace trust, a missing API key, a permission prompt, a
plan-mode confirmation.

- Never send the next task while blocked. `agent prompt` refuses it anyway.
- `herdr agent focus <name>` so the human sees the dialog.
- `herdr notification show "Agent blocked" --body "<name> needs input" --sound request`
  when the human may not be looking at that workspace.
- After they resolve it, re-check status, then continue.

## Timeouts and anti-deadloop

| Budget | Suggested default |
|---|---|
| `agent start` readiness | 60000 ms (its own default is 30000) |
| Task completion | 180000 ms, tuned per task |
| Re-waits after a timeout | 2–3, then escalate to the human |

On timeout:

1. `herdr agent get <target>` — current status and revision
2. `herdr agent read <target> --source recent-unwrapped --lines 80`
3. `herdr agent explain <target> --json` when the status itself looks wrong
4. Report the stall. Do not loop forever.

## Fallback: panes with no detected agent

The agent surface addresses only detected agents. A pane running an
unrecognized process returns `agent_not_found` from `agent get`, `prompt`, and
`wait`, even though `herdr pane get` reports its `agent_status` as `unknown`.

Reach for this path only when `preflight_send.py` exits 5:

1. Try `herdr integration install <agent>`, or start the agent through
   `herdr agent start <name> --kind KIND --pane <id>` so it is detected. This is
   the real fix; everything below is worse in every way.
2. Otherwise use the pane surface: `herdr pane run <pane> "<text>"` submits text
   and Enter atomically, and `herdr pane wait-output <pane> --match "<text>"`
   or `--regex "<pattern>"` waits on output rather than state. Note that
   `wait-output` searches the current snapshot immediately, so text already on
   screen matches.
3. `python3 "$here/wait_for_idle.py" <pane_id> --timeout 180 --lines 80` remains
   the content-stability waiter for this case. It polls `herdr pane get` and
   compares transcript snapshots, which is strictly weaker than an event-driven
   server wait — it can call a slow-thinking agent settled. Its exit codes are
   0 settled, 1 error, 2 timeout, 3 blocked.

## Event streams

For a long-lived monitor rather than a one-shot wait, the socket API exposes
`events.subscribe` with `pane.agent_status_changed`, `pane.output_matched`,
`pane.exited`, `workspace.metadata_updated` and the workspace/tab/pane
lifecycle events. That needs a persistent process and is out of scope for this
skill: `agent wait` is already event-driven server-side, and
`scripts/fleet_status.py` covers periodic monitoring in one call. See
https://herdr.dev/docs/socket-api/ if you build one anyway.
