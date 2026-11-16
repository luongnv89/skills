"""Checks for dev-machine-setup: runtime floors, approval tags, and stale notes.

Run: python3 -m unittest discover -s meta/dev-machine-setup/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import re
import unittest


REPO = Path(__file__).resolve().parents[3]
SKILL_DIR = REPO / "skills" / "dev-machine-setup"
REFS = SKILL_DIR / "references"


def _load_detect_env():
    spec = importlib.util.spec_from_file_location("detect_env", SKILL_DIR / "scripts" / "detect_env.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


detect_env = _load_detect_env()

# A remote installer piped into a shell: `curl … | [sudo] sh|bash`, `sh|bash -c "$(curl …)"`, `irm … | iex`.
PIPE = re.compile(r"curl\s[^|`]*\|\s*(?:sudo\s+(?:-\S+\s+)*)?(sh|bash)\b|(sh|bash)\s+-c\s+\\?\"\$\(curl\s|irm\s[^|`]*\|\s*iex\b")


def _finding_ids(tools: dict[str, str | None]) -> set[str]:
    return {f["id"] for f in detect_env.findings("linux", "x86_64", tools, ["apt"])}


def _all_text() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in sorted(SKILL_DIR.rglob("*.md")))


def _pipe_blocks(path: Path):
    """Yield (line_no, tag_context) for each remote-installer pipe in a fenced block.

    tag_context is the text paragraph right above the fence plus the fence lines
    above the pipe, which is where the skill puts an item's additive/mutating tag.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    in_fence = False
    fence_start = 0
    for i, line in enumerate(lines):
        if line.lstrip().startswith("````"):  # an outer example fence: its inner blocks still count
            continue
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            fence_start = i
            continue
        if in_fence and PIPE.search(line):
            j = fence_start - 1
            while j >= 0 and not lines[j].strip():
                j -= 1
            para = []
            while j >= 0 and lines[j].strip() and not lines[j].lstrip().startswith("```"):
                para.insert(0, lines[j])
                j -= 1
            yield i + 1, "\n".join(para + lines[fence_start + 1:i])


class RuntimeFloorTests(unittest.TestCase):
    def test_node_floor_is_22(self) -> None:
        self.assertEqual(detect_env.NODE_MIN_MAJOR, 22)
        self.assertIn("node-below-min", _finding_ids({"node": "v20.19.0"}))
        self.assertNotIn("node-below-min", _finding_ids({"node": "v22.12.0"}))

    def test_python_floor_is_3_11(self) -> None:
        self.assertEqual(detect_env.PYTHON_MIN_MINOR, 11)
        self.assertIn("python-below-min", _finding_ids({"python3": "Python 3.10.14"}))
        self.assertNotIn("python-below-min", _finding_ids({"python3": "Python 3.11.9"}))


class RemoteInstallerTests(unittest.TestCase):
    def test_approvals_states_the_remote_installer_rule(self) -> None:
        text = (REFS / "approvals.md").read_text(encoding="utf-8")
        self.assertIn("**Remote-installer pipes are always mutating**", text)
        rule = text.split("**Remote-installer pipes are always mutating**", 1)[1].split("\n\n", 1)[0]
        for form in ("`curl | sh`", '`/bin/bash -c "$(curl …)"`', "`irm … | iex`"):
            self.assertIn(form, rule)
        self.assertIn("URL", rule)
        self.assertIn("blanket approval never covers one", rule)

    def test_every_remote_installer_block_is_tagged_mutating(self) -> None:
        seen = 0
        for path in [SKILL_DIR / "SKILL.md", *sorted(REFS.glob("*.md"))]:
            if path.name == "session.md":  # a JSON state example, not a run-block
                continue
            for line_no, context in _pipe_blocks(path):
                seen += 1
                with self.subTest(file=path.name, line=line_no):
                    self.assertRegex(context, r"(?i)\bmutating\b")
        self.assertGreaterEqual(seen, 11)

    def test_oh_my_zsh_finding_is_mutating_in_the_example_table(self) -> None:
        text = (REFS / "approvals.md").read_text(encoding="utf-8")
        self.assertIn("| `oh-my-zsh-missing` | low | no completion/plugin baseline for zsh | mutating |", text)


class StaleNoteTests(unittest.TestCase):
    def test_no_external_scripts_repo_denials(self) -> None:
        text = _all_text()
        self.assertNotRegex(text, r"(?i)external scripts repo")
        self.assertNotIn("inbash", text)

    def test_no_provenance_link_in_debloat(self) -> None:
        self.assertNotIn("XFreeze", (REFS / "procedure.md").read_text(encoding="utf-8"))

    def test_pi_section_is_not_user_specific(self) -> None:
        text = (REFS / "agent-clis.md").read_text(encoding="utf-8")
        self.assertNotIn("This user's Pi", text)
        self.assertNotIn("pi-extensions", text)


class VersionTests(unittest.TestCase):
    def test_readme_row_matches_skill_version(self) -> None:
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        version = re.search(r"^  version: (\S+)$", skill, re.M).group(1)
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        self.assertIn(f"| [**dev-machine-setup**](skills/dev-machine-setup/) | {version} |", readme)


if __name__ == "__main__":
    unittest.main()
