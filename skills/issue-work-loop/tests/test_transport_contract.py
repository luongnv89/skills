#!/usr/bin/env python3
"""Focused regression tests for the issue-work-loop transport contract."""

from __future__ import annotations

import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
