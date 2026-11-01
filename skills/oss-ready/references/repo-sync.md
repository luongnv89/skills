# Repo Sync block — oss-ready

Run this block once, before Step 0 of SKILL.md. It requires a git repository, a named branch and an `origin` remote, then uses the stash-first sync flow. Each failure stops before any stash or sync operation.

```bash
git rev-parse --git-dir >/dev/null 2>&1 || {
  echo "✗ Not a git repository — stop."
  exit 1
}
branch="$(git symbolic-ref --quiet --short HEAD)" || {
  echo "✗ Detached HEAD — stop before stashing or syncing."
  exit 1
}
git remote get-url origin >/dev/null 2>&1 || {
  echo "✗ No 'origin' remote — ask the user before continuing without a sync."
  exit 1
}
dirty=0
if [ -n "$(git status --porcelain)" ]; then
  git stash push -u -m "pre-sync: ${branch} $(date +%Y-%m-%dT%H:%M:%S)" || {
    echo "✗ Could not stash local changes — resolution stopped."
    echo "  Recovery: inspect git status; do not discard the working tree."
    exit 1
  }
  dirty=1
fi

if ! git fetch origin || ! git pull --rebase origin "$branch"; then
  echo "✗ Repository sync failed — resolution stopped."
  if [ "$dirty" -eq 1 ]; then
    echo "  Your changes remain safe in the stash."
    echo "  Recovery: git stash list"
    echo "            git stash show -p stash@{0}"
  fi
  exit 1
fi

if [ "$dirty" -eq 1 ]; then
  git stash pop --index || {
    echo "✗ Stash restore failed — resolution stopped; your changes remain safe in the stash."
    echo "  Recovery: git stash list"
    echo "            git stash show -p stash@{0}"
    echo "            git checkout stash@{0} -- <path>"
    echo "            git stash pop --index stash@{0}"
    exit 1
  }
fi
```

## What the block does

It stops at the first failure:

1. Stop when `git rev-parse --git-dir` fails (not a git repository).
2. Stop when `git symbolic-ref --quiet --short HEAD` fails (detached HEAD), before any stash or sync.
3. Stop and ask the user when `git remote get-url origin` fails.
4. If `git status --porcelain` prints a line, stash with `git stash push -u`.
5. Run `git fetch origin && git pull --rebase origin "$branch"`.
6. Restore the stash with `git stash pop --index`.

## After the block

- **Exit 0**: go to Step 0.
- **Non-zero exit**: print the final report with `BLOCKED` (`references/final-report.md`). Never discard the working tree; give the user the printed recovery commands.
- **Missing `origin` only**: ask the user. With explicit approval, skip the stash and sync part of the block, go to Step 0, and list `Repo Sync skipped (no origin)` under `Uncertainty:`. Without approval, stop with `BLOCKED`.

## Step 0: Create feature branch

Run after the Repo Sync block exits 0.

1. Read the current branch: `git branch --show-current`.
2. Read the default branch: `git symbolic-ref --short refs/remotes/origin/HEAD`, without the `origin/` prefix. If that fails, use `main`, or `master` when only `master` exists.
3. If the current branch is not the default branch and its name contains `oss`, stay on it and go to Step 1.
4. Choose the prefix `feature/` when `git branch -a --format='%(refname:short)'` lists more `feature/` than `feat/` branches; otherwise `feat/`.
5. If `<prefix>oss-ready` exists, ask the user to reuse it or to give another name. Never reset an existing branch.
6. Run `git switch -c <prefix>oss-ready`, or `git switch <name>` to reuse. If it fails, stop with `BLOCKED`.
