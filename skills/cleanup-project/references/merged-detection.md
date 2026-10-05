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
- Protected branches (SKILL.md, Rules for every destructive step), including the current branch
  (`git branch --show-current`) and worktree checkouts.

Pair `feat/x` with `origin/feat/x` so the table shows one row per branch with
`local` / `remote` / `both`. Test each side on its own ref: a local branch that has new commits
the remote lacks is not proven merged by the remote's evidence.

**Test each side against its own base.** Local `<b>` uses `main`; `origin/<b>` uses
`origin/main`. In signals 1 and 2 below, substitute that base for `main`. `git pull --ff-only`
exits 0 when local `main` is only ahead of `origin/main`, so a branch merged into local `main`
but not pushed would otherwise pass against local `main` and get its `origin` ref deleted while
`origin/main` still lacks the work. Local-only merges never qualify a remote ref. Signal 3
already uses the base on GitHub.

## Signal 1: ancestry (true merge or fast-forward)

```bash
git merge-base --is-ancestor <ref> <base> && echo merged   # <base>: main or origin/main
# list form:
git branch --merged main
git branch -r --merged origin/main
```

Ancestry proves the branch tip is reachable from `main`. `git branch -d` accepts these.

Signals 2 and 3 together are the **squash evidence**.

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
working tree or index, and `git gc` removes the object later. A 2-commit branch squash-merged
into `main` prints `+ +` with plain `git cherry` and `-` with the squash-tree check; an unmerged
branch prints `+` with both.

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

### No `gh`, not authenticated, or a failing `gh pr list`

If `gh auth status` fails, or any `gh pr list` call fails (for example on a non-GitHub remote,
even with auth passing), signal 3 is unavailable for the whole run. Stop calling `gh`, continue
with signals 1 and 2, and record under `Unverified:`:
`merged-PR check unavailable — squash merges detected by patch equivalence only`. This applies in
every scope. It is not a Rule 3 stop and does not make the run PARTIAL by itself. A branch that
only a merged PR could prove stays in the unmerged list.

## Choosing the delete command

| Evidence | Local delete | Why |
|---|---|---|
| Signal 1 (ancestry) | `git branch -d <b>` | Git verifies the merge itself |
| Squash evidence only (signal 2 or 3) | `git branch -D <b>` | `-d` refuses a squash-merged branch (`error: the branch '<b>' is not fully merged`) |
| No signal | none | Unmerged: report it in Step 6 |

Remote side, for any branch with evidence on `origin/<b>`. Record the tip in the candidate table
(`sha="$(git rev-parse origin/<b>)"`), then delete with a lease on that exact tip:

```bash
git push --force-with-lease=refs/heads/<b>:<sha> origin :refs/heads/<b>
```

If someone pushed to `<b>` after the table was built, git rejects the delete with
`! [rejected] (delete) -> <b> (stale info)` and exit 1. Report it as a skipped delete with the
reason "remote tip moved since the table", and leave the branch. A matching tip deletes the ref;
a moved tip is rejected and the ref survives.

All deletes run only after the single table confirmation. A failed delete (permissions, branch
protection, already gone, stale info) is reported and skipped (SKILL.md rules). After the sweep,
run `git fetch origin --prune`; SKILL.md Step 7 re-checks that no merged ref remains.
