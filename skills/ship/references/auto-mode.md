# Auto Mode

Auto mode is the default. `--no-auto`, or a request such as "ask me before each step", selects interactive mode. Auto mode removes confirmations; it never widens the request's scope (SKILL.md → _Usage_ → **Scope**).

## Outcome at every gate

Each row is a point where interactive mode asks the user. Auto mode takes the outcome in the last column and records it under `Evidence` in the final report.

| Gate | Step | Interactive (`--no-auto`) | Auto (default) |
|---|---|---|---|
| Uncommitted changes (full release) | 1 | Ask: stash, commit, or abort | Stop: `BLOCKED — uncommitted changes`, files listed. Never release unknown work |
| Not on the default branch (full release) | 1 | Ask whether to release from `<branch>` | Stop: `BLOCKED — not on the default branch`. A release from a feature or maintenance branch needs `--no-auto` |
| `origin` missing | 1 | Ask whether to release locally | Skip the sync; tag locally; skip the push, the GitHub release, and publishing: `PARTIAL — no remote` |
| Sync conflict (pull or stash pop) | 1 | Stop and ask | Stop: `BLOCKED — sync conflict`, conflicting files under `Decision` |
| Release tool detected | 1 | Ask before running its release command | Stop: `BLOCKED — release owned by <tool>`, its command under `Decision`. Never run it unattended: a release script can prompt, only dry-run, or publish outside this skill's checks |
| Monorepo (`workspaces`, `pnpm-workspace.yaml`, Cargo `[workspace]`) | 1 | Ask which package to release; release each package independently | Stop: `BLOCKED — monorepo`; `Decision`: re-run with `--no-auto` |
| Version | 2 | Ask the user to confirm or override | Use the version argument, else the computed version (Version rules below) |
| Proposed file changes | 3 | Show the consolidated summary; wait for confirmation | Print the summary; continue to the review |
| Reviewer `NEEDS_FIX` | 4 | Show the issues; fix them with the user | Apply each suggestion, review once more; still `NEEDS_FIX` → `BLOCKED — release review failed` |
| Build | 6 | Ask before running | Run |
| Push branch and tag | 7 | Ask; declined → `PARTIAL — tag vX.Y.Z created locally, not pushed` | Push |
| GitHub release | 8 | Ask; declined → listed under `Decision` | Create |
| Publish to a registry | 9 | Ask per registry | Follow the decision made in Step 2 (`publishing.md` → _Decide per registry_) |
| npm asks for a one-time password | 9 | Ask the user for the code | Skip npm: `PARTIAL — npm requires 2FA`; `Decision`: `npm publish --otp <code>` |
| Rollback | any | Ask before each command | Never. Stop with `BLOCKED`; recovery commands under `Decision` |

## Hard stops (both modes)

Each of these stops the run with `BLOCKED`. Never retry with force and never overwrite:

- The tag for `NEW_VERSION` already exists locally or on origin
- `NEW_VERSION` already exists on a registry the project publishes to (checked in Step 2, before any file changes)
- `last_tag` exists and no commits follow it
- A subagent writes no output after one re-spawn
- The reviewer still returns `NEEDS_FIX` after one fix round, or reports that the version does not match a breaking change
- A version source still does not read `NEW_VERSION` after the Step 5 sweep
- The build fails
- A hook rejects the release commit. Never use `--no-verify`
- A push is rejected (protected branch, remote moved ahead). Never force-push
- `git ls-remote` does not show the pushed tag: skip Steps 8-9

A missing `gh` login or registry credential is not a hard stop: skip that step, report `PARTIAL`, and put the command under `Decision`.

A stop after Step 5 leaves the release edits uncommitted in the working tree. List the edited files under `Decision`, with `git restore <files>` to discard them before running `/ship` again.

## Version rules

Step 2 applies the first row that matches, after a version argument (which always wins) and before the commit-based bump. The primary version file is the first of `package.json`, `pyproject.toml`, `Cargo.toml`, `VERSION` that holds a version.

| Situation | Auto (default) | Interactive (`--no-auto`) |
|---|---|---|
| No previous tag | Release the primary version file's value as-is; no version file → `0.1.0` | Propose the same; ask |
| The primary version file is ahead of `OLD_VERSION` and that version has no tag | Release the file's value as-is | Propose the same; ask |
| `OLD_VERSION` is a pre-release (`2.0.0-rc.1`, PEP 440 `2.0.0rc1`) | Stop: `BLOCKED — pre-release needs an explicit version`; `Decision`: `/ship 2.0.0` or `/ship 2.0.0-rc.2` | Ask for the version |
| No conventional-commit prefixes | MINOR; write "no conventional commits, defaulted to minor" under `Uncertainty` | Show the commits; ask |
| Breaking change while `OLD_VERSION` is `0.y.z` | MINOR (`0.(y+1).0`). `1.0.0` only from an explicit version argument | Recommend MINOR; ask |

## What auto mode records

Under `Evidence` in the final report, list every auto decision with its reason:

- The chosen version and the rule that chose it
- Each skipped step and why (no credentials, package not published by this project, CI-owned release, no landing page)
- The reviewer status and each fix applied after `NEEDS_FIX`

Without the Agent tool, the review ran in the same context that wrote the proposals: say so under `Uncertainty`.
