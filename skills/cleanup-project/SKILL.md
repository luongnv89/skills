---
name: cleanup-project
description: "Prepare a git repo before new work: review uncommitted changes, fix .gitignore, delete merged branches, end on clean main, or inspect one branch before deciding. Don't use for dead code, commit-and-push, releases, LICENSE files, or git how-tos."
license: MIT
effort: high
metadata:
  version: 1.0.1
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Cleanup Project

Get a repository to a clean foundation before new work: every uncommitted change decided, ignore
files updated, merged branches deleted locally and on `origin`, and an up-to-date, clean `main`.

## When to use

- "Clean up this repo before I start the next feature."
- "Delete the branches that are already merged, local and remote."
- "My working tree is a mess. Help me decide what to keep and get back to main."
- "Tidy the .gitignore and get rid of stale branches."
- "Is `spike/llm-cache` worth keeping?" This goes straight to the single-branch drill-down (Step 6).

Don't use it to remove dead code or unused imports (`code-review` mode:cleanup), commit and
push everything (`auto-push`), cut a release or tag (`release-manager`), or add LICENSE, CONTRIBUTING and other OSS
files (`oss-ready`). For a git how-to question ("`branch -d` vs `-D`?"), answer it directly and run
no workflow.

## Inputs

- **Base branch.** `main` by default. If the repo has no `main`, ask once which branch is the base
  (`master`, `develop`, `trunk`) and use that answer everywhere this skill says `main`.
- **Remote.** `origin` by default. If `git remote` lists no `origin`, ask once: use another remote
  (by name), or run local-only. Use that answer everywhere this skill says `origin`. Local-only
  means no fetch, no pull, no push, and no remote delete; the report says `local-only`.
- **Scope.** Infer it from the request, then confirm it once in one line
  (`Scope: sweep (Steps 1, 3, 5, 6, 7). OK?`).

| Scope | Example request | Steps |
|---|---|---|
| full (default) | "clean up this repo before the next feature" | 1–7 |
| review | "help me decide what to keep in my working tree" | 1, 2, 3, 7 |
| ignore | "fix the .gitignore" | 1, 3, 4, 7 |
| sweep | "delete the merged branches" | 1, 3, 5, 6, 7 |
| report-only | "which branches are merged? don't touch anything" | 1, Step 5 up to the table, Step 6 list |
| drill-down | "is `spike/x` worth keeping?" | 1, then Step 6 drill-down for that branch |

Step 1 always runs. Steps 3 and 7 run in every scope except report-only and drill-down.
Report-only never switches, pulls, discards, or deletes. Residue left by a phase outside the
scope is reported `— skipped by user` and does not make the run PARTIAL. Per-scope details:
`references/scopes-and-results.md`.

## Prerequisites

Check these before Step 1. If one fails, stop and print the report as `BLOCKED — <failed check>`.

- `git rev-parse --git-dir` succeeds (inside a git repository).
- The base branch resolves: `git rev-parse --verify main` or `origin/main`, or a confirmed base.
- No operation is in progress: `git rev-parse -q --verify` fails for `MERGE_HEAD`, `REBASE_HEAD`,
  `CHERRY_PICK_HEAD` and `REVERT_HEAD`, and `test -d "$(git rev-parse --git-path rebase-merge)"`
  fails, as does the same for `rebase-apply` (never test a literal `.git/...` path: in a linked
  worktree `.git` is a file). Never "clean" through a conflict.

## Repo Sync Before Edits (mandatory)

This skill syncs first, but not with the usual stash → pull → pop:

```bash
git fetch origin --prune        # refresh refs; the working tree is untouched
```

Do **not** stash or pull before Step 2: a stash hides the state the user must review, and a pull
into a dirty tree can conflict before anything is decided. The pull happens in Step 3.
If the fetch fails, show the error and ask once: continue local-only, or stop
(`BLOCKED — fetch failed`). With no `origin`, the Inputs answer applies instead.

## Rules for every destructive step

1. **List → explicit confirm → execute.** Show the exact commands with real names. A "no", or
   silence, means nothing runs.
2. If the user confirms only part of a list ("yes except `feat/x`"), re-show the edited list and
   take a fresh yes.
