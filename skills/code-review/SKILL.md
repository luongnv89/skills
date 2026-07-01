---
name: code-review
description: "Review code changes for bugs, security vulnerabilities, and code quality issues — producing prioritized findings with specific fix suggestions. Don't use for performance tuning, writing new features from scratch, or generating test cases."
license: MIT
effort: medium
metadata:
  version: 1.2.0
  author: Luong NGUYEN <luongnv89@gmail.com>
  architecture: "subagent (Pattern B+C: Parallel Workers + Review Loop)"
---

# Code Review

Review code for quality issues, code smells, and pragmatic programming violations.

## When to Use

Use this skill when the user asks for a code review, PR review, audit, security check, or "review my changes". Trigger on phrases like "review this code", "audit this repo", "check this PR for issues", or "find bugs in these files". Do not trigger for performance profiling, writing new features from scratch, or test-case generation.

## Quick Start

First, run the Repo Sync workflow below. Then complete the Environment Check to pick a mode (PR/diff vs full audit). Next, follow the Instructions phases (checklist scan -> findings synthesis -> validation). Finally, emit the Output Format report and verify Acceptance Criteria.

## Overview

The skill orchestrates parallel reviewer subagents over batched files, then runs a validator pass. Each phase has explicit steps below. Read only the section you need; the rest is reference material.

## Repo Sync Before Edits (mandatory)

Before creating/updating/deleting files in an existing repository, sync the current branch with remote:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If the working tree is not clean, stash first, sync, then restore:

```bash
git stash push -u -m "pre-sync"
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin && git pull --rebase origin "$branch"
git stash pop
```

If `origin` is missing, pull is unavailable, or rebase/stash conflicts occur, stop and ask the user before continuing.

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
- Process: Run complete review inline in SKILL.md; no subagents needed
- Git commands:
  ```bash
  git diff --name-only <base>..HEAD
  git diff <base>..HEAD
  ```
- Scan focus: only changed lines and their immediate context
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

If the Agent tool is unavailable, degrade gracefully per `references/subagent-architecture.md`: run sequential inline review instead of Mode 2/3 subagent batching.

## Review Checklist

Findings are grouped into the four categories below and classified by severity:

### Severity Levels

| Level | Description | Action |
|-------|-------------|--------|
| **Critical** | Security risks, bugs, data loss potential | Must fix before merge |
| **Major** | Code smells, maintainability blockers | Should fix soon |
| **Minor** | Style, minor improvements | Nice to have |
| **Info** | Suggestions, alternatives | Optional |

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

## Output Format

Generate `CODE_REVIEW.md`:

```markdown
# Code Review Report

**Date**: YYYY-MM-DD
**Scope**: [PR #123 | Full Audit]
**Files Reviewed**: N

## Summary

| Severity | Count |
|----------|-------|
| Critical | X |
| Major    | X |
| Minor    | X |
| Info     | X |

## Critical Issues

### [Category]: Issue Title
**File**: `path/to/file.ts:42`
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

## Recommendations

1. Priority fixes
2. Refactoring suggestions
3. Architecture improvements
```

## Expected Output

A `CODE_REVIEW.md` file with findings grouped by severity. Example:

```markdown
# Code Review Report

**Date**: 2024-01-15
**Scope**: PR #42 — auth module refactor
**Files Reviewed**: 8

## Summary

| Severity | Count |
|----------|-------|
| Critical | 1     |
| Major    | 3     |
| Minor    | 5     |
| Info     | 2     |

## Critical Issues

### [Security]: Hardcoded API Secret
**File**: `src/auth/client.ts:17`
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

## Recommendations

1. Move all secrets to environment variables immediately
2. Add `.env` to `.gitignore` and document required vars in README
3. Consider extracting the 240-line `UserService` class into smaller focused services
```

## Acceptance Criteria

A run passes when **all** of the following are true:

- [ ] `CODE_REVIEW.md` exists in the repo root with `# Code Review Report` as the first heading.
- [ ] Report includes a `## Summary` table with rows for Critical, Major, Minor, and Info severities.
- [ ] Every reported finding cites a `path/to/file.ext:line` reference and a code smell or category label.
- [ ] Critical findings include both a "Before" and "Suggested Fix" code block when a code change is proposed.
- [ ] Mode used (Mode 1/2/3) is recorded in the report header along with the file count.
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

**Phase: Scope Assessment** — checks: `Scope assessment`, `File count estimated`

**Phase: Review Execution** — checks: `Code smell detection`, `Security scan`

**Phase: Report Generation** — checks: `Report generation`, `Severity classification`

**Phase: Validation Pass** — checks: `Validation pass`, `False positive check`

## Resources

- [references/code-smells.md](references/code-smells.md) - Complete catalog of code smells with examples
- [references/subagent-architecture.md](references/subagent-architecture.md) - Orchestration diagram, agent responsibilities, graceful degradation, and risk mitigation
