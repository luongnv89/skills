"""Stdlib fixtures for the deterministic Virality Score helper.

Run directly from the repository root::

    python3 -m unittest discover -s skills/viral-product-evaluator/tests -p 'test_*.py'

The CLI tests deliberately use subprocess only to exercise the executable
boundary.  The calculator itself has no subprocess, network, eval, git, or
report-writing dependency.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "virality_score.py"
sys.path.insert(0, str(SCRIPT.parent))

import virality_score as virality  # noqa: E402


PRINCIPLE_KEYS = [str(number) for number in range(1, 33)]


def verdicts(default="PASS", **overrides):
    """A complete 32-verdict map that callers may adjust per case."""
    result = {key: default for key in PRINCIPLE_KEYS}
    result.update({str(key): value for key, value in overrides.items()})
    return {"verdicts": result}


def with_verdict_counts(pass_count, partial_count, fail_count):
    assert pass_count + partial_count + fail_count == 32
    mapping = {}
    keys = iter(PRINCIPLE_KEYS)
    for _ in range(pass_count):
        mapping[next(keys)] = "PASS"
    for _ in range(partial_count):
        mapping[next(keys)] = "PARTIAL"
    for _ in range(fail_count):
        mapping[next(keys)] = "FAIL"
    return {"verdicts": mapping}


class ScoreTests(unittest.TestCase):
    def test_all_pass_is_100_viral_ready(self):
        result = virality.calculate_score(verdicts())
        self.assertEqual(result["counts"], {"pass": 32, "partial": 0, "fail": 0})
        self.assertEqual(result["points"], 32.0)
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["tier"], "Viral-ready")

    def test_all_fail_is_zero_not_viral(self):
        result = virality.calculate_score(verdicts("FAIL"))
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["tier"], "Not viral yet")

    def test_partial_counts_half_and_sums_correctly(self):
        result = virality.calculate_score(with_verdict_counts(20, 4, 8))
        self.assertEqual(result["counts"], {"pass": 20, "partial": 4, "fail": 8})
        self.assertEqual(result["points"], 22.0)
        # 22/32 * 100 = 68.75 -> 69
        self.assertEqual(result["score"], 69)
        self.assertEqual(result["tier"], "Promising")

    def test_half_point_rounds_half_up(self):
        # 18*1 + 4*0.5 = 20 points -> 20/32*100 = 62.5 exactly -> 63
        result = virality.calculate_score(with_verdict_counts(18, 4, 10))
        self.assertEqual(result["points"], 20.0)
        self.assertEqual(result["score"], 63)

    def test_tier_boundaries(self):
        cases = [
            (28, 0, 4, 88, "Viral-ready"),     # 28 -> 87.5 -> 88
            (27, 1, 4, 86, "Viral-ready"),     # 27.5 -> 85.9375 -> 86
            (27, 0, 5, 84, "Promising"),       # 27 -> 84.375 -> 84
            (21, 0, 11, 66, "Promising"),      # 21 -> 65.625 -> 66
            (13, 0, 19, 41, "Needs work"),     # 13 -> 40.625 -> 41
            (12, 1, 19, 39, "Not viral yet"),  # 12.5 -> 39.0625 -> 39
        ]
        for p, part, f, expected_score, expected_tier in cases:
            with self.subTest(counts=(p, part, f)):
                result = virality.calculate_score(with_verdict_counts(p, part, f))
                self.assertEqual(result["score"], expected_score)
                self.assertEqual(result["tier"], expected_tier)

    def test_result_is_order_independent(self):
        first = virality.calculate_score(with_verdict_counts(20, 4, 8))
        shuffled = {
            "verdicts": dict(
                reversed(list(with_verdict_counts(20, 4, 8)["verdicts"].items()))
            )
        }
        self.assertEqual(first, virality.calculate_score(shuffled))


class VerdictValidationTests(unittest.TestCase):
    def assertInvalid(self, payload, contains=None):
        with self.assertRaises(virality.InputError) as raised:
            virality.calculate_score(payload)
        if contains:
            self.assertIn(contains, str(raised.exception))

    def test_top_level_shape_is_strict(self):
        self.assertInvalid([], "must be a JSON object")
        self.assertInvalid({}, "missing required top-level key: verdicts")
        self.assertInvalid(
            {**verdicts(), "extra": 1}, "unexpected top-level key(s): extra"
        )
        self.assertInvalid({"verdicts": []}, "verdicts must be a JSON object")

    def test_missing_principle_is_rejected(self):
        payload = verdicts()
        del payload["verdicts"]["7"]
        self.assertInvalid(payload, "missing principle verdict(s): 7")

    def test_unknown_principle_key_is_rejected(self):
        payload = verdicts()
        payload["verdicts"]["33"] = "PASS"
        self.assertInvalid(payload, "unknown principle key(s): 33")

    def test_noncanonical_keys_are_rejected(self):
        for bad_key in ("01", "1.0", "one", "#1"):
            with self.subTest(bad_key=bad_key):
                payload = verdicts()
                payload["verdicts"][bad_key] = payload["verdicts"].pop("1")
                self.assertInvalid(payload, "unknown principle key(s)")

    def test_unknown_verdict_value_is_rejected(self):
        for bad in ("UNKNOWN", "pass", "Pass", "", None, 1, True, ["PASS"]):
            with self.subTest(bad=bad):
                payload = verdicts(**{"5": bad})
                self.assertInvalid(payload, "PASS, PARTIAL, or FAIL")


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
        result = self.run_cli(json.dumps(verdicts()), "--input", "-")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        parsed = json.loads(result.stdout)
        self.assertEqual(parsed["status"], "ok")
        self.assertEqual(parsed["score"], 100)
        self.assertEqual(result.stdout, result.stdout.rstrip() + "\n")

    def test_absolute_file_success(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "verdicts.json"
            path.write_text(json.dumps(verdicts("FAIL")), encoding="utf-8")
            result = self.run_cli("", "--input", str(path))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["tier"], "Not viral yet")

    def test_relative_file_path_is_rejected(self):
        result = self.run_cli("{}", "--input", "verdicts.json")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("absolute", result.stderr)

    def test_missing_verdict_has_stable_error_and_no_partial_result(self):
        payload = verdicts()
        del payload["verdicts"]["12"]
        result = self.run_cli(json.dumps(payload), "--input", "-")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("error[virality-input]: missing principle verdict(s): 12",
                      result.stderr)

    def test_duplicate_key_has_stable_error(self):
        raw = '{"verdicts": {' + ",".join(
            f'"{key}":"PASS"' for key in PRINCIPLE_KEYS
        ) + ',"1":"FAIL"}}'
        result = self.run_cli(raw, "--input", "-")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("duplicate JSON object key", result.stderr)

    def test_malformed_json_has_stable_error(self):
        result = self.run_cli("{", "--input", "-")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertTrue(
            result.stderr.startswith("error[virality-input]: input is not valid JSON:")
        )

    def test_empty_stdin_is_rejected_without_partial_result(self):
        result = self.run_cli("", "--input", "-")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("input is empty", result.stderr)


if __name__ == "__main__":
    unittest.main()
