#!/usr/bin/env python3
"""Contract tests for issue-work-loop: dependency preflight and final report,
the Herdr transport, and worker launch.

One section per contract; each section's comment block says what it covers.

Run directly (stdlib unittest only):
    python3 -m unittest discover -s skills/issue-work-loop/tests -p 'test_*.py'
"""


from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


# ============================================================================
# dependency_and_report_contract
# Regression tests for the dependency lease lifecycle and final-report contract.
# ============================================================================

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_MD = SKILL_DIR / "SKILL.md"
OUTPUT_FORMAT = SKILL_DIR / "references" / "output-format.md"
CLEANUP = SKILL_DIR / "references" / "cleanup.md"

FAKE_ASM = """#!/bin/sh
echo "$*" >> "$ASM_LOG"
if [ "$1" = deps ] && [ -n "$ASM_NO_DEPS" ]; then
  echo 'Error: Unknown command: "deps"' >&2; exit 2
fi
if [ "$1 $2" = "deps acquire" ]; then
  case " $ASM_FAIL " in
    *" $3 "*) echo "Error: Skill \\"$3\\" not found" >&2; exit 1 ;;
  esac
  printf '{"name": "%s", "path": "%s/%s", "skillMdPath": "%s/%s/SKILL.md"}\\n' "$3" "$ASM_ROOT" "$3" "$ASM_ROOT" "$3"
  exit 0
fi
echo '{}'
"""


def section(text: str, heading: str) -> str:
    start = text.index(heading)
    body = text[start:]
    nxt = body.find("\n## ", len(heading))
    return body if nxt < 0 else body[:nxt]


def frontmatter_dependencies(text: str) -> list[str]:
    fm = text.split("---", 2)[1]
    match = re.search(r"^dependencies:\n((?:  - .+\n)+)", fm, re.MULTILINE)
    if not match:
        return []
    return [line.strip()[2:].strip() for line in match.group(1).splitlines()]


class DependencyLeaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = SKILL_MD.read_text(encoding="utf-8")
        cls.preflight = section(cls.skill, "## Dependency Preflight (mandatory)")
        blocks = re.findall(r"```bash\n(.*?)```", cls.preflight, re.DOTALL)
        cls.snippet = blocks[0]

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        asm = self.bin / "asm"
        asm.write_text(FAKE_ASM, encoding="utf-8")
        asm.chmod(0o755)
        self.log = self.tmp / "asm.log"
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def run_snippet(self, mode, fail="", with_asm=True, no_deps=False):
        path_dirs = [str(self.bin)] if with_asm else []
        env = {
            "PATH": os.pathsep.join(path_dirs + ["/usr/bin", "/bin"]),
            "TMPDIR": str(self.tmp),
            "ASM_LOG": str(self.log),
            "ASM_ROOT": str(self.tmp / "skills"),
            "ASM_FAIL": fail,
            "ASM_NO_DEPS": "1" if no_deps else "",
            "mode": mode,
            "number": "42",
        }
        return subprocess.run(
            ["bash", "-c", self.snippet],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def calls(self):
        if not self.log.exists():
            return []
        return self.log.read_text(encoding="utf-8").splitlines()

    def acquired(self):
        return [c.split()[2] for c in self.calls() if c.startswith("deps acquire")]

    def test_frontmatter_declares_every_invoked_skill(self):
        self.assertEqual(
            sorted(frontmatter_dependencies(self.skill)),
            ["herdr-agent", "issue-pr-review", "issue-resolver"],
        )

    def test_pr_mode_never_acquires_issue_resolver(self):
        result = self.run_snippet("pr")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.acquired(), ["herdr-agent", "issue-pr-review"])
        self.assertIn("deps discover issue-work-loop --json", self.calls())

    def test_issue_mode_acquires_all_three_under_one_session(self):
        result = self.run_snippet("issue")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.acquired(), ["herdr-agent", "issue-pr-review", "issue-resolver"]
        )
        sessions = {
            c.split("--session ")[1].split()[0]
            for c in self.calls()
            if c.startswith("deps acquire")
        }
        self.assertEqual(len(sessions), 1, sessions)
        self.assertTrue(next(iter(sessions)).startswith("iwl-issue-42-"))

    def test_failed_acquisitions_are_collected_then_released(self):
        result = self.run_snippet("issue", fail="issue-pr-review issue-resolver")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("issue-pr-review", result.stderr)
        self.assertIn("issue-resolver", result.stderr)
        self.assertTrue(any(c.startswith("deps release --session") for c in self.calls()))

    def test_missing_asm_stops_with_installer_hint(self):
        result = self.run_snippet("pr", with_asm=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("npm install -g agent-skill-manager", result.stderr)

    def test_asm_without_deps_stops_with_upgrade_hint_not_missing_skills(self):
        result = self.run_snippet("issue", no_deps=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("agent-skill-manager@latest", result.stderr)
        self.assertNotIn("Missing required skill", result.stderr)
        self.assertEqual(self.acquired(), [])

    def test_release_runs_at_every_terminal_outcome(self):
        lowered = self.preflight.lower()
        for phrase in ("finally", "every terminal outcome", "--no-cleanup", "asm deps release"):
            self.assertIn(phrase, lowered, phrase)
        cleanup = CLEANUP.read_text(encoding="utf-8")
        self.assertIn('asm deps release --session "$iwl_session" --json', cleanup)


class FinalReportContractTests(unittest.TestCase):
    def test_every_final_report_opens_with_the_four_review_lines(self):
        text = OUTPUT_FORMAT.read_text(encoding="utf-8")
        headings = [
            "## Push-safety handoff",
            "## Final — CLEAN",
            "## Final — MAX_ROUNDS",
            "## Final — FAILED / ALREADY_RESOLVED / ABORTED",
        ]
        for heading in headings:
            with self.subTest(heading=heading):
                block = re.search(r"```text\n(.*?)```", section(text, heading), re.DOTALL)
                lines = [
                    line.strip()
                    for line in block.group(1).splitlines()[1:]
                    if line.strip() and not line.startswith("                 ")
                ]
                labels = [line.split(":", 1)[0] for line in lines[:4]]
                self.assertEqual(labels, ["Result", "Evidence", "Uncertainty", "Decision"])

    def test_skill_body_requires_understanding_criteria(self):
        criteria = section(SKILL_MD.read_text(encoding="utf-8"), "## Acceptance Criteria")
        for phrase in ("Result:", "Uncertainty:", "Decision:", "unconfirmed"):
            self.assertIn(phrase, criteria, phrase)


# ============================================================================
# transport_contract
# Focused regression tests for the issue-work-loop transport contract.
# ============================================================================

SKILL = Path(__file__).resolve().parents[2]
LOOP_PROTOCOL = SKILL / "issue-work-loop" / "references" / "loop-protocol.md"
AGENT_PROMPTS = SKILL / "issue-work-loop" / "references" / "agent-prompts.md"
HERDR_DELIVERY = SKILL / "herdr-agent" / "references" / "delivery-and-waiting.md"


def subsection(text: str, heading: str, next_heading: str) -> str:
    start = text.index(heading)
    end = text.index(next_heading, start + len(heading))
    return text[start:end]


class TransportContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = LOOP_PROTOCOL.read_text(encoding="utf-8")
        cls.prompts = AGENT_PROMPTS.read_text(encoding="utf-8")
        cls.delivery = HERDR_DELIVERY.read_text(encoding="utf-8")

    def test_normal_detected_agent_path_delegates_to_atomic_herdr_wait(self):
        normal = subsection(
            self.protocol,
            "### Detected-agent path (normal)",
            "### Explicit no-agent fallback",
        )
        for phrase in (
            "preflight_send.py",
            "herdr agent prompt",
            "--wait",
            "herdr agent read",
            "recent-unwrapped",
            "one server-side request",
            "working, blocked, or",
            "unverifiable target stops dispatch",
        ):
            self.assertIn(phrase, normal, phrase)

        retired_steps = (
            "Capture recent-unwrapped baseline.",
            "Mint a fresh completion marker.",
            "preflight_send.py immediately before `pane run`",
            "Wait with `wait_for_idle.py` using baseline + marker.",
        )
        for phrase in retired_steps:
            self.assertNotIn(phrase, normal, phrase)

    def test_legacy_transport_is_only_an_explicit_verified_no_agent_fallback(self):
        fallback = subsection(
            self.protocol,
            "### Explicit no-agent fallback",
            "## Max rounds and handoff",
        )
        for phrase in (
            "preflight exits 5",
            "agent_not_found",
            "explicitly verified fallback",
            "pane run",
            "wait_for_idle.py",
            "not the normal transport",
        ):
            self.assertIn(phrase, fallback, phrase)

        for phrase in ("agent_not_found", "pane run", "wait_for_idle.py", "fallback"):
            self.assertIn(phrase, self.delivery, phrase)

    def test_named_failure_outcomes_are_reported_without_blind_resend(self):
        transport = subsection(
            self.protocol,
            "## Herdr send/wait contract",
            "## Max rounds and handoff",
        )
        for phrase in (
            "agent_blocked",
            "agent_prompt_stalled",
            "timeout",
            "BLOCKED",
            "STALLED",
            "TIMEOUT",
            "never treat them as replies",
            "blindly resend",
            "never send another task or type into the dialog",
        ):
            self.assertIn(phrase, transport, phrase)

    def test_worker_prompts_delegate_and_keep_boot_switches_separate(self):
        intro = self.prompts[: self.prompts.index("## Context probe")]
        for phrase in (
            "Phase 4 — Prompt Safely",
            "Phase 5 — Read and Verify",
            "preflight_send.py",
            "herdr agent prompt ... --wait",
            "recent-unwrapped",
            "agent_not_found",
            "never blindly resend",
            "mode-switch keystrokes are separate from task sends",
            "Repeat after FRESHEN",
            "skip-permissions flag",
        ):
            self.assertIn(phrase, intro, phrase)

        for phrase in (
            "with baseline, fresh completion marker, preflight, wait, and reply-delta read",
            "pane run",
            "wait_for_idle.py",
        ):
            self.assertNotIn(phrase, intro, phrase)


# ============================================================================
# worker_launch_contract
# Regression tests for the issue-work-loop worker launch contract.
# ============================================================================

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
