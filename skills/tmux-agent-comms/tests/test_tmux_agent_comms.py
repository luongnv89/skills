#!/usr/bin/env python3
"""Tests for the tmux-agent-comms scripts, run against the fake `tmux` CLI in tests/bin.

One section per script; each section's comment block says what it covers.

Run directly (stdlib unittest only, no live tmux needed):
    python3 -m unittest discover -s skills/tmux-agent-comms/tests -p 'test_*.py'
"""


from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
FAKE_BIN = HERE / "bin"


# ============================================================================
# broadcast
# Behavioral tests for broadcast.sh against a fake `tmux` CLI.
#
# Run:
#     python3 -m unittest discover -s skills/tmux-agent-comms/tests -p 'test_*.py'
# ============================================================================

BROADCAST = SCRIPTS / "broadcast.sh"


class BroadcastFakeTmuxHarness:
    def __init__(self):
        self.tmpdir = tempfile.mkdtemp(prefix="tac_bcast_")
        self.state_path = os.path.join(self.tmpdir, "state.json")
        self.write_state({"sessions": {}})
        self.env = dict(os.environ)
        self.env["FAKE_TMUX_STATE"] = self.state_path
        self.env["PATH"] = f"{FAKE_BIN}{os.pathsep}{self.env.get('PATH', '')}"
        self.env["TAC_TIMEOUT"] = "3"
        # Keep waiter snappy under test.
        self.env["TAC_WAIT_ARGS"] = "--interval 0.1 --quiet-cycles 2"

    def write_state(self, state):
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(state, f)

    def read_state(self):
        with open(self.state_path, encoding="utf-8") as f:
            return json.load(f)

    def set_session(self, name, text, fail_capture=False, fail_send=False):
        state = self.read_state()
        state["sessions"][name] = {
            "text": text,
            "fail_capture": fail_capture,
            "fail_send": fail_send,
        }
        self.write_state(state)

    def set_text(self, name, text):
        state = self.read_state()
        state["sessions"][name]["text"] = text
        self.write_state(state)

    def run_broadcast(self, msg, *sessions, timeout=20):
        cmd = ["bash", str(BROADCAST), msg, *sessions]
        return subprocess.run(
            cmd, env=self.env, text=True, capture_output=True, timeout=timeout
        )


class BroadcastTests(unittest.TestCase):
    def setUp(self):
        self.h = BroadcastFakeTmuxHarness()

    def test_missing_session_fails_early(self):
        self.h.set_session("a", "idle\n")
        cp = self.h.run_broadcast("hi", "a", "missing")
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("don't exist", cp.stderr)

    def test_skips_blocked_and_fails(self):
        self.h.set_session("ok", "ready>\n")
        self.h.set_session("bad", "Do you trust the files in this folder?\n")
        # ok will get a send; complete it with the marker the send injects.
        def complete():
            # Poll until send appends task text, then inject joined marker.
            for _ in range(40):
                text = self.h.read_state()["sessions"]["ok"]["text"]
                m = re.search(r"TAC_DONE_ and (\S+)", text)
                if m:
                    joined = f"TAC_DONE_{m.group(1)}"
                    self.h.set_text("ok", text + f"\nreply\n{joined}\n")
                    return
                time.sleep(0.05)

        threading.Thread(target=complete, daemon=True).start()
        cp = self.h.run_broadcast("do work", "ok", "bad")
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("blocked", cp.stderr.lower())
        self.assertIn("ok", cp.stdout)

    def test_skips_working(self):
        self.h.set_session("busy", "working\nesc to interrupt\n")
        cp = self.h.run_broadcast("hi", "busy")
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("working", cp.stderr.lower())

    def test_success_with_marker(self):
        self.h.set_session("r1", "ready>\n")
        self.h.set_session("r2", "ready>\n")

        def complete_all():
            done = set()
            for _ in range(80):
                state = self.h.read_state()
                for name in ("r1", "r2"):
                    if name in done:
                        continue
                    text = state["sessions"][name]["text"]
                    m = re.search(r"TAC_DONE_ and (\S+)", text)
                    if m:
                        joined = f"TAC_DONE_{m.group(1)}"
                        self.h.set_text(name, text + f"\nok from {name}\n{joined}\n")
                        done.add(name)
                if len(done) == 2:
                    return
                time.sleep(0.05)

        threading.Thread(target=complete_all, daemon=True).start()
        cp = self.h.run_broadcast("pull main", "r1", "r2")
        self.assertEqual(cp.returncode, 0, msg=f"stdout={cp.stdout}\nstderr={cp.stderr}")
        self.assertIn("r1", cp.stdout)
        self.assertIn("r2", cp.stdout)

    def test_dedupes_targets(self):
        self.h.set_session("only", "ready>\n")

        def complete():
            for _ in range(40):
                text = self.h.read_state()["sessions"]["only"]["text"]
                # Count how many TAC_DONE split instructions landed.
                matches = re.findall(r"TAC_DONE_ and (\S+)", text)
                if matches:
                    # Complete with the last (only should be one after dedupe).
                    joined = f"TAC_DONE_{matches[-1]}"
                    self.h.set_text("only", text + f"\ndone\n{joined}\n")
                    return
                time.sleep(0.05)

        threading.Thread(target=complete, daemon=True).start()
        cp = self.h.run_broadcast("hi", "only", "only")
        self.assertEqual(cp.returncode, 0, msg=cp.stderr)
        self.assertIn("already targeted", cp.stderr)


