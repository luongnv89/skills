# Example Output — Full Run

A worked `/cleanup-project` run on a repo with a dirty tree (including an untracked `.env`), one
build-artifact directory, three merged branches (one squash-merged, one remote-only), and two
unmerged branches. User replies are marked `>`.

## Scope and Step 1 — fetch and snapshot

```
Scope: full (Steps 1–7). OK?
> yes
$ git fetch origin --prune
Start: branch feat/search-v2, base main, 5 uncommitted entries, merged-PR check available (gh)
```

## Step 2 — uncommitted review

```
Answers: keep (commit to wip/cleanup-<date>) / keep on disk + ignore / stash / leave as is / discard

1/5  M  src/search/index.ts   (+12 -3)
     @@ -40,7 +40,16 @@ export function rank(...)
     ...
> keep (commit to wip/cleanup-2026-10-05)

2/5  ??  debug.log   (3 KB, "TRACE rank() ...")
> discard

3/5  ??  node_modules/   (1,284 files)
     Looks like a build artifact. Suggested: keep on disk + ignore
> keep on disk + ignore

4/5  A  scratch.md   (new, staged, 8 lines)
     Discarding deletes the file; it is not in HEAD.
> discard

5/5  ??  .env   (214 bytes)
     ⚠ secret-like: .env — content not shown. Default: keep on disk + ignore
> keep on disk + ignore

Every entry has an answer; none left undecided.

Plan (runs top to bottom; discards cannot be undone):
  discard  debug.log            git clean -n -- debug.log  ("Would remove debug.log"), then git clean -f -- debug.log
  discard  scratch.md           git restore --staged --worktree -- scratch.md   (file is deleted)
  keep     src/search/index.ts  git switch -c wip/cleanup-2026-10-05; git add -- src/search/index.ts;
                                git commit -m "chore: keep work in progress from cleanup" -- src/search/index.ts
  ignore   node_modules/        kept on disk; pattern proposed in Step 4
  ignore   .env                 kept on disk; pattern proposed in Step 4   ⚠ secret-like
Run this? [yes/no]
> yes
$ git clean -f -- debug.log; git restore --staged --worktree -- scratch.md
$ git switch -c wip/cleanup-2026-10-05; git add -- src/search/index.ts; git commit ... -- src/search/index.ts

◆ Cleanup (step 2 of 7 — uncommitted review)
··································································
  Entries listed:     √ pass (5 entries, 1 ⚠ secret-like, content not shown)
  Decisions recorded: √ pass (1 keep, 2 discard, 2 keep on disk + ignore, 0 left as is)
  Plan confirmed:     √ pass (one yes for the consolidated plan)
  Discards run:       √ pass (debug.log, scratch.md)
  Keep commit:        √ pass (wip/cleanup-2026-10-05, 1 path)
  Stash:              √ pass (none needed)
  ____________________________
  Result:             PASS
```

## Step 3 — switch and pull

```
$ git worktree list --porcelain     → main is not checked out in another worktree
$ git switch main && git pull --ff-only
Updating 4f2a91c..8c03d7e  Fast-forward
$ git rev-list --count origin/main..main
0                     → main is not ahead of origin/main; no local-only merges
```

## Step 4 — ignore file

```
Evidence: node_modules/ and .env untracked (keep on disk + ignore); git ls-files -ci --exclude-standard → (none)
Kept paths tested: src/search/index.ts matches no proposed pattern
⚠ secret-like: .env (untracked) — will be ignored, stays on disk
--- a/.gitignore
+++ b/.gitignore
+node_modules/
+.env*
Apply? > yes
$ git status --porcelain   → node_modules/ and .env no longer listed
Commit on main as "chore: ignore node and env artifacts"? [yes / branch+PR / no]
> yes
Push main to origin now? [yes/no]
> yes
$ git push origin main
```

## Step 5 — merged-branch sweep

```
  (local rows tested against main, remote rows against origin/main)
  branch          where   signal                              remote tip  local        remote
  feat/login      both    ancestry                            1a2b3c4     branch -d    lease delete
  feat/filters    both    squash-tree cherry '-' (3 commits)  5d6e7f8     branch -D    lease delete
  fix/readme      remote  merged PR #57, headRefOid match     9a0b1c2     —            lease delete
  (lease delete = git push --force-with-lease=refs/heads/<b>:<remote tip> origin :refs/heads/<b>)
Protected, skipped: main, release/2.1
Delete these 3 branches (5 refs)? [yes/no]
> yes
Deleted branch feat/login (was 1a2b3c4).
Deleted branch feat/filters (was 5d6e7f8).
To github.com:acme/app.git  - [deleted] feat/login  - [deleted] feat/filters  - [deleted] fix/readme
$ git fetch origin --prune
```

## Step 6 — unmerged

```
  feat/search-v2          6 ahead, 2 behind, last commit 1 day ago
  spike/llm-cache        14 ahead, 210 behind, last commit 143 days ago
  wip/cleanup-2026-10-05  7 ahead, 2 behind (cut from feat/search-v2, plus the kept commit from Step 2)
Inspect one before deciding? (Delete / Archive / Open PR / Keep)
> no
```

## Step 7 — verify and report

```
$ git branch --show-current            → main
$ git status --porcelain               → (empty)
$ git branch --merged main             → * main
$ git branch -r --merged origin/main   → origin/HEAD -> origin/main, origin/main
Re-check: none needed (no remote delete was skipped)

◆ Cleanup Report
Result:      PASS
Verified:    show-current → main; status --porcelain → empty; branch --merged main → main;
             branch -r --merged origin/main → origin/HEAD, origin/main; 0 ahead of origin/main
Unverified:  none (merged-PR check available)
Next:        No approval needed
··································································
  Scope:              full
  Branch:             main (0 ahead of origin/main)
  Changes reviewed:   5 (1 kept → wip/cleanup-2026-10-05, 2 discarded, 2 ignored/deferred, 0 left as is)
  Ignore file:        +2 patterns, committed on main and pushed
  Merged deleted:     feat/login (ancestry, 1a2b3c4); feat/filters (squash-tree, 5d6e7f8);
                      fix/readme remote (merged PR #57, 9a0b1c2)
  Skipped deletes:    none
  Unmerged kept:      feat/search-v2, spike/llm-cache, wip/cleanup-2026-10-05
  Protected skipped:  release/2.1
```

Had the user chosen branch+PR in Step 4, the run would have ended with `git switch main`,
`node_modules/` and `.env` would still show in `git status` on `main`, and the report would open
`Result: PARTIAL — ignore rule pending in PR #58` with `Next: merge ignore PR #58`.
