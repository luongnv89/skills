# Uncommitted-Change Review

Step 2 procedure. The rule that governs everything here: **nothing is discarded without the
user's decision.** Until an entry has an answer, it stays untouched.

## 1. Read the state safely

```bash
git status --porcelain=v1 -z
```

Entries are NUL-separated. A rename or copy (`R`, `C`) carries **two** paths: the new path, then
the original. Split on NUL, never on spaces or newlines, and pass each path as one
single-quoted argument (`-- '<path>'`, writing an embedded `'` as `'\''`). Never use double
quotes: the shell expands `$` in them, so `src/routes/$postId/` becomes `src/routes//`. Run
path-taking git commands as `git --literal-pathspecs ...` so `[slug]`, `*` and `?` stay literal.

Before reviewing, confirm no merge, rebase, cherry-pick, or revert is in progress (see
Prerequisites in SKILL.md). A `UU`/`AA`/`DD` entry means one is. Stop (`BLOCKED — <operation> in
progress`) and ask the user to finish or abort it. `git restore` on a conflicted path exits 0 but leaves `MERGE_HEAD` behind, so
"discarding" there only hides the conflict.

## 2. Present each change

Group by file. For each, show the status code and the content:

| Code | Meaning | Show |
|---|---|---|
| ` M` | modified, unstaged | `git diff -- <p>` |
| `M ` | modified, staged | `git diff --cached -- <p>` |
| `MM` | staged plus further unstaged edits | both diffs |
| `A ` | new file, staged | `git diff --cached -- <p>` |
| ` D` / `D ` | deleted (unstaged / staged) | `git show HEAD:<p>` head |
| `R ` | renamed (new path, old path) | `git diff --cached -M -- <new> <old>` |
| `??` | untracked | first lines of the file, or the directory listing |

**Secret-like paths** (`.env*`, `*.pem`, `*.key`, `*.p12`, `id_rsa*`, `credentials*`): show only
the name and size (`wc -c < <p>`), never the content or the diff, whatever the status code. Print
`⚠ secret-like: <path>` on its own line.

**Large trees** (more than about 20 entries): show a grouped summary first, by top directory and
status code, for example:

```
 12  ??  node_modules/, dist/          (artifacts)
  6   M  src/search/                   (+140 -32)
  3  ??  notes/
```

Offer one decision per group and a full diff for any group on request. Proposing the groups is
fine; inferring a decision from them is not. A group answer covers only the entries listed in
that group.

## 3. Ask, then confirm one plan

Ask for each entry (or group):

`keep (commit to wip/cleanup-<date>) / keep on disk + ignore / stash / leave as is / discard`

| Answer | Consequence |
|---|---|
| keep (commit to wip/cleanup-<date>) | committed on a new branch; `main` stays clean |
| keep on disk + ignore | untracked paths only, and only when Step 4 is in scope: the file stays, Step 4 proposes an ignore pattern for it |
| stash | `git stash push -u` of that path; listed as residue in the report |
| leave as is | untouched; listed as residue (`left as is`) |
| discard | removed after the plan is confirmed; cannot be undone |

Defaults: offer `keep on disk + ignore` only for an untracked path and only when Step 4 is in
scope. A secret-like or local-config path (`.env*`, `*.local`, editor settings) then defaults to
`keep on disk + ignore`; when that option is not offered (a tracked path, or Step 4 out of
scope), it defaults to `leave as is`. Never default-commit a secret-like path; commit one only
when the user says so for that path. An artifact (`node_modules/`, `dist/`, `__pycache__/`,
`.venv/`, `.DS_Store`, `*.swp`) is usually `keep on disk + ignore` under the same condition.

After every entry has been asked, list any entry still without an answer and ask once: "leave
these untouched?". Only an explicit leave or skip makes an entry undecided (`left as is`).

Then show the consolidated plan (`action-plans.md` B) and take one yes. Nothing runs before it.
A partial yes means re-showing the edited plan for a fresh yes.

## 4. Keep

Run the approved discards (section 5) **before** the keep commit, so a discard-marked entry is
gone first.

```bash
git switch -c wip/cleanup-<yyyy-mm-dd>
git add -- <kept paths>
git commit -m "chore: keep work in progress from cleanup" -- <kept paths>
# stay on this branch; Step 3 switches to main after its worktree check
```

The pathspec on `git commit` is required. A bare `git commit` commits the whole index, which
would sweep any undecided staged entry into the wip commit. With the pathspec, only the kept
paths are committed and every other staged entry stays staged, untouched. For a kept rename,
pass both paths (`-- <new> <old>`).

Alternatives, each only when the user picks it:

- Named stash: `git stash push -u -m "cleanup: <name>" -- <paths>`. The `-u` is required for an
  untracked path; without it git rejects the pathspec.
- Commit on `main`: only with explicit consent, since it lands on the base branch. If
  `git worktree list --porcelain` shows `main` checked out in another worktree, the switch fails;
  use the new-branch default instead.

## 5. Discard

Show the exact command and the path before running it:

| Code | Command | Result |
|---|---|---|
| ` M`, `M `, `MM` | `git restore --staged --worktree -- <p>` | index and file back to `HEAD` |
| ` D`, `D ` | `git restore --staged --worktree -- <p>` | file restored from `HEAD` |
| `A ` | `git restore --staged --worktree -- <p>` | **file deleted**: it is not in `HEAD`, so its content is lost. Say so before confirming |
| `R ` | `git restore --staged --worktree -- <new> <old>` | both paths of the pair, in one command |
| `??` | `git --literal-pathspecs clean -n -- '<p>'`, then the same with `-f` (add `-d` for a directory) | dry run shows "Would remove <p>"; delete after confirming |

**Dry-run gate:** run `git clean -f` only if the `-n` output is exactly one `Would remove <p>`
line per decided path. If it names any other path, or none, do not run `-f`: stop and report
the mismatch; the file stays on disk and the run is PARTIAL.

Never run bare `git clean -fd`, `git clean -fdx`, `git checkout -- .`, `git reset --hard`, or
`git stash drop` here. Each would discard changes the user has not decided on.

## 6. Record

Keep a list of `{path, code, decision, command, outcome}` for the final report. Count the
decisions as `kept`, `discarded`, `ignored/deferred` and `left as is`. A `left as is` entry or a
stash is residue the user chose and makes the run PARTIAL (SKILL.md Results).
