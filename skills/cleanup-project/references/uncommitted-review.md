# Uncommitted-Change Review

Step 2 procedure. The rule that governs everything here: **nothing is discarded without the
user's decision.** No answer means keep the change and leave it untouched.

## 1. Read the state safely

```bash
git status --porcelain=v1 -z
```

Entries are NUL-separated. A rename or copy (`R`, `C`) carries **two** paths: the new path, then
the original. Split on NUL, never on spaces or newlines, and quote each path as one argument
(`-- "<path>"`).

Before reviewing, confirm no merge, rebase, cherry-pick, or revert is in progress (see
Prerequisites in SKILL.md). A `UU`/`AA`/`DD` entry means one is. Stop and ask the user to finish
or abort it. `git restore` on a conflicted path exits 0 but leaves `MERGE_HEAD` behind, so
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

Then ask **keep or discard?** for that change. Accept a group answer ("discard everything under
`tmp/`") only when the user states it. Never infer a batch decision from a pattern of answers.

## 3. Keep

Default: commit the kept changes on a new branch so `main` stays clean. Run the approved
discards (section 4) **before** this commit, so a discard-marked entry is gone first.

```bash
git switch -c wip/cleanup-<yyyy-mm-dd>
git add -- <kept paths>
git commit -m "chore: keep work in progress from cleanup" -- <kept paths>
# stay on this branch; Step 3 switches to main after its worktree check
```

The pathspec on `git commit` is required. A bare `git commit` commits the whole index, which
would sweep any undecided staged entry into the wip commit. With the pathspec, only the kept
paths are committed and every other staged entry stays staged, untouched. For a kept rename,
pass both paths (`-- <new> <old>`). Verified on a scratch repo (git 2.55.0).

Alternatives, each only when the user picks it:

- Named stash: `git stash push -u -m "cleanup: <name>" -- <paths>`. The `-u` is required for an
  untracked path; without it git rejects the pathspec. The stash shows up in the final report,
  because it is residue the user chose.
- Commit on `main`: only with explicit consent, since it lands on the base branch. If
  `git worktree list --porcelain` shows `main` checked out in another worktree, the switch fails;
  use the new-branch default instead.

## 4. Discard

Show the exact command and the path before running it. Tested behaviour (git 2.55.0, scratch repo):

| Code | Command | Result |
|---|---|---|
| ` M`, `M `, `MM` | `git restore --staged --worktree -- <p>` | index and file back to `HEAD` |
| ` D`, `D ` | `git restore --staged --worktree -- <p>` | file restored from `HEAD` |
| `A ` | `git restore --staged --worktree -- <p>` | **file deleted**: it is not in `HEAD`, so its content is lost. Say so before confirming |
| `R ` | `git restore --staged --worktree -- <new> <old>` | both paths of the pair, in one command |
| `??` | `git clean -n -- <p>`, then `git clean -f -- <p>` (add `-d` for a directory) | dry run shows "Would remove <p>"; delete after confirming |

Never run bare `git clean -fd`, `git clean -fdx`, `git checkout -- .`, `git reset --hard`, or
`git stash drop` here. Each would discard changes the user has not decided on.

## 5. Defer artifacts to the ignore step

Build output and editor junk (`node_modules/`, `dist/`, `__pycache__/`, `.venv/`, `.DS_Store`,
`*.swp`) can be deferred to Step 4 rather than deleted one at a time. If the ignore pattern for a
deferred path is declined or not applied, that path returns here for a keep or discard decision.

## 6. Record

Keep a list of `{path, code, decision, command, outcome}` for the final report. A path with no
decision is listed as `kept (no decision)` and makes the run PARTIAL.
