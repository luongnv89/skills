#!/usr/bin/env python3
"""Calculate the weighted SEO score from five model-owned dimension scores.

The model or caller supplies the evidence-backed dimension assessments.  This
helper performs only strict validation, null-aware weight renormalization, and
Decimal ROUND_HALF_UP aggregation.  It emits canonical JSON on stdout and
never fetches pages, writes reports, or changes the input evidence.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
import math
from pathlib import Path
import sys
from typing import Any, Dict, List, Mapping, Optional, Sequence


SCHEMA_VERSION = 1
DIMENSION_WEIGHTS = {
    "meta_tags": Decimal("0.20"),
    "heading_structure": Decimal("0.15"),
    "image_alt_text": Decimal("0.15"),
    "structured_data": Decimal("0.20"),
    "crawlability": Decimal("0.30"),
}
DIMENSION_KEYS = tuple(DIMENSION_WEIGHTS)
ZERO = Decimal("0")
ONE_HUNDRED = Decimal("100")


class InputError(ValueError):
    """A stable, user-facing input or schema error."""


def _duplicate_key_object(pairs: List[tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InputError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise InputError(f"non-finite JSON number is not allowed: {value}")


def _decimal_value(value: Any, label: str) -> Optional[Decimal]:
    if value is None:
        return None
    if isinstance(value, bool):
        raise InputError(f"{label} must be an integer 0..100 or null, not boolean")
    if isinstance(value, Decimal):
        decimal = value
    elif isinstance(value, int):
        decimal = Decimal(value)
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise InputError(f"{label} must be finite, got {value!r}")
        # str() avoids importing a binary float approximation into Decimal.
        try:
            decimal = Decimal(str(value))
        except InvalidOperation as exc:
            raise InputError(f"{label} must be a finite number") from exc
    else:
        raise InputError(f"{label} must be an integer 0..100 or null")

    if not decimal.is_finite():
        raise InputError(f"{label} must be finite, got {value!r}")
    if decimal.as_tuple().exponent != 0 or decimal != decimal.to_integral_value():
        raise InputError(f"{label} must be an integer 0..100 or null")
    if decimal < ZERO or decimal > ONE_HUNDRED:
        raise InputError(f"{label} must be between 0 and 100 inclusive")
    return decimal


def _validate_dimensions(payload: Any) -> Dict[str, Optional[int]]:
    if not isinstance(payload, dict):
        raise InputError(f"input must be a JSON object, got {type(payload).__name__}")

    expected = set(DIMENSION_KEYS)
    actual = set(payload)
    if any(not isinstance(key, str) for key in actual):
        raise InputError("dimension keys must be strings")
    missing = [key for key in DIMENSION_KEYS if key not in payload]
    extra = sorted(actual - expected)
    if missing:
        raise InputError(f"missing required dimension key(s): {', '.join(missing)}")
    if extra:
        raise InputError(f"unexpected dimension key(s): {', '.join(extra)}")

    dimensions: Dict[str, Optional[int]] = {}
    for key in DIMENSION_KEYS:
        value = _decimal_value(payload[key], key)
        dimensions[key] = None if value is None else int(value)
    return dimensions


def calculate_score(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate five dimensions and return the deterministic SEO result."""
    dimensions = _validate_dimensions(payload)
    known = [key for key in DIMENSION_KEYS if dimensions[key] is not None]
    unavailable = [key for key in DIMENSION_KEYS if dimensions[key] is None]

    if not known:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "PARTIAL",
            "availability": "unavailable",
            "reason": "all_dimensions_unavailable",
            "score": None,
            "dimension_scores": dimensions,
            "unavailable_dimensions": unavailable,
        }

    denominator = sum((DIMENSION_WEIGHTS[key] for key in known), ZERO)
    weighted_sum = sum(
        (DIMENSION_WEIGHTS[key] * Decimal(dimensions[key]) for key in known),
        ZERO,
    )
    score = int((weighted_sum / denominator).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    partial = bool(unavailable)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "PARTIAL" if partial else "PASS",
        "availability": "partial" if partial else "available",
        "reason": "some_dimensions_unavailable" if partial else None,
        "score": score,
        "dimension_scores": dimensions,
        "unavailable_dimensions": unavailable,
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
            raise InputError(f"cannot read --input file {path}: {exc}") from exc

    if not raw.strip():
        raise InputError("input is empty")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InputError(f"input is not valid UTF-8: {exc}") from exc
    try:
        return json.loads(
            text,
            object_pairs_hook=_duplicate_key_object,
            parse_int=Decimal,
            parse_float=Decimal,
            parse_constant=_reject_constant,
        )
    except InputError:
        raise
    except json.JSONDecodeError as exc:
        raise InputError(f"input is not valid JSON: {exc}") from exc


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Calculate a deterministic weighted SEO score from five dimensions."
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
        print(f"error[seo-input]: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover - last-resort no-traceback contract
        print(f"error[internal]: {exc}", file=sys.stderr)
        return 2

    json.dump(result, sys.stdout, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
