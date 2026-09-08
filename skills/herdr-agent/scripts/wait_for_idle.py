#!/usr/bin/env python3
"""Wait until a Herdr PANE finishes work, then print what's new. FALLBACK ONLY.

For any pane hosting a detected agent, use the agent surface instead:
`herdr agent prompt <target> "<task>" --wait --timeout MS` submits and waits in
one server-side request, and `herdr agent wait <target>` is event-driven. Both
beat this script, which polls and can call a slow-thinking agent settled.

This exists for the one case the agent surface cannot address: a pane whose
process Herdr does not recognize. `herdr agent get` returns `agent_not_found`
for it, even though `herdr pane get` reports its `agent_status` as `unknown`.
`preflight_send.py` exits 5 to route you here.

Primary path: poll `herdr pane get` for working → idle|done|blocked.
Fallback: poll `herdr pane read` until the transcript stops changing.

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
    --baseline-file PATH use a pre-send pane-read capture as the baseline
    --completion-marker S require S when working transition was missed
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
                # A null/non-object `pane` (e.g. {"result":{"pane":null}}) makes
                # the subscript raise TypeError — catch it and fall through to
                # the `agent get` path rather than crash with a traceback.
                return d["result"]["pane"]["pane_id"]
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

    cp = run(["herdr", "agent", "get", target])
    if cp.returncode == 0:
        try:
            d = json.loads(cp.stdout)
            agent = d.get("result", {}).get("agent") or d.get("result", {})
            pane = agent.get("pane_id")
            if pane:
                return pane
        except (json.JSONDecodeError, AttributeError, KeyError, TypeError):
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


# Distinct sentinel for a FAILED/unparseable `herdr pane get`, kept separate
# from a valid-but-absent status ("unknown"). Conflating the two is a
# fail-open bug: a persistent lookup failure on a `blocked` pane would look
# like "no status → fall back to content-stability → report ready". Callers
# must treat LOOKUP_FAILED as unverifiable (an error under --ready), while a
# genuine "unknown" (non-integrated CLI) still uses the content-stability path.
LOOKUP_FAILED = "\x00lookup-failed"

# The documented agent-status enum. ANY other value — a number, an empty
# string, a typo, an out-of-band string the server invents — is unverifiable,
# NOT a benign "unknown". Accepting arbitrary truthy values fails open: a
# numeric `123` status would sail past the working/blocked checks and be
# treated as sendable/settled. Absent/null still maps to "unknown" (the
# non-integrated-CLI case); everything off-enum maps to LOOKUP_FAILED so it is
# rejected on --ready and routed to content-stability (which needs real work
# before it settles) on a normal wait.
VALID_STATUSES = frozenset({"idle", "working", "blocked", "done", "unknown"})


def normalize_status(raw: object) -> str:
    """Map a raw agent_status value onto the documented enum.

    absent/null   -> "unknown"        (verifiable; non-integrated CLI)
    in the enum   -> that status
    anything else -> LOOKUP_FAILED    (wrong type, empty string, off-enum)
    """
    if raw is None:
        return "unknown"
    if isinstance(raw, str) and raw in VALID_STATUSES:
        return raw
    return LOOKUP_FAILED


def agent_status(pane_id: str) -> str:
    """Return the pane's agent status (a member of VALID_STATUSES), or
    LOOKUP_FAILED if the `herdr pane get` call failed, didn't parse, or
    reported a value outside the documented enum."""
    cp = run(["herdr", "pane", "get", pane_id])
    if cp.returncode != 0:
        return LOOKUP_FAILED
    try:
        pane = json.loads(cp.stdout)["result"]["pane"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return LOOKUP_FAILED
    # A valid JSON body can still carry a null / non-object `pane` (e.g.
    # {"result": {"pane": null}}); calling .get() on that raises AttributeError.
    # Treat a non-mapping pane as unverifiable rather than crashing.
    if not isinstance(pane, dict):
        return LOOKUP_FAILED
    return normalize_status(pane.get("agent_status"))


def _unverifiable(st: str, args) -> bool:
    """True when a status result is UNVERIFIABLE and that must fail a readiness
    check — i.e. the lookup failed AND we're doing a status-based `--ready`
    wait. This is checked after EVERY `agent_status` call (not just the first)
    so a valid status followed by a later lookup failure cannot slip through a
    loop and return a false ready. A valid "unknown" is verifiable and never
    trips this; non-ready waits and --no-prefer-status are unaffected."""
    return args.ready and args.prefer_status and st == LOOKUP_FAILED


def extract_pane_text(out: str) -> str:
    """Normalize either raw text or `herdr pane read` JSON to transcript text."""
    try:
        d = json.loads(out)
        r = d.get("result", d)
        for key in ("text", "content", "output", "data"):
            if isinstance(r.get(key), str):
                return r[key]
        if isinstance(r.get("lines"), list):
            return "\n".join(str(x) for x in r["lines"])
    except (json.JSONDecodeError, AttributeError):
        pass
    return out


def pane_read(pane_id: str, lines: int) -> str | None:
    """Read a pane's transcript, or None if the read command FAILED.

    A failed read (e.g. the pane disappeared mid-wait) must NOT be treated as
    transcript content: the error text would stabilize like any other output
    and trip a false "completion". Returning None lets callers propagate the
    failure as an error/timeout instead of a spurious success.
    """
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
        return None
    return extract_pane_text(cp.stdout)


STATUS_POLL_S = 0.25


def settle_sleep(deadline: float, cap_s: float = STATUS_POLL_S) -> None:
    """Bounded pause between status re-reads.

    herdr 0.9 exposes no pane-surface status wait: `herdr wait agent-status`
    does not exist (`unknown command: wait`), and `herdr pane wait-output`
    matches transcript text rather than lifecycle state. The status loop
    therefore polls `herdr pane get`, and this pause is what keeps that poll
    from spinning. The cap is load-bearing in the other direction too: control
    MUST return to the caller before the deadline.

    0.25s is chosen against both failure modes. It bounds detection latency
    well inside the short timeouts callers actually pass (a 1s cap can miss a
    transition that lands 1.2s into a 2s wait), while pacing the status loop
    at one tick per 0.25s instead of running it flat out. That is ~4 herdr
    calls per second on the working path and ~12 on the pre-task-idle path,
    which issues three calls per tick, against the ~30 the spin produced.
    """
    remaining = deadline - time.time()
    if remaining <= 0:
        return
    time.sleep(min(cap_s, remaining))


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
    ap.add_argument(
        "--baseline-file",
        help="pre-send `herdr pane read` capture; closes the fast-completion race",
    )
    ap.add_argument(
        "--completion-marker",
        help="marker the agent prints only after finishing the task",
    )
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
    if args.baseline_file:
        try:
            with open(args.baseline_file, encoding="utf-8") as f:
                baseline = extract_pane_text(f.read())
        except OSError as e:
            print(f"Error: could not read baseline file: {e}", file=sys.stderr)
            return 1
    else:
        baseline = pane_read(pane_id, args.lines)
        if baseline is None:
            print(f"Error: could not read pane {pane_id} for baseline", file=sys.stderr)
            return 1
    saw_work = False  # working status or transcript change
    saw_working = False  # authoritative working transition

    st = agent_status(pane_id)
    # Fail closed on an unverifiable status for a --ready wait (see _unverifiable).
    if _unverifiable(st, args):
        print(f"Error: cannot verify readiness of {pane_id} (status lookup failed)", file=sys.stderr)
        return 1
    if st == "blocked":
        if not args.no_print:
            print_delta(baseline, pane_read(pane_id, args.lines) or "", args.full)
        return 3

    if args.ready and st in ("idle", "done") and args.prefer_status:
        if not args.no_print:
            print_delta(baseline, baseline, args.full)
        return 0

    # `unknown` (validly absent status) → content-stability fallback below.
    # LOOKUP_FAILED under --ready was already rejected; for a non-ready wait it
    # also falls through to content-stability (which reads the transcript and
    # will itself error if the pane is gone).
    if args.prefer_status and st not in ("unknown", LOOKUP_FAILED):
        while time.time() < deadline:
            st = agent_status(pane_id)
            if _unverifiable(st, args):
                print(f"Error: readiness of {pane_id} became unverifiable (status lookup failed)", file=sys.stderr)
                return 1
            if st == "blocked":
                if not args.no_print:
                    print_delta(baseline, pane_read(pane_id, args.lines) or "", args.full)
                return 3

            if st == "working":
                saw_work = True
                saw_working = True
                # Single bounded pause, then loop back so the top-of-loop
                # re-read + the `st in ("idle", "done")` branch handle whichever
                # terminal state we reach — `done` and `idle` both land in that
                # one branch, so neither settle can strand us here. The cap is
                # load-bearing in both directions: it bounds detection latency,
                # and it guarantees control returns to the re-read before the
                # deadline. Do NOT reintroduce a blocking status
                # wait here: `herdr wait agent-status` does not exist, and
                # calling it returned instantly, turning this loop into a spin.
                settle_sleep(deadline)
                continue

            if st in ("idle", "done"):
                cur = pane_read(pane_id, args.lines)
                if cur is None:
                    # Pane vanished while we were reading it — a failed read is
                    # not a completed task. Report an error, not success.
                    print(f"Error: pane {pane_id} read failed (pane gone?)", file=sys.stderr)
                    return 1
                if cur != baseline:
                    saw_work = True
                marker_seen = (
                    args.completion_marker is not None
                    and args.completion_marker in cur
                    and args.completion_marker not in baseline
                )
                if args.ready:
                    if not args.no_print:
                        print_delta(baseline, cur, args.full)
                    return 0
                if args.completion_marker is not None:
                    # Marker mode: only a fresh marker (absent from baseline) proves
                    # THIS send finished. A stale `saw_working` from a pane that was
                    # already busy before this send must not short-circuit success.
                    if marker_seen:
                        if not args.no_print:
                            print_delta(baseline, cur, args.full)
                        return 0
                    # Not seen yet: keep waiting (fall through to re-poll below).
                elif saw_working:
                    if not args.no_print:
                        print_delta(baseline, cur, args.full)
                    return 0
                elif saw_work:
                    # Legacy fallback when no marker was arranged before send.
                    break
                # Pre-task idle: pause, then re-read. A working transition is
                # picked up by the top-of-loop read on the next iteration,
                # which sets saw_work/saw_working in the `working` branch.
                settle_sleep(deadline)
                # Also check blocked while waiting to start.
                st = agent_status(pane_id)
                if _unverifiable(st, args):
                    print(f"Error: readiness of {pane_id} became unverifiable (status lookup failed)", file=sys.stderr)
                    return 1
                if st == "blocked":
                    if not args.no_print:
                        print_delta(baseline, pane_read(pane_id, args.lines) or "", args.full)
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
        # A --ready wait that reaches here started from a valid "unknown"; if a
        # LATER lookup fails we can no longer verify readiness, so fail closed
        # rather than let content stability report a false ready (the round-9
        # repro: valid unknown, then lookup failure).
        if _unverifiable(st, args):
            print(f"Error: readiness of {pane_id} became unverifiable (status lookup failed)", file=sys.stderr)
            return 1
        if st == "blocked":
            if not args.no_print:
                print_delta(baseline, last, args.full)
            return 3
        if st == "working":
            saw_work = True
            saw_working = True
        cur = pane_read(pane_id, args.lines)
        if cur is None:
            # Pane disappeared mid-wait — do NOT let a failed read stabilize
            # into a false completion. Surface it as an error.
            print(f"Error: pane {pane_id} read failed (pane gone?)", file=sys.stderr)
            return 1
        if (
            args.completion_marker
            and args.completion_marker in cur
            and args.completion_marker not in baseline
        ):
            if not args.no_print:
                print_delta(baseline, cur, args.full)
            return 0
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
            if args.completion_marker and not args.ready:
                # Marker-enabled sends never infer completion from quiet prompt echo.
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
