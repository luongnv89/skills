#!/usr/bin/env python3
"""Wait until a tmux agent pane is idle, then print what's new.

Polls `tmux capture-pane` until the visible output stops changing for N reads
(the agent finished writing). Distinguishes three end states so the caller can
act on each:

  - IDLE    (exit 0): output is stable and no spinner/working chrome remains.
  - BLOCKED (exit 3): output is stable but parked on a prompt that needs a human
                      (trust dialog, auth/API-key prompt). Sending a message now
                      would be interpreted as menu navigation, not a reply — so
                      the caller must surface this to the user, not proceed.
  - TIMEOUT (exit 2): never settled within --timeout (agent still working).

Why this exists: a fixed `sleep` either wastes time or reads a half-written
reply, and content-stability alone can't tell "ready input box" from "stuck on a
trust prompt" (both are stable). Polling-to-stable + chrome detection adapts to
however long the agent takes and refuses to fire into a dialog.

By default it prints only the NEW lines since the wait started (the agent's
answer), not the whole 24-line pane of box-drawing and status bars. Over a
multi-turn conversation, relaying deltas instead of full frames is the dominant
token saving. Use --full to print the entire settled pane instead.

Usage:
    python3 wait_for_idle.py <target> [options]

    <target>   tmux target: a session name (e.g. agent1) or session:window.pane

Options:
    --timeout SEC        give up after this many seconds (default: 120)
    --quiet-cycles N     consecutive unchanged reads required to call it settled
                         (default: 3)
    --interval SEC       seconds between captures (default: 2)
    --scrollback N       capture N lines of scrollback too (default: 0, visible only)
    --full               print the entire settled pane, not just new lines
    --no-print           print nothing (exit code only)
    --busy-marker STR    add a spinner/working marker (repeatable). Also via the
                         env var TAC_BUSY_MARKERS (newline- or |-separated).
    --block-marker STR   add a needs-human prompt marker (repeatable). Also via
                         the env var TAC_BLOCK_MARKERS.

Exit codes:
    0  idle (settled, ready for the next message)
    1  usage / environment error (tmux missing, target not found)
    2  timed out before the pane settled
    3  blocked: settled on a prompt that needs human input
"""

import argparse
import os
import shutil
import subprocess
import sys
import time

# --- Marker policy -----------------------------------------------------------
#
# Markers are UNAMBIGUOUS TUI *chrome* — strings an agent's spinner/status bar
# or a dialog prints — NOT generic prose. Words like "running", "loading", or a
# bare ellipsis are deliberately excluded: agent replies routinely contain them
# ("CI is running"), and matching prose would make a normal reply never settle.
# Content stability is the universal primary signal (works for ANY CLI agent);
# these markers only refine the verdict at the moment the pane goes stable.
#
# Defaults below are VERIFIED against real installs (Claude Code 2.x, Gemini CLI
# boot dialogs). Other agents extend the lists via --busy-marker/--block-marker
# or the TAC_BUSY_MARKERS / TAC_BLOCK_MARKERS env vars — no code edit needed.

# Still-working chrome. Lives on the last line or two (a single status row).
DEFAULT_BUSY_MARKERS = (
    "esc to interrupt",
    "esc to cancel",
    "ctrl+c to interrupt",
    "press esc to",
)

# Needs-human prompts. These sit inside multi-line dialog *boxes*, so the prompt
# text can be several lines above the bottom — scan a wider window than busy.
# VERIFIED strings only (observed on real Claude Code / Gemini CLI boot dialogs).
# Deliberately NOT here: generic menu phrases like "1. yes" — an agent reply that
# ends in a numbered list would falsely match, the same prose trap the busy
# markers avoid. Add agent-specific prompts via --block-marker / TAC_BLOCK_MARKERS.
DEFAULT_BLOCK_MARKERS = (
    "do you trust",            # Claude Code / Gemini trust-folder dialog
    "trust the files",
    "paste your api key",      # Gemini auth prompt
    "press enter to submit",   # auth/confirm dialogs
)

# Trailing non-empty lines scanned for each marker class. Busy chrome is a single
# status row; block dialogs are taller boxes — hence the wider block window.
BUSY_SCAN_TAIL_LINES = 2
BLOCK_SCAN_TAIL_LINES = 12


def fail(msg, code=1):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(code)


def _env_markers(var):
    raw = os.environ.get(var, "")
    parts = []
    for chunk in raw.replace("|", "\n").splitlines():
        chunk = chunk.strip()
        if chunk:
            parts.append(chunk.lower())
    return parts


def capture(target, scrollback):
    """Return the captured pane text, or exit with an actionable error."""
    cmd = ["tmux", "capture-pane", "-t", target, "-p"]
    if scrollback > 0:
        cmd += ["-S", f"-{scrollback}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        fail(
            f"tmux capture-pane failed for target '{target}': "
            f"{stderr or 'unknown error'}. "
            f"Check the target with: tmux has-session -t {target}",
            code=1,
        )
    return result.stdout


