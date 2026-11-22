
# Code Review

Review code for quality issues, code smells, and pragmatic programming violations.

## Quick Start

First, record the Review Binding (head, base and working tree) and local tracking observations
without claiming remote freshness. Review analysis is source-read-only: do not fetch, stash, pull, rebase,
checkout/switch, create or delete branches/worktrees, or mutate the index, refs, stash, branch,
or any other worktree path. The only permitted file write is the named `CODE_REVIEW.md` report
artifact. Then complete the Environment Check to pick a mode (PR/diff vs full audit). Next, run
the selected mode's process from Mode Selection against the Review Checklist. Finally, emit the
Output Format report and verify Acceptance Criteria.

## Overview

The skill orchestrates parallel reviewer subagents over batched files, then runs a validator pass. Each phase has explicit steps below. Read only the section you need; the rest is reference material.

## Analysis Boundary (mandatory)

Review mode never performs repository sync or source mutation during analysis. If a separately
approved mutation is requested, hand it off to a workflow with its own freshness check and
sync/safety gates (cleanup mode stops on a dirty tree); this mode does not apply fixes.

## Review Binding (head and base)

A review counts only for the commit it reviewed: a pass on an out-of-date commit means nothing.
This section is the single home of the review's binding record. Other sections and later steps
use these names instead of re-deriving them.

**Record it first**, before any other analysis, from local data only. Never run `git fetch`,
`git pull`, `git remote update` or `gh pr checkout` to get a base:

```bash
head_sha="$(git rev-parse HEAD)"
head_branch="$(git rev-parse --abbrev-ref HEAD)"   # prints HEAD when detached
git status --porcelain=v1 --untracked-files=all -- . ':(exclude)CODE_REVIEW.md'   # empty: clean
# Diff or PR review only (a full audit has base_ref none and skips these three):
base_sha="$(git rev-parse --verify --quiet "${base_ref}^{commit}")"
base_full="$(git rev-parse --symbolic-full-name "$base_ref")"   # empty for a raw SHA
merge_base="$(git merge-base "$base_sha" "$head_sha")"           # where the change forked
```

| Name | Value |
|------|-------|
| `head_sha` | The full SHA of `HEAD` (40 hex characters, 64 in a SHA-256 repo). Never abbreviated in the report. |
| `base_ref` | The ref the diff is compared against, as the user named it (`main`, `origin/main`, a SHA). For a PR, its base branch's local remote-tracking ref `origin/<base branch>`, else the local branch of that name. `none` for a full audit with no base. |
| `base_sha` | The full SHA `base_ref` resolved to when recorded. |
| `base_source` | From `base_full`: `refs/remotes/…` is `local remote-tracking ref, not fetched (as of the last fetch)`; `refs/heads/…` is `local branch, not fetched`; `refs/tags/…` is `local tag, not fetched`; any other ref is `local ref <base_full>, not fetched`; empty is `commit`. |
| `merge_base` | The full SHA of `git merge-base <base_sha> <head_sha>`: the commit the change started from. |
| `working_tree` | `clean`, or `dirty — N uncommitted paths, not in Head` when `git status` printed N lines. The review's own `CODE_REVIEW.md` is not counted. |

- `<merge_base>` in every command in this file means `$merge_base`, so the diff matches the record
  even if the ref moves during the review. **The change** is `git diff <merge_base>..HEAD`.
- Never diff against the base tip (`<base_sha>..HEAD`): once the base has moved past the fork,
  that diff shows the base's newer commits reversed, as if the change had removed them.
- In a diff or PR review, a `base_ref` that does not resolve locally stops the review: ask for a
  base that exists locally. Never fetch one. An empty `merge_base` (unrelated histories, or a
  shallow clone without the fork point) also stops it: ask for a base that shares history, and
  never fetch or deepen. A full audit records no `base_sha`, `base_source` or `merge_base`.
- A local base can lag its remote. The report names `base_source` and never claims the base is the
  remote's current tip.
- A dirty tree means some reviewed lines are not in `head_sha`. List those paths in the report.

**Report header.** `CODE_REVIEW.md` carries these three lines (Output Format):

