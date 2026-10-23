#!/usr/bin/env python3
"""Tests for the herdr-agent scripts, run against the fake `herdr` CLI in tests/bin.

One section per script; each section's comment block says what it covers.

Run directly (stdlib unittest only, no live herdr needed):
    python3 -m unittest discover -s skills/herdr-agent/tests -p 'test_*.py'
"""


from __future__ import annotations

import json
import math
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


sys.path.insert(0, str(SCRIPTS))

from next_grid_split import (  # noqa: E402
    area_width_from_layout,
    boundary_resize_op,
    equal_targets,
    panes_from_layout,
    plan_next_split,
    require_root_membership,
    split_ratio,
    validate_live_layout,
    validate_single_row,
)


# ============================================================================
# badge
# Behavioral tests for badge.py against a fake `herdr` CLI.
#
# badge.py exists because `herdr pane report-metadata` takes a pane id while fleet
# bookkeeping runs on agent names. These tests cover that resolution, the state
# label validation Herdr would otherwise reject server-side, and the refusal to
# send an empty report.
# ============================================================================

BADGE = SCRIPTS / "badge.py"


class BadgeFakeHerdrHarness:
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
        self.h = BadgeFakeHerdrHarness()

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


# ============================================================================
# broadcast
# Behavioral tests for broadcast.sh against a fake `herdr` CLI.
#
# broadcast.sh dispatches `herdr agent prompt --wait` to every safe target
# concurrently. What these tests pin down is the behavior around that call: which
# targets it refuses, which it dedupes, how it maps Herdr's error codes, and that
# a refused or failed target is always reported rather than silently dropped.
# ============================================================================

BROADCAST = SCRIPTS / "broadcast.sh"


class BroadcastFakeHerdrHarness:
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
        self.h = BroadcastFakeHerdrHarness()

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
                h = BroadcastFakeHerdrHarness()
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


# ============================================================================
# fleet_status
# Behavioral tests for fleet_status.py against a fake `herdr` CLI.
#
# fleet_status.py is the skill's monitoring surface: one `herdr api snapshot` call
# renders the whole fleet. These tests pin the properties that make it usable as
# a report — attention ordering, scope filtering, fail-closed status reading, and
# the blocked exit code — rather than the exact table formatting.
# ============================================================================

FLEET_STATUS = SCRIPTS / "fleet_status.py"


class FleetStatusFakeHerdrHarness:
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
        self.h = FleetStatusFakeHerdrHarness()

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


# ============================================================================
# launch_profile
# Behavioral tests for launch_profile.py against a fake `herdr` CLI.
#
# A worker mirrors the main agent by default: same harness kind, model, thinking
# level and setup flags. The two failure modes that matter are a spawn that
# refuses to start when the main agent's model is UNKNOWN, and a Claude model id
# or effort handed to a worker of a different kind. Both are pinned here, along
# with argv filtering: session, prompt and credential tokens must never reach a
# worker or the printed profile.
# ============================================================================

PROFILE = SCRIPTS / "launch_profile.py"

ROOT = "w1:p1"
WORKER = "w1:p2"


class LaunchProfileFakeHerdrHarness:
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
        self.h = LaunchProfileFakeHerdrHarness()

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


# ============================================================================
# next_grid_split
# Fixture tests for next_grid_split.py's equal-width column planning.
#
# These cover the pure arithmetic that decides the split ratio and each
# equalizer resize op. The exact `herdr pane split --ratio` / `herdr pane
# resize --amount` semantics they encode were verified LIVE against herdr
# 0.7.4 (documented in SKILL.md "Equal-width columns — verified semantics"):
# `--ratio` = the existing/left child's fraction of the split pane; `--amount`
# = a cell delta as a fraction of the tab area width, growing the neighbor on
# `--direction`. `test_equalizer_sweep_converges_on_redistribution_model`
# simulates the observed proportional redistribution and confirms the
# outermost-first grow sweep is a contraction (converges to equal width).
# ============================================================================

def panes(*rects):
    return [
        {"pane_id": pid, "rect": {"x": x, "width": w}}
        for pid, x, w in rects
    ]


