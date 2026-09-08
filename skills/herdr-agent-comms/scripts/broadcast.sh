#!/usr/bin/env bash
# Broadcast one prompt to several Herdr agents, then report each outcome.
#
# Dispatch and wait are one server-side request per target (`herdr agent prompt
# --wait`), and every target runs concurrently, so wall-clock is the slowest
# single agent rather than the sum. There is no transcript baseline and no
# completion marker: the server starts the wait in the same request that submits
# the prompt, which is what those two mechanisms used to approximate from
# outside.
#
# Usage:
#   scripts/broadcast.sh "message" target1 target2 [target3 ...]
#
# Targets: agent names (reviewer) or pane ids (w1:p4). Duplicates that resolve
# to the same pane are sent once.
#
# Options (env vars):
#   HAC_TIMEOUT   per-agent wait timeout in seconds (default: 180)
#   HAC_LINES     transcript lines printed per reply (default: 60; 0 = none)
#   HAC_BADGE     set to 1 to badge each target's sidebar row with its phase
#
# Exit 0 only when every target was dispatched and settled. Any refusal, send
# failure, block, stall or timeout exits 1 with a per-target reason.

set -u

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
timeout_s="${HAC_TIMEOUT:-180}"
lines="${HAC_LINES:-60}"
badge="${HAC_BADGE:-0}"

if [ "$#" -lt 2 ]; then
  echo "Error: need a message and at least one target." >&2
  echo "Usage: scripts/broadcast.sh \"message\" target1 [target2 ...]" >&2
  exit 1
fi
if ! command -v herdr >/dev/null 2>&1; then
  echo "Error: herdr is not installed or not on PATH." >&2
  exit 1
fi

msg="$1"; shift
targets=("$@")
timeout_ms=$((timeout_s * 1000))

# One `herdr agent list` call resolves every target: name -> pane id and the
# status in the same consistent view. Per-target `agent get` would cost N calls
# and could observe a torn view where A is read before B changes state.
roster="$(herdr agent list 2>/dev/null)" || {
  echo "Error: 'herdr agent list' failed — is the Herdr server running?" >&2
  exit 1
}

resolve() {
  # resolve <target> -> "<pane_id> <status>" on stdout, non-zero if unresolved.
  printf '%s' "$roster" | TARGET="$1" python3 -c '
import json, os, sys
target = os.environ["TARGET"]
VALID = {"idle", "working", "blocked", "done", "unknown"}
try:
    agents = json.load(sys.stdin)["result"]["agents"]
except Exception:
    sys.exit(1)
for a in agents:
    if a.get("name") == target or a.get("pane_id") == target:
        raw = a.get("agent_status")
        status = raw if isinstance(raw, str) and raw in VALID else "unverifiable"
        print(a.get("pane_id", ""), status)
        sys.exit(0)
sys.exit(1)
'
}

# Phase 1 — resolve and dedupe. A target that does not resolve is fatal: the
# caller asked for a fleet, and silently shrinking it hides work that never ran.
panes=(); labels=(); statuses=(); missing=()
for t in "${targets[@]}"; do
  if line="$(resolve "$t")"; then
    p="${line%% *}"; st="${line##* }"
    dup=""
    for existing in ${panes[@]+"${panes[@]}"}; do
      [ "$existing" = "$p" ] && { dup=1; break; }
    done
    if [ -n "$dup" ]; then
      echo "Note: '$t' resolves to already-targeted pane $p — skipping duplicate." >&2
      continue
    fi
    panes+=("$p"); labels+=("$t"); statuses+=("$st")
  else
    missing+=("$t")
  fi
done
if [ "${#missing[@]}" -gt 0 ]; then
  echo "Error: these targets host no detected agent: ${missing[*]}" >&2
  echo "List them with: herdr agent list" >&2
  exit 1
fi

