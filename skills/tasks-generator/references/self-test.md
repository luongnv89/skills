# Self-Test Checklist

Run these checks before declaring success. If any check fails, fix `tasks.md` before reporting completion.

1. `grep -c "^### Task " tasks.md` — must be >= 15.
2. `python3 -c 'import re,sys; text=open(sys.argv[1], encoding="utf-8").read(); headings=re.findall(r"^#{1,6}[ \t]+Task\b.*$", text, re.M); canonical=re.compile(r"^### Task ([0-9]+\.[0-9]+):.*$"); assert headings; matches=[canonical.fullmatch(heading) for heading in headings]; assert all(matches), headings; ids=[match.group(1) for match in matches]; assert len(ids) == len(set(ids)), ids' tasks.md` — every task-like heading must be a full canonical `### Task <sprint>.<index>:` heading, and duplicate IDs fail even when titles differ.
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
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

repo_root = Path(sys.argv[1]).resolve()
worker = (repo_root / "skills/tasks-generator/agents/sprint-worker.md").read_text()
resolver = (repo_root / "skills/tasks-generator/agents/dependency-resolver.md").read_text()
template = (repo_root / "skills/tasks-generator/references/tasks-template.md").read_text()
self_test = (repo_root / "skills/tasks-generator/references/self-test.md").read_text()

# Execute the exact documented checklist command against valid and invalid inputs.
checklist_line = next(
    line for line in self_test.splitlines()
    if line.startswith("2. `python3 -c ")
)
command_text = checklist_line[len("2. `"):checklist_line.index("` —")]
assert command_text.endswith(" tasks.md")
documented_command = command_text[:-len(" tasks.md")]
checklist_cases = [
    ("valid", "### Task 1.1: valid\n### Task 1.2: valid\n", True),
    ("malformed", "### Task 1.1: valid\n### Task malformed: bad\n", False),
    ("wrong-level", "### Task 1.1: valid\n#### Task 1.2: wrong level\n", False),
    ("duplicate", "### Task 1.1: first\n### Task 1.1: second\n", False),
]
with tempfile.TemporaryDirectory() as temp_dir:
    for name, contents, expected_success in checklist_cases:
        tasks_path = Path(temp_dir) / name / "tasks.md"
        tasks_path.parent.mkdir()
        tasks_path.write_text(contents, encoding="utf-8")
        result = subprocess.run(
            [*shlex.split(documented_command), str(tasks_path)],
            capture_output=True,
            text=True,
        )
        assert (result.returncode == 0) == expected_success, (
            name, result.stdout, result.stderr
        )

# Source contracts: every task-like heading must be ### Task <sprint>.<index>:
TASK_HEADING = re.compile(r"^### Task ([0-9]+\.[0-9]+):.*$", re.MULTILINE)
TASK_LIKE_HEADING = re.compile(r"^#{1,6}[ \t]+Task\b.*$", re.MULTILINE)


def task_ids_from_markdown(source, *, require_unique=True):
    task_headings = TASK_LIKE_HEADING.findall(source)
    assert task_headings, source
    invalid = [heading for heading in task_headings
               if not TASK_HEADING.fullmatch(heading)]
    assert not invalid, invalid
    task_ids = [TASK_HEADING.fullmatch(heading).group(1)
                for heading in task_headings]
    if require_unique:
        assert len(task_ids) == len(set(task_ids)), task_ids
    return task_ids


def assert_rejects(check, value):
    try:
        check(value)
    except AssertionError:
        return
    raise AssertionError(f"expected rejection: {value!r}")

resolver_headings = task_ids_from_markdown(resolver)
# The template contains separate examples, so duplicate IDs across examples are legal.
template_headings = task_ids_from_markdown(template, require_unique=False)
assert resolver_headings and template_headings
assert_rejects(task_ids_from_markdown, "### Task 1.1 malformed")
assert_rejects(task_ids_from_markdown, "#### Task 1.1: wrong depth")
legacy_id = re.compile(r"\b[0-9]+\.[A-Za-z][A-Za-z0-9_-]*\.[0-9]+\b")
assert not legacy_id.search(worker + resolver + template)
assert "WORKSTREAM_ID" not in worker
assert re.search(r'"task_id":\s*"<sprint>\.<index>"', worker)
assert re.search(r'"workstream":\s*', worker)
assert re.search(r'"depends_on":\s*\["<sprint>\.<index>"\]', worker)
assert re.search(r'"blocks":\s*\["<sprint>\.<index>"\]', worker)

# Separate worker outputs: a worker records prior IDs only in depends_on.
worker_sprints = {
    1: [
        {"task_id": "1.1", "workstream": "backend", "depends_on": [],
         "blocks": ["1.3", "1.4", "1.5", "1.6", "1.7"]},
        {"task_id": "1.2", "workstream": "frontend", "depends_on": [],
         "blocks": []},
        {"task_id": "1.3", "workstream": "backend", "depends_on": ["1.1"],
         "blocks": []},
        {"task_id": "1.4", "workstream": "backend", "depends_on": ["1.1"],
         "blocks": []},
        {"task_id": "1.5", "workstream": "frontend", "depends_on": ["1.1"],
         "blocks": []},
        {"task_id": "1.6", "workstream": "frontend", "depends_on": ["1.1"],
         "blocks": []},
        {"task_id": "1.7", "workstream": "frontend", "depends_on": ["1.1"],
         "blocks": []},
    ],
    2: [
        {"task_id": "2.1", "workstream": "frontend", "depends_on": ["1.2"],
         "blocks": []},
    ],
}


def build_tasks(worker_sprints):
    records = [record for sprint_records in worker_sprints.values()
               for record in sprint_records]
    task_ids = [record["task_id"] for record in records]
    assert len(task_ids) == len(set(task_ids)), task_ids
    tasks = {record["task_id"]: record for record in records}
    assert len(task_ids) == len(tasks)
    return tasks


tasks = build_tasks(worker_sprints)
task_ids = list(tasks)
assert len(task_ids) == len(set(task_ids)) == len(tasks)
assert all(re.fullmatch(r"[0-9]+\.[0-9]+", task_id) for task_id in task_ids)
for sprint, sprint_records in worker_sprints.items():
    sprint_task_ids = [record["task_id"] for record in sprint_records]
    indices = [task_id.split(".")[1] for task_id in sprint_task_ids]
    assert len(indices) == len(set(indices))
    assert all(task_id.split(".")[0] == str(sprint) for task_id in sprint_task_ids)
assert {record["workstream"] for record in worker_sprints[1]} == {"backend", "frontend"}

# Duplicate canonical IDs across workstreams must fail before lookup construction.
duplicate_worker_sprints = {
    sprint: list(records) for sprint, records in worker_sprints.items()
}
duplicate_worker_sprints[1].append(
    {**worker_sprints[1][0], "workstream": "frontend"}
)
assert_rejects(build_tasks, duplicate_worker_sprints)

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
