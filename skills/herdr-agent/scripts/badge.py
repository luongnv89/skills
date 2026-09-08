#!/usr/bin/env python3
"""Badge a fleet pane with orchestrator-owned display metadata.

`herdr pane report-metadata` writes display-only fields that Herdr renders in
the human's sidebar: a pane title, a shown agent name, per-status labels, and
named tokens (rendered as `$name` in Agent rows). It changes nothing about
semantic agent state, waits, notifications or rollups — it is purely how the
fleet reads on screen.

That makes it the cheapest monitoring surface this skill has. Badge each worker
at spawn with its assigned job, and re-badge as the job changes, and the human
can see which agent owns what without reading a single transcript.

This wrapper exists for one reason the raw CLI does not cover: `report-metadata`
takes a pane id, while fleet bookkeeping is done in agent names. It resolves
either form, then forwards.

Usage:
    python3 badge.py reviewer --title "Review PR 412" --token role=review
    python3 badge.py reviewer --token phase=waiting --ttl-ms 600000
    python3 badge.py w1:p2 --state-label working="reviewing diff" \\
        --state-label done="review ready"

Exit codes:
    0  metadata accepted
    1  usage error, herdr missing, or the target did not resolve
    2  the report-metadata call failed

Caps enforced by Herdr (exceeding them is rejected server-side): 80 characters
per title / display name / state label / token value, at most 16 token keys per
report, 32 retained per pane, and token names of 1-32 ASCII letters, digits,
underscores or hyphens.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys

# Source identifies the reporter to Herdr. A pane accepts sequenced reports
# from at most 32 distinct sources in its lifetime, so keep this constant.
SOURCE = "user:herdr-agent"

STATUS_KEYS = {"idle", "working", "blocked", "done", "unknown"}


def resolve_pane(target: str) -> str | None:
    """Map an agent name or pane id to a pane id, or None if it does not exist."""
    for cmd, path in (
        (["herdr", "pane", "get", target], ("pane",)),
        (["herdr", "agent", "get", target], ("agent",)),
    ):
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            continue
        try:
            record = json.loads(proc.stdout)["result"][path[0]]
            pane_id = record["pane_id"]
        except Exception:  # noqa: BLE001 — try the next surface
            continue
        if isinstance(pane_id, str) and pane_id:
            return pane_id
    return None


def pair(value: str, what: str) -> tuple[str, str]:
    if "=" not in value:
        raise SystemExit(f"Error: --{what} needs NAME=VALUE, got {value!r}")
    name, _, val = value.partition("=")
    return name, val


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("target", help="agent name or pane id")
    ap.add_argument("--title", help="pane title shown in the sidebar")
    ap.add_argument("--display-agent", help="visible agent name")
    ap.add_argument(
        "--state-label",
        action="append",
        default=[],
        metavar="STATUS=TEXT",
        help="label for one status (idle|working|blocked|done|unknown)",
    )
    ap.add_argument(
        "--token",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="named token, rendered as $NAME in Agent rows",
    )
    ap.add_argument("--ttl-ms", type=int, help="expiry for this report (1-86400000)")
    args = ap.parse_args(argv)

    if not shutil.which("herdr"):
        print("Error: herdr is not installed or not on PATH.", file=sys.stderr)
        return 1
    if not (args.title or args.display_agent or args.state_label or args.token):
        print("Error: nothing to report — pass at least one field.", file=sys.stderr)
        return 1

    pane_id = resolve_pane(args.target)
    if pane_id is None:
        print(
            f"Error: {args.target} resolves to no pane or agent. "
            f"List them with 'herdr agent list'.",
            file=sys.stderr,
        )
        return 1

    cmd = ["herdr", "pane", "report-metadata", pane_id, "--source", SOURCE]
    if args.title:
        cmd += ["--title", args.title]
    if args.display_agent:
        cmd += ["--display-agent", args.display_agent]
    for raw in args.state_label:
        status, text = pair(raw, "state-label")
        if status not in STATUS_KEYS:
            print(
                f"Error: state label key {status!r} must be one of "
                f"{', '.join(sorted(STATUS_KEYS))}.",
                file=sys.stderr,
            )
            return 1
        cmd += ["--state-label", f"{status}={text}"]
    for raw in args.token:
        name, value = pair(raw, "token")
        cmd += ["--token", f"{name}={value}"]
    if args.ttl_ms is not None:
        cmd += ["--ttl-ms", str(args.ttl_ms)]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip() or f"exit {proc.returncode}"
        print(f"Error: report-metadata failed for {pane_id}: {detail}", file=sys.stderr)
        return 2
    print(pane_id)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
