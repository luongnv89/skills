"""Regression tests for the issue-work-loop worker launch contract."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SKILLS = Path(__file__).resolve().parents[2]
LOOP_SKILL = SKILLS / "issue-work-loop" / "SKILL.md"
PROTOCOL = SKILLS / "issue-work-loop" / "references" / "loop-protocol.md"
PROFILE = SKILLS / "herdr-agent" / "scripts" / "launch_profile.py"
FAKE_HERDR = SKILLS / "herdr-agent" / "tests" / "fake_herdr.py"
ROOT_PANE = "w1:p1"
WORKER_PANE = "w1:p2"


class WorkerLaunchContractTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="issue_work_loop_profile_"))
        fake_bin = self.tmpdir / "bin"
        fake_bin.mkdir()
        (fake_bin / "herdr").symlink_to(FAKE_HERDR)
        self.state_path = self.tmpdir / "state.json"
        self.env = dict(os.environ)
        self.env.update(
            {
                "FAKE_HERDR_STATE": str(self.state_path),
                "PATH": f"{fake_bin}{os.pathsep}{self.env.get('PATH', '')}",
            }
        )
        for var in ("CLAUDE_EFFORT", "HERDR_PANE_ID"):
            self.env.pop(var, None)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def write_state(self, root_fields):
        state = {
            "panes": {
                ROOT_PANE: {
                    "agent_status": "idle",
                    "text": "",
                    "name": "main",
                    "kind": "claude",
                    "processes": [["claude", "--ide"]],
                },
                WORKER_PANE: {
                    "agent_status": "unknown",
                    "text": "",
                    "name": None,
                    "no_agent": True,
                },
            }
        }
        state["panes"][ROOT_PANE].update(root_fields)
        self.state_path.write_text(json.dumps(state), encoding="utf-8")

    def run_profile(self, *args, start=True):
        command = ["python3", str(PROFILE), "--root-pane", ROOT_PANE]
        if start:
            command += ["--start", "worker", "--pane", WORKER_PANE]
        command += list(args)
        return subprocess.run(
            command,
            env=self.env,
            text=True,
            capture_output=True,
            check=False,
        )

    def state(self):
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def selective_profile_section(self, path, heading):
        text = path.read_text(encoding="utf-8")
        start = text.index(heading)
        body = text[start:]
        next_heading = body.find("\n## ", len(heading))
        return body if next_heading < 0 else body[:next_heading]

    def test_each_doc_section_requires_the_complete_worker_profile_policy(self):
        sections = (
            self.selective_profile_section(
                LOOP_SKILL, "## Selective Worker Launch Profile (mandatory)"
            ),
            self.selective_profile_section(
                PROTOCOL, "## Selective worker launch-profile gate"
            ),
        )
        required_groups = (
            ("initial issue", "reviewer", "pr fixer", "retry", "freshen", "replacement"),
            ("launch_profile.py", "--without bypass", "herdr agent start"),
            ("restrictive", "inherited", "--without flags"),
            ("exact", "kind", "model", "thinking", "native", "--start"),
            ("same", "cwd", "environment", "configuration"),
            ("flags", "explicit", "names only", "inspect"),
            ("profile.bypass", "inherited-only", "proof"),
            ("explicit native", "config", "environment", "prohibited"),
            ("unknown", "unmapped", "malformed", "fail", "closed"),
            ("resolve", "input", "unverified", "fallback"),
        )
        for section in sections:
            lowered = section.lower()
            for group in required_groups:
                for phrase in group:
                    self.assertIn(phrase.lower(), lowered, phrase)

    def test_selective_bypass_preserves_restrictive_inherited_flags(self):
        cases = (
            (
                "claude",
                [
                    "claude",
                    "--dangerously-skip-permissions",
                    "--disallowed-tools",
                    "Bash",
                    "--permission-mode",
                    "plan",
                    "--restricted",
                ],
                [
                    "--disallowed-tools",
                    "Bash",
                    "--permission-mode",
                    "plan",
                    "--restricted",
                ],
            ),
            (
                "pi",
                ["pi", "--approve", "--exclude-tools", "bash", "--no-approve"],
                ["--exclude-tools", "bash", "--no-approve"],
            ),
            (
                "codex",
                [
                    "codex",
                    "--dangerously-bypass-approvals-and-sandbox",
                    "--sandbox",
                    "read-only",
                    "--ask-for-approval",
                    "on-request",
                ],
                ["--sandbox", "read-only", "--ask-for-approval", "on-request"],
            ),
        )
        for kind, processes, expected_args in cases:
            with self.subTest(kind=kind):
                self.write_state({"kind": kind, "processes": [processes]})
                result = self.run_profile("--without", "bypass")
                self.assertEqual(result.returncode, 0, result.stderr)
                worker = self.state()["panes"][WORKER_PANE]
                self.assertEqual(worker["start_args"], expected_args)
                self.assertIn("without inherited bypass", result.stderr)

    def test_helper_summary_is_inherited_only_and_accepts_explicit_bypass(self):
        # Characterizes launch_profile.py: the loop's caller policy must reject
        # this explicit bypass before start; the helper intentionally reports it.
        self.write_state({"processes": [["claude", "--ide"]]})
        args = ("--without", "bypass", "--", "--dangerously-skip-permissions")
        resolved = self.run_profile(*args, start=False)
        self.assertEqual(resolved.returncode, 0, resolved.stderr)
        profile = json.loads(resolved.stdout)
        self.assertEqual(profile["bypass"], [])
        self.assertIn("--dangerously-skip-permissions", profile["explicit"])

        result = self.run_profile(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        worker = self.state()["panes"][WORKER_PANE]
        self.assertIn("--dangerously-skip-permissions", worker["start_args"])

    def test_unmapped_kind_is_helper_characterization_not_loop_enforcement(self):
        # The helper can describe an unmapped kind with bypass=[], but the loop
        # contract rejects unknown permission profiles before worker start.
        self.write_state({"kind": "gemini", "processes": [["gemini", "--yolo"]]})
        result = self.run_profile("--without", "bypass", start=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        profile = json.loads(result.stdout)
        self.assertEqual(profile["kind"], "gemini")
        self.assertEqual(profile["bypass"], [])
        self.assertIn("no flag table for kind 'gemini'", result.stderr)

    def test_unverifiable_effective_profile_fails_closed_before_worker_start(self):
        self.write_state({"fail_process_info": True})
        result = self.run_profile("--without", "bypass")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("start_args", self.state()["panes"][WORKER_PANE])
        self.assertIn("--without flags", result.stderr)


if __name__ == "__main__":
    unittest.main()
