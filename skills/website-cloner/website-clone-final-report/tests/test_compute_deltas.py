"""Stdlib fixtures for the deterministic before/after delta helper.

Run directly from the repository root::

    python3 -m unittest discover -s skills/website-cloner/website-clone-final-report/tests -p 'test_*.py'

The CLI tests deliberately use subprocess only to exercise the executable
boundary.  The calculator itself has no subprocess, network, eval, git, or
report-writing dependency.
"""

from __future__ import annotations

from decimal import Decimal
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "compute_deltas.py"
sys.path.insert(0, str(SCRIPT.parent))

import compute_deltas as deltas  # noqa: E402


def numeric(before, after, before_unit=None, after_unit=None):
    record = {"kind": "numeric", "before": before, "after": after}
    if before_unit is not None:
        record["before_unit"] = before_unit
    if after_unit is not None:
        record["after_unit"] = after_unit
    return record


def full_comparisons(**overrides):
    """A complete, valid comparison map that callers may mutate per case."""
    comparisons = {
        "performance.lcp_estimate_seconds": numeric(4.2, 1.8, "seconds", "seconds"),
        "performance.cls_estimate": numeric(0.18, 0.03),
        "performance.ttfb_estimate_seconds": numeric(0.8, 0.2, "seconds", "seconds"),
        "performance.total_page_weight_kb": numeric(2100, 650, "KB", "KB"),
        "performance.request_count": numeric(87, 32),
        "seo.score": numeric(62, 94),
        "seo.dimension_scores.meta_tags": numeric(60, 95),
        "seo.dimension_scores.heading_structure": numeric(50, 85),
        "seo.dimension_scores.image_alt_text": numeric(30, 100),
        "seo.dimension_scores.structured_data": numeric(20, 100),
        "seo.dimension_scores.crawlability": numeric(60, 90),
        "security.https": {"kind": "boolean", "before": True, "after": True},
        "security.mixed_content": {"kind": "boolean", "before": True, "after": False},
        "security.security_headers": {
            "kind": "array",
            "before": ["a", "b"],
            "after": ["a", "b", "c", "d"],
        },
        "security.exposed_metadata": {
            "kind": "array",
            "before": ["x", "y"],
            "after": [],
        },
    }
    comparisons.update(overrides)
    return {"comparisons": comparisons}


class NumericDeltaTests(unittest.TestCase):
    def test_percent_change_is_rounded_half_up(self):
        result = deltas.calculate_deltas(
            full_comparisons(
                **{"seo.score": numeric(80, 85)}  # (5/80)*100 = 6.25 -> 6
            )
        )
        self.assertEqual(result["comparisons"]["seo.score"]["percent_change"], 6)

    def test_exact_half_percent_rounds_up(self):
        result = deltas.calculate_deltas(
            full_comparisons(
                **{"seo.score": numeric(200, 201)}  # 0.5 -> 1, not banker's 0
            )
        )
        self.assertEqual(result["comparisons"]["seo.score"]["percent_change"], 1)

    def test_negative_delta_is_signed(self):
        result = deltas.calculate_deltas(full_comparisons())
        lcp = result["comparisons"]["performance.lcp_estimate_seconds"]
        self.assertEqual(lcp["absolute_change"], Decimal("-2.4"))
        self.assertEqual(lcp["percent_change"], -57)
        self.assertIsNone(lcp["reason"])

    def test_zero_baseline_keeps_absolute_and_null_percent(self):
        result = deltas.calculate_deltas(
            full_comparisons(**{"seo.score": numeric(0, 72)})
        )
        score = result["comparisons"]["seo.score"]
        self.assertEqual(score["absolute_change"], 72)
        self.assertIsNone(score["percent_change"])
        self.assertEqual(score["reason"], "zero_baseline")
        self.assertIn("seo.score", result["unavailable_comparisons"])

    def test_zero_to_zero_reports_zero_baseline(self):
        result = deltas.calculate_deltas(
            full_comparisons(**{"seo.score": numeric(0, 0)})
        )
        score = result["comparisons"]["seo.score"]
        self.assertEqual(score["absolute_change"], 0)
        self.assertIsNone(score["percent_change"])
        self.assertEqual(score["reason"], "zero_baseline")

    def test_matching_units_required_when_supplied(self):
        result = deltas.calculate_deltas(
            full_comparisons(
                **{
                    "performance.lcp_estimate_seconds": numeric(
                        4.2, 1.8, "seconds", "ms"
                    )
                }
            )
        )
        lcp = result["comparisons"]["performance.lcp_estimate_seconds"]
        self.assertEqual(lcp["reason"], "unit_mismatch")
        self.assertIsNone(lcp["percent_change"])

    def test_one_sided_unit_is_a_mismatch_but_both_absent_is_fine(self):
        result = deltas.calculate_deltas(
            full_comparisons(
                **{"performance.cls_estimate": numeric(0.18, 0.03, "unitless")}
            )
        )
        cls = result["comparisons"]["performance.cls_estimate"]
        self.assertEqual(cls["reason"], "unit_mismatch")
        ok = deltas.calculate_deltas(full_comparisons())
        self.assertEqual(
            ok["comparisons"]["performance.cls_estimate"]["percent_change"], -83
        )

    def test_wrong_expected_unit_is_rejected(self):
        result = deltas.calculate_deltas(
            full_comparisons(
                **{"seo.score": numeric(60, 90, "KB", "KB")}
            )
        )
        self.assertEqual(result["comparisons"]["seo.score"]["reason"], "unit_mismatch")

    def test_null_and_missing_sources_are_partial_not_invented(self):
        result = deltas.calculate_deltas(
            full_comparisons(
                **{
                    "seo.score": {"kind": "numeric", "before": None, "after": 94},
                    "performance.request_count": {"kind": "numeric", "after": 32},
                }
            )
        )
        self.assertEqual(result["status"], "PARTIAL")
        self.assertEqual(result["comparisons"]["seo.score"]["reason"], "null_before")
        self.assertEqual(
            result["comparisons"]["performance.request_count"]["reason"],
            "missing_before",
        )
        self.assertIn("seo.score", result["unavailable_comparisons"])

    def test_fractional_and_nonfinite_inputs_are_rejected(self):
        for bad in ("4.2", [4.2], True):
            with self.subTest(bad=bad):
                with self.assertRaises(deltas.InputError):
                    deltas.calculate_deltas(
                        full_comparisons(**{"seo.score": numeric(bad, 90)})
                    )

    def test_missing_comparison_fields_are_reported(self):
        payload = full_comparisons()
        del payload["comparisons"]["seo.score"]
        result = deltas.calculate_deltas(payload)
        self.assertEqual(result["status"], "PARTIAL")
        self.assertEqual(result["missing_comparisons"], ["seo.score"])
        self.assertIn("seo.score", result["unavailable_comparisons"])

    def test_complete_input_is_pass(self):
        result = deltas.calculate_deltas(full_comparisons())
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["missing_comparisons"], [])
        self.assertEqual(result["unavailable_comparisons"], [])


