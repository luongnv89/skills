# Deterministic SEO Scoring

`score_seo.py` is the arithmetic boundary for the analyzer's five SEO
sub-scores. The model remains responsible for fetching evidence, applying the
rubrics below, and deciding whether a dimension is known or unavailable. The
helper does not inspect HTML, fetch URLs, or invent evidence.

## Input schema

The JSON input is exactly the inner `seo.dimension_scores` map:

```json
{
  "meta_tags": 80,
  "heading_structure": 60,
  "image_alt_text": 90,
  "structured_data": null,
  "crawlability": 75
}
```

Exactly these five keys are required, with no extras:

| Key | Weight |
|---|---:|
| `meta_tags` | `0.20` |
| `heading_structure` | `0.15` |
| `image_alt_text` | `0.15` |
| `structured_data` | `0.20` |
| `crawlability` | `0.30` |

Each value must be an explicit JSON integer from `0` through `100`, or JSON
`null` when the model cannot compute that dimension. Booleans, strings,
arrays, fractional values, negative values, values above `100`, non-finite
numbers, missing keys, and unknown keys are rejected. JSON numbers are parsed
through `Decimal` rather than binary floating-point before validation and
calculation.

## Output schema

The successful output is canonical JSON with these fields:

```json
{
  "schema_version": 1,
  "status": "PASS",
  "availability": "available",
  "reason": null,
  "score": 72,
  "dimension_scores": {
    "meta_tags": 80,
    "heading_structure": 60,
    "image_alt_text": 90,
    "structured_data": null,
    "crawlability": 75
  },
  "unavailable_dimensions": ["structured_data"]
}
```

`score` is an integer rounded with `Decimal` `ROUND_HALF_UP` after known
weights are renormalized:

```text
sum(weight[key] * score[key] for known key)
/ sum(weight[key] for known key)
```

The result is not rounded with Python's banker rounding. For example, an
exact `51.5` becomes `52`. The `dimension_scores` values are returned unchanged
so downstream can preserve `seo.dimension_scores`; the returned `score` maps to
`seo.score`.

- All five known: `status: "PASS"`, `availability: "available"`,
  `unavailable_dimensions: []`, `reason: null`.
- Some null: `status: "PARTIAL"`, `availability: "partial"`,
  `reason: "some_dimensions_unavailable"`; known weights are renormalized.
- All five null: `status: "PARTIAL"`, `availability: "unavailable"`,
  `reason: "all_dimensions_unavailable"`, and `score: null`.

An all-null result is unavailable, not a numeric zero or a perfect score. Do
not coerce its `score` to `0`, `100`, or any other value; downstream reports
must not rank or compare it as a measured score.

## CLI invocation

Resolve the helper from this skill's installed directory to a quoted absolute
path. For example, with a trusted absolute skill directory:

```bash
skill_root="$(cd -- "/absolute/path/to/website-analyzer" && pwd)"
script_path="$skill_root/scripts/score_seo.py"
```

Send the extracted dimension map on stdin when it is already in memory:

```bash
printf '%s' "$dimension_scores_json" | python3 "$script_path" --input -
```

For a JSON file, use a quoted absolute path:

```bash
python3 "$script_path" --input "/absolute/path/to/dimension-scores.json"
```

`--input -` is stdin and is the default. Relative file paths are rejected. On
success, stdout contains exactly one deterministic JSON result and stderr is
empty. On malformed JSON, schema/type/range failure, or non-finite input, the
helper exits `2`, prints one concise `error[seo-input]: ...` diagnostic to
stderr, and leaves stdout empty. It does not write a report or modify the input.

## Resolver handoff

The analyzer supplies evidence-backed sub-scores and explicit nulls, invokes
the helper, and copies only its deterministic `score`,
`dimension_scores`, `status`, `availability`, `reason`, and
`unavailable_dimensions` fields into the final SEO object. It must preserve the
all-null `score: null` exception and report `PARTIAL`; qualitative evidence,
rubric interpretation, and notes remain model-owned.
