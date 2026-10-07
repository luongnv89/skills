---
name: aso-marketing
description: "Optimize App Store and Google Play listings via a 7-phase, plan-approval-gated ASO workflow (keyword strategy, metadata, localization). Don't use for web SEO, paid UA campaigns, or pre-submission compliance audits."
license: MIT
effort: max
metadata:
  version: 1.4.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# ASO Marketing — Full-Lifecycle App Store Optimization

A comprehensive, iterative ASO workflow that takes a mobile app from analysis through planning, execution, verification, and reporting — covering both Apple App Store and Google Play Store.

## Environment Check

Before running this skill, verify:
- The project is a mobile app (iOS/Android or both)
- You have access to the app's source code or metadata files
- You can read project configuration files (build.gradle, Info.plist, etc.)
- You can create/update metadata files in the project directory

If any check fails, stop and ask for clarification.

## Repo Sync Before Edits (mandatory)

Before creating, updating, or deleting files in an existing repository, sync the current branch with remote. **Run the dry-run command first to preview, then confirm with the user before destructive sync.**

```bash
# Dry-run preview first
git fetch --dry-run origin
git status

# Then sync (after user confirms working tree is clean or backed up)
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If the working tree is not clean, **ask the user before stashing**. If `origin` is missing, pull is unavailable, or rebase/stash conflicts occur, stop and ask the user before continuing.

**Backup-first rule for metadata files:** Before overwriting any existing metadata file (e.g. `metadata/version/1.0/en-US.json`, `fastlane/metadata/android/en-US/title.txt`), create a `.bak` copy in the same directory or confirm the file is in version control. Never delete metadata files without explicit user confirmation.

## Subagent Architecture

This skill uses a Staged Pipeline + Review Loop architecture. Each phase maps to a subagent in `agents/`:

1. `agents/analyzer.md` — Phase 1 analysis report
2. `agents/plan-writer.md` — Phase 2 ASO plan
3. `agents/compliance-checker.md` — Phase 3 prohibited-keyword + trademark check
4. `agents/executor.md` — Phase 4 metadata changes
5. `agents/reviewer.md` — Phases 5-6 review + best-practices verification

Main agent orchestrates phase transitions and the **user approval gate after Phase 3**.

## Workflow Overview

The skill follows a 7-phase cycle. Never skip the policy compliance check or the planning approval gate — the user must approve a policy-compliant plan before execution begins.

```
Phase 1: Analyze → Phase 2: Plan → Phase 3: Policy Compliance Check
  → [User Approval Gate] → Phase 4: Execute → Phase 5: Review
  → Phase 6: Verify → Phase 7: Summarize
