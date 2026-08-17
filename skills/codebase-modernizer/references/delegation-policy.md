# Delegation policy

The dimension table in `SKILL.md` says *which* path each dimension takes. This file says how to walk
each path without breaking the read-only contract.

**One rule governs every dimension: a delegate is invoked only if it changes no tracked file.**

## Invoked path — `BUG`, `PERF`, `UX`

These three delegates only read and report, so calling them during an audit is safe. Call them with
the Skill tool:

| Dim | Call | Args |
|---|---|---|
| `BUG` | `skill: "code-review"` | `args: "mode:review <scope>"` |
| `PERF` | `skill: "code-review"` | `args: "mode:perf <scope>"` |
| `UX` | `skill: "dont-make-me-think"` | review mode only — see the caution below |

Normalize each delegate's output into finding records with this skill's own `F-<DIM>-<NNN>` IDs and
`path:line` evidence, then record `Path: delegated` for the dimension. A delegate's own severity
labels are advisory — re-rank against `references/dimension-map.md` so severities stay comparable
across dimensions.

Two cautions:

- **`code-review` mode `review` writes its own `CODE_REVIEW.md`.** That is a **declared artifact**,
  not a contract breach — but it must appear in the report's Artifacts section. Mode `perf` writes
  no file.
- **`dont-make-me-think` has a Redesign Mode that edits UI source files.** Never let it enter that
  mode: ask for the usability review only, and decline any offer to apply fixes. If it has already
  modified a file before you could decline, that is a contract breach — report it, restore the file,
  and note the incident in Limitations.

## Inline path — `CLEAN`, `DEAD`, `TEST`, `CI`, `SEC`, `DOCS`

These six delegates **write**. They install hooks, configure CI, generate test files, rewrite docs,
or refactor source. Invoking one during an audit would break the read-only contract, so never do it —
not even with a flag that promises otherwise.

Instead, for each dimension:

1. Audit it yourself with that dimension's checklist in `references/dimension-map.md`.
2. Record `Path: inline`.
3. Name the delegate skill as the invocation in the plan task that does the work later.

Here `inline` is the **expected** path, not a degradation. Do not report it as a limitation, and do
not describe these dimensions as shallowly audited — the checklist is the intended depth.

## Skill tool unavailable

When the Skill tool is absent, or the session's skill list cannot be enumerated, the three invoked
dimensions fall back to inline as well. That *is* reduced depth, unlike the six above:

- Record `Path: inline (Skill tool unavailable)` — or `Path: inline (availability unknown)` when the
  list could not be read at all.
- Say so explicitly in the report's Limitations section.
- Audit `BUG`, `PERF`, and `UX` with their `references/dimension-map.md` checklists, and state that
  the delegate's deeper analysis was not obtained.

Never guess whether a delegate exists. An unverified assumption that a skill is present produces a
`Path: delegated` row backed by nothing.
