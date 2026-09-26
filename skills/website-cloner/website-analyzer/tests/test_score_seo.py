"""Stdlib fixtures for the deterministic SEO score helper."""

from __future__ import annotations

from decimal import Decimal
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "score_seo.py"
sys.path.insert(0, str(SCRIPT.parent))

import score_seo as seo  # noqa: E402


KEYS = tuple(seo.DIMENSION_WEIGHTS)


def dimensions(value=50):
    return {key: value for key in KEYS}


class ScoreTests(unittest.TestCase):
    def test_all_known_uses_exact_weights(self):
        result = seo.calculate_score(
            {
                "meta_tags": 100,
                "heading_structure": 80,
                "image_alt_text": 60,
                "structured_data": 40,
                "crawlability": 20,
            }
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["availability"], "available")
        self.assertEqual(result["score"], 55)
        self.assertEqual(result["unavailable_dimensions"], [])
        self.assertEqual(result["dimension_scores"]["meta_tags"], 100)

    def test_partial_null_renormalizes_known_weights(self):
        result = seo.calculate_score(
            {
                "meta_tags": 100,
                "heading_structure": None,
                "image_alt_text": 0,
                "structured_data": None,
                "crawlability": 50,
            }
        )
        # (0.20*100 + 0.15*0 + 0.30*50) / (0.20+0.15+0.30) = 53.846...
        self.assertEqual(result["status"], "PARTIAL")
        self.assertEqual(result["availability"], "partial")
        self.assertEqual(result["reason"], "some_dimensions_unavailable")
        self.assertEqual(result["score"], 54)
        self.assertEqual(
            result["unavailable_dimensions"], ["heading_structure", "structured_data"]
        )

    def test_each_single_known_dimension_is_renormalized(self):
        for key in KEYS:
            with self.subTest(key=key):
                payload = {name: None for name in KEYS}
                payload[key] = 73
                result = seo.calculate_score(payload)
                self.assertEqual(result["status"], "PARTIAL")
                self.assertEqual(result["score"], 73)
                self.assertEqual(result["unavailable_dimensions"], [name for name in KEYS if name != key])

    def test_all_null_is_unavailable_and_has_no_numeric_score(self):
        result = seo.calculate_score({key: None for key in KEYS})
        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(result["status"], "PARTIAL")
        self.assertEqual(result["availability"], "unavailable")
        self.assertEqual(result["reason"], "all_dimensions_unavailable")
        self.assertIsNone(result["score"])
        self.assertEqual(result["unavailable_dimensions"], list(KEYS))

    def test_all_zero_is_zero_but_available(self):
        result = seo.calculate_score(dimensions(0))
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["availability"], "available")
        self.assertEqual(result["score"], 0)

    def test_bounds_are_inclusive(self):
        result = seo.calculate_score(
            {
                "meta_tags": 0,
                "heading_structure": 100,
                "image_alt_text": 0,
                "structured_data": 100,
                "crawlability": 0,
            }
        )
        self.assertEqual(result["score"], 35)

    def test_round_half_up_not_bankers_rounding(self):
        payload = dimensions(50)
        payload["heading_structure"] = 60
        # 50 + (0.15 * 10) = 51.5; ROUND_HALF_UP must produce 52.
        result = seo.calculate_score(payload)
        self.assertEqual(result["score"], 52)

    def test_decimal_input_is_rejected_even_when_integral(self):
        payload = dimensions(50)
        payload["meta_tags"] = Decimal("50.0")
        with self.assertRaises(seo.InputError):
            seo.calculate_score(payload)


