#!/usr/bin/env python3
"""Render triage.json as a plan in /plan-to-issues grammar.

Every string that came from the scanner is sanitised before it reaches the page:
newlines collapsed, table pipes escaped, leading '#' stripped. The scan response
quotes content from the target site, so it is untrusted text -- it is copied as
prose, never executed and never allowed to create structure.

Usage: render_plan.py <outdir> [output.md]
"""
import json
import re
import sys
from pathlib import Path

# Scanner-stated prerequisite: AP2 is advertised through the A2A Agent Card.
DEPENDS = {"ap2": "a2aAgentCard"}

MILESTONE_EXIT = {
    "P0": "re-scan reports level {next_target} ({next_name}) or higher",
    "P1": "re-scan reports every discoverability and content-accessibility check as pass",
    "P2": "re-scan reports every bot-access-control check as pass",
    "P3": "re-scan reports every discovery check as pass",
    "P4": "re-scan reports every commerce check as pass",
}


def clean(s, *, cell=False):
    """Collapse scanner text to one safe line."""
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    s = re.sub(r"^#+\s*", "", s)          # no heading injection
    if cell:
        s = s.replace("|", "\\|")          # no column escape
    return s


def main() -> int:
    outdir = Path(sys.argv[1] if len(sys.argv) > 1 else ".agent-ready")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("agent-ready-plan.md")
    t = json.loads((outdir / "triage.json").read_text())

    site = clean(t.get("targetUrl") or t.get("url"))
    is_commerce = bool(t.get("isCommerce"))
    nxt = t.get("nextLevel") or {}
    counts = t.get("counts", {})

    # Stable task ids: phase number + position, so a re-run of the same scan
    # produces the same ids.
    ids = {}
    for ph in t["phases"]:
        n = ph["id"][1:]
        for i, task in enumerate(ph["tasks"], 1):
            ids[task["check"]] = f"{n}.{i}"

    L = []
    L.append(f"# Agent Readiness Plan — {site}")
    L.append("")
    L.append(f"**Baseline:** {t.get('level')}/5 ({clean(t.get('levelName'))}) — "
             f"{counts.get('pass', 0)} pass, {counts.get('fail', 0)} fail, "
             f"{counts.get('neutral', 0)} neutral")
    L.append(f"**Scanner:** isitagentready.com · scanned {clean(t.get('scannedAt'))}")
    L.append(f"**Verify with:** re-scan — `curl -sS -X POST "
             f"https://isitagentready.com/api/scan -H 'Content-Type: application/json' "
             f"-d '{{\"url\":\"{site}\"}}'`")
    if t.get("redirectedFrom") and t["redirectedFrom"] != site:
        L.append(f"**Note:** the scanner followed a redirect from "
                 f"{clean(t['redirectedFrom'])} — fixes must land on {site}.")
    L.append("")
    L.append("Each task closes exactly one failing check. The scanner is the only "
             "source: descriptions are its own fix prompts, and every task is "
             "verified by re-scanning, not by inspection.")
    L.append("")

    for ph in t["phases"]:
        pid = ph["id"]
        mid = f"M{pid[1:]}"
        exit_cond = MILESTONE_EXIT.get(pid, "re-scan reports the phase's checks as pass").format(
            next_target=nxt.get("target"), next_name=clean(nxt.get("name")))
        L.append(f"## Phase {pid} — {clean(ph['title'])}")
        L.append("")
        goal = (f"close {len(ph['tasks'])} failing "
                f"{'check' if len(ph['tasks']) == 1 else 'checks'} in this area")
        L.append(f"**Goal:** {goal} · **Milestone {mid}:** {exit_cond}")
        L.append("")
        L.append(f"### Sprint {pid} — {clean(ph['title'])}")
        L.append("")

        for task in ph["tasks"]:
            tid = ids[task["check"]]
            title = clean(task.get("title")) or clean(task.get("message")) or task["check"]
            desc = clean(task.get("prompt")) or clean(task.get("message"))
            guide = clean(task.get("guide"))
            dep = DEPENDS.get(task["check"])
            deps = ids[dep] if dep and dep in ids else None

            L.append(f"#### Task {tid}: {title}")
            L.append("")
            body = desc
            if guide:
                body += f" Implementation guide: {guide}"
            for spec in (task.get("specUrls") or []):
                body += f" Spec: {clean(spec)}"
            L.append(f"**Description**: {body}")
            L.append(f"**Closes**: — (milestone-enabling: {mid})")
            L.append(f"**Dependencies**: {deps if deps else 'None'}")
            L.append(f"**Effort**: {task.get('effort', 'M')}")
            L.append(f"**Verify**: re-scan {site}; "
                     f"`checks.{task['category']}.{task['check']}.status` is `pass`")
            L.append("**Acceptance Criteria**:")
            if guide:
                L.append(f"- [ ] Implementation follows the guide at {guide}")
            L.append(f"- [ ] Re-scanning {site} reports "
                     f"`checks.{task['category']}.{task['check']}.status` as `pass`")
            L.append(f"- [ ] The change is live on {site}, not only in a preview "
                     f"or staging environment")
            L.append("")

    # --- Milestones --------------------------------------------------------
    L.append("## Milestones")
    L.append("")
    L.append("| ID | Phase | Exit condition | Verify with |")
    L.append("|---|---|---|---|")
    for ph in t["phases"]:
        pid = ph["id"]
        mid = f"M{pid[1:]}"
        exit_cond = MILESTONE_EXIT.get(pid, "phase checks pass").format(
            next_target=nxt.get("target"), next_name=clean(nxt.get("name")))
        L.append(f"| {mid} | {pid} | {clean(exit_cond, cell=True)} | "
                 f"re-scan {clean(site, cell=True)} |")
    L.append("")

    chain = [ids[task["check"]] for ph in t["phases"] for task in ph["tasks"]]
    if chain:
        L.append(f"**Critical path:** {' → '.join(chain[:8])}"
                 + (" → …" if len(chain) > 8 else ""))
        L.append("")

    # --- Deferred ----------------------------------------------------------
    deferred = t.get("deferred") or []
    neutral = t.get("neutral") or []
    if deferred or neutral:
        L.append("## Deferred and out of scope")
        L.append("")
        L.append("| Check | Severity | Why deferred | Revisit when |")
        L.append("|---|---|---|---|")
        for row in deferred + neutral:
            msg = clean(row.get("message"), cell=True)
            if row.get("category") == "commerce" and not is_commerce:
                why = f"{msg} — the scanner detected no commerce signals on this site"
                when = "the site starts selling to agents"
            elif row in deferred:
                why = f"{msg} — deferred by phase mapping"
                when = "the phase is brought into scope"
            else:
                why = f"{msg} — reported as neutral, not a failing check"
                when = "the scanner reports it as a failing check"
            L.append(f"| {row['check']} | low | {why} | {when} |")
        L.append("")

    passing = t.get("passing") or []
    if passing:
        L.append(f"**Already passing ({len(passing)}):** "
                 + ", ".join(f"`{p['check']}`" for p in passing))
        L.append("")

    n_tasks = sum(len(p["tasks"]) for p in t["phases"])
    if n_tasks == 0:
        if deferred:
            n = len(deferred)
            why = ("the scanner detected no commerce signals on this site"
                   if all(r.get("category") == "commerce" for r in deferred)
                   and not is_commerce else "they were deferred by phase mapping")
            print(f"✓ nothing to plan — all {n} failing "
                  f"{'check' if n == 1 else 'checks'} on {site} are deferred: {why} "
                  f"(level {t.get('level')}/5, {t.get('levelName')}).", file=sys.stderr)
        else:
            print(f"✓ nothing to plan — {site} has no failing checks "
                  f"(level {t.get('level')}/5, {t.get('levelName')}).", file=sys.stderr)
        print("  /plan-to-issues rejects a file with no task headings; skip Phase 4.",
              file=sys.stderr)
        return 3
    out.write_text("\n".join(L))
    print(f"✓ wrote {out} — {len(t['phases'])} phases, {n_tasks} tasks, "
          f"{len(deferred)} deferred")
    return 0


if __name__ == "__main__":
    sys.exit(main())
