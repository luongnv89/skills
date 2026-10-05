---
name: cleanup-project
description: "Prepare a git repo for new work: review each uncommitted change, update ignore files, delete merged branches locally and on origin, end on clean main. Don't use for commit-and-push (auto-push), OSS prep (oss-ready), or releases (release-manager)."
license: MIT
effort: high
metadata:
  version: 1.0.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Cleanup Project

Get a repository to a clean foundation before starting new work. A complete run reviews every
uncommitted change with the user, updates the ignore files, deletes the branches already merged
into `main` (locally and on `origin`), and ends on an up-to-date `main` with nothing uncommitted.

Every destructive step follows the same pattern: **list → explicit confirm → execute**. Nothing
is discarded, deleted, or pushed without the user's decision. This skill supersedes the older
single-branch `branch-inspector`; its per-branch inspect flow lives on as an optional drill-down.

## When to use

- "Clean up this repo before I start the next feature."
- "Delete the branches that are already merged, local and remote."
- "My working tree is a mess. Help me decide what to keep and get back to main."
- "Tidy the .gitignore and get rid of stale branches."

Don't use it to commit and push everything (`auto-push`), add OSS files such as LICENSE or
CONTRIBUTING (`oss-ready`), or cut a release or tag (`release-manager`).

## Inputs

- **Base branch.** `main` by default. If the repo has no `main`, ask once which branch is the base
  (`master`, `develop`, `trunk`) and use that answer everywhere this skill says `main`.
- **Remote.** `origin` by default. If there is none, the run is local-only (see Edge cases).
- **Optional scope.** The user may skip a phase ("only the branches"). Report skipped phases as
  `— skipped by user`, never as PASS.

## Prerequisites

Check these before anything else. Stop and tell the user if one fails.

- `git rev-parse --git-dir` succeeds (inside a git repository).
- The base branch resolves: `git rev-parse --verify main` or `origin/main`, or a confirmed base.
- No operation is in progress: `git rev-parse -q --verify MERGE_HEAD`, `REBASE_HEAD`,
  `CHERRY_PICK_HEAD`, and `REVERT_HEAD` all fail, and `.git/rebase-merge`/`.git/rebase-apply` are absent.
  If one is in progress, stop and ask the user to finish or abort it first. `git restore` on a
  conflicted path exits 0 but leaves the merge open, so never "clean" through a conflict.
- `gh` is optional. `gh auth status` decides whether the merged-PR signal is available.

## Repo Sync Before Edits (mandatory)

This skill mutates the repository, so it syncs first, but in a deliberately different order from
the standard stash → pull → pop pattern:

```bash
git fetch origin --prune        # refresh refs; the working tree is untouched
```

Do **not** stash or pull before Step 2. A stash would hide the exact uncommitted state the user
must review, and a pull into a dirty tree can conflict before anyone has decided what to keep.
The pull happens in Step 3, after every change has a decision and the tree is clean. If `origin`
is missing or the fetch fails, say so and continue local-only only with the user's agreement.

## Workflow

### 1. Fetch and snapshot

Run the sync above, then record the starting state: current branch (or detached HEAD), base,
`git status --porcelain=v1 -z`, `git worktree list --porcelain`, and whether `gh` is usable.

### 2. Review each uncommitted change

