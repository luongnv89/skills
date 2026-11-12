# Final Report

Print this report at the end of every run, including runs that stop early. It comes after the last step report.

## Five parts, in this order

1. `Result:` with one status at the start of the line:
   - `COMPLETE` — every step in the request's scope ran.
   - `PARTIAL — <reason>` — a step was skipped: the user declined it in interactive mode, or auto mode skipped it for a stated reason (no remote, no `gh` login, no registry credentials, an npm one-time-password prompt).
   - `BLOCKED — <reason>` — a check failed or a hard stop fired (`auto-mode.md` → _Hard stops_), such as uncommitted changes in auto mode, a failed build, a rejected push, a tag that `git ls-remote` does not find on origin, or a publish error.
2. `Mode:` `auto` or `interactive`.
3. `Evidence:` only the checks that actually ran, each with its observed result: files changed, the sweep counts, the landing-page items, `git ls-remote` output, the release URL, the registry check. In auto mode, also each auto decision and its reason (`auto-mode.md` → _What auto mode records_).
4. `Uncertainty:` what was not verified, such as a clean install from the registry, or an edit skipped because its old line no longer matched.
5. `Decision:` the action still waiting on the user, or "No approval needed."

Then print the post-release checklist below.

## Examples

An auto-mode run that completed:

```
Result: COMPLETE — v2.4.0 released
Mode: auto

Evidence:
- Version: minor bump (3 feat, 4 fix, 0 breaking since v2.3.1)
- Version bumped: pyproject.toml, src/pkg/__init__.py, README.md badge (2.3.1 → 2.4.0)
- Sweep: 0 missed; 1 historical (docs/upgrading.md:8)
- Changelog: CHANGELOG.md "## Unreleased" promoted to "## v2.4.0 — 2026-10-09"
- Landing page (site/index.html): version updated, changelog updated, features updated, docs current
- Reviewer: PASS
- Git tag: v2.4.0 (annotated) pushed to origin (confirmed by git ls-remote)
- GitHub release: https://github.com/owner/repo/releases/tag/v2.4.0
- Published: PyPI — https://pypi.org/project/mypackage/2.4.0/ (PyPI JSON API returned the version)

Uncertainty:
- A clean install was not tested (pip install mypackage==2.4.0)

Decision: No approval needed.

Post-release reminders:
- [ ] Announce the release
- [ ] Monitor for install issues (pip install mypackage==2.4.0)
```

An auto-mode run without registry credentials:

```
Result: PARTIAL — released v2.4.0; npm publish skipped (no credentials)
Mode: auto

Evidence:
- Version bumped: package.json, package-lock.json (1.3.1 → 2.4.0)
- Git tag: v2.4.0 (annotated) pushed to origin (confirmed by git ls-remote)
- GitHub release: https://github.com/owner/repo/releases/tag/v2.4.0
- npm: skipped — npm whoami failed

Uncertainty:
- npm publish not attempted

Decision: Run npm login, then npm publish (version 2.4.0 is tagged and ready).
```

An interactive run where the user declined the push:

```
Result: PARTIAL — tag v2.4.0 created locally, not pushed
Mode: interactive

Evidence:
- Version bumped: package.json (1.3.1 → 2.4.0)
- Changelog: CHANGELOG.md updated (5 commits)
- Git tag: v2.4.0 (annotated), local only

Uncertainty:
- GitHub release and npm publish not attempted

Decision: Push the tag when ready: git push origin main && git push origin v2.4.0
```

A run where the push ran but `git ls-remote` found no tag on origin stops before the GitHub release and publishing:

```
Result: BLOCKED — tag v2.4.0 not on origin
Mode: auto

Evidence:
- Version bumped: package.json (1.3.1 → 2.4.0)
- Git tag: v2.4.0 (annotated), local
- git ls-remote --tags origin "refs/tags/v2.4.0": no output

Uncertainty:
- Why the tag push did not reach origin

Decision: Push the tag (git push origin v2.4.0), then run /ship again: it finds the tag on HEAD and resumes at the GitHub release, then publishing.
```

An auto-mode run that found uncommitted changes:

```
Result: BLOCKED — uncommitted changes
Mode: auto

Evidence:
- git status --porcelain: M src/app.ts, ?? notes.txt

Uncertainty:
- Whether these changes belong in this release

Decision: Commit or stash them, then run /ship again (or run /ship --no-auto to choose interactively).
```

## Reader checks

Grade the report against these checks:

- The opening line states the result and its status, so the reader finds the outcome without reading the step reports.
- Verified facts name the check that observed them. Unverified items appear under `Uncertainty`, not as facts.
- Each claim matches its evidence: a created tag is not reported as pushed, an upload is not reported as installable, and a skipped landing-page item is not reported as updated.
- `Decision:` names the pending user action, or states "No approval needed."

Without reviewer feedback, human understanding of the report stays unconfirmed. An agent's own reading does not confirm it.

## Post-release checklist

Remind the user about common follow-ups:

- [ ] Announce the release (blog, social, Discord, Slack)
- [ ] Bump to the next dev version (for example `X.Y.Z-dev`) if the project uses that convention
- [ ] Close the GitHub milestone if one exists
- [ ] Monitor for issues
- [ ] Verify packages install (`pip install pkg==X.Y.Z`, `npm install pkg@X.Y.Z`)
- [ ] Check that the deployed landing page shows the new version, if the site deploys separately