def full_rect_layout(area, *rects):
    """Layout with full x/y/width/height rects, for validate_single_row.

    `area` is (x, y, width, height); each rect is (pid, x, y, width, height).
    """
    ax, ay, aw, ah = area
    return {
        "result": {
            "layout": {
                "area": {"x": ax, "y": ay, "width": aw, "height": ah},
                "panes": [
                    {"pane_id": pid, "rect": {"x": x, "y": y, "width": w, "height": h}}
                    for pid, x, y, w, h in rects
                ],
            }
        }
    }


class PlanNextSplitTests(unittest.TestCase):
    def test_single_pane_plans_two_columns(self):
        rightmost, new_count = plan_next_split(panes(("root", 0, 200)), "root")
        self.assertEqual(rightmost, "root")
        self.assertEqual(new_count, 2)

    def test_orders_panes_left_to_right_and_splits_rightmost(self):
        rightmost, new_count = plan_next_split(
            panes(("sub1", 100, 100), ("root", 0, 100)), "root"
        )
        self.assertEqual(rightmost, "sub1")
        self.assertEqual(new_count, 3)

    def test_three_existing_columns_plans_fourth(self):
        rightmost, new_count = plan_next_split(
            panes(("root", 0, 66), ("sub1", 66, 67), ("sub2", 133, 67)), "root"
        )
        self.assertEqual(rightmost, "sub2")
        self.assertEqual(new_count, 4)

    def test_no_root_requested_still_plans_from_layout(self):
        # root_pane is None => "no specific root requested", plan normally.
        rightmost, new_count = plan_next_split(panes(("a", 0, 50), ("b", 50, 50)), None)
        self.assertEqual(rightmost, "b")
        self.assertEqual(new_count, 3)

    def test_requested_root_absent_from_layout_is_hard_error(self):
        # P4 round 6: a named root that isn't in the layout means we'd be
        # splitting the WRONG tab — must raise before any mutation, not warn.
        with self.assertRaises(SystemExit):
            plan_next_split(panes(("a", 0, 50), ("b", 50, 50)), "missing-root")

    def test_requested_root_present_plans_normally(self):
        rightmost, new_count = plan_next_split(panes(("a", 0, 50), ("b", 50, 50)), "a")
        self.assertEqual(rightmost, "b")
        self.assertEqual(new_count, 3)

    def test_no_usable_rects_raises(self):
        with self.assertRaises(SystemExit):
            plan_next_split([{"pane_id": "x", "rect": {"x": 0, "width": 0}}], "x")

    def test_pane_missing_rect_is_hard_error(self):
        # Round 16 finding #2: a pane with a VALID id but no rect must be a HARD
        # error, not a silent drop — dropping it during a live re-read would
        # compute resize ops for a partial grid. (Was
        # test_panes_missing_rect_fields_are_dropped, which asserted the drop;
        # that lenient behaviour is now the bug.)
        layout = [
            {"pane_id": "root", "rect": {"x": 0, "width": 100}},
            {"pane_id": "ghost"},
        ]
        with self.assertRaises(SystemExit):
            plan_next_split(layout, "root")


class PaneIdValidationTests(unittest.TestCase):
    """Round 15 finding #3: a malformed pane_id on the rightmost pane must be a
    HARD error, not a silent drop that retargets the split to another pane."""

    def test_rightmost_null_id_raises_not_mistarget(self):
        # Without the fix, _ordered_columns drops the null-id rightmost pane and
        # plan_next_split returns ("a", 3) — splitting the WRONG column.
        with self.assertRaises(SystemExit):
            plan_next_split(
                [{"pane_id": "a", "rect": {"x": 0, "width": 50}},
                 {"pane_id": None, "rect": {"x": 50, "width": 50}}],
                None,
            )

    def test_non_string_id_raises(self):
        with self.assertRaises(SystemExit):
            plan_next_split(
                [{"pane_id": "a", "rect": {"x": 0, "width": 50}},
                 {"pane_id": 123, "rect": {"x": 50, "width": 50}}],
                None,
            )

    def test_empty_string_id_raises(self):
        with self.assertRaises(SystemExit):
            plan_next_split(
                [{"pane_id": "a", "rect": {"x": 0, "width": 50}},
                 {"pane_id": "", "rect": {"x": 50, "width": 50}}],
                None,
            )

    def test_duplicate_ids_raise(self):
        with self.assertRaises(SystemExit):
            plan_next_split(
                [{"pane_id": "dup", "rect": {"x": 0, "width": 50}},
                 {"pane_id": "dup", "rect": {"x": 50, "width": 50}}],
                None,
            )

    def test_missing_id_key_raises(self):
        with self.assertRaises(SystemExit):
            plan_next_split(
                [{"pane_id": "a", "rect": {"x": 0, "width": 50}},
                 {"rect": {"x": 50, "width": 50}}],
                None,
            )

    def test_validate_single_row_rejects_malformed_id(self):
        with self.assertRaises(SystemExit):
            validate_single_row({"layout": {
                "area": {"x": 0, "y": 0, "width": 100, "height": 10},
                "panes": [
                    {"pane_id": "a", "rect": {"x": 0, "y": 0, "width": 50, "height": 10}},
                    {"pane_id": None, "rect": {"x": 50, "y": 0, "width": 50, "height": 10}},
                ],
            }})

    def test_all_valid_unique_ids_still_plan(self):
        # Control: valid unique ids plan normally (fix doesn't over-reach).
        rightmost, new_count = plan_next_split(
            [{"pane_id": "a", "rect": {"x": 0, "width": 50}},
             {"pane_id": "b", "rect": {"x": 50, "width": 50}}],
            None,
        )
        self.assertEqual(rightmost, "b")
        self.assertEqual(new_count, 3)