Parse `git status --porcelain=v1 -z` (NUL-separated, so paths with spaces and both paths of a
rename survive). Group entries by file and show each one with its diff (`git diff`, `git diff
--cached`, or the file's head for untracked files). For each change, ask: **keep or discard?**

- Accept a batch answer ("discard all of `tmp/`") only when the user explicitly gives one.
- **Keep** → a commit on a new branch (default, e.g. `wip/cleanup-<date>`), a named stash
  (`git stash push -u -m "<name>" -- <path>`), or a commit on `main` only with explicit consent.
- **Discard** → tracked: `git restore --staged --worktree -- <path>`; untracked: `git clean -n
  -- <path>` dry run, then delete that one path after the user confirms. Never run bare `git clean -fd`.
- Artifact-like untracked paths (`node_modules/`, `dist/`, `.DS_Store`, ...) may be deferred to
  Step 4 instead of being deleted one by one.
- A change with no answer stays untouched. Nothing is discarded without the user's decision.

Exact commands per status code (`A`, `D`, `R`, `MM`, `??`) are in `references/uncommitted-review.md`.

### 3. Switch to an up-to-date main

```bash
git switch main && git pull --ff-only
```

If the switch would overwrite a kept-but-uncommitted change, stop and return to Step 2. If
`--ff-only` refuses because local `main` diverged, show `git log --oneline origin/main...main` and
ask; never reset or force.

### 4. Update the ignore files

Propose patterns from evidence only: untracked artifacts seen in Step 2 (`node_modules/`, `dist/`,
`__pycache__/`, `.venv/`, `.DS_Store`, `*.swp`, `.env*`) and tracked files that already match an
ignore rule (`git ls-files -ci --exclude-standard`). Show the `.gitignore` diff, apply it only after
approval, then commit on `main` after a second explicit approval. The commit is local; pushing it
(`git push origin main`) is a separate choice that needs its own confirmation. Offer a `chore/`
branch plus PR instead, warning that the artifacts then stay visible on `main` until it merges.

- Never add a pattern that would hide a path the user chose to keep.
- Warn loudly on secret-like files (`.env*`, `*.pem`, `*.key`, `credentials*`): ignoring them
  does not remove them from history.
- Any untracked path not covered by an approved, applied pattern goes back to the Step 2 keep or
  discard decision.

Candidate patterns and the tracked-but-ignored flow: `references/ignore-patterns.md`.

### 5. Sweep merged branches (local and origin)

Build candidates from local branches and `origin/*`, excluding `origin/HEAD` and `origin/main`. A
branch is **merged** if any signal holds:

1. **Ancestry**: `git merge-base --is-ancestor <b> main` (or `git branch --merged main`).
2. **Patch equivalence**: `git cherry main <b>` prints only `-` lines, or the squash-tree check
   (a temporary commit of the branch tree on its merge-base) prints `-`. Plain `git cherry` only
   catches single-commit and rebase merges; the squash-tree check catches multi-commit squashes.
3. **Merged PR**: `gh pr list --head <b> --state merged --json number,baseRefName,mergedAt,headRefOid`
   returns a PR with base `main` whose `headRefOid` equals the branch tip. A tip that moved after
   the merge means new work, so the branch is unmerged.

Without `gh`, use signals 1 and 2 and say so in the report. Exact commands:
`references/merged-detection.md`.

**Protected, never deleted:** `main`, `master`, `develop`, `trunk`, `release/*`, the current
branch, and any branch checked out in a worktree (`git worktree list --porcelain`).

Show the full candidate table (branch, local or remote or both, signal, evidence, planned
command) and take **one** explicit confirmation for the whole table. Then run, per branch:

- `git branch -d <b>` when ancestry holds; `git branch -D <b>` only with squash evidence
  (signal 2 or 3), because `-d` refuses a squash-merged branch.
- `git push origin --delete <b>` for the remote side.

A failed delete is reported and skipped, never retried with force.

### 6. Report unmerged branches

List the branches that are not merged with their ahead/behind counts and last commit date. Do not
delete them. Offer the per-branch drill-down: build the overview from
`references/overview-fields.md`, then ask Delete / Archive / Open PR / Keep and follow the matching
confirm-then-execute plan in `references/action-plans.md`.

### 7. Verify the end state

```bash
git branch --show-current                 # expect: main
git status --porcelain                    # expect: empty
git branch --merged main                  # expect: only main and protected branches
git branch -r --merged main               # expect: only origin/main (and origin/HEAD)
```

Re-run the squash signals for any branch the sweep deleted locally but not remotely. Report any
local commits on `main` not yet on `origin` (an ignore commit, a kept change committed on `main`)
as `N ahead of origin/main`; push only if the user confirms. Print the final report. If residue remains because the user chose it (a declined discard, a kept stash, an
unmerged ignore PR), the result is **PARTIAL** with the reason, never PASS.

## Step Completion Reports

After each step, emit a short block in this shape:

```
◆ Cleanup (step 5 of 7 — merged-branch sweep)
··································································
  Candidates listed:  √ pass (4 local, 3 remote)
  User confirmation:  √ pass (one confirmation for the table)
  Deleted:            √ pass (6 refs, 0 failures)
  Protected skipped:  √ pass (main, release/2.1, worktree feat/wip)
  ____________________________
  Result:             PASS
```

Use `× fail` with the reason for a failed check and `— skipped` for a phase the user skipped.

## Expected output

A full run produces, in order: the change-by-change review with a keep or discard decision for
each; the switch-and-pull result; the proposed `.gitignore` diff and its commit; the merged-branch
candidate table with evidence; the unmerged list with the drill-down offer; and a final report:

```
◆ Cleanup Report
··································································
  Branch:             main (up to date with origin/main)
  Working tree:       clean
  Changes reviewed:   5 (2 kept → wip/cleanup-2026-10-05, 3 discarded)
  Ignore file:        +3 patterns, committed (chore: ignore build artifacts)
  Merged deleted:     4 local, 3 remote (1 via squash-tree, 1 via merged PR)
  Unmerged kept:      feat/search-v2, spike/llm-cache
  Protected skipped:  release/2.1
  ____________________________
  Result:             PASS
```

A full worked run is in `references/example-output.md`.

## Acceptance Criteria

A run is correct when all of these hold:

- `git fetch origin --prune` ran before any ref was read, and nothing was stashed before Step 2.
- Every uncommitted change was shown and got an explicit keep or discard decision; nothing was
  discarded without one.
- The ignore-file diff was shown before it was applied and committed with approval; no kept path
  was ignored.
- Every deleted branch had recorded merge evidence; `-D` was used only with squash evidence.
- Destructive steps followed list → explicit confirm → execute; protected branches were never
  deleted.
- The run ended on `main` with `git status --porcelain` empty and no merged branch left locally or
  on `origin`, or it reported PARTIAL with the reason.

## Edge Cases

- **No `main`.** Ask once for the base and use it throughout.
- **No `gh` or not authenticated.** Skip signal 3, state "merged-PR check unavailable", and keep any
  branch that only `gh` could have proven merged.
- **Squash-merged branch.** Ancestry fails and `-d` refuses; delete with `-D` only on signal 2 or 3.
- **PR merged, branch advanced after.** `headRefOid` differs from the tip: treat as unmerged.
- **Remote-only branch.** Run the signals on `origin/<b>`; delete with `git push origin --delete <b>`.
- **Local-only branch.** No push; note `remote=no`.
- **Detached HEAD.** Report the commit, offer to keep it on a new branch, then switch to `main`.
- **No `origin`.** Local-only run: no fetch, no pull, no remote deletes; say so in the report.
- **Branch checked out in a worktree.** Protected; tell the user to remove the worktree first.
- **Conflict on switch.** `git switch main` refuses because a kept change would be overwritten:
  go back to Step 2 and commit or stash it.
- **Merge or rebase in progress.** Stop at Prerequisites; never restore through a conflict.
- **User declines everything.** Change nothing, print the report as PARTIAL, and stop.
- **Branch identical to `main`.** Merged by ancestry; delete with `-d`.

## Notes

- **Don't trust branch names.** `fix/typo` is not proof of anything; only the signals count.
- **One confirmation per table, not per command.** The user sees every ref before confirming, so a
  single yes is informed; a new candidate discovered later needs a new confirmation.
- **Context budget.** For a large unmerged branch in the drill-down, summarize the diff with a
  subagent instead of reading it all into the main context.
