# Scope and branch selection

Resolve every row below **before Phase 0**. Each is a real branch in the workflow, not a preference —
it changes which probes run, how they run, or whether a dimension is obtainable at all. Record the
resolved value for each; the report's Limitations section lists every branch that degraded the run.

| Branch | Detect | Effect |
|---|---|---|
| **Target** | `$ARGUMENTS` path, else current working directory | Repo root for all probes and both output files |
| **Repo size** | count *source* files only — `git ls-files` filtered to source extensions, or `find` with the standard excludes (`node_modules`, `dist`, `build`, `vendor`, `target`, `.git`) when the target is not a git repo | < 50 source files → run dimensions inline; ≥ 50 → parallel `dimension-auditor` subagents |
| **Agent tool** | availability in this session | Unavailable → run every dimension inline, sequentially, and disclose reduced depth in the report |
| **Bash / shell** | can you run commands at all? | Unavailable (e.g. Claude.ai) → **no baseline is obtainable**: every Phase 0 probe and `dep_scan.sh` is a shell command. Record the whole baseline **Not Assessed — no shell**, audit only what static reading supports (`CLEAN`, `DEAD`, `UX`, `DOCS`, and manifest-declared versions read from the file), and state prominently that dependency *currency* and all runtime verification were impossible. Do not fabricate a verdict. |
| **Skill tool** | does the delegate appear by name in this session's skill list? | Present → invocable. Absent, or the list cannot be enumerated → inline, recorded as `Path: inline (availability unknown)`. Never guess availability |
| **UI present** | frontend deps in manifests, or `*.tsx/*.jsx/*.vue/*.svelte/*.html` outside build output, or template dirs | Absent → UI/UX dimensions are **Not Assessed — no UI detected**; never invent UX findings |
| **App runnable** | a start/dev script that a probe confirms exists | Not runnable → UX review is static-only; state that limitation in the report |
| **Ecosystems** | manifest files present (see `references/dependency-audit.md`) | Drives which dependency probes run; each **fail-soft** |
| **Dimension filter** | user names specific areas ("just deps and tests") | Audit only those; mark the rest **Not Assessed — out of requested scope** |

## Resolution order

1. **Target** first — every other detection runs relative to it.
2. **Bash / shell** next. It is the hardest gate: without it, the repo-size count, the ecosystem
   probes, and the entire baseline collapse to static reading. Resolve it before spending effort on
   branches it invalidates.
3. **Repo size** and **Agent tool** together — they jointly decide inline vs. parallel subagents.
   Either one unavailable or below threshold forces inline.
4. **Skill tool**, **UI present**, **App runnable**, **Ecosystems** — these set per-dimension paths.
5. **Dimension filter** last, applied over the worklist the previous rows produced.

## Recording the resolution

State the outcome of all nine rows in Phase 1's output and carry them into the report. Two of them
must be called out prominently rather than buried, because they change what the report can claim:

- **No Bash** → the report leads with "baseline Not Assessed — no shell" and every currency claim is
  manifest-declared only.
- **Agent tool unavailable** → the report's Limitations section states that dimensions ran inline
  and sequentially, at reduced depth.

A branch you could not resolve is itself recorded as **Not Assessed** with the reason. Never assume
the permissive side of a branch you did not check.
