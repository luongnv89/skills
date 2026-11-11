#!/usr/bin/env python3
"""Contract tests for issue-work-loop: dependency preflight and final report,
the Herdr transport, worker launch, and the Herdr desktop app backend.

One section per contract; each section's comment block says what it covers.

Run directly (stdlib unittest only):
    python3 -m unittest discover -s meta/issue-work-loop/tests -p 'test_*.py'
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


# ============================================================================
# dependency_and_report_contract
# Regression tests for the dependency lease lifecycle and final-report contract.
# ============================================================================

SKILL_DIR = Path(__file__).resolve().parents[3] / "skills" / "issue-work-loop"
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

# Records any call; the Herdr desktop app run must never reach the TUI CLI.
TRIPWIRE = """#!/bin/sh
echo "$(basename "$0") $*" >> "$CLI_LOG"
exit 99
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
        self.cli_log = self.tmp / "cli.log"
        # herdr, hc and herdr-app live outside self.bin so with_asm=False still
        # removes only asm. Each records a call and fails: preflight checks
        # existence with command -v and must never run them.
        self.cli = self.tmp / "cli"
        self.cli.mkdir()
        for name in ("herdr", "hc", "herdr-app"):
            stub = self.cli / name
            stub.write_text(TRIPWIRE, encoding="utf-8")
            stub.chmod(0o755)
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def run_snippet(self, mode, fail="", with_asm=True, no_deps=False, runtime="tui"):
        path_dirs = [str(self.bin)] if with_asm else []
        path_dirs.append(str(self.cli))
        env = {
            "PATH": os.pathsep.join(path_dirs + ["/usr/bin", "/bin"]),
            "TMPDIR": str(self.tmp),
            "ASM_LOG": str(self.log),
            "ASM_ROOT": str(self.tmp / "skills"),
            "ASM_FAIL": fail,
            "ASM_NO_DEPS": "1" if no_deps else "",
            "CLI_LOG": str(self.cli_log),
            "mode": mode,
            "number": "42",
        }
        if runtime in ("tui", "both"):
            env["HERDR_ENV"] = "1"
        if runtime in ("app", "both"):
            env["HC_TERMINAL_ID"] = "t2x"
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

    def cli_calls(self):
        if not self.cli_log.exists():
            return []
        return self.cli_log.read_text(encoding="utf-8").splitlines()

    def test_frontmatter_declares_every_invoked_skill(self):
        self.assertEqual(
            sorted(frontmatter_dependencies(self.skill)),
            ["hc-agent", "herdr-agent", "issue-pr-review", "issue-resolver"],
        )

    def test_app_runtime_acquires_hc_agent_and_never_calls_herdr(self):
        for mode, expected in (
            ("pr", ["hc-agent", "issue-pr-review"]),
            ("issue", ["hc-agent", "issue-pr-review", "issue-resolver"]),
        ):
            with self.subTest(mode=mode):
                self.log.unlink(missing_ok=True)
                result = self.run_snippet(mode, runtime="app")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.acquired(), expected)
                self.assertEqual(self.cli_calls(), [])

    def test_tui_wins_when_both_runtimes_are_set(self):
        result = self.run_snippet("pr", runtime="both")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.acquired(), ["herdr-agent", "issue-pr-review"])

    def test_no_runtime_stops_before_any_acquire(self):
        result = self.run_snippet("issue", runtime="none")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No Herdr runtime detected", result.stderr)
        self.assertIn("HERDR_ENV=1", result.stderr)
        self.assertIn("HC_TERMINAL_ID", result.stderr)
        self.assertEqual(self.acquired(), [])

    def test_app_runtime_with_a_missing_cli_stops_before_any_acquire(self):
        # bash's `command -v hc herdr-app` exits 0 when only one exists, so
        # the gate must check each binary on its own.
        (self.cli / "herdr-app").unlink()
        result = self.run_snippet("pr", runtime="app")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Herdr desktop app CLIs unavailable: herdr-app", result.stderr)
        self.assertEqual(self.acquired(), [])
        self.assertEqual(self.cli_calls(), [])

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

SKILL = Path(__file__).resolve().parents[3] / "skills"
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

