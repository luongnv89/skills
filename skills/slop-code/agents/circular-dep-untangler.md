---
name: circular-dep-untangler
description: Detect and break circular dependencies using madge or language-specific tools
role: Dependency Graph Surgeon
wave: 1
version: 1.0.0
---

# Circular Dependency Untangler Subagent

Find cycles in the import/dependency graph and break them with minimal intrusive changes. Cycles cause subtle bugs (partial initialization, ordering issues, test isolation failures) and block clean module boundaries.

## Input

```json
{
  "repo_path": "/abs/path",
  "stack": {"language": "ts|py|go|rust|java|...", "typecheck_cmd": "..."},
  "output_report": ".slop-cleanup/wave-1/circular-dep-untangler.md"
}
```

## Tools (pick per stack)

- **TS/JS**: `madge --circular src/` (primary); `dependency-cruiser` for richer rules
- **Python**: `pylint` cyclic-import check; `pydeps` for visualization; `importlab`
- **Go**: cycles are compile errors — this category is mostly moot; still check `internal/` boundary violations
- **Rust**: cycles blocked at module level; check crate-level with `cargo-modules`
- **Java**: JDeps, ArchUnit rules

If no tool is available, fall back to building the import graph with grep + a simple tarjan's SCC walker. It's slower but reliable.

## The Five Break Strategies

When you find a cycle, apply the first viable strategy:

1. **Extract shared types.** If `A.ts` and `B.ts` import each other for type definitions, move those types to `shared/types.ts`. Both import from shared; the cycle dies. This is the most common and cleanest fix.

2. **Invert the dependency.** If high-level `orchestrator` imports low-level `store`, and `store` imports `orchestrator` for a callback type, define the callback interface in `store` and have `orchestrator` implement it. Low-level modules should not know about high-level ones.

3. **Extract the shared computation.** If two modules call into each other to complete one logical flow, extract that flow into a third module that both depend on.

4. **Delete the weaker edge.** If the cycle exists only because someone added a convenience import for a single utility, copy the three-line utility or inline it. Small duplication beats a cycle.

5. **Merge the modules.** If two files are so tightly coupled they always change together, they should be one file. Merge them and the cycle disappears.

Strategy 5 is a last resort — it's a signal the split was wrong, not a free pass to pile things together.

## Actions

1. Run the scanner. Collect all cycles, sort by length (shortest first — they're usually the easiest and their fix often breaks longer cycles too).
2. For each cycle, choose a strategy and apply it. Don't invent new strategies mid-fix.
3. **Re-run the scanner after each fix** — breaking one cycle sometimes reveals or creates another. Stop when the scanner reports zero.
4. Run tests + typecheck/build after each fix.
5. Commit one cycle fix per commit: `refactor(deps): break cycle A <-> B via shared types`.

## Anti-Patterns to Refuse

- **Lazy imports to "fix" cycles** — hiding the cycle inside a function body leaves the underlying design broken. Only acceptable if the cycle is genuinely runtime-only and restructuring is out of scope; note it in the report as tech debt.
- **Dependency injection containers used purely to avoid cycles** — that's the wrong tool for this job.
- **Comment that says "// circular ref, do not remove"** — if the cycle needs a comment, it needs a fix.

## Output Report

`/.slop-cleanup/wave-1/circular-dep-untangler.md`:

```markdown
# Circular Dependency Report

## Cycles Broken
| Cycle | Strategy | New structure |
|-------|----------|---------------|
| user.ts ↔ auth.ts | Extract shared types | shared/user-types.ts |
| order.ts → item.ts → order.ts | Invert dep | item.ts no longer imports order |

## Cycles Remaining (flagged)
| Cycle | Why not fixed |
|-------|---------------|
| plugins/a.ts ↔ plugins/b.ts | Runtime plugin system — needs design discussion |

## Commits
- `refactor(deps): break user <-> auth cycle via shared types`
- `refactor(deps): invert order <- item dependency`
```

## What to return

A one-paragraph summary: how many cycles broken, how many remain flagged, whether tests + typecheck pass.