class ValidationTests(unittest.TestCase):
    def assertInvalid(self, payload, contains=None):
        with self.assertRaises(seo.InputError) as raised:
            seo.calculate_score(payload)
        if contains:
            self.assertIn(contains, str(raised.exception))

    def test_missing_dimension_is_rejected(self):
        payload = dimensions()
        del payload["crawlability"]
        self.assertInvalid(payload, "missing required dimension key")

    def test_unknown_dimension_is_rejected(self):
        payload = dimensions()
        payload["other"] = 50
        self.assertInvalid(payload, "unexpected dimension key")

    def test_non_string_dimension_key_is_rejected(self):
        payload = dimensions()
        payload[1] = 50
        self.assertInvalid(payload, "dimension keys must be strings")

    def test_non_object_is_rejected(self):
        self.assertInvalid([], "JSON object")
        self.assertInvalid(None, "JSON object")

    def test_string_nested_and_list_values_are_rejected(self):
        for value in ("50", {"score": 50}, [50]):
            with self.subTest(value=value):
                payload = dimensions()
                payload["meta_tags"] = value
                self.assertInvalid(payload, "meta_tags")

    def test_boolean_is_not_a_number(self):
        payload = dimensions()
        payload["meta_tags"] = True
        self.assertInvalid(payload, "boolean")

    def test_out_of_range_values_are_rejected(self):
        for value in (-1, 101):
            with self.subTest(value=value):
                payload = dimensions()
                payload["meta_tags"] = value
                self.assertInvalid(payload, "between 0 and 100")

    def test_fractional_values_are_rejected(self):
        for value in (50.5, Decimal("1.25"), Decimal("-0.1"), Decimal("100.1")):
            with self.subTest(value=value):
                payload = dimensions()
                payload["meta_tags"] = value
                self.assertInvalid(payload, "integer")

    def test_nonfinite_values_are_rejected(self):
        for value in (float("nan"), float("inf"), Decimal("NaN"), Decimal("Infinity")):
            with self.subTest(value=value):
                payload = dimensions()
                payload["meta_tags"] = value
                self.assertInvalid(payload, "finite")

    def test_decimal_ordinary_integer_is_accepted(self):
        result = seo.calculate_score(
            {key: Decimal(str(index)) for index, key in enumerate(KEYS)}
        )
        self.assertEqual(result["score"], 2)

    def test_result_is_reproducible_for_input_order(self):
        first = {
            "meta_tags": 17,
            "heading_structure": 29,
            "image_alt_text": None,
            "structured_data": 73,
            "crawlability": 41,
        }
        second = dict(reversed(list(first.items())))
        self.assertEqual(seo.calculate_score(first), seo.calculate_score(second))


class CliTests(unittest.TestCase):
    def run_cli(self, raw: str, *args: str):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            input=raw,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_stdin_success_is_canonical_json(self):
        result = self.run_cli(json.dumps(dimensions(50)), "--input", "-")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(json.loads(result.stdout)["score"], 50)
        self.assertEqual(result.stdout, result.stdout.rstrip() + "\n")

    def test_file_success_accepts_absolute_path(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dimensions.json"
            path.write_text(json.dumps(dimensions(80)), encoding="utf-8")
            result = self.run_cli("", "--input", str(path))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["score"], 80)

    def test_cli_json_is_reproducible_for_input_order(self):
        first = {
            "meta_tags": 17,
            "heading_structure": 29,
            "image_alt_text": None,
            "structured_data": 73,
            "crawlability": 41,
        }
        second = dict(reversed(list(first.items())))
        first_result = self.run_cli(json.dumps(first), "--input", "-")
        second_result = self.run_cli(json.dumps(second), "--input", "-")
        self.assertEqual(first_result.returncode, 0, first_result.stderr)
        self.assertEqual(second_result.returncode, 0, second_result.stderr)
        self.assertEqual(first_result.stdout, second_result.stdout)

    def test_relative_file_path_is_rejected(self):
        result = self.run_cli(json.dumps(dimensions()), "--input", "dimensions.json")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("absolute", result.stderr)

    def test_missing_input_is_rejected_without_result(self):
        payload = dict(dimensions())
        del payload["meta_tags"]
        result = self.run_cli(json.dumps(payload), "--input", "-")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr.startswith("error[seo-input]: missing required dimension key"))

    def test_extra_input_is_rejected_without_result(self):
        payload = dimensions()
        payload["extra"] = 20
        result = self.run_cli(json.dumps(payload), "--input", "-")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("unexpected dimension key", result.stderr)

    def test_malformed_json_is_stable_and_has_no_partial_result(self):
        result = self.run_cli("{", "--input", "-")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr.startswith("error[seo-input]: input is not valid JSON:"))

    def test_nonfinite_json_is_rejected(self):
        payload = json.dumps(dimensions()).replace("50", "NaN", 1)
        result = self.run_cli(payload, "--input", "-")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("non-finite JSON number", result.stderr)

    def test_duplicate_json_key_is_rejected(self):
        result = self.run_cli(
            '{"meta_tags": 50, "meta_tags": 51, "heading_structure": 50, '
            '"image_alt_text": 50, "structured_data": 50, "crawlability": 50}',
            "--input",
            "-",
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("duplicate JSON object key", result.stderr)

    def test_empty_stdin_is_rejected(self):
        result = self.run_cli("", "--input", "-")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("input is empty", result.stderr)


if __name__ == "__main__":
    unittest.main()
