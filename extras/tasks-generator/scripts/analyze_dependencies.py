#!/usr/bin/env python3
"""Validate a tasks-generator graph and calculate deterministic graph metrics.

The input is a small JSON object with one ``tasks`` list.  The task records may
carry the full sprint-worker schema; this helper reads only the graph fields it
needs.  It writes one canonical JSON result to stdout and never writes files,
executes commands, or produces ``tasks.md``.

Usage::

    python3 analyze_dependencies.py --input /absolute/path/graph.json
    cat graph.json | python3 analyze_dependencies.py --input -

Exit status 0 means the graph is valid and acyclic.  Invalid input and cycles
are reported on stderr with exit status 2; no partial result is written.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import heapq
import json
import math
from pathlib import Path
import re
import sys
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


SCHEMA_VERSION = 1
ID_PATTERN = re.compile(r"^([1-9][0-9]*)\.([1-9][0-9]*)$")
EFFORT_DAYS = {"1d": 1, "2d": 2, "3d": 3}

TaskId = Tuple[int, int]


class InputError(ValueError):
    """An input or graph-contract error suitable for a stable CLI diagnostic."""


@dataclass(frozen=True)
class Task:
    task_id: str
    key: TaskId
    effort_days: int
    depends_on: Tuple[str, ...]
    blocks: Tuple[str, ...]


def _duplicate_key_object(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InputError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise InputError(f"non-finite JSON number is not allowed: {value}")


def _check_finite(value: Any, path: str = "$") -> None:
    """Reject non-finite numbers even when a caller bypasses the JSON loader."""
    if isinstance(value, float) and not math.isfinite(value):
        raise InputError(f"{path} must be finite, got {value!r}")
    if isinstance(value, list):
        for index, child in enumerate(value):
            _check_finite(child, f"{path}[{index}]")
    elif isinstance(value, dict):
        for key, child in value.items():
            _check_finite(child, f"{path}.{key}")


def _read_payload(input_path: str) -> Mapping[str, Any]:
    if input_path == "-":
        raw = sys.stdin.buffer.read()
    else:
        path = Path(input_path)
        if not path.is_absolute():
            raise InputError("--input path must be absolute, or '-' for stdin")
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise InputError(f"cannot read --input file {path}: {exc}") from exc

    if not raw.strip():
        raise InputError("input is empty")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InputError(f"input is not valid UTF-8: {exc}") from exc

    try:
        data = json.loads(
            text,
            object_pairs_hook=_duplicate_key_object,
            parse_constant=_reject_constant,
        )
    except InputError:
        raise
    except json.JSONDecodeError as exc:
        raise InputError(f"input is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise InputError(f"input must be a JSON object, got {type(data).__name__}")
    _check_finite(data)
    return data


def _require_string(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise InputError(f"{label} must be a string, got {type(value).__name__}")
    return value


def _parse_task_id(value: Any, label: str) -> Tuple[str, TaskId]:
    task_id = _require_string(value, label)
    match = ID_PATTERN.fullmatch(task_id)
    if not match:
        raise InputError(
            f"{label} must match '<positive sprint>.<positive index>', got {task_id!r}"
        )
    try:
        key = (int(match.group(1)), int(match.group(2)))
    except ValueError as exc:
        raise InputError(f"{label} numeric components are too large") from exc
    return task_id, key


def _parse_id_list(value: Any, label: str) -> Tuple[str, ...]:
    if not isinstance(value, list):
        raise InputError(f"{label} must be a list, got {type(value).__name__}")
    parsed: List[str] = []
    seen = set()
    for index, item in enumerate(value):
        item_label = f"{label}[{index}]"
        task_id, _ = _parse_task_id(item, item_label)
        if task_id in seen:
            raise InputError(f"duplicate edge in {label}: {task_id}")
        seen.add(task_id)
        parsed.append(task_id)
    return tuple(parsed)


def _validate_tasks(payload: Mapping[str, Any]) -> Dict[str, Task]:
    keys = set(payload)
    if "tasks" not in payload:
        raise InputError("missing required key: tasks")
    extras = sorted(keys - {"tasks"})
    if extras:
        raise InputError(f"unexpected top-level key(s): {', '.join(extras)}")

    raw_tasks = payload["tasks"]
    if not isinstance(raw_tasks, list):
        raise InputError(f"tasks must be a list, got {type(raw_tasks).__name__}")

    tasks: Dict[str, Task] = {}
    for index, raw_task in enumerate(raw_tasks):
        label = f"tasks[{index}]"
        if not isinstance(raw_task, dict):
            raise InputError(f"{label} must be a JSON object, got {type(raw_task).__name__}")
        required = ("task_id", "effort_estimate", "depends_on", "blocks")
        missing = [key for key in required if key not in raw_task]
        if missing:
            raise InputError(f"{label} missing required key(s): {', '.join(missing)}")

        task_id, key = _parse_task_id(raw_task["task_id"], f"{label}.task_id")
        if task_id in tasks:
            raise InputError(f"duplicate task ID: {task_id}")

        effort = raw_task["effort_estimate"]
        if not isinstance(effort, str) or effort not in EFFORT_DAYS:
            raise InputError(
                f"{label}.effort_estimate must be one of 1d, 2d, 3d, got {effort!r}"
            )

        depends_on = _parse_id_list(raw_task["depends_on"], f"{label}.depends_on")
        blocks = _parse_id_list(raw_task["blocks"], f"{label}.blocks")
        tasks[task_id] = Task(
            task_id=task_id,
            key=key,
            effort_days=EFFORT_DAYS[effort],
            depends_on=depends_on,
            blocks=blocks,
        )

    return tasks


def _sorted_ids(ids: Iterable[str], tasks: Mapping[str, Task]) -> List[str]:
    return sorted(ids, key=lambda task_id: tasks[task_id].key)


def _build_graph(
    tasks: Mapping[str, Task],
) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Return dependency->dependent adjacency and its predecessor lists."""
    adjacency: Dict[str, List[str]] = {task_id: [] for task_id in tasks}
    predecessors: Dict[str, List[str]] = {task_id: [] for task_id in tasks}

    for task in tasks.values():
        for dependency in task.depends_on:
            if dependency not in tasks:
                raise InputError(f"unknown dependency endpoint: {task.task_id} depends on {dependency}")
            if dependency == task.task_id:
                raise InputError(f"self-loop is not allowed: {task.task_id}")
            if tasks[dependency].key[0] > task.key[0]:
                raise InputError(
                    f"future-sprint dependency is not allowed: {task.task_id} depends on {dependency}"
                )
            adjacency[dependency].append(task.task_id)
            predecessors[task.task_id].append(dependency)

    # Worker blocks are a same-sprint representation only.  The authoritative
    # edge set is depends_on; compare same-sprint blocks to its derived inverse
    # and reject any cross-sprint block supplied by a worker.
    derived_same_sprint: Dict[str, List[str]] = {task_id: [] for task_id in tasks}
    for dependency, dependents in adjacency.items():
        for dependent in dependents:
            if tasks[dependency].key[0] == tasks[dependent].key[0]:
                derived_same_sprint[dependency].append(dependent)

    for task in tasks.values():
        for blocked in task.blocks:
            if blocked not in tasks:
                raise InputError(f"unknown blocks endpoint: {task.task_id} blocks {blocked}")
            if blocked == task.task_id:
                raise InputError(f"self-loop is not allowed: {task.task_id}")
            if tasks[blocked].key[0] < task.key[0]:
                raise InputError(
                    f"blocks may only point to the same or a later sprint: {task.task_id} blocks {blocked}"
                )
            if tasks[blocked].key[0] != task.key[0]:
                raise InputError(
                    f"worker blocks must be same-sprint only: {task.task_id} blocks {blocked}"
                )

        expected = _sorted_ids(derived_same_sprint[task.task_id], tasks)
        supplied = _sorted_ids(task.blocks, tasks)
        if supplied != expected:
            raise InputError(
                f"blocks must be the derived same-sprint inverse for {task.task_id}: "
                f"expected {expected}, got {supplied}"
            )

    for task_id in tasks:
        adjacency[task_id] = _sorted_ids(adjacency[task_id], tasks)
        predecessors[task_id] = _sorted_ids(predecessors[task_id], tasks)
    return adjacency, predecessors


