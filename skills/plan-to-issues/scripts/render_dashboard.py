#!/usr/bin/env python3
"""Render the plan-to-issues epic plan map.

Reads the render input JSON on stdin (schema: references/epic-dashboard.md) and writes the
plan-map block — sentinels included — to stdout. Deterministic: same input, same bytes.
The clock is never read; `synced` is supplied by the caller.

The map is **static**: it encodes which issue implements which plan task, and nothing that
changes as work proceeds. Live status is GitHub's job — children are registered as native
sub-issues of the epic, so the sub-issues panel shows open/closed and progress without this
block ever being rewritten. Nothing here may depend on `state`.

Usage:  python3 render_dashboard.py < dashboard-input.json > dashboard.md
"""

import json
import re
import sys

START = "<!-- plan-dashboard:start -->"
END = "<!-- plan-dashboard:end -->"


def flat(value):
    """Collapse a plan-derived string to a single line.

    Plan text is untrusted markdown. A newline anywhere in it breaks the line-oriented grammar the
    dashboard is built on — it splits an `### P0 — Title` heading in two, and it breaks the
    `- #N — <id> <title>` form that sync's child-parsing grep depends on. Applied to every
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


def is_scalar(value):
    """A JSON scalar that renders as text.

    `bool` subclasses `int`, so a bare `isinstance(value, SCALAR)` admits JSON `true`/`false` and the
    renderer writes a Python repr — `True` — straight into the epic body. Both scalar checks route
    through here so neither can drift.
    """
    return isinstance(value, SCALAR) and not isinstance(value, bool)


def require_list(value, path):
    """Require a list-or-absent whose entries are all scalars.

    Entry types matter as much as the container's: an unhashable entry (a list or dict) reaching a
    dict lookup raises TypeError, which would exit 1 with a traceback instead of exit 2 with a hint.
    """
    require(value is None or isinstance(value, list),
            "%s must be a list, got %s" % (path, type(value).__name__),
            "see references/epic-dashboard.md -> Render input schema")
    for n, entry in enumerate(value or []):
        require(is_scalar(entry),
                "%s[%d] must be a string, got %s" % (path, n, type(entry).__name__))


def require_scalar(value, path, allow_none=False):
    require((value is None and allow_none) or is_scalar(value),
            "%s must be a string, got %s" % (path, type(value).__name__),
            "see references/epic-dashboard.md -> Render input schema")


def require_issue_number(value, path, allow_none=False):
    """Require a real issue number.

    `epic` and `issue` are caller-supplied, not plan-derived, and they are interpolated into
    `#N` refs and the sync hint. A string here is not merely wrong-typed: `"1 --> <!--
    plan-dashboard:end -->"` forges a premature end sentinel, and a newline in `issue` forges
    plan-map task lines that sync then reads back as real children. Collapsing whitespace is
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


def load():
    # Decode explicitly rather than letting `sys.stdin.read()` raise: a plan file in Latin-1 or
    # CP-1252 carries its bytes into dashboard-input.json, and an implicit decode would exit 1 with
    # a traceback — the one shape that escapes the exit-2-with-a-hint contract.
    raw = sys.stdin.buffer.read()
    try:
        raw = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        die("input is not valid UTF-8 (%s)" % exc,
            "write dashboard-input.json as UTF-8 — json.dump(..., ensure_ascii=False) on a UTF-8 stream")
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
    require(re.match(r"^\d{4}-\d{2}-\d{2}\Z", str(data["synced"])),
            "synced must be an ISO date (YYYY-MM-DD), got %r" % (data["synced"],),
            "supply it as `date -u +%Y-%m-%d` — the renderer never reads the clock")
    require_issue_number(data["epic"], "epic")
    require_scalar(data.get("baseline"), "baseline", allow_none=True)
    require_list(data.get("critical_path"), "critical_path")
    # `deferred` rows are objects, not scalars — check the container, then each row's shape.
    require(data.get("deferred") is None or isinstance(data["deferred"], list),
            "deferred must be a list, got %s" % type(data.get("deferred")).__name__,
            "see references/epic-dashboard.md -> Render input schema")
    for k, row in enumerate(data.get("deferred") or []):
        require(isinstance(row, dict),
                "deferred[%d] must be a JSON object, got %s" % (k, type(row).__name__))
        for dkey in ("id", "severity", "why", "revisit"):
            require_scalar(row.get(dkey), "deferred[%d].%s" % (k, dkey), allow_none=True)
    for i, phase in enumerate(data["phases"]):
        if not isinstance(phase, dict):
            die("phases[%d] must be a JSON object, got %s" % (i, type(phase).__name__),
                "see references/epic-dashboard.md -> Render input schema")
        for key in ("id", "title", "tasks"):
            if key not in phase:
                die("phases[%d] missing required key: %s" % (i, key))
        require_scalar(phase["id"], "phases[%d].id" % i)
        require_scalar(phase["title"], "phases[%d].title" % i)
        # `filed` gates the whole progress column: `phase_note()` tests `is False`, so a string
        # "false" or a 0 would silently render a 0% bar for an unfiled phase — the filed-but-unstarted
        # shape the dashboard must never show.
        require(phase.get("filed") is None or isinstance(phase["filed"], bool),
                "phases[%d].filed must be a boolean, got %s" % (i, type(phase.get("filed")).__name__),
                "see references/epic-dashboard.md -> Render input schema")
        require_scalar(phase.get("goal"), "phases[%d].goal" % i, allow_none=True)
        milestone = phase.get("milestone")
        require(milestone is None or isinstance(milestone, dict),
                "phases[%d].milestone must be a JSON object, got %s"
                % (i, type(milestone).__name__))
        for mkey in ("id", "exit"):
            require_scalar((milestone or {}).get(mkey),
                           "phases[%d].milestone.%s" % (i, mkey), allow_none=True)
        if not isinstance(phase["tasks"], list):
            die("phases[%d].tasks must be a list, got %s" % (i, type(phase["tasks"]).__name__),
                "use [] for a phase with no tasks — see references/epic-dashboard.md -> Render input schema")
        for j, task in enumerate(phase["tasks"]):
            if not isinstance(task, dict):
                die("phases[%d].tasks[%d] must be a JSON object, got %s"
                    % (i, j, type(task).__name__))
            for key in ("task_id", "title"):
                if key not in task:
                    die("phases[%d].tasks[%d] missing required key: %s" % (i, j, key))
            require_scalar(task["task_id"], "phases[%d].tasks[%d].task_id" % (i, j))
            require_scalar(task["title"], "phases[%d].tasks[%d].title" % (i, j))
            # `state` is accepted for backward compatibility and deliberately IGNORED: the map is
            # static, and live status comes from GitHub's sub-issues panel. Rendering it here is what
            # forced a re-sync on every issue close.
            require_scalar(task.get("state"), "phases[%d].tasks[%d].state" % (i, j),
                           allow_none=True)
            require_issue_number(task.get("issue"), "phases[%d].tasks[%d].issue" % (i, j),
                                 allow_none=True)
            require_list(task.get("depends_on"), "phases[%d].tasks[%d].depends_on" % (i, j))
            require_list(task.get("unknown_deps"), "phases[%d].tasks[%d].unknown_deps" % (i, j))
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


