# Ideas index

One rule for the ideas repo's README index, shared word for word by `idea-validator`, `prd-generator`,
`tad-generator` and `tasks-generator`. Keep the four copies identical.

The **ideas repo root** is the top level of the git repository that holds the idea folder
(`git -C <idea folder> rev-parse --show-toplevel`), or the ideas root when the folder is in no git repository.

## With the generator script

When the ideas repo root has `scripts/update_readme_ideas_index.py`, run it from the ideas repo root:

```bash
python3 scripts/update_readme_ideas_index.py
```

It regenerates the ideas sections of `README.md` between the `<!-- BEGIN GENERATED: ideas … -->` and
`<!-- END GENERATED: ideas -->` markers, and all of `DASHBOARD.md`, from the idea folders and
`idea_status.json`. Never edit between those markers or in `DASHBOARD.md` by hand, and never create the
script. If it exits non-zero, leave both files as they are, report its `[ERROR]` line, and the run is
`PARTIAL`. Stage `README.md` and `DASHBOARD.md` only when the run changed them.

## Without the script

Keep one `## Ideas index` table in the ideas repo root's `README.md`, with exactly these columns in this
order and no others; rows newest first by folder date:

| Idea | PRD | Tasks | Verdict | Status |
|---|---:|---:|---|---|
| [Idea: Habit Tracker for Nurses](ideas/2026_10_06_habit_tracker_for_nurses/idea.md) | ✅ | — | [Build](ideas/2026_10_06_habit_tracker_for_nurses/validate.md) | Active |

- **Idea**: the `idea.md` H1, linked to that file by its path from `README.md`.
- **PRD**, **Tasks**: `✅` when the idea folder has `prd.md` / `tasks.md`, else `—`.
- **Verdict**: the leading token of the `## Quick Verdict` line (`Build it` → `Build`, `Maybe`,
  `Skip it` → `Skip`), linked to `validate.md`; `—` before validation.
- **Status**: `Active` for a new row; keep an existing row's status.

A run that creates the table adds one row for every idea folder; later runs add or update only this idea's
row. There is no TAD column: `tad-generator` runs the script when it is
present and otherwise leaves `README.md` untouched.
