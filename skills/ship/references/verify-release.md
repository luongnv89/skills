# Verify the Release Commit

Step 7 runs these checks after the release commit and before the tag. A passing check on another commit says nothing about this one, and the cheap local checks run before anything is shared.

## Interactive mode: ask once

In interactive mode, list the checks this file finds (test command, CI push, verify skill, smoke script) before running any of them, and ask once. A decline of that prompt, or of the CI push prompt in section 2, ends the same way: no tag, `PARTIAL — release commit not verified, not tagged`. Under `Decision`: drop the unpushed release commit with `git reset --hard HEAD~1`, or verify it yourself and then push and tag by hand. Auto mode runs the checks without asking.

## What counts

Right after the release commit, record two values:

```bash
release_sha="$(git rev-parse HEAD)"
baseline="$(git status --porcelain)"   # untracked files included
```

Step 7's commit took every tracked change, so `baseline` can hold only untracked files, such as Step 6 build output that is not gitignored. The checks did not make those files, so they never count against a check (see _After each check_). A check counts only when it ran on `release_sha` and added nothing to the working tree beyond `baseline`. These do not count:

- A green CI run on the parent commit, the previous tag, or a pull request head
- The Step 6 build, because a build is not a test

Run every check from the repo root.

## Never run a release script as a check

Before running a test command, verify skill or smoke script, read what it runs: the `scripts.test` entry in `package.json` with its `pretest` and `posttest` hooks (and the matching hooks the lockfile's manager runs), the `test:` recipe in the Makefile with the targets it lists as prerequisites, the script file itself. If it calls a release, publish, deploy or version step, auto mode does not run it. That covers `release`, `publish`, `deploy`, `semantic-release`, `release-it`, `changeset publish`, `npm version`, `npm publish`, `twine upload`, `cargo publish` and `gh release`. Auto mode treats the command as missing and names it under `Uncertainty`. Interactive mode shows the line and asks.

A project's release command (`npm run release`, `make release`, `scripts/release*`, a release tool's command) is never run as a check, and auto mode never runs it at all.

## 1. Test command (local, first)

The first command found wins:

```bash
[ -f package.json ] && grep -qE '"test"[[:space:]]*:' package.json && ! grep -q 'no test specified' package.json && echo "npm test"
[ -f Makefile ] && grep -q '^test:' Makefile && echo "make test"
[ -f Cargo.toml ] && echo "cargo test"
[ -f go.mod ] && echo "go test ./..."
{ [ -f pytest.ini ] || [ -f conftest.py ] || grep -qs '^\[tool\.pytest' pyproject.toml || grep -qs '^\[tool:pytest\]' setup.cfg || grep -qs '^\[pytest\]' tox.ini; } && echo "python -m pytest"
```

For `npm test`, use the package manager that the lockfile names (`pnpm test`, `yarn test`).

- **Exit 0:** the release commit is verified. Record `<command> passed on <short sha>` under `Evidence`, with the test count if the runner prints one.
- **Non-zero exit:** stop with `BLOCKED — release commit failed <command>`. Put the first failing test and its error under `Evidence`.

## 2. CI on the release commit (only when there is no test command)

Use CI only when step 1 found no test command and a workflow in `.github/workflows/` runs on `push`. CI reports only on a pushed commit, so the branch goes up first, without the tag. Run `gh auth status` first: if it fails, push nothing and continue as in section 4.

- **Interactive:** ask "Push `<branch>` (no tag) so CI can verify `<short sha>`?". A decline ends as in _Interactive mode: ask once_.
- **Auto:** run `git push origin <branch>`.

Then wait for the runs on that exact commit:

```bash
gh run list --commit "$release_sha" --json databaseId,name,status,conclusion
gh run watch <databaseId> --exit-status   # once per run
```

Re-run `gh run list` until at least one run appears, for up to 5 minutes. Once every listed run has finished, wait about 30 seconds and list again, because workflows start at different times; watch any new run before deciding.

| What CI shows | Outcome |
|---|---|
| Every run is `success`, `skipped` or `neutral` | Verified. Record `CI green on <short sha>: <workflow names>` |
| Any other conclusion (`failure`, `cancelled`, `timed_out`, `action_required`, `startup_failure`, `stale`) | Stop with `BLOCKED — CI failed on release commit: <workflow> (<conclusion>)`. The commit is on origin with no tag |
| No run appears within 5 minutes, or `gh` cannot read runs | Not verified. Continue as in section 4 |

## 3. Verify skill or smoke script (as well)

Look for these, in order:

- A verify skill, as `/verify-setup` writes it: `verify/SKILL.md` or `verify-*/SKILL.md` under `.claude/skills/` or `.agents/skills/`, excluding `verify-setup` itself. The `.agents/` copy mirrors the `.claude/` one, so run only one of them. With several `verify-<app>` skills, run the one for the package being released, or all of them when the repo releases as one.
- devops-pipeline's smoke script: `scripts/e2e_test.sh` or `scripts/e2e_test.py`. Skip it if the verify skill already runs it.

Run each one you find after step 1 or 2. They run in addition to the test command or CI and never replace it: with no test command and no CI, section 4 still applies.

- **Verify skill:** follow its SKILL.md as written, from boot to teardown, and read its last `VERIFY` line. The line counts only when `commit=` is the short `release_sha` and the tree was clean when the skill started: `dirty=no`, or `dirty=yes` when `baseline` is not empty and the _After each check_ test printed nothing just before the skill ran (the verify skill counts the baseline's untracked files as dirty).
  - `VERIFY PASS`: the check passes.
  - `VERIFY PARTIAL`: the check passes, and each `UNVERIFIED` row goes under `Uncertainty`.
  - `VERIFY FAIL`: stop with `BLOCKED — verify skill failed: F<id> <observation>`.
  - No `VERIFY` line, a different commit, or a `dirty=yes` the rule above does not allow: stop with `BLOCKED — verify skill gave no verdict for <short sha>`.
- **Smoke script:** run `bash scripts/e2e_test.sh` or `python3 scripts/e2e_test.py`. A non-zero exit stops with `BLOCKED — smoke script failed: <path>`.

## After each check

After the test command and after each later check, compare the tree with `baseline`, so the next check, such as a verify skill, sees the tree the release commit left:

```bash
git status --porcelain | grep -vxF -f <(printf '%s\n' "$baseline")   # must print nothing
```

Any new or changed entry stops with `BLOCKED — release checks left files: <list>`. Entries already in `baseline` never stop the release.

## 4. Neither tests nor CI

The release still tags when nothing verified the commit, and `Uncertainty` says `Release commit <short sha> not verified: <reason>`, with one of these reasons:

- no test command or CI
- CI never ran on the commit
- gh could not read runs
- the test command was skipped because it calls a release step

`Evidence` never calls the commit verified, and the step report shows `—`, not `√`.

## 5. On failure

Every failure stops with `BLOCKED` and names the exact check that failed: the command, the workflow, the verify row or the script. No tag is created, and nothing rolls back automatically. Under `Decision`, in this order:

- **Local commit:** drop the unpushed release commit with `git reset --hard HEAD~1`, which discards the release edits that `/ship` recreates. Then fix the failing check, commit the fix (Step 1 needs a clean tree), and run `/ship` again.
- **Pushed for CI:** run `git revert <release_sha>` and push, which restores the old version files and changelog, so the next run writes one `## vX.Y.Z` entry, not two. Then fix the failing check, commit the fix, and run `/ship` again. Never force-push or delete the remote commit.
