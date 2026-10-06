# Final Report

Print this report at the end of every run, including runs that stop early. It comes after the last step report.

## Four parts, in this order

1. `Result:` with one status at the start of the line:
   - `COMPLETE` — every planned step ran.
   - `PARTIAL — <reason>` — the user declined or skipped a step, such as the push, the GitHub release, or publishing.
   - `BLOCKED — <reason>` — a check failed, such as a dirty tree the user chose not to resolve, a failed build, or a publish error.
2. `Evidence:` only the checks that actually ran, each with its observed result: files changed, `git ls-remote` output, the release URL, registry verification.
3. `Uncertainty:` what was not verified, such as a clean install from the registry or a skipped reviewer pass.
4. `Decision:` the action still waiting on the user, or "No approval needed."

Then print the post-release checklist below.

## Example

```
Result: COMPLETE — v2.4.0 released

Evidence:
- Version bumped: pyproject.toml, package.json (1.3.1 → 2.4.0)
- Changelog: CHANGELOG.md updated (8 commits: 3 features, 4 fixes, 1 breaking change)
- Git tag: v2.4.0 (annotated) pushed to origin (confirmed by git ls-remote)
- GitHub release: https://github.com/owner/repo/releases/tag/v2.4.0
- Published: PyPI — https://pypi.org/project/mypackage/2.4.0/ (PyPI JSON API returned the version)

Uncertainty:
- A clean install was not tested (pip install mypackage==2.4.0)

Decision: No approval needed.

Post-release reminders:
- [ ] Announce on Discord
- [ ] Monitor for install issues (pip install mypackage==2.4.0)
```

A run where the user declined the push ends like this:

```
Result: PARTIAL — tag v2.4.0 created locally, not pushed

Evidence:
- Version bumped: package.json (1.3.1 → 2.4.0)
- Changelog: CHANGELOG.md updated (5 commits)
- Git tag: v2.4.0 (annotated), local only

Uncertainty:
- GitHub release and npm publish not attempted

Decision: Push the tag when ready: git push origin main && git push origin v2.4.0
```

## Reader checks

Grade the report against these checks:

- The opening line states the result and its status, so the reader finds the outcome without reading the step reports.
- Verified facts name the check that observed them. Unverified items appear under `Uncertainty`, not as facts.
- Each claim matches its evidence: a created tag is not reported as pushed, and an upload is not reported as installable.
- `Decision:` names the pending user action, or states "No approval needed."

Without reviewer feedback, human understanding of the report stays unconfirmed. An agent's own reading does not confirm it.

## Post-release checklist

Remind the user about common follow-ups:

- [ ] Announce the release (blog, social, Discord, Slack)
- [ ] Bump to next dev version (e.g., `X.Y.Z-dev`) if the project uses that convention
- [ ] Close the GitHub milestone if one exists
- [ ] Monitor for issues
- [ ] Verify packages install (`pip install pkg==X.Y.Z`, `npm install pkg@X.Y.Z`)