# ============================================================================
# wait_for_idle
# Behavioral tests for wait_for_idle.py against a fake `tmux` CLI.
#
# Run:
#     python3 -m unittest discover -s skills/tmux-agent-comms/tests -p 'test_*.py'
# ============================================================================

WAITER = SCRIPTS / "wait_for_idle.py"


class WaitForIdleFakeTmuxHarness:
    def __init__(self):
        self.tmpdir = tempfile.mkdtemp(prefix="tac_test_")
        self.state_path = os.path.join(self.tmpdir, "state.json")
        self.write_state({"sessions": {}})
        self.env = dict(os.environ)
        self.env["FAKE_TMUX_STATE"] = self.state_path
        self.env["PATH"] = f"{FAKE_BIN}{os.pathsep}{self.env.get('PATH', '')}"

    def write_state(self, state):
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(state, f)

    def read_state(self):
        with open(self.state_path, encoding="utf-8") as f:
            return json.load(f)

    def set_session(self, name, text, fail_capture=False, fail_send=False):
        state = self.read_state()
        state["sessions"][name] = {
            "text": text,
            "fail_capture": fail_capture,
            "fail_send": fail_send,
        }
        self.write_state(state)

    def set_text(self, name, text):
        state = self.read_state()
        state["sessions"][name]["text"] = text
        self.write_state(state)

    def baseline_file(self, text):
        p = os.path.join(self.tmpdir, f"baseline_{time.time_ns()}.txt")
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        return p

    def run_waiter(self, target, *extra_args, timeout=5):
        cmd = [sys.executable, str(WAITER), target, "--timeout", str(timeout), "--interval", "0.1", "--quiet-cycles", "2"]
        cmd.extend(extra_args)
        return subprocess.run(
            cmd, env=self.env, text=True, capture_output=True, timeout=timeout + 10
        )