class PaneGeometryValidationTests(unittest.TestCase):
    """Round 16 finding #2: every pane must carry valid rect/x/positive-width
    geometry. A missing/malformed/non-positive value must be a HARD error, not a
    silent drop — dropping one during a live equalize re-read would compute
    resize ops for a partial grid (a column omitted)."""

    def _split(self, second_rect):
        return plan_next_split(
            [{"pane_id": "a", "rect": {"x": 0, "width": 50}},
             {"pane_id": "b", "rect": second_rect}],
            None,
        )

    def test_missing_rect_raises(self):
        with self.assertRaises(SystemExit):
            plan_next_split(
                [{"pane_id": "a", "rect": {"x": 0, "width": 50}},
                 {"pane_id": "b"}],
                None,
            )

    def test_missing_x_raises(self):
        # Old behaviour defaulted missing x to 0, misordering columns.
        with self.assertRaises(SystemExit):
            self._split({"width": 50})

    def test_missing_width_raises(self):
        with self.assertRaises(SystemExit):
            self._split({"x": 50})

    def test_zero_width_raises(self):
        with self.assertRaises(SystemExit):
            self._split({"x": 50, "width": 0})

    def test_negative_width_raises(self):
        with self.assertRaises(SystemExit):
            self._split({"x": 50, "width": -10})

    def test_non_numeric_width_raises(self):
        with self.assertRaises(SystemExit):
            self._split({"x": 50, "width": "wide"})

    def test_non_numeric_x_raises(self):
        with self.assertRaises(SystemExit):
            self._split({"x": "left", "width": 50})

    def test_all_valid_geometry_still_plans(self):
        # Control: fully-valid geometry plans normally (no over-reach).
        rightmost, new_count = self._split({"x": 50, "width": 50})
        self.assertEqual(rightmost, "b")
        self.assertEqual(new_count, 3)


