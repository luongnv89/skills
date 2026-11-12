# Resume a Stopped Release

Step 1 sends a full release here when HEAD carries a release tag and the request has no version argument, or its explicit version equals that tag's release version. A different explicit version or `major|minor|patch` follows the normal sync and version-selection path instead. Resume skips the Repo Sync and Steps 2-5 and reuses the existing commit and tag. Step 1's clean-tree and default-branch checks still apply, because publishing builds from the working tree.

## 1. Recover the release inputs

```bash
TAG="$(git describe --exact-match --tags HEAD)"
NEW_VERSION="${TAG#v}"
WORKSPACE="$(mktemp -d "${TMPDIR:-/tmp}/ship-XXXXXX")"
```

Rebuild the release notes from the history file (`CHANGELOG.md`, `CHANGES.*`, `HISTORY.*`, or `NEWS.*`): copy the section whose heading names `NEW_VERSION`, from that heading through the line before the next `## ` heading, into `$WORKSPACE/release-notes.md`. If no section names the version, create the GitHub release with `--generate-notes` instead, and say so under `Uncertainty`.

## 2. Decide each registry again

Run `publishing.md` → _Decide per registry_ checks 1, 2, 3, and 5. Check 4 means something else on resume: a version already on the registry was published before the stop. Confirm it with _Post-publish verification_ and report it as published, not as `BLOCKED`.

## 3. Rebuild before unfinished local uploads

Only a registry whose version is absent and whose decision permits a local upload needs this step. Already-published, skipped, and CI-owned registries need no local build or upload; verify their existing publication or workflow instead.

Run the required project builds from Step 6 against the tagged source before any pending local upload. Interactive mode asks first; auto mode runs them. Rebuild even on resume: ignored artifacts such as `dist/` may be absent in a fresh clone or stale from another build. A failed build stops with `BLOCKED — build failed`; upload nothing.

Then follow `publishing.md`'s package checks for each pending local registry:

- **npm:** run `npm pack --dry-run` after the build. Confirm required publish files, including built entry points named by `package.json`, exist and appear in the packed file list. A successful pack command alone does not prove those files are included.
- **PyPI:** build the distribution as described there unless this run's build already produced it, then run `twine check` and confirm the distribution's package name and version match `NEW_VERSION`. Do not reuse artifacts merely because they are present.

Missing or invalid artifacts stop with `BLOCKED — package verification failed`. Record the build and package checks under `Evidence`; only then continue to the remaining upload.

## 4. Finish the remaining steps

| Step | Already done when | Otherwise |
|---|---|---|
| 7. Push | `git ls-remote --tags origin "refs/tags/$TAG"` prints the tag | Push the branch and the tag, then confirm with `git ls-remote` |
| 8. GitHub release | `gh release view "$TAG"` succeeds | Create it with `--notes-file "$WORKSPACE/release-notes.md"`; a CI-owned release is verified, not created |
| 9. Publish | The registry has `NEW_VERSION` | Publish according to section 2, after section 3's build and package checks |

Report each step as `done before the stop` or `completed now` under `Evidence`.

## Push rejected because origin moved ahead

Never rebase or re-tag automatically: a rebase would add upstream commits that the release notes do not cover. Stop with `BLOCKED — origin moved ahead of the release commit`. Under `Decision`, give the commands, and say to review the new upstream commits first:

```bash
git tag -d vX.Y.Z
git pull --rebase origin <branch>
git tag -a vX.Y.Z -m "Release vX.Y.Z"
```

Then `/ship` again resumes from the push.
