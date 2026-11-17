#!/usr/bin/env bash
# Broadcast one message to several tmux agent sessions, then collect each reply.
#
# Sends to EVERY safe target first (fast), then waits on all of them
# CONCURRENTLY via wait_for_idle.py. Wall-clock is the slowest single agent,
# not the sum — serializing send->wait->read per agent would let one slow
# agent stall the whole fleet.
#
# Fail-closed: skips targets that are busy, blocked, or unverifiable; captures
# a pre-send baseline + split completion marker per target so fast replies and
# prompt echo cannot false-complete.
#
# Usage:
#   scripts/broadcast.sh "message" session1 session2 [session3 ...]
#
# Options (env vars):
#   TAC_TIMEOUT       per-agent wait timeout in seconds (default: 120)
#   TAC_SCROLLBACK    capture-pane -S window for baseline/waiter (default: 80)
#   TAC_WAIT_ARGS     extra args passed to wait_for_idle.py (e.g. "--full")
#
# Output: one labeled block per agent with its reply delta and the wait exit
# code (0 idle / 2 timeout / 3 blocked). Exit 0 if all agents went idle and
# every requested target was safely dispatched; otherwise 1.

set -u

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
waiter="$here/wait_for_idle.py"
preflight="$here/preflight_send.py"
timeout="${TAC_TIMEOUT:-120}"
scrollback="${TAC_SCROLLBACK:-80}"

if [ "$#" -lt 2 ]; then
  echo "Error: need a message and at least one session." >&2
  echo "Usage: scripts/broadcast.sh \"message\" session1 [session2 ...]" >&2
  exit 1
fi
if ! command -v tmux >/dev/null 2>&1; then
  echo "Error: tmux is not installed or not on PATH (brew install tmux / apt install tmux)." >&2
  exit 1
fi
if [ ! -f "$waiter" ]; then
  echo "Error: helper not found at $waiter — run broadcast.sh from the skill dir." >&2
  exit 1
fi
if [ ! -f "$preflight" ]; then
  echo "Error: preflight helper not found at $preflight." >&2
  exit 1
fi

msg="$1"; shift
raw_targets=("$@")

# Phase 1: verify existence + dedupe (bash 3.2-safe linear scan).
sessions=()
missing=()
for t in "${raw_targets[@]}"; do
  if ! tmux has-session -t "$t" 2>/dev/null; then
    missing+=("$t")
    continue
  fi
  dup=""
  for existing in "${sessions[@]+"${sessions[@]}"}"; do
    if [ "$existing" = "$t" ]; then
      dup=1
      break
    fi
  done
  if [ -n "$dup" ]; then
    echo "Note: '$t' already targeted — skipping duplicate." >&2
    continue
  fi
  sessions+=("$t")
done
if [ "${#missing[@]}" -gt 0 ]; then
  echo "Error: these sessions don't exist: ${missing[*]}" >&2
  echo "List them with: tmux list-sessions" >&2
  exit 1
fi
if [ "${#sessions[@]}" -eq 0 ]; then
  echo "Error: no targets left to send to." >&2
  exit 1
fi

# Phase 1b: fail-closed preflight — skip working / blocked / unverifiable.
busy=()
blocked=()
unverifiable=()
ready=()
for s in "${sessions[@]}"; do
  # Capture preflight stderr separately so we can still surface the reason.
  pf_err="$(mktemp "${TMPDIR:-/tmp}/tac_pf.XXXXXX")"
  python3 "$preflight" "$s" >/dev/null 2>"$pf_err"
  rc=$?
  case "$rc" in
    0) ready+=("$s") ;;
    2) busy+=("$s") ;;
    3) blocked+=("$s") ;;
    *) unverifiable+=("$s") ;;
  esac
  if [ "$rc" -ne 0 ]; then
    cat "$pf_err" >&2 2>/dev/null || true
  fi
  rm -f "$pf_err"
done
if [ "${#busy[@]}" -gt 0 ]; then
  echo "Error: these targets are already working and were skipped: ${busy[*]}" >&2
  echo "Wait for them to go idle first, or target only the idle agents." >&2
fi
if [ "${#blocked[@]}" -gt 0 ]; then
  echo "Error: these targets are blocked (trust/auth dialog) and were skipped: ${blocked[*]}" >&2
  echo "A human must answer the dialog first (open a visible app tab / attach)." >&2
fi
if [ "${#unverifiable[@]}" -gt 0 ]; then
  echo "Error: could not verify these targets and skipped them: ${unverifiable[*]}" >&2
  echo "Refusing to send into a pane whose busy/blocked state is unknown." >&2
fi
sessions=("${ready[@]+"${ready[@]}"}")
if [ "${#sessions[@]}" -eq 0 ]; then
  echo "Error: no targets left to send to." >&2
  exit 1
fi

tmpdir="$(mktemp -d "${TMPDIR:-/tmp}/tac_broadcast.XXXXXX")"
trap 'rm -rf "$tmpdir"' EXIT

