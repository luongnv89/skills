"""Tests for the rex-agent scripts, run against tests/fake_rex.py.

    python3 -m unittest discover -s tests -p 'test_*.py' -v

The fake reproduces the JSON shapes captured from Rex: root records with an
empty id, owner pids, block events wrapped in session_event > block_event,
and layout trees with exact split ratios.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

import launch_profile  # noqa: E402

SESSION = "session:00000000-0000-0000-0000-000000000001"
WINDOW = "window:00000001"
ROOT = "block:00000001-0000-0000-0000-000000000000"
STAMP = "2026-10-16T20:00:00.000000000Z"


def block_id(n: int) -> str:
    return f"block:{n:08x}-0000-0000-0000-000000000000"


def agent(label: str, pid: int, state: str | None = "idle", app: str = "claude-code",
          argv0: str = "claude", fg_pid: int | None = None, fg_argv0: str | None = None) -> dict:
    # Fake pids sit above any pid_max, so no test reads a real process.
    pid, fg_pid = 4200000 + pid, (4200000 + fg_pid) if fg_pid else None
    fg = {"pid": fg_pid or pid, "user_id": 501, "name": "2.1.301", "argv0": fg_argv0 or argv0}
    records = [] if state is None else [
        {"state": state, "app": app, "updated_at": STAMP, "owner": {"pid": pid, "name": "2.1.301"}}]
    return {"label": label, "window_id": WINDOW, "records": records, "paste": True, "screen": "",
            "typed": [], "keys": [], "on_enter": [], "command": [],
            "process": {"last_exit": None, "child": dict(fg), "foreground": fg}}


def row(*ids: str, ratio: float = 0.5) -> dict:
    """A right-nested chain of horizontal splits over the given blocks."""
    if len(ids) == 1:
        return {"block_id": ids[0]}
    return {"split": {"split_id": f"split:{ids[0][-6:]}", "direction": "horizontal", "ratio": ratio,
                      "before": {"block_id": ids[0]}, "after": row(*ids[1:], ratio=ratio)}}


class FakeRexCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="rex-agent-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        bin_dir = self.tmp / "bin"
        bin_dir.mkdir()
        shim = bin_dir / "rex"
        shim.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{HERE / "fake_rex.py"}" "$@"\n')
        shim.chmod(shim.stat().st_mode | stat.S_IEXEC)
        self.state_path = self.tmp / "state.json"
        env = {
            "PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}",
            "FAKE_REX_STATE": str(self.state_path), "FAKE_REX_EVENTS_MAX": "8",
            "REX_SESSION": SESSION, "REX_BLOCK": ROOT, "SHELL": "/bin/zsh",
        }
        patcher = mock.patch.dict(os.environ, env)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop("CLAUDE_EFFORT", None)
        self.write_state({ROOT: agent("root", 100, state="working")}, row(ROOT))

    def write_state(self, blocks: dict, layout: dict, **extra) -> None:
        state = {"session": SESSION, "me": ROOT, "windows": [{"window_id": WINDOW, "layout": layout}],
                 "blocks": blocks, "events": [], "pending": [], "log": [], "next_id": 100, **extra}
        self.state_path.write_text(json.dumps(state))

    def state(self) -> dict:
        return json.loads(self.state_path.read_text())

    def calls(self, verb: str) -> list[list[str]]:
        return [c for c in self.state()["log"] if c[:1] == [verb]]

    def run_script(self, script: str, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(SCRIPTS / script), *args], input=stdin,
                              capture_output=True, text=True, timeout=60)

    def fleet_with(self, **workers: dict) -> dict:
        blocks = {ROOT: agent("root", 100, state="working")}
        ids = [ROOT]
        for n, (label, spec) in enumerate(workers.items(), start=2):
            blocks[block_id(n)] = {**agent(label, 100 + n), **spec} if isinstance(spec, dict) else spec
            ids.append(block_id(n))
        self.write_state(blocks, row(*ids))
        return {label: block_id(n) for n, label in enumerate(workers, start=2)}


class PromptTests(FakeRexCase):
    def prompt(self, target: str, text: str = "Summarize the open PRs", *extra: str):
        proc = self.run_script("agent.py", "prompt", target, text, "--activity-timeout", "1.5",
                               "--timeout", "4", *extra)
        return proc, (json.loads(proc.stdout) if proc.stdout.strip() else {})

    def test_settles_on_done_after_working_and_wraps_paste(self):
        ids = self.fleet_with(reviewer={})
        st = self.state()
        st["blocks"][ids["reviewer"]]["on_enter"] = [[[0.2, {"state": "working", "app": "claude-code"}],
                                                       [0.6, {"state": "done", "app": "claude-code"}]]]
        self.state_path.write_text(json.dumps(st))
        proc, res = self.prompt("reviewer")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual((res["outcome"], res["state"], res["observed_working"]), ("settled", "done", True))
        block = self.state()["blocks"][ids["reviewer"]]
        self.assertRegex(res["turn"], r"^[0-9a-f]{6}$")
        self.assertEqual(block["typed"], [f"\x1b[200~Summarize the open PRs\n\n(rex-agent turn {res['turn']})\x1b[201~"])
        self.assertEqual(block["keys"], ["enter"])

    def test_refuses_working_target_without_sending(self):
        self.fleet_with(reviewer=agent("reviewer", 102, state="working"))
        proc, res = self.prompt("reviewer")
        self.assertEqual((proc.returncode, res["outcome"], res["sent"]), (6, "working", False))
        self.assertEqual(self.calls("send"), [])

    def test_refuses_blocked_target_without_sending(self):
        self.fleet_with(reviewer=agent("reviewer", 102, state="blocked"))
        proc, res = self.prompt("reviewer")
        self.assertEqual((proc.returncode, res["outcome"]), (3, "blocked"))
        self.assertEqual(self.calls("send"), [])

    def test_stale_done_left_at_a_shell_is_no_agent(self):
        self.fleet_with(reviewer=agent("reviewer", 102, state="done", fg_pid=222, fg_argv0="-zsh"))
        proc, res = self.prompt("reviewer")
        self.assertEqual((proc.returncode, res["outcome"]), (5, "no_agent"))
        self.assertEqual(self.calls("send"), [])

    def test_record_from_an_earlier_process_is_not_trusted(self):
        self.fleet_with(reviewer=agent("reviewer", 102, state="done", fg_pid=333))
        proc, res = self.prompt("reviewer")
        self.assertEqual((proc.returncode, res["outcome"]), (4, "unverifiable"))
        self.assertEqual(self.calls("send"), [])

    def test_agent_without_any_record_is_unverifiable(self):
        self.fleet_with(reviewer=agent("reviewer", 102, state=None, argv0="codex"))
        proc, res = self.prompt("reviewer")
        self.assertEqual((proc.returncode, res["outcome"]), (4, "unverifiable"))
        self.assertEqual(self.calls("send"), [])

    def test_blocked_after_send_is_reported(self):
        ids = self.fleet_with(reviewer={})
        st = self.state()
        st["blocks"][ids["reviewer"]]["on_enter"] = [[[0.2, {"state": "blocked", "kind": "permission",
                                                             "msg": "approve Bash: ls"}]]]
        self.state_path.write_text(json.dumps(st))
        proc, res = self.prompt("reviewer")
        self.assertEqual((proc.returncode, res["outcome"], res["msg"]), (3, "blocked", "approve Bash: ls"))

    def test_no_activity_is_stalled(self):
        self.fleet_with(reviewer={})
        proc, res = self.prompt("reviewer")
        self.assertEqual((proc.returncode, res["outcome"], res["sent"]), (7, "stalled", True))

    def test_working_that_never_settles_times_out(self):
        ids = self.fleet_with(reviewer={})
        st = self.state()
        st["blocks"][ids["reviewer"]]["on_enter"] = [[[0.2, {"state": "working", "app": "claude-code"}]]]
        self.state_path.write_text(json.dumps(st))
        proc, res = self.prompt("reviewer")
        self.assertEqual((proc.returncode, res["outcome"]), (8, "timeout"))

    def test_removed_record_mid_turn_is_unverifiable(self):
        ids = self.fleet_with(reviewer={})
        st = self.state()
        st["blocks"][ids["reviewer"]]["on_enter"] = [[[0.2, {"state": "working", "app": "claude-code"}],
                                                       [0.5, "remove"]]]
        self.state_path.write_text(json.dumps(st))
        proc, res = self.prompt("reviewer")
        self.assertEqual((proc.returncode, res["outcome"]), (4, "unverifiable"))

    def test_agent_exit_mid_turn_is_reported(self):
        ids = self.fleet_with(reviewer={})
        st = self.state()
        st["blocks"][ids["reviewer"]]["on_enter"] = [[[0.2, {"state": "working", "app": "claude-code"}],
                                                       [0.5, {"exit": 1}]]]
        self.state_path.write_text(json.dumps(st))
        proc, res = self.prompt("reviewer")
        self.assertEqual((proc.returncode, res["outcome"]), (9, "exited"))

    def test_own_block_is_refused(self):
        self.fleet_with(reviewer={})
        proc, _ = self.prompt("root")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("your own block", proc.stderr)
        self.assertEqual(self.calls("send"), [])

    def test_name_never_matches_an_id_suffix(self):
        self.fleet_with(other={})
        proc, _ = self.prompt("0000")  # every fake block ID ends in zeros
        self.assertEqual(proc.returncode, 1)
        self.assertIn("no block labeled '0000'", proc.stderr)
        self.assertEqual(self.calls("send"), [])

    def test_ambiguous_label_is_refused(self):
        self.fleet_with(dup={}, twin=agent("dup", 103))
        proc, _ = self.prompt("dup")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("labels 2 blocks", proc.stderr)

    def test_escape_sequences_are_stripped_from_the_text(self):
        ids = self.fleet_with(reviewer={})
        _, res = self.prompt("reviewer", "review\x1b[201~\x1b[2Jnow\r\nthen")
        typed = self.state()["blocks"][ids["reviewer"]]["typed"][0]
        self.assertEqual(typed, f"\x1b[200~review[201~[2Jnow\nthen\n\n(rex-agent turn {res['turn']})\x1b[201~")

    def test_a_leading_bang_is_refused_unless_raw(self):
        ids = self.fleet_with(reviewer={})
        proc, _ = self.prompt("reviewer", "!rm -rf build")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("shell command", proc.stderr)
        self.assertEqual(self.calls("send"), [])
        self.prompt("reviewer", "/compact", "--raw")
        self.assertEqual(self.state()["blocks"][ids["reviewer"]]["typed"], ["\x1b[200~/compact\x1b[201~"])

    def test_a_newer_idle_without_working_does_not_settle(self):
        ids = self.fleet_with(reviewer=agent("reviewer", 102, state="done"))
        st = self.state()
        st["blocks"][ids["reviewer"]]["on_enter"] = [[[0.2, {"state": "idle", "app": "claude-code"}]]]
        self.state_path.write_text(json.dumps(st))
        proc, res = self.prompt("reviewer")
        self.assertEqual((proc.returncode, res["outcome"]), (7, "stalled"))

    def test_a_newer_done_settles_even_if_working_was_missed(self):
        ids = self.fleet_with(reviewer={})
        st = self.state()
        st["blocks"][ids["reviewer"]]["on_enter"] = [[[0.2, {"state": "done", "app": "claude-code"}]]]
        self.state_path.write_text(json.dumps(st))
        proc, res = self.prompt("reviewer")
        self.assertEqual((proc.returncode, res["outcome"], res["observed_working"]), (0, "settled", False))

    def test_multiline_text_is_refused_without_bracketed_paste(self):
        self.fleet_with(reviewer={**agent("reviewer", 102), "paste": False})
        proc, _ = self.prompt("reviewer", "line one\nline two")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("bracketed paste off", proc.stderr)
        self.assertEqual(self.calls("send"), [])

    def test_screen_settle_is_an_explicit_fallback(self):
        ids = self.fleet_with(oc=agent("oc", 102, state=None, argv0="opencode"))
        st = self.state()
        st["blocks"][ids["oc"]]["on_enter"] = [[[0.3, {"screen": "thinking..."}], [0.8, {"screen": "answer"}]]]
        self.state_path.write_text(json.dumps(st))
        proc, res = self.prompt("oc", "hello", "--settle", "screen", "--quiet", "1")
        self.assertEqual((proc.returncode, res["outcome"], res["state"]), (0, "settled", "screen-quiet"))

    def test_prompt_text_can_come_from_stdin(self):
        ids = self.fleet_with(reviewer={})
        proc = self.run_script("agent.py", "prompt", "reviewer", "-", "--activity-timeout", "1", "--timeout", "2",
                               stdin="from stdin")
        turn = json.loads(proc.stdout)["turn"]
        self.assertEqual(self.state()["blocks"][ids["reviewer"]]["typed"],
                         [f"\x1b[200~from stdin\n\n(rex-agent turn {turn})\x1b[201~"])


class WatchTests(FakeRexCase):
    def test_events_in_one_write_arrive_together(self):
        import rexlib
        st = self.state()
        st["pending"] = [{"at": time.time() + 0.4, "block": ROOT, "action": {"state": "working"}},
                         {"at": time.time() + 0.4, "block": ROOT, "action": {"state": "done"}}]
        self.state_path.write_text(json.dumps(st))
        watch = rexlib.Watch(SESSION)
        try:
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline and len(watch.events) < 2:
                watch.pump(0.2)
        finally:
            watch.close()
        states = [e["payload"]["record"]["state"] for e in watch.events]
        self.assertEqual(states, ["working", "done"])


class CheckTests(FakeRexCase):
    def test_check_reports_this_terminal(self):
        proc = self.run_script("agent.py", "check")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["block_id"], ROOT)

    def test_check_refuses_a_stale_block_and_missing_capabilities(self):
        st = self.state()
        st["me"] = block_id(7)
        self.state_path.write_text(json.dumps(st))
        proc = self.run_script("agent.py", "check")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("do not exist as this session and block", proc.stderr)
        st["me"], st["no_program_status"] = ROOT, True
        self.state_path.write_text(json.dumps(st))
        proc = self.run_script("agent.py", "check")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("no program_status method", proc.stderr)


class ReadFleetBroadcastTests(FakeRexCase):
    def test_read_after_skips_a_hard_wrapped_echo(self):
        screen = ("banner\n❯ Summarize the open\n  PRs please\n\n\n\n⏺ Two PRs are open.\n\n"
                  "────\n❯ \n")
        self.fleet_with(reviewer={**agent("reviewer", 102), "screen": screen})
        proc = self.run_script("agent.py", "read", "reviewer", "--after", "Summarize the open PRs please")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(proc.stdout.startswith("⏺ Two PRs are open."), proc.stdout)
        self.assertNotIn("banner", proc.stdout)
        self.assertNotIn("\n\n\n", proc.stdout)

    def test_read_after_anchors_on_the_end_of_a_long_task(self):
        task = "Start of a long brief\n" + "\n".join(f"filler {i}" for i in range(30)) + "\nreply GOT-IT"
        screen = "filler 28\nfiller 29\nreply GOT-IT\n\n⏺ GOT-IT\n"
        self.fleet_with(reviewer={**agent("reviewer", 102), "screen": screen})
        proc = self.run_script("agent.py", "read", "reviewer", "--after", task)
        self.assertEqual((proc.returncode, proc.stdout.strip()), (0, "⏺ GOT-IT"))

    def test_read_turn_ignores_a_reply_that_repeats_the_task(self):
        screen = ("❯ propose a minimal test plan\n\n  (rex-agent turn ab12cd)\n\n⏺ Here is the plan.\n"
                  "  Want me to also propose a minimal test plan for grid.py?\n\n❯ \n")
        self.fleet_with(tests={**agent("tests", 102), "screen": screen})
        proc = self.run_script("agent.py", "read", "tests", "--turn", "ab12cd")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(proc.stdout.startswith("⏺ Here is the plan."), proc.stdout)
        self.assertIn("for grid.py?", proc.stdout)

    def test_read_after_missing_means_the_reply_scrolled_off(self):
        self.fleet_with(reviewer={**agent("reviewer", 102), "screen": "only the tail\n"})
        proc = self.run_script("agent.py", "read", "reviewer", "--after", "Summarize the open PRs")
        self.assertEqual(proc.returncode, 4)
        self.assertIn("file fallback", proc.stderr)

    def test_fleet_sorts_blocked_first_and_can_fail_on_it(self):
        self.fleet_with(a={}, b=agent("b", 103, state="blocked"), c=agent("c", 104, state="working"))
        proc = self.run_script("agent.py", "fleet", "--json", "--fail-on-blocked")
        self.assertEqual(proc.returncode, 3)
        rows = json.loads(proc.stdout)
        self.assertEqual([r["name"] for r in rows], ["b", "c", "a", "root"])
        self.assertEqual([r["role"] for r in rows], ["unknown", "unknown", "unknown", "root"])

    def test_dispatch_sends_each_target_its_own_task(self):
        ids = self.fleet_with(a={}, b={})
        st = self.state()
        for name in ("a", "b"):
            st["blocks"][ids[name]]["on_enter"] = [[[0.2, {"state": "working", "app": "claude-code"}],
                                                     [0.5, {"state": "done", "app": "claude-code"}]]]
        self.state_path.write_text(json.dumps(st))
        proc = self.run_script("agent.py", "dispatch", "-", "--timeout", "4", "--json",
                               stdin=json.dumps({"a": "review the diff", "b": "run the suite"}))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        results = {r["target"]: r for r in map(json.loads, proc.stdout.splitlines())}
        self.assertEqual({r["outcome"] for r in results.values()}, {"settled"})
        blocks = self.state()["blocks"]
        self.assertIn("review the diff", blocks[ids["a"]]["typed"][0])
        self.assertIn("run the suite", blocks[ids["b"]]["typed"][0])

    def test_broadcast_dedupes_and_skips_unsafe_targets(self):
        ids = self.fleet_with(a={}, b={}, busy=agent("busy", 104, state="working"))
        st = self.state()
        for name in ("a", "b"):
            st["blocks"][ids[name]]["on_enter"] = [[[0.2, {"state": "working", "app": "claude-code"}],
                                                     [0.5, {"state": "done", "app": "claude-code"}]]]
        self.state_path.write_text(json.dumps(st))
        start = time.monotonic()
        proc = self.run_script("agent.py", "broadcast", "pull main", "a", "b", "a", "busy", "ghost",
                               "--timeout", "4", "--activity-timeout", "1.5")
        self.assertLess(time.monotonic() - start, 6, "targets must run concurrently")
        self.assertEqual(proc.returncode, 1)
        lines = dict(line.split(": ", 1) for line in proc.stdout.strip().splitlines())
        self.assertRegex(lines["a"], r"^settled \(done\) · turn [0-9a-f]{6}$")
        self.assertRegex(lines["b"], r"^settled \(done\) · turn [0-9a-f]{6}$")
        self.assertEqual(lines["busy"], "working")
        self.assertTrue(lines["ghost"].startswith("error"))
        sent_to = sorted(c[c.index("-b") + 1] for c in self.calls("send"))
        self.assertEqual(sent_to, sorted([ids["a"], ids["b"]]))


class GridTests(FakeRexCase):
    def widths(self) -> list[float]:
        proc = subprocess.run(["rex", "session", "inspect", SESSION, "--json"], capture_output=True, text=True)
        layout = json.loads(proc.stdout)["windows"][0]["layers"][0]["layout"]

        def walk(node):
            if "split" in node:
                return walk(node["split"]["before"]) + walk(node["split"]["after"])
            return [(node["rect"][0], node["rect"][2])]
        return [w for _, w in sorted(walk(layout))]

    def test_plan_picks_the_rightmost_column(self):
        ids = self.fleet_with(a={}, b={})
        proc = self.run_script("grid.py", "plan")
        self.assertEqual(proc.stdout.strip(), ids["b"])

    def test_equalize_sets_exact_ratios_in_one_pass(self):
        for count in (2, 3, 4, 5):
            with self.subTest(columns=count):
                blocks = {ROOT: agent("root", 100)}
                ids = [ROOT] + [block_id(n) for n in range(2, count + 1)]
                for n, b in enumerate(ids[1:], start=2):
                    blocks[b] = agent(f"w{n}", 100 + n)
                self.write_state(blocks, row(*ids))
                proc = self.run_script("grid.py", "equalize")
                self.assertEqual(proc.returncode, 0, proc.stderr)
                for width in self.widths():
                    self.assertAlmostEqual(width, 1 / count, places=6)
                self.assertLessEqual(len([c for c in self.state()["log"] if c[:2] == ["api", "call"]]), count - 1)

    def test_equalize_handles_a_left_nested_tree(self):
        a, b = block_id(2), block_id(3)
        layout = {"split": {"split_id": "split:top", "direction": "horizontal", "ratio": 0.8,
                            "before": {"split": {"split_id": "split:in", "direction": "horizontal", "ratio": 0.3,
                                                 "before": {"block_id": ROOT}, "after": {"block_id": a}}},
                            "after": {"block_id": b}}}
        self.write_state({ROOT: agent("root", 100), a: agent("a", 102), b: agent("b", 103)}, layout)
        self.assertEqual(self.run_script("grid.py", "equalize").returncode, 0)
        for width in self.widths():
            self.assertAlmostEqual(width, 1 / 3, places=6)

    def test_a_stacked_pane_is_refused(self):
        a = block_id(2)
        layout = {"split": {"split_id": "split:v", "direction": "vertical", "ratio": 0.5,
                            "before": {"block_id": ROOT}, "after": {"block_id": a}}}
        self.write_state({ROOT: agent("root", 100), a: agent("a", 102)}, layout)
        proc = self.run_script("grid.py", "plan")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("not a single row", proc.stderr)


class LaunchProfileTests(FakeRexCase):
    def run_lp(self, *args: str, argv: list[str] | None = ("claude",)):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(launch_profile, "read_process_argv", lambda pid: list(argv) if argv else None), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = launch_profile.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_inherits_setup_flags_and_drops_session_flags(self):
        code, out, err = self.run_lp(argv=["claude", "--model", "opus", "--dangerously-skip-permissions",
                                           "--resume", "abc", "--mcp-config", "/tmp/m.json", "do this"])
        self.assertEqual(code, 0, err)
        profile = json.loads(out)
        self.assertEqual(profile["model"], {"value": "opus", "source": "root argv"})
        self.assertEqual(profile["flags"], ["--dangerously-skip-permissions", "--mcp-config"])
        self.assertIn("--resume", profile["dropped"])
        self.assertIn("⚠ permission bypass inherited from main: --dangerously-skip-permissions", err)
        self.assertNotIn("/tmp/m.json", err)

    def test_self_report_and_claude_effort_win_over_argv(self):
        os.environ["CLAUDE_EFFORT"] = "max"
        code, out, err = self.run_lp("--main-model", "claude-opus-5-5", argv=["claude", "--model", "haiku"])
        profile = json.loads(out)
        self.assertEqual(profile["model"], {"value": "claude-opus-5-5", "source": "self-report"})
        self.assertEqual(profile["thinking"], {"value": "max", "source": "env CLAUDE_EFFORT"})
        self.assertIn("differs from launch argv haiku", err)

    def test_another_kind_inherits_nothing(self):
        code, out, _ = self.run_lp("--kind", "codex", "--main-model", "claude-opus-5-5",
                                   argv=["claude", "--dangerously-skip-permissions"])
        profile = json.loads(out)
        self.assertEqual((code, profile["inherited"], profile["flags"]), (0, False, []))
        self.assertEqual(profile["model"]["source"], "not inherited")

    def test_unreadable_argv_fails_closed_unless_flags_are_waived(self):
        code, _, err = self.run_lp(argv=None)
        self.assertEqual(code, 1)
        self.assertIn("--without flags", err)
        code, out, err = self.run_lp("--without", "flags", argv=None)
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["flags_source"], "opted out")

    def test_remote_server_never_reads_local_argv(self):
        st = self.state()
        st["endpoint"] = "tcp://studio:7400"
        self.state_path.write_text(json.dumps(st))
        code, _, err = self.run_lp(argv=["claude"])
        self.assertEqual(code, 1)
        self.assertIn("remote", err)

    def test_start_runs_through_the_interactive_shell_and_waits_for_idle(self):
        st = self.state()
        st["blocks"][ROOT]["process"]["foreground"]["invoked_path"] = "/opt/bin/claude"
        st["blocks"][block_id(9)] = agent("reviewer", 109)
        st["windows"][0]["layout"] = row(ROOT, block_id(9))
        st["spawn"] = [[0.3, {"state": "idle", "app": "claude-code"}]]
        self.state_path.write_text(json.dumps(st))
        code, out, err = self.run_lp("--start", "tests", "--cwd", "/tmp", "--", "--effort", "low")
        self.assertEqual(code, 0, err)
        report = json.loads(out)
        self.assertEqual((report["name"], report["outcome"]), ("tests", "ready"))
        split = self.calls("split")[0]
        self.assertEqual(split[split.index("-b") + 1], block_id(9), "split from the rightmost column")
        self.assertIn("--keep-open", split)
        self.assertEqual(split[split.index("--label") + 1], "tests")
        self.assertEqual(split[split.index("--") + 1:],
                         ["/bin/zsh", "-ic", 'exec "$0" "$@"', "env", "REX_AGENT_ROLE=tests",
                          "/opt/bin/claude", "--effort", "low"])
        top = self.state()["windows"][0]["layout"]["split"]
        self.assertAlmostEqual(top["ratio"], 1 / 3)
        self.assertAlmostEqual(top["after"]["split"]["ratio"], 1 / 2)

    def test_a_dialog_at_boot_exits_3(self):
        st = self.state()
        st["spawn"] = [[0.3, {"state": "blocked", "kind": "question", "app": "claude-code", "msg": "Trust?"}]]
        self.state_path.write_text(json.dumps(st))
        code, out, err = self.run_lp("--start", "tests", "--timeout", "5")
        self.assertEqual(code, 3)
        self.assertIn("never answer it for them", err)

    def test_an_error_at_boot_fails_fast(self):
        st = self.state()
        st["spawn"] = [[0.2, {"state": "error", "app": "claude-code", "msg": "invalid API key"}]]
        self.state_path.write_text(json.dumps(st))
        start = time.monotonic()
        code, _, err = self.run_lp("--start", "tests", "--timeout", "20")
        self.assertEqual(code, 1)
        self.assertLess(time.monotonic() - start, 5)
        self.assertIn("invalid API key", err)

    def test_a_rejected_flag_fails_fast(self):
        st = self.state()
        st["spawn"] = [[0.2, {"exit": 1}]]
        self.state_path.write_text(json.dumps(st))
        start = time.monotonic()
        code, _, err = self.run_lp("--start", "tests", "--timeout", "20")
        self.assertEqual(code, 1)
        self.assertLess(time.monotonic() - start, 5)
        self.assertIn("its program exited", err)

    def test_name_collision_gets_a_suffix_and_bad_names_are_refused(self):
        st = self.state()
        st["blocks"][block_id(9)] = agent("tests", 109)
        st["windows"][0]["layout"] = row(ROOT, block_id(9))
        st["spawn"] = [[0.2, {"state": "idle", "app": "claude-code"}]]
        self.state_path.write_text(json.dumps(st))
        code, out, err = self.run_lp("--start", "tests")
        self.assertEqual(code, 0, err)
        self.assertRegex(json.loads(out)["name"], r"^tests-\d+$")
        code, _, err = self.run_lp("--start", "Bad Name")
        self.assertEqual(code, 2)


class DocCommandTests(unittest.TestCase):
    """Every `rex` command the docs teach must exist. herdr-agent once shipped an
    invented command whose fake made its tests pass; this guards against that."""

    KNOWN = {"new", "attach", "ls", "list", "run", "split", "do", "send", "send-key", "capture", "kill",
             "focus", "zoom", "move", "swap", "resize", "session", "window", "block", "client", "events",
             "wait", "api", "actions", "server", "config", "keymap", "whoami", "skill", "help", "version"}
    GROUPS = {"session": {"inspect", "ls", "list", "rename", "kill", "new"},
              "window": {"new", "ls", "list", "inspect", "focus", "move", "rename", "close"},
              "block": {"ls", "list", "inspect", "focus", "types", "send", "send-key", "capture", "zoom",
                        "move", "swap", "call", "rename", "close"},
              "api": {"list", "describe", "call"}, "client": {"ls", "list"}, "skill": {"show", "status"}}

    def doc_commands(self) -> list[list[str]]:
        """`rex …` invocations inside fenced blocks and inline code, never prose."""
        found = []
        for path in [SKILL / "SKILL.md", *sorted((SKILL / "references").glob("*.md"))]:
            text = path.read_text()
            code = re.findall(r"```[^\n]*\n(.*?)```", text, re.S)
            code += re.findall(r"`([^`\n]+)`", re.sub(r"```.*?```", "", text, flags=re.S))
            for segment in code:
                for match in re.finditer(r"(?:^|[\s(|;&])rex((?: +[^\s|;&)`]+)+)", segment, re.M):
                    words = match.group(1).split()
                    while words and words[0].startswith("-"):
                        words = words[2:] if words[0] in ("-S", "-C") else words[1:]
                    if words and re.match(r"^[a-z][a-z-]*$", words[0]):
                        found.append(words)
        return found

    def test_documented_subcommands_exist(self):
        commands = self.doc_commands()
        self.assertGreater(len(commands), 10)
        for words in commands:
            with self.subTest(command=" ".join(words[:2])):
                self.assertIn(words[0], self.KNOWN)
                if words[0] in self.GROUPS and len(words) > 1 and not words[1].startswith("-"):
                    self.assertIn(words[1], self.GROUPS[words[0]])

    @unittest.skipUnless(shutil.which("rex") and "fake" not in (shutil.which("rex") or ""),
                         "the real rex CLI is not on PATH")
    def test_documented_flags_exist_in_live_help(self):
        seen = set()
        for words in self.doc_commands():
            path = words[:2] if words[0] in self.GROUPS and len(words) > 1 and not words[1].startswith("-") else words[:1]
            flags = {w.split("=")[0] for w in words if w.startswith("--")}
            key = (tuple(path), tuple(sorted(flags)))
            if key in seen:
                continue
            seen.add(key)
            text = subprocess.run(["rex", *path, "--help"], capture_output=True, text=True).stdout
            for flag in flags:
                with self.subTest(command=" ".join(path), flag=flag):
                    self.assertIn(flag, text)


if __name__ == "__main__":
    unittest.main()
