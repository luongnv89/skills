#!/usr/bin/env python3
"""Behavioral tests for broadcast.sh against a fake `herdr` CLI.

broadcast.sh dispatches `herdr agent prompt --wait` to every safe target
concurrently. What these tests pin down is the behavior around that call: which
targets it refuses, which it dedupes, how it maps Herdr's error codes, and that
a refused or failed target is always reported rather than silently dropped.

Run directly (stdlib unittest only):
    python3 -m unittest discover -s skills/herdr-agent/tests -p 'test_*.py'
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
FAKE_BIN = HERE / "bin"
BROADCAST = SCRIPTS / "broadcast.sh"


class FakeHerdrHarness:
    def __init__(self):
        self.tmpdir = tempfile.mkdtemp(prefix="hac_bcast_test_")
        self.state_path = os.path.join(self.tmpdir, "state.json")
        self.write_state({"panes": {}})
        self.env = dict(os.environ)
        self.env["FAKE_HERDR_STATE"] = self.state_path
        self.env["PATH"] = f"{FAKE_BIN}{os.pathsep}{self.env.get('PATH', '')}"
        # Keep tests fast and quiet: no reply dumps, short waits.
        self.env["HAC_LINES"] = "0"
        self.env["HAC_TIMEOUT"] = "5"

    def write_state(self, state):
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(state, f)

    def read_state(self):
        with open(self.state_path, encoding="utf-8") as f:
            return json.load(f)

    def set_pane(self, pane_id, status, name=None, fail_prompt=None,
                 no_agent=False, status_after=None, status_flip_to=None):
        state = self.read_state()
        state["panes"][pane_id] = {
            "agent_status": status,
            "text": "",
            "name": name,
            "fail_prompt": fail_prompt,
            "no_agent": no_agent,
            "status_after": status_after,
            "status_flip_to": status_flip_to,
        }
        self.write_state(state)

    def run(self, message, *targets, timeout=40, **env):
        env_all = dict(self.env)
        env_all.update(env)
        return subprocess.run(
            ["bash", str(BROADCAST), message, *targets],
            env=env_all,
            text=True,
            capture_output=True,
            timeout=timeout,
        )


class BroadcastTests(unittest.TestCase):
    def setUp(self):
        self.h = FakeHerdrHarness()

    def test_dispatches_to_every_safe_target(self):
        self.h.set_pane("w1:p1", "idle", name="reviewer")
        self.h.set_pane("w1:p2", "done", name="tests")
        res = self.h.run("do the thing", "reviewer", "tests")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("reviewer (w1:p1): settled", res.stdout)
        self.assertIn("tests (w1:p2): settled", res.stdout)
        self.assertIn("2 dispatched, 0 skipped", res.stdout)

    def test_name_and_pane_alias_send_once(self):
        self.h.set_pane("w1:p1", "idle", name="reviewer")
        res = self.h.run("hello", "reviewer", "w1:p1")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("skipping duplicate", res.stderr)
        self.assertEqual(self.h.read_state()["panes"]["w1:p1"]["text"].count("hello"), 1)

    def test_working_target_is_skipped_not_prompted(self):
        self.h.set_pane("w1:p1", "working", name="busy")
        res = self.h.run("hello", "busy")
        self.assertEqual(res.returncode, 1)
        self.assertIn("working", res.stderr)
        self.assertNotIn("hello", self.h.read_state()["panes"]["w1:p1"]["text"])

    def test_blocked_target_is_skipped_not_prompted(self):
        self.h.set_pane("w1:p1", "blocked", name="stuck")
        res = self.h.run("hello", "stuck")
        self.assertEqual(res.returncode, 1)
        self.assertIn("blocked", res.stderr)
        self.assertNotIn("hello", self.h.read_state()["panes"]["w1:p1"]["text"])

    def test_one_unsafe_target_does_not_block_the_others(self):
        self.h.set_pane("w1:p1", "idle", name="reviewer")
        self.h.set_pane("w1:p2", "working", name="busy")
        res = self.h.run("hello", "reviewer", "busy")
        self.assertEqual(res.returncode, 1)
        self.assertIn("reviewer (w1:p1): settled", res.stdout)
        self.assertIn("busy: working", res.stderr)
        self.assertIn("1 dispatched, 1 skipped", res.stdout)

    def test_unresolvable_target_is_fatal_before_any_send(self):
        """Silently shrinking a fleet hides work that never ran."""
        self.h.set_pane("w1:p1", "idle", name="reviewer")
        res = self.h.run("hello", "reviewer", "ghost")
        self.assertEqual(res.returncode, 1)
        self.assertIn("ghost", res.stderr)
        self.assertNotIn("hello", self.h.read_state()["panes"]["w1:p1"]["text"])

    def test_pane_without_detected_agent_does_not_resolve(self):
        self.h.set_pane("w1:p9", "unknown", no_agent=True)
        res = self.h.run("hello", "w1:p9")
        self.assertEqual(res.returncode, 1)
        self.assertIn("no detected agent", res.stderr)

    def test_target_that_turns_working_after_the_roster_read_is_skipped(self):
        """The roster is read once at T0; resolving and badging take real time.

        Herdr refuses a target that turned `blocked` in that window, but not one
        that turned `working` — and a prompt into a working agent can be settled
        by the turn already in flight, so the reply read back is the wrong one.
        """
        self.h.set_pane("w1:p1", "idle", name="reviewer",
                        status_after=0, status_flip_to="working")
        res = self.h.run("hello", "reviewer")
        self.assertEqual(res.returncode, 1)
        self.assertIn("became unsafe before dispatch", res.stderr)
        self.assertIn("0 dispatched, 1 skipped", res.stdout)
        self.assertNotIn("hello", self.h.read_state()["panes"]["w1:p1"]["text"])

    def test_other_targets_still_dispatch_when_one_races(self):
        self.h.set_pane("w1:p1", "idle", name="reviewer")
        self.h.set_pane("w1:p2", "idle", name="racer",
                        status_after=0, status_flip_to="blocked")
        res = self.h.run("hello", "reviewer", "racer")
        self.assertEqual(res.returncode, 1)
        self.assertIn("reviewer (w1:p1): settled", res.stdout)
        self.assertIn("1 dispatched, 1 skipped", res.stdout)

    def test_error_codes_map_to_reasons(self):
        for code, expected in (
            ("agent_prompt_stalled", "STALLED"),
            ("timeout", "TIMEOUT"),
            ("agent_not_found", "GONE"),
        ):
            with self.subTest(code=code):
                h = FakeHerdrHarness()
                h.set_pane("w1:p1", "idle", name="reviewer", fail_prompt=code)
                res = h.run("hello", "reviewer")
                self.assertEqual(res.returncode, 1)
                self.assertIn(expected, res.stderr)

    def test_badging_is_opt_in(self):
        self.h.set_pane("w1:p1", "idle", name="reviewer")
        res = self.h.run("hello", "reviewer", HAC_BADGE="1")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(
            self.h.read_state()["panes"]["w1:p1"].get("tokens", {}).get("phase"),
            "done",
        )

    def test_no_badges_without_the_flag(self):
        self.h.set_pane("w1:p1", "idle", name="reviewer")
        self.h.run("hello", "reviewer")
        self.assertEqual(self.h.read_state()["panes"]["w1:p1"].get("tokens", {}), {})

    def test_usage_error_without_targets(self):
        res = subprocess.run(
            ["bash", str(BROADCAST), "only a message"],
            env=self.h.env,
            text=True,
            capture_output=True,
        )
        self.assertEqual(res.returncode, 1)
        self.assertIn("at least one target", res.stderr)


if __name__ == "__main__":
    unittest.main()
