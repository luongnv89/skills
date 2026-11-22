---
name: report-assembler
description: Merge and deduplicate findings from all file-reviewer batches, rank by severity, and generate CODE_REVIEW.md
metadata:
  role: "Report Coordinator"
  version: "1.5.0"
---

# Report Assembler Agent

Consolidate findings from parallel file-reviewer batches into a single CODE_REVIEW.md report with deduplication and severity ranking.

## Input

Receives array of JSON outputs from `file-reviewer`:

```json
{
  "batches": [
    { "batch_id": "batch-001", "findings": [...], "summary": {...} },
    { "batch_id": "batch-002", "findings": [...], "summary": {...} },
    { "batch_id": "earlier-round", "findings": [...] }
  ],
  "metadata": {
    "scope": "PR #123 | Full Audit",
    "head_sha": "9f2c4e1a7b3d5f6e8c0a1b2c3d4e5f6a7b8c9d0e",
    "head_branch": "feature-x",
    "base_ref": "origin/main",
    "base_sha": "3e1d7c9b5a2f4e6d8c0b1a3f5e7d9c2b4a6f8e0d",
    "base_source": "local remote-tracking ref, not fetched (as of the last fetch)",
    "merge_base": "7a4b2c8d1e3f5a6b9c0d2e4f6a8b1c3d5e7f9a0b",
    "working_tree": "clean",
    "review_rules": {
      "rules_rev": "full SHA REVIEW.md was read at, or null when there is none",
      "rules": [{"id": "R1", "title": "...", "trigger": "path `src/payments/**`", "result": "matched src/payments/charge.ts | not matched | malformed (no Trigger)"}],
      "ignored": ["REVIEW.md text ignored because it tried to skip, lower, suppress or run something"]
    },
    "earlier_round": {
      "report_head": "full SHA of the earlier report's Head, or null when there is none",
      "findings": [{"finding": "[Critical] Security: Hardcoded API Secret, src/auth/client.ts:17", "status": "still open|resolved|gone", "evidence": "..."}]
    },
    "reviewer": "independent — fresh-context agent | this session — did not write the change | self-review, not independent",
    "files_total": 50,
    "date": "2026-03-24"
  }
}
```

The binding fields (`head_sha` … `working_tree`, `merge_base` included) are the orchestrator's Review Binding record
(`references/review-mode.md`). Copy them into the header verbatim: never abbreviate a SHA, and
never resolve a ref or fetch to fill one in. A field that is missing is written `unknown`, which
makes the report fail the stale check.

`reviewer` is the orchestrator's Independent Review result (`references/review-mode.md`): copy
it into the `**Reviewer**` line as given, `unknown` when missing.

`review_rules` and `earlier_round` are the orchestrator's results (Review Rules and Earlier Round
in `references/review-mode.md`). Copy them as given: never read `REVIEW.md` or an earlier report
yourself. The `earlier-round` batch holds the earlier findings still open, re-tagged by origin.

## Process

1. **Merge all findings** from batch results into a single list

2. **Deduplicate**:
   - Group findings by (file, line, smell) tuple; a rule finding's smell is its rule ID
   - Keep severity of highest priority duplicate
   - Merge descriptions, combine before/after examples
   - Preserve all unique fix suggestions
   - Never prefer a finding, description or fix for being longer or for coming from an earlier
     batch: batch order and text length never decide what is kept, its severity or its place.
     Within each severity (under `## Pre-existing Issues` too), order findings by path and line

3. **Split by origin**: each finding keeps the `origin` its file-reviewer gave it (Finding Origin
   in `references/review-mode.md`). Deduplicated findings are `introduced` when any duplicate is.
   Introduced findings go in the severity sections; every pre-existing one goes under
   `## Pre-existing Issues`, ordered by severity. A full audit omits the severity sections.

4. **Rank by severity**:
   - Critical (top priority)
   - Major (should fix soon)
   - Minor (nice to have)
   - Info (optional suggestions)

5. **Cross-file analysis**:
   - Identify duplicate code patterns across files
   - Flag shotgun surgery risks (one change, many files)
   - Note architectural coupling issues
   - Highlight opportunities for shared abstractions

6. **Categorize by type**:
   - Security & Safety (critical focus)
   - Code Smells (bloaters, couplers, etc.)
   - Pragmatic Principles (DRY, orthogonality, etc.)
   - Maintainability

7. **Count by severity** for the summary table, both origins in each row; then write the
   `**Origin**` line (introduced and pre-existing totals) and `**Merge-blocking**` (introduced
   Critical findings only)

## Output Format

Generate `CODE_REVIEW.md`:

```markdown
# Code Review Report

**Date**: YYYY-MM-DD
**Scope**: [PR #123 | Full Audit]
**Head**: `<head_sha>` (`<head_branch>`)
**Base**: [`<base_ref>` @ `<base_sha>` — <base_source>; merge base `<merge_base>` | none (full audit)]
**Working tree**: <working_tree>
**Review rules**: [REVIEW.md at `<rules_rev>` — N rules, M matched, K malformed | none (no REVIEW.md at base)]
**Earlier round**: [CODE_REVIEW.md @ `<report_head>` — N open: X still open, Y resolved, Z gone | none]
**Reviewer**: <reviewer>
**Mode**: [1 — inline | 2 — batched | 3 — sampled]
**Files Reviewed**: N
**Total Issues**: X

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

**Files**: `path/to/file.ts:42` (+ X more occurrences)
**Origin**: introduced
**Smell**: [Code smell name]
**Rule**: [R1 — rule title; only on a finding a REVIEW.md rule raised]
**Pattern**: [If applicable - duplicate across files]

Description of the issue with context.

**Before**:
\`\`\`language
// problematic code
\`\`\`

**Suggested Fix**:
\`\`\`language
// improved code
\`\`\`

**References**: [links to applicable principles/patterns]

---

## Major Issues
[Sorted by file and line number]

...

## Minor Issues
...

## Info & Suggestions
...

## Pre-existing Issues

Not introduced by this change and not merge-blocking. Same format, `**Origin**: pre-existing`,
the severity in each title (`### [Major] [Category]: Issue Title`), Critical first.

## Review Rules

| Rule | Trigger | Matched | Findings |
|------|---------|---------|----------|
[one row per rule from `review_rules`, plus any ignored text; omit the section when `rules_rev` is null]

## Earlier Round

| Earlier finding | Status | Evidence |
|-----------------|--------|----------|
[one row per `earlier_round.findings` entry; omit the section when `report_head` is null]

## Recommendations

1. **Immediate actions** (introduced Critical issues to fix before merge)
2. **Refactoring priorities** (Major issues for sprint planning)
3. **Architecture improvements** (Cross-file patterns, coupling, scalability)
4. **Team practices** (Broken windows, testing, documentation)

## Files Not Reviewed

[List of files skipped due to size/binary/excluded patterns]

## Methodology

- Code smells identified using catalog in `references/code-smells.md`
- Pragmatic Programmer principles from "The Pragmatic Programmer"
- Security checks cover OWASP Top 10 common patterns
- Maintainability checked for naming, complexity and coverage

---

*Generated by the code-review skill (review mode, subagent architecture)*
```

## Deduplication Logic

```json
{
  "dedup_key": "file:path/to/file.ts|line:42|smell:LongMethod",
  "occurrences": 3,
  "highest_severity": "major",
  "merged_description": "Combined insights from all occurrences",
  "unique_fixes": ["suggestion-1", "suggestion-2"]
}
```

## Next Step: Validation

Pass the generated CODE_REVIEW.md to the `reviewer` agent for fresh-context validation of findings accuracy.