SKILLS = Path(__file__).resolve().parents[3] / "skills"
LOOP_SKILL = SKILLS / "issue-work-loop" / "SKILL.md"
PROTOCOL = SKILLS / "issue-work-loop" / "references" / "loop-protocol.md"
PROFILE = SKILLS / "herdr-agent" / "scripts" / "launch_profile.py"
FAKE_HERDR = SKILLS.parent / "meta" / "herdr-agent" / "tests" / "fake_herdr.py"
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


# ============================================================================
# app_backend_contract
# The Herdr desktop app backend (hc-agent): runtime rule, launch-profile gate,
# seconds-based timeouts, close policy, and docs naming both runtimes.
# ============================================================================

FLEET_BACKEND = SKILLS / "issue-work-loop" / "references" / "fleet-backend.md"
HC_AGENT = SKILLS / "hc-agent"
HC_BIN = SKILLS.parent / "meta" / "hc-agent" / "tests" / "bin"
META_README = SKILLS.parent / "meta" / "issue-work-loop" / "docs" / "README.md"
APP_ROOT = "t1"


def bash_blocks(text: str) -> list[str]:
    return re.findall(r"```bash\n(.*?)```", text, re.DOTALL)


class AppBackendContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = FLEET_BACKEND.read_text(encoding="utf-8")
        cls.gate_block, cls.probe_block = bash_blocks(section(cls.doc, "## App launch-profile gate"))[:2]
        cls.parser_block = bash_blocks(
            WorkerLaunchContractTests.selective_profile_section(
                None, PROTOCOL, "### Probe and target evidence"
            )
        )[0]

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="issue_work_loop_app_"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def bash(self, script, **env):
        # The interpreter running these tests, not whatever python3 /usr/bin has.
        base = {
            "PATH": f"{Path(sys.executable).parent}{os.pathsep}/usr/bin:/bin",
            "HOME": str(self.tmp),
            "FAKE_HC_PYTHON": sys.executable,
        }
        base.update(env)
        return subprocess.run(
            ["bash", "-c", script], env=base, text=True, capture_output=True, check=False
        )

    def test_runtime_rule_puts_tui_first_and_stops_without_either(self):
        rule = section(self.doc, "## Runtime detection")
        rows = [line for line in rule.splitlines() if line.startswith("| ")]
        tui, app, neither = rows[1:4]
        self.assertIn("HERDR_ENV=1", tui)
        self.assertIn("also set", tui)
        self.assertIn("herdr-agent", tui)
        self.assertIn("HC_TERMINAL_ID", app)
        self.assertIn("hc-agent", app)
        self.assertIn("No Herdr runtime detected", neither)
        self.assertIn("never calls `herdr` in the app", rule)

    def test_app_gate_accepts_hc_agent_and_requires_agent_py(self):
        ok = self.bash(self.gate_block, fleet_dir=str(HC_AGENT))
        self.assertEqual(ok.returncode, 0, ok.stderr)
        partial = self.tmp / "partial"
        (partial / "scripts").mkdir(parents=True)
        for script in ("launch_profile.py", "hclib.py"):  # everything but agent.py
            shutil.copy(HC_AGENT / "scripts" / script, partial / "scripts")
        missing = self.bash(self.gate_block, fleet_dir=str(partial))
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("hc-agent scripts are unavailable", missing.stderr)
        self.assertNotEqual(self.bash(self.gate_block).returncode, 0)

    def probe(self, root_argv, without_bypass=True):
        state = self.tmp / "hc-state.json"
        record = {
            "address": APP_ROOT, "argv": root_argv, "created_ms": 1000, "cwd": "/work/project",
            "foreground": {"argv": root_argv, "cwd": "/work/project", "name": "x", "pid": 42},
            "labels": {"herdr.space": "sp1", "herdr.tab": "tb1"}, "state": "live",
            "status": {"app": "claude-code", "msg": "", "state": "idle"},
            "status_ms": 1000, "turn": 1, "parent": None, "die_with_parent": False,
        }
        state.write_text(json.dumps({"terminals": {APP_ROOT: record}, "app": {"spaces": []}, "log": []}))
        block = self.probe_block
        if not without_bypass:
            block = block.replace(" --without bypass", "")
        script = "\n".join((
            f"helper={json.dumps(str(HC_AGENT / 'scripts' / 'launch_profile.py'))}",
            "main_model=''", "main_thinking=''", "worker_profile_args=()", "worker_native_args=()",
            block, 'printf "%s" "$profile_json"',
        ))
        result = self.bash(
            script,
            PATH=os.pathsep.join((str(HC_BIN), str(Path(sys.executable).parent), "/usr/bin", "/bin")),
            FAKE_HC_STATE=str(state),
            HC_TERMINAL_ID=APP_ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        log = json.loads(state.read_text())["log"]
        self.assertTrue(log, "the probe must read the root through hc")
        self.assertFalse([call for call in log if call[0] == "herdr"], log)
        return result.stdout

    def parse(self, profile_json):
        helper = self.tmp / "profile-helper.py"
        helper.write_text("import os\nprint(os.environ['PROFILE_JSON'], end='')\n")
        script = "\n".join((
            "root_pane='root'", "main_model=''", "main_thinking=''",
            "worker_profile_args=()", "worker_native_args=()", self.parser_block,
        ))
        return self.bash(script, helper=str(helper), PROFILE_JSON=profile_json)

    def test_app_probe_uses_root_and_its_json_passes_the_loop_parser(self):
        self.assertIn('--root "$HC_TERMINAL_ID"', self.probe_block)
        self.assertNotIn("--root-pane", self.probe_block)
        self.assertIn("--without bypass", self.probe_block)
        root_argv = ["/opt/agents/bin/claude", "--dangerously-skip-permissions"]
        accepted = self.parse(self.probe(root_argv))
        self.assertEqual(accepted.returncode, 0, accepted.stderr)
        rejected = self.parse(self.probe(root_argv, without_bypass=False))
        self.assertNotEqual(rejected.returncode, 0, "inherited bypass must fail closed")

    def test_app_timeouts_are_seconds_and_reads_use_turn_ids(self):
        spawn = bash_blocks(section(self.doc, "## App spawn"))[0]
        self.assertRegex(spawn, r"--start \"\$worker_name\" --cwd \"\$project_dir\" --timeout 60(?!\d)")
        self.assertNotIn("--pane", spawn)
        self.assertNotIn("--env", spawn)
        transport = section(self.doc, "## App send, wait, and read")
        prompt, read = bash_blocks(transport)[:2]
        self.assertRegex(prompt, r'agent\.py" prompt "\$t" - --timeout 180(?!\d)')
        self.assertIn('read "$t" --turn "$turn"', read)
        self.assertIn("250000", transport)
        for code in range(0, 10):
            self.assertRegex(transport, rf"\n\| {code} \|")

    def test_app_never_recommends_permission_bypass(self):
        for flag in ("--dangerously-skip-permissions", "bypassPermissions"):
            for line in self.doc.splitlines():
                if flag in line:
                    self.assertIn("never", line.lower(), line)
        boot = section(self.doc, "## App boot gate")
        for phrase in ("hc keys \"$t\" shift+tab", "not yet verified live", "fails closed",
                       "--without bypass", "App boot mode unverifiable"):
            self.assertIn(phrase, boot, phrase)

    def test_close_policy_needs_explicit_approval_and_own_workers_only(self):
        policy = section(self.doc, "## Close-confirmation policy")
        for phrase in (
            "Rule 8", "Confirm destruction", "invoking the loop approves",
            "`work_loop.auto_cleanup: true`", "**not** approval", "ask before closing",
            "leaves them open", "spawn ledger", "--confirmed", "Never pass root",
        ):
            self.assertIn(phrase, policy, phrase)

    def test_differing_steps_are_named(self):
        steps = section(self.doc, "## Steps that differ in the app").lower()
        for phrase in (
            "no no-agent fallback", "one call", "no `--env`", "seconds", "turn id",
            "close-confirmation policy", "not verified live", "polled", "badges or notifications",
        ):
            self.assertIn(phrase, steps, phrase)

    def test_docs_name_both_runtimes(self):
        for path in (SKILL_MD, META_README):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                for phrase in ("Herdr TUI", "Herdr desktop app", "hc-agent"):
                    self.assertTrue(phrase in text, f"{path.name} lacks {phrase!r}")
        must_not = section(SKILL_MD.read_text(encoding="utf-8"), "## What You Must Not Do")
        self.assertIn("Call `herdr` in the Herdr desktop app", must_not)
        self.assertIn("Close a terminal or pane this run did not spawn", must_not)


if __name__ == "__main__":
    unittest.main()
