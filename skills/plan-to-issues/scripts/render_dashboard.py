#!/usr/bin/env python3
"""Render the plan-to-issues epic dashboard.

Reads the render input JSON on stdin (schema: references/epic-dashboard.md) and writes the
dashboard block — sentinels included — to stdout. Deterministic: same input, same bytes.
The clock is never read; `synced` is supplied by the caller.

Usage:  python3 render_dashboard.py < dashboard-input.json > dashboard.md
"""

import json
import re
import sys

START = "<!-- plan-dashboard:start -->"
END = "<!-- plan-dashboard:end -->"
CELLS = 10

STATE_ICON = {"closed": "✅", "open": "○", "missing": "⚠"}


def flat(value):
    """Collapse a plan-derived string to a single line.

    Plan text is untrusted markdown. A newline anywhere in it breaks the line-oriented grammar the
    dashboard is built on — it splits an `### P0 — Title` heading in two, and it breaks the
    `- [x] #N — <id> <title>` form that sync's child-parsing grep depends on. Applied to every
    plan-derived string, table cell or not.
    """
    text = "—" if value is None else str(value)
    return " ".join(text.split()) or "—"


def cell(value):
    """Escape a plan-derived string for use inside a markdown table cell.

    Collapses newlines (see flat()) and escapes `|`, which would otherwise open an extra column and
    break the whole table out of alignment.
    """
    return flat(value).replace("\\", "\\\\").replace("|", "\\|") or "—"


def require(cond, msg, hint=None):
    if not cond:
        die(msg, hint)


SCALAR = (str, int, float)


def require_list(value, path):
    """Require a list-or-absent whose entries are all scalars.

    Entry types matter as much as the container's: an unhashable entry (a list or dict) reaching a
    dict lookup raises TypeError, which would exit 1 with a traceback instead of exit 2 with a hint.
    """
    require(value is None or isinstance(value, list),
            "%s must be a list, got %s" % (path, type(value).__name__),
            "see references/epic-dashboard.md -> Render input schema")
    for n, entry in enumerate(value or []):
        require(isinstance(entry, SCALAR),
                "%s[%d] must be a string, got %s" % (path, n, type(entry).__name__))


def require_scalar(value, path, allow_none=False):
    require((value is None and allow_none) or isinstance(value, SCALAR),
            "%s must be a string, got %s" % (path, type(value).__name__),
            "see references/epic-dashboard.md -> Render input schema")


def require_issue_number(value, path, allow_none=False):
    """Require a real issue number.

    `epic` and `issue` are caller-supplied, not plan-derived, and they are interpolated into
    `#N` refs and the sync hint. A string here is not merely wrong-typed: `"1 --> <!--
    plan-dashboard:end -->"` forges a premature end sentinel, and a newline in `issue` forges
    dashboard checklist lines that sync then reads back as real children. Collapsing whitespace is
    not enough — the value must be a number.
    """
    if value is None and allow_none:
        return
    require(isinstance(value, int) and not isinstance(value, bool) and value > 0,
            "%s must be a positive integer issue number, got %r" % (path, value),
            "issue numbers come from `gh issue create`; do not pass them as strings")


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
    require_scalar(data["plan_path"], "plan_path")
    require_scalar(data["synced"], "synced")
    require(re.match(r"^\d{4}-\d{2}-\d{2}$", str(data["synced"])),
            "synced must be an ISO date (YYYY-MM-DD), got %r" % (data["synced"],),
            "supply it as `date -u +%Y-%m-%d` — the renderer never reads the clock")
    require_issue_number(data["epic"], "epic")
    require_scalar(data.get("baseline"), "baseline", allow_none=True)
    require_list(data.get("critical_path"), "critical_path")
    require_list(data.get("deferred"), "deferred")
    for k, row in enumerate(data.get("deferred") or []):
        require(isinstance(row, dict),
                "deferred[%d] must be a JSON object, got %s" % (k, type(row).__name__))
    for i, phase in enumerate(data["phases"]):
        if not isinstance(phase, dict):
            die("phases[%d] must be a JSON object, got %s" % (i, type(phase).__name__),
                "see references/epic-dashboard.md -> Render input schema")
        for key in ("id", "title", "tasks"):
            if key not in phase:
                die("phases[%d] missing required key: %s" % (i, key))
        milestone = phase.get("milestone")
        require(milestone is None or isinstance(milestone, dict),
                "phases[%d].milestone must be a JSON object, got %s"
                % (i, type(milestone).__name__))
        if not isinstance(phase["tasks"], list):
            die("phases[%d].tasks must be a list, got %s" % (i, type(phase["tasks"]).__name__),
                "use [] for a phase with no tasks — see references/epic-dashboard.md -> Render input schema")
        for j, task in enumerate(phase["tasks"]):
            if not isinstance(task, dict):
                die("phases[%d].tasks[%d] must be a JSON object, got %s"
                    % (i, j, type(task).__name__))
            for key in ("task_id", "title", "state"):
                if key not in task:
                    die("phases[%d].tasks[%d] missing required key: %s" % (i, j, key))
            require_scalar(task["task_id"], "phases[%d].tasks[%d].task_id" % (i, j))
            require_scalar(task["title"], "phases[%d].tasks[%d].title" % (i, j))
            require_scalar(task["state"], "phases[%d].tasks[%d].state" % (i, j))
            require_issue_number(task.get("issue"), "phases[%d].tasks[%d].issue" % (i, j),
                                 allow_none=True)
            require_list(task.get("depends_on"), "phases[%d].tasks[%d].depends_on" % (i, j))
            require_list(task.get("unknown_deps"), "phases[%d].tasks[%d].unknown_deps" % (i, j))
            if task["state"] not in STATE_ICON:
                die("phases[%d].tasks[%d] has state %r — expected open, closed, or missing"
                    % (i, j, task["state"]))
    return data


