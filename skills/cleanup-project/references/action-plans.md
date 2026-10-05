# Action Plans — Confirm, Then Execute

Every plan below follows the SKILL.md **Rules for every destructive step** (list → explicit
confirm → execute, partial confirmation, no retry with force, protected branches). Show the
numbered commands with real names substituted, wait for an explicit yes, then run them one by one
and report each outcome.

## A. Merged-branch sweep (Step 5)

```
Candidates (one confirmation covers this table):
  branch       where   local signal   remote signal             remote tip  local cmd      remote cmd
  feat/login   both    ancestry       ancestry                  1a2b3c4     git branch -d  lease delete
  feat/search  both    squash-tree    squash-tree               9e8d7c6     git branch -D  lease delete
  fix/typo     remote  —              merged PR #41, OID match  4b5a6f7     —              lease delete
  feat/cache   both    ancestry       none (unmerged → Step 6)  3c2d1e0     git branch -d  —
  (lease delete = git push --force-with-lease=refs/heads/<b>:<remote tip> origin :refs/heads/<b>)

Delete these 4 branches (6 refs)? [yes/no]
```

Each side is tested against its own base (`merged-detection.md`): local `<b>` against `main`,
`origin/<b>` against `origin/main`. A side is deleted only on its own signal; a side with none
gets `—` and goes to the Step 6 unmerged list. On yes, for each row: local delete if its
`local cmd` is set, then remote delete if its `remote cmd` is set, then `git fetch origin
--prune`. A `stale info` rejection means the remote tip moved: report the row as skipped with
that reason. `-D` appears only when the local signal is squash evidence (signal 2 or 3). A reply like "yes except feat/search" removes that row: re-show
the edited table with the new counts and take a fresh yes. If a new candidate appears after
confirmation, it needs its own confirmation.

## B. Consolidated Step 2 plan

```
Plan (runs top to bottom; discards cannot be undone):
  discard  src/debug.log    ??  git clean -n -- src/debug.log, then git clean -f -- src/debug.log
  discard  notes/draft.md   A   git restore --staged --worktree -- notes/draft.md   (file is deleted)
  keep     app/config.ts     M  git switch -c wip/cleanup-<date>; git add -- app/config.ts;
                                git commit -m "<msg>" -- app/config.ts
  stash    notes/ideas.md   ??  git stash push -u -m "cleanup: ideas" -- notes/ideas.md
  ignore   .env             ??  kept on disk; pattern proposed in Step 4   ⚠ secret-like
  leave    scratch/         ??  untouched (left as is)
Run this? [yes/no]
```

Each row exists only because the user gave that answer for it in the review. Run the
`git clean -n` dry run before any `git clean -f` and show its output; run `-f` only if it lists
exactly the decided paths, else stop and report. Paths are single-quoted and passed with
`git --literal-pathspecs` (`uncommitted-review.md` 1), so `$` and `[slug]` stay literal. Discards run before the
keep commit, and that commit names its paths so no other staged entry is swept into it.

## C. Ignore-file commit (Step 4)

```
1. Apply the diff shown above to .gitignore          [approved]
2. git add -- .gitignore
3. git commit -m "chore: ignore build artifacts" -- .gitignore     on main
Commit on main? [yes / branch+PR / no]
```

Push is a separate question: `Push main to origin now? [yes/no]` → `git push origin main`.

Untrack variant, when the user approved `git rm --cached` for tracked-but-ignored paths (re-run
`git ls-files -ci --exclude-standard` after step 1; it lists files, so `<p>` is one file each):

```
1. Apply the diff shown above to .gitignore          [approved]
2. git rm --cached -- <p>                            [approved untrack; stays on disk]
3. git add -- .gitignore
4. git diff --cached --name-only        # expect exactly .gitignore and each <p>
5. git commit -m "chore: ignore build artifacts"     on main (no pathspec)
```

No pathspec in 5: `git commit -- <p>` re-stages `<p>` from the working tree, so it stays tracked.
If 4 lists any other path, do not run 5: run `git commit -m "<msg>" -- .gitignore`, then
`git restore --staged -- <p>` (undoes the untrack), and list `<p>` under `Next:` as still
tracked. Never leave a staged `D <p>` behind.

Branch+PR alternative:

```
1. git switch -c chore/gitignore-cleanup
2. git add -- .gitignore && git commit -m "chore: ignore build artifacts" -- .gitignore
   (untrack variant: run its steps 2–4 before 1, then commit with no pathspec here)
   Push chore/gitignore-cleanup and open PR? [yes/no]     # ask before 3 and 4
3. git push -u origin chore/gitignore-cleanup
4. gh pr create --base main --head chore/gitignore-cleanup --title "chore: ignore build artifacts"
5. git switch main
```

On "no" to the push question, skip 3 and 4, still run 5, and report the local branch under
`Next:` (`push chore/gitignore-cleanup and open a PR`).

Until the PR merges, `main` has no such rule, so the result is `PARTIAL — ignore rule pending in
PR #<n>`.

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
`stale info` rejection on the lease push means someone pushed since: stop and report it as
PARTIAL.

### Archive — pick the source tip first (both variants)

The local and remote tips can differ. Archiving the local tip and then deleting `origin/<branch>`
would lose any commit only the remote has. Compare them before either variant:

```
l="$(git rev-parse -q --verify refs/heads/<branch>)"                # empty if no local ref
sha="$(git rev-parse -q --verify refs/remotes/origin/<branch>)"     # the tip the lease guards
```

| Tips | `<src>` to archive |
|---|---|
| equal, or no remote ref | `<branch>` |
| no local ref, or local is an ancestor of origin (`git merge-base --is-ancestor "$l" "$sha"`) | `origin/<branch>` |
| origin is an ancestor of local (`git merge-base --is-ancestor "$sha" "$l"`) | `<branch>` (contains every remote commit) |
| diverged (neither test passes) | stop and ask; or, if the user picks it, archive both: `archive/<branch>` from `<branch>` and `archive/<branch>-remote` from `origin/<branch>` |

**Invariant:** the pushed archive must contain `<sha>`, the exact tip the `--force-with-lease`
delete guards. Check `git merge-base --is-ancestor "$sha" archive/<branch>` (or
`archive/<branch>-remote`) before the delete. If it fails, stop and do not delete the remote ref.

### Archive — tag and delete (preferred)

```
1. pick <src> and record <sha> (above)
2. git tag archive/<branch> <src>
3. git push origin archive/<branch>
4. git merge-base --is-ancestor <sha> archive/<branch>     # invariant; stop if it fails
5. git branch -D <branch>                                  # if a local ref exists
6. git push --force-with-lease=refs/heads/<branch>:<sha> origin :refs/heads/<branch>
Recovery: git switch -c <branch> archive/<branch>
```

Ask "tag-and-delete or rename to `archive/<branch>`?" before choosing; do not assume.

### Archive — rename namespace

```
1. pick <src> and record <sha> (above)
2. git branch --no-track archive/<branch> <src>            # not `git branch -m`: <src> may be origin/<branch>
3. git push origin archive/<branch>
4. git merge-base --is-ancestor <sha> archive/<branch>     # invariant; stop if it fails
5. git branch -D <branch>                                  # if a local ref exists
6. git push --force-with-lease=refs/heads/<branch>:<sha> origin :refs/heads/<branch>
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
