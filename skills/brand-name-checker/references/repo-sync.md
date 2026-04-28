# Repo Sync Before Edits

Before creating/updating/deleting files in an existing repository, sync the current branch with remote.

## Clean working tree

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

## Dirty working tree

If the working tree is not clean, stash first, sync, then restore:

```bash
git stash push -u -m "pre-sync"
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin && git pull --rebase origin "$branch"
git stash pop
```

## Failure handling

If `origin` is missing, `pull` is unavailable, or rebase/stash conflicts occur, stop and ask the user before continuing.
