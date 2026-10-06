#!/usr/bin/env python3
"""Regression tests for the dependency lease lifecycle and final-report contract."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