class WaitForIdleTests(unittest.TestCase):
    def setUp(self):
        self.h = WaitForIdleFakeTmuxHarness()

    def test_ready_accepts_already_idle(self):
        self.h.set_session("agent1", "ready>\n")
        cp = self.h.run_waiter("agent1", "--ready", "--no-print", timeout=2)
        self.assertEqual(cp.returncode, 0, msg=cp.stderr)

    def test_blocked_returns_3(self):
        self.h.set_session("agent1", "Do you trust the files in this folder?\n")
        cp = self.h.run_waiter("agent1", "--ready", timeout=2)
        self.assertEqual(cp.returncode, 3, msg=cp.stderr)
        self.assertIn("blocked", cp.stderr.lower())

    def test_missing_session_returns_1(self):
        cp = self.h.run_waiter("nope", "--ready", timeout=1)
        self.assertEqual(cp.returncode, 1)

    def test_stale_marker_in_baseline_is_not_success(self):
        marker = "TAC_DONE_stale123"
        pane = f"previous task output\n{marker}\n"
        self.h.set_session("agent1", pane)
        baseline = self.h.baseline_file(pane)
        cp = self.h.run_waiter(
            "agent1",
            "--baseline-file",
            baseline,
            "--completion-marker",
            marker,
            timeout=1,
        )
        self.assertEqual(cp.returncode, 2, msg=f"stdout={cp.stdout!r} stderr={cp.stderr!r}")

    def test_fresh_marker_completes(self):
        baseline_text = "prompt ready\n"
        self.h.set_session("agent1", baseline_text)
        baseline = self.h.baseline_file(baseline_text)
        marker = "TAC_DONE_fresh99"

        def flip():
            time.sleep(0.25)
            self.h.set_text(
                "agent1",
                baseline_text + f"answer: all good\n{marker}\n",
            )

        threading.Thread(target=flip, daemon=True).start()
        cp = self.h.run_waiter(
            "agent1",
            "--baseline-file",
            baseline,
            "--completion-marker",
            marker,
            timeout=3,
        )
        self.assertEqual(cp.returncode, 0, msg=cp.stderr)
        self.assertIn("all good", cp.stdout)

    def test_post_send_without_work_times_out(self):
        """Without --ready, pre-existing idle must not count as THIS send done."""
        self.h.set_session("agent1", "idle prompt\n")
        baseline = self.h.baseline_file("idle prompt\n")
        cp = self.h.run_waiter(
            "agent1",
            "--baseline-file",
            baseline,
            "--no-print",
            timeout=1,
        )
        self.assertEqual(cp.returncode, 2, msg=cp.stderr)

    def test_busy_then_idle_without_marker(self):
        baseline_text = "start\n"
        self.h.set_session("agent1", baseline_text + "esc to interrupt\n")
        baseline = self.h.baseline_file(baseline_text)

        def flip():
            time.sleep(0.3)
            self.h.set_text("agent1", baseline_text + "done answer\n")

        threading.Thread(target=flip, daemon=True).start()
        cp = self.h.run_waiter(
            "agent1",
            "--baseline-file",
            baseline,
            timeout=3,
        )
        self.assertEqual(cp.returncode, 0, msg=cp.stderr)
        self.assertIn("done answer", cp.stdout)

    def test_marker_mode_ignores_quiet_prompt_echo(self):
        """Prompt echo changes text but without joined marker → keep waiting."""
        baseline_text = "ready\n"
        self.h.set_session("agent1", baseline_text)
        baseline = self.h.baseline_file(baseline_text)
        marker = "TAC_DONE_echoonly"

        def flip():
            time.sleep(0.2)
            # Echo halves only — not the joined marker.
            self.h.set_text(
                "agent1",
                baseline_text + "task...\nprint TAC_DONE_ and echoonly\n",
            )

        threading.Thread(target=flip, daemon=True).start()
        cp = self.h.run_waiter(
            "agent1",
            "--baseline-file",
            baseline,
            "--completion-marker",
            marker,
            "--no-print",
            timeout=1,
        )
        self.assertEqual(cp.returncode, 2, msg=cp.stderr)


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.h = WaitForIdleFakeTmuxHarness()
        self.preflight = SCRIPTS / "preflight_send.py"

    def run_pf(self, target):
        return subprocess.run(
            [sys.executable, str(self.preflight), target],
            env=self.h.env,
            text=True,
            capture_output=True,
            timeout=5,
        )

    def test_sendable_idle(self):
        self.h.set_session("a", "ready>\n")
        cp = self.run_pf("a")
        self.assertEqual(cp.returncode, 0, msg=cp.stderr)
        self.assertEqual(cp.stdout.strip(), "idle")

    def test_working(self):
        self.h.set_session("a", "thinking...\nesc to interrupt\n")
        cp = self.run_pf("a")
        self.assertEqual(cp.returncode, 2, msg=cp.stderr)

    def test_blocked(self):
        self.h.set_session("a", "Do you trust the files in this folder?\n")
        cp = self.run_pf("a")
        self.assertEqual(cp.returncode, 3, msg=cp.stderr)

    def test_missing(self):
        cp = self.run_pf("ghost")
        self.assertEqual(cp.returncode, 4, msg=cp.stderr)


if __name__ == "__main__":
    unittest.main()
