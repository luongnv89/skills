# Overview Fields — Per-Branch Drill-Down

Used in Step 6 when the user asks to inspect one unmerged branch before deciding Delete / Archive / Open PR / Keep. Collect as much signal as the available tools allow; the inspection is read-only and never checks the branch out. Run independent git commands in parallel where possible.

## Identity & activity

- Tip commit SHA, author, date.
- First commit unique to the branch (where it diverged from main).
- Total commits ahead of main, commits behind main.
- Last activity date and days since.
- All distinct authors who touched the branch.

## Merge status

- Already merged into main? (`git branch --merged main` and `git log main --oneline | grep <sha>`)
- Squash-merged? Check whether the patch-id of branch commits matches any commit on main (`git cherry main <branch>` — lines starting with `-` are equivalent commits already on main), plus the squash-tree check in `merged-detection.md` for multi-commit squashes.
- Linked PR via `gh pr list --head <branch> --state all --json number,state,title,url,headRefOid` if `gh` is available.

## Diff scope

- Files changed vs main (`git diff --stat main...<branch>`).
- Lines added/removed.
- Top-touched directories.
- File overlap with recent main activity (last 30 days) — flags likely conflicts.

## Implementation depth (the part that matters for the decision)

Go beyond mechanical stats. Read enough of the diff and commit messages to explain *what the branch does*, not just how big it is.

- Read `git log main..<branch>` for commit messages and the story they tell.
- Run `git diff main...<branch>` and inspect the actual changes — which functions/classes/modules were added or modified, what new dependencies were introduced, what tests were added, what was removed.
- For large diffs, read the diff in chunks and prioritize: new files, then modified files in core directories, then test files. Skip vendored/lockfile/generated files.
- Identify the **intent**: feature, refactor, bugfix, experiment, spike, abandoned WIP. Signals: TODO/FIXME density, presence of tests, commit message quality, whether commits look polished or scratch.
- Note unfinished signals: failing-looking commit messages ("WIP", "broken", "trying X"), commented-out code, dangling debug prints.

If `git diff --shortstat main...<branch>` reports more than 1000 changed lines (insertions plus deletions), spawn an Explore subagent to summarize the implementation instead of reading the diff in the main context. If no subagent is available, read it in the prioritized chunks above and say in the overview which files were not read. A weak summary is worse than admitting the diff was only partly read.

## Staleness signals

- Days since last commit.
- Has main moved significantly since the branch diverged (commits behind)?
- Are the touched files still present on main, or has the area been rewritten?

## Overview block

```
◆ Branch Overview: <branch>
··································································
  Refs:               local=<yes/no> remote=<yes/no> in-sync=<yes/no>
  Tip:                <sha-short> <date> by <author>
  Activity:           <N> ahead, <M> behind main, last commit <X> days ago
  Diff:               <files> files, +<added>/-<removed> lines
  Merge status:       <unmerged> (cherry-equivalent: <K>/<N>)
  Linked PR:          <url or "none" or "n/a — gh not available">
  Staleness:          <fresh | stale (>30d) | abandoned (>90d)>
  Intent:             <feature | refactor | bugfix | experiment | WIP | unclear>

What this branch implements: <2-6 sentences grounded in the diff>
Recommendation: <delete | archive | open PR | keep> — <one-sentence reason>
```

The recommendation is a suggestion. Ask the user to choose, then follow `action-plans.md`.