# Phase 2: snapshot every pane BEFORE send. A fast agent can finish before its
# waiter starts; stable output after this baseline still proves new activity.
for i in "${!sessions[@]}"; do
  s="${sessions[$i]}"
  if ! tmux capture-pane -t "$s" -p -S "-$scrollback" >"$tmpdir/$i.baseline"; then
    echo "Error: could not capture baseline for $s" >&2
    exit 1
  fi
done

# Phase 3: fan out with split completion markers. The full marker is
# deliberately absent from the prompt: prompt echo contains its two halves;
# only the completed reply joins them.
#
# A failed send here must NOT abort the whole broadcast: panes sent earlier
# are already mid-task. Record the failure and keep going.
markers=()
send_failed=()
became_unsafe=()
for i in "${!sessions[@]}"; do
  s="${sessions[$i]}"
  # Re-check immediately before dispatch (status can flip during baseline loop).
  if ! python3 "$preflight" "$s" >/dev/null 2>"$tmpdir/$i.pf"; then
    rc=$?
    echo "Error: $s became unsafe before dispatch (preflight rc $rc) — skipped (not sent)." >&2
    cat "$tmpdir/$i.pf" >&2 2>/dev/null || true
    became_unsafe+=("$i")
    continue
  fi
  suffix="$(date +%s)_$$_${i}_${RANDOM}"
  markers[$i]="TAC_DONE_$suffix"
  task="$msg

After fully finishing the task, concatenate and print these two parts without spaces: TAC_DONE_ and $suffix"
  if ! tmux send-keys -t "$s" "$task"; then
    echo "Error: send-keys failed for $s — dispatch stopped for this target." >&2
    send_failed+=("$i")
    continue
  fi
  if ! tmux send-keys -t "$s" Enter; then
    echo "Error: Enter failed for $s — dispatch stopped for this target." >&2
    send_failed+=("$i")
    continue
  fi
done

# Phase 4: wait concurrently only on panes that actually received a send.
pids=()
wait_indices=()
for i in "${!sessions[@]}"; do
  skip=""
  for f in ${send_failed[@]+"${send_failed[@]}"} ${became_unsafe[@]+"${became_unsafe[@]}"}; do
    [ "$f" = "$i" ] && { skip=1; break; }
  done
  [ -n "$skip" ] && continue
  s="${sessions[$i]}"
  wait_indices+=("$i")
  # shellcheck disable=SC2086
  (
    python3 "$waiter" "$s" --timeout "$timeout" ${TAC_WAIT_ARGS:-} \
      --scrollback "$scrollback" \
      --baseline-file "$tmpdir/$i.baseline" \
      --completion-marker "${markers[$i]}" \
      >"$tmpdir/$i.out" 2>"$tmpdir/$i.err"
    echo "$?" >"$tmpdir/$i.code"
  ) &
  pids+=("$!")
done
for p in ${pids[@]+"${pids[@]}"}; do wait "$p"; done

# Phase 5: emit labeled blocks; any skip/failure fails the overall exit.
overall=0
if [ "${#busy[@]}" -gt 0 ] || [ "${#blocked[@]}" -gt 0 ] \
   || [ "${#unverifiable[@]}" -gt 0 ] || [ "${#send_failed[@]}" -gt 0 ] \
   || [ "${#became_unsafe[@]}" -gt 0 ]; then
  overall=1
fi

for i in ${wait_indices[@]+"${wait_indices[@]}"}; do
  s="${sessions[$i]}"
  code="$(cat "$tmpdir/$i.code" 2>/dev/null || echo "?")"
  case "$code" in
    0) state="idle" ;;
    2) state="TIMEOUT"; overall=1 ;;
    3) state="BLOCKED (needs human)"; overall=1 ;;
    *) state="error"; overall=1 ;;
  esac
  echo "===== $s [$state, exit $code] ====="
  cat "$tmpdir/$i.out" 2>/dev/null
  if [ "$code" != "0" ]; then
    cat "$tmpdir/$i.err" 2>/dev/null >&2
  fi
  echo
done
for i in ${send_failed[@]+"${send_failed[@]}"}; do
  echo "===== ${sessions[$i]} [SEND-FAILED, not waited] =====" >&2
done
for i in ${became_unsafe[@]+"${became_unsafe[@]}"}; do
  echo "===== ${sessions[$i]} [BECAME-UNSAFE before dispatch, not sent] =====" >&2
done

if [ "${#send_failed[@]}" -gt 0 ] || [ "${#became_unsafe[@]}" -gt 0 ]; then
  ndrop=$(( ${#send_failed[@]} + ${#became_unsafe[@]} ))
  echo "Partial results: $ndrop of ${#sessions[@]} ready target(s) never received the message (see SEND-FAILED / BECAME-UNSAFE above). Results above are only for targets successfully dispatched." >&2
fi

exit "$overall"
