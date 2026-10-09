---
name: ship
description: "Run a release end to end, autonomous by default: version bump everywhere, changelog, docs, landing page, tag, push, GitHub release, PyPI/npm. Use to ship, cut, or tag a release. Don't use for routine commits, pull requests, or marketplace publishing."
license: MIT
effort: max
metadata:
  version: 3.0.1
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Ship

Release a project end to end: the version in every place it appears, the developer changelog and end-user notes, the README, docs, and landing page, then build, tag, push, GitHub release, and PyPI/npm publish.

## Usage

```
/ship [X.Y.Z | major | minor | patch] [--auto | --no-auto]
```

- **Auto mode (default)** runs every step without asking. Each point where interactive mode asks has a fixed outcome: continue, skip with `PARTIAL`, or stop with `BLOCKED`.
- **Interactive mode (`--no-auto`)** asks the user to confirm the version, the file changes, the build, the push, the GitHub release, and each publish. "Ask me before each step" selects it too.
- **Version argument**: `X.Y.Z` releases that version; `major|minor|patch` sets the bump.

Read `references/auto-mode.md` before Step 1: outcome table, hard stops, version rules.

**Scope.** A mode removes confirmations; it never widens the request. Only `/ship` or an explicit request to ship, cut, tag, or publish a release runs Steps 6-9. "What changed?" or "draft release notes" runs Step 2 and the changelog-generator only, and changes no file. "Bump the version" or "update the docs/landing page for the release" runs Steps 1-5 and leaves the changes uncommitted.

## Steps

1. **Pre-flight**: mode, resume check, clean tree, branch, sync, release tool
2. **Determine version** from the commits since the last tag, and check the registries
3. **Prepare changes**: *(subagents, two waves)* version, changelog, docs, landing page
4. **Review**: *(subagent)* mandatory in auto mode
5. **Apply and sweep**: write the changes, prove no stale version remains
6. **Build**
7. **Commit, tag, push**
8. **GitHub release**
9. **Publish** to PyPI and/or npm

## Repo Sync Before Edits (mandatory)

