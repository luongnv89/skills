#!/usr/bin/env python3
"""One-call fleet status report for a Herdr agent fleet.

`herdr api snapshot` returns the whole live session — workspaces, tabs, panes,
layouts and agent records — in a single socket round trip. Rendering the fleet
from that snapshot costs one `herdr` invocation regardless of fleet size, where
per-agent `herdr agent get` polling costs N and can observe a torn view (agent
A read before B changed state).

Use this for every status/monitor/report step: the orchestrator's periodic
check, the "what is the fleet doing" answer, and the final run report.

Usage:
    python3 fleet_status.py                      # every agent the server sees
    python3 fleet_status.py --tab w1:t1          # only this tab (the fleet)
    python3 fleet_status.py --workspace w1
    python3 fleet_status.py --panes              # include agent-less panes
    python3 fleet_status.py --json               # machine-readable
    python3 fleet_status.py --fail-on-blocked    # exit 3 if any agent blocked

Exit codes:
    0  report rendered
    1  herdr missing, snapshot failed, or unparseable
    3  --fail-on-blocked and at least one agent is blocked
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys

STATUSES = ("working", "blocked", "done", "idle", "unknown")

# Attention order: what a human must look at first comes first.
ORDER = {"blocked": 0, "done": 1, "working": 2, "idle": 3, "unknown": 4}


def snapshot() -> dict:
    """Return the live session snapshot, or exit 1 with a reason on stderr."""
    if not shutil.which("herdr"):
        print("Error: herdr is not installed or not on PATH.", file=sys.stderr)
        raise SystemExit(1)
    proc = subprocess.run(
        ["herdr", "api", "snapshot"], capture_output=True, text=True
    )
    if proc.returncode != 0:
        detail = proc.stderr.strip() or f"exit {proc.returncode}"
        print(f"Error: 'herdr api snapshot' failed: {detail}", file=sys.stderr)
        raise SystemExit(1)
    try:
        return json.loads(proc.stdout)["result"]["snapshot"]
    except Exception as exc:  # noqa: BLE001 — any malformed shape is fatal here
        print(f"Error: could not parse snapshot ({exc}).", file=sys.stderr)
        raise SystemExit(1) from exc


def status_of(record: dict) -> str:
    """Fail-closed status read: anything off-enum reports as `unknown`."""
    raw = record.get("agent_status")
    return raw if isinstance(raw, str) and raw in STATUSES else "unknown"


def rows(snap: dict, tab: str | None, workspace: str | None, panes: bool) -> list[dict]:
    records = list(snap.get("agents") or [])
    if panes:
        seen = {r.get("pane_id") for r in records}
        for pane in snap.get("panes") or []:
            if pane.get("pane_id") not in seen:
                records.append(pane)
    out = []
    for rec in records:
        if tab and rec.get("tab_id") != tab:
            continue
        if workspace and rec.get("workspace_id") != workspace:
            continue
        tokens = rec.get("tokens") if isinstance(rec.get("tokens"), dict) else {}
        out.append(
            {
                "name": rec.get("name") or "-",
                "pane_id": rec.get("pane_id") or "-",
                "kind": rec.get("agent") or "-",
                "status": status_of(rec),
                # Metadata title (set by `herdr pane report-metadata`) is the
                # orchestrator's own label; the terminal title is what the CLI
                # itself last advertised. Prefer ours, fall back to theirs.
                "title": rec.get("title") or rec.get("terminal_title_stripped") or "",
                "tokens": tokens,
                "focused": bool(rec.get("focused")),
                "cwd": rec.get("foreground_cwd") or rec.get("cwd") or "",
                "seq": rec.get("state_change_seq"),
            }
        )
    out.sort(key=lambda r: (ORDER.get(r["status"], 9), r["pane_id"]))
    return out


def render(snap: dict, items: list[dict]) -> str:
    counts = {s: sum(1 for i in items if i["status"] == s) for s in STATUSES}
    plural = "" if len(items) == 1 else "s"
    lines = [
        f"Fleet status  ({len(items)} agent{plural} · herdr {snap.get('version', '?')})",
        "  " + " · ".join(f"{s}={counts[s]}" for s in STATUSES),
        "",
    ]
    if not items:
        lines.append("  (no agents match this scope)")
        return "\n".join(lines)
    width = max(len(i["name"]) for i in items)
    for i in items:
        mark = "*" if i["focused"] else " "
        note = i["title"][:60]
        if i["tokens"]:
            note = (note + "  " if note else "") + " ".join(
                f"{k}={v}" for k, v in sorted(i["tokens"].items())
            )
        lines.append(
            f"{mark} {i['name']:<{width}}  {i['pane_id']:<10} "
            f"{i['status']:<8} {i['kind']:<10} {note}"
        )
    blocked = [i["name"] for i in items if i["status"] == "blocked"]
    if blocked:
        lines += ["", f"  ATTENTION: blocked, a human must answer: {', '.join(blocked)}"]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tab", help="restrict to one tab id (the fleet's tab)")
    ap.add_argument("--workspace", help="restrict to one workspace id")
    ap.add_argument(
        "--panes",
        action="store_true",
        help="also list panes with no detected agent",
    )
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    ap.add_argument(
        "--fail-on-blocked",
        action="store_true",
        help="exit 3 when any listed agent is blocked",
    )
    args = ap.parse_args(argv)

    snap = snapshot()
    items = rows(snap, args.tab, args.workspace, args.panes)
    if args.json:
        print(
            json.dumps(
                {
                    "version": snap.get("version"),
                    "focused_pane_id": snap.get("focused_pane_id"),
                    "agents": items,
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(render(snap, items))
    if args.fail_on_blocked and any(i["status"] == "blocked" for i in items):
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
