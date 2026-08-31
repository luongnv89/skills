# Delivery Verification & Waiting — the full rationale

The deep "why" behind SKILL.md Phases 3 and 4. The SKILL.md gives you the commands and the branch logic; read this when you need to understand *why* a step is shaped the way it is, or when a check behaves unexpectedly.

## The exit-code table (canonical)

The single source for every helper exit code in this skill. SKILL.md's Critical Rules, Phase 1, and Phase 4 name *the exit-code table* and point here rather than restating it — the codes live in exactly one place so they cannot drift apart.

### `preflight_send.py` — is this pane sendable?

| Exit | Meaning | Action |
|---|---|---|
| 0 | sendable (idle) | proceed |
| 2 | working (busy chrome) | wait for settle; do not send |
| 3 | blocked (dialog) | surface to human; do not send |
| 4 | unverifiable | refuse; fix session / capture |
| 1 | usage / tmux missing | fix environment |

### `wait_for_idle.py` — readiness gate and settled-reply wait

| Exit | Meaning | Action |
|---|---|---|
| 0 | settled — or ready, under `--ready` | proceed to read the reply / assign work |
| 2 | timeout — the bounded wait elapsed | classify working vs stalled with an independent capped-tail read |
| 3 | blocked (trust/auth/permission dialog) | escalate to a human; never type task text |
| 1 | error — usage, tmux missing, bad target | fix environment |

Both scripts share the same code *meanings* (0 good, 1 environment error, 2 not-yet, 3 blocked) so one mental model covers both. Only `preflight_send.py` exit 0 authorizes a send; `wait_for_idle.py` never does.

## Fail-closed preflight

Before every `send-keys` **and** before every recovery Enter, run:

```bash
python3 "$here/preflight_send.py" "$target"
```

Read the verdict off the exit-code table above. Typing into a trust dialog submits menu garbage and reports a false success. Typing into a working pane races the prior task's completion signal. Preflight is the single-target twin of `broadcast.sh` Phase 1b — keep them in lockstep.

## Why "text on screen" does not prove a message was submitted

After `send-keys`, the message text appears in `capture-pane` whether it was **submitted** or is merely **typed and still parked in the input box** — both render as the same characters. So "the text is on screen" only proves it was typed, not sent. Reading the message text back out of the pane to confirm delivery is therefore unreliable.

The reliable signal is **post-send activity** against a **pre-send baseline**:

1. Capture baseline to a **file** before send.
2. Preflight, then send text + Enter (separate calls).
3. Sleep once (~5s), capture to a **second file**.
4. Delivered if busy chrome (`esc to interrupt` / spinner) **or** `cmp` shows the files differ.

Use file-to-file `cmp`, not `$(...)` string compare — command substitution strips trailing newlines and makes identical transcripts look different.

### The two outcomes (neither is a reply timeout)

- **`delivered` / transcript activity** — agent accepted input (spinner) or the pane changed vs baseline → proceed to Phase 4. Activity may be only prompt echo; the split completion marker distinguishes echo from a finished reply.
- **`NOT-DELIVERED`** — no post-send activity. Usually the separate-Enter gotcha or a dropped keystroke. **Re-run preflight**, then send a lone `Enter`, re-check once. Propagate failure if still quiet — do not report success. Distinct from a Phase 4 reply timeout: nothing was submitted, so don't start waiting until it lands.

Never send recovery Enter blind: the first send may have flipped the pane into a blocked dialog, and bare Enter would answer *that* dialog.

## Pre-send baseline + split completion marker

Two races without them:

1. **Fast completion** — agent finishes before `wait_for_idle.py` takes its own baseline snapshot → wait times out on a finished task, or delta is empty.
2. **Prompt echo** — the typed task appears in the transcript and stabilizes → content-stability thinks the reply is done.

Contract:

```bash
baseline_file="$(mktemp)"
tmux capture-pane -t "$target" -p -S -80 >"$baseline_file"
suffix="$(date +%s)_$$_$RANDOM"
completion_marker="TAC_DONE_$suffix"
task="…real work…

After fully finishing, concatenate and print these two parts without spaces: TAC_DONE_ and $suffix"
# preflight → send → delivery check →
python3 "$here/wait_for_idle.py" "$target" --timeout 180 --scrollback 80 \
  --baseline-file "$baseline_file" --completion-marker "$completion_marker"
rc=$?; rm -f "$baseline_file"
```

- Split the marker in the prompt so echo never contains the joined form.
- Only a **fresh** marker (present in current, **absent from baseline**) proves THIS send finished.
- A stale marker left from a prior task must not satisfy the new wait.

### Wait modes

| Mode | Flag | Behavior |
|---|---|---|
| Post-send (default) | (none) | Requires saw_work (busy chrome / transcript change) **or** fresh completion marker before idle success |
| Boot / ready | `--ready` | Accepts already-idle; still returns 3 on blocked dialogs |
| Marker-required | `--completion-marker` | Quiet prompt echo alone never completes |

Exit codes: see *the exit-code table* at the top of this file.

## Why the helper's verdict is advisory

`wait_for_idle.py` exit 0 means *the pane stopped changing under the mode rules above*, which is usually "done" but can also be a paused agent or a UI that quiesced mid-task. Content stability is the universal signal (works for any CLI agent); spinner chrome and dialog text only refine the verdict.

When the verdict matters (before relaying a result the user will act on, or on any exit-2 timeout), do an **independent, human-style read**:

```bash
tmux capture-pane -t agent1 -p -S -40
```

Third failure mode (stalled agent) vs working:

- **Still working:** spinner / `esc to interrupt`, or tail differs from a capture moments ago → keep waiting; **don't send**.
- **Stuck / stalled:** unchanged across reads, no spinner, no completion → surface it; do not silently re-wait.

## Concurrent fleet waits

Capture every baseline first, preflight, send all with markers, then wait concurrently. Prefer `scripts/broadcast.sh` — it:

1. Dedupes targets and verifies `has-session`
2. Fail-closed preflight (skip working / blocked / unverifiable)
3. Snapshots baselines
4. Re-preflights immediately before each dispatch
5. Fans out split markers + task text
6. Waits concurrently with `--baseline-file` + `--completion-marker`
7. Aggregates SEND-FAILED / BECAME-UNSAFE / waiter codes into exit 1

Manual pattern only if the script is unavailable — never serialize full send→wait→read per agent.

## Follow-ups

Every steer/follow-up is a **new** Phase 3→4 cycle: new baseline file, new marker suffix, new preflight. Phase 4 deletes the previous baseline; the previous joined marker is already in the transcript.

## Anti-deadloop — bound the whole loop, not just one wait

| Budget | Suggested default |
|---|---|
| Boot to ready (`--ready`) | 60s |
| Delivery activity check | ~5s once (+ one recovery Enter) |
| Task completion | 180s (tune per task) |
| Re-waits after timeout | max 2–3, then escalate |

`--timeout` caps a **single** call; the real risk is a re-wait / re-send loop that polls forever. When the overall budget is spent, **stop and escalate** with last capture and how long you waited. Never poll indefinitely and never auto-re-send past the cap.

### Manual fallback (no Python / restricted env)

Capture, `sleep 3`, capture again, compare — under the same overall budget. Matching captures with no spinner = done. A spinner or `esc to interrupt` still showing → wait and re-capture; **don't send a new message yet**. If the budget runs out with no resolution, stop and surface it. Without preflight/marker helpers you lose fail-closed dialog protection — prefer installing Python for the scripts.
