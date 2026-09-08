#!/usr/bin/env python3
"""Fail-closed pre-send readiness check for one Herdr agent target.

`herdr agent prompt` already refuses a `blocked` target (`agent_blocked`) before
writing any input, so this check is no longer the last line of defence it once
was. What it still covers is the case the server does NOT refuse: a target that
is already `working`. Herdr's wait tracks lifecycle state, not one turn, so a
prompt sent into a working agent can be "completed" by the previous turn ending
— the reply you read back is then the wrong one. Refuse instead.

It also resolves whether the target is reachable on the agent surface at all.
A pane running an undetected process has no agent record: `herdr agent get`
returns `agent_not_found`, and the caller must fall back to the pane surface
(`herdr pane run` + `wait_for_idle.py`) documented in
`references/delivery-and-waiting.md`.

Exit codes (callers branch on the reason):
    0  sendable      (idle / done / unknown — dispatch with `herdr agent prompt`)
    2  working       (a turn is in flight; wait for it to settle first)
    3  blocked       (a dialog is on screen; a human must answer it)
    4  unverifiable  (lookup/parse failed, or an off-enum status value)
    5  no agent      (pane hosts no detected agent — use the pane fallback)
    1  usage error   (herdr missing, or no target given)

On a non-zero exit a one-line reason goes to stderr and nothing to stdout. On
success the resolved status is echoed to stdout.

Usage:
    python3 preflight_send.py <agent-name|pane-id>
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys

VALID = {"idle", "working", "blocked", "done", "unknown"}


def agent_record(target: str) -> tuple[dict | None, str]:
    """Return (record, error_code). error_code is "" when the record resolved."""
    proc = subprocess.run(
        ["herdr", "agent", "get", target], capture_output=True, text=True
    )
    payload = proc.stdout or proc.stderr
    try:
        data = json.loads(payload)
    except Exception:  # noqa: BLE001 — non-JSON output is unverifiable, full stop
        return None, "unparseable"
    if "error" in data:
        code = data["error"].get("code") or "error"
        return None, str(code)
    record = (data.get("result") or {}).get("agent")
    if not isinstance(record, dict):
        return None, "unparseable"
    return record, ""


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: preflight_send.py <agent-name|pane-id>", file=sys.stderr)
        return 1
    target = argv[0]
    if not shutil.which("herdr"):
        print("Error: herdr not on PATH", file=sys.stderr)
        return 1

    record, err = agent_record(target)
    if err == "agent_not_found":
        print(
            f"Error: {target} hosts no detected agent — the agent surface "
            f"(prompt/wait/read) cannot address it. Start one with 'herdr agent "
            f"start <name> --kind KIND --pane {target}', or use the pane-surface "
            f"fallback in references/delivery-and-waiting.md.",
            file=sys.stderr,
        )
        return 5
    if record is None:
        print(
            f"Error: cannot verify {target} ({err}) — refusing to send into an "
            f"unverifiable target.",
            file=sys.stderr,
        )
        return 4

    raw = record.get("agent_status")
    if not (isinstance(raw, str) and raw in VALID):
        print(
            f"Error: {target} reported an off-enum status ({raw!r}) — refusing "
            f"to send.",
            file=sys.stderr,
        )
        return 4
    if raw == "working":
        print(
            f"Error: {target} is already working — a prompt sent now can be "
            f"'completed' by the turn already in flight, and you would read back "
            f"the wrong reply. Wait with 'herdr agent wait {target}' first.",
            file=sys.stderr,
        )
        return 2
    if raw == "blocked":
        print(
            f"Error: {target} is blocked (trust/auth/permission dialog) — a "
            f"human must answer it first ('herdr agent focus {target}').",
            file=sys.stderr,
        )
        return 3
    # idle / done / unknown: `herdr agent prompt` accepts these.
    print(raw)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
