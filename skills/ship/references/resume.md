# Resume a Stopped Release

Step 1 sends a full release here when `git describe --exact-match --tags HEAD` prints a tag: the release commit and its tag exist, and a later step stopped. Resume skips the Repo Sync and Steps 2-6, then runs each remaining step only if it is not done yet. Step 1's clean-tree and default-branch checks still apply, because publishing builds from the working tree.

## 1. Recover the release inputs

```bash
TAG="$(git describe --exact-match --tags HEAD)"
NEW_VERSION="${TAG#v}"
WORKSPACE="$(mktemp -d "${TMPDIR:-/tmp}/ship-XXXXXX")"
```

Rebuild the release notes from the history file (`CHANGELOG.md`, `CHANGES.*`, `HISTORY.*`, or `NEWS.*`): copy the section whose heading names `NEW_VERSION`, from that heading through the line before the next `## ` heading, into `$WORKSPACE/release-notes.md`. If no section names the version, create the GitHub release with `--generate-notes` instead, and say so under `Uncertainty`.

## 2. Decide each registry again

Run `publishing.md` → _Decide per registry_ checks 1, 2, 3, and 5. Check 4 means something else on resume: a version already on the registry was published before the stop. Confirm it with _Post-publish verification_ and report it as published, not as `BLOCKED`.

## 3. Finish the remaining steps

| Step | Already done when | Otherwise |
|---|---|---|
| 7. Push | `git ls-remote --tags origin "refs/tags/$TAG"` prints the tag | Push the branch and the tag, then confirm with `git ls-remote` |
| 8. GitHub release | `gh release view "$TAG"` succeeds | Create it with `--notes-file "$WORKSPACE/release-notes.md"`; a CI-owned release is verified, not created |
| 9. Publish | The registry has `NEW_VERSION` | Publish according to section 2 |

Report each step as `done before the stop` or `completed now` under `Evidence`.

## Push rejected because origin moved ahead

Never rebase or re-tag automatically: a rebase would add upstream commits that the release notes do not cover. Stop with `BLOCKED — origin moved ahead of the release commit`. Under `Decision`, give the commands, and say to review the new upstream commits first:

```bash
git tag -d vX.Y.Z
git pull --rebase origin <branch>
git tag -a vX.Y.Z -m "Release vX.Y.Z"
```

Then `/ship` again resumes from the push.
