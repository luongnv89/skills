#!/usr/bin/env python3
"""Tests for agent-profile's confined opencode `ask` and `edits` modes (#496).

Run: python3 meta/agent-profile/tests/test_opencode_confine.py
Standard library only; no opencode run happens (subprocess is stubbed). The fixtures are
trimmed `opencode debug agents --standalone` output from opencode 2.2.7: a clean repo
(ask, edits) and a repo-root opencode.json with allow-all agent rules, cwd in a subfolder.
"""
import contextlib
import copy
import importlib.util
import io
import json
import subprocess
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
spec = importlib.util.spec_from_file_location(
    "agent_profile", ROOT / "skills" / "agent-profile" / "scripts" / "agent_profile.py")
ap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ap)

OC = "/usr/local/bin/opencode"


def fixture(name):
    return json.loads((FIXTURES / name).read_text())


def build_of(data):
    return next(a for a in data if a["id"] == "build")


class FakePopen:
    """Stands in for the `opencode debug agents` process."""
    calls = []

    def __init__(self, out="", err="", code=0, hang=False):
        self.out, self.err, self.returncode, self.hang, self.pid = out, err, code, hang, 4242

    def __call__(self, argv, **kw):
        FakePopen.calls.append((argv, kw))
        return self

    def communicate(self, timeout=None):
        if self.hang and timeout is not None:
            raise subprocess.TimeoutExpired("opencode", timeout)
        return self.out, self.err


def verify(mode, popen, env_unset=(), env_set=None):
    """Run the verifier; return (exit code or None, stderr)."""
    FakePopen.calls = []
    err = io.StringIO()
    with mock.patch.object(ap.subprocess, "Popen", popen), contextlib.redirect_stderr(err):
        try:
            ap.verify_opencode_perms(OC, mode, "/repo/sub", list(env_unset), env_set or {}, timeout=5)
        except SystemExit as e:
            return e.code, err.getvalue()
    return None, err.getvalue()


def profile(mode):
    return {"name": f"oc-{mode}", "harness": "opencode", "model": "opencode/free-model",
            "permissions": mode, "scope": "global"}


@mock.patch.object(ap, "recheck", lambda p: [])
@mock.patch.object(ap.shutil, "which", lambda b: OC)
@mock.patch.object(ap, "checked_help", lambda path, a, cmd: "--agent string  Agent to use\n--auto\n")
class BuildTest(unittest.TestCase):

    def build(self, mode):
        with mock.patch.object(ap, "verify_opencode_perms") as v:
            out = ap.build(profile(mode), "/tmp/prompt.md", "/repo/sub")
        return out, v

    def check_confined(self, mode, allowed):
        (argv, stdin, env_unset, env_set, notes), v = self.build(mode)
        self.assertEqual(argv, [OC, "run", "--standalone", "--model", "opencode/free-model", "--agent", "build",
                                "--file", "/tmp/prompt.md", "--", ap.OPENCODE_MESSAGE])
        self.assertNotIn("--auto", argv)
        self.assertIsNone(stdin)
        self.assertEqual(env_unset, ["OPENCODE_CONFIG", "OPENCODE_CONFIG_DIR", "OPENCODE_CLI_CONFIG_CONTENT"])
        cfg = json.loads(env_set["OPENCODE_CONFIG_CONTENT"])
        self.assertEqual(list(cfg["permission"]), ["*", "read", "glob", "grep", "list"] + allowed)
        self.assertEqual(cfg["permission"]["*"], "deny")
        self.assertEqual(cfg["permission"]["read"],
                         {"*": "allow", "*.env": "deny", "*.env.*": "deny", "*.env.example": "allow"})
        self.assertEqual(cfg["agent"]["build"], {"mode": "primary", "hidden": False, "permission": cfg["permission"]})
        self.assertNotIn("shell", cfg["permission"])
        v.assert_called_once_with(OC, mode, "/repo/sub", env_unset, env_set)
        self.assertTrue(any("not checked" in n for n in notes))
        shown = ap.display(argv, stdin, "/tmp/prompt.md", env_unset, env_set)
        self.assertIn("env -u OPENCODE_CONFIG ", shown)
        self.assertIn("OPENCODE_CONFIG_CONTENT=", shown)

    def test_ask(self):
        self.check_confined("ask", [])

    def test_edits(self):
        self.check_confined("edits", ["edit"])

    def test_full_unchanged(self):
        (argv, stdin, env_unset, env_set, notes), v = self.build("full")
        self.assertEqual(argv, [OC, "run", "--standalone", "--model", "opencode/free-model", "--auto",
                                "--file", "/tmp/prompt.md", "--", ap.OPENCODE_MESSAGE])
        self.assertEqual((env_unset, env_set), ([], {}))
        v.assert_not_called()

    def test_confined_modes_are_offered(self):
        self.assertEqual(sorted(ap.ADAPTERS["opencode"]["permissions"]), ["ask", "edits", "full"])


