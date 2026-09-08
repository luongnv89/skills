#!/usr/bin/env python3
"""Behavioral tests for wait_for_idle.py against a fake `herdr` CLI.

Covers the P1.1/P2.7 false-completion fix: a pane already `working` (or
already carrying the completion marker) before this send must not be
reported as settled for THIS send.

Run directly (stdlib unittest only):
    python3 -m unittest discover -s skills/herdr-agent-comms/tests -p 'test_*.py'
"""

from __future__ import annotations

import json
import os
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
WAITER = SCRIPTS / "wait_for_idle.py"


class FakeHerdrHarness:
    def __init__(self):
        self.tmpdir = tempfile.mkdtemp(prefix="hac_test_")
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

    def set_pane(self, pane_id, status, text, name=None, fail_get=False,
                 fail_get_after=None, null_pane_get=False, fail_read=False):
        state = self.read_state()
        state["panes"][pane_id] = {
            "agent_status": status, "text": text, "name": name, "fail_get": fail_get,
            "null_pane_get": null_pane_get, "fail_read": fail_read,
        }
        if fail_get_after is not None:
            # pane get succeeds fail_get_after times, then fails every call after.
            state["panes"][pane_id]["fail_get_after"] = fail_get_after
        self.write_state(state)

    def set_status(self, pane_id, status):
        state = self.read_state()
        state["panes"][pane_id]["agent_status"] = status
        self.write_state(state)

    def delete_pane(self, pane_id):
        state = self.read_state()
        state["panes"].pop(pane_id, None)
        self.write_state(state)

    def append_text(self, pane_id, text):
        state = self.read_state()
        state["panes"][pane_id]["text"] += text
        self.write_state(state)

    def baseline_file(self, text):
        p = os.path.join(self.tmpdir, f"baseline_{time.time_ns()}.txt")
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        return p

    def run_waiter(self, pane_id, *extra_args, timeout=5):
        cmd = [sys.executable, str(WAITER), pane_id, "--timeout", str(timeout)]
        cmd.extend(extra_args)
        return subprocess.run(cmd, env=self.env, text=True, capture_output=True, timeout=timeout + 10)

    def count_herdr_calls(self):
        """Put a logging `herdr` ahead of the fake on PATH, so a test can
        assert how many CLI round trips the waiter actually made."""
        shim_dir = os.path.join(self.tmpdir, "counting_bin")
        os.makedirs(shim_dir, exist_ok=True)
        self.call_log = os.path.join(self.tmpdir, "calls.log")
        shim = os.path.join(shim_dir, "herdr")
        with open(shim, "w", encoding="utf-8") as f:
            f.write(
                "#!/usr/bin/env bash\n"
                f'echo "$*" >> {self.call_log}\n'
                f'exec python3 "{HERE / "fake_herdr.py"}" "$@"\n'
            )
        os.chmod(shim, 0o755)
        self.env["PATH"] = f"{shim_dir}{os.pathsep}{self.env['PATH']}"

    def calls_made(self):
        if not os.path.exists(self.call_log):
            return []
        with open(self.call_log, encoding="utf-8") as f:
            return [ln.strip() for ln in f if ln.strip()]


