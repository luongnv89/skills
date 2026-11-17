# Repo Sync for an output path inside a git worktree

Read this only when the `viral-evaluation.md` output path — `output-dir`, else the repo root,
else the current working directory — is inside a git worktree. An output path outside any git
repository needs no sync, and an inline-only run never syncs, stashes or otherwise mutates a
checkout. `$repo` is the worktree that will hold the report.

1. Ask the user to confirm the synchronization. Phase 3's single write confirmation covers
   this step when the need for a sync was named there. Without confirmation, write the report
   to a path outside the worktree instead and skip the remaining steps.
2. Inspect `git -C "$repo" status` and `git -C "$repo" remote -v`.
3. If the worktree is dirty, ask permission to stash including untracked work. With it, run
   `git -C "$repo" stash push -u -m "pre-viral-evaluation"`; without it, write outside the
   worktree.
4. Sync, then pop the stash, also after an aborted sync:

```bash
branch="$(git -C "$repo" rev-parse --abbrev-ref HEAD)"
git -C "$repo" fetch origin && git -C "$repo" pull --rebase origin "$branch" \
  || { git -C "$repo" rebase --abort 2>/dev/null; echo "sync failed: stop and ask" >&2; }
git -C "$repo" stash pop 2>/dev/null || true   # only when step 3 stashed
```

5. If `origin` is absent, the branch cannot be synced, or the rebase conflicts, stop and ask
   before writing there — or write outside the worktree with the user's agreement.
6. Disclose the approved synchronization in the report's caveats, separately from the
   product evidence.
