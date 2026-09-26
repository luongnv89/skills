# Deterministic Delta Computation

`compute_deltas.py` owns the before/after arithmetic for the final clone
report. The model remains responsible for extracting each baseline/after
value, deciding whether evidence exists, rendering the report, and all UI/UX
judgment. The helper does not read snapshots, fetch pages, or write
`final-report.md`.

## Input schema

The CLI accepts exactly one top-level key, `comparisons`, mapping each
canonical field to a record:

```json
{
  "comparisons": {
    "performance.lcp_estimate_seconds": {
      "kind": "numeric",
      "before": 4.2,
      "after": 1.8,
      "before_unit": "seconds",
      "after_unit": "seconds"
    },
    "security.https": {"kind": "boolean", "before": true, "after": true},
    "security.security_headers": {
      "kind": "array",
      "before": ["x-frame-options"],
      "after": ["x-frame-options", "content-security-policy"]
    }
  }
}
```

Exactly these fields are known — omit a field only when its snapshot lacks it:

| Field | Kind | Expected unit |
|---|---|---|
| `performance.lcp_estimate_seconds` | `numeric` | `seconds` |
| `performance.cls_estimate` | `numeric` | `unitless` |
| `performance.ttfb_estimate_seconds` | `numeric` | `seconds` |
| `performance.total_page_weight_kb` | `numeric` | `KB` |
| `performance.request_count` | `numeric` | `count` |
| `seo.score` | `numeric` | `score` |
| `seo.dimension_scores.meta_tags` | `numeric` | `score` |
| `seo.dimension_scores.heading_structure` | `numeric` | `score` |
| `seo.dimension_scores.image_alt_text` | `numeric` | `score` |
| `seo.dimension_scores.structured_data` | `numeric` | `score` |
| `seo.dimension_scores.crawlability` | `numeric` | `score` |
| `security.https` | `boolean` | — |
| `security.mixed_content` | `boolean` | — |
| `security.security_headers` | `array` | — |
| `security.exposed_metadata` | `array` | — |

Record rules:

- `kind` is required and must match the field's expected kind exactly.
- `before`/`after` hold the snapshot values, an explicit JSON `null`, or are
  absent when the snapshot lacks the field. Numeric values must be finite
  numbers; booleans must be JSON `true`/`false`; arrays must be JSON lists.
  Booleans-as-numbers and strings are rejected, never coerced.
- `before_unit`/`after_unit` are optional on numeric records only. When both
  are present they must equal each other and the expected unit; a one-sided or
  mismatched unit yields `unit_mismatch`, not a computed delta. Both absent is
  compatible.
- Unknown fields, unexpected record keys, missing `kind`, and extra top-level
  keys are rejected.

## Output schema

Exit 0 writes one canonical JSON object to stdout:

```json
{
  "schema_version": 1,
  "status": "PASS",
  "comparisons": {
    "seo.score": {
      "kind": "numeric",
      "before": 62,
      "after": 94,
      "before_unit": null,
      "after_unit": null,
      "absolute_change": 32,
      "percent_change": 52,
      "reason": null
    }
  },
  "missing_comparisons": [],
  "unavailable_comparisons": []
}
```

- Numeric results carry `absolute_change` (`after - before`) and
  `percent_change` (`(after - before) / before × 100`, Decimal `ROUND_HALF_UP`
  to the nearest whole percent — an exact `…​.5` rounds up). When
  `before` is `0`, `percent_change` is `null` and `reason` is
  `zero_baseline`; render the absolute change and label the percentage
  `N/A (zero baseline)`.
- Boolean results carry `changed` from direct `!=` comparison.
- Array results carry `before_count`, `after_count`, and `changed` from
  comparing those counts; render the counts in the report table.
- Missing or null sources and unit mismatches leave the delta fields `null`
  with a `reason` of `missing_before`/`missing_after`, `null_before`/
  `null_after`, `multiple_issues` (details in `diagnostics`), or
  `unit_mismatch`.
- `status` is `PARTIAL` whenever any field is missing or unavailable;
  `missing_comparisons` lists absent fields and `unavailable_comparisons`
  lists every field without a computed delta.

## CLI invocation

Resolve the helper from this skill's installed directory to a quoted absolute
path and send the comparison map on stdin:

```bash
printf '%s' "$comparisons_json" | python3 "$script_path" --input -
```

For a JSON file, use a quoted absolute path:

```bash
python3 "$script_path" --input "/absolute/path/to/comparisons.json"
```

`--input -` is stdin and is the default. Relative file paths are rejected.
Malformed JSON, schema/type/unit failures, or non-finite input exit `2`,
print one `error[delta-input]: ...` diagnostic to stderr, and leave stdout
empty. The helper uses only Python's standard library; it performs no network
access, subprocess execution, `eval`, git operation, file write, or report
rendering.

## Report handoff

Consume `comparisons`, `missing_comparisons`, and `unavailable_comparisons`
directly; never recompute or round deltas in prose. Every field without a
computed delta keeps the report `PARTIAL` — show the absolute change for
`zero_baseline` and mark unavailable cells rather than inventing values.
UI/UX change descriptions remain model judgment from tasks.md versus the
Phase 1 analysis.

## Fixture command

Run the local standard-library fixtures from the repository root:

```bash
python3 -m unittest discover -s skills/website-cloner/website-clone-final-report/tests -p 'test_*.py'
```