class WaitForIdleMarkerSemanticsTests(unittest.TestCase):
    def setUp(self):
        self.h = FakeHerdrHarness()

    def test_stale_marker_in_baseline_is_not_success(self):
        """P2.7: a marker already present in the pre-send baseline (leftover
        from a previous task) must not be accepted as proof THIS send
        finished — the pane should time out waiting for a *fresh* marker.
        """
        marker = "HERDR_DONE_stale123"
        pane_text = f"previous task output\n{marker}\n"
        self.h.set_pane("p1", "idle", pane_text)
        baseline = self.h.baseline_file(pane_text)  # baseline == current text (marker included)

        cp = self.h.run_waiter(
            "p1", "--baseline-file", baseline, "--completion-marker", marker, "--timeout", "1"
        )
        self.assertEqual(cp.returncode, 2, msg=f"stdout={cp.stdout!r} stderr={cp.stderr!r}")

    def test_prior_working_pane_does_not_falsely_complete_this_send(self):
        """P1.1: pane is ALREADY working (prior task in flight) when the
        waiter starts. Baseline was captured while working. No fresh marker
        ever appears. The waiter must NOT report success — it must time out,
        not short-circuit on a stale `saw_working` transition.
        """
        prior_text = "prior task still running...\n"
        self.h.set_pane("p1", "working", prior_text)
        baseline = self.h.baseline_file(prior_text)
        marker = "HERDR_DONE_thissend456"

        # Pane flips to idle shortly after (prior task finishes) but the
        # fresh marker for THIS send never shows up.
        def flip():
            time.sleep(0.3)
            self.h.set_status("p1", "idle")

        t = threading.Thread(target=flip)
        t.start()
        cp = self.h.run_waiter(
            "p1", "--baseline-file", baseline, "--completion-marker", marker, "--timeout", "1"
        )
        t.join()
        self.assertEqual(cp.returncode, 2, msg=f"stdout={cp.stdout!r} stderr={cp.stderr!r}")

    def test_fresh_marker_after_working_is_success(self):
        """Sanity/control: once the fresh marker actually appears after a
        real working transition, the waiter must succeed (rc 0)."""
        baseline_text = "before send\n"
        self.h.set_pane("p1", "idle", baseline_text)
        baseline = self.h.baseline_file(baseline_text)
        marker = "HERDR_DONE_real789"

        def do_work():
            time.sleep(0.1)
            self.h.set_status("p1", "working")
            time.sleep(0.2)
            self.h.append_text("p1", f"reply text {marker}\n")
            self.h.set_status("p1", "idle")

        t = threading.Thread(target=do_work)
        t.start()
        cp = self.h.run_waiter(
            "p1", "--baseline-file", baseline, "--completion-marker", marker, "--timeout", "5"
        )
        t.join()
        self.assertEqual(cp.returncode, 0, msg=f"stdout={cp.stdout!r} stderr={cp.stderr!r}")
        self.assertIn(marker, cp.stdout)

    def test_working_to_done_transition_is_success_not_timeout(self):
        """Regression (P2 round 4): a pane that goes working -> DONE and stays
        `done` (never `idle`) must be reported as finished (rc 0), not time out
        (rc 2). The old working-branch waited for `done` in only HALF the slice
        then spent the WHOLE remaining deadline waiting only for `idle`, so a
        pane settling on `done` AFTER that half-window blocked until timeout.
        The fix bounds the idle-wait too and loops back to re-check either
        terminal state.

        Timing matters: the pane must stay `working` past the first half-window
        (~half the deadline) and only then flip to `done`, otherwise the old
        code's initial `wait done` succeeds and the bug never triggers. With a
        2s deadline the half-window is ~1s, so flip at 1.2s.
        """
        baseline_text = "before send\n"
        self.h.set_pane("p1", "working", baseline_text)
        baseline = self.h.baseline_file(baseline_text)

        def do_work():
            time.sleep(1.2)  # past the first half-window; misses the buggy `wait done`
            self.h.append_text("p1", "reply text, task complete\n")
            self.h.set_status("p1", "done")  # terminal DONE, never idle

        t = threading.Thread(target=do_work)
        t.start()
        cp = self.h.run_waiter("p1", "--baseline-file", baseline, "--timeout", "2")
        t.join()
        self.assertEqual(cp.returncode, 0, msg=f"stdout={cp.stdout!r} stderr={cp.stderr!r}")

    def test_working_to_done_with_marker_is_success(self):
        """Same working->done transition (flipping past the half-window), but
        with a completion marker: the fresh marker appearing at the `done`
        transition must be accepted, not lost because the branch only watched
        for `idle`."""
        baseline_text = "before send\n"
        self.h.set_pane("p1", "working", baseline_text)
        baseline = self.h.baseline_file(baseline_text)
        marker = "HERDR_DONE_done_only_42"

        def do_work():
            time.sleep(1.2)
            self.h.append_text("p1", f"reply {marker}\n")
            self.h.set_status("p1", "done")  # terminal DONE, never idle

        t = threading.Thread(target=do_work)
        t.start()
        cp = self.h.run_waiter(
            "p1", "--baseline-file", baseline, "--completion-marker", marker, "--timeout", "2"
        )
        t.join()
        self.assertEqual(cp.returncode, 0, msg=f"stdout={cp.stdout!r} stderr={cp.stderr!r}")
        self.assertIn(marker, cp.stdout)

    def test_pane_disappearing_mid_wait_is_error_not_completion(self):
        """Regression (P2 round 5): if the pane vanishes during the
        content-stability wait, a FAILED `herdr pane read` must not stabilize
        into a false completion (rc 0). It must surface as an error (rc 1).
        --no-status forces the content-stability path (no agent-status).
        """
        baseline_text = "task running\n"
        self.h.set_pane("p1", "working", baseline_text)
        baseline = self.h.baseline_file(baseline_text)

        def kill_pane():
            time.sleep(0.4)
            self.h.delete_pane("p1")  # pane gone: reads now fail (rc 1)

        t = threading.Thread(target=kill_pane)
        t.start()
        cp = self.h.run_waiter(
            "p1", "--baseline-file", baseline, "--no-status",
            "--interval", "0.2", "--timeout", "3",
        )
        t.join()
        self.assertEqual(cp.returncode, 1, msg=f"stdout={cp.stdout!r} stderr={cp.stderr!r}")

    def test_pane_gone_in_status_path_read_is_error_not_completion(self):
        """Same disappearance, but on the prefer-status path: pane is idle/done
        (so we take the terminal branch), then the transcript read fails. A
        failed read there must be an error (rc 1), never a success. Uses a
        pane id shaped like a real herdr id (w..:..) so resolve_pane accepts it
        and the failure happens at the transcript read, not at resolution.

        Deterministic: `fail_read` keeps `pane get` succeeding (so the waiter
        reaches the terminal branch) while `pane read` fails, instead of
        racing a 0.05s delete window against the 0.25s status poll."""
        baseline_text = "task running\n"
        self.h.set_pane("w1:p1", "done", baseline_text, fail_read=True)
        baseline = self.h.baseline_file(baseline_text)
        cp = self.h.run_waiter("w1:p1", "--baseline-file", baseline, "--timeout", "3")
        # rc 1 (read failed) is the correct outcome; the bug returned 0.
        self.assertEqual(cp.returncode, 1, msg=f"stdout={cp.stdout!r} stderr={cp.stderr!r}")

    def test_blocked_status_returns_3(self):
        self.h.set_pane("p1", "blocked", "trust dialog\n")
        baseline = self.h.baseline_file("trust dialog\n")
        cp = self.h.run_waiter("p1", "--baseline-file", baseline, "--timeout", "1")
        self.assertEqual(cp.returncode, 3)

    def test_ready_accepts_already_idle_without_working(self):
        self.h.set_pane("p1", "idle", "already done earlier\n")
        cp = self.h.run_waiter("p1", "--ready", "--timeout", "1")
        self.assertEqual(cp.returncode, 0)

    def test_ready_with_status_lookup_failure_is_error_not_ready(self):
        """Regression (P1 round 8): a `--ready` check must NOT report ready
        (rc 0) when `herdr pane get` fails — a failed status lookup is
        unverifiable, not a valid `unknown`. Previously this fell through to
        content-stability and returned 0. Now it errors (rc 1)."""
        # Pane resolves (via `agent get`) but every `pane get` status lookup
        # fails, so status is unverifiable throughout.
        self.h.set_pane("p1", "idle", "boot\n", name="flaky", fail_get=True)
        cp = self.h.run_waiter("p1", "--ready", "--timeout", "2")
        self.assertEqual(cp.returncode, 1, msg=f"stdout={cp.stdout!r} stderr={cp.stderr!r}")

    def test_ready_blocked_pane_with_lookup_failure_is_not_ready(self):
        """The reported repro: a genuinely `blocked` pane whose status lookup
        also persistently fails must NOT be reproduced as ready rc 0. Since the
        lookup is unverifiable, `--ready` errors (rc 1) rather than guessing
        ready — never silently proceeding as if a dialog weren't there.

        Small --interval + short quiet-cycles so that, under the OLD fail-open
        behaviour, the static dialog text WOULD stabilize and return a false
        ready rc 0 — that is exactly what the fix must prevent. rc 1 (fixed)
        vs rc 0 (buggy) is the discriminating outcome."""
        self.h.set_pane("p1", "blocked", "Trust this workspace? [y/n]\n",
                        name="gated", fail_get=True)
        cp = self.h.run_waiter(
            "p1", "--ready", "--interval", "0.1", "--quiet-cycles", "2", "--timeout", "5"
        )
        self.assertEqual(cp.returncode, 1, msg=f"stdout={cp.stdout!r} stderr={cp.stderr!r}")

    def test_valid_unknown_status_still_uses_content_stability(self):
        """A validly-absent status ("unknown", e.g. a non-integrated CLI) must
        NOT be treated as a lookup failure — it still uses the content-stability
        path and can settle ready. This guards against over-correcting #1 into
        breaking integration-less agents. (Small --interval + enough timeout so
        the quiet-cycle stability check can actually complete.)"""
        self.h.set_pane("p1", "unknown", "some stable output\n")
        cp = self.h.run_waiter(
            "p1", "--ready", "--interval", "0.1", "--quiet-cycles", "2", "--timeout", "5"
        )
        self.assertEqual(cp.returncode, 0, msg=f"stdout={cp.stdout!r} stderr={cp.stderr!r}")

    def test_ready_unknown_then_lookup_failure_is_error_not_ready(self):
        """Regression (P round 9): the initial status is a VALID `unknown`
        (passes the first probe → enters content-stability), then a LATER
        `herdr pane get` fails. That later lookup failure must ALSO fail the
        --ready check (rc 1), not be ignored so content stability reports a
        false ready rc 0. `fail_get_after=1` = first lookup ok, then fail.
        Small interval/quiet so, unfixed, stability would settle ready fast."""
        self.h.set_pane("p1", "unknown", "stable output\n", name="flaky", fail_get_after=1)
        cp = self.h.run_waiter(
            "p1", "--ready", "--interval", "0.1", "--quiet-cycles", "2", "--timeout", "5"
        )
        self.assertEqual(cp.returncode, 1, msg=f"stdout={cp.stdout!r} stderr={cp.stderr!r}")

    def test_ready_working_then_lookup_failure_is_error_not_ready(self):
        """The status-loop variant: initial status `working` enters the status
        loop, then a subsequent `herdr pane get` fails. That in-loop lookup
        failure must fail the --ready check (rc 1). `fail_get_after=1` = the
        initial working read succeeds, the next in-loop read fails."""
        self.h.set_pane("p1", "working", "running\n", name="busy", fail_get_after=1)
        cp = self.h.run_waiter(
            "p1", "--ready", "--interval", "0.1", "--quiet-cycles", "2", "--timeout", "5"
        )
        self.assertEqual(cp.returncode, 1, msg=f"stdout={cp.stdout!r} stderr={cp.stderr!r}")

    def test_ready_numeric_status_is_unverifiable_not_ready(self):
        """Regression (round 10, finding #1): an off-enum status VALUE (here a
        numeric 123) must be treated as unverifiable, NOT as a benign truthy
        status that sails through. Under --ready it must error (rc 1), never
        report ready (rc 0). fake_herdr passes agent_status straight through
        json.dumps, so this injects a real numeric status into `pane get`."""
        self.h.set_pane("p1", 123, "some output\n")
        cp = self.h.run_waiter(
            "p1", "--ready", "--interval", "0.1", "--quiet-cycles", "2", "--timeout", "3"
        )
        self.assertEqual(cp.returncode, 1, msg=f"stdout={cp.stdout!r} stderr={cp.stderr!r}")

    def test_ready_garbage_string_status_is_unverifiable_not_ready(self):
        """Same fail-open hole via an out-of-enum STRING (a typo / server-invented
        value): must be unverifiable (rc 1 under --ready), not accepted."""
        self.h.set_pane("p1", "totally-bogus", "some output\n")
        cp = self.h.run_waiter(
            "p1", "--ready", "--interval", "0.1", "--quiet-cycles", "2", "--timeout", "3"
        )
        self.assertEqual(cp.returncode, 1, msg=f"stdout={cp.stdout!r} stderr={cp.stderr!r}")

    def test_null_pane_get_is_unverifiable_not_crash(self):
        """Regression (round 12 note): a valid-JSON 0-exit `pane get` with a
        null `pane` ({"result":{"pane":null}}) must be treated as unverifiable
        (rc 1 under --ready), NOT raise AttributeError from `None.get(...)`.
        A traceback on stderr and a crash exit code is the buggy behavior."""
        self.h.set_pane("p1", "idle", "boot\n", name="nullpane", null_pane_get=True)
        cp = self.h.run_waiter("p1", "--ready", "--timeout", "2")
        self.assertEqual(cp.returncode, 1, msg=f"stdout={cp.stdout!r} stderr={cp.stderr!r}")
        self.assertNotIn("Traceback", cp.stderr)
        self.assertNotIn("AttributeError", cp.stderr)

    def test_resolve_pane_null_pane_does_not_crash(self):
        """Regression (round 12): a `w..:..` pane id whose `herdr pane get`
        returns {"result":{"pane":null}} must NOT crash resolve_pane with an
        uncaught TypeError (None["pane_id"]). It falls through to `agent get`,
        resolves, and the subsequent null-pane status read is unverifiable
        (rc 1 under --ready) — never a traceback."""
        self.h.set_pane("w1:p1", "idle", "boot\n", name="nullres", null_pane_get=True)
        cp = self.h.run_waiter("w1:p1", "--ready", "--timeout", "2")
        self.assertNotIn("Traceback", cp.stderr, msg=f"stderr={cp.stderr!r}")
        self.assertNotIn("TypeError", cp.stderr)
        self.assertEqual(cp.returncode, 1, msg=f"stdout={cp.stdout!r} stderr={cp.stderr!r}")

    def test_empty_string_status_is_unverifiable(self):
        """An empty-string status is NOT a valid 'unknown' — the old `or
        "unknown"` masked it. It's off-enum, so unverifiable (rc 1 --ready)."""
        self.h.set_pane("p1", "", "some output\n")
        cp = self.h.run_waiter(
            "p1", "--ready", "--interval", "0.1", "--quiet-cycles", "2", "--timeout", "3"
        )
        self.assertEqual(cp.returncode, 1, msg=f"stdout={cp.stdout!r} stderr={cp.stderr!r}")

    def test_no_marker_legacy_fallback_uses_saw_working(self):
        """Without a completion marker arranged, a genuine working->idle
        transition for THIS send is still accepted (legacy behavior)."""
        baseline_text = "before\n"
        self.h.set_pane("p1", "idle", baseline_text)
        baseline = self.h.baseline_file(baseline_text)

        def do_work():
            time.sleep(0.1)
            self.h.set_status("p1", "working")
            # Hold `working` past several 0.25s status polls: the old 0.2s
            # window could fall between two polls (plus subprocess overhead),
            # miss `saw_working`, fall to content-stability (6s for 3x2s
            # quiet cycles) and time out the 5s wait with rc 2.
            time.sleep(1.0)
            self.h.append_text("p1", "reply without marker\n")
            self.h.set_status("p1", "idle")

        t = threading.Thread(target=do_work)
        t.start()
        cp = self.h.run_waiter("p1", "--baseline-file", baseline, "--timeout", "5")
        t.join()
        self.assertEqual(cp.returncode, 0, msg=f"stdout={cp.stdout!r} stderr={cp.stderr!r}")