class RowsTest(unittest.TestCase):

    def test_rows_match_real_resolved_order(self):
        # opencode 2.2.7 resolves the injected block verbatim: no reordering, no path expansion
        for mode, name in (("ask", "debug-agents-ask.json"), ("edits", "debug-agents-edits.json")):
            got = [(r["action"], r["resource"], r["effect"]) for r in build_of(fixture(name))["permissions"]]
            want = ap.opencode_rows(mode)
            self.assertEqual(want[0], ("*", "*", "deny"))
            self.assertEqual(got[-len(want) - 2:-2], want)  # then opencode's own deny rows


class VerifyTest(unittest.TestCase):

    def ok(self, mode, data):
        code, err = verify(mode, FakePopen(out=json.dumps(data)))
        self.assertIsNone(code, err)

    def refused(self, mode, popen, needle):
        code, err = verify(mode, popen)
        self.assertEqual(code, 1, err)
        self.assertIn(needle, err)
        self.assertIn(f"do not run this `{mode}` profile", err)

    def refused_data(self, mode, data, needle):
        self.refused(mode, FakePopen(out=json.dumps(data)), needle)

    def test_pass_on_real_output(self):
        self.ok("ask", fixture("debug-agents-ask.json"))
        self.ok("edits", fixture("debug-agents-edits.json"))

    def test_pass_with_repo_override_before_the_rules(self):
        self.ok("ask", fixture("debug-agents-ask-override.json"))

    def test_runs_with_the_run_env_and_cwd(self):
        env_set = {"OPENCODE_CONFIG_CONTENT": "{}"}
        with mock.patch.dict(ap.os.environ, {"OPENCODE_CONFIG": "/x.json", "KEEP": "1"}):
            verify("ask", FakePopen(out=json.dumps(fixture("debug-agents-ask.json"))),
                   env_unset=["OPENCODE_CONFIG"], env_set=env_set)
            want_env = ap.run_env("/repo/sub", ["OPENCODE_CONFIG"], env_set)
        argv, kw = FakePopen.calls[0]
        self.assertEqual(argv, [OC, "debug", "agents", "--standalone"])
        self.assertEqual(kw["cwd"], "/repo/sub")
        self.assertEqual(kw["env"], want_env)
        self.assertNotIn("OPENCODE_CONFIG", kw["env"])
        self.assertEqual((kw["env"]["PWD"], kw["env"]["KEEP"]), ("/repo/sub", "1"))
        self.assertTrue(kw["start_new_session"])

    def test_refuse_allow_rule_after_the_block(self):
        data = fixture("debug-agents-ask.json")
        build_of(data)["permissions"].append({"action": "shell", "resource": "*", "effect": "allow"})
        self.refused_data("ask", data, "rules after the `ask` rules")

    def test_refuse_ask_rule_after_the_block(self):
        data = fixture("debug-agents-ask.json")
        build_of(data)["permissions"].insert(-1, {"action": "edit", "resource": "*", "effect": "ask"})
        self.refused_data("ask", data, "rules after the `ask` rules")

    def test_refuse_when_block_missing(self):
        data = fixture("debug-agents-ask.json")
        perms = build_of(data)["permissions"]
        build_of(data)["permissions"] = [r for r in perms if r["action"] != "glob"]
        self.refused_data("ask", data, "rules after the `ask` rules")

    def test_refuse_edits_rules_for_ask(self):
        self.refused_data("ask", fixture("debug-agents-edits.json"), "rules after the `ask` rules")

    def test_refuse_build_not_primary(self):
        for key, value in (("mode", "subagent"), ("hidden", True)):
            data = fixture("debug-agents-ask.json")
            build_of(data)[key] = value
            self.refused_data("ask", data, "not a visible primary agent")

    def test_refuse_missing_build_agent(self):
        data = [a for a in fixture("debug-agents-ask.json") if a["id"] != "build"]
        self.refused_data("ask", data, "exactly one agent `build`")

    def test_refuse_unknown_shape(self):
        data = fixture("debug-agents-ask.json")
        bad = copy.deepcopy(data)
        del build_of(bad)["permissions"][0]["effect"]
        self.refused_data("ask", bad, "shape this script does not know")
        self.refused_data("ask", {"agents": data}, "not a list of agents")
        self.refused("ask", FakePopen(out="Error: something"), "not JSON")

    def test_refuse_nonzero_exit(self):
        self.refused("ask", FakePopen(err="boom", code=3), "exited 3: boom")

    def test_refuse_timeout_and_kill_server(self):
        with mock.patch.object(ap, "kill_group") as kill:
            self.refused("ask", FakePopen(hang=True), "did not answer within 5s")
        kill.assert_called_once_with(4242)

    def test_refuse_cannot_start(self):
        def boom(*a, **k):
            raise FileNotFoundError(2, "No such file or directory")
        self.refused("ask", boom, "cannot check opencode's resolved permissions")


if __name__ == "__main__":
    unittest.main(verbosity=2)