class NonFiniteGeometryTests(unittest.TestCase):
    """Round 17 finding #1: NaN/inf pass float() but defeat every comparison
    (`nan <= 0`, `nan > tol` are all False), so non-finite geometry would sail
    past the positive-width and single-row checks. `json.loads` accepts
    NaN/Infinity by default, so this is reachable, not theoretical. Every
    coordinate/dimension must be finite (dimensions also strictly positive)."""

    def _split(self, second_rect):
        return plan_next_split(
            [{"pane_id": "a", "rect": {"x": 0, "width": 50}},
             {"pane_id": "b", "rect": second_rect}],
            None,
        )

    def test_nan_width_raises(self):
        with self.assertRaises(SystemExit):
            self._split({"x": 50, "width": float("nan")})

    def test_inf_width_raises(self):
        with self.assertRaises(SystemExit):
            self._split({"x": 50, "width": float("inf")})

    def test_nan_x_raises(self):
        with self.assertRaises(SystemExit):
            self._split({"x": float("nan"), "width": 50})

    def test_inf_x_raises(self):
        with self.assertRaises(SystemExit):
            self._split({"x": float("-inf"), "width": 50})

    def test_nan_area_width_raises(self):
        # A present-but-NaN area width must be a hard error, not skip the
        # <=0 fallback trigger and return a poisoned width.
        with self.assertRaises(SystemExit):
            area_width_from_layout({"layout": {
                "area": {"width": float("nan")},
                "panes": [{"pane_id": "a", "rect": {"x": 0, "width": 50}}],
            }})

    def test_nan_area_coord_in_single_row_raises(self):
        with self.assertRaises(SystemExit):
            validate_single_row(full_rect_layout(
                (0, float("nan"), 100, 10),
                ("a", 0, 0, 50, 10), ("b", 50, 0, 50, 10)))

    def test_inf_pane_height_in_single_row_raises(self):
        with self.assertRaises(SystemExit):
            validate_single_row(full_rect_layout(
                (0, 0, 100, 10),
                ("a", 0, 0, 50, float("inf")), ("b", 50, 0, 50, 10)))

    def test_nan_json_roundtrips_to_float_nan(self):
        # Sanity: the real JSON path can carry NaN, so float('nan') fixtures
        # faithfully represent it.
        self.assertTrue(math.isnan(json.loads('{"w": NaN}')["w"]))


class ValidateLiveLayoutTests(unittest.TestCase):
    """Round 17 finding #2: the centralized live-layout validator must enforce
    BOTH shape (single clean row) AND root membership. The discriminating case:
    a stacked/gapped layout with coincidentally-equal widths + a valid root must
    RAISE — the old final convergence check ran only `_ordered_columns` and
    returned success on exactly this."""

    def test_stacked_layout_with_equal_widths_raises(self):
        # Two panes, equal widths, but STACKED (same x, split vertically) —
        # widths are "equal" yet this is a 2D layout, not a row of columns.
        stacked = full_rect_layout(
            (0, 0, 100, 20),
            ("a", 0, 0, 100, 10), ("b", 0, 10, 100, 10))
        with self.assertRaises(SystemExit):
            validate_live_layout(stacked, "a")

    def test_gapped_layout_with_equal_widths_raises(self):
        # Equal widths but a gap between columns (b starts at 60, not 50).
        gapped = full_rect_layout(
            (0, 0, 110, 10),
            ("a", 0, 0, 50, 10), ("b", 60, 0, 50, 10))
        with self.assertRaises(SystemExit):
            validate_live_layout(gapped, "a")

    def test_clean_row_but_root_absent_raises(self):
        clean = full_rect_layout(
            (0, 0, 100, 10),
            ("a", 0, 0, 50, 10), ("b", 50, 0, 50, 10))
        with self.assertRaises(SystemExit):
            validate_live_layout(clean, "not-here")

    def test_clean_row_with_present_root_passes(self):
        clean = full_rect_layout(
            (0, 0, 100, 10),
            ("a", 0, 0, 50, 10), ("b", 50, 0, 50, 10))
        ids, widths = validate_live_layout(clean, "a")
        self.assertEqual(ids, ["a", "b"])
        self.assertEqual(widths, [50, 50])

    def test_clean_row_none_root_passes(self):
        clean = full_rect_layout(
            (0, 0, 100, 10),
            ("a", 0, 0, 50, 10), ("b", 50, 0, 50, 10))
        ids, _ = validate_live_layout(clean, None)
        self.assertEqual(ids, ["a", "b"])


class MalformedLayoutJsonTests(unittest.TestCase):
    """Round 14 note: malformed-but-valid JSON must yield a clean SystemExit
    validation error, NOT an uncaught AttributeError traceback."""

    def test_top_level_null_is_clean_error(self):
        # json.load of "null" is None; .get() on it would crash.
        with self.assertRaises(SystemExit):
            panes_from_layout(None)

    def test_top_level_list_is_clean_error(self):
        with self.assertRaises(SystemExit):
            panes_from_layout([1, 2, 3])

    def test_panes_with_null_element_is_clean_error(self):
        # `panes: [null]` — the null element would crash every pane.get(...).
        with self.assertRaises(SystemExit):
            panes_from_layout({"layout": {"panes": [None]}})

    def test_panes_with_non_object_element_is_clean_error(self):
        with self.assertRaises(SystemExit):
            panes_from_layout({"layout": {"panes": ["not-a-pane"]}})

    def test_null_element_via_validate_single_row_is_clean_error(self):
        with self.assertRaises(SystemExit):
            validate_single_row({"layout": {"area": {"x": 0, "y": 0, "width": 100, "height": 10},
                                            "panes": [None]}})

    def test_null_element_via_plan_next_split_is_clean_error(self):
        with self.assertRaises(SystemExit):
            plan_next_split([None], "root")


