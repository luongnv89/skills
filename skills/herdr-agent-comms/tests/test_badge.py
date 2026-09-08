#!/usr/bin/env python3
"""Behavioral tests for badge.py against a fake `herdr` CLI.

badge.py exists because `herdr pane report-metadata` takes a pane id while fleet
bookkeeping runs on agent names. These tests cover that resolution, the state
label validation Herdr would otherwise reject server-side, and the refusal to
send an empty report.

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
BADGE = SCRIPTS / "badge.py"


class FakeHerdrHarness:
    def __init__(self):
        self.tmpdir = tempfile.mkdtemp(prefix="hac_badge_test_")
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

    def set_pane(self, pane_id, status="idle", name=None, fail_metadata=False):
        state = self.read_state()
        state["panes"][pane_id] = {
            "agent_status": status,
            "text": "",
            "name": name,
            "fail_metadata": fail_metadata,
        }
        self.write_state(state)

    def run(self, *args):
        return subprocess.run(
            [sys.executable, str(BADGE), *args],
            env=self.env,
            text=True,
            capture_output=True,
            timeout=15,
        )


class BadgeTests(unittest.TestCase):
    def setUp(self):
        self.h = FakeHerdrHarness()

    def test_resolves_an_agent_name_to_its_pane(self):
        self.h.set_pane("w1:p1", name="reviewer")
        res = self.h.run("reviewer", "--title", "Review PR 412")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(res.stdout.strip(), "w1:p1")
        self.assertEqual(self.h.read_state()["panes"]["w1:p1"]["title"], "Review PR 412")

    def test_accepts_a_pane_id_directly(self):
        self.h.set_pane("w1:p1", name="reviewer")
        res = self.h.run("w1:p1", "--token", "role=review")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(
            self.h.read_state()["panes"]["w1:p1"]["tokens"]["role"], "review"
        )

    def test_multiple_tokens_are_all_forwarded(self):
        self.h.set_pane("w1:p1", name="reviewer")
        res = self.h.run("reviewer", "--token", "role=review", "--token", "phase=working")
        self.assertEqual(res.returncode, 0, res.stderr)
        tokens = self.h.read_state()["panes"]["w1:p1"]["tokens"]
        self.assertEqual(tokens, {"role": "review", "phase": "working"})

    def test_unknown_target_fails_without_calling_herdr(self):
        res = self.h.run("ghost", "--title", "x")
        self.assertEqual(res.returncode, 1)
        self.assertIn("resolves to no pane or agent", res.stderr)

    def test_empty_report_is_refused(self):
        self.h.set_pane("w1:p1", name="reviewer")
        res = self.h.run("reviewer")
        self.assertEqual(res.returncode, 1)
        self.assertIn("nothing to report", res.stderr)

    def test_invalid_state_label_key_is_rejected_locally(self):
        """Herdr accepts only the five lifecycle keys; fail before the call."""
        self.h.set_pane("w1:p1", name="reviewer")
        res = self.h.run("reviewer", "--state-label", "busy=nope")
        self.assertEqual(res.returncode, 1)
        self.assertIn("must be one of", res.stderr)

    def test_malformed_token_is_rejected(self):
        self.h.set_pane("w1:p1", name="reviewer")
        res = self.h.run("reviewer", "--token", "novalue")
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("NAME=VALUE", res.stderr)

    def test_server_rejection_exits_2(self):
        self.h.set_pane("w1:p1", name="reviewer", fail_metadata=True)
        res = self.h.run("reviewer", "--title", "x")
        self.assertEqual(res.returncode, 2)
        self.assertIn("report-metadata failed", res.stderr)


if __name__ == "__main__":
    unittest.main()
