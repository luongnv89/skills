
# Clean Code

Audit code against the **bbv Clean Code Cheat Sheet** (Urs Enzler, V2.2) — Clean Code principles plus Clean ATDD/TDD practices — then deliver a findings report and a phased, task-level implementation plan ordered by priority.

## When to Use

**This mode is user-invoked only.** Run it only when the user explicitly:

- selects the `clean` mode (`code-review mode:clean`), or
- asks for a "clean code audit", "clean code review", "check this against clean code", "how clean is this code", "clean code report", or "clean code plan".

Do **not** auto-trigger on general coding, bug-fixing, feature work, performance tuning, or ordinary PR review — those belong to the `review` or `perf` modes, or `test-coverage`. If a request is ambiguous (plain "review this code"), assume the `review` mode and ask before running this audit.

## What It Produces

`CLEAN_CODE_AUDIT.md` (always), written to the repo root, containing:

1. **Findings** grouped by cheat-sheet category, each citing `file:line` and a principle/smell label.
2. **A phased implementation plan** split by priority — Phase 1 (Critical) → Phase 2 (Major) → Phase 3 (Minor) — where every task has an ID, a target `file:line`, the principle it fixes, an effort estimate, and an acceptance check.

**Optional `CLEAN_CODE_AUDIT.html`** — a single self-contained, offline-safe visual report (dark-IDE theme: metric tiles, a severity donut, effort-by-phase bars, collapsible findings, and an interactive phased plan with progress tracking). Offer it after writing the `.md`; build it from `references/report-template.html` following `references/html-report-guide.md`. Same data as the `.md`, visual form — keep counts consistent between the two.

This skill **does not edit source code.** It audits and plans; a human (or a follow-up skill like `code-review`/`test-coverage`) executes the tasks.

## Repo Sync Before Edits (mandatory)

This skill writes `CLEAN_CODE_AUDIT.md` into the repository, so sync the current branch with remote before writing:

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

If `origin` is missing, pull is unavailable, or rebase/stash conflicts occur, stop and ask the user before continuing. If the target is not a git repo at all, note that and write the report anyway.

## Quick Start

1. **Sync** the repo (section above).
2. **Scope** the audit (Phase 0 below) — pick what to scan and confirm with the user if scope is large.
3. **Audit** the code against the two checklists (Phase 1).
4. **Synthesize** findings and rank by severity (Phase 2).
5. **Plan** the phased, task-level remediation (Phase 3).
6. **Write** `CLEAN_CODE_AUDIT.md` and verify against Acceptance Criteria (Phase 4).

## Workflow

### Phase 0 — Scope

Determine what to audit and how deep:

- **Targeted**: specific files/dirs the user named, or the current diff (`git diff --name-only`). Default when the user points at something.
- **Full audit**: the whole codebase. Prioritize entry points (`main`, `index`, `app`), core business logic, then the rest.
- **Size guard**: if the scope exceeds ~50 files or ~10K lines, tell the user the size, propose auditing the highest-value subset first (entry points + most-changed files via `git log`), and confirm before proceeding. Record the chosen subset in the report header.

Detect the primary language(s) so checks are idiomatic — do not flag a Python idiom as a smell in JavaScript, or vice versa.

### Phase 1 — Audit Against the Checklists

Read both checklist references and apply them to the in-scope code. To respect the agent's context budget, load only the reference you need when you need it; don't hold both in context if the scope is one-sided.

- **Clean Code half** — read `references/clean-code-checklist.md`: smells, class design (SOLID), package cohesion/coupling, design principles, dependencies, naming, methods, source structure, conditionals, maintainability killers, exception handling.
- **Clean ATDD/TDD half** — read `references/tdd-checklist.md`: kinds of tests, design for testability, unit-test principles, test smells, TDD process smells, red/green patterns, ATDD, the test pyramid, and CI practices.

