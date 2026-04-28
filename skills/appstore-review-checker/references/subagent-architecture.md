# Subagent Architecture

When the Agent tool is available, this skill uses a 4-phase, multi-agent architecture optimized for large codebases. Each agent is self-contained, with clear responsibilities and structured outputs that can be reviewed independently.

## Phase 1: Project Explorer Agent

**Purpose:** Read all project files and build a structured app-profile.json inventory.

This agent:
- Scans Xcode project configuration (pbxproj, targets, frameworks)
- Reads Info.plist, entitlements, dependency files (Podfile, Package.swift)
- Analyzes source code for permission/API usage patterns
- Creates app-profile.json: a complete machine-readable inventory of the app's capabilities and patterns

**Output artifact:** `<project>/app-profile.json`

## Phase 2: Guideline Auditor Agent

**Purpose:** Apply 150+ App Store guidelines against the app profile.

This agent:
- Reads app-profile.json
- Applies each guideline from `references/guidelines.md`
- Produces per-guideline verdicts: PASS, FAIL, WARNING, or N/A
- Creates audit-results.json: structured verdicts with evidence and remediation guidance

**Output artifact:** `<project>/audit-results.json`

## Phase 3: Report Writer Agent

**Purpose:** Format audit results into a human-readable markdown report.

This agent:
- Reads audit-results.json
- Groups FAILs by severity, highlights top rejection triggers
- Generates APPSTORE_AUDIT.md with verdict summary, critical issues, warnings, and pre-submission checklist
- Provides actionable fix guidance for each failure

**Output artifact:** `<project>/APPSTORE_AUDIT.md`

## Phase 4: Fixer Agent (Optional)

**Purpose:** Apply code-level fixes for user-approved failures.

This agent:
- Receives user-approved FAIL guideline IDs from the report
- Implements fixes in Swift/Objective-C code and Info.plist
- Handles: missing privacy descriptions, restore purchases, account deletion UI, deprecated APIs, etc.
- Does NOT touch metadata or entitlements (those require App Store Connect or Xcode)

**Output:** Modified source files with git-ready changes.

## Data Flow

```
Project Files
    ↓
[Project Explorer] → app-profile.json
    ↓
[Guideline Auditor] → audit-results.json
    ↓
[Report Writer] → APPSTORE_AUDIT.md
    ↓
(User approves fixes)
    ↓
[Fixer] → Source code changes
```