class TypedDeltaTests(unittest.TestCase):
    def test_boolean_compares_directly(self):
        result = deltas.calculate_deltas(full_comparisons())
        https = result["comparisons"]["security.https"]
        mixed = result["comparisons"]["security.mixed_content"]
        self.assertFalse(https["changed"])
        self.assertTrue(mixed["changed"])

    def test_boolean_requires_bool_values(self):
        payload = full_comparisons(
            **{"security.https": {"kind": "boolean", "before": "yes", "after": True}}
        )
        with self.assertRaises(deltas.InputError):
            deltas.calculate_deltas(payload)

    def test_array_compares_by_counts_not_membership(self):
        result = deltas.calculate_deltas(full_comparisons())
        headers = result["comparisons"]["security.security_headers"]
        self.assertEqual(headers["before_count"], 2)
        self.assertEqual(headers["after_count"], 4)
        self.assertTrue(headers["changed"])

    def test_array_same_count_different_members_is_unchanged(self):
        result = deltas.calculate_deltas(
            full_comparisons(
                **{
                    "security.security_headers": {
                        "kind": "array",
                        "before": ["a", "b"],
                        "after": ["x", "y"],
                    }
                }
            )
        )
        self.assertFalse(result["comparisons"]["security.security_headers"]["changed"])

    def test_array_requires_list_values(self):
        payload = full_comparisons(
            **{
                "security.security_headers": {
                    "kind": "array",
                    "before": 2,
                    "after": ["a"],
                }
            }
        )
        with self.assertRaises(deltas.InputError):
            deltas.calculate_deltas(payload)


class PayloadValidationTests(unittest.TestCase):
    def assertInvalid(self, payload, contains=None):
        with self.assertRaises(deltas.InputError) as raised:
            deltas.calculate_deltas(payload)
        if contains:
            self.assertIn(contains, str(raised.exception))

    def test_top_level_shape_is_strict(self):
        self.assertInvalid([], "must be a JSON object")
        self.assertInvalid({}, "missing required top-level key: comparisons")
        self.assertInvalid(
            {"comparisons": {}, "extra": 1}, "unexpected top-level key(s): extra"
        )
        self.assertInvalid({"comparisons": []}, "comparisons must be a JSON object")

    def test_unknown_field_is_rejected(self):
        payload = full_comparisons()
        payload["comparisons"]["seo.mystery"] = numeric(1, 2)
        self.assertInvalid(payload, "unknown comparison field")

    def test_wrong_kind_is_rejected(self):
        payload = full_comparisons()
        payload["comparisons"]["seo.score"] = {
            "kind": "boolean",
            "before": False,
            "after": True,
        }
        self.assertInvalid(payload, "kind must be 'numeric'")

    def test_unexpected_record_keys_are_rejected(self):
        payload = full_comparisons()
        payload["comparisons"]["seo.score"]["note"] = "looks better"
        self.assertInvalid(payload, "unexpected key(s): note")
        payload = full_comparisons()
        payload["comparisons"]["security.https"]["before_unit"] = "bool"
        self.assertInvalid(payload, "unexpected key(s): before_unit")

    def test_nonfinite_value_is_rejected(self):
        self.assertInvalid(
            full_comparisons(**{"seo.score": numeric(float("nan"), 90)})
        )


class CliContractTests(unittest.TestCase):
    def run_cli(self, raw: str, *args: str):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            input=raw,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_stdin_success_is_canonical_json(self):
        result = self.run_cli(json.dumps(full_comparisons()), "--input", "-")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        parsed = json.loads(result.stdout)
        self.assertEqual(parsed["status"], "PASS")
        self.assertEqual(result.stdout, result.stdout.rstrip() + "\n")

    def test_absolute_file_success(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "comparisons.json"
            path.write_text(json.dumps(full_comparisons()), encoding="utf-8")
            result = self.run_cli("", "--input", str(path))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["schema_version"], 1)

    def test_relative_file_path_is_rejected(self):
        result = self.run_cli("{}", "--input", "comparisons.json")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("absolute", result.stderr)

    def test_malformed_json_has_stable_error_and_no_partial_result(self):
        result = self.run_cli("{", "--input", "-")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertTrue(
            result.stderr.startswith("error[delta-input]: input is not valid JSON:")
        )

    def test_empty_stdin_is_rejected_without_partial_result(self):
        result = self.run_cli("", "--input", "-")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("input is empty", result.stderr)


if __name__ == "__main__":
    unittest.main()
