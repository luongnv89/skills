# Member Contracts

What each member does on its own, so the orchestrator neither duplicates nor suppresses it. Every
member is used **unedited**; these notes describe its current behavior, they do not change it.

## idea-validator

- **Input:** the idea text in `$ARGUMENTS`; asks the user to describe it when empty.
- **Storage:** resolves the ideas root (`IDEAS_ROOT` → `~/.config/ideas-root.txt` → legacy
  `~/.openclaw/ideas-root.txt` → asks once) and always creates a new `YYYY_MM_DD_<short_snake_case_name>/`.
  It has no input for writing into an existing folder.
- **Writes:** `idea.md`, `validate.md`. Echoes the absolute project folder path: capture it.
- **Gates:** Phase 1 and Phase 2 questions to the user; stops and asks if web search is unavailable;
  asks whether to proceed when a near-identical product exists.
- **Verdict:** `Build it` / `Maybe` / `Skip it`, plus four 1–10 ratings.
- **Git:** commits and pushes immediately, **without asking** for push permission. Reports GitHub links
  to `idea.md`, `validate.md`, and `README.md` if updated, plus the commit hash.

## prd-generator

- **Input:** project folder in `$ARGUMENTS`; needs `idea.md` and `validate.md` there.
- **Writes:** `prd.md` (10 sections).
- **Existing `prd.md`:** backs it up as `prd.backup.YYYYMMDD_HHMMSS.md` and enters Modification Mode.
- **Gates:** Phase 3 clarifications (official product name, business model, MVP timeframe, team,
  compliance); stops and asks when `validate.md` is missing; checks for a `REJECT`/`NOT RECOMMENDED`
  verdict (does not match idea-validator's `Skip it`).
- **Git:** commits, then **confirms before pushing**. Reports the `prd.md` GitHub link and commit hash.

## brand-name-checker (optional)

- **Input:** the name to check in `$ARGUMENTS`. Take it from `prd.md` (the official product name
  prd-generator asked for). If `prd.md` names none, ask the user.
- **Writes:** no file. Returns a compact report ending in `RISK:` (Low/Moderate/High) and
  `RECOMMEND:` (Proceed/Modify/Abandon). Reads `prd.md` for a Name Fit Assessment.
- **Early exit:** an exact social handle taken returns Abandon and skips the other checks.
- **Dedup:** it leaves no artifact, so it never runs unless the user asks for it in this invocation.

## tad-generator

- **Input:** project folder in `$ARGUMENTS`; needs `prd.md`; reads `idea.md`/`validate.md` if present.
- **Writes:** `tad.md` (11 sections).
- **Existing `tad.md`:** goes straight into Modification Mode (backup `tad.md.bak.<timestamp>`, asks
  which area changed). This is why it must not be invoked when `tad.md` exists and no change was asked.
- **Gates:** Phase 3 architecture questions (deployment, database, auth, budget); stops when `prd.md` is
  missing; warns when the PRD is under 200 words.
- **Git:** commits, then **confirms before pushing**. Reports the `tad.md` link and commit hash.

## tasks-generator

- **Input:** the **PRD file path** (`PROJECT_DIR/prd.md`), not the folder.
- **Reads:** `tad.md`, `ux_design.md`, `brand_kit.md` in the same folder when present.
- **Writes:** `tasks.md` next to the PRD.
- **Existing `tasks.md`:** backs it up as `tasks_backup_YYYY_MM_DD_HHMMSS.md` and regenerates.
- **Gates:** stops and asks when no `origin` remote exists; **confirms before pushing**. Reports the
  `tasks.md` link and commit hash.

## Closing summary template

```text
◆ Product Planner — Summary
··································································
  Project:    /abs/path/2026_10_06_example
  Range:      stages 1–4 (brand check: ran)
  Verdict:    Build it (Creativity 7, Feasibility 8, Market 6, Execution 8)

  | Artifact    | Status      | Path                         | Link / commit            |
  |-------------|-------------|------------------------------|--------------------------|
  | idea.md     | reused      | /abs/.../idea.md             | —                        |
  | validate.md | reused      | /abs/.../validate.md         | —                        |
  | prd.md      | generated   | /abs/.../prd.md              | <github link> · a1b2c3d  |
  | brand check | inline      | (no file)                    | RISK: Moderate · RECOMMEND: Modify |
  | tad.md      | generated   | /abs/.../tad.md              | <github link> · d4e5f6a  |
  | tasks.md    | not reached | —                            | stopped: push declined   |

  Overrides:  none
  Stale:      none
  Stopped:    after tad-generator — user declined the tasks-generator push
  Next step:  re-run /product-planner on this folder to resume at tasks-generator
```

Status values: `generated`, `reused`, `regenerated`, `skipped` (outside the range or opted out),
`not reached` (chain stopped earlier), `inline` (brand check). A `Skip it` override reads
`Overrides: verdict Skip it overridden by user`.
