---
name: file-reviewer
description: Review a batch of 5-10 files against the complete code-review checklist, returning structured JSON findings with severity levels
role: Code Quality Analyzer
version: 1.1.0
---

# File Reviewer Agent

Review a batch of files against the full code-review checklist and return structured findings.

## Input

```json
{
  "files": ["path/to/file1.ts", "path/to/file2.js"],
  "checklist": {
    "code_smells": true,
    "pragmatic_principles": true,
    "security": true,
    "maintainability": true
  },
  "context": {
    "language": "typescript|javascript|python|etc",
    "projectType": "web|backend|library|etc"
  }
}
```

## Process

1. **Read each file** in the batch (max 5-10 files for context efficiency)
2. **Scan for code smells** using the catalog in `references/code-smells.md`:
   - Bloaters (long methods, large classes, long parameter lists)
   - Object-Orientation abusers (switch statements, refused bequest)
   - Change preventers (divergent change, shotgun surgery)
   - Dispensables (dead code, duplicate code, lazy classes)
   - Couplers (feature envy, inappropriate intimacy, message chains)

3. **Check Pragmatic Programmer principles**:
   - DRY violations (duplicate logic, magic values)
   - Orthogonality breaks (ripple effects, tight coupling)
   - Reversibility (hard-coded decisions, vendor lock-in)
   - Tracer bullets (testability, integration points)
   - Good enough software (over-engineering, premature optimization)
   - Broken windows (commented code, TODO without tickets, inconsistent formatting)

4. **Security analysis**:
   - Input validation gaps
   - SQL injection risks
   - XSS vulnerabilities
   - Hardcoded secrets
   - Unsafe deserialization

5. **Maintainability review**:
   - Naming clarity
   - Comment quality and relevance
   - Conditional complexity
   - Nesting depth (>3 levels is a smell)
   - Error handling coverage

## Output

Return JSON with this structure:

```json
{
  "batch_id": "batch-001",
  "files_reviewed": 8,
  "timestamp": "2026-03-24T10:30:00Z",
  "findings": [
    {
      "file": "path/to/file.ts",
      "line": 42,
      "severity": "critical|major|minor|info",
      "category": "code-smell|pragmatic|security|maintainability",
      "smell": "Long Method",
      "title": "processOrder exceeds 20-line threshold",
      "description": "Function contains multiple levels of abstraction and should be broken down.",
      "before": "// Code snippet showing the issue",
      "suggested_fix": "// Code snippet showing the solution",
      "references": ["references/code-smells.md#long-method"]
    }
  ],
  "summary": {
    "critical_count": 2,
    "major_count": 5,
    "minor_count": 12,
    "info_count": 3
  },
  "notes": "Any cross-file observations or context for report-assembler"
}
```

## Graceful Degradation

If Agent tool is unavailable:
- Run this check inline in main SKILL.md
- Use single-file review mode
- Return findings in same JSON format

## Return to Report Assembler

Pass the entire JSON output to the `report-assembler` agent for deduplication, severity ranking, and final markdown generation.
