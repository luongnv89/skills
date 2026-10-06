#!/usr/bin/env python3
"""Fail-closed pre-send readiness check for a single tmux agent target.

Run this immediately BEFORE typing a task (or a lone Enter) into a session. It
answers one question: is this pane safe to deliver to *right now*? A pane that
shows busy chrome (spinner / "esc to interrupt"), a trust/auth dialog, or whose
capture can't be verified is NOT safe — sending into it either races a prior
task or types the payload into a dialog.

This is the single-target twin of `scripts/broadcast.sh` Phase 1b: the exact
same fail-closed chrome check, in one testable place so the two paths can't
drift. Marker lists live in `wait_for_idle.py` (imported here).

Exit codes (chosen so callers can branch on the reason):
    0  sendable   (not busy, not blocked, capture succeeded)
    2  working    (busy chrome present; wait for it to settle first)
    3  blocked    (a dialog is on screen; a human must answer it)
    4  unverifiable (capture/has-session failed)
    1  usage error (tmux missing, no target)

On a non-zero exit a one-line reason is printed to stderr; nothing is printed
to stdout unless the pane is sendable (then "idle" is echoed).

Usage:
    python3 preflight_send.py <target>
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wait_for_idle import (  # noqa: E402
    BLOCK_SCAN_TAIL_LINES,
    BUSY_SCAN_TAIL_LINES,
    build_marker_lists,
    looks_blocked,
    looks_busy,
)


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(
            f"Error: expected exactly one tmux target, got {len(argv)} argument(s). "
            "Usage: preflight_send.py <session[:window.pane]>",
            file=sys.stderr,
        )
        return 1
    target = argv[0]
    if not shutil.which("tmux"):
        print(
            "Error: tmux is not installed or not on PATH. "
            "Install it (brew install tmux / apt install tmux), then re-run.",
            file=sys.stderr,
        )
        return 1

    has = subprocess.run(
        ["tmux", "has-session", "-t", target],
        capture_output=True,
        text=True,
    )
    if has.returncode != 0:
        print(
            f"Error: cannot verify target '{target}' (session missing) — "
            f"refusing to send. List sessions with: tmux list-sessions",
            file=sys.stderr,
        )
        return 4

    # Prefer a short scrollback so dialog text a few lines above the bottom is
    # still visible; matches waiter block-scan window needs.
    cap = subprocess.run(
        ["tmux", "capture-pane", "-t", target, "-p", "-S", "-40"],
        capture_output=True,
        text=True,
    )
    if cap.returncode != 0:
        print(
            f"Error: cannot capture '{target}' (lookup failed) — refusing to "
            f"send into an unverifiable pane. Check the target with: "
            f"tmux has-session -t {target}",
            file=sys.stderr,
        )
        return 4

    text = cap.stdout
    busy_markers, block_markers = build_marker_lists([], [])

    # Prefer blocked over busy when a dialog is stable: a trust prompt can
    # include words that look "active", but typing into it is worse. Busy
    # chrome on the last 1–2 lines with no dialog → working.
    if looks_blocked(text, block_markers) and not looks_busy(text, busy_markers):
        print(
            f"Error: {target} is blocked (trust/auth/permission dialog) — a "
            f"human must answer it first; typing the task now would submit "
            f"garbage into the dialog.",
            file=sys.stderr,
        )
        return 3
    if looks_busy(text, busy_markers):
        print(
            f"Error: {target} is already working — wait for it to settle "
            f"before sending, or this send's completion can't be told apart "
            f"from the prior task's.",
            file=sys.stderr,
        )
        return 2
    if looks_blocked(text, block_markers):
        # Busy + blocked text: still refuse — dialog ate focus.
        print(
            f"Error: {target} is blocked (trust/auth/permission dialog) — a "
            f"human must answer it first; typing the task now would submit "
            f"garbage into the dialog.",
            file=sys.stderr,
        )
        return 3

    # Silence unused-import lint for scan constants re-exported for tests.
    _ = (BUSY_SCAN_TAIL_LINES, BLOCK_SCAN_TAIL_LINES)

    print("idle")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
