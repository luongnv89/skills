"""Stdlib fixtures for website-agent-readiness's plan renderer.

Run directly from the repository root::

    python3 -m unittest discover -s meta/website-agent-readiness/tests -p 'test_*.py'

Each test writes a triage.json to a temporary directory, renders it, and reads
the plan back.
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = (Path(__file__).resolve().parents[3] / "extras" / "website-agent-readiness"
          / "scripts" / "render_plan.py")
sys.path.insert(0, str(SCRIPT.parent))

import render_plan  # noqa: E402


GOOGLE_URL = "https://developers.google.com/search/docs/fundamentals/ai-optimization-guide"
SITE = "https://example.com"


def task(check, category, prompt=None):
    return {
        "check": check,
        "category": category,
        "title": f"Fix {check}",
        "message": f"{check} failed",
        "prompt": prompt if prompt is not None else f"Add {check} support to the site.",
        "guide": f"https://isitagentready.com/.well-known/agent-skills/{check}/SKILL.md",
        "effort": "S",
    }


def triage(tasks, deferred=(), neutral=()):
    return {
        "targetUrl": SITE,
        "level": 1,
        "levelName": "Basic",
        "scannedAt": "2026-11-25T00:00:00Z",
        "counts": {"pass": 3, "fail": len(tasks), "neutral": len(neutral)},
        "nextLevel": {"target": 2, "name": "Readable"},
        "phases": [{"id": "P1", "title": "Content", "tasks": list(tasks)}],
        "deferred": list(deferred),
        "neutral": list(neutral),
        "passing": [],
    }


def render(t):
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "plan.md"
        (Path(d) / "triage.json").write_text(json.dumps(t))
        argv = sys.argv
        sys.argv = ["render_plan.py", d, str(out)]
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                rc = render_plan.main()
        finally:
            sys.argv = argv
        assert rc == 0, rc
        return out.read_text()


def ai_notes(plan):
    return [ln for ln in plan.splitlines()
            if ln.startswith("**Note:**") and GOOGLE_URL in ln]


class AiTextNoteTests(unittest.TestCase):
    def test_each_check_alone_gives_one_note(self):
        for check in ("llmsTxt", "llmsFullTxt", "markdownNegotiation"):
            with self.subTest(check=check):
                plan = render(triage([task("sitemap", "discoverability"),
                                      task(check, "contentAccessibility")]))
                notes = ai_notes(plan)
                self.assertEqual(len(notes), 1)
                self.assertIn("tasks 1.2 publish", notes[0])
                self.assertIn("AI agents and other tools", notes[0])
                self.assertIn("Google Search does not use llms.txt", notes[0])

    def test_all_three_checks_give_one_note(self):
        plan = render(triage([task("llmsTxt", "contentAccessibility"),
                              task("llmsFullTxt", "contentAccessibility"),
                              task("markdownNegotiation", "contentAccessibility")]))
        notes = ai_notes(plan)
        self.assertEqual(len(notes), 1)
        self.assertIn("tasks 1.1, 1.2, 1.3 publish", notes[0])

    def test_no_ai_text_task_gives_no_note(self):
        self.assertEqual(ai_notes(render(triage([task("sitemap", "discoverability")]))), [])

    def test_deferred_or_neutral_row_gives_no_note(self):
        row = {"check": "llmsTxt", "category": "contentAccessibility", "message": "missing"}
        plan = render(triage([task("sitemap", "discoverability")],
                             deferred=[row], neutral=[dict(row, check="markdownNegotiation")]))
        self.assertEqual(ai_notes(plan), [])

    def test_prompt_text_never_triggers_the_note(self):
        plan = render(triage([task("sitemap", "discoverability",
                                   prompt="Also publish llms.txt and llms-full.txt.")]))
        self.assertEqual(ai_notes(plan), [])

    def test_note_sits_in_the_header_and_creates_no_structure(self):
        plan = render(triage([task("llmsTxt", "contentAccessibility")]))
        header = plan.split("\n## Phase ", 1)[0]
        self.assertEqual(len(ai_notes(header)), 1)
        note = ai_notes(plan)[0]
        self.assertNotIn("\n", note)
        self.assertFalse(note.startswith(("#", "- [")))
        self.assertIsNone(re.match(r"^\*\*[A-Za-z ]+\*\*: ", note))

    def test_task_list_is_unchanged(self):
        t = triage([task("llmsTxt", "contentAccessibility"),
                    task("markdownNegotiation", "contentAccessibility")])
        with_note = render(t)
        saved = render_plan.AI_TEXT_CHECKS
        render_plan.AI_TEXT_CHECKS = ()
        try:
            without = render(t)
        finally:
            render_plan.AI_TEXT_CHECKS = saved
        self.assertEqual(ai_notes(without), [])
        self.assertEqual(with_note.replace(ai_notes(with_note)[0] + "\n", "", 1), without)

    def test_plan_format_checks_still_hold(self):
        plan = render(triage([task("llmsTxt", "contentAccessibility"),
                              task("llmsFullTxt", "contentAccessibility")]))
        self.assertEqual(len(re.findall(r"^#{3,4} Task ", plan, flags=re.M)), 2)
        self.assertEqual(len(re.findall(r"^\*\*Effort\*\*: (XS|S|M|L|XL)$", plan, flags=re.M)), 2)
        bad = [b.split(":")[0] for b in re.split(r"^#### Task ", plan, flags=re.M)[1:]
               if not re.search(r"^- \[ \] ", b, flags=re.M)]
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
