"""Tests for the hc-agent scripts, run against tests/fake_hc.py and tests/fake_herdr_app.py.

    python3 -m unittest discover -s meta/hc-agent/tests -p 'test_*.py' -v

SAFETY: these tests run on machines where the real Herdr app is live. Every
script runs in an environment built from scratch: PATH is tests/bin plus the
system directories only, HOME and every hc/app path point into a temp dir, and
HC_TERMINAL_ID names a fake terminal. tests/bin/herdr is a tripwire that fails
any call to the Herdr TUI CLI. EnvGuardTests fails first if hc or herdr-app
could resolve anywhere else.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[2] / "skills" / "hc-agent"
SCRIPTS = SKILL / "scripts"
BIN = HERE / "bin"
SYSTEM_PATH = "/usr/bin:/bin:/usr/sbin:/sbin"
sys.path.insert(0, str(SCRIPTS))

import launch_profile  # noqa: E402

ROOT, ROOT_PANE = "t1", "p00000000000000000000000000000001"
SPACE, TAB = "sp00000000000000000000000000000001", "tb00000000000000000000000000000001"
OTHER_SPACE, OTHER_TAB = "sp00000000000000000000000000000002", "tb00000000000000000000000000000002"
PROJECT = "/work/project"
CLAUDE = "/opt/agents/bin/claude"


def term(addr: str, *, state: str | None = "idle", app: str = "claude-code", fg: list[str] | None = None,
         argv: list[str] | None = None, labels: dict | None = None, created: int = 1000,
         space: str = SPACE, tab: str = TAB, screen: str = "") -> dict:
    fg = [CLAUDE] if fg is None else fg
    return {
        "address": addr, "argv": argv or fg, "cols": 75, "created_ms": created, "cwd": PROJECT,
        "die_with_parent": False, "exit_code": None, "finished_ms": None,
        "foreground": {"argv": fg, "cwd": PROJECT, "name": "2.1.322", "pid": 4200000 + created},
        "identity": "ghostty", "keep": True,
        "labels": {"herdr.space": space, "herdr.tab": tab, "where": "project / 1", **(labels or {})},
        "name": None, "notify": True, "parent": None, "pid": 4200000 + created, "reason": None,
        "reported": True, "rm": False, "rows": 53, "screen": screen, "signal": None, "state": "live",
        "status": None if state is None else {"app": app, "msg": "", "state": state},
        "status_ms": 1000, "template": None, "title": "", "turn": 1,
    }


def worker(addr: str, name: str, **kw) -> dict:
    return term(addr, labels={"hc-agent.role": kw.pop("role", "worker"), "hc-agent.name": name,
                              "hc-agent.space": SPACE, "hc-agent.tab": TAB}, **kw)


class FakeAppCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hc-agent-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        (self.tmp / "home").mkdir()
        self.state_path = self.tmp / "state.json"
        self.tripwire = self.tmp / "herdr-calls"
        self.env = {
            "PATH": f"{BIN}{os.pathsep}{SYSTEM_PATH}",
            "HOME": str(self.tmp / "home"),
            "HC_TERMINAL_ID": ROOT,
            "HC_SCOPE": "hc-agent-test-scope",
            "HC_SESSION": "hc-agent-test",
            "HC_SOCKET": str(self.tmp / "no-core.sock"),
            "HC_TERMINAL_SOCKET": str(self.tmp / "no-terminal.sock"),
            "HERDR_APP_HOME": str(self.tmp / "app-home"),
            "XDG_CONFIG_HOME": str(self.tmp / "xdg-config"),
            "XDG_DATA_HOME": str(self.tmp / "xdg-data"),
            "XDG_STATE_HOME": str(self.tmp / "xdg-state"),
            "XDG_RUNTIME_DIR": str(self.tmp / "xdg-run"),
            "FAKE_HC_STATE": str(self.state_path),
            "FAKE_HC_PYTHON": sys.executable,
            "FAKE_HERDR_TRIPWIRE": str(self.tripwire),
            "LANG": "en_US.UTF-8",
        }
        self.write_state({ROOT: term(ROOT, state="working", argv=["mcc", "run", "--", "/issue-resolver 469"],
                                     fg=[CLAUDE, "/issue-resolver 469"])})

    def tearDown(self):
        calls = self.tripwire.read_text() if self.tripwire.exists() else ""
        self.assertEqual(calls, "", "hc-agent called the herdr TUI CLI")

    # --- state -------------------------------------------------------------

    def write_state(self, terminals: dict, *, extra_tab: dict | None = None, **extra) -> None:
        panes = {ROOT: ROOT_PANE}
        rows = []
        for n, addr in enumerate(terminals, start=1):
            pane = panes.get(addr) or f"p{n:032x}"
            rows.append({"terminal": addr, "pane": pane, "status": None, "app": None, "name": None,
                         "sub_agents": []})
        spaces = [{"id": SPACE, "name": "project", "folder": PROJECT, "machine": None, "active": True,
                   "tabs": [{"id": TAB, "name": "1", "active": True, "settled": False, "terminals": rows}]}]
        others = dict(extra_tab or {})
        if others:
            spaces.append({"id": OTHER_SPACE, "name": "elsewhere", "folder": "/work/other", "machine": None,
                           "active": False, "tabs": [{"id": OTHER_TAB, "name": "1", "active": True,
                                                      "settled": False, "terminals": [
                               {"terminal": a, "pane": f"q{i:032x}", "status": None, "app": None, "name": None,
                                "sub_agents": []} for i, a in enumerate(others, start=1)]}]})
        state = {"terminals": {**terminals, **others},
                 "app": {"spaces": spaces, "recent": []},
                 "status": {"zoom": 1.0, "space": SPACE, "tab": TAB, "focused_pane": ROOT_PANE,
                            "layout": "default", "agent": ROOT, "floats": {}, "overlays": [], "errors": []},
                 "pending": [], "on_send": {}, "spawn": [], "log": [], "next": 0x40, **extra}
        self.state_path.write_text(json.dumps(state))

    def state(self) -> dict:
        return json.loads(self.state_path.read_text())

    def update(self, fn) -> None:
        st = self.state()
        fn(st)
        self.state_path.write_text(json.dumps(st))

    def pane(self, addr: str) -> str:
        for space in self.state()["app"]["spaces"]:
            for tab in space["tabs"]:
                for t in tab["terminals"]:
                    if t["terminal"] == addr:
                        return t["pane"]
        raise KeyError(addr)

    def log(self, tool: str | None = None) -> list[list[str]]:
        return [c for c in self.state()["log"] if tool is None or c[0] == tool]

    def run_script(self, script: str, *args: str, stdin: str | None = None, env: dict | None = None):
        return subprocess.run([sys.executable, str(SCRIPTS / script), *args], input=stdin, capture_output=True,
                              text=True, timeout=60, env=env or self.env)

    def assert_no_forbidden_calls(self) -> None:
        for call in self.log():
            text = " ".join(call)
            self.assertNotIn("terminal.open", text)
            self.assertNotIn("terminal.keep", text)
            self.assertFalse(call[:2] == ["hc", "run"], text)
            self.assertNotEqual(call, ["herdr-app"], "bare herdr-app opens the window")


class EnvGuardTests(FakeAppCase):
    def test_tools_resolve_only_to_the_fakes(self):
        for tool in ("hc", "herdr-app", "herdr"):
            found = shutil.which(tool, path=self.env["PATH"])
            self.assertIsNotNone(found, tool)
            self.assertEqual(Path(found).resolve().parent, BIN.resolve(), f"{tool} resolved to {found}")
        for key, value in self.env.items():
            if key.endswith(("SOCKET", "HOME", "_DIR")) and key != "PATH":
                self.assertTrue(value.startswith(str(self.tmp)), f"{key}={value} escapes the temp dir")
        self.assertEqual(self.env["PATH"].split(os.pathsep), [str(BIN), *SYSTEM_PATH.split(":")])
        self.assertNotIn("HERDR_ENV", self.env)

    def test_shims_are_executable(self):
        for tool in ("hc", "herdr-app", "herdr"):
            self.assertTrue(os.access(BIN / tool, os.X_OK), tool)


class CheckTests(FakeAppCase):
    def test_check_reports_terminal_pane_and_tab(self):
        proc = self.run_script("agent.py", "check")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual((out["terminal"], out["pane"], out["space"], out["tab"]), (ROOT, ROOT_PANE, SPACE, TAB))
        self.assertEqual((out["kind"], out["cwd"]), ("claude", PROJECT))
        self.assertEqual({c[0] for c in self.log()}, {"hc", "herdr-app"})

    def test_herdr_env_routes_to_herdr_agent(self):
        proc = self.run_script("agent.py", "check", env={**self.env, "HERDR_ENV": "1"})
        self.assertEqual(proc.returncode, 1)
        self.assertIn("herdr-agent", proc.stderr)
        self.assertEqual(self.log(), [])

    def test_missing_terminal_id_is_blocked(self):
        env = {k: v for k, v in self.env.items() if k != "HC_TERMINAL_ID"}
        proc = self.run_script("agent.py", "check", env=env)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("HC_TERMINAL_ID is unset", proc.stderr)

    def test_terminal_without_window_labels_is_blocked(self):
        self.update(lambda st: st["terminals"][ROOT]["labels"].pop("herdr.tab"))
        proc = self.run_script("agent.py", "check")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("herdr.space/herdr.tab", proc.stderr)

    def test_missing_tools_are_named(self):
        proc = self.run_script("agent.py", "check", env={**self.env, "PATH": SYSTEM_PATH})
        self.assertEqual(proc.returncode, 1)
        self.assertIn("hc and herdr-app not on PATH", proc.stderr)


class PromptTests(FakeAppCase):
    def fleet(self, **workers: dict) -> dict:
        terms = {ROOT: self.state()["terminals"][ROOT]}
        for n, (name, spec) in enumerate(workers.items(), start=2):
            terms[f"t{n}"] = worker(f"t{n}", name, created=1000 + n, **spec)
        self.write_state(terms)
        return {name: f"t{n}" for n, name in enumerate(workers, start=2)}

    def on_send(self, addr: str, *steps) -> None:
        self.update(lambda st: st["on_send"].setdefault(addr, []).append([list(s) for s in steps]))

    def prompt(self, target: str, text: str = "Summarize the open PRs", *extra: str):
        proc = self.run_script("agent.py", "prompt", target, text, "--activity-timeout", "1.5", "--timeout", "4",
                               *extra)
        return proc, (json.loads(proc.stdout) if proc.stdout.strip() else {})

    def sends(self) -> list[list[str]]:
        return [c for c in self.log("hc") if c[1:2] == ["send"]]

    def test_idle_target_settles_after_working_then_done(self):
        ids = self.fleet(reviewer={})
        self.on_send(ids["reviewer"], (0.2, {"app": "claude-code", "state": "working", "msg": ""}),
                     (0.6, {"app": "claude-code", "state": "done", "msg": ""}, "Two open PRs.\n"))
        proc, out = self.prompt("reviewer")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual((out["outcome"], out["terminal"], out["sent"]), ("settled", ids["reviewer"], True))
        send = self.sends()[0]
        self.assertEqual(send[:6], ["hc", "send", "--json", "--if", "idle", "--"])
        self.assertEqual(send[6], ids["reviewer"], "hc must get the address, never the label name")
        self.assertTrue(send[7].endswith(f"(hc-agent turn {out['turn']})"))
        self.assert_no_forbidden_calls()

    def test_done_target_is_sent_without_the_idle_guard(self):
        ids = self.fleet(reviewer={"state": "done"})
        self.on_send(ids["reviewer"], (0.2, {"app": "claude-code", "state": "working"}),
                     (0.5, {"app": "claude-code", "state": "done"}))
        proc, out = self.prompt("reviewer")
        self.assertEqual(out["outcome"], "settled", proc.stderr)
        self.assertNotIn("--if", self.sends()[0])

    def test_a_missed_working_still_settles_when_the_turn_moves(self):
        ids = self.fleet(reviewer={})

        def idle_with_new_turn(st):
            st["on_send"][ids["reviewer"]] = [[[0.3, {"app": "claude-code", "state": "working"}],
                                               [0.3, {"app": "claude-code", "state": "idle"}]]]
        self.update(idle_with_new_turn)
        proc, out = self.prompt("reviewer")
        self.assertEqual(out["outcome"], "settled", proc.stderr)

    def test_unsafe_targets_are_refused_before_any_send(self):
        cases = {"busy": ({"state": "working"}, "working", 6), "dialog": ({"state": "blocked"}, "blocked", 3),
                 "silent": ({"state": None}, "unverifiable", 4),
                 "shell": ({"state": None, "fg": ["/bin/zsh", "-l"]}, "no_agent", 5),
                 "stale": ({"state": "done", "fg": ["/bin/zsh"]}, "unverifiable", 4)}
        self.fleet(**{name: spec for name, (spec, _, _) in cases.items()})
        for name, (_, outcome, code) in cases.items():
            with self.subTest(target=name):
                proc, out = self.prompt(name)
                self.assertEqual((proc.returncode, out["outcome"], out["sent"]), (code, outcome, False))
        self.assertEqual(self.sends(), [])

    def test_status_change_at_send_is_refused_by_hc(self):
        ids = self.fleet(reviewer={})
        self.update(lambda st: st.update(flip_after_get={ids["reviewer"]: [1, {"app": "claude-code",
                                                                                "state": "working"}]}))
        proc, out = self.prompt("reviewer")
        self.assertEqual((proc.returncode, out["outcome"], out["sent"]), (6, "working", False), proc.stderr)
        self.assertEqual(len(self.sends()), 1, "hc's own --if idle check refused the send")
        self.assertNotIn("> Summarize", self.state()["terminals"][ids["reviewer"]]["screen"])

    def test_own_terminal_is_refused(self):
        self.fleet(reviewer={})
        proc, _ = self.prompt(ROOT)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("your own terminal", proc.stderr)
        self.assertEqual(self.sends(), [])

    def test_terminal_outside_the_root_tab_is_never_targeted(self):
        terms = {ROOT: self.state()["terminals"][ROOT]}
        self.write_state(terms, extra_tab={"t9": worker("t9", "reviewer", space=OTHER_SPACE, tab=OTHER_TAB)})
        # t9 even carries this tab's hc-agent.tab label: membership comes from herdr-app ls, not labels
        for target in ("reviewer", "t9"):
            with self.subTest(target=target):
                proc, _ = self.prompt(target)
                self.assertEqual(proc.returncode, 1)
                self.assertIn(f"no terminal named or addressed '{target}' in the root's tab", proc.stderr)
        self.assertEqual(self.sends(), [])

    def test_ambiguous_name_is_refused(self):
        terms = {ROOT: self.state()["terminals"][ROOT], "t2": worker("t2", "dup"), "t3": worker("t3", "dup")}
        self.write_state(terms)
        proc, _ = self.prompt("dup")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("names 2 terminals", proc.stderr)

    def test_leading_bang_refused_unless_raw_and_controls_stripped(self):
        ids = self.fleet(reviewer={})
        proc, _ = self.prompt("reviewer", "!rm -rf build")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("starts with '!'", proc.stderr)
        self.on_send(ids["reviewer"], (0.1, {"app": "claude-code", "state": "working"}),
                     (0.3, {"app": "claude-code", "state": "done"}))
        proc, out = self.prompt("reviewer", "hello\x1b[201~ world")
        self.assertEqual(out["outcome"], "settled", proc.stderr)
        self.assertNotIn("\x1b", self.sends()[0][7])

    def test_a_task_starting_with_a_dash_stays_text(self):
        ids = self.fleet(reviewer={})
        self.on_send(ids["reviewer"], (0.1, {"app": "claude-code", "state": "working"}),
                     (0.3, {"app": "claude-code", "state": "done"}))
        proc, out = self.prompt("reviewer", "--help me read this")
        self.assertEqual(out["outcome"], "settled", proc.stderr)
        self.assertTrue(self.sends()[0][7].startswith("--help me"))

    def test_outcomes_after_send(self):
        cases = [
            ("blocked", [(0.2, {"app": "claude-code", "state": "blocked", "msg": "approve Bash"})], 3),
            ("stalled", [], 7),
            ("timeout", [(0.2, {"app": "claude-code", "state": "working"})], 8),
            ("unverifiable", [(0.2, {"app": "claude-code", "state": "working"}), (0.5, None)], 4),
            ("exited", [(0.2, {"app": "claude-code", "state": "working"}), (0.5, "finish")], 9),
        ]
        for outcome, steps, code in cases:
            with self.subTest(outcome=outcome):
                ids = self.fleet(reviewer={})
                self.on_send(ids["reviewer"], *steps)
                proc, out = self.prompt("reviewer")
                self.assertEqual((proc.returncode, out["outcome"], out["sent"]), (code, outcome, True), proc.stderr)

    def test_prompt_text_from_stdin(self):
        ids = self.fleet(reviewer={})
        self.on_send(ids["reviewer"], (0.1, {"app": "claude-code", "state": "working"}),
                     (0.3, {"app": "claude-code", "state": "done"}))
        proc = self.run_script("agent.py", "prompt", "reviewer", "-", "--activity-timeout", "1.5", "--timeout", "4",
                               stdin="line one\nline $HOME `two`\n")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("line $HOME `two`", self.sends()[0][7])

    def test_read_turn_anchors_on_the_tag(self):
        ids = self.fleet(reviewer={})
        self.on_send(ids["reviewer"], (0.1, {"app": "claude-code", "state": "working"}),
                     (0.3, {"app": "claude-code", "state": "done"},
                      "Answer line 1\n(hc-agent turn ffffff) quoted\nAnswer line 2\n"))
        _, out = self.prompt("reviewer", "Repeat after me")
        proc = self.run_script("agent.py", "read", "reviewer", "--turn", out["turn"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(proc.stdout.startswith("Answer line 1"), proc.stdout)
        self.assertNotIn("Repeat after me", proc.stdout)
        self.assertIn(["hc", "read", ids["reviewer"], "--lines", "400"], self.log("hc"))
        proc = self.run_script("agent.py", "read", "reviewer", "--turn", "000000")
        self.assertEqual(proc.returncode, 4)

    def test_wait_until_blocked(self):
        ids = self.fleet(reviewer={"state": "working"})
        self.update(lambda st: st["pending"].append(
            {"addr": ids["reviewer"], "at": __import__("time").time() + 0.3,
             "status": {"app": "claude-code", "state": "blocked"}}))
        proc = self.run_script("agent.py", "wait", "reviewer", "--until", "blocked", "--timeout", "4")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["outcome"], "blocked")
        self.assertTrue(any(c[1:2] == ["wait"] for c in self.log("hc")), "a working target blocks in hc wait")


class FleetTests(PromptTests):
    def test_fleet_lists_only_the_root_tab_with_roles(self):
        terms = {ROOT: self.state()["terminals"][ROOT], "t2": worker("t2", "reviewer", state="blocked"),
                 "t3": worker("t3", "tests", state="done"), "t4": term("t4", state=None, fg=["/bin/zsh"]),
                 "t5": worker("t5", "main-g2", role="main")}
        self.write_state(terms, extra_tab={"t9": worker("t9", "far", space=OTHER_SPACE, tab=OTHER_TAB)})
        proc = self.run_script("agent.py", "fleet", "--json", "--fail-on-blocked")
        self.assertEqual(proc.returncode, 3, proc.stderr)
        rows = json.loads(proc.stdout)
        self.assertEqual([(r["terminal"], r["role"], r["status"]) for r in rows],
                         [("t2", "worker", "blocked"), ("t3", "worker", "done"), ("t5", "main", "idle"),
                          ("t4", "other", "no-agent"), (ROOT, "root", "working")])
        proc = self.run_script("agent.py", "fleet")
        self.assertIn("Fleet: 2 worker(s): 1 blocked, 1 done", proc.stdout)

    def test_broadcast_dedupes_and_skips_unsafe_targets(self):
        ids = self.fleet(reviewer={}, tests={}, busy={"state": "working"})
        for name in ("reviewer", "tests"):
            self.on_send(ids[name], (0.1, {"app": "claude-code", "state": "working"}),
                         (0.4, {"app": "claude-code", "state": "done"}))
        proc = self.run_script("agent.py", "broadcast", "pull main", "reviewer", ids["reviewer"], "tests", "busy",
                               "ghost", "--json", "--activity-timeout", "1.5", "--timeout", "4")
        results = {r["target"]: r for r in map(json.loads, proc.stdout.splitlines())}
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(results["reviewer"]["outcome"], "settled")
        self.assertEqual(results["tests"]["outcome"], "settled")
        self.assertEqual(results["busy"]["outcome"], "working")
        self.assertEqual(results["ghost"]["outcome"], "error")
        self.assertNotIn(ids["reviewer"], results, "the same terminal is prompted once")
        self.assertEqual(len(self.sends()), 2)

    def test_dispatch_sends_each_target_its_own_task(self):
        ids = self.fleet(reviewer={}, tests={})
        for name in ids:
            self.on_send(ids[name], (0.1, {"app": "claude-code", "state": "working"}),
                         (0.3, {"app": "claude-code", "state": "done"}))
        proc = self.run_script("agent.py", "dispatch", "-", "--activity-timeout", "1.5", "--timeout", "4",
                               stdin=json.dumps({"reviewer": "review it", "tests": "test it"}))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        texts = {c[6]: c[7] for c in self.sends()}
        self.assertTrue(texts[ids["reviewer"]].startswith("review it"))
        self.assertTrue(texts[ids["tests"]].startswith("test it"))

    def test_focus_uses_agent_focus_with_the_address(self):
        ids = self.fleet(reviewer={})
        proc = self.run_script("agent.py", "focus", "reviewer")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(["herdr-app", "do", "agent.focus", "--terminal", ids["reviewer"]], self.log("herdr-app"))
        self.assertEqual(self.state()["status"]["focused_pane"], self.pane(ids["reviewer"]))

    def test_close_needs_confirmation_and_closes_only_workers(self):
        terms = {ROOT: self.state()["terminals"][ROOT], "t2": worker("t2", "reviewer"),
                 "t3": term("t3", state="idle"), "t4": worker("t4", "main-g2", role="main")}
        self.write_state(terms)
        proc = self.run_script("agent.py", "close", "reviewer")
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(self.log(), [])
        reviewer_pane = self.pane("t2")
        proc = self.run_script("agent.py", "close", "reviewer", "t3", "main-g2", ROOT, "--confirmed")
        results = {r["target"]: r["outcome"] for r in map(json.loads, proc.stdout.splitlines())}
        self.assertEqual(results, {"reviewer": "closed", "t3": "refused", "main-g2": "refused", ROOT: "refused"})
        closes = [c for c in self.log("herdr-app") if c[2:3] == ["pane.close"]]
        self.assertEqual(closes, [["herdr-app", "do", "pane.close", "--pane", reviewer_pane]])
        self.assertEqual(self.state()["terminals"]["t2"]["state"], "finished")


class LaunchProfileUnitTests(unittest.TestCase):
    """Pure functions only: nothing here starts a process."""

    SPEC = launch_profile.KINDS["claude"]

    def test_direct_launch_strips_the_root_prompt(self):
        rec = term(ROOT, argv=[CLAUDE, "--model", "opus", "/issue-resolver 469"],
                   fg=[CLAUDE, "--model", "opus", "/issue-resolver 469"])
        launch, err, _ = launch_profile.read_launch(rec, self.SPEC, False)
        self.assertEqual((launch["mode"], launch["prefix"], err), ("direct", [CLAUDE], ""))
        groups, dropped = launch_profile.parse_groups(self.SPEC, launch["tail"], strict=True)
        self.assertEqual([t for g in groups for t in g["tokens"]], ["--model", "opus"])
        self.assertEqual(dropped, ["1 positional"])

    def test_wrapper_prefix_is_kept_and_its_tail_parsed(self):
        rec = term(ROOT, argv=["mcc", "run", "--", "--permission-mode", "plan", "/issue-resolver 469"],
                   fg=[CLAUDE, "--settings", "/injected.json", "--permission-mode", "plan", "/issue-resolver 469"])
        launch, err, _ = launch_profile.read_launch(rec, self.SPEC, False)
        self.assertEqual((launch["mode"], launch["prefix"], err), ("wrapper", ["mcc", "run", "--"], ""))
        self.assertEqual(launch["tail"], ["--permission-mode", "plan", "/issue-resolver 469"])

    def test_wrapper_without_separator_fails_closed_unless_dropped(self):
        rec = term(ROOT, argv=["mcc", "claude"], fg=[CLAUDE])
        launch, err, _ = launch_profile.read_launch(rec, self.SPEC, False)
        self.assertIsNone(launch)
        self.assertTrue(err.startswith(launch_profile.WRAPPER_ERR))
        launch, err, warning = launch_profile.read_launch(rec, self.SPEC, True)
        self.assertEqual(launch["prefix"], [CLAUDE])
        self.assertIn("another account", warning)

    def test_agent_typed_at_a_shell_is_direct(self):
        rec = term(ROOT, argv=["/bin/zsh", "-l"], fg=["node", "/opt/agents/claude.js", "--effort", "max"])
        launch, _, _ = launch_profile.read_launch(rec, self.SPEC, False)
        self.assertEqual((launch["mode"], launch["prefix"], launch["tail"]),
                         ("direct", ["node", "/opt/agents/claude.js"], ["--effort", "max"]))


class LaunchProfileTests(FakeAppCase):
    def run_lp(self, *args: str, env: dict | None = None):
        proc = self.run_script("launch_profile.py", *args, env=env)
        return proc.returncode, proc.stdout, proc.stderr

    def split_calls(self) -> list[list[str]]:
        return [c for c in self.log("herdr-app") if c[1:3] == ["do", "pane.split"]]

    def test_profile_inherits_wrapper_flags_but_never_the_root_prompt(self):
        self.update(lambda st: st["terminals"][ROOT].update(
            argv=["mcc", "run", "--", "--dangerously-skip-permissions", "--resume", "abc", "/issue-resolver 469"]))
        code, out, err = self.run_lp("--main-model", "claude-opus-5-5", "--main-thinking", "max")
        self.assertEqual(code, 0, err)
        profile = json.loads(out)
        self.assertEqual((profile["kind"], profile["launch"]), ("claude", {"mode": "wrapper", "via": "mcc"}))
        self.assertEqual(profile["flags"], ["--dangerously-skip-permissions"])
        self.assertIn("--resume", profile["dropped"])
        self.assertIn("⚠ permission bypass inherited", err)
        self.assertEqual(self.split_calls(), [])

    def test_another_kind_inherits_nothing(self):
        code, out, err = self.run_lp("--kind", "codex", "--main-model", "claude-opus-5-5")
        self.assertEqual(code, 0, err)
        profile = json.loads(out)
        self.assertEqual((profile["inherited"], profile["model"]["value"], profile["launch"]["mode"]),
                         (False, "", "bare"))

    def test_claude_effort_is_read_inside_the_root_terminal(self):
        code, out, err = self.run_lp(env={**self.env, "CLAUDE_EFFORT": "max"})
        self.assertEqual(json.loads(out)["thinking"], {"value": "max", "source": "env CLAUDE_EFFORT"}, err)

    def start(self, *extra: str, spawn=((0.2, {"app": "claude-code", "state": "idle"}),)):
        self.update(lambda st: st.update(spawn=[list(s) for s in spawn]))
        return self.run_lp("--main-model", "claude-opus-5-5", "--start", "reviewer", "--timeout", "3", *extra)

    def test_start_splits_explicitly_labels_restores_focus_and_waits(self):
        self.update(lambda st: st["status"].update(focused_pane="pelsewhere"))
        self.update(lambda st: st["app"]["spaces"][0]["tabs"][0]["terminals"].append(
            {"terminal": "t7", "pane": "pelsewhere", "status": None, "app": None, "name": None, "sub_agents": []}))
        self.update(lambda st: st["terminals"].update(t7=term("t7", state=None, fg=["/bin/zsh"])))
        code, out, err = self.start()
        self.assertEqual(code, 0, err)
        report = json.loads(out)
        self.assertEqual((report["outcome"], report["focus_restored"], report["cwd"]), ("ready", True, PROJECT))
        split = self.split_calls()
        self.assertEqual(len(split), 1)
        self.assertEqual(split[0][3:7], ["--direction", "right", "--pane", ROOT_PANE])
        argv = json.loads(split[0][split[0].index("--argv") + 1])
        self.assertEqual(argv[:4], ["/bin/sh", "-c", 'cd "$0" && exec "$@"', PROJECT])
        self.assertEqual(argv[4:7], ["mcc", "run", "--"])
        self.assertNotIn("/issue-resolver 469", argv)
        self.assertEqual(argv[-2:], ["--model", "claude-opus-5-5"])
        new = report["terminal"]
        calls = self.log()
        i_split = calls.index(split[0])
        self.assertEqual(calls[i_split + 1][:3], ["hc", "label", new])
        self.assertIn("hc-agent.role=worker", calls[i_split + 1])
        self.assertIn("hc-agent.name=reviewer", calls[i_split + 1])
        self.assertIn(f"hc-agent.tab={TAB}", calls[i_split + 1])
        self.assertEqual(calls[i_split + 2], ["herdr-app", "do", "pane.focus", "--pane", "pelsewhere"])
        self.assertEqual(self.state()["status"]["focused_pane"], "pelsewhere")
        self.assert_no_forbidden_calls()

    def test_second_worker_splits_the_newest_worker_pane(self):
        self.update(lambda st: st["app"]["spaces"][0]["tabs"][0]["terminals"].append(
            {"terminal": "t3", "pane": "pworker3", "status": None, "app": None, "name": None, "sub_agents": []}))
        self.update(lambda st: st["terminals"].update(t3=worker("t3", "first", created=5000)))
        code, _, err = self.start()
        self.assertEqual(code, 0, err)
        self.assertEqual(self.split_calls()[0][5:7], ["--pane", "pworker3"])

    def test_focus_is_restored_even_when_labeling_fails(self):
        self.update(lambda st: st.update(label_fails=True))
        code, _, err = self.start()
        self.assertEqual(code, 1)
        self.assertIn("is an orphan", err)
        calls = self.log()
        i_split = calls.index(self.split_calls()[0])
        self.assertEqual(calls[i_split + 2], ["herdr-app", "do", "pane.focus", "--pane", ROOT_PANE])
        self.assertEqual(self.state()["status"]["focused_pane"], ROOT_PANE)
        self.assertFalse(any(c[1:2] == ["send"] for c in self.log("hc")))

    def test_dialog_at_boot_exits_3_and_timeout_names_the_orphan(self):
        code, _, err = self.start(spawn=((0.2, {"app": "claude-code", "state": "blocked", "msg": "trust?"}),))
        self.assertEqual(code, 3, err)
        self.assertIn("never answer it", err)
        self.update(lambda st: st.update(spawn=[]))
        code, _, err = self.run_lp("--start", "tests", "--timeout", "1")
        self.assertEqual(code, 1)
        self.assertIn("is an orphan", err)

    def test_name_rules(self):
        self.update(lambda st: st["app"]["spaces"][0]["tabs"][0]["terminals"].append(
            {"terminal": "t3", "pane": "pworker3", "status": None, "app": None, "name": None, "sub_agents": []}))
        self.update(lambda st: st["terminals"].update(t3=worker("t3", "reviewer")))
        code, out, err = self.start()
        self.assertEqual(code, 0, err)
        self.assertRegex(json.loads(out)["name"], r"^reviewer-\d+$")
        for bad in ("Bad Name", "t2x"):
            with self.subTest(name=bad):
                code, _, _ = self.run_lp("--start", bad)
                self.assertEqual(code, 2)

    def test_split_failure_still_restores_focus(self):
        self.update(lambda st: st.update(split_fails=True))
        code, _, err = self.start()
        self.assertEqual(code, 1)
        self.assertIn("split refused", err)
        self.assertEqual(self.log("herdr-app")[-2][:5], ["herdr-app", "do", "pane.focus", "--pane", ROOT_PANE])


class DocCommandTests(unittest.TestCase):
    """Every hc / herdr-app command the docs teach must exist, and no doc may drive the TUI `herdr` CLI.
    herdr-agent once shipped an invented command whose fake made its tests pass."""

    HC = {"get", "ls", "read", "send", "keys", "interrupt", "wait", "kill", "rm", "label", "attach", "run",
          "server"}

    def code_segments(self, fenced_only: bool = False) -> list[str]:
        found = []
        for path in [SKILL / "SKILL.md", *sorted((SKILL / "references").glob("*.md"))]:
            text = path.read_text()
            found += [body for lang, body in re.findall(r"```([^\n]*)\n(.*?)```", text, re.S)
                      if lang.strip() != "text"]  # ```text blocks are prose: help text, reports
            if not fenced_only:
                found += re.findall(r"`([^`\n]+)`", re.sub(r"```.*?```", "", text, flags=re.S))
        return found

    def test_documented_commands_exist(self):
        sys.path.insert(0, str(HERE))
        from fake_herdr_app import COMMANDS
        hc_seen = app_seen = 0
        for segment in self.code_segments():
            for m in re.finditer(r"(?:^|[\s(|;&$\"'])hc +([a-z][a-z-]*)", segment, re.M):
                if m.group(1) == "herdr-app":  # `command -v hc herdr-app`
                    continue
                hc_seen += 1
                self.assertIn(m.group(1), self.HC, segment)
            for m in re.finditer(r"herdr-app +do +([a-z_.]+)", segment):
                app_seen += 1
                self.assertIn(m.group(1), COMMANDS, segment)
                self.assertNotIn(m.group(1), ("terminal.open", "terminal.keep"), segment)
        self.assertGreater(hc_seen, 5)
        self.assertGreater(app_seen, 3)

    def test_no_runnable_block_calls_the_tui_cli_or_hc_run(self):
        """Prose may name `herdr …` to compare or forbid it; no fenced block may run it."""
        for segment in self.code_segments(fenced_only=True):
            self.assertIsNone(re.search(r"(?:^|[\s;&|(])herdr +(?!-app)[a-z]", segment, re.M), segment)
            self.assertIsNone(re.search(r"(?:^|[\s;&|(])hc +run\b", segment, re.M), segment)


if __name__ == "__main__":
    unittest.main()