def phase_label(phase):
    return "%s %s" % (flat(phase["id"]), flat(phase["title"]))


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
    num = "#%s" % flat(task["issue"]) if task.get("issue") else "(not filed)"
    line = "- [%s] %s — %s %s" % (box, num, flat(task["task_id"]), flat(task["title"]))
    notes = []
    if task["state"] == "missing":
        notes.append("⚠ missing")
    deps = [d for d in task.get("depends_on", []) if d]
    if deps:
        notes.append("depends on %s" % ", ".join(flat(d) for d in deps))
    for unknown in task.get("unknown_deps", []) or []:
        notes.append("⚠ unknown dep %s" % flat(unknown))
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
                    refs.append("#%s" % flat(target["issue"]))
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

    head = "**Plan:** `%s`" % flat(data["plan_path"])
    if data.get("baseline"):
        head += " · **Baseline at audit:** %s" % flat(data["baseline"])
    out.append(head)

    all_tasks = [t for p in data["phases"] for t in p["tasks"]]
    done = sum(1 for t in all_tasks if t["state"] == "closed")
    out.append("**Progress:** %d/%d closed %s · **Last synced:** %s"
               % (done, len(all_tasks), bar(done, len(all_tasks)), flat(data["synced"])))
    out.append("")

    out.append("| Phase | Progress | Milestone | Status |")
    out.append("|---|---|---|---|")
    for phase in data["phases"]:
        tasks = phase["tasks"]
        pdone = sum(1 for t in tasks if t["state"] == "closed")
        ms = phase.get("milestone") or {}
        ms_cell = "%s — %s" % (cell(ms.get("id", "—")), cell(ms.get("exit", "—"))) if ms else "—"
        note = phase_note(phase)
        progress = ("— %s" % note) if note else "%d/%d %s" % (pdone, len(tasks), bar(pdone, len(tasks)))
        out.append("| %s | %s | %s | %s |"
                   % (cell(phase_label(phase)), progress, ms_cell, milestone_status(phase)))
    out.append("")

    for phase in data["phases"]:
        tasks = phase["tasks"]
        pdone = sum(1 for t in tasks if t["state"] == "closed")
        note = phase_note(phase)
        heading = "### %s — %s" % (flat(phase["id"]), flat(phase["title"]))
        heading += " · %s" % (note if note else "%d/%d %s" % (pdone, len(tasks), bar(pdone, len(tasks))))
        out.append(heading)
        out.append("")
        ms = phase.get("milestone") or {}
        meta = []
        if phase.get("goal"):
            meta.append("**Goal:** %s" % flat(phase["goal"]))
        if ms:
            meta.append("**Milestone %s:** %s — %s"
                        % (flat(ms.get("id", "—")), flat(ms.get("exit", "—")),
                           milestone_status(phase)))
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
                chain.append("#%s %s" % (flat(target["issue"]), STATE_ICON[target["state"]]))
            elif target:
                chain.append("%s %s" % (flat(task_id), STATE_ICON[target["state"]]))
            else:
                chain.append("%s ⚠" % flat(task_id))
        out.append("**Critical path:** %s" % " → ".join(chain))
        out.append("")

    actionable = []
    for phase in data["phases"]:
        for task in phase["tasks"]:
            if task["state"] != "open" or not task.get("issue"):
                continue
            if task.get("unknown_deps"):
                continue  # an unresolvable dep cannot be shown closed — never call it actionable
            blockers = [index[d] for d in task.get("_dep_ids", []) if d in index]
            if all(b["state"] == "closed" for b in blockers):
                actionable.append("#%s" % flat(task["issue"]))
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
            out.append("| %s | %s | %s | %s |" % (cell(row.get("id", "—")), cell(row.get("severity", "—")),
                                                  cell(row.get("why", "—")), cell(row.get("revisit", "—"))))
        out.append("")

    out.append("<sub>Rendered by `/plan-to-issues` — refresh with `/plan-to-issues sync %s`</sub>"
               % flat(data["epic"]))
    out.append(END)
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    sys.stdout.write(render(load()))
