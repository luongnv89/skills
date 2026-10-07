# Repo Sync Before Edits

Before creating/updating/deleting files in an existing repository, sync the current branch with remote.

## Clean working tree

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

## Dirty working tree

If the working tree is not clean, stash first, sync, then restore. The snippet exits 0 on a clean tree and stops before syncing if the stash fails:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
dirty=0
if [ -n "$(git status --porcelain)" ]; then
  git stash push -u -m "pre-sync: ${branch}" || { echo "Stash failed; nothing was synced" >&2; exit 1; }
  dirty=1
fi
git fetch origin && git pull --rebase origin "$branch" || exit 1
if [ "$dirty" -eq 1 ]; then
  git stash pop || { echo "Stash pop failed; changes are safe in: git stash list" >&2; exit 1; }
fi
```

## Failure handling

If `origin` is missing, `pull` is unavailable, or rebase/stash conflicts occur, stop and ask the user before continuing.
