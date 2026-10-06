# Member Contracts

What each member does on its own, so the orchestrator neither duplicates nor suppresses it. Every
member is used **unedited**; these notes describe its current behavior, they do not change it.

## Shared by all four chain members

- **Member report:** each run, stops included, ends with a Final Report whose lines are `Result:`
  (starting with `COMPLETE`, `PARTIAL` or `BLOCKED`), `Evidence:`, `Uncertainty:`, `Decision:` and
  `Next step:`. idea-validator adds `Strengths:` and `Concerns:` between `Evidence:` and `Uncertainty:`.
- **Evidence:** the commit hash and GitHub links built from `git remote get-url origin` and the
  **current branch** (`blob/<branch>/...`, not `blob/main`). Copy them from this line into the
  orchestrator's Final Report; never rebuild them.
- **Declined push or missing `origin`:** the member commits locally and reports `PARTIAL`, with the
  hash marked `local only` and no links. The file exists, so the orchestrator asks before continuing.
- **Repo Sync:** each member runs its own, scoped with `git -C`. Do not skip or suppress it.

## idea-validator

- **Input:** the idea text in `$ARGUMENTS`; asks the user to describe it when empty.
- **Storage:** resolves the ideas root (`IDEAS_ROOT` → `~/.config/ideas-root.txt` → legacy
  `~/.openclaw/ideas-root.txt` → asks once) and creates `YYYY_MM_DD_<short_snake_case_name>/`. When a
  folder with the same date and name already exists, it **reuses that folder and updates its files**
  instead of creating a second one. It picks the name itself and has no input for writing into a
  chosen folder.
- **Writes:** `idea.md`, `validate.md`. Echoes the absolute project folder path, and repeats it on its
  `Evidence:` line: capture it as `PROJECT_DIR`.
- **Gates:** Phase 1 and Phase 2 questions to the user; stops and asks if web search is unavailable;
  asks whether to proceed when a near-identical product exists.
- **Verdict:** the bold line under `## Quick Verdict` in `validate.md`: `**Build it**`, `**Maybe**` or
  `**Skip it**`. The verdict rule number and rationale belong under `## Why`; match the leading token
  so a trailing parenthetical such as `**Maybe (rule 2)**` still reads as `Maybe`. Four 1–10 ratings.
- **Git:** commits and pushes immediately, **without asking** for push permission. Its `Evidence:` line
  carries the links to `idea.md`, `validate.md` and, when changed, `README.md`, plus the commit hash.
- **Status:** `BLOCKED` with no idea description, an unwritable ideas root, or a declined no-search run;
  `PARTIAL` when a step stopped early, search was unavailable, or the files were not pushed.

## prd-generator

- **Input:** `PROJECT_DIR` in `$ARGUMENTS`; needs `idea.md` and `validate.md` there.
- **Writes:** `prd.md` (10 sections).
- **Existing `prd.md`:** backs it up as `prd.backup.YYYYMMDD_HHMMSS.md` and enters Modification Mode.
- **Gates:** Phase 3 clarifications (official product name, business model, MVP timeframe, team,
  compliance); asks whether to continue when `validate.md` is missing. On a `Skip it`, `REJECT` or
  `NOT RECOMMENDED` verdict it shows the verdict and **asks whether the user still wants a PRD**;
  without a yes it stops. The orchestrator passes the user's override with the folder so the user is
  not asked twice; if it asks anyway, relay the question unchanged.
- **Git:** commits, then **confirms before pushing**. Its `Evidence:` line carries the `prd.md` link and
  commit hash.

## brand-name-checker (optional)

- **Input:** the name to check in `$ARGUMENTS`. Take it from `prd.md` (the official product name
  prd-generator asked for). If `prd.md` names none, ask the user.
- **Writes:** no file. Returns a compact report ending in `RISK:` (Low/Moderate/High) and
  `RECOMMEND:` (Proceed/Modify/Abandon). Reads `prd.md` for a Name Fit Assessment.
- **Early exit:** an exact social handle taken returns Abandon and skips the other checks.
- **Dedup:** it leaves no artifact, so it never runs unless the user asks for it in this invocation.

## tad-generator

- **Input:** `PROJECT_DIR` in `$ARGUMENTS`; needs `prd.md`; reads `idea.md`/`validate.md` if present.
- **Writes:** `PROJECT_DIR/tad.md` (11 sections).
- **Existing `tad.md`:** goes into Modification Mode, after a non-empty backup
  `tad.md.bak.YYYYMMDD_HHMMSS`, and asks which area changed. This is why it must not be invoked when
  `tad.md` exists and no change was asked.
- **Gates:** Phase 3 architecture questions (deployment, database, auth, budget). A `prd.md` under 200
  words makes it **wait for the user's input**: "proceed anyway" continues with `TBD` values, and no
  answer is `BLOCKED`, which stops the chain at stage 3.
- **Status:** `BLOCKED` also for a missing `prd.md`, an unwritable `PROJECT_DIR`, a failed backup, or an
  unresolved sync conflict; no `tad.md` is written.
- **Git:** commits, then **confirms before pushing**. Its `Evidence:` line carries the `tad.md` link and
  commit hash.

## tasks-generator

- **Input:** the **PRD file path** (`PROJECT_DIR/prd.md`), not the folder.
- **Reads:** `tad.md`, `ux_design.md`, `brand_kit.md` in the same folder when present.
- **Writes:** `tasks.md` next to the PRD.
- **Existing `tasks.md`:** backs it up as `tasks_backup_YYYY_MM_DD_HHMMSS.md` (checked non-empty) and
  regenerates.
- **Status:** `BLOCKED` when `python3` is missing or the dependency script rejects the graph twice (also
  for an unwritable folder, a failed backup, or an agent that failed twice); no new `tasks.md` is
  written, and the chain stops at stage 4.
- **Git:** commits, then **confirms before pushing**; a missing `origin` skips the push (`PARTIAL`). Its
  `Evidence:` line carries the `tasks.md` link and commit hash.

## Final Report

The orchestrator's closing summary is defined in `SKILL.md` (*Final Report*). Its template, filled
examples and fill rules live in `references/final-report.md`.
