# Dimension Map

One row per dimension: how it is audited, its checklist, and when to skip it. `DEP` lives in
`references/dependency-audit.md` and is not repeated here.

Every dimension returns **finding records** in the shape at the bottom of this file. A dimension that
produced nothing citable is **Not Assessed**, never "no issues found".

## One rule: invoke a delegate only if it changes no tracked file

Three dimensions have a delegate that reports without modifying anything under version control. Six
have a delegate that **writes** — installs hooks, configures CI, generates tests, rewrites docs,
refactors source. Running one of those during an audit would break this skill's read-only contract,
so it is never invoked here; it is named in the plan task that does the work later.

| Dimension | During the audit | Named in the plan task |
|---|---|---|
| `BUG` | **invoke** `code-review` mode `review` — writes `CODE_REVIEW.md`, a declared artifact | — |
| `PERF` | **invoke** `code-review` mode `perf` — writes no file | — |
| `UX` | **invoke** `dont-make-me-think` — **review mode only**, never Redesign Mode | — |
| `CLEAN` | inline checklist | `code-review` mode `clean` |
| `DEAD` | inline checklist | `code-review` mode `cleanup` |
| `TEST` | inline checklist | `test-coverage` |
| `CI` | inline checklist | `devops-pipeline` |
| `SEC` | inline checklist | `security-setup` |
| `DOCS` | inline checklist | `doc-manager` |

Record `Path: delegated` or `Path: inline` per dimension. For the six inline rows, `inline` is the
**expected** path — never report it as a limitation. Only the three invocable dimensions falling back
to inline (Skill tool unavailable) counts as reduced depth and belongs in Limitations.

Either way, the finding records in `MODERNIZATION_REPORT.md` are the artifact this skill owns.

## The nine non-`DEP` dimensions

### `BUG` — Bugs, security holes, quality
- **Audit:** invoke `code-review` mode `review`. It touches no source but writes its own
  `CODE_REVIEW.md` — list that as a declared artifact in the report.
- **Checklist:** null/undefined handling on external input; unchecked error paths and swallowed
  exceptions; off-by-one and boundary conditions; race conditions and unawaited promises; resource
  leaks (files, sockets, connections); injection sinks (SQL, shell, template, path traversal);
  authn/authz gaps on entry points; unvalidated deserialization; hardcoded credentials.
- **Skip:** never.

### `PERF` — Bottlenecks, leaks, algorithmic waste
- **Audit:** invoke `code-review` mode `perf` — reports in-conversation, writes no file.
- **Checklist:** nested loops over unbounded collections; N+1 queries; missing indexes implied
  by query shape; synchronous I/O on a hot path; unbounded caches and growing globals; repeated work
  that could be memoized; large payloads with no pagination; bundle size and unlazy-loaded routes.
- **Skip:** never (mark **Not Assessed** if the user filtered it out).

### `CLEAN` — Readability vs Clean Code standards
- **Audit:** inline only. `code-review` mode `clean` writes `CLEAN_CODE_AUDIT.md`, so it is never run
  here; the plan schedules it as a task.
- **Checklist:** functions over ~50 lines or with > 3 levels of nesting; > 4 parameters;
  boolean flag parameters; names that lie or abbreviate; comments explaining *what* instead of *why*;
  magic numbers; mixed levels of abstraction inside one function; god classes/modules.
- **Skip:** never.

### `DEAD` — Dead code, duplication, slop, weak types
- **Audit:** inline only. `code-review` mode `cleanup` writes code, so it is never run here; the plan
  schedules it as a task.
- **Checklist:** unreferenced exports, files, and routes; commented-out blocks; duplicated
  logic across files (same shape ≥ 3 times); `any`/`interface{}`/`Object` where a real type exists;
  defensive branches that cannot be reached; feature flags for shipped features; TODO/FIXME older
  than a year (`git log -S`); vestigial config for removed services.
- **Skip:** never.

### `UX` — Usability and UI flow
- **Audit:** invoke `dont-make-me-think` **in review mode only**. It also has a Redesign Mode that
  edits UI source files — never enter it; decline any offer to apply fixes.