3. If a command fails, stop that plan and report the error. Never retry with force or a stronger
   flag (`-D` for `-d`, `--force`, `--ignore-other-worktrees`).
4. **Protected branches** are never deleted, renamed, or force-pushed: `main`, `master`,
   `develop`, `trunk`, `release/*`, the current branch, and any branch in a
   `branch refs/heads/<b>` line of `git worktree list --porcelain`. If the user asks to delete
   one, refuse and name the rule. For a worktree branch, tell them to run `git worktree remove
   <path>` first.

## Workflow

### 1. Fetch and snapshot

1. Run the sync above.
2. Record the current branch (or detached HEAD), base, `git status --porcelain=v1 -z`, and
   `git worktree list --porcelain`. If `main` is checked out in another worktree and Step 3 is in
   scope, warn now that the run will stop BLOCKED at Step 3, before any Step 2 plan is confirmed.
3. Run `gh auth status`. It decides whether the merged-PR signal is available (not a stop
   condition).
4. If HEAD is detached, run `git log HEAD --not --branches --remotes --oneline`. If it prints
   commits, report them and offer `git switch -c <name>` to keep them (in report-only and
   drill-down, report them only).

### 2. Review each uncommitted change

1. Parse `git status --porcelain=v1 -z` (NUL-separated, so paths with spaces and both paths of a
   rename survive).
2. If there are more than 20 entries, show a grouped summary (by directory and status) and
   offer one decision per group. Show full diffs on request. You may propose groups; never infer
   a decision from them.
3. Show each entry with its status code and diff. If the path is secret-like (`.env*`, `*.pem`,
   `*.key`, `*.p12`, `id_rsa*`, `credentials*`), show only its name and size, never its content
   or diff, and print `⚠ secret-like: <path>`.
4. Ask: `keep (commit to wip/cleanup-<date>) / keep on disk + ignore / stash / leave as is /
   discard`. Offer `keep on disk + ignore` only for an untracked path and only when Step 4 is in
   scope; it defers the path to Step 4. For a secret-like or local-config path, the offered
   default is `keep on disk + ignore` when that option is offered, and `leave as is` otherwise.
   Never default-commit a secret-like path.
5. After every entry has been asked, list the entries still without an answer and ask once:
   "leave these untouched?". Only an explicit leave or skip makes an entry undecided.
6. Show the consolidated plan (`references/action-plans.md` B) and take one yes. Nothing runs
   before that yes.
7. On yes, run the discards first: `git restore --staged --worktree -- <path>` (tracked), or
   `git clean -n -- <path>` then `git clean -f -- <path>` (untracked), with each path
   single-quoted and `git --literal-pathspecs`. Run `-f` only if the dry run names exactly the
   decided paths; otherwise stop and report. Never run bare `git clean -fd`.
8. Then commit the kept paths: `git switch -c wip/cleanup-<date>`, `git add -- <kept>`,
   `git commit -m "<msg>" -- <kept>` (the pathspec keeps other staged entries out); then run any
   stash. Commit on `main` only if the user
   explicitly asks.

Commands per status code, the stash form and the large-tree format:
`references/uncommitted-review.md`.

### 3. Switch to an up-to-date main

1. Check `git worktree list --porcelain`. If a `branch refs/heads/main` line belongs to another
   worktree, stop and print the report as `BLOCKED — main checked out at <path>; run
   /cleanup-project there`.
2. If HEAD is detached, re-run `git log HEAD --not --branches --remotes --oneline`. If it still
   prints N commits and the user declined a branch, require the explicit answer "abandon these N
   commits" before switching. Without it, stop: `BLOCKED — N commits on no branch`.
3. Run `git switch main`. If git refuses because a change would be overwritten, name the path
   and ask once: commit it to the wip branch, stash it, or discard it. If it stays undecided,
   stop: `BLOCKED — main not reached: <path> undecided`. Do not loop back to Step 2.
4. Run `git pull --ff-only`. If it refuses because local `main` diverged, show
   `git log --oneline origin/main...main` and ask: continue without the pull, or stop
   (`BLOCKED — main diverged`). Never reset or force.
