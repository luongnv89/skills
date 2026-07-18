#!/usr/bin/env python3
"""Wait until a Herdr agent pane finishes work, then print what's new.

Primary path: poll `herdr pane get` / status waits for working → idle|done|blocked.
Fallback: poll `herdr pane read` until the transcript stops changing (unknown agents).

By default this is a **post-send completion wait**: it will not treat a pre-existing
idle/done pane as success until it has seen `working` (or a transcript change).
Use --ready for boot/ready waits that may already be idle.

Exit codes:
    0  idle/done after work (or already ready with --ready)
    1  usage / environment error (herdr missing, bad target)
    2  timed out before the pane settled
    3  blocked: needs human input

Usage:
    python3 wait_for_idle.py <target> [options]

    <target>   pane id (w26:p4) or unique agent name (reviewer)

Options:
    --timeout SEC        give up after this many seconds (default: 120)
    --quiet-cycles N     consecutive unchanged reads to call it settled (default: 3)
    --interval SEC       seconds between captures (default: 2)
    --lines N            pane read line window (default: 60)
    --full               print entire last capture, not just new lines
    --no-print           print nothing (exit code only)
    --prefer-status      use herdr status first (default: on)
    --no-prefer-status   content-stability only (alias: --no-status)
    --ready              accept already-idle/done without requiring prior working
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time


def run(cmd: list[str], timeout: float | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def resolve_pane(target: str) -> str:
    """Return a pane_id for a pane id or agent name."""
    if ":" in target and target.split(":", 1)[0].startswith("w"):
        cp = run(["herdr", "pane", "get", target])
        if cp.returncode == 0:
            try:
                d = json.loads(cp.stdout)
                return d["result"]["pane"]["pane_id"]
            except (json.JSONDecodeError, KeyError):
                pass

    cp = run(["herdr", "agent", "get", target])
    if cp.returncode == 0:
        try:
            d = json.loads(cp.stdout)
            agent = d.get("result", {}).get("agent") or d.get("result", {})
            pane = agent.get("pane_id")
            if pane:
                return pane
        except (json.JSONDecodeError, AttributeError, KeyError):
            pass

    cp = run(["herdr", "agent", "list"])
    if cp.returncode != 0:
        raise SystemExit(f"herdr agent list failed: {cp.stderr or cp.stdout}")
    try:
        d = json.loads(cp.stdout)
        agents = d["result"]["agents"]
    except (json.JSONDecodeError, KeyError) as e:
        raise SystemExit(f"could not parse agent list: {e}") from e

    matches = [
        a
        for a in agents
        if a.get("name") == target
        or a.get("pane_id") == target
        or a.get("terminal_id") == target
    ]
    if len(matches) == 1:
        return matches[0]["pane_id"]
    if len(matches) > 1:
        raise SystemExit(f"ambiguous target {target!r}: {[m.get('pane_id') for m in matches]}")
    raise SystemExit(f"target not found: {target!r}")


def agent_status(pane_id: str) -> str | None:
    cp = run(["herdr", "pane", "get", pane_id])
    if cp.returncode != 0:
        return None
    try:
        d = json.loads(cp.stdout)
        return d["result"]["pane"].get("agent_status")
    except (json.JSONDecodeError, KeyError):
        return None


def pane_read(pane_id: str, lines: int) -> str:
    cp = run(
        [
            "herdr",
            "pane",
            "read",
            pane_id,
            "--source",
            "recent-unwrapped",
            "--lines",
            str(lines),
        ]
    )
    if cp.returncode != 0:
        return cp.stdout or cp.stderr or ""
    out = cp.stdout or ""
    try:
        d = json.loads(out)
        r = d.get("result", d)
        for key in ("text", "content", "output", "data"):
            if isinstance(r.get(key), str):
                return r[key]
        if isinstance(r.get("lines"), list):
            return "\n".join(str(x) for x in r["lines"])
    except json.JSONDecodeError:
        pass
    return out


def wait_status(pane_id: str, status: str, timeout_ms: int) -> bool:
    if timeout_ms <= 0:
        return False
    cp = run(
        [
            "herdr",
            "wait",
            "agent-status",
            pane_id,
            "--status",
            status,
            "--timeout",
            str(timeout_ms),
        ]
    )
    return cp.returncode == 0


def print_delta(baseline: str, final: str, full: bool) -> None:
    if full:
        print(final)
        return
    if final.startswith(baseline):
        print(final[len(baseline) :].lstrip("\n"))
    else:
        print(final)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("target", help="pane id or agent name")
    ap.add_argument("--timeout", type=float, default=120.0)
    ap.add_argument("--quiet-cycles", type=int, default=3)
    ap.add_argument("--interval", type=float, default=2.0)
    ap.add_argument("--lines", type=int, default=60)
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--no-print", action="store_true")
    ap.add_argument(
        "--prefer-status",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="use herdr agent-status first (default: true)",
    )
    ap.add_argument(
        "--no-status",
        action="store_true",
        help="alias for --no-prefer-status",
    )
    ap.add_argument(
        "--ready",
        action="store_true",
        help="accept already-idle/done without requiring a prior working transition",
    )
    args = ap.parse_args()
    if args.no_status:
        args.prefer_status = False

    if not shutil.which("herdr"):
        print("Error: herdr not on PATH", file=sys.stderr)
        return 1

    try:
        pane_id = resolve_pane(args.target)
    except SystemExit as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    deadline = time.time() + args.timeout
    baseline = pane_read(pane_id, args.lines)
    saw_work = False  # working status or transcript change

    st = agent_status(pane_id)
    if st == "blocked":
        if not args.no_print:
            print(baseline if args.full else "")
        return 3

    if args.ready and st in ("idle", "done") and args.prefer_status:
        if not args.no_print:
            print_delta(baseline, baseline, args.full)
        return 0

    if args.prefer_status and st not in (None, "unknown"):
        while time.time() < deadline:
            st = agent_status(pane_id)
            if st == "blocked":
                if not args.no_print:
                    print_delta(baseline, pane_read(pane_id, args.lines), args.full)
                return 3

            if st == "working":
                saw_work = True
                slice_ms = min(30_000, max(1, int((deadline - time.time()) * 1000)))
                # Prefer short waits so we can notice idle or done either way
                half = max(1, slice_ms // 2)
                if not wait_status(pane_id, "done", half):
                    wait_status(pane_id, "idle", max(1, int((deadline - time.time()) * 1000)))
                continue

            if st in ("idle", "done"):
                cur = pane_read(pane_id, args.lines)
                if cur != baseline:
                    saw_work = True
                if saw_work or args.ready:
                    if not args.no_print:
                        print_delta(baseline, cur, args.full)
                    return 0
                # Pre-task idle: wait for working (or transcript change via status loop)
                slice_ms = min(5_000, max(1, int((deadline - time.time()) * 1000)))
                if wait_status(pane_id, "working", slice_ms):
                    saw_work = True
                    continue
                # Also check blocked while waiting to start
                if agent_status(pane_id) == "blocked":
                    if not args.no_print:
                        print_delta(baseline, pane_read(pane_id, args.lines), args.full)
                    return 3
                continue

            # unknown mid-flight — fall through to content stability
            break
        else:
            return 2

    # Content-stability fallback
    last = baseline
    quiet = 0
    while time.time() < deadline:
        time.sleep(args.interval)
        st = agent_status(pane_id)
        if st == "blocked":
            if not args.no_print:
                print_delta(baseline, last, args.full)
            return 3
        if st == "working":
            saw_work = True
        cur = pane_read(pane_id, args.lines)
        if cur != last:
            if cur != baseline:
                saw_work = True
            quiet = 0
            last = cur
            continue
        quiet += 1
        if quiet >= args.quiet_cycles:
            if st == "working":
                quiet = 0
                continue
            if not saw_work and not args.ready:
                # still pre-task idle with no transcript change — keep waiting
                quiet = 0
                continue
            if not args.no_print:
                print_delta(baseline, cur, args.full)
            return 0
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.TimeoutExpired:
        sys.exit(2)