- **Checklist:** unclear primary action per screen; navigation depth and orientation cues;
  form validation timing and error copy; empty/loading/error states present; touch-target and
  contrast obvious failures; irreversible actions without confirmation; jargon in user-facing copy.
- **Skip:** **no UI detected** (no frontend deps, no `*.tsx/*.jsx/*.vue/*.svelte`, no templates outside
  build output) → **Not Assessed — no UI detected**. Never invent UX findings for a headless service.
- **Degraded:** app not runnable → static-only review from source; state that in the report.

### `TEST` — Untested branches and edge cases
- **Audit:** inline only. `test-coverage` generates test files, so it is never run here; the plan
  schedules it per module.
- **Checklist:** modules with zero test files; coverage report gaps if one exists; error paths
  and edge cases untested; tests asserting implementation instead of behavior; skipped/`.only` tests;
  flaky tests (retries, sleeps, time/network dependence); no test for each past bug fix.
- **Skip:** no test framework **and** no test files → the finding is "no test suite exists", severity
  `Critical`, and it lands in P0.

### `CI` — Pipelines, pre-commit, quality gates
- **Audit:** inline only. `devops-pipeline` writes hooks and workflow files, so it is never run here;
  the plan schedules it.
- **Checklist:** no CI config; CI that does not run tests; no lint/typecheck gate; no
  pre-commit hooks; unpinned action refs; secrets in workflow files; no branch protection implied by
  workflow triggers; build not reproducible (missing lockfile, floating base image).
- **Skip:** never.

### `SEC` — Secrets and dependency vulnerabilities
- **Audit:** inline only. `security-setup` installs hooks and CI, so it is never run here; the plan
  schedules it.
- **Checklist:** committed secrets (`git log -p -S` for key patterns, `.env` in history);
  secrets in config or CI files; overly permissive CORS/CSP; missing security headers; debug mode or
  verbose errors enabled in production config; unencrypted sensitive storage; dependency advisories
  from the `DEP` probes (cross-reference, do not duplicate the row — link the `F-DEP-*` ID).
- **Skip:** never.

### `DOCS` — Docs drifted from code
- **Audit:** inline only. `doc-manager` rewrites docs, so it is never run here; the plan schedules it.
- **Checklist:** README setup steps that fail against the current manifest; documented commands
  that no longer exist; API docs referencing removed endpoints; architecture docs describing removed
  components; missing CONTRIBUTING/env-var documentation; stale version numbers and badges.
- **Skip:** never.

## Severity rubric (all dimensions)

| Severity | Bar |
|---|---|
| `Critical` | exploitable, data-losing, or blocks every other improvement (EOL runtime, no test suite, broken build, committed secret) |
| `High` | user-visible defect, security weakness, or a blocker for a phase milestone |
| `Medium` | real quality or maintainability cost; deferrable one phase without new risk |
| `Low` | cosmetic, stylistic, or nice-to-have |

Severity is argued from evidence, not vibes. If two dimensions disagree on the same line, take the
higher severity and list both dimensions on the one finding.

## Finding record shape

```markdown
| ID | Dim | Severity | Evidence | Problem | Fix direction | Effort |
|---|---|---|---|---|---|---|
| F-BUG-004 | BUG | Critical | `src/api/user.ts:118` | Raw string interpolation into SQL query | Parameterize via the driver's prepared statement API | S |
| F-TEST-001 | TEST | Critical | repo-wide | No test framework configured; 0 test files | Add the stack's standard runner and one smoke test | M |
```

Rules:
- `Evidence` is `path:line`, or `path` plus a named symbol, or `repo-wide` **only** for
  absence-of-thing findings. Anything else is dropped.
- `Effort` is `S` (< 1 day), `M` (1–3 days), `L` (> 3 days — must be split into tasks in the plan).
- IDs are `F-<DIM>-<NNN>` zero-padded to three digits, numbered per dimension, stable once assigned; the plan references them.
