# Repo Sync before writing the plan

Phase 3 writes `agent-ready-plan.md` into the repo and Phase 4 files issues against it.
The sync mutates the working tree, so it runs **after gate G3 approval** — the G3
message names it, and that one confirmation covers the sync and the write. Never sync
before the user has approved, and never sync in a run that will not write.

Not in a git repo at all? Phases 1–3 still run: write the plan to the working directory
and report that Phase 4 needs a git repo with a GitHub remote. No sync, no stash.

1. Confirm at gate G3 that the branch will be synced before the write. Without that
   approval, do not sync and do not write.
2. Inspect `git status --porcelain` and `git remote -v`.
3. If the tree is dirty, stash including untracked work, then sync, then pop:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
dirty=0
if [ -n "$(git status --porcelain)" ]; then
  git stash push -u -m "pre-agent-ready-sync: ${branch}"
  dirty=1
fi
git fetch origin
git pull --rebase origin "$branch" || {
  git rebase --abort 2>/dev/null
  echo "✗ sync failed — stop and ask the user" >&2
}
if [ "$dirty" -eq 1 ]; then
  git stash pop || {
    echo "✗ stash pop failed — recover with: git stash list && git stash show -p stash@{0}" >&2
  }
fi
```

4. If `origin` is missing, the pull conflicts, or the stash pop fails, **stop and ask
   the user** — do not write the plan on a partial sync. Report the run PARTIAL when
   Phases 1–2 were already delivered (see `final-report.md`).