def _tail_lower(text, n):
    nonempty = [ln for ln in text.splitlines() if ln.strip()]
    return "\n".join(nonempty[-n:]).lower()


def looks_busy(text, markers):
    return any(m in _tail_lower(text, BUSY_SCAN_TAIL_LINES) for m in markers)


def looks_blocked(text, markers):
    return any(m in _tail_lower(text, BLOCK_SCAN_TAIL_LINES) for m in markers)


def new_lines(baseline, current):
    """Lines present in `current` that weren't in the `baseline` capture.

    Agent TUIs redraw the whole frame, so a positional diff is noisy. Instead,
    treat the baseline's non-empty lines as a seen-set and return current's
    non-empty lines that aren't in it — that surfaces the freshly written reply
    while dropping unchanged chrome. Order is preserved; duplicates within the
    new content are kept (a reply may legitimately repeat a line).
    """
    seen = {ln for ln in baseline.splitlines() if ln.strip()}
    out = [ln for ln in current.splitlines() if ln.strip() and ln not in seen]
    return "\n".join(out)


def emit(text):
    sys.stdout.write(text)
    if not text.endswith("\n"):
        sys.stdout.write("\n")


def main():
    parser = argparse.ArgumentParser(
        description="Wait until a tmux agent pane is idle, then print what's new.",
        add_help=True,
    )
    parser.add_argument("target", help="tmux target: session name or session:window.pane")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--quiet-cycles", type=int, default=3)
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--scrollback", type=int, default=0)
    parser.add_argument("--full", action="store_true", help="print the whole pane, not just new lines")
    parser.add_argument("--no-print", action="store_true")
    parser.add_argument("--busy-marker", action="append", default=[])
    parser.add_argument("--block-marker", action="append", default=[])
    args = parser.parse_args()

    if shutil.which("tmux") is None:
        fail(
            "tmux is not installed or not on PATH. Install it "
            "(brew install tmux / apt install tmux) and retry.",
            code=1,
        )
    if args.quiet_cycles < 1:
        fail("--quiet-cycles must be >= 1.", code=1)
    if args.interval <= 0:
        fail("--interval must be > 0.", code=1)

    busy_markers = list(DEFAULT_BUSY_MARKERS) + _env_markers("TAC_BUSY_MARKERS") + [m.lower() for m in args.busy_marker]
    block_markers = list(DEFAULT_BLOCK_MARKERS) + _env_markers("TAC_BLOCK_MARKERS") + [m.lower() for m in args.block_marker]

    # Fail fast if the target session doesn't exist, with an actionable message.
    has = subprocess.run(
        ["tmux", "has-session", "-t", args.target],
        capture_output=True,
        text=True,
    )
    if has.returncode != 0:
        fail(
            f"target session '{args.target}' not found. "
            f"List sessions with: tmux list-sessions",
            code=1,
        )

    deadline = time.monotonic() + args.timeout
    baseline = capture(args.target, args.scrollback)  # state at the start of the wait
    previous = baseline
    stable_reads = 1  # the first capture counts as one read of the current state

    while time.monotonic() < deadline:
        time.sleep(args.interval)
        current = capture(args.target, args.scrollback)

        if current != previous or looks_busy(current, busy_markers):
            # Output changed, or a spinner is up — not settled yet.
            stable_reads = 0
            previous = current
            continue

        stable_reads += 1
        if stable_reads < args.quiet_cycles:
            continue

        # Settled. Decide IDLE vs BLOCKED before printing.
        if looks_blocked(current, block_markers):
            print(
                f"Error: target '{args.target}' is blocked on a prompt that needs "
                f"human input (e.g. a trust or auth dialog). Do NOT send a message "
                f"— it would be read as menu input. Show the pane to the user and "
                f"ask how to respond.",
                file=sys.stderr,
            )
            if not args.no_print:
                emit(current)  # always show the full pane so the user sees the dialog
            return 3

        if not args.no_print:
            out = current if args.full else new_lines(baseline, current)
            emit(out if out.strip() else current)  # fall back to full if delta is empty
        return 0

    # Timed out. Emit what we last saw so the caller still has context.
    print(
        f"Error: target '{args.target}' did not settle within "
        f"{args.timeout:.0f}s ({args.quiet_cycles} quiet cycles never reached). "
        f"The agent may still be working — increase --timeout or re-check the pane.",
        file=sys.stderr,
    )
    if not args.no_print:
        emit(previous if args.full else new_lines(baseline, previous) or previous)
    return 2


if __name__ == "__main__":
    sys.exit(main())