For each issue found, capture: the **principle/smell name**, the exact **`file:line`**, a one-line **description of the violation**, and a **proposed fix direction** (what clean-code pattern resolves it).

Use the **Severity Levels** table below to classify each finding as you go.

### Phase 2 — Synthesize & Rank

- Deduplicate findings by `(file, line, principle)`.
- Promote **cross-file patterns** to their own findings: Duplicate Code (DRY), Shotgun Surgery, Divergent Change, Parallel Inheritance — these are invisible at single-file granularity and matter most.
- Rank every finding by severity (Critical → Major → Minor → Info).
- Do **not** fabricate findings. If the code is clean, say so with all-zero counts and a brief "LGTM" note.

### Phase 3 — Build the Phased Plan

Convert findings into actionable tasks, grouped into priority phases. **Phasing is by severity** — see the **Severity Levels** table below for the Critical/Major/Minor definitions and their phase mapping.

Each task MUST have: a stable **ID** (`1.1`, `1.2`, `2.1`…), a short **title**, the **target `file:line`(s)**, the **principle/smell** it addresses, an **effort estimate** (e.g. `~15m`, `~2h`, `~1d`), **dependencies** (other task IDs that must come first, or `none`), and an **acceptance check** (how to confirm the task is done).

Order tasks within a phase so that enabling refactors (extract method, introduce abstraction) precede the changes that depend on them.

### Phase 4 — Write & Verify

Write `CLEAN_CODE_AUDIT.md` (format below). Then verify it against the **Acceptance Criteria**. Emit the **Step Completion Report**.

Then **offer the optional HTML report**: "Want a visual `CLEAN_CODE_AUDIT.html` too?" If yes, build it from `references/report-template.html` per `references/html-report-guide.md` — fill every `{{placeholder}}`, expand the `REPEAT` blocks, and confirm zero `{{` tokens remain and counts match the `.md`.

## Severity Levels

| Level        | Meaning                                                          | Phase   |
| ------------ | --------------------------------------------------------------- | ------- |
| **Critical** | Bugs, security risks, broken core principles, risky-untested    | Phase 1 |
| **Major**    | Code smells, high coupling, maintainability blockers, test smells | Phase 2 |
| **Minor**    | Naming, small conditionals, dead code, style                    | Phase 3 |
| **Info**     | Suggestions/alternatives; not scheduled into a phase            | —       |

## Output Format

Write `CLEAN_CODE_AUDIT.md` with this structure:

````markdown
# Clean Code Audit

**Date**: YYYY-MM-DD
**Scope**: [files/dirs or "Full audit (subset: …)"]
**Files Audited**: N
**Source standard**: bbv Clean Code Cheat Sheet V2.2

## Summary

| Severity | Count |
| -------- | ----- |
| Critical | X     |
| Major    | X     |
| Minor    | X     |
| Info     | X     |

## Findings

### Critical

#### [Principle/Smell]: Short title
**File**: `path/to/file.ext:42`
**Principle**: [e.g. Single Responsibility Principle]

One-line description of the violation.

**Fix direction**: [which clean-code pattern resolves it]

```language
// optional: minimal illustrative snippet
```

### Major
…

### Minor
…

### Info
…

## Implementation Plan

### Phase 1 — Critical (do first)

- [ ] **1.1 — [title]**
  - File: `path/to/file.ext:42`
  - Principle: [name]
  - Effort: ~2h
  - Depends on: none
  - Acceptance: [how to confirm done]

- [ ] **1.2 — [title]**
  - …

### Phase 2 — Major

- [ ] **2.1 — [title]**
  - …

### Phase 3 — Minor

- [ ] **3.1 — [title]**
  - …

## Notes

- [Cross-file patterns, sampling notes, excluded files, language-specific caveats]
````

### Expected Output

For a finding, the report should read like this:

```markdown
#### [Single Responsibility Principle]: UserService does too much
**File**: `src/user_service.py:1`
**Principle**: Single Responsibility Principle (Class Design)

`UserService` (312 lines) handles persistence, validation, and email — three reasons to change.

**Fix direction**: Extract persistence into `UserRepository` and email into `Notifier`; keep only orchestration here.
```

