# Deterministic Dependency Analysis

`analyze_dependencies.py` owns graph validation and numeric graph results for
tasks-generator. The resolver still owns feature coverage, task prose, sprint
explanations, parallel-work judgments, and the final `tasks.md` rendering.

## Input schema

The CLI accepts exactly one top-level key, `tasks`:

```json
{
  "tasks": [
    {
      "task_id": "<positive sprint>.<positive index>",
      "effort_estimate": "1d|2d|3d",
      "depends_on": ["<task id>"],
      "blocks": ["<same-sprint task id>"],
      "title": "optional full worker field",
      "workstream": "optional full worker field"
    }
  ]
}
```

Full sprint-worker records may retain their other fields. The helper requires
`task_id`, `effort_estimate`, `depends_on`, and `blocks`; it does not interpret
prose fields.

- IDs are canonical positive numeric tuples: `1.2` is valid; `1`, `1.0`,
  `01.2`, floats, and booleans are invalid. Sort IDs by `(sprint, index)`, not
  as strings.
- `depends_on` is authoritative and represents `dependency -> dependent`.
  A dependency may point to the same sprint or an earlier sprint, never a
  later sprint. Endpoints must exist and may not self-reference.
- `blocks` is the worker's same-sprint inverse representation. The helper
  derives the complete inverse from `depends_on`; it rejects unknown,
  duplicate, self, cross-sprint, or inconsistent same-sprint `blocks` entries.
  Cross-sprint reciprocal blocks are derived by the resolver after this call.
- `effort_estimate` accepts only `1d`, `2d`, or `3d`; it is the node weight.
- Reject malformed JSON, duplicate task IDs/edges, missing fields, unexpected
  top-level keys, non-finite JSON values, and booleans where typed values are
  expected. Empty `tasks` is valid.

## Success output schema

Exit 0 writes one canonical JSON object to stdout (sorted keys, stable arrays):

```json
{
  "schema_version": 1,
  "status": "ok",
  "task_count": 0,
  "edge_count": 0,
  "critical_path": {
    "task_ids": [],
    "effort_days": 0
  },
  "bottlenecks": [],
  "cycles": []
}
```

`critical_path.task_ids` is the deterministic longest node-weighted path across
all disconnected components; `effort_days` is the sum of its `1d`/`2d`/`3d`
weights. Equal-cost complete paths use lexicographically smallest numeric ID
sequences, so `2` sorts before `10`.

`bottlenecks` contains objects for every task with at least five distinct direct
downstream dependents, sorted by numeric task ID:

```json
"bottlenecks": [
  {"task_id": "1.1", "direct_dependents": 5}
]
```

`cycles` is an empty list on success. A directed cycle is an error: the helper
reports one deterministic actual cycle witness, not downstream nodes left over
after a failed root-only traversal. It writes no partial JSON on failure.

## CLI

Resolve the script from this skill's installed directory and quote the resulting
absolute path. A resolver with the graph in memory should use stdin:

```bash
printf '%s' "$graph_json" | python3 "$script_path" --input -
```

For a JSON file, use an absolute quoted path:

```bash
python3 "$script_path" --input "/absolute/path/to/graph.json"
```

`--input -` is stdin and is the default. Relative file paths are rejected.
Invalid input or a cycle exits 2, prints a stable `error[graph-input]: ...`
diagnostic on stderr, and leaves stdout empty. The helper uses only Python's
standard library; it performs no network access, subprocess execution, `eval`,
git operation, file write, or `tasks.md` rendering.

## Resolver handoff

After the resolver has loaded worker records and applied its feature/coverage
checks, pass the compact `{ "tasks": [...] }` graph to this helper. Consume
`critical_path`, `bottlenecks`, and the cycle/error result directly. Do not
recompute path sums, bottleneck counts, or cycle membership in prose. If the
helper rejects the graph, stop before rendering `tasks.md`; the model may still
explain the correction, but may not override the deterministic result.

## Fixture command

Run the local standard-library fixtures from the repository root:

```bash
python3 -m unittest discover -s skills/tasks-generator/tests -p 'test_*.py'
```
