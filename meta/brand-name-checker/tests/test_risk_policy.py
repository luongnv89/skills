"""Static contract checks for the qualitative brand-risk policy.

These tests inspect the skill instructions and schemas. They do not implement a
risk classifier or scoring framework.
"""

import json
from pathlib import Path
import re
import unittest


SKILL_DIR = Path(__file__).resolve().parents[3] / "extras" / "brand-name-checker"
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
SOURCE_CHECKS_TEXT = (SKILL_DIR / "references" / "source-checks.md").read_text(encoding="utf-8")
REMOVED_WORKERS = ("social-checker", "registry-checker", "domain-checker", "trademark-checker")


def worker_text(name: str) -> str:
    return (AGENTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def source_checker_output_schema() -> dict:
    """Parse the unfilled JSON output schema from the source-checker instructions."""
    output = worker_text("source-checker").split("## Output", 1)[1]
    match = re.search(r"```json\n(\{.*?\})\n```", output, re.DOTALL)
    if not match:
        raise AssertionError("source-checker JSON schema fence is missing")
    return json.loads(match.group(1))


class SourceCheckerTests(unittest.TestCase):
    """One source-checker runs every check from source-checks.md and leaves risk to SKILL.md Step 5."""

    def test_per_source_workers_are_gone(self) -> None:
        self.assertEqual(
            sorted(path.stem for path in AGENTS_DIR.glob("*.md")),
            ["source-checker", "synthesizer"],
        )
        for name in REMOVED_WORKERS:
            with self.subTest(name=name):
                self.assertNotIn(name, SKILL_TEXT)
                self.assertNotIn(name, SOURCE_CHECKS_TEXT)
                self.assertNotIn(name, SYNTH_TEXT)

    def test_skill_spawns_one_source_checker_per_check(self) -> None:
        self.assertIn("source-checker", SKILL_TEXT)
        self.assertIn("once per check", SKILL_TEXT)
        self.assertIn("returns `taken (exact)`", SKILL_TEXT)

    def test_source_checker_takes_the_four_checks(self) -> None:
        text = worker_text("source-checker")
        self.assertIn('"check": "social|registry|domain|trademark"', text)
        self.assertIn('"targets": ["<source>"]', text)
        self.assertIn("../references/source-checks.md", text)
        for section in (
            "Step 1: Social Media Check",
            "Step 2: Package Registry Check",
            "Step 3: Domain Check",
            "Step 4: Trademark Check",
        ):
            with self.subTest(section=section):
                self.assertIn(section, text)
                self.assertIn(f"## {section}", SOURCE_CHECKS_TEXT)

    def test_source_checker_output_matches_the_decision(self) -> None:
        schema = source_checker_output_schema()
        self.assertEqual(set(schema), {"check", "results"})
        self.assertEqual(set(schema["results"][0]), {"source", "status", "evidence", "checked_at"})

    def test_source_checker_has_no_risk_policy(self) -> None:
        text = worker_text("source-checker")
        self.assertIn("never assign either", text)
        for token in (
            "Conflict Risk Scoring",
            "Qualitative risk matrix",
            "0.85",
            "0.60",
            "similarity_score",
            "conflict_risk",
            '"risk_level"',
            '"recommendation"',
            "high_risk_conflicts",
            "moderate_risk_conflicts",
            "myproductname",
            "2026-03-24",
        ):
            with self.subTest(token=token):
                self.assertNotIn(token, text)

    def test_source_checker_never_infers_availability_from_no_site(self) -> None:
        text = worker_text("source-checker")
        self.assertNotIn("No active site", text)
        self.assertIn("no active site was found is `unknown`; do not infer", text)

    def test_linkedin_query_targets_the_exact_company_slug(self) -> None:
        self.assertIn('`"[NAME]" site:linkedin.com/company/[NAME]`', SOURCE_CHECKS_TEXT)

    def test_social_statuses_are_exact_and_non_exact(self) -> None:
        section = SOURCE_CHECKS_TEXT.split("## Step 1", 1)[1].split("## Step 2", 1)[0]
        self.assertNotIn("unclear", section)
        self.assertIn("Statuses: `available`, `taken (exact)`, `similar (non-exact)`, `unknown`.", section)

    def test_registry_statuses_cover_similar_and_unknown(self) -> None:
        section = SOURCE_CHECKS_TEXT.split("## Step 2", 1)[1].split("## Step 3", 1)[0]
        self.assertIn("**Similar**: no exact match, but close variants exist", section)
        self.assertIn("**Unknown**: the registry did not answer, or answered with an error other than 404", section)

    def test_domain_checks_never_infer_availability(self) -> None:
        section = SOURCE_CHECKS_TEXT.split("## Step 3", 1)[1].split("## Step 4", 1)[0]
        self.assertIn("A search that finds no site proves nothing about registration; record it as Unknown.", section)
        self.assertIn("[NAME].[TLD]", section)
        self.assertIn(
            "Check `.com` first, then `.io` and `.app`. Add `.co`, `.eu`, `.fr` or another TLD"
            " only when `prd.md` or the user names it",
            section,
        )
        domain_rows = [
            line for line in worker_text("source-checker").splitlines() if line.startswith("| `domain` |")
        ]
        self.assertEqual(
            domain_rows,
            ["| `domain` | *Step 3: Domain Check* | `.com`, `.io`, `.app`, plus each extra TLD that `prd.md` or the user names |"],
        )

    def test_trademark_statuses_carry_no_risk(self) -> None:
        section = SOURCE_CHECKS_TEXT.split("## Step 4", 1)[1]
        self.assertIn("Statuses: `clear`, `similar`, `conflicts_found`, `unknown`.", section)
        for status in ("clear", "similar", "conflicts_found", "unknown"):
            with self.subTest(status=status):
                self.assertIn(f"- `{status}`: ", section)
        self.assertIn("live or expired, its class, and its owner", section)
        self.assertNotIn("risk", section.lower())

    def test_output_contract_counts_extra_tlds(self) -> None:
        text = (SKILL_DIR / "references" / "output-contract.md").read_text(encoding="utf-8")
        self.assertIn("There are 16 checks by default", text)
        self.assertIn("each extra TLD that `prd.md` or the user names adds one domain check", text)

    def test_catalog_row_matches_skill_version(self) -> None:
        version = re.search(r"^  version: (\S+)$", SKILL_TEXT, re.MULTILINE).group(1)
        readme = (SKILL_DIR.parents[1] / "README.md").read_text(encoding="utf-8")
        self.assertIn(f"| [**brand-name-checker**](extras/brand-name-checker/) | {version} |", readme)

    def test_skill_checks_the_three_reported_tlds(self) -> None:
        self.assertNotIn("`.app`, `.co`, `.eu`, `.fr`:", SKILL_TEXT)
        self.assertIn("DOMAIN: .com ([status]) | .io ([status]) | .app ([status])", SKILL_TEXT)
        self.assertNotIn("is unchanged", SKILL_TEXT)


class WebAccessAndDomainTests(unittest.TestCase):
    """Any working web access runs the skill (#673); domains are asked of the registry first (#671)."""

    @staticmethod
    def environment_section() -> str:
        return SKILL_TEXT.split("## Environment Check", 1)[1].split("\n## ", 1)[0]

    @staticmethod
    def domain_section() -> str:
        return SOURCE_CHECKS_TEXT.split("## Step 3", 1)[1].split("## Step 4", 1)[0]

    def test_environment_check_accepts_any_web_access(self) -> None:
        section = self.environment_section()
        self.assertNotIn("confirm the WebSearch and WebFetch tools are available", section)
        self.assertIn("WebFetch, an MCP fetch tool, or `curl` in a shell) or a web-search tool", section)
        self.assertIn("Either kind is enough", section)

    def test_blocked_only_when_no_web_access_works(self) -> None:
        section = self.environment_section()
        self.assertIn("If no tool works, stop and return the `BLOCKED` report", section)
        self.assertIn("When only one kind works, run every check and mark each source it cannot reach Unknown", section)
        self.assertIn("**BLOCKED** when no name was given or no web access works", SKILL_TEXT)
        contract = (SKILL_DIR / "references" / "output-contract.md").read_text(encoding="utf-8")
        self.assertNotIn("enable WebSearch and re-run", contract)

    def test_source_checks_prefer_direct_endpoints(self) -> None:
        preamble = SOURCE_CHECKS_TEXT.split("## Step 1", 1)[0]
        self.assertIn("Each source lists its direct endpoint first", preamble)
        self.assertNotIn("Run one WebSearch per platform", SOURCE_CHECKS_TEXT)
        self.assertNotIn("Use WebFetch for each registry", SOURCE_CHECKS_TEXT)
        for endpoint in (
            "https://api.github.com/users/[NAME]",
            "https://discord.com/api/v10/invites/[NAME]",
            "https://packages.debian.org/search?keywords=[NAME]&searchon=names&exact=1",
        ):
            with self.subTest(endpoint=endpoint):
                self.assertIn(endpoint, SOURCE_CHECKS_TEXT)
        worker = worker_text("source-checker")
        self.assertNotIn("If WebFetch or a direct database search is unavailable", worker)
        self.assertIn("Query the\n   direct endpoint first", worker)

    def test_domain_check_asks_the_registry_first(self) -> None:
        section = self.domain_section()
        rdap = section.index("https://data.iana.org/rdap/dns.json")
        whois = section.index("whois -h whois.iana.org [TLD]")
        search = section.index('"[NAME].[TLD]" domain availability')
        self.assertLess(rdap, search)
        self.assertLess(whois, search)
        self.assertIn("Ask the TLD's registry first, by RDAP or WHOIS", SKILL_TEXT)

    def test_registry_not_found_is_available_with_that_evidence(self) -> None:
        section = self.domain_section()
        self.assertIn(
            "A registry not-found reply is Available; cite the RDAP URL or the WHOIS command and its reply as the evidence",
            section,
        )
        self.assertIn("Never count a 404 from a redirector such as `rdap.org`", section)
        self.assertIn("- Available: the TLD registry's RDAP or WHOIS answers that the domain is not found", SKILL_TEXT)

    def test_search_only_domain_result_stays_unknown(self) -> None:
        section = self.domain_section()
        self.assertIn("but the status stays Unknown", section)
        self.assertIn("nothing short of the registry shows it is Available", section)
        self.assertIn("- Unknown: no registry RDAP or WHOIS answer, so the result rests on search", SKILL_TEXT)

    def test_failed_site_fetch_never_makes_a_domain_parked(self) -> None:
        section = self.domain_section()
        self.assertIn("leaves Active or Parked undecided: record the domain as Unknown", section)
        self.assertNotIn("A registered domain with no site is Parked.", section)
        self.assertIn("A registered domain whose page could not be fetched or shows neither a site nor a parking page is Unknown too", SKILL_TEXT)
        self.assertIn("- Parked: registered, and its page shows parking or a sale offer\n", SKILL_TEXT)
        self.assertIn("A registered domain is Parked only when its page shows parking or a sale offer.", section)

    def test_failed_whois_does_not_end_the_domain_check(self) -> None:
        section = self.domain_section()
        self.assertIn("A failed WHOIS never ends the check while RDAP is untried", section)
        self.assertIn("a host that does not resolve", section)


if __name__ == "__main__":
    unittest.main()