```

## Before You Start

1. Read `references/aso_best_practices.md` for the complete ASO knowledge base — **especially the "Store Policy Compliance" section** detailing prohibited keywords, trademark rules, and listing policy restrictions for both Apple and Google.
2. Determine which store(s) the user wants to optimize for.
3. Identify whether the user has existing metadata files, a live store listing, or is launching fresh.

## Phase Execution

Run each phase in order. Detailed instructions, templates, and checklists live in the reference files. Read each one before executing the corresponding phase, and only then, to keep the context window small.

### Phase 1: Analyze

Read `references/phases-1-2.md` (Phase 1 section). Gather codebase info, audit existing store metadata, identify competitors, baseline performance, and produce an Analysis Report.

### Phase 2: Plan

Read `references/phases-1-2.md` (Phase 2 section). Build a prioritized plan covering objectives, target keywords (primary/secondary/long-tail), metadata optimization (title, subtitle, keywords, description, what's-new), visual assets, localization, ratings strategy, and timeline.

### Phase 3: Policy Compliance Check

Read `references/phase-3-compliance.md`. Validate every proposed metadata field against:
- Prohibited keyword lists (Apple + Google)
- Trademark and competitor brand checks
- Formatting rules (no emojis, no ALL CAPS, character limits)
- Content accuracy

If any violation is found, **revise the plan silently and re-run the compliance check**. The user should only ever see a compliant plan.

### User Approval Gate

After compliance passes, present the plan and compliance report to the user. **Do not proceed to Phase 4 until the user explicitly approves the plan.** Iterate as many times as needed; each revision must re-pass the compliance check.

### Phase 4: Execute

Read `references/phases-4-7.md` (Phase 4 section). Implement approved changes systematically, in priority order. **Before overwriting any existing metadata file, create a `.bak` backup or confirm version control coverage.** Validate character limits after each edit.

### Phase 5: Review

Read `references/phases-4-7.md` (Phase 5 section). Run the review checklist on every changed field. Re-scan for prohibited keywords and trademark leaks.

### Phase 6: Verify Against Best Practices

Read `references/phases-4-7.md` (Phase 6 section) and cross-reference `references/aso_best_practices.md`. Final pass for policy compliance.

### Phase 7: Summarize

Read `references/phases-4-7.md` (Phase 7 section). Produce the final summary report (Changes Made, Metadata Comparison, Compliance Status, Expected Outcomes, Next Steps, Files Modified).

## Step Completion Reports

Emit exactly 5 reports per run — the denominator `M` is always 5: Phase 1, Phases 2-3, Phase 4, Phases 5-6, Phase 7. Each uses `√` pass / `×` fail markers. Format and per-phase check lists are in `references/edge-cases.md` (Step Completion Reports section).

## Expected Output

A complete run produces three artifacts: Analysis Report (Phase 1), ASO Plan + Compliance Report + updated metadata files (Phases 2-4), and Summary Report (Phase 7). Worked examples for each: see `references/expected-output.md`. The run then closes with the Final Report.

## Final Report

End every run, stops included, with a four-line `Result` / `Evidence` / `Uncertainty` / `Decision` block after the Step Completion Reports; it never replaces the Phase 7 Summary Report. The first word after `Result:` is `COMPLETE` (every applicable Acceptance Criteria item is checked), `PARTIAL` (the Analysis Report exists but an item is unchecked, for example the user rejected the plan), or `BLOCKED` (no Analysis Report). Status table, examples and fill rules: `references/final-report.md`.

## Example

Input: an iOS+Android productivity app with weak metadata.

```
Title (iOS): FocusFlow: Work Timer            (21/30, no primary keyword)
Keywords (iOS): timer,focus,work,productivity (29/100, 71 chars unused)
Short Desc (Android): A simple timer for focused work. (32/80, weak)
```

Output after Phase 4 (`metadata/app-info/en-US.json`):

```json
{
  "name": "FocusFlow: Focus & Work Timer",
  "subtitle": "Deep Work Sessions & Tracking"
}
```

Output keywords field:

```
pomodoro,concentration,study,productivity,distraction,blocker,habit,goal,task,routine,break,planner
```

(99/100 chars, all prohibited terms cleared, no word repeated from the title or subtitle.) Full walkthrough in `references/expected-output.md`.

## Acceptance Criteria

The skill run is successful when all metadata is within character limits, contains no prohibited keywords or trademarks, the user-approval gate was respected, and all required reports were produced. Full criteria list: `references/edge-cases.md` (Acceptance Criteria section). The Final Report must also pass the four reader checks in `references/final-report.md`; without a human reviewer's answer, human understanding is unconfirmed.

## Edge Cases

Common edge cases (no local metadata files, single-platform app, no competitor access, pre-launch app, non-English primary locale, user rejects plan, compliance violation in draft) are documented in `references/edge-cases.md`. Read that file when an edge case applies — do not improvise.

## Platform-Specific Notes

Apple App Store, Google Play Store, and cross-store conventions (indexed fields, character limits, OCR-indexed screenshots, A/B testing surfaces) are documented in `references/edge-cases.md` (Platform-Specific Notes section).

## Cross-Skill Integration

This skill complements `seo-ai-optimizer`. See `references/edge-cases.md` (Cross-Skill Integration section) for when to combine.

## Safety and Caution

- **No destructive action without confirmation.** Before `git pull --rebase`, run the dry-run preview in Repo Sync and get the user's confirmation. Before `git stash` or any file deletion, ask the user. Before overwriting an existing metadata file, create a `.bak` backup or confirm the file is tracked in version control. Report every failure or error to the user; do not retry it silently.
- **Compliance gate is non-negotiable.** Never present a non-compliant plan to the user; never execute without explicit approval.
- **Trademark caution:** Competitor brand names from Phase 1 analysis must never appear in proposed metadata.