class WaitForIdleStatusLoopPacingTests(unittest.TestCase):
    """Regression: the status loop must poll, never spin.

    `wait_status()` used to shell out to `herdr wait agent-status`, a command
    herdr 0.9 does not have (`unknown command: wait`). It returned instantly
    every time, and because the loop had no pause of its own, a pane that
    stayed `working` produced a hot spin — ~149 CLI round trips and 85% CPU
    over a 5s timeout, against the very fallback path this script documents.
    """

    def setUp(self):
        self.h = FakeHerdrHarness()
        self.h.count_herdr_calls()

    def test_working_pane_does_not_busy_spin(self):
        self.h.set_pane("p1", "working", "still going...\n")
        baseline = self.h.baseline_file("still going...\n")

        cp = self.h.run_waiter("p1", "--baseline-file", baseline, "--timeout", "3")
        self.assertEqual(cp.returncode, 2, msg=f"stdout={cp.stdout!r} stderr={cp.stderr!r}")

        calls = self.h.calls_made()
        # One `pane get` per STATUS_POLL_S (0.25s) slice over a 3s wait, plus
        # the initial resolve/baseline reads: ~14 in practice. The pre-fix spin
        # made ~90 here, so the bound separates the two by a wide margin rather
        # than pinning an exact count that machine speed would make flaky.
        self.assertLessEqual(
            len(calls), 30,
            msg=f"status loop is spinning: {len(calls)} herdr calls in 3s\n" + "\n".join(calls[:20]),
        )

    def test_pre_task_idle_pane_does_not_busy_spin(self):
        """The second former call site: a pane still `idle` because the task
        has not started yet. It used to wait on `--status working`, which was
        the same nonexistent command, so this branch spun too."""
        pane_text = "start\n"
        self.h.set_pane("p1", "idle", pane_text)
        # `herdr pane read` prints the text with a trailing newline, so the
        # baseline must match that exactly or the loop takes the changed-text
        # path instead of the pre-task-idle one under test.
        baseline = self.h.baseline_file(pane_text + "\n")

        cp = self.h.run_waiter("p1", "--baseline-file", baseline, "--timeout", "3")
        self.assertEqual(cp.returncode, 2, msg=f"stdout={cp.stdout!r} stderr={cp.stderr!r}")

        calls = self.h.calls_made()
        # This branch issues three calls per tick (two `pane get`, one
        # `pane read`), so its ceiling is higher than the working path's.
        # Pre-fix it made ~86 here.
        self.assertLessEqual(
            len(calls), 50,
            msg=f"pre-task-idle loop is spinning: {len(calls)} herdr calls in 3s\n" + "\n".join(calls[:20]),
        )

    def test_no_call_to_the_nonexistent_wait_subcommand(self):
        """herdr 0.9 answers `herdr wait ...` with `unknown command: wait`."""
        self.h.set_pane("p1", "working", "still going...\n")
        baseline = self.h.baseline_file("still going...\n")
        self.h.run_waiter("p1", "--baseline-file", baseline, "--timeout", "2")

        offenders = [c for c in self.h.calls_made() if c.startswith("wait ")]
        self.assertEqual(offenders, [], msg=f"called a nonexistent herdr subcommand: {offenders}")


if __name__ == "__main__":
    unittest.main()
