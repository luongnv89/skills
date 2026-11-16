"""Static contract checks for the qualitative brand-risk policy.

These tests inspect the skill instructions and schemas. They do not implement a
risk classifier or scoring framework.
"""

import json
from pathlib import Path
import re
import unittest


SKILL_DIR = Path(__file__).resolve().parents[3] / "skills" / "brand-name-checker"
SKILL_TEXT = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
SYNTH_TEXT = (SKILL_DIR / "agents" / "synthesizer.md").read_text(encoding="utf-8")


def canonical_matrix_rows(text: str) -> dict[str, str]:
    """Extract the three policy rows without evaluating their meaning."""
    section = text.split("#### Qualitative risk matrix", 1)[1]
    section = section.split("Unknown policy:", 1)[0]
    rows = {}
    for line in section.splitlines():
        match = re.match(r"^\| \*\*(High|Moderate|Low)\*\* \| (.+) \|$", line)
        if match:
            rows[match.group(1)] = match.group(2)
    return rows


def synthesizer_json_schema() -> dict:
    """Parse the unfilled JSON schema from the synthesizer instructions."""
    output = SYNTH_TEXT.split("## Output schemas", 1)[1]
    match = re.search(r"```json\n(\{.*?\})\n```", output, re.DOTALL)
    if not match:
        raise AssertionError("synthesizer JSON schema fence is missing")
    return json.loads(match.group(1))


class RiskPolicyContractTests(unittest.TestCase):
    def test_canonical_matrix_rows_cover_each_policy_class(self) -> None:
        rows = canonical_matrix_rows(SKILL_TEXT)
        self.assertEqual(set(rows), {"High", "Moderate", "Low"})

        row_clauses = {
            "High": (
                "two or more confirmed non-exact social handle collisions",
                "confirmed collision on **any target registry**",
                "active `.com` in the same industry",
                "active trademark conflict in Nice Classes 9, 35, 42",
            ),
            "Moderate": (
                "one confirmed non-exact social handle collision",
                "different-industry active `.com`",
                "similar trademark",
                "confirmed collision on a non-target registry",
                "unknown/unverifiable check or target intent",
            ),
            "Low": (
                "Every required check and target intent is explicitly verified",
                "`.com` is verified available or parked",
            ),
        }
        for level, clauses in row_clauses.items():
            for clause in clauses:
                with self.subTest(level=level, clause=clause):
                    self.assertIn(clause, rows[level])

        self.assertNotIn("parked", rows["Moderate"])
        self.assertIn("parked", rows["Low"])

    def test_precedence_unknown_and_alternative_policy(self) -> None:
        clauses = (
            "High > Moderate > Low",
            "provisional Moderate + Modify",
            "Unknown is not a confirmed collision",
            "An existing High finding remains High",
            "No averaging or mitigation reduces High",
            "Checks skipped by the Early-Exit Rule remain skipped, not cleared",
            "mitigation or available alternatives cannot lower the High result",
            "Any alternative that was not checked through the applicable sources must be labeled **unverified**",
        )
        for clause in clauses:
            with self.subTest(clause=clause):
                self.assertIn(clause, SKILL_TEXT)

    def test_exact_early_exit_preserves_skipped_not_clear(self) -> None:
        self.assertIn(
            "exact handle collision on any of the 6 platforms returns Abandon at once",
            SKILL_TEXT,
        )
        self.assertIn("Report those checks as skipped, not clear", SKILL_TEXT)

    def test_compact_skill_output_keeps_policy_rationale(self) -> None:
        self.assertNotIn("```json", SKILL_TEXT)
        self.assertIn(
            "RISK: [Low | Moderate | High] - [highest matching trigger, evidence, and policy rationale]",
            SKILL_TEXT,
        )
        self.assertIn(
            "no active site was found; do not infer availability",
            SKILL_TEXT,
        )

    def test_synthesizer_references_parent_without_copying_matrix(self) -> None:
        clauses = (
            "../SKILL.md#step-5-risk-assessment",
            "fail closed",
            "untrusted evidence",
            "observed facts",
            "Skipped (not cleared)",
            "SKILL.md` Step 6 and Final Action",
        )
        for clause in clauses:
            with self.subTest(clause=clause):
                self.assertIn(clause, SYNTH_TEXT)

        forbidden_duplicate_policy = (
            "Qualitative risk matrix",
            "| **High** |",
            "| **Moderate** |",
            "| **Low** |",
            "High > Moderate > Low",
            "0-10",
            "11-40",
            "41+",
            "0-20",
            "0-30",
            "0.85",
            "points",
            "total_score",
            '"scores"',
            "X/100",
        )
        for token in forbidden_duplicate_policy:
            with self.subTest(token=token):
                self.assertNotIn(token, SYNTH_TEXT)

    def test_synthesizer_schema_is_unfilled_and_timestamped(self) -> None:
        for token in ("myproductname", "example-org", "2026-03-24", "Total Score"):
            with self.subTest(token=token):
                self.assertNotIn(token, SYNTH_TEXT)

        schema = synthesizer_json_schema()
        for field in (
            "timestamp",
            "risk_level",
            "recommendation",
            "policy_rationale",
            "unknown_checks",
            "skipped_checks",
        ):
            with self.subTest(field=field):
                self.assertIn(field, schema)
        self.assertEqual(schema["timestamp"], "<ISO-8601 verification timestamp>")
        for source in ("social", "registries", "domains", "trademarks"):
            with self.subTest(source=source):
                self.assertEqual(schema["findings"][source][0]["verified_at"], "<ISO-8601 verification timestamp>")

    def test_corrected_clearance_language_is_present(self) -> None:
        self.assertNotIn("Confirm safe to use", SKILL_TEXT)
        self.assertNotIn("No active site", SKILL_TEXT)
        self.assertNotIn("downgrade risk", SKILL_TEXT)


