#!/usr/bin/env python3
"""Render the plan-to-issues epic dashboard.

Reads the render input JSON on stdin (schema: references/epic-dashboard.md) and writes the
dashboard block — sentinels included — to stdout. Deterministic: same input, same bytes.
The clock is never read; `synced` is supplied by the caller.

Usage:  python3 render_dashboard.py < dashboard-input.json > dashboard.md
"""

import json
import sys

START = "<!-- plan-dashboard:start -->"
END = "<!-- plan-dashboard:end -->"
CELLS = 10

STATE_ICON = {"closed": "✅", "open": "○", "missing": "⚠"}


def die(msg, hint=None):
    sys.stderr.write("✗ render_dashboard: %s\n" % msg)
    if hint:
        sys.stderr.write("\n  To fix:  %s\n" % hint)
    sys.exit(2)


def bar(done, total):
    if total <= 0:
        return "░" * CELLS + " 0%"
    pct = int(done * 100 / total)
    filled = int(done * CELLS / total)  # floor: 99% never shows a full bar
    return "%s%s %d%%" % ("█" * filled, "░" * (CELLS - filled), pct)


def load():
    raw = sys.stdin.read()
    if not raw.strip():
        die("no input on stdin", "python3 render_dashboard.py < dashboard-input.json")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        die("input is not valid JSON (%s)" % exc, "validate it: python3 -m json.tool < dashboard-input.json")
    if not isinstance(data, dict):
        die("input must be a JSON object, got %s" % type(data).__name__)
    for key in ("plan_path", "synced", "epic", "phases"):
        if key not in data:
            die("missing required key: %s" % key, "see references/epic-dashboard.md -> Render input schema")
    if not isinstance(data["phases"], list) or not data["phases"]:
        die("`phases` must be a non-empty list — a plan always has at least one phase")
    for i, phase in enumerate(data["phases"]):
        for key in ("id", "title", "tasks"):
            if key not in phase:
                die("phases[%d] missing required key: %s" % (i, key))
        for j, task in enumerate(phase["tasks"]):
            for key in ("task_id", "title", "state"):
                if key not in task:
                    die("phases[%d].tasks[%d] missing required key: %s" % (i, j, key))
            if task["state"] not in STATE_ICON:
                die("phases[%d].tasks[%d] has state %r — expected open, closed, or missing"
                    % (i, j, task["state"]))
    return data


def phase_label(phase):
    return "%s %s" % (phase["id"], phase["title"])


def phase_note(phase):
    """A phase with nothing to list still renders — a missing row reads as done."""
    if phase.get("filed") is False:
        return "not filed"
    if not phase["tasks"]:
        return "no tasks in plan"
    return None


def milestone_status(phase):
    tasks = phase["tasks"]
    if not tasks:
        return "○ not started"
    done = sum(1 for t in tasks if t["state"] == "closed")
    if done == len(tasks):
        return "✅ met"
    return "◐ in progress" if done else "○ not started"


def task_line(task):
    box = "x" if task["state"] == "closed" else " "
    num = "#%s" % task["issue"] if task.get("issue") else "(not filed)"
    line = "- [%s] %s — %s %s" % (box, num, task["task_id"], task["title"])
    notes = []
    if task["state"] == "missing":
        notes.append("⚠ missing")
    deps = [d for d in task.get("depends_on", []) if d]
    if deps:
        notes.append("depends on %s" % ", ".join(deps))
    for unknown in task.get("unknown_deps", []) or []:
        notes.append("⚠ unknown dep %s" % unknown)
    if notes:
        line += "  ·  " + "  ·  ".join(notes)
    return line


def resolve_deps(data):
    """Rewrite each task's depends_on from task ids to #issue refs, keeping unknowns separate."""
    index = {}
    for phase in data["phases"]:
        for task in phase["tasks"]:
            index[task["task_id"]] = task
    for phase in data["phases"]:
        for task in phase["tasks"]:
            refs, unknown = [], list(task.get("unknown_deps") or [])
            for dep in task.get("depends_on") or []:
                target = index.get(dep)
                if target and target.get("issue"):
                    refs.append("#%s" % target["issue"])
                elif target:
                    refs.append(dep)
                else:
                    unknown.append(dep)
            task["_dep_refs"] = refs
            task["_dep_ids"] = list(task.get("depends_on") or [])
            task["unknown_deps"] = unknown
    return index


