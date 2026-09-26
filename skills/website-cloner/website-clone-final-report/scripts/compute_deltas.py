#!/usr/bin/env python3
"""Compute deterministic before/after deltas for the final clone report.

The caller supplies explicit comparison records.  This helper validates source
kinds and units, computes only numeric arithmetic, and compares booleans/lists
as typed values.  It does not interpret whether a negative change is good or
bad, fetch evidence, or write final-report.md.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
import json
import math
from pathlib import Path
import sys
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


SCHEMA_VERSION = 1

NUMERIC_FIELDS: Tuple[Tuple[str, str], ...] = (
    ("performance.lcp_estimate_seconds", "seconds"),
    ("performance.cls_estimate", "unitless"),
    ("performance.ttfb_estimate_seconds", "seconds"),
    ("performance.total_page_weight_kb", "KB"),
    ("performance.request_count", "count"),
    ("seo.score", "score"),
    ("seo.dimension_scores.meta_tags", "score"),
    ("seo.dimension_scores.heading_structure", "score"),
    ("seo.dimension_scores.image_alt_text", "score"),
    ("seo.dimension_scores.structured_data", "score"),
    ("seo.dimension_scores.crawlability", "score"),
)
BOOLEAN_FIELDS = ("security.https", "security.mixed_content")
ARRAY_FIELDS = ("security.security_headers", "security.exposed_metadata")
EXPECTED_FIELDS = tuple(name for name, _ in NUMERIC_FIELDS) + BOOLEAN_FIELDS + ARRAY_FIELDS
EXPECTED_KINDS = {
    **{name: "numeric" for name, _ in NUMERIC_FIELDS},
    **{name: "boolean" for name in BOOLEAN_FIELDS},
    **{name: "array" for name in ARRAY_FIELDS},
}
EXPECTED_UNITS = dict(NUMERIC_FIELDS)
DECIMAL_ONE_HUNDRED = Decimal("100")
DECIMAL_INTEGER = Decimal("1")


class InputError(ValueError):
    """A stable, user-facing input or schema error."""


class Source:
    """Presence/value pair so missing and explicit JSON null remain distinct."""

    def __init__(self, present: bool, value: Any = None) -> None:
        self.present = present
        self.value = value


def _duplicate_key_object(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InputError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise InputError(f"non-finite JSON number is not allowed: {value}")


def _check_finite(value: Any, path: str = "$") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise InputError(f"{path} must be finite")
    if isinstance(value, Decimal) and not value.is_finite():
        raise InputError(f"{path} must be finite")
    if isinstance(value, list):
        for index, child in enumerate(value):
            _check_finite(child, f"{path}[{index}]")
    elif isinstance(value, dict):
        for key, child in value.items():
            _check_finite(child, f"{path}.{key}")


def _decimal(value: Any, label: str) -> Decimal:
    if isinstance(value, bool):
        raise InputError(f"{label} must be a finite number, not boolean")
    if isinstance(value, Decimal):
        result = value
    elif isinstance(value, int):
        result = Decimal(value)
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise InputError(f"{label} must be finite")
        try:
            result = Decimal(str(value))
        except InvalidOperation as exc:
            raise InputError(f"{label} must be a finite number") from exc
    else:
        raise InputError(f"{label} must be a finite number")
    if not result.is_finite():
        raise InputError(f"{label} must be finite")
    return result


def _source(record: Mapping[str, Any], side: str) -> Source:
    return Source(side in record, record.get(side))


def _unit(record: Mapping[str, Any], side: str) -> Optional[str]:
    key = f"{side}_unit"
    if key not in record or record[key] is None:
        return None
    value = record[key]
    if not isinstance(value, str) or not value:
        raise InputError(f"{key} must be a non-empty string or null")
    return value


def _issues_for_sources(before: Source, after: Source) -> List[str]:
    issues: List[str] = []
    for side, source in (("before", before), ("after", after)):
        if not source.present:
            issues.append(f"missing_{side}")
        elif source.value is None:
            issues.append(f"null_{side}")
    return issues


def _primary_reason(issues: Sequence[str]) -> Optional[str]:
    if not issues:
        return None
    if len(issues) == 1:
        return issues[0]
    return "multiple_issues"


def _unit_issue(
    field: str, before_unit: Optional[str], after_unit: Optional[str]
) -> Optional[str]:
    # Both absent is explicitly compatible: source snapshots often omit units
    # when the field name itself is canonical. One-sided absence is not safe.
    if before_unit is None and after_unit is None:
        return None
    expected = EXPECTED_UNITS[field]
    if before_unit is None or after_unit is None:
        return "unit_mismatch"
    if before_unit != after_unit or before_unit != expected:
        return "unit_mismatch"
    return None


def _numeric_result(field: str, record: Mapping[str, Any]) -> Dict[str, Any]:
    before = _source(record, "before")
    after = _source(record, "after")
    before_unit = _unit(record, "before")
    after_unit = _unit(record, "after")

    source_issues = _issues_for_sources(before, after)
    # Bool/array/string values are rejected rather than silently coerced into
    # arithmetic. Explicit null/missing values remain structured PARTIAL data.
    before_decimal = None if not before.present or before.value is None else _decimal(before.value, f"{field}.before")
    after_decimal = None if not after.present or after.value is None else _decimal(after.value, f"{field}.after")
    unit_issue = _unit_issue(field, before_unit, after_unit)
    issues = source_issues + ([unit_issue] if unit_issue else [])

    result: Dict[str, Any] = {
        "kind": "numeric",
        "before": before_decimal,
        "after": after_decimal,
        "before_unit": before_unit,
        "after_unit": after_unit,
        "absolute_change": None,
        "percent_change": None,
        "reason": _primary_reason(issues),
    }
    if issues:
        if unit_issue and not source_issues:
            result["reason"] = unit_issue
        if len(issues) > 1:
            result["diagnostics"] = list(issues)
        return result

    assert before_decimal is not None and after_decimal is not None
    with localcontext() as context:
        context.prec = max(
            50,
            len(before_decimal.as_tuple().digits)
            + len(after_decimal.as_tuple().digits)
            + 20,
        )
        absolute = after_decimal - before_decimal
        result["absolute_change"] = absolute if absolute != 0 else Decimal("0")
        if before_decimal == 0:
            result["reason"] = "zero_baseline"
        else:
            percent = (absolute / before_decimal * DECIMAL_ONE_HUNDRED).quantize(
                DECIMAL_INTEGER, rounding=ROUND_HALF_UP
            )
            result["percent_change"] = percent if percent != 0 else Decimal("0")
    return result


def _typed_result(field: str, record: Mapping[str, Any], kind: str) -> Dict[str, Any]:
    before = _source(record, "before")
    after = _source(record, "after")
    issues = _issues_for_sources(before, after)
    if not issues:
        if kind == "boolean":
            if not isinstance(before.value, bool) or not isinstance(after.value, bool):
                raise InputError(f"{field} requires boolean before/after values")
        else:
            if not isinstance(before.value, list) or not isinstance(after.value, list):
                raise InputError(f"{field} requires array before/after values")

    result: Dict[str, Any] = {
        "kind": kind,
        "before": before.value if before.present else None,
        "after": after.value if after.present else None,
        "changed": None,
        "reason": _primary_reason(issues),
    }
    if kind == "array":
        # Arrays compare by reproducible counts, so the helper owns len() and
        # the report renders these counts directly.
        result["before_count"] = (
            len(before.value) if isinstance(before.value, list) else None
        )
        result["after_count"] = (
            len(after.value) if isinstance(after.value, list) else None
        )
    if issues:
        if len(issues) > 1:
            result["diagnostics"] = list(issues)
        return result
    if kind == "array":
        result["changed"] = result["before_count"] != result["after_count"]
    else:
        result["changed"] = before.value != after.value
    return result


def _validate_payload(payload: Any) -> Dict[str, Mapping[str, Any]]:
    if not isinstance(payload, dict):
        raise InputError(f"input must be a JSON object, got {type(payload).__name__}")
    if any(not isinstance(key, str) for key in payload):
        raise InputError("top-level keys must be strings")
    if "comparisons" not in payload:
        raise InputError("missing required top-level key: comparisons")
    extra = sorted(set(payload) - {"comparisons"})
    if extra:
        raise InputError(f"unexpected top-level key(s): {', '.join(extra)}")
    comparisons = payload["comparisons"]
    if not isinstance(comparisons, dict):
        raise InputError(f"comparisons must be a JSON object, got {type(comparisons).__name__}")

    validated: Dict[str, Mapping[str, Any]] = {}
    for field, record in comparisons.items():
        if not isinstance(field, str) or field not in EXPECTED_KINDS:
            raise InputError(f"unknown comparison field: {field!r}")
        if not isinstance(record, dict):
            raise InputError(f"comparisons[{field!r}] must be a JSON object")
        allowed = {"kind", "before", "after"}
        if EXPECTED_KINDS[field] == "numeric":
            allowed.update({"before_unit", "after_unit"})
        unknown = sorted(set(record) - allowed)
        if unknown:
            raise InputError(
                f"comparisons[{field!r}] unexpected key(s): {', '.join(unknown)}"
            )
        expected_kind = EXPECTED_KINDS[field]
        if record.get("kind") != expected_kind:
            raise InputError(
                f"comparisons[{field!r}].kind must be {expected_kind!r}"
            )
        validated[field] = record
    return validated


def calculate_deltas(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate comparison records and return deterministic delta results."""
    if not isinstance(payload, dict):
        raise InputError(f"input must be a JSON object, got {type(payload).__name__}")
    _check_finite(payload)
    comparisons = _validate_payload(payload)
    rendered: Dict[str, Any] = {}
    unavailable: List[str] = []

    for field in sorted(comparisons):
        record = comparisons[field]
        kind = EXPECTED_KINDS[field]
        if kind == "numeric":
            item = _numeric_result(field, record)
            if item["absolute_change"] is None or item["percent_change"] is None:
                unavailable.append(field)
        else:
            item = _typed_result(field, record, kind)
            if item["changed"] is None:
                unavailable.append(field)
        rendered[field] = item

    missing = [field for field in EXPECTED_FIELDS if field not in comparisons]
    unavailable.extend(missing)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "PARTIAL" if unavailable else "PASS",
        "comparisons": rendered,
        "missing_comparisons": missing,
        "unavailable_comparisons": sorted(set(unavailable)),
    }


def _format_decimal(value: Decimal) -> str:
    if not value.is_finite():
        raise InputError("cannot serialize non-finite decimal")
    if value == 0:
        return "0"
    return format(value.normalize(), "f")


def _canonical_json(value: Any) -> str:
    if isinstance(value, Decimal):
        return _format_decimal(value)
    if value is None or isinstance(value, (bool, int, float, str)):
        return json.dumps(value, ensure_ascii=True, separators=(",", ":"))
    if isinstance(value, list):
        return "[" + ",".join(_canonical_json(item) for item in value) + "]"
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise InputError("output object keys must be strings")
        members = []
        for key in sorted(value):
            members.append(
                json.dumps(key, ensure_ascii=True, separators=(",", ":"))
                + ":"
                + _canonical_json(value[key])
            )
        return "{" + ",".join(members) + "}"
    raise InputError(f"cannot serialize output type: {type(value).__name__}")


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
        description="Compute deterministic before/after deltas for clone-report fields."
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
        result = calculate_deltas(payload)
        output = _canonical_json(result)
    except InputError as exc:
        print(f"error[delta-input]: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover - last-resort no-traceback contract
        print(f"error[internal]: {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(output + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
