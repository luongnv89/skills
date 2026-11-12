# Publishing to Package Registries

Auto mode publishes without asking, so this file decides **whether** to publish from evidence, not from a prompt. Interactive mode (`--no-auto`) runs the same checks and asks before each upload.

## Decide per registry (in Step 2, before any file changes)

A registry applies when the project has a `package.json` with a `"name"` (npm), or a `pyproject.toml` with a `[build-system]` table and a package name in `[project]` or `[tool.poetry]`, or a `setup.py` (PyPI). For each one, select the publisher in check 1, then run checks 2–4 for both local and CI publishers before any file changes. The first failed gate decides the outcome, and Step 9 acts on it. Check 5 applies only to an unfinished local upload. On resume, verify an existing target version instead of blocking on check 4 (`resume.md`); no upload credentials are needed for that completed publication.

| # | Check | npm | PyPI | Failure or selection outcome |
|---|---|---|---|---|
| 1 | Publisher selection | A workflow publishes on tag push or a published release → CI; otherwise local (_CI-owned publishing_ below) | Same | Record the publisher and continue through checks 2–4. For CI, Step 9 verifies the workflow instead of uploading locally |
| 2 | Not private | No `"private": true` | No `Private :: Do Not Upload` classifier | Local: skip; note "not a published package" under `Evidence`. CI: stop with `BLOCKED — CI publication not authorized` |
| 3 | Published by this project | `npm view <name> repository.url` names the same repository as `git remote get-url origin` | `https://pypi.org/pypi/<name>/json` exists, and its `info.project_urls` or `info.home_page` names the same repository | Name not on the registry: publish only if the request names the registry ("publish to npm"); otherwise local skips, CI stops with `BLOCKED — CI publication not authorized`. Name owned by another project: local skips, CI stops with the same `BLOCKED`; put the name conflict under `Decision` |
| 4 | Version is new | `npm view <name>@X.Y.Z version` prints nothing | `https://pypi.org/pypi/<name>/X.Y.Z/json` returns 404 | Stop before any file changes: `BLOCKED — X.Y.Z already on <registry>` |
| 5 | Local upload credentials | `npm whoami` succeeds | `TWINE_PASSWORD` is set or `~/.pypirc` exists | Skip this check for CI or a completed resume publication. Otherwise skip at Step 9: `PARTIAL — no <registry> credentials`, the setup under `Decision` |

A rejected CI eligibility gate stops before any release file changes, tag push, or GitHub release creation: those events can publish even when the local upload is skipped. Record the rejected gate under `Evidence`. A local registry skip does not make the release `PARTIAL`, except for missing credentials and a one-time-password prompt.

### CI-owned publishing

```bash
grep -lE 'npm publish|pnpm publish|yarn (npm )?publish|JS-DevTools/npm-publish|twine upload|pypa/gh-action-pypi-publish|poetry publish|uv publish|flit publish|hatch publish|changesets/action|goreleaser' .github/workflows/*.y*ml 2>/dev/null
```

If a matching workflow runs on tag push or on a published release, the tag push in Step 7 starts it, and a local upload would be a duplicate. Find the run for the release commit, retrying every 10 seconds for up to one minute until it appears, then wait for it:

```bash
gh run list --workflow <file> --commit "$(git rev-parse HEAD)" --limit 1 --json databaseId,status,conclusion
gh run watch <databaseId> --exit-status
```

When the run succeeds, verify the registry (_Post-publish verification_). A failed run stops publishing: `BLOCKED — publish workflow failed`, with the run URL under `Evidence`.

### CI-owned releases

The same applies to the GitHub release in Step 8. If a workflow creates releases on tag push (`softprops/action-gh-release`, `goreleaser`, or `gh release create` inside a workflow), skip `gh release create`. After the workflow finishes, confirm the release with `gh release view vX.Y.Z`.

## Publish to PyPI

### Build the distribution

If Step 6 already produced the files in `dist/`, reuse them. Otherwise build inside the project's virtual environment (`.venv/` or `venv/`) when one exists:

```bash
python -m pip install --upgrade build twine
rm -rf dist/ build/ *.egg-info
python -m build
```

### Verify the package

```bash
twine check dist/*
ls -la dist/
```

### Upload

In interactive mode, ask first, because a published version cannot be overwritten:

"Ready to publish to PyPI:
- `dist/package-X.Y.Z.tar.gz`
- `dist/package-X.Y.Z-py3-none-any.whl`

Proceed? Once published, this version cannot be overwritten on PyPI."

In auto mode, upload when the Step 2 decision for PyPI is "publish":

```bash
twine upload dist/*
```

Record the URL: `https://pypi.org/project/<package-name>/X.Y.Z/`

## Publish to npm

### Verify the package

```bash
npm pack --dry-run
grep -A5 '"publishConfig"' package.json 2>/dev/null
```

### Publish

In interactive mode, ask first: "Ready to publish `<package-name>@X.Y.Z` to npm. Proceed?" In auto mode, publish when the Step 2 decision for npm is "publish":

```bash
npm publish                               # add --access public for a public scoped package
npm publish --tag next                    # pre-release version (contains "-")
npm publish --tag release-<major>.<minor> # version below the highest existing tag
```

Without `--tag`, npm moves `latest` to whatever version is published, so a pre-release or an older-line release must use its tag.

If npm stops for a one-time password (error `EOTP`), do not retry: skip npm with `PARTIAL — npm requires 2FA` and put `npm publish --otp <code>` under `Decision`.

Record the URL: `https://www.npmjs.com/package/<package-name>/v/X.Y.Z`

## Handle publish failures

- **Authentication error**: skip the registry and put the setup under `Decision`:
  - PyPI: an API token via `TWINE_USERNAME=__token__` and `TWINE_PASSWORD=<token>`, or `~/.pypirc`
  - npm: `npm login`, or an `NPM_TOKEN` environment variable
- **Version conflict**: the version already exists on the registry: `BLOCKED`. The fix is a new version.
- **Package name conflict**: the name is taken: `BLOCKED`. Suggest a scoped or different name under `Decision`.
- **Build error**: re-run Step 6 and fix it before retrying.

## Post-publish verification

```bash
curl -sf "https://pypi.org/pypi/<package-name>/X.Y.Z/json" > /dev/null && echo "PyPI: OK"
npm view <package-name>@X.Y.Z version 2>/dev/null && echo "npm: OK"
```

Report a registry as published only after its check prints `OK`. Registry indexes can lag for a minute: retry the check up to three times, 20 seconds apart, before reporting the publish as unverified under `Uncertainty`.
