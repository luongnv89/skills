"""Stdlib fixtures for the deterministic tasks-generator graph helper.

Run directly from the repository root::

    python3 -m unittest discover -s skills/tasks-generator/tests -p 'test_*.py'

The CLI tests deliberately use subprocess only to exercise the executable
boundary.  The calculator itself has no subprocess, network, eval, git, or
report-writing dependency.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "analyze_dependencies.py"
sys.path.insert(0, str(SCRIPT.parent))

import analyze_dependencies as graph  # noqa: E402


def _sprint(task_id: str) -> int:
    return int(task_id.split(".", 1)[0])


def payload_from_deps(
    dependencies: dict[str, list[str]],
    efforts: dict[str, str] | None = None,
) -> dict:
    """Build full-ish worker records and derive same-sprint blocks."""
    efforts = efforts or {}
    blocks: dict[str, list[str]] = {task_id: [] for task_id in dependencies}
    for child, parents in dependencies.items():
        for parent in parents:
            if parent in blocks and _sprint(parent) == _sprint(child):
                blocks[parent].append(child)
    records = []
    for task_id, parents in dependencies.items():
        records.append(
            {
                "task_id": task_id,
                "title": task_id,
                "description": "fixture",
                "effort_estimate": efforts.get(task_id, "1d"),
                "depends_on": list(parents),
                "blocks": list(blocks[task_id]),
                "workstream": "fixture",
            }
        )
    # The helper sorts by parsed numeric IDs, not by input order.  Keep the
    # fixture's blocks valid while avoiding string ordering surprises.
    for record in records:
        record["blocks"] = sorted(
            record["blocks"], key=lambda value: tuple(int(part) for part in value.split("."))
        )
    return {"tasks": records}


def mutate_task(payload: dict, task_id: str, **changes) -> dict:
    clone = json.loads(json.dumps(payload))
    record = next(task for task in clone["tasks"] if task["task_id"] == task_id)
    record.update(changes)
    return clone


class GraphMetricsTests(unittest.TestCase):
    def test_empty_graph_has_explicit_zero_result(self):
        result = graph.analyze_graph({"tasks": []})
        self.assertEqual(
            result,
            {
                "schema_version": 1,
                "status": "ok",
                "task_count": 0,
                "edge_count": 0,
                "critical_path": {"task_ids": [], "effort_days": 0},
                "bottlenecks": [],
                "cycles": [],
            },
        )

    def test_single_node_path(self):
        result = graph.analyze_graph(payload_from_deps({"1.1": []}, {"1.1": "3d"}))
        self.assertEqual(result["critical_path"], {"task_ids": ["1.1"], "effort_days": 3})

    def test_disconnected_graph_selects_heaviest_component(self):
        result = graph.analyze_graph(
            payload_from_deps(
                {"1.1": [], "1.2": [], "2.1": ["2.2"], "2.2": []},
                {"1.1": "1d", "1.2": "3d", "2.1": "2d", "2.2": "2d"},
            )
        )
        self.assertEqual(result["critical_path"], {"task_ids": ["2.2", "2.1"], "effort_days": 4})

    def test_diamond_tie_uses_numeric_complete_path(self):
        result = graph.analyze_graph(
            payload_from_deps(
                {"1.1": [], "1.2": ["1.1"], "1.3": ["1.1"], "1.4": ["1.2", "1.3"]},
                {"1.1": "1d", "1.2": "2d", "1.3": "2d", "1.4": "1d"},
            )
        )
        self.assertEqual(result["critical_path"], {"task_ids": ["1.1", "1.2", "1.4"], "effort_days": 4})

    def test_equal_tie_orders_two_before_ten_numerically(self):
        result = graph.analyze_graph(
            payload_from_deps(
                {"1.1": [], "1.2": ["1.1"], "1.10": ["1.1"], "1.20": ["1.2", "1.10"]},
                {task_id: "1d" for task_id in ("1.1", "1.2", "1.10", "1.20")},
            )
        )
        self.assertEqual(result["critical_path"]["task_ids"], ["1.1", "1.2", "1.20"])

    def test_cross_sprint_dependency_is_valid_and_blocks_are_derived(self):
        result = graph.analyze_graph(payload_from_deps({"1.1": [], "2.1": ["1.1"]}))
        self.assertEqual(result["edge_count"], 1)
        self.assertEqual(result["critical_path"]["task_ids"], ["1.1", "2.1"])

    def test_four_direct_dependents_is_not_a_bottleneck(self):
        deps = {"1.1": []}
        deps.update({f"1.{index}": ["1.1"] for index in range(2, 6)})
        result = graph.analyze_graph(payload_from_deps(deps))
        self.assertEqual(result["bottlenecks"], [])

    def test_five_direct_dependents_is_a_bottleneck(self):
        deps = {"1.1": []}
        deps.update({f"1.{index}": ["1.1"] for index in range(2, 7)})
        result = graph.analyze_graph(payload_from_deps(deps))
        self.assertEqual(result["bottlenecks"], [{"task_id": "1.1", "direct_dependents": 5}])

    def test_rootless_cycle_reports_only_actual_cycle_not_downstream_residue(self):
        payload = payload_from_deps(
            {"1.1": ["1.2"], "1.2": ["1.1"], "1.3": ["1.2"]}
        )
        with self.assertRaises(graph.InputError) as raised:
            graph.analyze_graph(payload)
        self.assertEqual(str(raised.exception), "directed cycle: 1.1 -> 1.2 -> 1.1")
        self.assertNotIn("1.3", str(raised.exception))


class GraphValidationTests(unittest.TestCase):
    def assertInvalid(self, payload: dict, contains: str | None = None):
        with self.assertRaises(graph.InputError) as raised:
            graph.analyze_graph(payload)
        if contains:
            self.assertIn(contains, str(raised.exception))

    def test_duplicate_task_ids(self):
        payload = payload_from_deps({"1.1": []})
        payload["tasks"].append(dict(payload["tasks"][0]))
        self.assertInvalid(payload, "duplicate task ID")

    def test_duplicate_dependency_edge(self):
        payload = payload_from_deps({"1.1": [], "1.2": ["1.1"]})
        payload = mutate_task(payload, "1.2", depends_on=["1.1", "1.1"])
        self.assertInvalid(payload, "duplicate edge")

    def test_duplicate_blocks_edge(self):
        payload = payload_from_deps({"1.1": [], "1.2": ["1.1"]})
        payload = mutate_task(payload, "1.1", blocks=["1.2", "1.2"])
        self.assertInvalid(payload, "duplicate edge")

    def test_unknown_dependency_endpoint(self):
        payload = payload_from_deps({"1.1": [], "1.2": ["1.1"]})
        payload = mutate_task(payload, "1.2", depends_on=["1.9"])
        self.assertInvalid(payload, "unknown dependency endpoint")

    def test_unknown_blocks_endpoint(self):
        payload = payload_from_deps({"1.1": [], "1.2": ["1.1"]})
        payload = mutate_task(payload, "1.1", blocks=["1.9"])
        self.assertInvalid(payload, "unknown blocks endpoint")

    def test_self_loop(self):
        payload = payload_from_deps({"1.1": []})
        payload = mutate_task(payload, "1.1", depends_on=["1.1"], blocks=["1.1"])
        self.assertInvalid(payload, "self-loop")

    def test_future_sprint_dependency(self):
        payload = payload_from_deps({"1.1": [], "2.1": ["3.1"], "3.1": []})
        self.assertInvalid(payload, "future-sprint dependency")

    def test_cross_sprint_blocks_are_not_worker_input(self):
        payload = payload_from_deps({"1.1": [], "2.1": ["1.1"]})
        payload = mutate_task(payload, "1.1", blocks=["2.1"])
        self.assertInvalid(payload, "same-sprint only")

    def test_inconsistent_same_sprint_blocks_are_rejected(self):
        payload = payload_from_deps({"1.1": [], "1.2": ["1.1"]})
        payload = mutate_task(payload, "1.1", blocks=[])
        self.assertInvalid(payload, "derived same-sprint inverse")

    def test_malformed_ids_are_rejected(self):
        for malformed in ("1", "1.0", "0.1", "01.1", "1.01", "1.2.3", 1.2, True):
            with self.subTest(malformed=malformed):
                payload = payload_from_deps({"1.1": []})
                payload["tasks"][0]["task_id"] = malformed
                self.assertInvalid(payload, "task_id")

    def test_effort_estimate_is_strict(self):
        for effort in ("0d", "4d", "1", "1.5d", 1, True, None):
            with self.subTest(effort=effort):
                payload = payload_from_deps({"1.1": []})
                payload["tasks"][0]["effort_estimate"] = effort
                self.assertInvalid(payload, "effort_estimate")

    def test_required_container_types_are_strict(self):
        payload = payload_from_deps({"1.1": []})
        self.assertInvalid({}, "missing required key")
        self.assertInvalid({"tasks": {}}, "tasks must be a list")
        self.assertInvalid({"tasks": [None]}, "must be a JSON object")
        self.assertInvalid({"tasks": [{"task_id": "1.1"}]}, "missing required key")
        self.assertInvalid({"tasks": [], "extra": []}, "unexpected top-level")
        self.assertInvalid(mutate_task(payload, "1.1", depends_on=None), "depends_on must be a list")
        self.assertInvalid(mutate_task(payload, "1.1", blocks=None), "blocks must be a list")

    def test_nonfinite_number_is_rejected_even_before_shape_checks(self):
        payload = {"tasks": [], "note": float("nan")}
        with self.assertRaises(graph.InputError):
            graph.analyze_graph(payload)

    def test_deterministic_result_ignores_input_order(self):
        first = payload_from_deps(
            {"1.1": [], "1.3": ["1.1"], "1.2": ["1.1"], "1.4": ["1.2", "1.3"]}
        )
        second = {"tasks": list(reversed(first["tasks"]))}
        for task in second["tasks"]:
            task["depends_on"] = list(reversed(task["depends_on"]))
            task["blocks"] = list(reversed(task["blocks"]))
        self.assertEqual(graph.analyze_graph(first), graph.analyze_graph(second))


class CliContractTests(unittest.TestCase):
    def run_cli(self, raw: str, *args: str):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            input=raw,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_stdin_success_is_canonical_json(self):
        result = self.run_cli(json.dumps(payload_from_deps({"1.1": []})), "--input", "-")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(json.loads(result.stdout)["status"], "ok")
        self.assertEqual(result.stdout, result.stdout.rstrip() + "\n")

    def test_absolute_file_success(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "graph.json"
            path.write_text(json.dumps(payload_from_deps({"1.1": []})), encoding="utf-8")
            result = self.run_cli("", "--input", str(path))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["task_count"], 1)

    def test_relative_file_path_is_rejected(self):
        result = self.run_cli("{}", "--input", "graph.json")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("absolute", result.stderr)

    def test_malformed_json_has_stable_error_and_no_partial_result(self):
        result = self.run_cli("{", "--input", "-")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr.startswith("error[graph-input]: input is not valid JSON:"))

    def test_nonfinite_json_has_stable_error(self):
        result = self.run_cli('{"tasks": [], "value": NaN}', "--input", "-")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("non-finite JSON number", result.stderr)

    def test_empty_stdin_is_rejected_without_partial_result(self):
        result = self.run_cli("", "--input", "-")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("input is empty", result.stderr)


if __name__ == "__main__":
    unittest.main()