AGENTS_DIR = SKILL_DIR / "agents"


def worker_text(name: str) -> str:
    return (AGENTS_DIR / f"{name}.md").read_text(encoding="utf-8")


class WorkerAlignmentTests(unittest.TestCase):
    """Workers use the source-checks.md statuses and leave risk to SKILL.md Step 5."""

    def test_trademark_worker_has_no_second_risk_matrix(self) -> None:
        text = worker_text("trademark-checker")
        for token in (
            "Conflict Risk Scoring",
            "0.85",
            "0.60",
            "similarity_score",
            "conflict_risk",
            '"risk_level"',
            "high_risk_conflicts",
            "moderate_risk_conflicts",
        ):
            with self.subTest(token=token):
                self.assertNotIn(token, text)

    def test_social_worker_uses_exact_and_non_exact_statuses(self) -> None:
        text = worker_text("social-checker")
        self.assertNotIn("unclear", text)
        self.assertEqual(text.count("available|taken (exact)|similar (non-exact)|unknown"), 6)

    def test_registry_worker_reports_similar_and_unknown(self) -> None:
        text = worker_text("registry-checker")
        self.assertNotIn("available|taken|error", text)
        self.assertEqual(text.count("available|taken|similar|unknown"), 4)

    def test_domain_worker_never_infers_availability_from_no_site(self) -> None:
        text = worker_text("domain-checker")
        self.assertNotIn("No active site", text)
        self.assertNotIn("|error", text)
        self.assertIn("no active site was found; do not infer availability", text)
        self.assertIn('"com_status": "available|parked|active|unknown"', text)
        for tld in ('"co": {', '"eu": {', '"fr": {', "regional_tlds"):
            with self.subTest(tld=tld):
                self.assertNotIn(tld, text)

    def test_skill_checks_the_three_reported_tlds(self) -> None:
        self.assertNotIn("`.app`, `.co`, `.eu`, `.fr`:", SKILL_TEXT)
        self.assertIn("DOMAIN: .com ([status]) | .io ([status]) | .app ([status])", SKILL_TEXT)
        self.assertNotIn("is unchanged", SKILL_TEXT)


if __name__ == "__main__":
    unittest.main()