Before creating, updating, or deleting files, sync the current branch with the remote. If the working tree is not clean, run `git stash push -u -m "pre-sync"` first and `git stash pop` after:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin && git pull --rebase origin "$branch"
```

If a rebase or stash conflict occurs, stop with `BLOCKED — sync conflict` and list the files under `Decision` (interactive mode: ask the user). If `origin` is missing, follow the `origin missing` row in `references/auto-mode.md`.

---

## Step 1: Pre-flight (inline)

1. Print the mode, the version argument, and the scope.
2. Full release only: run `git status --porcelain`. If it prints anything: auto mode stops with `BLOCKED — uncommitted changes` and lists the files; interactive mode asks whether to stash (pop after the final report), commit, or abort. Never discard work.
3. Full release only: check that the current branch is the default branch: `git symbolic-ref --short refs/remotes/origin/HEAD` prints `origin/<default>`; if that ref is missing, read the `HEAD branch:` line of `git remote show origin`. If the branches differ, follow the `Not on the default branch` row in `references/auto-mode.md`.
4. Full release only: run `git describe --exact-match --tags HEAD`. Resume that release only when no version argument was given, or an explicit version equals the tag's release version. A different version or `major|minor|patch` continues through the sync and normal version selection. For resume, follow `references/resume.md`: skip version preparation, but rebuild and verify artifacts before any unfinished local upload.
5. Run the Repo Sync above.
6. Check for a release tool or a monorepo:

   ```bash
   ls -d .releaserc* .changeset .versionrc* lerna.json release.config.* pnpm-workspace.yaml 2>/dev/null
   grep -qs '^\[workspace\]' Cargo.toml && echo "cargo workspace"
   grep -E '"(release|semantic-release|release-it|@changesets/cli|standard-version|workspaces)"[[:space:]]*:' package.json 2>/dev/null
   ```

   The `package.json` grep matches a `scripts.release` entry, a release-tool dependency, or `workspaces`, never `"version"`. On a match, follow the `Release tool detected` or `Monorepo` row in `references/auto-mode.md`.

## Step 2: Determine Version (inline)

```bash
last_tag="$(git describe --tags --abbrev=0 2>/dev/null)"
range="${last_tag:+$last_tag..}HEAD"
git log "$range" --oneline --no-merges -n 300
git log "$range" --format=%B --no-merges | grep -E '^BREAKING[ -]CHANGE:'
```

`OLD_VERSION` is `last_tag` without its prefix; the new tag keeps that prefix (`v` when there are no tags). Choose `NEW_VERSION` by the first rule that applies:

1. A version argument → use it.
2. `last_tag` exists and the log is empty → `BLOCKED — nothing to release`.
3. A row in `references/auto-mode.md` → _Version rules_ matches → use its outcome.
4. Commits: **MAJOR** for a `BREAKING:` or `!:` subject or a `BREAKING CHANGE:` footer, **MINOR** for `feat:`, else **PATCH**.

Stop with `BLOCKED` before any file changes if the tag for `NEW_VERSION` exists locally or on origin, or if a registry the project publishes to already has `NEW_VERSION` (`references/publishing.md` → _Decide per registry_). Print "N features, M fixes, K breaking since vOLD → **vNEW** (rule: <rule>)". Interactive mode asks the user to confirm or override; auto mode continues.

## Step 3: Prepare Changes (subagents, two waves)

Subagents read in isolated context so the main agent's context window stays small. Spawn inputs, file ownership, and the workspace: `references/orchestration.md`. Without the Agent tool, run each agent file inline in the same order.

- **Wave 1**, same turn: `version-bumper` and `changelog-generator`.
- **Wave 2**, same turn, after wave 1 returns: `docs-updater` and `landing-page-updater`, both reading `version-changes.json` and `user-notes.md`.

The landing-page-updater owns the files that render the landing site and reports four items, each `updated`, `current`, or `not on page` with evidence: **version** (stale older values too), **changelog for end users** (plain language, no hashes, PR numbers, or authors), **feature list**, and **documentation**. It never adds a section the page lacks. With no landing page it reports "No landing page — skipped."

Interactive mode shows the consolidated summary and waits for confirmation.

## Step 4: Review (subagent)

Spawn `release-reviewer`. Auto mode always runs it; it replaces the human check. On `NEEDS_FIX`, apply each issue's suggestion to the workspace proposals and review once more. Still `NEEDS_FIX` → `BLOCKED — release review failed`, with no project file written. Without the Agent tool, run the reviewer's checklist inline and note under `Uncertainty` that the review was not independent.

## Step 5: Apply and Sweep (inline)

Apply in the order in `references/orchestration.md` → _Apply changes_. Then, unless this is a first release, sweep for the old version:

```bash
git grep -n -I -F "$OLD_VERSION" -- . ':(exclude,glob)**/CHANGELOG*' ':(exclude,glob)**/CHANGES*' ':(exclude,glob)**/HISTORY*' ':(exclude,glob)**/NEWS*'
```

Run the same sweep for each drifted `current` value in `version_sources`. Use one class per hit: `missed` (the project's own version: fix it and re-run the sweep), `historical`, `dependency`, or `fixture`. The step passes when no hit is `missed` and every `version_sources` file reads `NEW_VERSION`; otherwise stop with `BLOCKED — version not updated in <file>`. Record the class counts under `Evidence`.

## Step 6: Build (inline)

```bash
[ -f package.json ] && grep -q '"build"' package.json && echo "npm run build"
[ -f Makefile ] && grep -q '^build:' Makefile && echo "make build"
[ -f Cargo.toml ] && echo "cargo build --release"
[ -f pyproject.toml ] && grep -q '^\[build-system\]' pyproject.toml && echo "python -m build"
```

Interactive mode asks first; auto mode runs it. A failed build stops the run: `BLOCKED — build failed`. No build step → skip and say so.

## Step 7: Commit, Tag, Push (inline)

Step 1 guaranteed a clean start, so every tracked change belongs to the release, including regenerated lockfiles:

```bash
git add -u
git add <each file Step 5 created, such as a new CHANGELOG.md>
git commit -m "chore(release): vX.Y.Z"
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git status --porcelain --untracked-files=no   # must print nothing
```

If a hook rejects the commit, stop: `BLOCKED — commit hook failed`; never use `--no-verify`. Interactive mode asks "Push `<branch>` and tag `vX.Y.Z` to origin?"; a decline ends with `PARTIAL — tag vX.Y.Z created locally, not pushed`. Auto mode pushes:

```bash
git push origin <branch> && git push origin vX.Y.Z
git ls-remote --tags origin "refs/tags/vX.Y.Z"
```

A rejected push stops with `BLOCKED — push rejected`; never force-push. If `git ls-remote` prints nothing, stop, skip Steps 8-9: `BLOCKED — tag vX.Y.Z not on origin` (recovery: `references/final-report.md`).

## Step 8: GitHub Release (inline)

If `gh auth status` fails or the remote is not GitHub, skip with `PARTIAL` and put the command under `Decision`. If a workflow creates releases on tag push, verify with `gh release view vX.Y.Z` instead (`references/publishing.md`). Interactive mode asks first.

```bash
gh release create vX.Y.Z --title "vX.Y.Z" --notes-file "$WORKSPACE/changelog-generator/release-notes.md" --latest
```

A pre-release (a `-` suffix, or a PEP 440 `a`, `b`, `rc`, or `.dev` suffix) uses `--prerelease` instead of `--latest`; a version below the highest existing tag uses `--latest=false`. Append artifact paths if any exist.

## Step 9: Publish to Package Registries (inline)

Follow `references/publishing.md`, using the per-registry decision made in Step 2. Auto mode publishes only where the package already exists for this repository, or to a registry the request names; a missing credential or an npm one-time-password prompt skips that registry with `PARTIAL`; a CI-owned publish is verified, not repeated.

## Expected Output

Every run, including one that stops early, ends with: `Result:` (`COMPLETE`, `PARTIAL — <reason>`, or `BLOCKED — <reason>`), `Mode:`, `Evidence:` (checks that ran, plus each auto decision and its reason), `Uncertainty:` (not verified), and `Decision:` (pending user action, or "No approval needed"). Then the post-release checklist. Status rules, an example report for each status, and the checklist: `references/final-report.md`.

## Edge Cases

- **No remote**: tag locally; skip the push, the GitHub release, and publishing: `PARTIAL — no remote`.
- **Resume**: HEAD carries the requested release tag after an earlier stop (no version argument, or the same explicit version). Step 1 sends the run to `references/resume.md`, which recovers the notes and registry decisions, rebuilds for unfinished local uploads, and finishes only the steps not yet done.
- **Failure after the push**: never roll back automatically, in either mode. Stop with `BLOCKED` and list the recovery commands (delete the tag locally and on origin, revert the commit) under `Decision`; the user confirms and runs them. A version published to PyPI or npm cannot be reused; the fix is a new version.

## Acceptance Criteria

- [ ] The Step 1 report and the final report print the mode; in auto mode, every gate outcome matches `references/auto-mode.md` and appears under `Evidence`
- [ ] In interactive mode, the user confirms the version, the file changes, the build, the push, the GitHub release, and each publish
- [ ] A narrower request (notes, bump, docs) never commits, tags, pushes, or publishes
- [ ] Auto mode releases only from the default branch, and never runs a project's own release script
- [ ] Every version source reads the new version and the sweep ends with no `missed` hit
- [ ] The history file has exactly one entry for the release; an existing `## Unreleased` section is promoted, not duplicated
- [ ] A landing page's report covers version, end-user changelog, feature list, and documentation, each with a status and evidence
- [ ] The tag is confirmed on origin by `git ls-remote`; the GitHub release exists when `gh` is available
- [ ] The final report passes the reader checks in `references/final-report.md`: result findable first, facts separated from assumptions, claims traceable to evidence, next decision named. Without reviewer feedback, human understanding stays unconfirmed

## Step Completion Reports

After each step, print a status report (`√` pass, `×` fail, a `Criteria` line, `Result: PASS | FAIL | PARTIAL`). Templates: `references/step-reports.md`.

## Reference files

- `references/auto-mode.md`: gate outcomes in both modes, hard stops, version rules
- `references/orchestration.md`: workspace, two-wave spawn inputs, file ownership, apply order
- `references/step-reports.md`: step report templates
- `references/publishing.md`: per-registry decision, CI-owned publishing, PyPI / npm commands
- `references/resume.md`: finishing a release that stopped after its tag was created
- `references/final-report.md`: status rules, examples, reader checks, post-release checklist
- `agents/`: `version-bumper`, `changelog-generator`, `docs-updater`, `landing-page-updater`, `release-reviewer`