5. Run `git rev-list --count origin/main..main` and record `N ahead of origin/main`. Commits only
   on local `main` never qualify a remote ref as merged in Step 5.

### 4. Update the ignore files

1. Collect evidence: untracked artifacts and `keep on disk + ignore` paths from Step 2 (or from
   the Step 1 snapshot when Step 2 is out of scope; every untracked non-artifact path then counts
   as kept), plus tracked files that already match a rule (`git ls-files -ci --exclude-standard`).
2. Test the proposed patterns against every kept path (committed, stashed, or left as is): write
   them to a temp file and run `git -c core.excludesFile=<tmp> check-ignore --no-index -v --
   <kept paths>`. If one matches, narrow or drop the pattern. `keep on disk + ignore` paths are
   exempt.
3. For each secret-like path, print `⚠ secret-like: <path>` above the diff. If it is tracked, add
   that ignoring does not remove it from history and the secret should be rotated.
4. Show the full `.gitignore` diff and ask to apply it.
5. If approved, apply it and re-run `git status --porcelain`. Expect every covered path to be
   gone. If one remains, show `git check-ignore -v -- <path>` and fix the pattern.
6. Ask `Commit on main? [yes / branch+PR / no]` and follow `references/action-plans.md` C (its
   untrack variant for approved `git rm --cached -- <p>` paths: no pathspec on the commit). Pushing
   `main`, or pushing the PR branch and opening the PR, each needs its own yes. Branch+PR ends
   with `git switch main`; it and a declined commit make the result PARTIAL.
7. If a deferred path is not covered by a pattern applied on `main`, ask `commit to wip / stash /
   leave as is / discard` for it here (`references/ignore-patterns.md`). After branch+PR, report
   those paths under `ignore rule pending in PR #N` instead. Steps 2 and 3 do not repeat.

Candidate patterns and the tracked-but-ignored flow: `references/ignore-patterns.md`.

### 5. Sweep merged branches (local and origin)

Build candidates from local branches and `origin/*`, excluding `origin/HEAD`, `origin/main` and
protected branches. Test a local `<b>` against `main` and `origin/<b>` against `origin/main`
(see `references/merged-detection.md`). A branch is **merged** if any signal holds:

1. **Ancestry**: `git merge-base --is-ancestor <b> main` (or `git branch --merged main`).
2. **Patch equivalence**: `git cherry main <b>` prints only `-` lines, or the squash-tree check
   (a temporary commit of the branch tree on its merge-base) prints `-`.
3. **Merged PR**: `gh pr list --head <b> --state merged` returns a PR with base `main` whose
   `headRefOid` equals the branch tip. A tip that moved after the merge means unmerged new work.

Signals 2 and 3 are the **squash evidence**. If `gh` is unusable or any `gh pr list` call fails
(including a non-GitHub remote), signal 3 is unavailable for the run: record it under
`Unverified:` and continue with signals 1 and 2. This is not a Rule 3 stop and not PARTIAL.

1. Show the full candidate table (`references/action-plans.md` A). A new candidate found later
   needs its own confirmation.
2. In report-only scope, list a merged current branch as `current, not deletable`, then stop
   and go to the Step 6 list.
3. Take **one** explicit confirmation for the whole table.
4. Each side is deleted only on its own signal (local `<b>` vs `main`, `origin/<b>` vs
   `origin/main`); a side without one goes to Step 6. Locally, run `git branch -d <b>` when
   ancestry holds, or `git branch -D <b>` only with squash evidence (`-d` refuses those).
5. For a proven `origin/<b>`, run `git push --force-with-lease=refs/heads/<b>:<sha> origin :refs/heads/<b>`, where
   `<sha>` is the recorded tip. If `origin/<b>` moved, git rejects it as `stale info`: report the
   row as skipped with that reason.
6. Run `git fetch origin --prune`.

### 6. Report unmerged branches

1. List the unmerged branches with ahead/behind counts and last commit date. Do not delete them.
2. In report-only scope, offer only the read-only overview (never a plan from `action-plans.md`
   D), then print the report.
3. In every other scope, offer the per-branch drill-down. For a branch the user picks, build the
   overview from `references/overview-fields.md`.
