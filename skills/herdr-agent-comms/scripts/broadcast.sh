#!/usr/bin/env bash
# Broadcast one message to several Herdr agents, then collect each reply.
#
# Sends to EVERY target first (fast), then waits on all of them CONCURRENTLY.
# Wall-clock is the slowest single agent, not the sum.
#
# Usage:
#   scripts/broadcast.sh "message" target1 target2 [target3 ...]
#
# Targets: agent names (reviewer) or pane ids (w26:p4)
#
# Options (env vars):
#   HAC_TIMEOUT       per-agent wait timeout in seconds (default: 180)
#   HAC_WAIT_ARGS     extra args passed to wait_for_idle.py (e.g. "--full")
#
# Exit 0 if all agents settled idle/done; otherwise 1.

set -u

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
waiter="$here/wait_for_idle.py"
timeout="${HAC_TIMEOUT:-180}"

if [ "$#" -lt 2 ]; then
  echo "Error: need a message and at least one target." >&2
  echo "Usage: scripts/broadcast.sh \"message\" target1 [target2 ...]" >&2
  exit 1
fi
if ! command -v herdr >/dev/null 2>&1; then
  echo "Error: herdr is not installed or not on PATH." >&2
  exit 1
fi
if [ ! -f "$waiter" ]; then
  echo "Error: helper not found at $waiter — run broadcast.sh from the skill dir." >&2
  exit 1
fi

msg="$1"; shift
targets=("$@")

resolve_pane() {
  local t="$1"
  if herdr pane get "$t" >/dev/null 2>&1; then
    printf '%s\n' "$t"
    return 0
  fi
  herdr agent get "$t" 2>/dev/null | python3 -c '
import sys, json
try:
    d = json.load(sys.stdin)
    a = d.get("result", {}).get("agent") or d.get("result", {})
    print(a["pane_id"])
except Exception:
    sys.exit(1)
'
}

# Phase 1: resolve all targets first
panes=()
labels=()
missing=()
for t in "${targets[@]}"; do
  if p="$(resolve_pane "$t")"; then
    panes+=("$p")
    labels+=("$t")
  else
    missing+=("$t")
  fi
done
if [ "${#missing[@]}" -gt 0 ]; then
  echo "Error: these targets don't resolve: ${missing[*]}" >&2
  echo "List them with: herdr agent list" >&2
  exit 1
fi

# Phase 2: fan out (pane run = text + Enter)
for p in "${panes[@]}"; do
  herdr pane run "$p" "$msg" >/dev/null || {
    echo "Error: pane run failed for $p" >&2
    exit 1
  }
done

# Phase 3: wait concurrently
tmpdir="$(mktemp -d "${TMPDIR:-/tmp}/hac_broadcast.XXXXXX")"
trap 'rm -rf "$tmpdir"' EXIT
pids=()
for i in "${!panes[@]}"; do
  p="${panes[$i]}"
  # shellcheck disable=SC2086
  (
    python3 "$waiter" "$p" --timeout "$timeout" ${HAC_WAIT_ARGS:-} \
      >"$tmpdir/$i.out" 2>"$tmpdir/$i.err"
    echo "$?" >"$tmpdir/$i.code"
  ) &
  pids+=("$!")
done
for pid in "${pids[@]}"; do wait "$pid"; done

# Phase 4: emit labeled blocks
overall=0
for i in "${!panes[@]}"; do
  label="${labels[$i]}"
  p="${panes[$i]}"
  code="$(cat "$tmpdir/$i.code" 2>/dev/null || echo "?")"
  case "$code" in
    0) state="idle/done" ;;
    2) state="TIMEOUT"; overall=1 ;;
    3) state="BLOCKED (needs human)"; overall=1 ;;
    *) state="error"; overall=1 ;;
  esac
  echo "===== $label ($p) [$state, exit $code] ====="
  cat "$tmpdir/$i.out" 2>/dev/null
  if [ "$code" != "0" ]; then
    cat "$tmpdir/$i.err" 2>/dev/null >&2
  fi
  echo
done

exit "$overall"