class RequireRootMembershipTests(unittest.TestCase):
    def test_none_root_is_allowed(self):
        require_root_membership(["a", "b"], None)  # must not raise

    def test_present_root_is_allowed(self):
        require_root_membership(["a", "b"], "a")

    def test_absent_root_raises(self):
        with self.assertRaises(SystemExit):
            require_root_membership(["a", "b"], "missing")

    def test_absent_root_in_empty_layout_raises(self):
        with self.assertRaises(SystemExit):
            require_root_membership([], "root")


class SplitRatioTests(unittest.TestCase):
    """`--ratio` = 1/N (the existing/left child's fraction). Verified live
    against herdr 0.7.4: from two equal 105/105 columns, splitting the
    rightmost with ratio 1/3 gives a new pane of 70 (= 210/3, the equal
    target). The earlier (N-1)/N value was BACKWARDS — it made the new pane
    the *small* child (35, not 70)."""

    def test_second_column_is_half(self):
        self.assertEqual(split_ratio(2), 0.5)

    def test_third_column_is_one_third(self):
        self.assertAlmostEqual(split_ratio(3), 1.0 / 3.0, places=9)

    def test_fourth_column_is_one_quarter(self):
        self.assertEqual(split_ratio(4), 0.25)

    def test_ratio_is_reciprocal_of_new_count(self):
        for n in range(2, 12):
            self.assertAlmostEqual(split_ratio(n), 1.0 / n, places=9)

    def test_new_pane_lands_on_equal_target(self):
        """The point of the ratio: splitting the rightmost of N-1 equal
        columns (each 1/(N-1) of the tab) at ratio 1/N makes the new pane
        exactly 1/N of the tab."""
        area = 210.0
        for n in range(2, 8):
            existing = n - 1
            rightmost_col_width = area / existing  # existing columns are equal
            r = split_ratio(n)
            new_pane_width = (1.0 - r) * rightmost_col_width
            self.assertAlmostEqual(new_pane_width, area / n, places=6)

    def test_below_two_raises(self):
        with self.assertRaises(SystemExit):
            split_ratio(1)


class EqualTargetsTests(unittest.TestCase):
    def test_even_division(self):
        self.assertEqual(equal_targets(5, 210), [42, 42, 42, 42, 42])

    def test_remainder_goes_to_leftmost_columns(self):
        # 210 / 4 = 52.5 -> two columns get 53, two get 52; sum stays 210.
        self.assertEqual(equal_targets(4, 210), [53, 53, 52, 52])
        self.assertEqual(sum(equal_targets(4, 210)), 210)

    def test_single_column(self):
        self.assertEqual(equal_targets(1, 210), [210])

    def test_zero_columns_raises(self):
        with self.assertRaises(SystemExit):
            equal_targets(0, 210)


class BoundaryResizeOpTests(unittest.TestCase):
    ids = ["a", "b", "c"]

    def test_boundary_must_move_right_grows_left_column(self):
        # widths 40/80/90 (area 210), targets 70/70/70. Boundary 0 cum=40,
        # target cum=70 -> move right by 30 -> grow column a on its right.
        op = boundary_resize_op(self.ids, [40, 80, 90], [70, 70, 70], 210, 0)
        self.assertEqual(op, ("a", "right", 30 / 210))

    def test_boundary_must_move_left_grows_right_column(self):
        # widths 105/53/52, targets 70/70/70. Boundary 0 cum=105, target=70
        # -> move left by 35 -> grow the RIGHT column b on its left edge.
        op = boundary_resize_op(self.ids, [105, 53, 52], [70, 70, 70], 210, 0)
        self.assertEqual(op, ("b", "left", 35 / 210))

    def test_on_target_returns_none(self):
        op = boundary_resize_op(self.ids, [70, 70, 70], [70, 70, 70], 210, 0)
        self.assertIsNone(op)

    def test_sub_cell_delta_returns_none(self):
        # cum 70.4 vs target 70 -> 0.4 cell, nothing herdr can act on.
        op = boundary_resize_op(self.ids, [70.4, 70, 69.6], [70, 70, 70], 210, 0)
        self.assertIsNone(op)


