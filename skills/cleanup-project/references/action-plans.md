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
  branch          where   signal                    remote tip  local cmd        remote cmd
  feat/login      both    ancestry                  1a2b3c4     git branch -d    lease delete
  feat/search     both    squash-tree cherry '-'    9e8d7c6     git branch -D    lease delete
  fix/typo        remote  merged PR #41, OID match  4b5a6f7     —                lease delete
  (lease delete = git push --force-with-lease=refs/heads/<b>:<remote tip> origin :refs/heads/<b>)

Delete these 3 branches (5 refs)? [yes/no]
```

Local rows are tested against `main`, remote rows against `origin/main`; a merge that exists
only on unpushed local `main` does not qualify the remote ref. On yes, for each row: local delete, then remote delete, then `git fetch origin --prune`. A
`stale info` rejection means the remote tip moved: report the row as skipped with that reason. `-D`
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
`git clean -n` dry run before any `git clean -f` and show its output. Discards run before the
keep commit, and that commit names its paths (`git commit -m "<msg>" -- <kept paths>`) so no
other staged entry is swept into it.

## C. Ignore-file commit (Step 4)

```
1. Apply the diff shown above to .gitignore          [approved]
2. git add -- .gitignore
3. git commit -m "chore: ignore build artifacts" -- .gitignore     on main
   (alternative: git switch -c chore/gitignore-cleanup, commit, push, gh pr create)
Commit on main? [yes / branch+PR / no]
```

## D. Drill-down decisions for one unmerged branch (Step 6)

Pick the plan matching the user's choice and substitute `<branch>`.

### Delete (unmerged work is lost)

```
1. git worktree list --porcelain           # confirm no worktree uses <branch>
2. git rev-parse origin/<branch>           # record <sha>, if it exists on origin
3. git branch -D <branch>                  # force: the branch is not merged
4. git push --force-with-lease=refs/heads/<branch>:<sha> origin :refs/heads/<branch>
5. git branch -a --list '*<branch>'        # expect no output
```

Say plainly that the commits become unreachable. Offer Archive as the safer option. A
`stale info` rejection on the lease push means someone pushed since: stop and report it.

### Archive — tag and delete (preferred)

```
1. git tag archive/<branch> <branch>
2. git push origin archive/<branch>
3. git rev-parse origin/<branch>           # record <sha>
4. git branch -D <branch>
5. git push --force-with-lease=refs/heads/<branch>:<sha> origin :refs/heads/<branch>
Recovery: git switch -c <branch> archive/<branch>
```

Ask "tag-and-delete or rename to `archive/<branch>`?" before choosing; do not assume.

### Archive — rename namespace

```
1. git rev-parse origin/<branch>           # record <sha>
2. git branch -m <branch> archive/<branch>
3. git push origin archive/<branch>
4. git push --force-with-lease=refs/heads/<branch>:<sha> origin :refs/heads/<branch>
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
