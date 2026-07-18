#!/usr/bin/env python3
"""Wait until a Herdr agent pane is idle/done (or content-stable), then print what's new.

Primary path: `herdr wait agent-status` for idle|done|blocked when Herdr detects the agent.
Fallback: poll `herdr pane read` until the transcript stops changing (unknown agents).

Exit codes:
    0  idle/done (settled, ready for the next message)
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
    --prefer-status      use herdr status waits first (default: on)
    --no-status          skip status waits; content-stability only
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
        # likely pane id wN:pM or tab id wN:tM — prefer as-is if pane get works
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

    # scan list
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
    # CLI may return plain text or JSON depending on version — prefer raw stdout text
    out = cp.stdout or ""
    try:
        d = json.loads(out)
        # common shapes
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", help="pane id or agent name")
    ap.add_argument("--timeout", type=float, default=120.0)
    ap.add_argument("--quiet-cycles", type=int, default=3)
    ap.add_argument("--interval", type=float, default=2.0)
    ap.add_argument("--lines", type=int, default=60)
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--no-print", action="store_true")
    ap.add_argument("--prefer-status", action=argparse.BooleanOptionalAction, default=True)
    args = ap.parse_args()

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

    # Fast path: already terminal
    st = agent_status(pane_id)
    if st == "blocked":
        if not args.no_print:
            print(baseline if args.full else "")
        return 3
    if st in ("idle", "done") and args.prefer_status:
        # might still be pre-task idle; only treat as done if caller waited after send
        # Content path still runs if we want delta — but status is authoritative for blocked
        pass

    if args.prefer_status and st not in (None, "unknown"):
        remaining_ms = max(1, int((deadline - time.time()) * 1000))
        # wait for blocked first with short timeout? better: loop statuses
        # Wait until not working: race done and idle via polling get
        while time.time() < deadline:
            st = agent_status(pane_id)
            if st == "blocked":
                if not args.no_print:
                    print(pane_read(pane_id, args.lines) if args.full else "")
                return 3
            if st in ("idle", "done"):
                final = pane_read(pane_id, args.lines)
                if not args.no_print:
                    if args.full:
                        print(final)
                    else:
                        # print suffix not in baseline
                        if final.startswith(baseline):
                            print(final[len(baseline) :].lstrip("\n"))
                        else:
                            print(final)
                return 0
            if st == "working":
                # block until done or idle
                slice_ms = min(30_000, max(1, int((deadline - time.time()) * 1000)))
                if wait_status(pane_id, "done", slice_ms) or wait_status(pane_id, "idle", 1_000):
                    continue
                continue
            # unknown — fall through to content stability after loop break
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
                print(last if args.full else "")
            return 3
        cur = pane_read(pane_id, args.lines)
        if cur == last:
            quiet += 1
            if quiet >= args.quiet_cycles:
                if st == "working":
                    quiet = 0  # still working chrome-stable briefly
                    continue
                if not args.no_print:
                    if args.full:
                        print(cur)
                    else:
                        if cur.startswith(baseline):
                            print(cur[len(baseline) :].lstrip("\n"))
                        else:
                            print(cur)
                return 0
        else:
            quiet = 0
            last = cur
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.TimeoutExpired:
        sys.exit(2)