def render(data):
    index = resolve_deps(data)
    out = [START, "", "## Implementation Dashboard", ""]

    head = "**Plan:** `%s`" % data["plan_path"]
    if data.get("baseline"):
        head += " · **Baseline at audit:** %s" % data["baseline"]
    out.append(head)

    all_tasks = [t for p in data["phases"] for t in p["tasks"]]
    done = sum(1 for t in all_tasks if t["state"] == "closed")
    out.append("**Progress:** %d/%d closed %s · **Last synced:** %s"
               % (done, len(all_tasks), bar(done, len(all_tasks)), data["synced"]))
    out.append("")

    out.append("| Phase | Progress | Milestone | Status |")
    out.append("|---|---|---|---|")
    for phase in data["phases"]:
        tasks = phase["tasks"]
        pdone = sum(1 for t in tasks if t["state"] == "closed")
        ms = phase.get("milestone") or {}
        ms_cell = "%s — %s" % (ms.get("id", "—"), ms.get("exit", "—")) if ms else "—"
        note = phase_note(phase)
        progress = ("— %s" % note) if note else "%d/%d %s" % (pdone, len(tasks), bar(pdone, len(tasks)))
        out.append("| %s | %s | %s | %s |"
                   % (phase_label(phase), progress, ms_cell, milestone_status(phase)))
    out.append("")

    for phase in data["phases"]:
        tasks = phase["tasks"]
        pdone = sum(1 for t in tasks if t["state"] == "closed")
        note = phase_note(phase)
        heading = "### %s — %s" % (phase["id"], phase["title"])
        heading += " · %s" % (note if note else "%d/%d %s" % (pdone, len(tasks), bar(pdone, len(tasks))))
        out.append(heading)
        out.append("")
        ms = phase.get("milestone") or {}
        meta = []
        if phase.get("goal"):
            meta.append("**Goal:** %s" % phase["goal"])
        if ms:
            meta.append("**Milestone %s:** %s — %s"
                        % (ms.get("id", "—"), ms.get("exit", "—"), milestone_status(phase)))
        if meta:
            out.append(" · ".join(meta))
            out.append("")
        for task in tasks:
            task["depends_on"] = task.get("_dep_refs", [])
            out.append(task_line(task))
        if tasks:
            out.append("")

    cp = data.get("critical_path") or []
    if cp:
        chain = []
        for task_id in cp:
            target = index.get(task_id)
            if target and target.get("issue"):
                chain.append("#%s %s" % (target["issue"], STATE_ICON[target["state"]]))
            elif target:
                chain.append("%s %s" % (task_id, STATE_ICON[target["state"]]))
            else:
                chain.append("%s ⚠" % task_id)
        out.append("**Critical path:** %s" % " → ".join(chain))
        out.append("")

    actionable = []
    for phase in data["phases"]:
        for task in phase["tasks"]:
            if task["state"] != "open" or not task.get("issue"):
                continue
            blockers = [index[d] for d in task.get("_dep_ids", []) if d in index]
            if all(b["state"] == "closed" for b in blockers):
                actionable.append("#%s" % task["issue"])
    if actionable:
        out.append("**Next actionable** — open, every dependency closed: %s" % ", ".join(actionable))
        out.append("")

    deferred = data.get("deferred") or []
    if deferred:
        out.append("### Deferred and out of scope")
        out.append("")
        out.append("| Finding | Severity | Why deferred | Revisit when |")
        out.append("|---|---|---|---|")
        for row in deferred:
            out.append("| %s | %s | %s | %s |" % (row.get("id", "—"), row.get("severity", "—"),
                                                  row.get("why", "—"), row.get("revisit", "—")))
        out.append("")

    out.append("<sub>Rendered by `/plan-to-issues` — refresh with `/plan-to-issues sync %s`</sub>"
               % data["epic"])
    out.append(END)
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    sys.stdout.write(render(load()))