def task_line(task):
    """One static row: which issue implements which plan task.

    No checkbox. GitHub does not auto-check a task-list box from the referenced issue's state
    (verified: a closed issue referenced from another body still renders `aria-label="Incomplete
    task"`), so a checkbox here is a claim that goes stale the moment the issue closes — and it is
    what made a `sync` necessary after every close. The issue number is the live link; the
    sub-issues panel is the live status.
    """
    num = "#%s" % flat(task["issue"]) if task.get("issue") else "(not filed)"
    line = "- %s — %s %s" % (num, flat(task["task_id"]), flat(task["title"]))
    notes = []
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
    out = [START, "", "## Plan", ""]

    head = "**Plan:** `%s`" % flat(data["plan_path"])
    if data.get("baseline"):
        head += " · **Baseline at audit:** %s" % flat(data["baseline"])
    out.append(head)
    out.append("")
    out.append("Open/closed status is live in the **Sub-issues** panel above — this map is static "
               "and is rewritten only when issues are filed.")
    out.append("")

    out.append("| Phase | Milestone | Tasks |")
    out.append("|---|---|---|")
    for phase in data["phases"]:
        ms = phase.get("milestone") or {}
        ms_cell = "%s — %s" % (cell(ms.get("id", "—")), cell(ms.get("exit", "—"))) if ms else "—"
        note = phase_note(phase)
        # A count of plan tasks is static — it changes only when the plan or the filing scope does,
        # never when an issue closes. That is the line between what may live here and what may not.
        tasks_cell = ("— %s" % note) if note else "%d" % len(phase["tasks"])
        out.append("| %s | %s | %s |" % (cell(phase_label(phase)), ms_cell, tasks_cell))
    out.append("")

    for phase in data["phases"]:
        tasks = phase["tasks"]
        note = phase_note(phase)
        heading = "### %s — %s" % (flat(phase["id"]), flat(phase["title"]))
        if note:
            heading += " · %s" % note
        out.append(heading)
        out.append("")
        ms = phase.get("milestone") or {}
        meta = []
        if phase.get("goal"):
            meta.append("**Goal:** %s" % flat(phase["goal"]))
        if ms:
            meta.append("**Milestone %s:** %s"
                        % (flat(ms.get("id", "—")), flat(ms.get("exit", "—"))))
        if meta:
            out.append(" · ".join(meta))
            out.append("")
        for task in tasks:
            task["depends_on"] = task.get("_dep_refs", [])
            out.append(task_line(task))
        if tasks:
            out.append("")

    # The critical path is an ordering the plan asserts — static. The per-node ✅/○ icons it used to
    # carry were not, and a "Next actionable" list is state-derived by definition: both are gone, and
    # both are answerable from the sub-issues panel.
    cp = data.get("critical_path") or []
    if cp:
        chain = []
        for task_id in cp:
            target = index.get(task_id)
            if target and target.get("issue"):
                chain.append("#%s" % flat(target["issue"]))
            elif target:
                chain.append(flat(task_id))
            else:
                chain.append("%s ⚠" % flat(task_id))
        out.append("**Critical path:** %s" % " → ".join(chain))
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

    out.append("<sub>Plan map rendered %s by `/plan-to-issues` — re-render after filing more issues "
               "with `/plan-to-issues sync %s`</sub>" % (flat(data["synced"]), flat(data["epic"])))
    out.append(END)
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    sys.stdout.write(render(load()))
