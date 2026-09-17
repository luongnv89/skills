#!/usr/bin/env python3
"""Behavioral tests for launch_profile.py against a fake `herdr` CLI.

A worker mirrors the main agent by default: same harness kind, model, thinking
level and setup flags. The two failure modes that matter are a spawn that
refuses to start when the main agent's model is UNKNOWN, and a Claude model id
or effort handed to a worker of a different kind. Both are pinned here, along
with argv filtering: session, prompt and credential tokens must never reach a
worker or the printed profile.

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
PROFILE = SCRIPTS / "launch_profile.py"

ROOT = "w1:p1"
WORKER = "w1:p2"


class FakeHerdrHarness:
    def __init__(self):
        self.tmpdir = tempfile.mkdtemp(prefix="hac_profile_test_")
        self.state_path = os.path.join(self.tmpdir, "state.json")
        self.write_state({"panes": {}})
        self.env = dict(os.environ)
        # The suite may itself run inside a Claude Code pane: never let the
        # host's own effort or pane id leak into a test.
        for var in ("CLAUDE_EFFORT", "HERDR_PANE_ID"):
            self.env.pop(var, None)
        self.env["FAKE_HERDR_STATE"] = self.state_path
        self.env["PATH"] = f"{FAKE_BIN}{os.pathsep}{self.env.get('PATH', '')}"

    def write_state(self, state):
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(state, f)

    def read_state(self):
        with open(self.state_path, encoding="utf-8") as f:
            return json.load(f)

    def set_pane(self, pane_id, **fields):
        state = self.read_state()
        pane = {"agent_status": "idle", "text": "", "name": None}
        pane.update(fields)
        state["panes"][pane_id] = pane
        self.write_state(state)

    def set_root(self, kind="claude", processes=None, **fields):
        self.set_pane(ROOT, kind=kind, name="main", processes=processes or [], **fields)

    def run(self, args, extra_env=None, timeout=15):
        env = dict(self.env)
        env.update(extra_env or {})
        return subprocess.run(
            [sys.executable, str(PROFILE), "--root-pane", ROOT, *args],
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
        )


class LaunchProfileTests(unittest.TestCase):
    def setUp(self):
        self.h = FakeHerdrHarness()

    def resolve(self, *args, extra_env=None):
        res = self.h.run(list(args), extra_env)
        self.assertEqual(res.returncode, 0, res.stderr)
        return json.loads(res.stdout), res.stderr

    def start(self, *args, extra_env=None):
        """Run --start into a fresh worker pane; return (result, launched pane)."""
        self.h.set_pane(WORKER, agent_status="unknown", no_agent=True)
        res = self.h.run(["--start", "worker", "--pane", WORKER, *args], extra_env)
        return res, self.h.read_state()["panes"][WORKER]

    def test_bare_claude_main_mirrors_self_reported_model_and_env_effort(self):
        # The live shape: argv is bare `claude`, the model lives only in the
        # agent's own knowledge, the effort only in CLAUDE_EFFORT.
        self.h.set_root(processes=[["caffeinate", "-i", "-t", "300"], ["claude"]], leader=1)
        res, pane = self.start(
            "--main-model", "claude-opus-5[1m]",
            extra_env={"HERDR_PANE_ID": ROOT, "CLAUDE_EFFORT": "max"},
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(pane["kind"], "claude")
        self.assertEqual(pane["start_args"], ["--model", "claude-opus-5[1m]", "--effort", "max"])
        self.assertIn("model claude-opus-5[1m] (self-report)", res.stderr)
        self.assertIn("thinking max (env CLAUDE_EFFORT)", res.stderr)

    def test_claude_effort_env_ignored_outside_the_root_pane(self):
        self.h.set_root(processes=[["claude", "--effort", "high"]])
        profile, _ = self.resolve(extra_env={"HERDR_PANE_ID": "w1:p9", "CLAUDE_EFFORT": "max"})
        self.assertEqual(profile["thinking"], {"value": "high", "source": "root argv"})

    def test_setup_flags_inherited_while_session_and_prompt_tokens_drop(self):
        self.h.set_root(processes=[[
            "claude", "--dangerously-skip-permissions", "--resume", "abc123",
            "--model", "sonnet", "--add-dir", "../a", "../b", "-p", "fix the bug",
        ]])
        res, pane = self.start("--main-model", "opus")
        self.assertEqual(res.returncode, 0, res.stderr)
        # Self-report replaces the launch-time model instead of duplicating it.
        self.assertEqual(
            pane["start_args"],
            ["--dangerously-skip-permissions", "--add-dir", "../a", "../b", "--model", "opus"],
        )
        self.assertIn("dropped --resume, -p", res.stderr)
        self.assertIn("⚠ permission bypass inherited from main: --dangerously-skip-permissions", res.stderr)
        self.assertNotIn("abc123", res.stderr + res.stdout)
        self.assertNotIn("fix the bug", res.stderr + res.stdout)

    def test_without_bypass_and_without_flags_opt_out_of_inherited_setup(self):
        self.h.set_root(processes=[[
            "claude", "--dangerously-skip-permissions", "--ide", "--effort", "high",
        ]])
        res, pane = self.start("--without", "bypass")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(pane["start_args"], ["--ide", "--effort", "high"])
        self.assertNotIn("⚠", res.stderr)
        res, pane = self.start("--without", "flags")
        self.assertEqual(res.returncode, 0, res.stderr)
        # Model and thinking are the profile itself, not setup: they stay.
        self.assertEqual(pane["start_args"], ["--effort", "high"])
        self.assertIn("without inherited flags", res.stderr)

    def test_codex_config_bypass_is_disclosed_and_dropped_by_without_bypass(self):
        self.h.set_root(kind="codex", processes=[[
            "codex", "-c", 'approval_policy="never"', "-c", 'sandbox_mode="danger-full-access"', "--search",
        ]])
        profile, err = self.resolve()
        self.assertEqual(profile["bypass"], ["--config:approval_policy never", "--config:sandbox_mode danger-full-access"])
        self.assertIn("⚠", err)
        res, pane = self.start("--without", "bypass")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(pane["start_args"], ["--search"])

    def test_glued_or_prompt_tokens_print_only_a_flag_stem(self):
        self.h.set_root(kind="codex", processes=[[
            "codex", "-cmodel_providers.corp.api_key=sk-SECRET456", "-rotate the key sk-live-SECRET123",
        ]])
        res = self.h.run([])
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertNotIn("SECRET", res.stdout + res.stderr)

    def test_self_report_that_disagrees_with_launch_argv_warns(self):
        self.h.set_root(kind="codex", processes=[["codex", "-m", "gpt-5-codex"]])
        _, err = self.resolve("--main-model", "gpt-4o")
        self.assertIn("differs from launch argv gpt-5-codex", err)

    def test_unknown_model_still_starts_on_config_default(self):
        self.h.set_root(processes=[["claude"]])
        res, pane = self.start()
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(pane["start_args"], [])
        self.assertIn("model UNKNOWN (worker uses its config default)", res.stderr)
        self.assertIn("thinking UNKNOWN", res.stderr)

    def test_different_kind_inherits_nothing_but_the_choice_of_kind(self):
        self.h.set_root(processes=[["claude", "--dangerously-skip-permissions", "--model", "opus"]])
        res, pane = self.start(
            "--main-model", "claude-opus-5[1m]", "--main-thinking", "max",
            "--kind", "pi", "--thinking", "low",
            extra_env={"HERDR_PANE_ID": ROOT, "CLAUDE_EFFORT": "max"},
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(pane["kind"], "pi")
        self.assertEqual(pane["start_args"], ["--thinking", "low"])
        self.assertIn("main is claude, so model, thinking and flags are not inherited", res.stderr)
        self.assertNotIn("claude-opus-5", " ".join(pane["start_args"]))

    def test_explicit_thinking_replaces_the_inherited_flag_for_a_node_wrapped_cli(self):
        self.h.set_root(kind="pi", processes=[[
            "node", "/opt/homebrew/bin/pi", "--provider", "anthropic",
            "--thinking", "high", "--continue",
        ]])
        res, pane = self.start("--thinking", "low")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(pane["start_args"], ["--provider", "anthropic", "--thinking", "low"])
        self.assertIn("dropped --continue", res.stderr)

    def test_native_flag_after_double_dash_replaces_the_inherited_group(self):
        self.h.set_root(processes=[["claude", "--permission-mode", "plan", "--ide"]])
        res, pane = self.start("--", "--permission-mode", "acceptEdits")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(pane["start_args"], ["--ide", "--permission-mode", "acceptEdits"])
        self.assertIn("explicit --permission-mode", res.stderr)

    def test_inline_equals_flags_and_bypass_by_value(self):
        self.h.set_root(processes=[["claude", "--permission-mode=bypassPermissions", "--effort=high"]])
        profile, err = self.resolve()
        self.assertEqual(profile["thinking"], {"value": "high", "source": "root argv"})
        self.assertEqual(profile["bypass"], ["--permission-mode bypassPermissions"])
        self.assertIn("⚠ permission bypass inherited", err)

    def test_codex_config_effort_replaced_and_subcommand_dropped(self):
        self.h.set_root(kind="codex", processes=[[
            "codex", "resume", "--last", "-m", "gpt-5",
            "-c", 'model_reasoning_effort="low"',
            "-c", "sandbox_workspace_write.network_access=true",
            "--dangerously-bypass-approvals-and-sandbox", "-i", "a.png", "b.png",
        ]])
        res, pane = self.start("--main-thinking", "high")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(
            pane["start_args"],
            [
                "-m", "gpt-5",
                "-c", "sandbox_workspace_write.network_access=true",
                "--dangerously-bypass-approvals-and-sandbox",
                "--config", 'model_reasoning_effort="high"',
            ],
        )
        self.assertIn("model gpt-5 (root argv)", res.stderr)
        self.assertIn("dropped --last, -i, 1 positional", res.stderr)

    def test_unmapped_kind_inherits_the_kind_only_and_says_so(self):
        self.h.set_root(kind="gemini", processes=[["gemini", "--yolo"]])
        res, pane = self.start("--main-model", "gemini-2.5-pro")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(pane["kind"], "gemini")
        self.assertEqual(pane["start_args"], [])
        self.assertIn("no flag table for kind 'gemini'", res.stderr)

    def test_unmapped_kind_refuses_an_explicit_thinking_level(self):
        self.h.set_root(processes=[["claude"]])
        res = self.h.run(["--kind", "gemini", "--thinking", "high"])
        self.assertEqual(res.returncode, 1)
        self.assertIn("no model/thinking flag mapping for kind 'gemini'", res.stderr)

    def test_unreadable_main_kind_requires_reduced_inheritance_for_same_looking_kind(self):
        self.h.set_root(no_agent=True)
        res = self.h.run([])
        self.assertEqual(res.returncode, 1)
        self.assertIn("Pass --kind KIND --without flags", res.stderr)

        res, pane = self.start(
            "--kind", "claude", "--main-model", "opus", "--main-thinking", "high"
        )
        self.assertEqual(res.returncode, 1)
        self.assertNotIn("start_args", pane)
        self.assertIn("cannot verify whether worker kind 'claude' matches", res.stderr)
        self.assertIn("--without flags", res.stderr)

        res, pane = self.start(
            "--kind", "claude", "--main-model", "opus", "--main-thinking", "high",
            "--without", "flags",
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(pane["start_args"], [])
        self.assertIn("model — (not inherited)", res.stderr)
        self.assertIn("thinking — (not inherited)", res.stderr)

    def test_unreadable_main_kind_does_not_cross_apply_self_report_to_different_kind(self):
        self.h.set_root(no_agent=True)
        res, pane = self.start(
            "--kind", "pi",
            "--main-model", "claude-opus-5[1m]", "--main-thinking", "max",
            "--without", "flags",
            extra_env={"HERDR_PANE_ID": ROOT, "CLAUDE_EFFORT": "max"},
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(pane["start_args"], [])
        self.assertIn("main agent's harness unreadable", res.stderr)

    def test_unreadable_process_info_fails_closed_before_start(self):
        self.h.set_root(processes=[["claude", "--ide"]], fail_process_info=True)
        res, pane = self.start("--main-model", "opus")
        self.assertEqual(res.returncode, 1)
        self.assertNotIn("start_args", pane)
        self.assertIn("cannot safely inherit", res.stderr)
        self.assertIn("--without flags", res.stderr)

        res, pane = self.start("--main-model", "opus", "--without", "flags")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(pane["start_args"], ["--model", "opus"])
        self.assertIn("setup flag inheritance explicitly disabled", res.stderr)

    def test_real_090_argv0_only_payload_fails_closed_before_start(self):
        observed_payload = [
            {
                "argv": ["rg", "--", "pi", "/Users/test/project"],
                "argv0": "rg",
                "cmdline": "rg -- pi /Users/test/project",
                "cwd": "/Users/test/project",
                "name": "rg",
                "pid": 48014,
            },
            {
                "argv0": "pi",
                "cwd": "/Users/test/project",
                "name": "node",
                "pid": 10764,
            },
        ]
        self.h.set_root(kind="pi", process_info_processes=observed_payload, leader=1)
        res, pane = self.start(
            "--kind", "pi", "--main-model", "anthropic/claude-sonnet-4"
        )
        self.assertEqual(res.returncode, 1)
        self.assertNotIn("start_args", pane)
        self.assertIn("process-info returned argv0 without full argv", res.stderr)
        self.assertIn("--without flags", res.stderr)

        res, pane = self.start("--without", "bypass")
        self.assertEqual(res.returncode, 1)
        self.assertNotIn("start_args", pane)

        res, pane = self.start("--kind", "claude")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(pane["kind"], "claude")
        self.assertEqual(pane["start_args"], [])

    def test_argv0_only_payload_starts_only_with_explicit_flags_opt_out(self):
        argv0_only = [{
            "argv0": "pi",
            "cwd": "/Users/test/project",
            "name": "node",
            "pid": 10764,
        }]
        self.h.set_root(kind="pi", process_info_processes=argv0_only, leader=0)
        res, pane = self.start(
            "--main-model", "anthropic/claude-sonnet-4", "--without", "flags"
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(pane["start_args"], ["--model", "anthropic/claude-sonnet-4"])
        self.assertIn("setup flag inheritance explicitly disabled", res.stderr)
        self.assertIn("flags none (opted out)", res.stderr)

    def test_malformed_argv_fails_closed_before_start(self):
        malformed_values = ("pi --no-tools", [], ["pi", ""], ["pi", 7])
        for raw_argv in malformed_values:
            with self.subTest(argv=raw_argv):
                malformed = [{"argv": raw_argv, "argv0": "pi", "pid": 10764}]
                self.h.set_root(kind="pi", process_info_processes=malformed, leader=0)
                res, pane = self.start()
                self.assertEqual(res.returncode, 1)
                self.assertNotIn("start_args", pane)
                self.assertIn("process-info returned malformed argv", res.stderr)

    def test_credential_and_setup_flag_values_are_never_printed(self):
        self.h.set_root(kind="pi", processes=[[
            "pi", "--api-key", "sk-secret-123", "--append-system-prompt", "internal note",
        ]])
        res, pane = self.start()
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(pane["start_args"], ["--append-system-prompt", "internal note"])
        printed = res.stdout + res.stderr
        self.assertNotIn("sk-secret-123", printed)
        self.assertNotIn("internal note", printed)
        self.assertIn("dropped --api-key", res.stderr)

    def test_failed_start_points_at_the_pane_for_the_cli_error(self):
        self.h.set_root(processes=[["claude"]])
        self.h.set_pane(WORKER, agent_status="unknown", no_agent=True, blocked_on_start=True)
        res = self.h.run(["--start", "worker", "--pane", WORKER])
        self.assertEqual(res.returncode, 1)
        self.assertIn(f"herdr pane read {WORKER}", res.stderr)


if __name__ == "__main__":
    unittest.main()
