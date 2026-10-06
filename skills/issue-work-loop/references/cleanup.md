# Cleanup — /issue-work-loop

**SWEEP** runs before **USER-MERGE** on CLEAN, MAX_ROUNDS, and failures after workers/PR exist (unless `--no-cleanup`). It closes only this run's worker panes, removes only loop-created/non-primary PR worktrees, and returns the primary checkout to a clean default branch. Never merge or close the root pane.

## Mode-owned resources

| Mode | Panes | Worktrees |
|---|---|---|
| ISSUE | implementer + reviewer, including FRESHEN replacements | issue-resolver/implementer worktrees plus any reviewer-independent loop worktree |
| PR, CLEAN first review | reviewer only | none expected |
| PR, FINDINGS fixed | reviewer + lazily spawned FIXER | dedicated FIXER isolated worktree |
| Failure before spawn | none | none |

Do not assume an issue-resolver worktree exists in PR mode. Do not claim or close a FIXER pane that was never spawned.

## Strict order

1. Snapshot `mode`, PR URL/number, issue context, head branch/SHA, verdict, FINDINGS, spawned pane ids, and observed loop worktrees.
2. Close tracked worker panes.
3. Remove eligible loop worktrees.
4. Return primary checkout to default branch and a clean tree.
5. Verify and print the SWEEP report.
6. Release the dependency lease: `asm deps release --session "$iwl_session" --json`. This step also runs under `--no-cleanup` and on every stop. If it fails, record it under the final report's `Uncertainty:` line.
7. Print the USER-MERGE final report (`output-format.md` → *Final report contract*).

Continue safe cleanup after a partial failure. Preserve handoff facts.

## A — Close tracked worker panes

Close each current and orphaned FRESHEN replacement recorded by this run:

```bash
herdr pane close "$worker_pane" 2>/dev/null || true
```

Never close `root_pane`/`$HERDR_PANE_ID`, stop the Herdr server, or infer ownership solely from a broad name prefix. Re-query `herdr agent list` and require every tracked pane id to be absent.

Expected names:

- ISSUE: configured `impl-{N}` and reviewer, plus tracked FRESHEN variants.
- PR: configured reviewer and, only if spawned, `fix-{M}`, plus tracked FRESHEN variants.

## B — Remove loop worktrees

```bash
repo_root="$(git rev-parse --show-toplevel)"
default_branch="$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##')"
[ -n "$default_branch" ] || default_branch=main
pr_branch="{head_ref}"
git worktree list --porcelain
```

An eligible worktree must be outside `$repo_root` and attributable to this run by recorded path/pane report, exact PR branch, or ISSUE-mode issue-resolver path pattern. PR mode prefers the recorded isolated FIXER worktree; never sweep unrelated worktrees merely because no issue-resolver worktree exists.

For each eligible `$wt`:

```bash
git -C "$repo_root" worktree remove "$wt" --force 2>/dev/null \
  || { git -C "$repo_root" worktree prune; git -C "$repo_root" worktree remove "$wt" --force; }
```

Verify its path no longer appears in `git worktree list --porcelain`. Never remove the primary worktree, delete `origin/{head_ref}`, or delete/force-update the open PR branch. A local branch ref may remain.

## C — Reset primary checkout safely

```bash
cd "$repo_root"
default_branch="$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##')"
[ -n "$default_branch" ] || default_branch=main

if [ -n "$(git status --porcelain)" ]; then
  git stash push -u -m "issue-work-loop: pre-cleanup stash before sync of ${default_branch}"
fi

if [ "$(git rev-parse --abbrev-ref HEAD)" != "$default_branch" ]; then
  git checkout "$default_branch"
fi

git fetch origin
git pull --rebase origin "$default_branch" || {
  git rebase --abort 2>/dev/null || true
  echo "⚠ default-branch sync failed; inspect git status and git stash list"
}

if [ -n "$(git status --porcelain)" ]; then
  git stash push -u -m "issue-work-loop: residual dirty tree after cleanup"
fi
```

Never `reset --hard` uncertain user work. A recoverable stash is preferable.

## D — Demanding verification

```bash
test "$(git rev-parse --abbrev-ref HEAD)" = "$default_branch"
test -z "$(git status --porcelain)"
# every tracked worker pane id is absent from herdr agent list
# every recorded loop-created worktree path is absent from git worktree list --porcelain
# no non-primary worktree from this run checks out refs/heads/${pr_branch}
```

Report each check independently. `PASS` requires all applicable checks. A CLEAN-first PR run validly reports reviewer closed, FIXER not spawned, and no worktree. If a check fails, use `error-messages.md`, mark `PARTIAL`, and still print the PR handoff.

## State to track

```text
mode: ISSUE | PR
spawned_panes: [{role, name, pane_id}, ...]
pr_number, pr_url, head_ref, head_sha
issue_context: none | #N | #N,#K
worktree_paths_seen: [...]
fixer_spawned: true | false
```

Re-scan pane/worktree state at SWEEP; do not trust worker claims alone.

## Forbidden

- `gh pr merge`, auto-merge, `gh pr close`
- force-push or remote PR-branch deletion
- closing root pane/tab/workspace/server
- removing primary or unrelated worktrees
- claiming PR FIXER cleanup when no FIXER was spawned
- discarding user work without a recoverable stash
