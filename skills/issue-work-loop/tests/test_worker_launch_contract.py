"""Regression tests for the issue-work-loop worker launch contract."""

from __future__ import annotations

import json
import os
import re
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

    def protocol_bash_block(self, heading):
        section = self.selective_profile_section(PROTOCOL, heading)
        blocks = re.findall(r"```bash\n(.*?)```", section, re.DOTALL)
        self.assertTrue(blocks, heading)
        return blocks[0]

    def run_capability_gate(self, mode):
        installed = self.tmpdir / "installed"
        scripts = installed / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        env = dict(self.env)
        if mode == "empty":
            env.pop("herdr_agent_dir", None)
        else:
            env["herdr_agent_dir"] = str(installed)
        helper = scripts / "launch_profile.py"
        helper.unlink(missing_ok=True)
        if mode != "missing":
            if mode == "help-fail":
                body = "import sys\nsys.exit(7)\n"
            elif mode == "unsupported":
                body = "print('usage: --without flags')\n"
            else:
                body = "print('usage: --without bypass')\n"
            helper.write_text(body, encoding="utf-8")
        return subprocess.run(
            ["bash", "-c", self.protocol_bash_block("### Installed-helper capability gate")],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def run_profile_parser(self, profile_json):
        helper = self.tmpdir / "profile-helper.py"
        helper.write_text(
            "import os\nprint(os.environ['PROFILE_JSON'], end='')\n",
            encoding="utf-8",
        )
        env = dict(self.env)
        env["helper"] = str(helper)
        env["PROFILE_JSON"] = (
            profile_json if isinstance(profile_json, str) else json.dumps(profile_json)
        )
        script = "\n".join(
            (
                "root_pane='root'",
                "main_model=''",
                "main_thinking=''",
                "worker_profile_args=()",
                "worker_native_args=()",
                self.protocol_bash_block("### Probe and target evidence"),
            )
        )
        return subprocess.run(
            ["bash", "-c", script],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    @staticmethod
    def valid_profile():
        return {
            "kind": "claude",
            "inherited": True,
            "model": {"value": "", "source": "UNKNOWN"},
            "thinking": {"value": "", "source": "UNKNOWN"},
            "flags": [],
            "flags_source": "root argv",
            "without": ["bypass"],
            "explicit": [],
            "bypass": [],
            "dropped": [],
            "warnings": [],
            "argc": 0,
        }

    def test_installed_helper_capability_gate_is_executable_and_fail_closed(self):
        snippet = self.protocol_bash_block("### Installed-helper capability gate")
        self.assertIn('[ -n "$here" ] ||', snippet)
        for mode in ("empty", "missing", "unsupported", "help-fail"):
            with self.subTest(mode=mode):
                result = self.run_capability_gate(mode)
                self.assertNotEqual(result.returncode, 0, result.stderr)
        supported = self.run_capability_gate("supported")
        self.assertEqual(supported.returncode, 0, supported.stderr)

    def test_extracted_profile_parser_rejects_unverifiable_helper_json(self):
        valid = self.valid_profile()
        cases = {
            "valid": (valid, True),
            "malformed": ("{not-json", False),
            "non-dict": ([], False),
            "missing": ({key: value for key, value in valid.items() if key != "argc"}, False),
            "inherited bypass": ({**valid, "bypass": ["permission"]}, False),
            "unknown kind": ({**valid, "kind": "gemini"}, False),
            "blanket flags": ({**valid, "without": ["bypass", "flags"]}, False),
            "model non-string": (
                {**valid, "model": {"value": None, "source": "UNKNOWN"}},
                False,
            ),
            "thinking non-string": (
                {**valid, "thinking": {"value": 7, "source": "UNKNOWN"}},
                False,
            ),
        }
        for name, (payload, accepted) in cases.items():
            with self.subTest(case=name):
                result = self.run_profile_parser(payload)
                if accepted:
                    self.assertEqual(result.returncode, 0, result.stderr)
                else:
                    self.assertNotEqual(result.returncode, 0, result.stderr)

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

    def test_policy_has_capability_and_fail_closed_target_gate(self):
        section = self.selective_profile_section(
            PROTOCOL, "## Selective worker launch-profile gate"
        ).lower()
        required_phrases = (
            'helper="$here/launch_profile.py"',
            'python3 "$helper" --help',
            "does not support --without bypass",
            "profile_json",
            "python3 -c",
            "destination pane",
            "caller environment",
            "inherited inline settings",
            "process-info",
            "no destination config",
            "not an immutable start snapshot",
            "supported local evidence",
            "refusing to start",
        )
        for phrase in required_phrases:
            self.assertIn(phrase.lower(), section, phrase)

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
