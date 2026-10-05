# Action Plans — Confirm, Then Execute

Every plan below follows **list → explicit confirm → execute**. Show the numbered commands with
real names substituted, wait for an explicit yes, then run them one by one and report each
outcome. A "no", or silence, means nothing runs. A failure stops that plan; never retry with
force.

## Protected branches (apply to every plan)

Never delete, rename, or force-push: `main`, `master`, `develop`, `trunk`, `release/*`, the
current branch, and any branch listed in `git worktree list --porcelain`. If the user asks to
delete one, refuse and explain which rule applies. For a worktree branch, tell them to run
`git worktree remove <path>` themselves first.

## A. Merged-branch sweep (Step 5)

```
Candidates (one confirmation covers this table):
  branch          where   signal                    local cmd            remote cmd
  feat/login      both    ancestry                  git branch -d        git push origin --delete
  feat/search     both    squash-tree cherry '-'    git branch -D        git push origin --delete
  fix/typo        remote  merged PR #41, OID match  —                    git push origin --delete

Delete these 3 branches (5 refs)? [yes/no]
```

On yes, for each row: local delete, then remote delete, then `git fetch origin --prune`. `-D`
appears only on rows whose evidence is signal 2 or 3 (see `merged-detection.md`). If a new
candidate appears after confirmation, it needs its own confirmation.

## B. Discards (Step 2)

```
Discard these changes? This cannot be undone.
  1. src/debug.log      ??   git clean -f -- src/debug.log
  2. app/config.ts       M   git restore --staged --worktree -- app/config.ts
  3. notes/draft.md     A    git restore --staged --worktree -- notes/draft.md   (file is deleted)
[yes/no]
```

Each row exists only because the user answered "discard" for it in the review. Run the
`git clean -n` dry run before any `git clean -f` and show its output.

## C. Ignore-file commit (Step 4)

```
1. Apply the diff shown above to .gitignore          [approved]
2. git add .gitignore
3. git commit -m "chore: ignore build artifacts"     on main
   (alternative: git switch -c chore/gitignore-cleanup, commit, push, gh pr create)
Commit on main? [yes / branch+PR / no]
```

## D. Drill-down decisions for one unmerged branch (Step 6)

Pick the plan matching the user's choice and substitute `<branch>`.

### Delete (unmerged work is lost)

```
1. git worktree list --porcelain           # confirm no worktree uses <branch>
2. git branch -D <branch>                  # force: the branch is not merged
3. git push origin --delete <branch>       # if it exists on origin
4. git branch -a --list '*<branch>'        # expect no output
```

Say plainly that the commits become unreachable. Offer Archive as the safer option.

### Archive — tag and delete (preferred)

```
1. git tag archive/<branch> <branch>
2. git push origin archive/<branch>
3. git branch -D <branch>
4. git push origin --delete <branch>
Recovery: git switch -c <branch> archive/<branch>
```

Ask "tag-and-delete or rename to `archive/<branch>`?" before choosing; do not assume.

### Archive — rename namespace

```
1. git branch -m <branch> archive/<branch>
2. git push origin archive/<branch>
3. git push origin --delete <branch>
```

### Open a PR

```
1. git push origin <branch>                 # if local is ahead
2. gh pr create --base main --head <branch> --title "<title>" --body "<body>"
```

Draft the title and body from the overview's implementation summary. Rebasing first is optional
and only on request.

### Keep

No commands. Note the branch in the final report as `unmerged, kept`.