class AreaWidthTests(unittest.TestCase):
    def test_reads_explicit_area(self):
        data = {"layout": {"area": {"width": 210}, "panes": panes(("a", 0, 210))}}
        self.assertEqual(area_width_from_layout(data), 210)

    def test_falls_back_to_summed_widths(self):
        data = {"layout": {"panes": panes(("a", 0, 100), ("b", 100, 110))}}
        self.assertEqual(area_width_from_layout(data), 210)


class ValidateSingleRowTests(unittest.TestCase):
    """Reject 2D / stacked layouts before any split or equalize (P3 round 5).
    Area = (x, y, w, h); panes carry full x/y/w/h rects."""

    AREA = (0, 0, 210, 55)

    def test_valid_single_row_passes(self):
        layout = full_rect_layout(
            self.AREA,
            ("a", 0, 0, 105, 55),
            ("b", 105, 0, 105, 55),
        )
        validate_single_row(layout)  # must not raise

    def test_valid_three_columns_passes(self):
        layout = full_rect_layout(
            self.AREA,
            ("a", 0, 0, 70, 55),
            ("b", 70, 0, 70, 55),
            ("c", 140, 0, 70, 55),
        )
        validate_single_row(layout)

    def test_stacked_panes_sharing_x_are_rejected(self):
        # b and c share x=105 but are stacked vertically (half height each) —
        # the column model would double-count them. Must reject.
        layout = full_rect_layout(
            self.AREA,
            ("a", 0, 0, 105, 55),
            ("b", 105, 0, 105, 27),
            ("c", 105, 27, 105, 28),
        )
        with self.assertRaises(SystemExit):
            validate_single_row(layout)

    def test_partial_height_pane_is_rejected(self):
        layout = full_rect_layout(
            self.AREA,
            ("a", 0, 0, 105, 55),
            ("b", 105, 0, 105, 30),  # not full height
        )
        with self.assertRaises(SystemExit):
            validate_single_row(layout)

    def test_top_offset_pane_is_rejected(self):
        layout = full_rect_layout(
            self.AREA,
            ("a", 0, 0, 105, 55),
            ("b", 105, 5, 105, 50),  # not top-aligned with area
        )
        with self.assertRaises(SystemExit):
            validate_single_row(layout)

    def test_gap_between_columns_is_rejected(self):
        layout = full_rect_layout(
            self.AREA,
            ("a", 0, 0, 100, 55),
            ("b", 110, 0, 100, 55),  # gap from 100..110
        )
        with self.assertRaises(SystemExit):
            validate_single_row(layout)

    def test_overlapping_columns_are_rejected(self):
        layout = full_rect_layout(
            self.AREA,
            ("a", 0, 0, 110, 55),
            ("b", 100, 0, 110, 55),  # overlaps a from 100..110
        )
        with self.assertRaises(SystemExit):
            validate_single_row(layout)

    def test_columns_not_filling_width_are_rejected(self):
        layout = full_rect_layout(
            self.AREA,
            ("a", 0, 0, 70, 55),
            ("b", 70, 0, 70, 55),  # spans to 140, area ends at 210
        )
        with self.assertRaises(SystemExit):
            validate_single_row(layout)

    def test_missing_area_rect_is_rejected(self):
        layout = {"result": {"layout": {"panes": panes(("a", 0, 210))}}}
        with self.assertRaises(SystemExit):
            validate_single_row(layout)

    def test_pane_missing_yheight_is_rejected(self):
        # A pane rect with only x/width (the old shape) can't be validated as
        # a full-height column — must reject rather than assume.
        layout = {
            "result": {
                "layout": {
                    "area": {"x": 0, "y": 0, "width": 210, "height": 55},
                    "panes": [{"pane_id": "a", "rect": {"x": 0, "width": 210}}],
                }
            }
        }
        with self.assertRaises(SystemExit):
            validate_single_row(layout)