And the matching plan task:

```markdown
- [ ] **1.1 — Split UserService into focused classes**
  - File: `src/user_service.py:1`
  - Principle: Single Responsibility Principle
  - Effort: ~3h
  - Depends on: none
  - Acceptance: `UserService` ≤100 lines; persistence and email live in their own classes; tests pass.
```

## Acceptance Criteria

A run passes when **all** are true:

- [ ] `CLEAN_CODE_AUDIT.md` exists at the repo root, first heading `# Clean Code Audit`.
- [ ] Header records Date, Scope, Files Audited, and the source standard.
- [ ] A `## Summary` table with Critical/Major/Minor/Info rows is present and matches the findings count.
- [ ] Every finding cites a `path/to/file.ext:line` and a named principle/smell from the cheat sheet.
- [ ] An `## Implementation Plan` exists with Phase 1/2/3 sections; each task has ID, file:line, principle, effort, dependencies, and acceptance check.
- [ ] Phase assignment matches severity (Critical→Phase 1, Major→Phase 2, Minor→Phase 3).
- [ ] No source files were modified by this skill.
- [ ] If no issues exist, the report shows all-zero counts and an "LGTM" note instead of fabricated findings.
- [ ] If the HTML report was produced: `CLEAN_CODE_AUDIT.html` has no remaining `{{` placeholder tokens, and its severity counts match the `.md` Summary table.

## Edge Cases

- **Empty/whitespace-only scope**: report zero files audited; skip and inform the user.
- **Binary/generated/minified files** (`dist/`, `*.min.js`, lockfiles): exclude and note them in the report header.
- **Polyglot repo**: apply language-appropriate checks per file; don't cross-flag idioms.
- **No tests present at all**: that itself is a Critical finding (no safety net) per the TDD checklist — schedule "establish a test harness" as a Phase 1 task.
- **Scope exceeds size guard**: fall back to the highest-value subset and record the sampling strategy in `## Notes`.
- **Not a git repo**: note it, skip Repo Sync, still write the report.
- **Merge-conflict markers** (`<<<<<<<`, `=======`, `>>>>>>>`) in source: surface as a Critical finding; never silently ignore.

## Step Completion Reports

After each major phase, output a status report:

```
◆ [Step Name] ([step N of M] — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          √ pass (note if relevant)
  [Check 3]:          × fail — [reason]
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Use `√` for pass, `×` for fail, `—` for context. Skill-specific checks per phase:

- **Phase 0 — Scope**: `Scope determined`, `Language(s) detected`, `Size guard checked`
- **Phase 1 — Audit**: `Clean Code checks run`, `TDD/ATDD checks run`, `Findings captured with file:line`
- **Phase 2 — Synthesize**: `Deduplicated`, `Cross-file patterns surfaced`, `Severity assigned`
- **Phase 3 — Plan**: `Tasks created`, `Phased by severity`, `Each task has acceptance check`
- **Phase 4 — Write**: `CLEAN_CODE_AUDIT.md written`, `Acceptance criteria met`, `No source edited`

## Resources

- [references/clean-code-checklist.md](references/clean-code-checklist.md) — Clean Code half: smells, SOLID, naming, methods, conditionals, exceptions, design, dependencies.
- [references/tdd-checklist.md](references/tdd-checklist.md) — Clean ATDD/TDD half: test kinds, testability, test smells, TDD cycle, red/green patterns, test pyramid, CI.
- [references/report-template.html](references/report-template.html) — self-contained dark-IDE HTML report template (placeholders + REPEAT blocks). Only loaded when producing the optional HTML output.
- [references/html-report-guide.md](references/html-report-guide.md) — how to fill the HTML template: placeholder map, REPEAT-block expansion, percentage/effort math, and the pre-delivery self-check.