```markdown
**Head**: `<head_sha>` (`<head_branch>`)
**Base**: `<base_ref>` @ `<base_sha>` — <base_source>; merge base `<merge_base>`
**Working tree**: <working_tree>
```

A full audit writes `**Base**: none (full audit)`.

**Stale check.** Run it whenever an existing `CODE_REVIEW.md` is used (its verdict or counts
cited, its findings acted on, the report handed on) and whenever it is validated (the `reviewer`
agent's first phase):

```bash
report_head="$(sed -n 's/^\*\*Head\*\*: `\([0-9a-f]\{40,64\}\)`.*/\1/p' CODE_REVIEW.md | head -n 1)"
if [ -n "$report_head" ] && [ "$report_head" = "$(git rev-parse HEAD)" ]; then echo current; else echo stale; fi
```

- `current`: the report describes this `HEAD`.
- `stale`: its Head differs from the current `HEAD`, or it has no full Head line (a report written
  before this binding existed). Print `⚠ CODE_REVIEW.md is stale: reviewed <report_head, first 12
  characters, or "unknown"> but HEAD is <HEAD, first 12 characters>`. Never count its verdict or
  an all-zero summary as a pass for `HEAD`. Its findings are history only; re-run review mode on
  `HEAD` for a verdict.
- A base that now resolves to another SHA does not make the report stale, because the Head is what
  was reviewed. Say `base moved` beside its verdict.

## Finding Origin (introduced or pre-existing)

The author of a change answers for the lines the change touched, not for old bugs next to them.
Every finding carries one origin tag, decided by its cited lines:

- **introduced**: at least one line it cites is in the change. That is a line added or modified in
  `git diff -U0 <merge_base>..HEAD` (the `+` side of a hunk), a line that diff deletes (a removed
  test, assertion or gate), or, on a dirty tree, an uncommitted line or a line of an untracked file.
- **pre-existing**: every line it cites is unchanged since `merge_base`. This includes context
  lines next to a hunk. A pre-existing finding **never blocks a merge**, whatever its severity.

Rules:

- When the change is what makes an unchanged line wrong (a changed signature that breaks an
  unchanged caller), cite the changed line as well. The finding is then introduced.
- Category 5 (Verification Integrity) findings come from the diff, so they are always introduced.
- A full audit has no change: every finding is pre-existing and none blocks a merge.
- Decide the tag from the diff, never from `git blame` or a guess about who wrote the line.

## Environment Check

Before proceeding with code review:

1. **Verify Agent tool availability**: Check if `/Agent` subagent system is available
2. **Codebase scope**: Determine if full audit or PR/diff review
3. **Context budget**: Estimate file count and total lines to review, then pick a mode from Mode Selection below

## Subagent Architecture

### Pattern: B (Parallel Workers) + C (Review Loop)

For full codebase audits and large PRs, this skill uses a parallel-worker + review-loop pattern: the main orchestrator batches files across parallel `file-reviewer` agents, a `report-assembler` merges and deduplicates their findings, and a `reviewer` agent validates the final report with fresh eyes.

Full orchestration diagram, per-agent responsibilities, graceful degradation when the Agent tool is unavailable, and risk mitigations: `references/subagent-architecture.md`.

## Mode Selection

**Mode 1: Small PR/Diff (Fast Path - Inline)**
- Changed files: <50
- Total lines changed: <5000
- Process: run the Review Checklist inline over the changed lines; no subagents
- Git commands:
  ```bash
  git diff --name-only <merge_base>..HEAD
  git diff <merge_base>..HEAD
  ```
- Scan focus: only changed lines and their immediate context (a finding on a context line is pre-existing)
- Output: CODE_REVIEW.md in seconds

**Mode 2: Medium Audit (Batched with Subagents)**
- Files: 50-200
- Total lines: 5K-50K
- Process:
  1. Batch files into groups of 5-10
  2. Launch parallel file-reviewer agents
  3. Collect JSON outputs
  4. Merge with report-assembler
  5. Validate with reviewer
- Scan focus: all source files, prioritizing entry points (main, index, app) and core business logic
- Output: CODE_REVIEW.md with comprehensive findings

**Mode 3: Large Audit (Sampled with Subagents)**
- Files: >200
- Total lines: >50K
- Process:
  1. Identify and scan entry points (main, index, app files)
  2. Scan business logic hotspots — most frequently modified files:
     ```bash
     git log --format='%H' | head -100 | xargs -I{} git diff-tree --no-commit-id --name-only -r {} | sort | uniq -c | sort -rn
     ```
  3. Sample distributed files across codebase
  4. Use parallel batching as in Mode 2
  5. Full validation pass
- Output: CODE_REVIEW.md with sampled findings + note about sampling strategy

If the Agent tool is unavailable, run the Mode 2/3 batches inline and sequentially, and note in the report that the validation pass was skipped.

In every mode, a diff or PR review also runs checklist category 5 (Verification Integrity) once, inline, over the whole diff, before any batching. In Mode 2/3 the orchestrator adds its category-5 findings and the `## Verification Changes` table to the report after the report-assembler merge and before the reviewer validation pass. A full audit with no base skips it.

In Mode 2/3 the orchestrator passes `merge_base` (or `null` for a full audit) to every `file-reviewer`, which tags each finding's origin (Finding Origin), and the binding record to the `report-assembler`.

## Review Checklist

Findings are grouped into the five categories below and classified by severity:

### Severity Levels

| Level | Description | Action |
|-------|-------------|--------|
| **Critical** | Security risks, bugs, data loss potential, weakened verification (category 5) | Must fix before merge (introduced findings only) |
| **Major** | Code smells, maintainability blockers | Should fix soon |
| **Minor** | Style, minor improvements | Nice to have |
| **Info** | Suggestions, alternatives | Optional |

Severity and origin are separate: a pre-existing finding keeps its severity but never blocks a
merge (Finding Origin). Only an introduced Critical finding is merge-blocking.

### 1. Code Smells

Read `references/code-smells.md` when a code smell is identified that requires the full catalog for classification.

**Bloaters** - Code that grows too large
- Long Method (>20 lines)
- Large Class (>200 lines)
- Long Parameter List (>3 params)
- Primitive Obsession

**Object-Orientation Abusers**
- Switch Statements (replace with polymorphism)
- Refused Bequest
- Alternative Classes with Different Interfaces

**Change Preventers**
- Divergent Change (one class, many reasons to change)
- Shotgun Surgery (one change, many classes affected)
- Parallel Inheritance Hierarchies

**Dispensables**
- Dead Code
- Duplicate Code
- Lazy Class
- Speculative Generality

**Couplers**
- Feature Envy
- Inappropriate Intimacy
- Message Chains
- Middle Man

### 2. Pragmatic Programmer Principles

**DRY (Don't Repeat Yourself)**
- Duplicated logic or knowledge
- Copy-paste code
- Repeated magic values

**Orthogonality**
- Components that should be independent but aren't
- Changes rippling across unrelated modules

**Reversibility**
- Hard-coded decisions that should be configurable
- Vendor lock-in without abstraction

**Tracer Bullets**
- Is the code testable end-to-end?
- Are there integration points?

**Good Enough Software**
- Over-engineering for unlikely scenarios
- Premature optimization

**Broken Windows**
- Commented-out code
- TODO/FIXME without tickets
- Inconsistent formatting

### 3. Security & Safety

- Input validation
- SQL injection risks
- XSS vulnerabilities
- Hardcoded secrets
- Unsafe deserialization

### 4. Maintainability

- Unclear naming
- Missing or outdated comments
- Complex conditionals
- Deep nesting (>3 levels)
- Missing error handling

### 5. Verification Integrity (diff only)

If a change can modify the check that judges it, the check is broken. This category looks for a diff that weakens its own verification.

**When it runs.** Only when the diff touches at least one of these. Check the paths with `git diff --name-only <merge_base>..HEAD`; the Thresholds trigger needs the diff content (`git diff <merge_base>..HEAD`). Otherwise skip it and write `Verification integrity: skipped (no test, test or lint config, CI, hook or threshold change)` under the report's Summary.

- **Tests:** files under `test/`, `tests/`, `__tests__/` or `spec/`, or named `test_*`, `*_test.*`, `*.test.*`, `*.spec.*`, `*Test.*`, `*Tests.*`, plus `conftest.py`, fixtures and snapshots
- **Test or lint config:** `pytest.ini`, `tox.ini`, `.coveragerc`, `jest.config.*`, `vitest.config.*`, `playwright.config.*`, `cypress.config.*`, `.mocharc*`, `karma.conf.*`, `phpunit.xml*`, `.eslintrc*`, `eslint.config.*`, `ruff.toml`, `.ruff.toml`, `.flake8`, `.pylintrc`, `mypy.ini`, `.golangci.*`, `.rubocop.yml`, `.swiftlint.yml`, `tsconfig*.json`; in `pyproject.toml`, `setup.cfg` or `package.json`, only a changed hunk in a test, lint, type-check or coverage section (`[tool.pytest…]`, `[tool.coverage…]`, `[tool.ruff…]`, `[tool.mypy]`, `jest`, `eslintConfig`, a `test` or `lint` script)
- **CI workflows:** `.github/workflows/`, `.gitlab-ci.yml`, `.circleci/`, `azure-pipelines.yml`, `Jenkinsfile`, `.buildkite/`
- **Hook config:** `.pre-commit-config.yaml`, `.husky/`, `lefthook.yml`, `.lefthook.yml`, `.githooks/`, lint-staged config
- **Thresholds:** a changed line in any file that sets a coverage floor (`fail_under`, `--cov-fail-under`, `coverageThreshold`), a lint limit (`--max-warnings`, `max-complexity`) or a test timeout or retry count, or that adds a lint or type-check suppression (`noqa`, `eslint-disable`, `@ts-ignore`, `type: ignore`) or a hook bypass (`--no-verify`, `SKIP=`, `HUSKY=0`)

**What it flags.** Each signal below is a **Critical** finding (category `Verification Integrity`) unless the change states why:

| Signal | Examples |
|--------|----------|
| Deleted test | a test function, case, file or parametrize row removed |
| Skipped or narrowed test | `skip`, `skipif`, `xfail`, `it.skip`, `xit`, `describe.skip`, `t.Skip()`, `@Disabled`, `@Ignore`, `#[ignore]`; `.only`, `fit`, `fdescribe` (the rest stop running); a path added to `testPathIgnorePatterns`, `--ignore`, `--deselect` or `-k "not …"` |
| Weakened or removed assertion | an `assert` or `expect` removed; an exact match swapped for a looser one (`toEqual` → `toBeDefined`, `assertEqual` → `assertIsNotNone`, a wider tolerance); an expected value rewritten to match new output; an assertion error caught and ignored; snapshots regenerated wholesale |
| Added sleep or retry | `sleep`, `time.sleep`, `setTimeout` or `waitForTimeout` in a test; `@flaky`, `--reruns`, `jest.retryTimes`, `retries:` in test config, a retry loop around a test command; a raised test timeout |
| Lowered threshold | a coverage floor reduced; `--max-warnings` raised; a rule moved from `error` to `warn` or `off`, or added to an ignore list; `# noqa`, `eslint-disable`, `@ts-ignore` or `type: ignore` added; type-check strictness reduced |
| Removed hook or gate | a pre-commit hook, husky or lefthook hook removed; a CI job or step removed or neutralized (`if: false`, `continue-on-error: true`, `allow_failure: true`, `\|\| true`); `--no-verify`, `SKIP=` or `HUSKY=0` added |

**The change states why** only when the reason is in the change itself: a commit message in `<merge_base>..HEAD`, the PR description, or a comment on or beside the changed line. It must explain this item, for example "the export feature is removed" or "upstream flake, tracked in #123". "Fix tests" or "cleanup" is not a reason. With a stated reason, the item is listed with the reason quoted, at **Info**, so a person can judge it.

**A test deleted together with the code it covered** is listed but not flagged: no severity, no finding. It qualifies when the diff also deletes every function, class or module the test exercised, so `git grep` at `HEAD` finds no definition of it. This keeps cleanup mode's dead-code removals reviewable. A deleted test whose subject still exists at `HEAD` is a Deleted test.

## Output Format

Generate `CODE_REVIEW.md`:

```markdown
# Code Review Report

**Date**: YYYY-MM-DD
**Scope**: [PR #123 | Full Audit]
**Head**: `<head_sha>` (`<head_branch>`)
**Base**: [`<base_ref>` @ `<base_sha>` — <base_source>; merge base `<merge_base>` | none (full audit)]
**Working tree**: [clean | dirty — N uncommitted paths, not in Head]
**Mode**: [1 — inline | 2 — batched | 3 — sampled]
**Files Reviewed**: N

## Summary

| Severity | Count |
|----------|-------|
| Critical | X |
| Major    | X |
| Minor    | X |
| Info     | X |

**Origin**: X introduced · Y pre-existing
**Merge-blocking**: N — introduced Critical findings only; pre-existing findings never block

## Critical Issues

### [Category]: Issue Title
**File**: `path/to/file.ts:42`
**Origin**: introduced
**Smell**: [Code smell name]

Description of the issue.

**Before**:
```language
// problematic code
```

**Suggested Fix**:
```language
// improved code
```

## Major Issues
...

## Minor Issues
...

## Info
...

## Pre-existing Issues

Not introduced by this change and not merge-blocking (Finding Origin). Ordered by severity; same
finding format, with `**Origin**: pre-existing` and the severity in the title.

### [Critical] [Category]: Issue Title
**File**: `path/to/other.ts:10`
**Origin**: pre-existing
...

## Verification Changes

| File | Signal | Status | Reason stated |
|------|--------|--------|---------------|
| `tests/test_api.py:88` | Skipped or narrowed test | Critical | none |
| `.github/workflows/ci.yml:31` | Lowered threshold | Info | "coverage tool changed, floor rebased" (commit a1b2c3d) |
| `tests/test_legacy_export.py` | Deleted test | Listed, covered code deleted | n/a |

## Recommendations

1. Priority fixes
2. Refactoring suggestions
3. Architecture improvements
```

- The Summary keeps its four severity rows; each Count covers both origins. The `**Origin**` and
  `**Merge-blocking**` lines below the table split them.
- `## Critical Issues`, `## Major Issues`, `## Minor Issues` and `## Info` hold introduced findings
  only. Every pre-existing finding goes under `## Pre-existing Issues`, whatever its severity.
- A full audit has no introduced findings: it omits the four severity sections, writes
  `**Merge-blocking**: 0 — full audit, no change` and lists every finding under Pre-existing Issues.

## Expected Output

A `CODE_REVIEW.md` file with findings grouped by severity. Example:

```markdown
# Code Review Report

**Date**: 2024-01-15
**Scope**: PR #42 — auth module refactor
**Head**: `9f2c4e1a7b3d5f6e8c0a1b2c3d4e5f6a7b8c9d0e` (`feat/auth-refactor`)
**Base**: `origin/main` @ `3e1d7c9b5a2f4e6d8c0b1a3f5e7d9c2b4a6f8e0d` — local remote-tracking ref, not fetched (as of the last fetch); merge base `7a4b2c8d1e3f5a6b9c0d2e4f6a8b1c3d5e7f9a0b`
**Working tree**: clean
**Mode**: 1 — inline
**Files Reviewed**: 8

## Summary

| Severity | Count |
|----------|-------|
| Critical | 1     |
| Major    | 3     |
| Minor    | 5     |
| Info     | 2     |

**Origin**: 9 introduced · 2 pre-existing
**Merge-blocking**: 1 — introduced Critical findings only; pre-existing findings never block

## Critical Issues

### [Security]: Hardcoded API Secret
**File**: `src/auth/client.ts:17`
**Origin**: introduced
**Smell**: Hardcoded secrets

API key is embedded directly in source code and will be committed to version control.

**Before**:
```typescript
const API_KEY = "sk-prod-abc123xyz";
```

**Suggested Fix**:
```typescript
const API_KEY = process.env.API_KEY;
if (!API_KEY) throw new Error("API_KEY env var is required");
```

## Pre-existing Issues

### [Major] [Code Smell]: Long Method in `refreshToken`
**File**: `src/auth/session.ts:88`
**Origin**: pre-existing
**Smell**: Long Method

The 64-line method sits beside the changed hunk but this change did not touch it.

## Recommendations

1. Move all secrets to environment variables immediately
2. Add `.env` to `.gitignore` and document required vars in README
3. Consider extracting the 240-line `UserService` class into smaller focused services
```

## Acceptance Criteria

A run passes when **all** of the following are true:

- [ ] `CODE_REVIEW.md` exists in the repo root with `# Code Review Report` as the first heading.
- [ ] Report includes a `## Summary` table with rows for Critical, Major, Minor, and Info severities.
- [ ] Every finding carries `**Origin**: introduced` or `**Origin**: pre-existing`, decided by whether a cited line is in `git diff <merge_base>..HEAD` (Finding Origin). Pre-existing findings are listed only under `## Pre-existing Issues` and never counted in `**Merge-blocking**`.
- [ ] Every reported finding cites a `path/to/file.ext:line` reference and a code smell or category label.
- [ ] Critical findings include both a "Before" and "Suggested Fix" code block when a code change is proposed.
- [ ] Mode used (Mode 1/2/3) is recorded in the report header along with the file count.
- [ ] The header names the full `head_sha`, the base as `base_ref` @ full `base_sha` with its `base_source` and full `merge_base` (or `none (full audit)`), and the working-tree state (Review Binding). No fetch ran.
- [ ] An existing `CODE_REVIEW.md` that was used or validated passed the stale check first; a stale one was reported as stale and its verdict not counted.
- [ ] When the diff touches a test, test or lint config, CI workflow, hook config or threshold, the report has a `## Verification Changes` table listing every signal found, each Critical, Info with its quoted reason, or listed with its covered code deleted. Otherwise the report says the check was skipped.
- [ ] No merge-conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) are silently dropped — they appear as Critical findings if present in the source.

## Edge Cases

- **Empty or whitespace-only diff**: Report scope as zero files reviewed; skip review and inform the user.
- **Binary files or generated code**: Skip minified/generated files (e.g., `dist/`, `*.min.js`, `package-lock.json`) and note them as excluded in the report header.
- **Single-language vs. polyglot repos**: Apply language-appropriate checks for each file; don't flag Python idioms as issues in JS files.
- **No issues found**: Produce a report with all-zero severity counts and a brief "LGTM" summary — don't fabricate findings.
- **Files exceeding context limits**: Fall back to mode 3 (sampling) and note which files were sampled vs. fully reviewed.
- **Merge conflict markers**: Flag any `<<<<<<<` / `=======` / `>>>>>>>` as a Critical issue — never silently ignore them.

## Step Completion Reports

After completing each major step, output a status report in this format:

```
◆ [Step Name] ([step N of M] — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          √ pass (note if relevant)
  [Check 3]:          × fail — [reason]
  [Check 4]:          √ pass
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Adapt the check names to match what the step actually validates. Use `√` for pass, `×` for fail, and `—` to add brief context. The "Criteria" line summarizes how many acceptance criteria were met. The "Result" line gives the overall verdict.

### Skill-specific checks per phase

**Phase: Scope Assessment** — checks: `Review binding` (head, base, working tree recorded), `Scope assessment`, `File count estimated`

**Phase: Review Execution** — checks: `Code smell detection`, `Security scan`, `Verification integrity` (or `skipped` when no trigger path changed)

**Phase: Report Generation** — checks: `Report generation`, `Severity classification`, `Origin tagged` (every finding introduced or pre-existing)

**Phase: Validation Pass** — checks: `Head current` (stale check), `Validation pass`, `False positive check`

## Resources

- [references/code-smells.md](references/code-smells.md) - Complete catalog of code smells with examples
- [references/subagent-architecture.md](references/subagent-architecture.md) - Orchestration diagram, agent responsibilities, graceful degradation, and risk mitigation
