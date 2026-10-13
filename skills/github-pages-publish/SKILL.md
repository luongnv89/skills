---
name: github-pages-publish
description: "Publish or update a static site (gh-pages) on GitHub Pages via GitHub Actions in any repo: text or pre-built HTML in, workflow set up, live URL verified. Don't use for CI test pipelines, framework/SSG builds, or Netlify/Vercel hosting."
license: MIT
effort: high
dependencies:
  - frontend-design
metadata:
  version: 1.0.1
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# GitHub Pages Publish

Put a website live on GitHub Pages and hand back a URL that was checked live. The input
is the content (text, one HTML file, or a folder of ready files) and the target repo,
which can differ from the repo the user is working in. The skill creates or repairs a
GitHub Actions deploy workflow, sets Pages to deploy from Actions, pushes to the
default branch, and proves the live site serves the committed bytes. Automate every
step. Stop only at a confirmation gate.

Terms used throughout:

- **target repo**: `owner/name` that hosts the site. A bare `name` means the gh user's account.
- **content**: the files to publish, staged in `<work>/content/` before anything is pushed.
- **workspace**: the checkout that receives the commit. It is the current checkout (in-place) or a clone in `<work>/repo/`.
- **site folder**: the folder inside the workspace that Pages deploys: `.`, `docs`, or the user's choice.
- **confirmation gate**: one of the questions listed in Step 2. Nothing else stops the run.
- **pre-authorized**: the request already answers a gate ("create it if needed", "make it public"). State the answer in one line and continue.
- **live check**: `verify` passes, which means every checked file at the Pages URL matches the committed file byte for byte.
- **run log**: `.pages-publish/run-<UTC>.md` in the current directory. Every step appends one row.

`P` means `python3 <skill>/scripts/pages_publish.py`. Each subcommand prints JSON. Exit 1
means a check failed, 2 means bad input or a missing tool, and 3 means a conflict
that needs the user. On a nonzero exit, read the `error:` and `fix:` lines on stderr,
then use `references/troubleshooting.md`. Load a `references/` file only at the step
that names it, to save the agent's context budget.

## When to Use

Use when someone wants a website, page, or set of HTML files published or updated on
GitHub Pages, in the current repo or another one. Not for CI test or lint pipelines
(`devops-pipeline`), release tagging (`ship`), designing a page without publishing it
(`frontend-design`), building a framework or site-generator project (publish its built
output instead), custom-domain DNS setup, or hosting outside GitHub Pages.

## Step 0: Select the branch

