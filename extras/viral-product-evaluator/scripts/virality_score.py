#!/usr/bin/env python3
"""Calculate the Virality Score and tier from the 32 principle verdicts.

The caller supplies evidence-backed verdicts for every principle.  This helper
performs only strict coverage validation, point summation, Decimal
ROUND_HALF_UP normalization, and tier lookup.  It emits canonical JSON on
stdout and never reads the codebase, fetches pages, or writes
``viral-evaluation.md``.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


SCHEMA_VERSION = 1
PRINCIPLE_COUNT = 32
EXPECTED_KEYS = frozenset(str(number) for number in range(1, PRINCIPLE_COUNT + 1))
VERDICT_POINTS = {
    "PASS": Decimal("1"),
    "PARTIAL": Decimal("0.5"),
    "FAIL": Decimal("0"),
}

# Tier thresholds from references/principles.md — the single source of truth
# for where each band starts.
TIER_BANDS: Tuple[Tuple[int, str], ...] = (
    (85, "Viral-ready"),
    (65, "Promising"),
    (40, "Needs work"),
    (0, "Not viral yet"),
)


class InputError(ValueError):
    """A stable, user-facing input or schema error."""


def _duplicate_key_object(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InputError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise InputError(f"non-finite JSON number is not allowed: {value}")


def _validate_verdicts(payload: Any) -> Dict[str, str]:
    if not isinstance(payload, dict):
        raise InputError(
            f"input must be a JSON object, got {type(payload).__name__}"
            ' — pass {"verdicts": {"1": "PASS", ...}}'
        )
    if any(not isinstance(key, str) for key in payload):
        raise InputError("top-level keys must be strings — quote every key")
    if "verdicts" not in payload:
        raise InputError(
            "missing required top-level key: verdicts"
            ' — the payload must be {"verdicts": {"1": "PASS", ...}}'
        )
    extra = sorted(set(payload) - {"verdicts"})
    if extra:
        raise InputError(
            f"unexpected top-level key(s): {', '.join(extra)}"
            ' — only "verdicts" is allowed'
        )

    verdicts = payload["verdicts"]
    if not isinstance(verdicts, dict):
        raise InputError(
            f"verdicts must be a JSON object, got {type(verdicts).__name__}"
            " — map each principle number to PASS, PARTIAL or FAIL"
        )

    keys = set(verdicts)
    if any(not isinstance(key, str) for key in keys):
        raise InputError('verdict keys must be strings — use "1" ... "32"')
    unknown = sorted(keys - EXPECTED_KEYS, key=_sort_key)
    if unknown:
        raise InputError(
            f"unknown principle key(s): {', '.join(unknown)}"
            " — use only principle numbers 1-32"
        )
    missing = sorted(EXPECTED_KEYS - keys, key=_sort_key)
    if missing:
        raise InputError(
            f"missing principle verdict(s): {', '.join(missing)}"
            " — score all 32 principles; use FAIL for absent features"
        )

    validated: Dict[str, str] = {}
    for key in sorted(EXPECTED_KEYS, key=_sort_key):
        value = verdicts[key]
        if not isinstance(value, str) or value not in VERDICT_POINTS:
            raise InputError(
                f"verdicts[{key!r}] must be PASS, PARTIAL, or FAIL, got {value!r}"
            )
        validated[key] = value
    return validated


def _sort_key(principle: str) -> Tuple[int, Any]:
    """Sort canonical numeric keys numerically; malformed keys last, by name."""
    try:
        return (0, int(principle))
    except ValueError:
        return (1, principle)


def _tier(score: int) -> str:
    for threshold, label in TIER_BANDS:
        if score >= threshold:
            return label
    raise AssertionError("unreachable: score is always >= 0")


def calculate_score(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate the 32 verdicts and return the deterministic result."""
    verdicts = _validate_verdicts(payload)
    counts = {"pass": 0, "partial": 0, "fail": 0}
    points = Decimal("0")
    for key in EXPECTED_KEYS:
        verdict = verdicts[key]
        counts[verdict.lower()] += 1
        points += VERDICT_POINTS[verdict]

    score = int(
        (points * 100 / PRINCIPLE_COUNT).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "ok",
        "counts": counts,
        "points": float(points),
        "score": score,
        "tier": _tier(score),
    }


def _read_payload(input_path: str) -> Any:
    if input_path == "-":
        raw = sys.stdin.buffer.read()
    else:
        path = Path(input_path)
        if not path.is_absolute():
            raise InputError("--input path must be absolute, or '-' for stdin")
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise InputError(
                f"cannot read --input file {path}: {exc}"
                " — check the path exists and is readable, or pass '-' for stdin"
            ) from exc
    if not raw.strip():
        raise InputError(
            "input is empty"
            ' — provide a JSON object like {"verdicts": {"1": "PASS", ...}} covering all 32 principles'
        )
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InputError(
            f"input is not valid UTF-8: {exc} — re-encode the payload as UTF-8"
        ) from exc
    try:
        return json.loads(
            text,
            object_pairs_hook=_duplicate_key_object,
            parse_constant=_reject_constant,
        )
    except InputError:
        raise
    except json.JSONDecodeError as exc:
        raise InputError(
            f"input is not valid JSON: {exc}"
            ' — fix the JSON syntax; the payload must be one object with a "verdicts" key'
        ) from exc


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Calculate the Virality Score and tier from 32 verdicts."
    )
    parser.add_argument(
        "--input",
        default="-",
        metavar="PATH|-",
        help="absolute JSON file path, or '-' for stdin (default: stdin)",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        payload = _read_payload(args.input)
        result = calculate_score(payload)
    except InputError as exc:
        print(f"error[virality-input]: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover - last-resort no-traceback contract
        print(f"error[internal]: {exc}", file=sys.stderr)
        return 2

    json.dump(result, sys.stdout, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
