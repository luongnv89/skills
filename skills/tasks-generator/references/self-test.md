# Self-Test Checklist

Run these checks before declaring success. If any check fails, fix `tasks.md` before reporting completion.

1. `grep -c "^### Task " tasks.md` — must be >= 15.
2. `python3 -c 'import re,sys; text=open(sys.argv[1], encoding="utf-8").read(); ids=re.findall(r"^### Task ([0-9]+\.[0-9]+):", text, re.M); assert len(ids) == len(set(ids)), ids' tasks.md` — every heading uses the canonical `<sprint>.<index>` form and duplicate IDs fail even when titles differ.
3. Every `Depends On` and `Blocks` ID also appears as a task heading (no dangling or fabricated references).
4. No task has itself in its own dependency chain (no cycles).
5. Each `### Task` block contains all four labels: `**Description**`, `**Acceptance Criteria**`, `**Dependencies**`, `**PRD Reference**`.
6. Indices are unique across each sprint even when tasks belong to different workstreams; workstream names never appear in task IDs.
7. Same-sprint edges are represented in both directions: `A` in `B`'s
   `depends_on` exactly matches `B` in `A`'s `blocks`; the resolver adds the
   reciprocal `blocks` entry for a verified cross-sprint dependency in its
   normalized combined map.

## Focused Dependency Contract Fixture

Run this small source-and-data fixture from the repository root. It covers the
actual agent/template heading and schema contracts, two worker workstreams, a
legal cross-sprint edge, five distinct immediate dependents, and the negative
case where five prerequisites alone do not make a bottleneck. It uses only
Python's standard library; do not add a graph helper or test framework.

```bash
repo_root="$(git rev-parse --show-toplevel)"
python3 - "$repo_root" <<'PY'
import re
import sys
from pathlib import Path

repo_root = Path(sys.argv[1]).resolve()
worker = (repo_root / "skills/tasks-generator/agents/sprint-worker.md").read_text()
resolver = (repo_root / "skills/tasks-generator/agents/dependency-resolver.md").read_text()
template = (repo_root / "skills/tasks-generator/references/tasks-template.md").read_text()

# Source contracts: headings are ### Task <sprint>.<index>, not workstream IDs.
for source in (resolver, template):
    assert not re.search(r"^#### Task ", source, re.MULTILINE)
    headings = re.findall(r"^### Task ([0-9]+\.[0-9]+):", source, re.MULTILINE)
    assert headings
    assert all(re.fullmatch(r"[0-9]+\.[0-9]+", task_id) for task_id in headings)
resolver_headings = re.findall(r"^### Task ([0-9]+\.[0-9]+):", resolver, re.MULTILINE)
assert len(resolver_headings) == len(set(resolver_headings)), resolver_headings
legacy_id = re.compile(r"\b[0-9]+\.[A-Za-z][A-Za-z0-9_-]*\.[0-9]+\b")
assert not legacy_id.search(worker + resolver + template)
assert "WORKSTREAM_ID" not in worker
assert re.search(r'"task_id":\s*"<sprint>\.<index>"', worker)
assert re.search(r'"workstream":\s*', worker)
assert re.search(r'"depends_on":\s*\["<sprint>\.<index>"\]', worker)
assert re.search(r'"blocks":\s*\["<sprint>\.<index>"\]', worker)

# Separate worker outputs: a worker records prior IDs only in depends_on.
worker_sprints = {
    1: {
        "1.1": {"workstream": "backend", "depends_on": [],
                "blocks": ["1.3", "1.4", "1.5", "1.6", "1.7"]},
        "1.2": {"workstream": "frontend", "depends_on": [], "blocks": []},
        "1.3": {"workstream": "backend", "depends_on": ["1.1"], "blocks": []},
        "1.4": {"workstream": "backend", "depends_on": ["1.1"], "blocks": []},
        "1.5": {"workstream": "frontend", "depends_on": ["1.1"], "blocks": []},
        "1.6": {"workstream": "frontend", "depends_on": ["1.1"], "blocks": []},
        "1.7": {"workstream": "frontend", "depends_on": ["1.1"], "blocks": []},
    },
    2: {
        "2.1": {"workstream": "frontend", "depends_on": ["1.2"], "blocks": []},
    },
}
task_ids = [task_id for sprint in worker_sprints.values() for task_id in sprint]
tasks = {task_id: task for sprint in worker_sprints.values() for task_id, task in sprint.items()}
assert len(task_ids) == len(set(task_ids)) == len(tasks)
assert all(re.fullmatch(r"[0-9]+\.[0-9]+", task_id) for task_id in task_ids)
for sprint, sprint_tasks in worker_sprints.items():
    indices = [task_id.split(".")[1] for task_id in sprint_tasks]
    assert len(indices) == len(set(indices))
    assert all(task_id.split(".")[0] == str(sprint) for task_id in sprint_tasks)
assert {tasks[task_id]["workstream"] for task_id in worker_sprints[1]} == {"backend", "frontend"}

# Worker direction rule: same-sprint edges are inverse; prior dependencies are
# verified but do not require a worker to edit another worker's blocks.
for task_id, task in tasks.items():
    current_sprint = int(task_id.split(".")[0])
    for dependency in task["depends_on"]:
        assert dependency in tasks, (task_id, dependency)
        dependency_sprint = int(dependency.split(".")[0])
        assert dependency_sprint <= current_sprint
        if dependency_sprint == current_sprint:
            assert task_id in tasks[dependency]["blocks"]
    for blocked in task["blocks"]:
        assert blocked in tasks, (task_id, blocked)
        blocked_sprint = int(blocked.split(".")[0])
        if blocked_sprint == current_sprint:
            assert task_id in tasks[blocked]["depends_on"]
assert tasks["2.1"]["depends_on"] == ["1.2"]
assert tasks["1.2"]["blocks"] == []

# Resolver normalization derives reciprocal blocks in memory, including a
# later-sprint block, without inventing a dependency.
normalized = {
    task_id: {**task, "blocks": list(task["blocks"])}
    for task_id, task in tasks.items()
}
for task_id, task in tasks.items():
    for dependency in task["depends_on"]:
        if task_id not in normalized[dependency]["blocks"]:
            normalized[dependency]["blocks"].append(task_id)
assert normalized["1.2"]["blocks"] == ["2.1"]
assert int("2.1".split(".")[0]) > int("1.2".split(".")[0])
assert normalized["2.1"]["depends_on"] == ["1.2"]
for task_id, task in normalized.items():
    for dependency in task["depends_on"]:
        assert task_id in normalized[dependency]["blocks"]
    for blocked in task["blocks"]:
        assert task_id in normalized[blocked]["depends_on"]

downstream = {task_id for task_id, task in normalized.items()
              if "1.1" in task["depends_on"]}
assert downstream == {"1.3", "1.4", "1.5", "1.6", "1.7"}
assert len(set(normalized["1.1"]["blocks"])) == 5
bottlenecks = {task_id for task_id, task in normalized.items()
               if len(set(task["blocks"])) >= 5}
assert bottlenecks == {"1.1"}
prerequisites_only = {"depends_on": ["1.1", "1.2", "1.3", "1.4", "1.5"],
                      "blocks": []}
assert len(prerequisites_only["depends_on"]) == 5
assert len(prerequisites_only["blocks"]) < 5
print("contract fixture: PASS")
PY
```
