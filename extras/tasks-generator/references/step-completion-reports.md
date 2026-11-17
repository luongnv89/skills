# Step Completion Reports — check names per phase

Read this before emitting the first report (SKILL.md → *Step Completion Reports*). Use these check names; add a check only when the phase validated something extra.

| Phase | Checks |
|-------|--------|
| 1 Setup | `PRD resolved`, `PROJECT_DIR writable`, `python3 available`, `Repo synced` (or `— skipped: not a git repo` / `— skipped: no origin`), `Backup written` (or `— no prior tasks.md`), `WORK_DIR created` |
| 2 Requirements | `PRD parsed`, `Features extracted`, `Constraints identified`, `Ambiguities listed` |
| 3 Sprint Plan | `Phases defined`, `Sprints assigned`, `Feature dependencies mapped` |
| 4 Sprint Tasks | `Workers run` (`N/N`), `Sprint files valid`, `IDs canonical` |
| 5 Dependencies | `analyze_dependencies.py exit 0`, `Critical path taken from script`, `tasks.md written` |
| 6 Verify | `Self-test` (`N/7`), `Acceptance Criteria` (`N/M`), `Regenerated` (`— none` or what) |
| 7 README | `README updated` (or `— skipped: not an ideas repo`) |
| 8 Commit and push | `Staged by path`, `Committed`, `Pushed` (or `— declined` / `— no origin`) |

## Example (Phase 5)

```
◆ Dependencies (step 5 of 9 — 26 tasks, 4 sprints)
··································································
  analyze_dependencies.py exit 0:   √ pass — 26 tasks, 31 edges
  Critical path taken from script:  √ pass — 5 tasks, 12 days
  tasks.md written:                 √ pass
  [Criteria]:                       √ 3/3 met
  ____________________________
  Result:             PASS
```

## Example (Phase 8, push declined)

```
◆ Commit and push (step 8 of 9 — /Users/me/ideas)
··································································
  Staged by path:     √ pass — tasks.md, tasks_backup_2026_10_06_141502.md
  Committed:          √ pass — 4b7d0aa
  Pushed:             × fail — user declined
  [Criteria]:         √ 2/3 met
  ____________________________
  Result:             PARTIAL
```

A skipped phase prints one line instead of a report: `◆ README (step 7 of 9) — skipped: not an ideas repo`.
