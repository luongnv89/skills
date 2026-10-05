# Example Output — Full Run

A worked `/cleanup-project` run on a repo with a dirty tree, build artifacts, three merged
branches (one squash-merged), and two unmerged branches. User replies are marked `>`.

## Step 1 — fetch and snapshot

```
$ git fetch origin --prune
 - [deleted]  (none)
Start: branch feat/search-v2, base main, 4 uncommitted entries, gh authenticated
```

## Step 2 — uncommitted review

```
1/4  M  src/search/index.ts   (+12 -3)
     @@ -40,7 +40,16 @@ export function rank(...)
     ...
     Keep or discard?
> keep

2/4  ??  debug.log   (3 KB, "TRACE rank() ...")
     Keep or discard?
> discard

3/4  ??  node_modules/   (1,284 files)
     Looks like a build artifact. Defer to the ignore step?
> yes

4/4  A  scratch.md   (new, staged, 8 lines)
     Keep or discard? Discarding deletes the file; it is not in HEAD.
> discard

Plan:
  keep     src/search/index.ts → commit on wip/cleanup-2026-10-05
  discard  debug.log           → git clean -n -- debug.log  ("Would remove debug.log"), then git clean -f -- debug.log
  discard  scratch.md          → git restore --staged --worktree -- scratch.md
  deferred node_modules/       → Step 4
Run this? [yes/no]
> yes
```

## Step 3 — switch and pull

```
$ git switch main && git pull --ff-only
Updating 4f2a91c..8c03d7e  Fast-forward
```

## Step 4 — ignore file

```
Evidence: node_modules/ untracked; git ls-files -ci --exclude-standard → (none)
--- a/.gitignore
+++ b/.gitignore
+node_modules/
+.DS_Store
Apply? > yes      (git status no longer lists node_modules/)
Commit on main as "chore: ignore node and macOS artifacts"? [yes / branch+PR / no]
> yes
Push main to origin now? [yes/no]
> yes
$ git push origin main
```

## Step 5 — merged-branch sweep

```
  branch          where   signal                         local        remote
  feat/login      both    ancestry                       branch -d    push --delete
  feat/filters    both    squash-tree cherry '-' (3 commits)  branch -D    push --delete
  fix/readme      remote  merged PR #57, headRefOid match    —            push --delete
Protected, skipped: main, release/2.1
Delete these 3 branches (5 refs)? [yes/no]
> yes
Deleted branch feat/login (was 1a2b3c4).
Deleted branch feat/filters (was 5d6e7f8).
To github.com:acme/app.git  - [deleted] feat/login  - [deleted] feat/filters  - [deleted] fix/readme
```

## Step 6 — unmerged

```
  feat/search-v2     6 ahead, 2 behind, last commit 1 day ago
  spike/llm-cache   14 ahead, 210 behind, last commit 143 days ago
  wip/cleanup-2026-10-05  1 ahead (kept work from Step 2)
Inspect one before deciding? (Delete / Archive / Open PR / Keep)
> no
```

## Step 7 — verify and report

```
$ git branch --show-current     → main
$ git status --porcelain        → (empty)
$ git branch --merged main      → * main
$ git branch -r --merged main   → origin/HEAD -> origin/main, origin/main

◆ Cleanup Report
··································································
  Branch:             main (up to date with origin/main)
  Working tree:       clean
  Changes reviewed:   4 (1 kept → wip/cleanup-2026-10-05, 2 discarded, 1 ignored)
  Ignore file:        +2 patterns, committed on main and pushed
  Merged deleted:     2 local, 3 remote (1 squash-tree, 1 merged PR)
  Unmerged kept:      feat/search-v2, spike/llm-cache, wip/cleanup-2026-10-05
  Protected skipped:  release/2.1
  merged-PR check:    available (gh)
  ____________________________
  Result:             PASS
```

Had the user chosen the branch+PR option in Step 4, `node_modules/` would still show in
`git status` on `main`, and the result would read `PARTIAL — ignore rule pending in PR #58`.
