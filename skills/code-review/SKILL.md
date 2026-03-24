---
name: code-review
description: Perform code reviews following best practices from Code Smells and The Pragmatic Programmer. Use when asked to "review this code", "check for code smells", "review my PR", "audit the codebase", or need quality feedback on code changes. Supports both full codebase audits and focused PR/diff reviews. Outputs structured markdown reports grouped by severity.
effort: medium
license: MIT
metadata:
  version: 1.1.0
  creator: Luong NGUYEN <luongnv89@gmail.com>
  architecture: subagent (Pattern B+C: Parallel Workers + Review Loop)
---

# Code Review

Review code for quality issues, code smells, and pragmatic programming violations.

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
3. **Context budget**: Estimate file count and total lines to review
   - Small PR/diff: <50 files, <5000 lines → run inline (fast path)
   - Medium audit: 50-200 files, 5K-50K lines → use batch processing
   - Large audit: >200 files, >50K lines → sample entry points and hot paths

## Subagent Architecture

### Pattern: B (Parallel Workers) + C (Review Loop)

For full codebase audits and large PRs, use parallel subagent architecture:

```
┌─────────────────────────────────┐
│  Main SKILL (Orchestrator)      │
│  - Parse scope (PR/audit)       │
│  - Batch files into groups      │
│  - Check Agent availability     │
└──────────────┬──────────────────┘
               │
       ┌───────┴───────┬───────────┬─────────────┐
       │               │           │             │
       v               v           v             v
   ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
   │ Reviewer 1 │ │ Reviewer 2 │ │ Reviewer 3 │ │ Reviewer N │
   │   Batch 1  │ │   Batch 2  │ │   Batch 3  │ │  Batch N   │
   │   5-10     │ │   5-10     │ │   5-10     │ │   5-10     │
   │   files    │ │   files    │ │   files    │ │   files    │
   │ (parallel) │ │ (parallel) │ │ (parallel) │ │ (parallel) │
   └─────┬──────┘ └─────┬──────┘ └─────┬──────┘ └─────┬──────┘
         │              │              │              │
         │              └──────────────┴──────────────┘
         │                             │
         └─────────────────────────────┘
                     │
        ┌────────────v────────────────┐
        │  Report Assembler           │
        │  - Merge all findings       │
        │  - Deduplicate issues       │
        │  - Rank by severity         │
        │  - Generate CODE_REVIEW.md  │
        └────────────┬────────────────┘
                     │
             ┌───────v────────┐
             │  Reviewer      │
             │  Validator     │
             │  - Fresh eyes  │
             │  - Verify      │
             │  - Completeness│
             └────────────────┘
```

#### Agent Files

- **agents/file-reviewer.md** — Review a batch of 5-10 files against the full checklist
  - Returns structured JSON with findings, severity levels, and fix suggestions
  - Run in parallel on multiple batches
  - Input: file list, checklist config, language context
  - Output: JSON with findings array

- **agents/report-assembler.md** — Merge all batch results into one report
  - Deduplicates findings by (file, line, smell)
  - Ranks by severity (critical → major → minor → info)
  - Identifies cross-file patterns (duplicate code, shotgun surgery)
  - Generates final CODE_REVIEW.md
  - Input: array of JSON outputs from file-reviewer
  - Output: Markdown report + validation JSON

- **agents/reviewer.md** — Fresh-context validation pass
  - Verifies accuracy of all findings
  - Catches false positives and severity miscategorizations
  - Identifies missed issues
  - Returns validation report with corrections
  - Input: CODE_REVIEW.md + original source files
  - Output: Validation JSON + updated CODE_REVIEW.md if corrections needed

### Mode Selection & Degradation

**Mode 1: Small PR/Diff (Fast Path - Inline)**
- Changed files: <50
- Total lines changed: <5000
- Process: Run complete review inline in SKILL.md
- No subagents needed
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
- Output: CODE_REVIEW.md with comprehensive findings

**Mode 3: Large Audit (Sampled with Subagents)**
- Files: >200
- Total lines: >50K
- Process:
  1. Identify and scan entry points (main, index, app files)
  2. Scan business logic hotspots (most frequently modified)
  3. Sample distributed files across codebase
  4. Use parallel batching as in Mode 2
  5. Full validation pass
- Output: CODE_REVIEW.md with sampled findings + note about sampling strategy

### Graceful Degradation

If Agent tool unavailable:
- Fall back to inline execution in main SKILL.md
- Use sequential file processing instead of parallel batches
- Return CODE_REVIEW.md without validation pass
- Log message: "Subagent architecture unavailable; running inline review"

### Risk Mitigation

**Missed cross-file smells**: Report-assembler cross-file analysis partially mitigates by identifying:
- Duplicate code patterns
- Shotgun surgery risks
- Architectural coupling

**Context overflow**: Batching 5-10 files per agent keeps context manageable while maintaining review quality.

**False positives**: Reviewer agent catches most false positives through fresh-context validation before final report.

## Review Modes

### Mode 1: PR/Diff Review

```bash
# Get changed files
git diff --name-only <base>..HEAD
git diff <base>..HEAD
```

Focus only on changed lines and their immediate context.

### Mode 2: Full Codebase Audit

Scan all source files, prioritizing:
1. Entry points (main, index, app)
2. Core business logic
3. Frequently modified files (`git log --format='%H' | head -100 | xargs -I{} git diff-tree --no-commit-id --name-only -r {} | sort | uniq -c | sort -rn`)

## Review Checklist

### 1. Code Smells (Critical)

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

## Severity Levels

| Level | Description | Action |
|-------|-------------|--------|
| **Critical** | Security risks, bugs, data loss potential | Must fix before merge |
| **Major** | Code smells, maintainability blockers | Should fix soon |
| **Minor** | Style, minor improvements | Nice to have |
| **Info** | Suggestions, alternatives | Optional |

## Resources

- [references/code-smells.md](references/code-smells.md) - Complete catalog of code smells with examples
