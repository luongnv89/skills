# Verify the Release Commit

Step 7 runs these checks after the release commit and before the tag. A passing check on another commit says nothing about this one, and the cheap local checks run before anything is shared.

## What counts

Right after the release commit, record `release_sha="$(git rev-parse HEAD)"`. A check counts only when it ran on `release_sha` with no tracked file changed. These do not count:

- A green CI run on the parent commit, the previous tag, or a pull request head
- The Step 6 build, because a build is not a test

Run every check from the repo root.

## Never run a release script as a check

Before running a test command, verify skill or smoke script, read what it runs: the `scripts.test` entry in `package.json`, the `test:` recipe in the Makefile, the script file itself. If it calls a release, publish, deploy or version step, auto mode does not run it. That covers `release`, `publish`, `deploy`, `semantic-release`, `release-it`, `changeset publish`, `npm version`, `npm publish`, `twine upload`, `cargo publish` and `gh release`. Auto mode treats the command as missing and names it under `Uncertainty`. Interactive mode shows the line and asks.

A project's release command (`npm run release`, `make release`, `scripts/release*`, a release tool's command) is never a check. It belongs to the `Release tool detected` row in `auto-mode.md`.

## 1. Test command (local, first)

The first command found wins:

```bash
[ -f package.json ] && grep -qE '"test"[[:space:]]*:' package.json && ! grep -q 'no test specified' package.json && echo "npm test"
[ -f Makefile ] && grep -q '^test:' Makefile && echo "make test"
[ -f Cargo.toml ] && echo "cargo test"
[ -f go.mod ] && echo "go test ./..."
{ [ -f pytest.ini ] || grep -qs '^\[tool\.pytest' pyproject.toml; } && echo "python -m pytest"
```

For `npm test`, use the package manager that the lockfile names (`pnpm test`, `yarn test`).

- **Exit 0:** the release commit is verified. Record `<command> passed on <short sha>` under `Evidence`, with the test count if the runner prints one.
- **Non-zero exit:** stop with `BLOCKED — release commit failed <command>`. Put the first failing test and its error under `Evidence`.

## 2. CI on the release commit (only when there is no test command)

Use CI only when step 1 found no test command and a workflow in `.github/workflows/` runs on `push`. CI reports only on a pushed commit, so the branch goes up first, without the tag:

- **Interactive:** ask "Push `<branch>` (no tag) so CI can verify `<short sha>`?". If the user declines, stop with `PARTIAL — release commit not verified, not tagged`.
- **Auto:** run `git push origin <branch>`.

Then wait for the runs on that exact commit:

```bash
gh run list --commit "$release_sha" --json databaseId,name,status,conclusion
gh run watch <databaseId> --exit-status   # once per run
```

Re-run `gh run list` until at least one run appears, for up to 5 minutes.

| What CI shows | Outcome |
|---|---|
| Every run is `success`, `skipped` or `neutral` | Verified. Record `CI green on <short sha>: <workflow names>` |
| Any run is `failure`, `cancelled` or `timed_out` | Stop with `BLOCKED — CI failed on release commit: <workflow>`. The commit is on origin with no tag |
| No run appears within 5 minutes, or `gh` cannot read runs | Not verified. Continue as in section 4 |

## 3. Verify skill or smoke script (as well)

Look for these, in order:

- A verify skill, as `/verify-setup` writes it: `.claude/skills/verify*/SKILL.md`, or `.agents/skills/verify*/SKILL.md`. The second is a copy of the first, so run only one of them.
- devops-pipeline's smoke script: `scripts/e2e_test.sh` or `scripts/e2e_test.py`. Skip it if the verify skill already runs it.

Run each one you find after step 1 or 2. They run in addition to the test command or CI and never replace it: with no test command and no CI, section 4 still applies.

- **Verify skill:** follow its SKILL.md as written, from boot to teardown, and read its last `VERIFY` line. The line counts only when `commit=` is the short `release_sha` and `dirty=no`.
  - `VERIFY PASS`: the check passes.
  - `VERIFY PARTIAL`: the check passes, and each `UNVERIFIED` row goes under `Uncertainty`.
  - `VERIFY FAIL`: stop with `BLOCKED — verify skill failed: F<id> <observation>`.
  - No `VERIFY` line, a different commit, or `dirty=yes`: stop with `BLOCKED — verify skill gave no verdict for <short sha>`.
- **Smoke script:** run `bash scripts/e2e_test.sh` or `python3 scripts/e2e_test.py`. A non-zero exit stops with `BLOCKED — smoke script failed: <path>`.

## After the checks

`git status --porcelain --untracked-files=no` must print nothing. A check that changed a tracked file stops with `BLOCKED — release checks changed tracked files`, and the files are listed.

In interactive mode, list the checks before running them and ask once. If the user declines, tag anyway and write `release commit not verified (user declined)` under `Uncertainty`.

## 4. Neither tests nor CI

Sometimes no test command exists, no workflow runs on push, or CI never ran on the commit. The release still tags, and `Uncertainty` says `Release commit <short sha> not verified: no test command or CI`. `Evidence` never calls the commit verified, and the step report shows `—`, not `√`.

## 5. On failure

Every failure stops with `BLOCKED` and names the exact check that failed: the command, the workflow, the verify row or the script. No tag is created, and nothing rolls back automatically. Under `Decision`:

- **Local commit:** fix the failing check. Then drop the unpushed release commit with `git reset --hard HEAD~1`, which discards the release edits that `/ship` recreates. Run `/ship` again.
- **Pushed for CI:** fix forward, then run `/ship` again, or revert with `git revert <sha>` and push. Never force-push or delete the remote commit.
