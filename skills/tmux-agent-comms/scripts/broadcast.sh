#!/usr/bin/env bash
# Broadcast one message to several tmux agent sessions, then collect each reply.
#
# Sends to EVERY target first (fast, non-blocking), then waits on all of them
# CONCURRENTLY via wait_for_idle.py running in the background. Wall-clock is the
# slowest single agent, not the sum — serializing send->wait->read per agent
# would let one slow agent stall the whole fleet.
#
# Usage:
#   scripts/broadcast.sh "message" session1 session2 [session3 ...]
#
# Options (env vars):
#   TAC_TIMEOUT       per-agent wait timeout in seconds (default: 120)
#   TAC_WAIT_ARGS     extra args passed to wait_for_idle.py (e.g. "--full")
#
# Output: one labeled block per agent with its reply delta and the wait exit
# code (0 idle / 2 timeout / 3 blocked). Exit 0 if all agents went idle,
# otherwise 1 (so a caller can detect that some agent timed out or is blocked).

set -u

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
waiter="$here/wait_for_idle.py"
timeout="${TAC_TIMEOUT:-120}"

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

msg="$1"; shift
sessions=("$@")

# Phase 1: verify every target exists before touching any (fail loud, fail early).
missing=()
for s in "${sessions[@]}"; do
  tmux has-session -t "$s" 2>/dev/null || missing+=("$s")
done
if [ "${#missing[@]}" -gt 0 ]; then
  echo "Error: these sessions don't exist: ${missing[*]}" >&2
  echo "List them with: tmux list-sessions" >&2
  exit 1
fi

# Phase 2: fan the message out to all sessions (Enter sent separately for TUIs
# that don't submit an inline Enter — see SKILL.md Phase 3).
for s in "${sessions[@]}"; do
  tmux send-keys -t "$s" "$msg"
  tmux send-keys -t "$s" Enter
done

# Phase 3: wait on all sessions concurrently, each capturing to its own temp file.
tmpdir="$(mktemp -d "${TMPDIR:-/tmp}/tac_broadcast.XXXXXX")"
trap 'rm -rf "$tmpdir"' EXIT
declare -a pids=()
for i in "${!sessions[@]}"; do
  s="${sessions[$i]}"
  # shellcheck disable=SC2086
  ( python3 "$waiter" "$s" --timeout "$timeout" ${TAC_WAIT_ARGS:-} >"$tmpdir/$i.out" 2>"$tmpdir/$i.err"; echo "$?" >"$tmpdir/$i.code" ) &
  pids+=("$!")
done
for p in "${pids[@]}"; do wait "$p"; done

# Phase 4: emit one labeled block per agent; track overall success.
overall=0
for i in "${!sessions[@]}"; do
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

exit "$overall"
