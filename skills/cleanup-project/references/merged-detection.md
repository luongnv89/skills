# Merged-Branch Detection

How Step 5 decides that a branch is merged into the base (`main` below), for local branches and
for `origin/<b>`. A branch is a deletion candidate when **any** signal holds. Record which one,
with its evidence, in the candidate table.

## Build the candidate list

```bash
git fetch origin --prune
git for-each-ref --format='%(refname:short)' refs/heads/            # local
git for-each-ref --format='%(refname:short)' refs/remotes/origin/   # remote
```

Drop from both lists before testing:

- `origin/HEAD` (its short name prints as `origin`) and `origin/main`.
- Protected names: `main`, `master`, `develop`, `trunk`, `release/*`.
- The current branch (`git branch --show-current`).
- Any branch in a `branch refs/heads/<b>` line of `git worktree list --porcelain`.

Pair `feat/x` with `origin/feat/x` so the table shows one row per branch with
`local` / `remote` / `both`. Test each side on its own ref: a local branch that has new commits
the remote lacks is not proven merged by the remote's evidence.

## Signal 1: ancestry (true merge or fast-forward)

```bash
git merge-base --is-ancestor <ref> main && echo merged
# list form:
git branch --merged main
git branch -r --merged main
```

Ancestry proves the branch tip is reachable from `main`. `git branch -d` accepts these.

## Signal 2: patch equivalence (rebase or squash merge)

Per-commit form, which catches single-commit squashes and rebase merges:

```bash
git cherry main <ref>      # every line starts with '-' => all commits already on main
```

A multi-commit branch squashed into one commit shows `+` lines here, because no single commit
on `main` matches any one branch commit. Use the squash-tree check for that case:

```bash
base="$(git merge-base main <ref>)"
tmp="$(git commit-tree "<ref>^{tree}" -p "$base" -m squash-check)"
git cherry main "$tmp"     # a single '-' line => the branch's whole diff is on main
```

`git commit-tree` writes only a dangling commit object. It creates no ref, does not touch the
working tree or index, and `git gc` removes the object later. Verified on a scratch repo: a
2-commit branch squash-merged into `main` prints `+ +` with plain `git cherry` and `-` with the
squash-tree check; an unmerged branch prints `+` with both.

Limitation: if `main` changed the same lines after the squash, the patch no longer matches and
the check reports `+`. That is a false "unmerged", which is the safe direction; use signal 3.

## Signal 3: merged pull request (needs `gh`)

```bash
gh pr list --head <b> --state merged \
  --json number,baseRefName,mergedAt,headRefOid --limit 20
```

Count it only when a returned PR has `baseRefName == "main"` **and** `headRefOid` equals the tip
being deleted (`git rev-parse <b>` or `git rev-parse origin/<b>`). A different OID means the
branch received commits after the merge, or the name was reused. Treat that branch as
**unmerged**, because `-D` would drop the new commits.

This is the load-bearing signal for squash merges that GitHub performed with conflict resolution,
where signal 2 can miss.

### No `gh`, or not authenticated

If `gh auth status` fails, skip signal 3. Use signals 1 and 2 only, and say so in the report:
`merged-PR check unavailable — squash merges detected by patch equivalence only`. A branch that
only a merged PR could prove stays in the unmerged list.

## Choosing the delete command

| Evidence | Local delete | Why |
|---|---|---|
| Signal 1 (ancestry) | `git branch -d <b>` | Git verifies the merge itself |
| Signal 2 or 3 only | `git branch -D <b>` | `-d` refuses a squash-merged branch (`error: the branch '<b>' is not fully merged`) |
| No signal | none | Unmerged: report it in Step 6 |

Remote side, for any branch with evidence on `origin/<b>`:

```bash
git push origin --delete <b>
```

All deletes run only after the single table confirmation. A failed delete (permissions, branch
protection, already gone) is reported and skipped, never retried with force. After the sweep,
`git fetch origin --prune` again and re-check that no merged ref remains.
