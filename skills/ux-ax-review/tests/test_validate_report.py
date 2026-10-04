"""Regression tests for the structural report contract (stdlib only)."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_report.py"
ASPECTS = (
    "clarity", "brand", "responsive", "accessibility", "performance", "conversion",
    "robots-sitemap", "structured-data", "markdown-pages", "llms-txt",
    "crawler-access", "ai-actions",
)
HEADINGS = (
    "Executive Summary", "Scope and Evidence", "Human UX", "AI/Search AX",
    "Prioritized Findings", "Improvement Plan", "Limitations and Next Step",
)


def report_fixture():
    return {
        "schema_version": 1,
        "scope": {
            "target": "saved HTML", "mode": "evidence-only", "audience": "unknown",
            "primary_goal": "unknown", "sampled_surfaces": ["pricing"], "limitations": [],
        },
        "evidence": [],
        "coverage": [
            {"aspect": aspect, "status": "not-tested", "rationale": "No adequate evidence",
             "evidence_ids": [], "finding_ids": []} for aspect in ASPECTS
        ],
        "findings": [],
        "plan": [],
    }


def observed_fixture():
    report = report_fixture()
    report["evidence"] = [{"id": "E1", "source": "pricing.html:12", "method": "saved HTML",
                           "observation": "Two identical purchase labels", "limitations": ""}]
    report["findings"] = [{"id": "F1", "aspect": "clarity", "kind": "observed",
                           "severity": "medium", "confidence": "medium", "title": "Ambiguous labels",
                           "evidence_ids": ["E1"], "recommendation": "Use specific labels"}]
    report["coverage"][0].update(status="issues", evidence_ids=["E1"], finding_ids=["F1"])
    report["plan"] = [{"id": "T1", "phase": 1, "priority": "P2", "finding_ids": ["F1"],
                       "title": "Clarify labels", "owner": "design", "effort": "S",
                       "dependencies": [], "expected_impact": "Reduce ambiguity",
                       "acceptance_checks": ["Each action names its option"]}]
    return report


def validate(report, markdown=None):
    if not SCRIPT.exists():
        return ["validator not implemented"]
    spec = importlib.util.spec_from_file_location("validate_report", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_report(report, markdown)


class ReportTests(unittest.TestCase):
    def assert_invalid(self, report, field, markdown=None):
        errors = validate(report, markdown)
        self.assertTrue(errors, f"Expected an error for {field}")
        self.assertTrue(any(field in error for error in errors), errors)
        self.assertTrue(all(isinstance(error, str) for error in errors), errors)

    def test_valid_empty_report(self):
        self.assertEqual(validate(report_fixture()), [])

    def test_root_and_schema_types(self):
        for value in (None, [], "report", 1, True):
            with self.subTest(value=value):
                self.assert_invalid(value, "report")
        for value in (None, True, 1.0, "1", 2):
            report = report_fixture()
            report["schema_version"] = value
            with self.subTest(version=value):
                self.assert_invalid(report, "schema_version")
        report = report_fixture()
        del report["schema_version"]
        self.assert_invalid(report, "schema_version")

    def test_collection_shapes(self):
        for key in ("evidence", "coverage", "findings", "plan"):
            for value in (None, "", {}, float("nan"), True):
                report = report_fixture()
                report[key] = value
                with self.subTest(key=key, value=value):
                    self.assert_invalid(report, key)
            report = report_fixture()
            del report[key]
            self.assert_invalid(report, key)
            for value in (None, "row", [], 2, True):
                report = report_fixture()
                report[key] = [value]
                with self.subTest(key=key, row=value):
                    self.assert_invalid(report, key + "[0]")

    def test_scope_shape_and_nonempty_fields(self):
        for value in (None, "scope", [], False):
            report = report_fixture()
            report["scope"] = value
            self.assert_invalid(report, "scope")
        required = ("target", "mode", "audience", "primary_goal", "sampled_surfaces", "limitations")
        for field in required:
            report = report_fixture()
            del report["scope"][field]
            self.assert_invalid(report, "scope." + field)
        for field in ("target", "mode", "audience", "primary_goal"):
            for value in (None, "", "  ", [], 1):
                report = report_fixture()
                report["scope"][field] = value
                self.assert_invalid(report, "scope." + field)
        for field in ("sampled_surfaces", "limitations"):
            for value in (None, "text", {}, [""], [False]):
                report = report_fixture()
                report["scope"][field] = value
                self.assert_invalid(report, "scope." + field)
        report = report_fixture()
        report["scope"]["sampled_surfaces"] = []
        self.assertEqual(validate(report), [])

    def test_record_fields_required_and_typed(self):
        fields = {
            "evidence": ("id", "source", "method", "observation", "limitations"),
            "coverage": ("aspect", "status", "rationale", "evidence_ids", "finding_ids"),
            "findings": ("id", "aspect", "kind", "severity", "confidence", "title", "evidence_ids", "recommendation"),
            "plan": ("id", "phase", "priority", "finding_ids", "title", "owner", "effort", "dependencies", "expected_impact", "acceptance_checks"),
        }
        array_fields = {"evidence_ids", "finding_ids", "dependencies", "acceptance_checks"}
        for collection, keys in fields.items():
            for key in keys:
                report = observed_fixture()
                del report[collection][0][key]
                self.assert_invalid(report, f"{collection}[0].{key}")
                if key == "phase":
                    continue
                bad_values = (None, {}, "text", [False], [""]) if key in array_fields else (None, [], " ")
                if key == "limitations":
                    bad_values = (None, [])
                for value in bad_values:
                    report = observed_fixture()
                    report[collection][0][key] = value
                    with self.subTest(collection=collection, field=key, value=value):
                        self.assert_invalid(report, f"{collection}[0].{key}")
        self.assertEqual(validate(observed_fixture()), [])

    def test_enums_and_phase(self):
        domains = {
            "scope.mode": ("live-web", "repo", "evidence-only", "native-app"),
            "coverage.status": ("pass", "issues", "not-tested", "not-applicable"),
            "findings.kind": ("observed", "hypothesis"),
            "findings.severity": ("critical", "high", "medium", "low"),
            "findings.confidence": ("high", "medium", "low"),
            "plan.priority": ("P0", "P1", "P2", "P3"),
            "plan.effort": ("XS", "S", "M", "L"),
        }
        for key, choices in domains.items():
            collection, field = key.split(".")
            for value in ("invalid", [], {}, True):
                report = observed_fixture()
                obj = report[collection] if collection == "scope" else report[collection][0]
                obj[field] = value
                self.assert_invalid(report, "scope.mode" if collection == "scope" else f"{collection}[0].{field}")
            for value in choices:
                report = observed_fixture()
                obj = report[collection] if collection == "scope" else report[collection][0]
                obj[field] = value
                if collection == "findings" and field == "kind" and value == "hypothesis":
                    report["coverage"][0]["status"] = "not-tested"
                self.assertEqual(validate(report), [])
        for value in (-1, 4, True, 1.0, "1", None, [], float("nan")):
            report = observed_fixture()
            report["plan"][0]["phase"] = value
            self.assert_invalid(report, "plan[0].phase")
        for value in range(4):
            report = observed_fixture()
            report["plan"][0]["phase"] = value
            self.assertEqual(validate(report), [])

    def test_exact_aspect_coverage(self):
        for mutation in ("missing", "extra", "duplicate", "unknown", "malformed"):
            report = report_fixture()
            if mutation == "missing":
                report["coverage"].pop()
            elif mutation == "extra":
                report["coverage"].append(copy.deepcopy(report["coverage"][0]))
            elif mutation == "duplicate":
                report["coverage"][1]["aspect"] = "clarity"
            elif mutation == "unknown":
                report["coverage"][0]["aspect"] = "custom"
            else:
                report["coverage"][0]["aspect"] = []
            self.assert_invalid(report, "coverage")
        report = observed_fixture()
        for value in ("custom", [], {}):
            report["findings"][0]["aspect"] = value
            self.assert_invalid(report, "findings[0].aspect")
        report = report_fixture()
        report["coverage"].reverse()
        self.assertEqual(validate(report), [])

    def test_duplicate_ids(self):
        for collection in ("evidence", "findings", "plan"):
            report = observed_fixture()
            report[collection].append(copy.deepcopy(report[collection][0]))
            self.assert_invalid(report, f"{collection}[1].id")
            for value in ([], {}, None, " "):
                report = observed_fixture()
                report[collection][0]["id"] = value
                self.assert_invalid(report, f"{collection}[0].id")

    def test_references_must_exist(self):
        for collection, field in (("coverage", "evidence_ids"), ("coverage", "finding_ids"),
                                  ("findings", "evidence_ids"), ("plan", "finding_ids"),
                                  ("plan", "dependencies")):
            report = observed_fixture()
            report[collection][0][field] = ["missing"]
            self.assert_invalid(report, f"{collection}[0].{field}[0]")
            for value in ([[]], [{}], None, "E1"):
                report = observed_fixture()
                report[collection][0][field] = value
                self.assert_invalid(report, f"{collection}[0].{field}")

    def test_observed_requires_evidence(self):
        report = observed_fixture()
        report["findings"][0]["evidence_ids"] = []
        self.assert_invalid(report, "findings[0].evidence_ids")
        report["findings"][0]["kind"] = "hypothesis"
        report["coverage"][0]["status"] = "not-tested"
        self.assertEqual(validate(report), [])

    def test_conclusive_coverage_requires_evidence(self):
        for status in ("pass", "issues"):
            report = observed_fixture()
            report["coverage"][0].update(status=status, evidence_ids=[])
            self.assert_invalid(report, "coverage[0].evidence_ids")
        report = observed_fixture()
        report["coverage"][0]["status"] = "pass"
        self.assertEqual(validate(report), [])

    def test_coverage_finding_aspect_matches(self):
        report = observed_fixture()
        report["findings"][0]["aspect"] = "brand"
        self.assert_invalid(report, "coverage[0].finding_ids[0]")
        report = observed_fixture()
        report["coverage"][1]["finding_ids"] = ["F1"]
        self.assert_invalid(report, "coverage[1].finding_ids[0]")

    def test_issues_require_same_aspect_observed_finding(self):
        report = observed_fixture()
        report["coverage"][0]["finding_ids"] = []
        self.assert_invalid(report, "coverage[0].finding_ids")
        report = observed_fixture()
        report["findings"][0]["kind"] = "hypothesis"
        self.assert_invalid(report, "coverage[0].finding_ids")
        report = observed_fixture()
        report["findings"][0]["aspect"] = "brand"
        self.assert_invalid(report, "coverage[0].finding_ids")

    def test_related_aspects_allow_one_cross_audience_finding(self):
        report = observed_fixture()
        report["findings"][0]["related_aspects"] = ["ai-actions"]
        report["coverage"][-1].update(status="issues", evidence_ids=["E1"], finding_ids=["F1"])
        self.assertEqual(validate(report), [])
        for value in ("ai-actions", ["bogus"], [{}]):
            report["findings"][0]["related_aspects"] = value
            self.assert_invalid(report, "findings[0].related_aspects")

    def test_every_finding_is_planned(self):
        report = observed_fixture()
        report["plan"] = []
        self.assert_invalid(report, "findings[0].id")
        report["findings"][0]["kind"] = "hypothesis"
        report["coverage"][0]["status"] = "not-tested"
        self.assert_invalid(report, "findings[0].id")

    def test_tasks_require_acceptance_checks(self):
        report = observed_fixture()
        report["plan"][0]["acceptance_checks"] = []
        self.assert_invalid(report, "plan[0].acceptance_checks")

    def test_dependencies_are_ordered_and_acyclic(self):
        report = observed_fixture()
        other = copy.deepcopy(report["plan"][0])
        other["id"] = "T2"
        other["finding_ids"] = []
        other["dependencies"] = ["T1"]
        report["plan"].append(other)
        self.assertEqual(validate(report), [])
        report["plan"].reverse()
        self.assert_invalid(report, "dependencies")
        report["plan"].reverse()
        report["plan"][0]["dependencies"] = ["T2"]
        self.assert_invalid(report, "dependencies")
        report = observed_fixture()
        report["plan"][0]["dependencies"] = ["T1"]
        self.assert_invalid(report, "dependencies")

    def test_markdown_requires_all_headings_outside_fences(self):
        markdown = "\n".join("## " + heading for heading in HEADINGS)
        self.assertEqual(validate(observed_fixture(), markdown), [])
        self.assert_invalid(observed_fixture(), "markdown", markdown.replace("## Human UX", "# Human UX"))
        self.assert_invalid(observed_fixture(), "markdown", "```markdown\n" + markdown + "\n```")
        self.assert_invalid(observed_fixture(), "markdown", 7)

    def test_markdown_closing_fence_matches_character_and_length(self):
        headings = "\n".join("## " + heading for heading in HEADINGS)
        missing = [f"markdown: missing H2 heading {heading!r}" for heading in HEADINGS]
        for marker in ("`", "~"):
            for closer in (marker * 3, ("~" if marker == "`" else "`") * 4):
                with self.subTest(marker=marker, closer=closer):
                    markdown = marker * 4 + "markdown\n" + closer + "\n" + headings + "\n" + marker * 4
                    self.assertEqual(validate(observed_fixture(), markdown), missing)
            for length in (4, 5):
                with self.subTest(marker=marker, valid_length=length):
                    markdown = marker * 4 + "markdown\ncode\n" + marker * length + " \t\n" + headings
                    self.assertEqual(validate(observed_fixture(), markdown), [])

    def test_markdown_closing_fence_forbids_trailing_text(self):
        headings = "\n".join("## " + heading for heading in HEADINGS)
        missing = [f"markdown: missing H2 heading {heading!r}" for heading in HEADINGS]
        for marker in ("`", "~"):
            for suffix in ("not-a-close", " not-a-close", "\tnot-a-close"):
                with self.subTest(marker=marker, suffix=suffix):
                    markdown = marker * 3 + "markdown\n" + marker * 3 + suffix + "\n" + headings + "\n" + marker * 3
                    self.assertEqual(validate(observed_fixture(), markdown), missing)

    def test_markdown_fences_allow_at_most_three_leading_spaces(self):
        headings = "\n".join("## " + heading for heading in HEADINGS)
        missing = [f"markdown: missing H2 heading {heading!r}" for heading in HEADINGS]
        for marker in ("`", "~"):
            for spaces in range(4):
                indent = " " * spaces
                with self.subTest(marker=marker, valid_indent=spaces):
                    opening = indent + marker * 3 + "markdown\n"
                    closing = indent + marker * 3
                    self.assertEqual(validate(observed_fixture(), opening + headings + "\n" + closing), missing)
                    self.assertEqual(validate(observed_fixture(), opening + "code\n" + closing + " \t\n" + headings), [])
            for indent in ("    ", "\t", " \t"):
                with self.subTest(marker=marker, code_indent=indent):
                    markdown = indent + marker * 3 + "markdown\n\n" + headings
                    self.assertEqual(validate(observed_fixture(), markdown), [])
                    markdown = marker * 3 + "markdown\n" + indent + marker * 3 + "\n" + headings + "\n" + marker * 3
                    self.assertEqual(validate(observed_fixture(), markdown), missing)
        self.assertEqual(validate(observed_fixture(), "\n".join("    ## " + heading for heading in HEADINGS)), missing)

    def test_cli_success_and_field_errors(self):
        with tempfile.TemporaryDirectory(dir=str(Path(__file__).resolve().parents[1] / "tests")) as temp:
            path = Path(temp) / "report.json"
            path.write_text(json.dumps(observed_fixture()), encoding="utf-8")
            result = subprocess.run([sys.executable, "-B", str(SCRIPT), str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("PASS", result.stdout)
            path.write_text('{}', encoding="utf-8")
            result = subprocess.run([sys.executable, "-B", str(SCRIPT), str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("schema_version", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_cli_parse_read_and_markdown_errors(self):
        with tempfile.TemporaryDirectory(dir=str(Path(__file__).resolve().parents[1] / "tests")) as temp:
            path = Path(temp) / "report.json"
            for content in ("{", "null", "[]", "\x00", "NaN", '{"a": Infinity}'):
                path.write_text(content, encoding="utf-8")
                result = subprocess.run([sys.executable, "-B", str(SCRIPT), str(path)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 1)
                self.assertTrue(result.stderr.strip())
                self.assertNotIn("Traceback", result.stderr)
            missing = Path(temp) / "missing.json"
            result = subprocess.run([sys.executable, "-B", str(SCRIPT), str(missing)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertNotIn("Traceback", result.stderr)
            path.write_text(json.dumps(observed_fixture()), encoding="utf-8")
            md = Path(temp) / "review.md"
            for content, code in [("not a report", 1), ("\n".join("## " + h for h in HEADINGS), 0)]:
                md.write_text(content, encoding="utf-8")
                result = subprocess.run([sys.executable, "-B", str(SCRIPT), str(path), "--markdown", str(md)], capture_output=True, text=True)
                self.assertEqual(result.returncode, code, result.stderr)
            result = subprocess.run([sys.executable, "-B", str(SCRIPT), str(path), "--markdown", str(missing)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertNotIn("Traceback", result.stderr)

    def test_programmatic_nonfinite_values_are_rejected(self):
        for number in (float("nan"), float("inf"), -float("inf")):
            report = report_fixture()
            report["extra"] = {"nested": [number]}
            self.assert_invalid(report, "extra.nested[0]")


if __name__ == "__main__":
    unittest.main()
