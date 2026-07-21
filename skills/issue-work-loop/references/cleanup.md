# Cleanup — /issue-work-loop

Mandatory **Phase 6** after the review loop ends (CLEAN, MAX_ROUNDS, FAILED with a known PR, or ALREADY_RESOLVED with an open PR). Goal: a **clean workspace** so the human only reviews the PR URL and merges. Never merge. Never close the root orchestrator pane.

Leading words:

- **SWEEP** — tear down worker panes + remove loop worktrees + return main repo to default branch
- **USER-MERGE** — PR stays open on remote; human merges later

## When SWEEP runs

| Outcome | SWEEP |
|---------|-------|
| CLEAN | Yes (full) |
| MAX_ROUNDS | Yes (full) — still leave PR for human decision |
| FAILED after PR exists | Yes (full) |
| FAILED before PR / before workers | Partial: only close any panes this run spawned |
| ALREADY_RESOLVED (no workers / no worktree) | Partial: no-op or prune only if this run created workers |

Always SWEEP even when FINDINGS remain — the point is a clean **local** workspace, not a clean review.

Do **not** ask for confirmation before SWEEP. The skill owns the panes and worktrees it created; leaving them is the exception, not the default.

## Order (strict)

1. Record handoff facts first (PR URL, branch, head SHA, verdict, FINDINGS) — cleanup must not erase what you need to report.
2. Tear down **worker panes** (implementer, reviewer, and any FRESHEN renames from this run).
3. Remove **git worktrees** for the PR branch created/used by this loop.
4. Reset **main repo workspace** to default branch, clean tree.
5. Print SWEEP report + final USER-MERGE summary.

If a step fails, print the matching error/warning, continue remaining safe steps, and mark SWEEP `PARTIAL` in the final report. Never abort past handoff facts — the user still needs the PR URL.

---

## Step A — Tear down worker panes

Close only panes this skill spawned (tracked `impl-*` / `rev-*` pane ids for issue `{N}`). Never close `root_pane` / `$HERDR_PANE_ID`.

```bash
# for each worker pane_id recorded during the run:
herdr pane close "$worker_pane" 2>/dev/null || true
```

If a name still appears in `herdr agent list` after close, try resolving pane id again and close once more. Do not `herdr server stop`. Do not close the whole tab/workspace.

After closes, optional equalize is unnecessary (root alone is fine).

Report:

```
  Panes:             √ closed impl-{N}, rev-{N}
```

or

```
  Panes:             ⚠ partial — could not close {pane_id} ({reason})
```

---

## Step B — Remove loop worktrees

Discover worktrees linked to the PR branch (and common issue-resolver sibling layouts):

```bash
repo_root="$(git rev-parse --show-toplevel)"
# Resolve default branch — the fallback must live outside the pipeline
# (`... | sed ... || echo main` never fires: sed exits 0 on empty input).
default_branch="$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##')"
[ -n "$default_branch" ] || default_branch=main
pr_branch="{branch_name}"   # from loop state; empty if unknown

git worktree list --porcelain
```

**Candidates to remove** (all must match):

1. Path is **not** `$repo_root` (never remove the primary worktree).
2. Worktree branch equals `{pr_branch}`, **or** path matches common patterns for this issue:
   - `*/{repo}-worktrees/*{N}*`
   - `*/wt-{N}*`
   - path basename contains the branch with `/` → `-`
3. Prefer worktrees whose `HEAD` commit is an ancestor of / equal to the PR head when branch name is missing.

For each candidate path `$wt`:

```bash
# Ensure no worker still has cwd inside $wt (panes already closed in Step A)
git -C "$repo_root" worktree remove "$wt" --force 2>/dev/null \
  || { git -C "$repo_root" worktree prune; git -C "$repo_root" worktree remove "$wt" --force; }
```

Verify gone:

```bash
git -C "$repo_root" worktree list --porcelain | grep -F "worktree $wt" && echo STILL_PRESENT
```

If still present → `⚠` + recovery line from `references/error-messages.md` → *Worktree remove failed*; continue.

**Do not** `git branch -D {pr_branch}` while the PR is open — remote branch must stay for USER-MERGE. Local branch tip may remain as a ref after worktree remove; that is fine.

Report paths removed or `○ none`.

---

## Step C — Reset main repo workspace

Run in `$repo_root` (orchestrator project dir):

```bash
cd "$repo_root"
default_branch="$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##')"
[ -n "$default_branch" ] || default_branch=main

# Leave the PR branch if checked out here
if [ "$(git rev-parse --abbrev-ref HEAD)" != "$default_branch" ]; then
  dirty=0
  if [ -n "$(git status --porcelain)" ]; then
    git stash push -u -m "issue-work-loop: pre-cleanup stash before return to ${default_branch}"
    dirty=1
  fi
  git checkout "$default_branch"
fi

git fetch origin
git pull --rebase origin "$default_branch" || {
  git rebase --abort 2>/dev/null || true
  echo "⚠ could not rebase ${default_branch} — left on branch, user should sync"
}

# Drop loop-only uncommitted junk on default branch only when status is dirty
# from worker residue (never discard the pre-cleanup stash of user work)
if [ -n "$(git status --porcelain)" ]; then
  # Prefer stash over hard reset when unsure — preserve user data
  git stash push -u -m "issue-work-loop: residual dirty tree after cleanup"
fi
```

**Done bar (checkable):**

```bash
test "$(git rev-parse --abbrev-ref HEAD)" = "$default_branch"
test -z "$(git status --porcelain)"
# optional: no worktree still on pr_branch
! git worktree list --porcelain | grep -q "branch refs/heads/${pr_branch}$"
```

If dirty only because of an intentional user stash from pre-sync, report stash refs; tree can still be clean.

**Forbidden:** `git push --force`, deleting `origin/{pr_branch}`, `gh pr close`, `gh pr merge`, `git reset --hard` on default without a recoverable stash when the dirty files might be user work.

---

## Step D — SWEEP report

```
◆ SWEEP (cleanup)
··································································
  Worker panes:       √ closed | ⚠ partial | ○ none spawned
  Worktrees removed:  √ {paths} | ○ none | ⚠ partial
  On default branch:  √ {default_branch} | × still on {branch}
  Working tree:       √ clean | ⚠ stashed residual | × dirty
  Criteria:           √ N/M met
  Result:             PASS | PARTIAL | FAIL
```

Then print the final USER-MERGE summary from `references/output-format.md` (includes cleanup lines).

---

## Tracking state during the run

Maintain in orchestrator memory (not a required on-disk file):

```
spawned_panes: [{name, pane_id}, ...]
pr_branch: ...
pr_number: ...
worktree_paths_seen: [...]   # from implementer report or git worktree list mid-run
```

If implementer reports a worktree path in its structured output, record it. At SWEEP, re-scan `git worktree list` rather than trusting memory alone.

---

## Interaction with FRESHEN

Mid-loop FRESHEN may close and re-open panes — track the **current** pane ids. SWEEP closes whatever is current at end, plus any orphan pane ids still listed under `impl-{N}*` / `rev-{N}*` names for this issue if safe to attribute.

---

## Failure matrix

| Failure | Continue? | Report |
|---------|-----------|--------|
| Pane close fails | Yes | ⚠ partial panes |
| Worktree remove fails | Yes | ⚠ + recovery commands; do not delete remote branch |
| Cannot checkout default | Yes | × on-default-branch; leave instructions |
| Dirty tree cannot clean safely | Yes | stash residual; ⚠ |
| Root pane mistaken for worker | Never close | — |
