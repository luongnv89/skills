# Repo Sync for an output directory inside a git worktree

Read this only when the output directory must be inside a git worktree. An external output
directory needs no sync, and an inspection-only run never syncs, stashes or otherwise
mutates the target checkout. `$repo` is the worktree that will hold the output.

1. Ask the user to confirm the synchronization. Without that confirmation, select an
   external output directory and skip the remaining steps.
2. Inspect `git -C "$repo" status` and `git -C "$repo" remote -v`.
3. If the worktree is dirty, ask permission to stash including untracked work. With it, run
   `git -C "$repo" stash push -u`; without it, select an external output directory.
4. Sync **before collecting evidence**, then audit the synced revision:

```bash
branch="$(git -C "$repo" rev-parse --abbrev-ref HEAD)"
git -C "$repo" fetch origin && git -C "$repo" pull --rebase origin "$branch" \
  || { git -C "$repo" rebase --abort 2>/dev/null; echo "sync failed: stop and ask" >&2; }
```

5. If you stashed, run `git -C "$repo" stash pop`, also after an aborted sync.
6. If `origin` is absent, the branch cannot be synced, or the rebase conflicts, stop and ask
   before writing there.
7. Disclose the approved synchronization in `Scope and Evidence`, separately from the
   audit's evidence records.

The checkout snapshot in workflow step 1 is taken after this sync, so the before/after
comparison covers the synced revision.
