#!/usr/bin/env python3
"""Behavioral tests for preflight_send.py against a fake `herdr` CLI.

preflight_send.py guards the one thing the server does not: `herdr agent prompt`
refuses a `blocked` target itself, but happily accepts a `working` one, and its
wait tracks lifecycle state rather than one turn. Each rejection reason gets a
distinct exit code so a caller can branch on it.

Run directly (stdlib unittest only):
    python3 -m unittest discover -s skills/herdr-agent-comms/tests -p 'test_*.py'
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
PREFLIGHT = SCRIPTS / "preflight_send.py"


class FakeHerdrHarness:
    def __init__(self):
        self.tmpdir = tempfile.mkdtemp(prefix="hac_preflight_test_")
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

    def set_pane(self, pane_id, status, name=None, no_agent=False):
        state = self.read_state()
        state["panes"][pane_id] = {
            "agent_status": status,
            "text": "",
            "name": name,
            "no_agent": no_agent,
        }
        self.write_state(state)

    def run_preflight(self, target, timeout=8):
        return subprocess.run(
            [sys.executable, str(PREFLIGHT), target],
            env=self.env,
            text=True,
            capture_output=True,
            timeout=timeout,
        )


class PreflightSendTests(unittest.TestCase):
    def setUp(self):
        self.h = FakeHerdrHarness()

    def test_sendable_statuses_exit_zero(self):
        for status in ("idle", "done", "unknown"):
            with self.subTest(status=status):
                self.h.set_pane("w1:p1", status, name="reviewer")
                res = self.h.run_preflight("reviewer")
                self.assertEqual(res.returncode, 0, res.stderr)
                self.assertEqual(res.stdout.strip(), status)

    def test_working_is_refused_with_code_2(self):
        """The server does NOT refuse this; the skill must."""
        self.h.set_pane("w1:p1", "working", name="reviewer")
        res = self.h.run_preflight("reviewer")
        self.assertEqual(res.returncode, 2)
        self.assertIn("working", res.stderr)
        self.assertEqual(res.stdout.strip(), "")

    def test_blocked_is_refused_with_code_3(self):
        self.h.set_pane("w1:p1", "blocked", name="reviewer")
        res = self.h.run_preflight("reviewer")
        self.assertEqual(res.returncode, 3)
        self.assertIn("blocked", res.stderr)

    def test_off_enum_status_is_unverifiable_not_safe(self):
        self.h.set_pane("w1:p1", 123, name="reviewer")
        res = self.h.run_preflight("reviewer")
        self.assertEqual(res.returncode, 4)
        self.assertEqual(res.stdout.strip(), "")

    def test_pane_without_detected_agent_reports_code_5(self):
        """agent_not_found is a routing signal, not a generic failure."""
        self.h.set_pane("w1:p9", "unknown", no_agent=True)
        res = self.h.run_preflight("w1:p9")
        self.assertEqual(res.returncode, 5)
        self.assertIn("no detected agent", res.stderr)

    def test_unknown_target_reports_code_5(self):
        res = self.h.run_preflight("ghost")
        self.assertEqual(res.returncode, 5)

    def test_resolves_by_pane_id_too(self):
        self.h.set_pane("w1:p1", "idle", name="reviewer")
        res = self.h.run_preflight("w1:p1")
        self.assertEqual(res.returncode, 0, res.stderr)

    def test_usage_error_without_target(self):
        res = subprocess.run(
            [sys.executable, str(PREFLIGHT)],
            env=self.h.env,
            text=True,
            capture_output=True,
        )
        self.assertEqual(res.returncode, 1)
        self.assertIn("usage", res.stderr)


if __name__ == "__main__":
    unittest.main()