| Condition | Branch |
|---|---|
| The request says "dry run", "plan only", or "don't push" | **Dry run**: run Steps 1, 3, 4 and 5 in a clone (never in-place, never the Repo Sync on the user's checkout) with `--dry-run`. Create, change, and push nothing. Report `DRY-RUN` |
| The content is text: inline in the request, or a `.md` or `.txt` file | **Text**: Step 3 builds the page with `frontend-design` |
| The content is one `.html` file, or a folder that holds HTML | **Ready files**: Step 3 stages the files as given |
| No content or no target repo can be found in the request | Ask for the missing item. Do nothing else |

Defaults: if the request names no target repo, use the current checkout's `origin`. If
the current directory is not a GitHub checkout, ask for the target repo.

After each step, append one run-log row with
`P log --file <log> --step "<N name>" --status pass|fail|skip|info|ask --msg "<result>" --cmd "<command>"`,
then print a Step Completion Report: `√`/`×` rows tied to a command, file, or count, then
`Result: PASS | FAIL | PARTIAL`. Log a gate as `ask` when it is asked or pre-authorized, then
log the answer as `pass` (yes) or `fail` (no).

## Step 1: Log and preflight (read-only)

1. Run `P log-init --request "<one-line request>"`. Record the `log` path.
2. Run `P preflight --repo <target>`. The command only reads.
3. If `blockers` is not empty, log each blocker, report BLOCKED with the blocker's `fix`, and stop.
4. Keep the JSON. Later steps read `target`, `pages`, `workflows`, `local`, and `scope_gaps` from it.
5. Set `work` to `${TMPDIR:-/tmp}/github-pages-publish/<owner>-<name>-<UTC stamp>`.
6. Read the site type from `target.project_site`, and the URL the site will have from `target.expected_url` (a dry run reports this one, labeled "expected, not checked"). A project site is served under `/<name>/`. A user site (`<owner>.github.io`) or a custom-domain site is served at the domain root.

Bar: `preflight` exited 0 and `blockers` is empty.

## Step 2: Resolve the confirmation gates

Ask only for the gates that `preflight` returned. Put all of them in one message. If the
run is pre-authorized for a gate, log `ask` with the request's wording and do not ask.

| Gate id | Ask | Action on yes | Action on no |
|---|---|---|---|
| `create-repo` | "Create public repo `<owner>/<name>`?" | Create it in Step 4 | BLOCKED |
| `private-repo` | "`<repo>` is private. Pages sites are public. Make the repo public (recommended), keep it private (needs a paid plan), or stop?" | Public: `gh repo edit <repo> --visibility public --accept-visibility-change-consequences`. Keep private: continue, and a 422 from `configure` means BLOCKED | BLOCKED |
| `enable-actions` | "Actions is disabled on `<repo>`. Enable it?" | `gh api -X PUT repos/<repo>/actions/permissions -F enabled=true` | BLOCKED |

A command named in a gate's `fix` (`gh auth refresh ...`) is interactive: ask the user to
run it (in Claude Code, with the `!` prefix), then re-run `preflight`. A dry run lists the
gates it would ask and changes nothing. Bar: every gate has a logged
answer, or the run ended BLOCKED.

## Dependency Preflight (mandatory)

This skill optionally invokes `frontend-design`, declared in frontmatter `dependencies`.
It is used on the Text branch only. Before Step 3:

```bash
command -v asm >/dev/null || echo "asm not installed: npm install -g agent-skill-manager"
asm deps discover "<this skill's directory>" --json
printf 'gp_session=%s\n' "github-pages-publish-$(date +%s)-$$"   # record it; reuse it verbatim
```

On the Text branch, run `asm deps acquire frontend-design --session <gp_session> --json`
and read the returned `skillMdPath`. Without `asm`, read
`~/.claude/skills/frontend-design/SKILL.md` or `~/.agents/skills/frontend-design/SKILL.md`.
On the Ready files branch, do not acquire it. At the end, including an early stop, run
`asm deps release --session <gp_session> --json`. All of this is fail-soft. Without
`frontend-design`, fill `<skill>/assets/text-page.html` yourself and record the fallback
under Uncertainty.

## Step 3: Prepare the content

Read `references/content-prep.md` and follow the section for the branch from Step 0. It
stages the content in `<work>/content/`, never touching the user's originals:

- **Text branch**: `frontend-design` builds `index.html` from a pre-authorized brief that keeps the text verbatim. Without it, the fallback template is used.
- **Ready files branch**: copy the file or folder. Resolve a missing `index.html`.

Then run `P check-site --dir <work>/content`. For a project site, add `--project-site <name> --fix-root-links`, with `<name>` from preflight `target.name`.
Handle each error id as the reference says, then re-run the check.

Bar: `check-site` exits 0, and every `fixed` entry and warning is logged.

## Repo Sync Before Edits (mandatory)

Run this before the first write in Step 4. Use `ws` for the workspace path.

```bash
branch="$(git -C "$ws" rev-parse --abbrev-ref HEAD)"
[ -n "$(git -C "$ws" status --porcelain)" ] && git -C "$ws" stash push -u -m pages-publish-presync && stashed=1
if git -C "$ws" fetch origin && git -C "$ws" pull --rebase origin "$branch"; then sync=ok
elif [ -d "$ws/.git/rebase-merge" ] || [ -d "$ws/.git/rebase-apply" ]; then git -C "$ws" rebase --abort; sync=conflict
else sync=failed; fi
if [ "${stashed:-0}" = 1 ] && ! git -C "$ws" stash pop; then sync=pop-conflict; fi
```

Skip this block for a clone of an empty repo (`git -C "$ws" rev-parse HEAD` fails): there is
nothing to pull. If `sync=conflict`, `sync=pop-conflict`, or `origin` is missing, stop and ask
the user how to continue; the stash stays in `git stash list`. If `sync=failed`, retry once.
If it fails again, report BLOCKED.

## Step 4: Open the workspace

1. If `local.in_place` is true and this is not a dry run, use the current checkout. `preflight` sets it only when the checkout's `origin` is the target repo, it is on the default branch, and it has no unpushed commits that would ride along with the push.
2. If the gate `create-repo` was approved, run `gh repo create <owner>/<name> --public`. The default branch is `main`. In a dry run against a missing repo, run `git init -b main <work>/repo` instead and skip items 3–4.
3. If the workspace is not in-place, run `gh repo clone <owner>/<name> <work>/repo -- --filter=blob:none`.
4. Run the Repo Sync.
5. Choose the site folder. Use the first rule that applies:
   1. The user named a folder.
   2. `.github/pages-publish.json` exists. Use its `site_dir`.
   3. Pages already deploys a folder of the default branch. Use the `path:` of the existing static deploy workflow, or the legacy `pages.source.path` when `pages.source_on_default_branch` is true (`/docs` gives `docs`, `/` gives `.`). A legacy source on another branch (`gh-pages`) does not count: fall through, and record under Uncertainty that the old branch is no longer served.
   4. The repo is new or empty, or its root holds only site files plus README, LICENSE, or CNAME. Use `.`.
   5. Otherwise use `docs`.

Bar: the workspace is on the default branch, `sync=ok` (or a fresh clone), and the site folder is logged with its rule number.

## Step 5: Place the site and the workflow

1. Run `P sync-site --src <work>/content --repo-dir <ws> --site-dir <folder> --dry-run`.
2. If it exits 3 (`site-dir-changed`), ask which folder to keep. To keep the old folder, use it as `<folder>`. To move, add `--move-from <previous>`, which deletes the files published in the old folder. Then repeat item 1.
3. If `first_publish_sweep` is true and the folder is not the folder Pages currently deploys, ask before deleting. Show the `deleted` list and ask for another folder name as the alternative.
4. If `gitignored` is not empty, log those paths. Step 6 adds them with `-f`, because they are site files the user asked to publish.
5. Skip this item in a dry run. Otherwise run the same command without `--dry-run`, adding `--paths-out <work>/paths.txt`. Log `added`, `changed`, `deleted`, and `deleted_from_old_dir`. Log `stale_not_deleted` (untracked files are never deleted) under Uncertainty.
6. Run `P workflow --repo-dir <ws> --site-dir <folder> --branch <default> --paths-out <work>/paths.txt`. When the managed workflow already exists, add `--keep-versions` so an unchanged site gets no workflow change. In a dry run, add `--dry-run` and drop `--paths-out`. Record its `file`.
7. If `workflow` exits 3, show the conflicting workflows and ask: replace them, or stop. A conflict means the repo builds its site; replacing it deploys the staged files instead. Replace means deleting the conflicting files, adding their paths to `paths.txt`, and running item 6 again. A dry run asks nothing here: it stops and puts the question in its Decision line.
8. If `workflow` reports `created` or `updated`, `scope_gaps` has `scope-workflow`, and `git -C <ws> remote get-url origin` starts with `https://`, ask the user to run its `fix` command. Wait for confirmation. Then run `gh auth status` and check that the `workflow` scope is listed.

Bar: `sync-site` and `workflow` exited 0, and `paths.txt` lists every changed path. A dry run ends here with its report.

## Step 6: Configure, commit, and push

1. Run `P configure --repo <owner>/<name>`. If it fails on an empty new repo, set `dispatch=1` and run it again after item 5.
2. If `paths.txt` is missing or empty, nothing changed. Skip items 3–7 and set `dispatch=1`.
3. Run `GIT_LITERAL_PATHSPECS=1 git -C <ws> add -A -f --pathspec-from-file=<work>/paths.txt`.
4. Run `GIT_LITERAL_PATHSPECS=1 git -C <ws> commit -m "chore(pages): publish site" --pathspec-from-file=<work>/paths.txt`. Only the listed paths enter the commit.
5. Run `git -C <ws> push origin HEAD:<default>`.
6. If the push is rejected as non-fast-forward, run `git -C <ws> pull --rebase origin <default>` and push once more.
7. If the push is rejected by branch protection, push to `pages-publish/<stamp>` and open a PR with `gh pr create --base <default> --fill`. The result is PARTIAL, and the Decision is "merge PR #N". Skip Step 7.
8. If `dispatch=1`, run `gh workflow run <file> -R <owner>/<name> --ref <default>`.

Bar: `configure` reports `build_type` `workflow`, and `git -C <ws> rev-parse HEAD` equals `origin/<default>`.

## Step 7: Live check

Run `P verify --repo <owner>/<name> --repo-dir <ws> --site-dir <folder> --workflow <file>`.
If `dispatch=1`, add `--event workflow_dispatch`. The command verifies the workspace's
`HEAD`, which is the pushed commit. It waits for that commit's deploy run (up to 900 s),
reads the Pages URL, and polls until every file in the manifest (first 100) is served
byte-identical to the committed blob (up to 600 s). It also checks the root URL.

If it exits 1, apply the matching fix from `references/troubleshooting.md` once, then
run `verify` again. Bar: `verify` exits 0 with `matched` equal to `checked`. If `capped`
is true, report the count as `checked` of `files_total` under Evidence. Never report the
URL as live without this exit.

## Step 8: Report

Release the dependency session. Log the final row. Then print the report.

Expected output (format):

```
Result: PUBLISHED | PARTIAL | BLOCKED | DRY-RUN — <URL, or what is missing>
Evidence: <repo and visibility; commit sha; run URL and conclusion; files matched N/N at the URL; Pages build_type; site folder and rule>
Uncertainty: <unverified items: custom-domain HTTPS, stale files kept, fallbacks used, assumptions>
Decision: <the approval still needed (merge PR, run an auth command), or "No approval needed">
Log: <run log path>
```

Example (expected result of a first publish to a new repo):

```
Result: PUBLISHED — https://octo.github.io/tea-club/ (live check: 4/4 files match commit 3f9c2ab)
Evidence: created public repo octo/tea-club (gate answered yes); site folder "." (rule 4); workflow .github/workflows/pages.yml created (checkout v7, upload-pages-artifact v5, deploy-pages v5); Pages build_type workflow; run https://github.com/octo/tea-club/actions/runs/123 success; 2 root-absolute links rewritten in index.html (/css/style.css, /about.html)
Uncertainty: none beyond these checks; the page was not reviewed visually
Decision: No approval needed
Log: .pages-publish/run-20261013T101500Z.md
```

Show the URL only as PUBLISHED after the live check passed. PARTIAL names the step that
failed and the URL to try once that step is fixed. When grading runs, also check four
things. A reader finds the result first. Verified facts are separated from
assumptions. Each claim traces to a command or a log row. The next decision is stated.
Without a human review, mark understanding as unconfirmed.

## Edge Cases

- The target is the current repo, but the checkout is on a feature branch or has unpushed commits: use a fresh clone, then tell the user that their local default branch is behind `origin`.
- The content is a framework or site-generator project: `check-site` returns `needs-build`. Report BLOCKED with the Decision "build it, then publish the output folder".
- The content is already the site folder in the workspace: `sync-site` copies nothing and only refreshes the manifest.
- `CNAME` in the site folder is never deleted. The custom domain itself lives in the Pages settings.
- Files whose names start with `.` are never deployed. `check-site` warns about them.
- The repo name is `<owner>.github.io`: a user site at the domain root. No `/<name>/` prefix applies.

## Acceptance Criteria

- [ ] The run log has one row per step that ran, including every gate's answer.
- [ ] No repo was created, and no repo's visibility changed, without a logged yes or a pre-authorization.
- [ ] The commit holds only the paths in `paths.txt`.
- [ ] `verify` exited 0 before any URL was reported as PUBLISHED.
- [ ] The final report has Result, Evidence, Uncertainty, Decision, and Log.

## Reference files

- `references/content-prep.md`: the Text-branch brief, the fallback template steps, ready-file rules, and check-site error handling (Step 3).
- `references/troubleshooting.md`: symptom → cause → fix for push, Pages, runs, and the live check (Steps 6–7).
- `assets/pages-workflow.yml`: the managed workflow template that `workflow` renders.
- `assets/text-page.html`: the fallback page shell when `frontend-design` is unavailable (Step 3).