4. Ask Delete / Archive / Open PR / Keep, then follow the matching plan in
   `references/action-plans.md` D.
5. In drill-down scope, skip items 1 and 2. If the named branch is merged, show its signal and
   offer the Step 5 delete for that one row. Otherwise run items 3 and 4 for it.

### 7. Verify the end state

```bash
git branch --show-current                 # expect: main
git status --porcelain                    # expect: empty
git branch --merged main                  # expect: only main and protected branches
git branch -r --merged origin/main        # expect: only origin/main, origin/HEAD and protected branches
```

1. Run the four checks. If one prints something else, report `× <check>: <observed>`; the result
   is then not PASS. If that leftover comes from a phase outside the scope, report it
   `— skipped by user` instead; it does not affect the result.
2. For each branch deleted locally whose remote delete was skipped, re-run the merge signals
   (ancestry, then squash evidence) on `origin/<b>` against `origin/main`. Report
   `re-check origin/<b>: still merged (<signal>)` or `re-check origin/<b>: not merged`. A ref
   that still qualifies needs a new table row and a new confirmation; one that does not is
   listed as `remote kept — unproven`.
3. If `main` is ahead of `origin/main`, report `N ahead of origin/main`. Ask to push only if the
   user did not already decline it in Step 4; otherwise name it under `Next:`.
4. Print the final report.

## Results

Each result applies to the steps in scope (`references/scopes-and-results.md`).

- **PASS**, for the checks in scope: on `main`, `git status --porcelain` empty, and no
  unprotected merged branch left locally or on `origin`. `main` ahead of `origin` with the push
  declined is allowed and named under `Next:`.
- **PARTIAL — reason**: residue remains. Residue is anything that keeps the end state from PASS
  inside the scope: something the user chose (a stash, a change left as is, a declined discard,
  table row or ignore commit, an unmerged ignore PR) or a skipped or `stale info` delete. Name
  each item with its reason; join several with `; `.
- **BLOCKED — stop point**: the run stopped at a prerequisite, at Step 3, or on an error.

A step with nothing to do reports `√ pass (none needed)`.

## Step Completion Reports

After each step, emit a short `◆ Cleanup (step N of 7 — <name>)` block with one line per check:
`√ pass (<evidence>)`, `× fail (<reason>)`, or `— skipped by user`. The template and the check
names per step are in `references/scopes-and-results.md`.

## Expected output

After the per-step blocks, a run ends with a final report that opens with the result:

```
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

Field rules (`Unverified:` and `Next:` values): `references/scopes-and-results.md`. A full worked
run: `references/example-output.md`.

## Acceptance Criteria

A run is correct when all of these hold:

- `git fetch origin --prune` ran before any ref was read; nothing was stashed before Step 2.
- Every uncommitted change in scope got an explicit decision; no secret-like content was printed
  or committed by default.
- The ignore diff was shown before it was applied; no kept path was ignored.
- Every deleted branch had recorded merge evidence; `-D` was used only with squash evidence.
- Destructive steps followed the rules above; protected branches were never deleted.
- The run ended on `main` with `git status --porcelain` empty and no unprotected merged branch
  left locally or on `origin`, or it reported PARTIAL or BLOCKED with the reason.

The report must also be understandable:

- The first line after the header gives PASS, PARTIAL or BLOCKED and the reason.
- `Verified:` (checks run and their output) is separate from `Unverified:`.
- Each deleted ref names its signal and its sha or PR number.
- `Next:` names the remaining user action or says `No approval needed`.

These are instruction checks. Without reviewer feedback, human understanding of the report stays
unconfirmed; agent inspection cannot confirm it.

## Edge Cases

- **Local-only branch.** No remote delete; the table shows `local`.
- **Archive with differing tips.** See `references/action-plans.md` D before the lease delete.
- **User declines everything.** Change nothing and print the report as PARTIAL.

## Notes

- **Context budget.** In the drill-down, if `git diff --shortstat main...<b>` reports more than
  1000 changed lines, summarize the diff with a subagent instead of reading it into the main
  context (`references/overview-fields.md`).
