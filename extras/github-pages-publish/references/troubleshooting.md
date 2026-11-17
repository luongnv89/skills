# Troubleshooting a GitHub Pages publish

Read this when a step's command fails or the live check times out. Match the
symptom, apply the fix once, log it, and re-run only the failed step.

## Push and permissions

| Symptom | Cause | Fix |
|---|---|---|
| `refusing to allow an OAuth App to create or update workflow` | The token lacks the `workflow` scope | Ask the user to run `! gh auth refresh -h github.com -s workflow`, then push again |
| `Permission to owner/repo.git denied` / HTTP 403 on push | Read-only access, or git does not use gh credentials | Run `gh auth setup-git`, then push again. If the push still fails, record the `no-push` blocker |
| `Author identity unknown` on commit | git `user.name`/`user.email` unset (preflight blocker `git-identity`) | The user sets them with `git config --global` |
| `GH006: Protected branch update failed` / `push declined due to repository rule violations` | Branch protection or rulesets | Take the protected-branch route in Step 6 (branch and PR) |
| `! [rejected] ... (fetch first)` | Someone pushed after the sync | Run `git pull --rebase origin <branch>`, then push once more |

## Pages configuration

| Symptom | Cause | Fix |
|---|---|---|
| `configure` exits 1 with HTTP 422 and a plan message | Pages on a private repo needs GitHub Pro, Team or Enterprise | Repeat the private-repo gate: make the repo public, or stop |
| `configure` fails on a brand-new empty repo | No branch exists yet | Push first, run `configure` again, then `gh workflow run <file> -R <repo> --ref <branch>` |
| Run fails at `configure-pages` with `Get Pages site failed` | Pages is not enabled, or still uses branch deploys | Run `configure`, then re-run the workflow |
| Deploy job: `Branch "x" is not allowed to deploy to github-pages due to environment protection rules` | The `github-pages` environment allows other branches only | Deploy from the default branch. Otherwise the user edits Settings > Environments > github-pages |
| Settings show "Your site is ready to be published" but there is no URL | The first deploy has not finished | Wait for the run to finish, then read `html_url` again |

## Workflow runs

| Symptom | Cause | Fix |
|---|---|---|
| `verify` reports that no run appeared | The `paths` filter skipped the commit, Actions is disabled, the workflow file is not on the default branch, or the repo is a fork whose workflows were never enabled in the Actions tab | Check the commit touched `<site_dir>/`. Then run `gh workflow run <file> -R <repo> --ref <branch>` and call `verify --event workflow_dispatch` |
| The run ended `failure` | Read the log: `gh run view <id> -R <repo> --log-failed` | Fix the named cause, re-run with `gh run rerun <id> -R <repo>`, then verify again |
| `workflow` exits 3: `existing-pages-workflow` or `several-pages-workflows` | An unmanaged workflow already deploys Pages, often after a build step, and the two would overwrite each other | Ask: replace the listed workflows (delete them, add their paths to `paths.txt`, re-run `workflow`), or stop. Never keep both |

## Live check

| Symptom | Cause | Fix |
|---|---|---|
| 404 on every file right after a successful run | CDN propagation, which usually takes under 2 minutes | `verify` keeps polling until `--live-timeout` |
| 404 only on some paths | Case-sensitive paths, or hidden files (names starting with `.`) that `upload-pages-artifact` skips | Rename the files, or record them under Uncertainty |
| `content differs from commit` until timeout | Another workflow or a branch-based build deployed over this one | Run `gh api repos/<repo>/pages` and check `build_type` is `workflow`. Then list the runs that deployed after yours |
| Connection errors on a custom domain | DNS is not pointing at GitHub, or HTTPS is still being provisioned (up to 24 h). The `github.io` URL redirects to the custom domain, so it cannot be used as a fallback | Report PARTIAL: the deploy run succeeded, but the live check on the custom domain is unverified. The Decision names the DNS or HTTPS fix |
| Assets load locally but 404 live | Root-absolute links (`/css/x.css`) on a project site served under `/<repo>/` | Run `check-site --project-site <name> --fix-root-links` (links already under `/<name>/` stay) |

## Limits

- Published site: 1 GB. Single file in git: 100 MB. Soft bandwidth: 100 GB per month.
- Git LFS files deploy as pointer files unless the workflow checks out with `lfs: true`. `check-site` warns about LFS pointers.
- An Actions deploy serves files exactly as committed. Jekyll does not run, so Markdown files are served as plain text.
- The live site is public on the internet, even when the repo is private (except Enterprise Cloud private Pages).
