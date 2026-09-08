#!/usr/bin/env python3
"""Behavioral tests for fleet_status.py against a fake `herdr` CLI.

fleet_status.py is the skill's monitoring surface: one `herdr api snapshot` call
renders the whole fleet. These tests pin the properties that make it usable as
a report — attention ordering, scope filtering, fail-closed status reading, and
the blocked exit code — rather than the exact table formatting.

Run directly (stdlib unittest only):
    python3 -m unittest discover -s skills/herdr-agent/tests -p 'test_*.py'
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
FAKE_BIN = HERE / "bin"
FLEET_STATUS = SCRIPTS / "fleet_status.py"


class FakeHerdrHarness:
    def __init__(self):
        self.tmpdir = tempfile.mkdtemp(prefix="hac_status_test_")
        self.state_path = os.path.join(self.tmpdir, "state.json")
        self.write_state({"panes": {}})
        self.env = dict(os.environ)
        self.env["FAKE_HERDR_STATE"] = self.state_path
        self.env["PATH"] = f"{FAKE_BIN}{os.pathsep}{self.env.get('PATH', '')}"

    def write_state(self, state):
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(state, f)

    def read_state(self):
        with open(self.state_path, encoding="utf-8") as f:
            return json.load(f)

    def set_pane(self, pane_id, status, name=None, tab_id="w1:t1",
                 no_agent=False, title=None, tokens=None):
        state = self.read_state()
        state["panes"][pane_id] = {
            "agent_status": status,
            "text": "",
            "name": name,
            "tab_id": tab_id,
            "no_agent": no_agent,
            "title": title,
            "tokens": tokens or {},
        }
        self.write_state(state)

    def run(self, *args):
        return subprocess.run(
            [sys.executable, str(FLEET_STATUS), *args],
            env=self.env,
            text=True,
            capture_output=True,
            timeout=15,
        )

    def run_json(self, *args):
        res = self.run("--json", *args)
        assert res.returncode in (0, 3), res.stderr
        return json.loads(res.stdout), res


class FleetStatusTests(unittest.TestCase):
    def setUp(self):
        self.h = FakeHerdrHarness()

    def test_reports_every_agent_with_status(self):
        self.h.set_pane("w1:p1", "idle", name="reviewer")
        self.h.set_pane("w1:p2", "working", name="tests")
        data, res = self.h.run_json()
        self.assertEqual(res.returncode, 0)
        by_name = {a["name"]: a["status"] for a in data["agents"]}
        self.assertEqual(by_name, {"reviewer": "idle", "tests": "working"})

    def test_blocked_agents_sort_first(self):
        """A human reading the report must see what needs them at the top."""
        self.h.set_pane("w1:p1", "idle", name="reviewer")
        self.h.set_pane("w1:p2", "working", name="tests")
        self.h.set_pane("w1:p3", "blocked", name="docs")
        data, _ = self.h.run_json()
        self.assertEqual(data["agents"][0]["name"], "docs")

    def test_fail_on_blocked_exits_3(self):
        self.h.set_pane("w1:p1", "blocked", name="docs")
        res = self.h.run("--fail-on-blocked")
        self.assertEqual(res.returncode, 3)
        self.assertIn("ATTENTION", res.stdout)

    def test_fail_on_blocked_is_opt_in(self):
        self.h.set_pane("w1:p1", "blocked", name="docs")
        self.assertEqual(self.h.run().returncode, 0)

    def test_tab_scope_filters(self):
        self.h.set_pane("w1:p1", "idle", name="reviewer", tab_id="w1:t1")
        self.h.set_pane("w2:p1", "idle", name="other", tab_id="w2:t1")
        data, _ = self.h.run_json("--tab", "w1:t1")
        self.assertEqual([a["name"] for a in data["agents"]], ["reviewer"])

    def test_agentless_panes_are_hidden_unless_requested(self):
        self.h.set_pane("w1:p1", "idle", name="reviewer")
        self.h.set_pane("w1:p9", "unknown", no_agent=True)
        without, _ = self.h.run_json()
        self.assertEqual(len(without["agents"]), 1)
        with_panes, _ = self.h.run_json("--panes")
        self.assertEqual(len(with_panes["agents"]), 2)

    def test_off_enum_status_reads_as_unknown_not_a_crash(self):
        self.h.set_pane("w1:p1", 42, name="reviewer")
        data, _ = self.h.run_json()
        self.assertEqual(data["agents"][0]["status"], "unknown")

    def test_badges_are_surfaced(self):
        self.h.set_pane("w1:p1", "idle", name="reviewer",
                        title="Review PR 412", tokens={"role": "review"})
        res = self.h.run()
        self.assertIn("Review PR 412", res.stdout)
        self.assertIn("role=review", res.stdout)

    def test_empty_fleet_is_not_an_error(self):
        res = self.h.run("--tab", "w9:t9")
        self.assertEqual(res.returncode, 0)
        self.assertIn("no agents match", res.stdout)


if __name__ == "__main__":
    unittest.main()