# Phase 2 — fail closed. `herdr agent prompt` refuses a blocked target itself
# (agent_blocked, before writing any input), but it does NOT refuse a working
# one, and its wait tracks lifecycle state rather than one turn: a prompt sent
# into a working agent can be satisfied by the turn already in flight. Refuse
# both here so a skipped target is reported rather than mis-reported as done.
send_idx=(); skipped=()
for i in "${!panes[@]}"; do
  case "${statuses[$i]}" in
    idle|done|unknown) send_idx+=("$i") ;;
    working) skipped+=("${labels[$i]}: working (a turn is already in flight)") ;;
    blocked) skipped+=("${labels[$i]}: blocked (a human must answer a dialog)") ;;
    *)       skipped+=("${labels[$i]}: unverifiable status") ;;
  esac
done

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

# Phase 3 — dispatch every safe target concurrently. Each job submits and waits
# in a single request, so there is no send-then-wait race to close.
#
# The Phase 2 branch used the roster read from T0. Resolving and badging N
# targets takes real time, so recheck each target immediately before its own
# dispatch. Herdr refuses a target that turned `blocked` in that window, but it
# does NOT refuse one that turned `working` — and that is the case that reads
# back the wrong reply. preflight_send.py is the single place that check lives.
pids=(); raced=()
for i in ${send_idx[@]+"${send_idx[@]}"}; do
  if ! reason="$(python3 "$here/preflight_send.py" "${panes[$i]}" 2>&1 >/dev/null)"; then
    raced+=("${labels[$i]}: became unsafe before dispatch — ${reason#Error: }")
    continue
  fi
  if [ "$badge" = "1" ]; then
    python3 "$here/badge.py" "${panes[$i]}" --token phase=working \
      --ttl-ms "$((timeout_ms + 60000))" >/dev/null 2>&1 || true
  fi
  herdr agent prompt "${panes[$i]}" "$msg" --wait --timeout "$timeout_ms" \
    >"$tmpdir/$i.out" 2>"$tmpdir/$i.err" &
  pids+=("$!:$i")
done

# Phase 4 — collect. Herdr reports failures as a JSON error object with a code;
# map the codes back to a human reason instead of printing raw protocol noise.
overall=0
for entry in ${pids[@]+"${pids[@]}"}; do
  jp="${entry%%:*}"; i="${entry#*:}"
  label="${labels[$i]}"; pane="${panes[$i]}"
  if wait "$jp"; then
    echo "$label ($pane): settled"
    if [ "$lines" -gt 0 ] 2>/dev/null; then
      echo "--- $label reply (last $lines lines) ---"
      herdr agent read "$pane" --source recent-unwrapped --lines "$lines" \
        || echo "  (reply read failed)" >&2
    fi
    [ "$badge" = "1" ] && python3 "$here/badge.py" "$pane" --token phase=done \
      --ttl-ms 600000 >/dev/null 2>&1
  else
    code="$(sed -n 's/.*"code"[[:space:]]*:[[:space:]]*"\([a-z_]*\)".*/\1/p' "$tmpdir/$i.err" | head -1)"
    case "$code" in
      agent_blocked)         reason="BLOCKED — a human must answer a dialog; nothing was sent" ;;
      agent_prompt_stalled)  reason="STALLED — submitted, but no agent activity followed" ;;
      timeout)               reason="TIMEOUT — no settled state within ${timeout_s}s" ;;
      agent_not_found)       reason="GONE — the agent left this pane mid-run" ;;
      "")                    reason="FAILED — $(head -1 "$tmpdir/$i.err" 2>/dev/null)" ;;
      *)                     reason="FAILED ($code)" ;;
    esac
    echo "$label ($pane): $reason" >&2
    [ "$badge" = "1" ] && python3 "$here/badge.py" "$pane" --token phase="$code" \
      --ttl-ms 600000 >/dev/null 2>&1
    overall=1
  fi
done

for s in ${skipped[@]+"${skipped[@]}"} ${raced[@]+"${raced[@]}"}; do
  echo "Skipped $s" >&2
  overall=1
done

echo "Broadcast: ${#pids[@]} dispatched, $(( ${#skipped[@]} + ${#raced[@]} )) skipped"
exit "$overall"