class EqualizerConvergenceTests(unittest.TestCase):
    """Simulate the live herdr redistribution behaviour and confirm the
    outermost-first, always-grow boundary sweep is a contraction toward
    equal width. The model mirrors what was observed live: a resize moves
    one boundary by the requested delta and redistributes the freed/absorbed
    cells *proportionally* among the panes on the other side of that
    boundary.
    """

    AREA = 210

    def _resize(self, widths, pane_index, direction, amount):
        """Apply one resize to a copy of `widths`, returning the new list.

        Moves the boundary between `pane_index` and its neighbor on
        `direction`, redistributing `delta` cells proportionally across the
        panes on the far side of that boundary.
        """
        w = list(widths)
        delta = amount * self.AREA
        if direction == "right":
            # grow pane_index rightward: boundary between pane_index and
            # pane_index+1 moves right; cells taken from all panes to the right.
            w[pane_index] += delta
            right = list(range(pane_index + 1, len(w)))
            total = sum(w[i] for i in right)
            for i in right:
                w[i] -= delta * (w[i] / total)
        else:  # left: grow pane_index leftward, boundary between it and
            # pane_index-1 moves left; cells taken from panes to the left.
            w[pane_index] += delta
            left = list(range(0, pane_index))
            total = sum(w[i] for i in left)
            for i in left:
                w[i] -= delta * (w[i] / total)
        return w

    def _sweep_once(self, widths):
        ids = [f"c{i}" for i in range(len(widths))]
        targets = equal_targets(len(widths), self.AREA)
        for boundary in range(len(widths) - 1):
            op = boundary_resize_op(ids, widths, targets, self.AREA, boundary)
            if op is None:
                continue
            pane_id, direction, amount = op
            idx = ids.index(pane_id)
            widths = self._resize(widths, idx, direction, amount)
        return widths

    def test_four_column_decay_converges(self):
        # geometric decay a naive split leaves behind: 105/35/18/52-ish.
        widths = [105.0, 35.0, 18.0, 52.0]
        # normalize to area
        scale = self.AREA / sum(widths)
        widths = [w * scale for w in widths]
        start_spread = max(widths) - min(widths)
        for _ in range(12):
            if max(widths) - min(widths) <= 1.5:
                break
            widths = self._sweep_once(widths)
        # This float model converges to ~1 cell; live herdr (integer cells)
        # lands at spread 0 for this case. Either way the sweep is a strong
        # contraction — assert it collapsed to a near-equal fixed point.
        self.assertLess(max(widths) - min(widths), start_spread)
        self.assertLessEqual(max(widths) - min(widths), 1.5)

    def test_already_equal_is_a_fixed_point(self):
        widths = [70.0, 70.0, 70.0]
        out = self._sweep_once(widths)
        for a, b in zip(out, widths):
            self.assertAlmostEqual(a, b, places=6)


# ============================================================================
# preflight_send
# Behavioral tests for preflight_send.py against a fake `herdr` CLI.
#
# preflight_send.py guards the one thing the server does not: `herdr agent prompt`
# refuses a `blocked` target itself, but happily accepts a `working` one, and its
# wait tracks lifecycle state rather than one turn. Each rejection reason gets a
# distinct exit code so a caller can branch on it.
# ============================================================================

PREFLIGHT = SCRIPTS / "preflight_send.py"


class PreflightFakeHerdrHarness:
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
        self.h = PreflightFakeHerdrHarness()

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


# ============================================================================
# wait_for_idle
# Behavioral tests for wait_for_idle.py against a fake `herdr` CLI.
#
# Covers the P1.1/P2.7 false-completion fix: a pane already `working` (or
# already carrying the completion marker) before this send must not be
# reported as settled for THIS send.
# ============================================================================

WAITER = SCRIPTS / "wait_for_idle.py"


class WaitForIdleFakeHerdrHarness:
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
        self.h = WaitForIdleFakeHerdrHarness()

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
        # Fast content-stability fallback (0.2s x 2): if a slow CI poller
        # misses the `working` window, the status loop breaks to fallback on
        # transcript change, and the default 2.0s x 3 fallback needs 6s+
        # which cannot fit the 5s timeout. With 0.2s x 2 it settles in ~0.6s.
        cp = self.h.run_waiter("p1", "--baseline-file", baseline, "--timeout", "5", "--interval", "0.2", "--quiet-cycles", "2")
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
        self.h = WaitForIdleFakeHerdrHarness()
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
