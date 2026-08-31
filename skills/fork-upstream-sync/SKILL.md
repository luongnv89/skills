---
name: fork-upstream-sync
description: "Sync a GitHub fork with upstream while keeping unmerged feature branches and open PRs mergeable. Use for rebase on upstream, PR conflicts, integration main. Don't use for git init, releases, or non-fork repos."
license: MIT
effort: medium
metadata:
  version: 1.3.3
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Fork Upstream Sync

**Integration main** means fork `main` = `upstream/main` plus your unmerged commits in linear history (not a merge commit that duplicates feature work).

## Prerequisites

Before selecting a path, validate all requirements:

- **Tools:** require Git 2.30+; require `gh` only for PR-state checks.
- **Access:** confirm authenticated fetch and push access to `origin`, plus fetch access to `upstream`.
- **State:** check that the working tree is clean or stashable and that the target branches are not checked out in another worktree.
- **Recovery:** record the current branch and SHA. If fetch, stash, rebase, reset, or push fails, stop at that command; never continue with stale assumptions.

## Branch selector

Pick one path per user request:

| Path | When |
|------|------|
| **A — Bootstrap** | No `upstream` remote yet, or first-time fork sync |
| **B — PR branch** | Open PR is `CONFLICTING` or `DIRTY`; rebase feature branch on `upstream/main` |
| **C — Integration main** | Fork `main` should match upstream plus same tip as feature branch |
| **D — Post-merge** | Upstream merged your PR; drop duplicate commits on fork `main` |

Paths B then C is the usual full sync (PR mergeable, fork `main` carries your WIP).

## Repo sync before edits (mandatory)

Before any rebase, reset, or force push:

```bash
git fetch upstream
git fetch origin
```

If the working tree is dirty:

```bash
git stash push -u -m "pre-sync: $(git rev-parse --abbrev-ref HEAD)"
# ...run the fetch/rebase/reset steps for the chosen path...
git stash pop
```

On `git stash pop` conflict, stop — the stash is preserved (`git stash list`); resolve manually before continuing.

If `upstream` is missing, `origin` is missing, or the user has not said which upstream org/repo to use, stop and ask. Never force-push `main` without `--force-with-lease`.

## Step completion reports

After each major phase, emit a short report with checks for upstream remote, commits behind upstream, PR mergeable status, conflicts resolved, and whether integration `main` matches the feature branch tip. End with Result PASS, FAIL, or PARTIAL.

---

## Path A — Bootstrap upstream remote

1. Confirm parent repo (for example `gh repo view --json parent,isFork`).
2. Add remote if absent: `git remote add upstream git@github.com:ORG/REPO.git`, then `git fetch upstream`.

**Done when:** `git rev-parse upstream/main` succeeds and `git remote -v` lists `upstream`.

---

## Path B — Rebase feature branch on upstream

1. Identify PR head branch and upstream base (`main`).
2. `git checkout <feature-branch>` then `git rebase upstream/main`.
3. On each conflict, resolve files. When upstream and your feature both added valid code, keep **both** (union), not either/or. If a conflict can't be confidently resolved, `git rebase --abort` and stop to ask the user rather than guessing.
4. `git add` resolved files, then `GIT_EDITOR=true git rebase --continue`.
5. For locale JSON conflicts, keep the rebased side then run the repo catalog fix if documented (for example `pnpm run sync:localization-catalog --fix`).
6. `git push origin <feature-branch> --force-with-lease`.
7. Verify with `gh pr view <n> --repo ORG/REPO --json mergeable,mergeStateStatus` (expect MERGEABLE; CI may lag).

**Done when:** rebase completes, no conflict markers in tree, PR is MERGEABLE or user accepts waiting on CI.

---

## Path C — Rebuild fork integration main

After Path B:

```bash
git checkout main
git reset --hard upstream/main
git merge --ff-only <feature-branch> && git push origin main --force-with-lease
```

If `--ff-only` fails, `main` is already reset to bare `upstream/main` — **do not push**. The feature branch is behind the new `upstream/main`; re-run Path B to rebase it, then retry this merge. Pushing here without the fast-forward would force-publish plain `upstream/main`, silently dropping your integration WIP from `origin/main`.

**Done when:** `upstream/main` is ancestor of `main`, `main` SHA equals feature branch SHA, and ahead count matches your feature commits.

---

## Path D — Post-merge cleanup

When upstream `main` already contains your merged PR:

```bash
git fetch upstream
git checkout main
git reset --hard upstream/main
git push origin main --force-with-lease
```

**Done when:** `main` SHA equals `upstream/main` SHA.

---

## Verify with the command reference

Protect the context budget: read `references/command-checks.md` only when executing or diagnosing a path. See that reference for the routine command sequence and exact SHA, ancestry, ahead-count, and clean-tree checks.

## What not to do

- Do not merge `upstream/main` into fork `main` with a merge commit while also keeping a parallel rebased feature branch.
- Do not force-push without `--force-with-lease`.
- Do not treat `origin` as upstream; `origin` is your fork, `upstream` is the parent.

## Acceptance criteria

Verify the selected path before reporting success:

- [ ] Required remotes resolve and the working tree has no unresolved conflicts.
- [ ] The expected branch ancestry or equality check for the selected path passes.
- [ ] Every push used `--force-with-lease`; no destructive push targeted the wrong branch.
- [ ] For Path B, the PR response is `MERGEABLE`, or CI delay is explicitly reported as partial.

Run:

```bash
git log --oneline -1 upstream/main main <feature-branch>
git rev-list --count upstream/main..main
git merge-base --is-ancestor upstream/main main
```

**Expected output:** the log identifies the intended tips, the ahead count equals the retained feature commits, and the ancestry command exits 0. For Paths C and D, also assert the exact SHA equality required by that path.

## Edge cases

- **Renamed default branch:** discover it with `gh repo view --json defaultBranchRef`; do not assume `main`.
- **Protected fork branch:** if GitHub rejects a lease-protected push, stop and report the protection rule; do not weaken it.
- **Deleted PR branch:** recreate only from a verified local or remote SHA after user confirmation.
- **Upstream rewrote history:** fetch, compare old and new tips, and ask before rebasing or resetting across the rewrite.