def _find_cycle(tasks: Mapping[str, Task], adjacency: Mapping[str, Sequence[str]]) -> Optional[List[str]]:
    """Find one deterministic directed cycle, excluding downstream residue."""
    state: Dict[str, int] = {task_id: 0 for task_id in tasks}
    next_index: Dict[str, int] = {}
    active_position: Dict[str, int] = {}
    stack: List[str] = []

    for start in _sorted_ids(tasks, tasks):
        if state[start] != 0:
            continue
        state[start] = 1
        stack.append(start)
        active_position[start] = 0
        next_index[start] = 0

        while stack:
            current = stack[-1]
            children = adjacency[current]
            child_index = next_index[current]
            if child_index >= len(children):
                state[current] = 2
                stack.pop()
                active_position.pop(current, None)
                next_index.pop(current, None)
                continue

            child = children[child_index]
            next_index[current] = child_index + 1
            if state[child] == 0:
                state[child] = 1
                active_position[child] = len(stack)
                next_index[child] = 0
                stack.append(child)
            elif state[child] == 1:
                return stack[active_position[child] :] + [child]
    return None


def _topological_order(
    tasks: Mapping[str, Task], adjacency: Mapping[str, Sequence[str]], predecessors: Mapping[str, Sequence[str]]
) -> List[str]:
    indegree = {task_id: len(predecessors[task_id]) for task_id in tasks}
    ready = [tasks[task_id].key + (task_id,) for task_id, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    order: List[str] = []
    while ready:
        _, _, current = heapq.heappop(ready)
        order.append(current)
        for child in adjacency[current]:
            indegree[child] -= 1
            if indegree[child] == 0:
                key = tasks[child].key
                heapq.heappush(ready, key + (child,))
    if len(order) != len(tasks):
        raise InputError("graph contains a directed cycle")
    return order


def _longest_path(
    tasks: Mapping[str, Task],
    order: Sequence[str],
    predecessors: Mapping[str, Sequence[str]],
) -> Tuple[List[str], int]:
    costs: Dict[str, int] = {}
    paths: Dict[str, Tuple[TaskId, ...]] = {}
    path_ids: Dict[str, Tuple[str, ...]] = {}

    for task_id in order:
        task = tasks[task_id]
        if not predecessors[task_id]:
            costs[task_id] = task.effort_days
            paths[task_id] = (task.key,)
            path_ids[task_id] = (task_id,)
            continue

        candidates = []
        for dependency in predecessors[task_id]:
            candidates.append(
                (
                    costs[dependency] + task.effort_days,
                    paths[dependency] + (task.key,),
                    path_ids[dependency] + (task_id,),
                )
            )
        best_cost = max(candidate[0] for candidate in candidates)
        # The cost is maximized, while a complete numeric path tie is resolved
        # by its lexicographically smallest tuple sequence.
        tied = [candidate for candidate in candidates if candidate[0] == best_cost]
        best_cost, best_path, best_ids = min(tied, key=lambda candidate: candidate[1])
        costs[task_id] = best_cost
        paths[task_id] = best_path
        path_ids[task_id] = best_ids

    if not tasks:
        return [], 0
    terminal_candidates = [
        (costs[task_id], paths[task_id], path_ids[task_id]) for task_id in tasks
    ]
    max_cost = max(candidate[0] for candidate in terminal_candidates)
    best = min((candidate for candidate in terminal_candidates if candidate[0] == max_cost), key=lambda candidate: candidate[1])
    return list(best[2]), best[0]


def analyze_graph(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate ``payload`` and return the stable success result."""
    if not isinstance(payload, dict):
        raise InputError(f"input must be a JSON object, got {type(payload).__name__}")
    _check_finite(payload)
    tasks = _validate_tasks(payload)
    adjacency, predecessors = _build_graph(tasks)
    cycle = _find_cycle(tasks, adjacency)
    if cycle:
        rendered = " -> ".join(cycle)
        raise InputError(f"directed cycle: {rendered}")

    order = _topological_order(tasks, adjacency, predecessors)
    critical_ids, critical_days = _longest_path(tasks, order, predecessors)
    bottlenecks = [
        {"task_id": task_id, "direct_dependents": len(adjacency[task_id])}
        for task_id in _sorted_ids(tasks, tasks)
        if len(adjacency[task_id]) >= 5
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "ok",
        "task_count": len(tasks),
        "edge_count": sum(len(children) for children in adjacency.values()),
        "critical_path": {
            "task_ids": critical_ids,
            "effort_days": critical_days,
        },
        "bottlenecks": bottlenecks,
        "cycles": [],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a tasks-generator graph and calculate deterministic metrics."
    )
    parser.add_argument(
        "--input",
        default="-",
        metavar="PATH|-",
        help="absolute JSON file path, or '-' for stdin (default: stdin)",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        payload = _read_payload(args.input)
        result = analyze_graph(payload)
    except InputError as exc:
        print(f"error[graph-input]: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover - last-resort no-traceback contract
        print(f"error[internal]: {exc}", file=sys.stderr)
        return 2

    json.dump(result, sys.stdout, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
