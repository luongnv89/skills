---
name: oss-ready
description: "Transform a project into a professional open-source repository by adding LICENSE, README, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, and GitHub issue/PR templates. Don't use for documentation overhauls, landing-page generation, or registry publishing."
license: MIT
effort: low
metadata:
  version: 1.4.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# OSS Ready

Transform a project into a professional open-source repository with standard community files and GitHub templates.

Two terms are used throughout:

- **Additive edit**: on a file that already exists, add only missing sections or lines. Never replace, reword, translate or delete the user's content.
- **Placeholder**: a match of `PH='\[(YEAR|COPYRIGHT HOLDER|INSERT [A-Z ]+)\]|TODO|TBD|FIXME'` in a created file, or in a line the run added to an existing file.

## Repo Sync Before Edits (mandatory)

Prerequisites: a git repository on a named branch with an `origin` remote. Run the block in `references/repo-sync.md` once, before Step 0. It stops at the first failure:

1. Stop when `git rev-parse --git-dir` fails (not a git repository).
2. Stop when `git symbolic-ref --quiet --short HEAD` fails (detached HEAD), before any stash or sync.
3. Stop and ask the user when `git remote get-url origin` fails.
4. If `git status --porcelain` prints a line, stash with `git stash push -u`.
5. Run `git fetch origin && git pull --rebase origin "$branch"`.
6. Restore the stash with `git stash pop --index`.

On a non-zero exit, print the final report with `BLOCKED` and the recovery commands the block printed. Never discard changes. If the only failure is the missing `origin` and the user approves continuing, go to Step 0 and list `Repo Sync skipped (no origin)` under `Uncertainty:`.

## Workflow

> Before Step 0, check `references/edge-cases.md`. If a case matches the repo, handle it as written there first.

### Step 0: Create Feature Branch

1. Read the current branch: `git branch --show-current`.
2. Read the default branch: `git symbolic-ref --short refs/remotes/origin/HEAD`, without the `origin/` prefix. If that fails, use `main`, or `master` when only `master` exists.
3. If the current branch is not the default branch and its name contains `oss`, stay on it and go to Step 1.
4. Choose the prefix `feature/` when `git branch -a --format='%(refname:short)'` lists more `feature/` than `feat/` branches; otherwise `feat/`.
5. If `<prefix>oss-ready` exists, ask the user to reuse it or to give another name. Never reset an existing branch.
6. Run `git switch -c <prefix>oss-ready`, or `git switch <name>` to reuse. If it fails, stop with `BLOCKED`.

### Step 1: Analyze Project

Record the stack, purpose, existing files, license, repo URL, README language, visibility and fill values, as `references/file-specs.md` → *Analysis values* describes. Ask for the security and conduct contacts in one question. If no stack is detectable, ask which stack to assume.

### Step 2: Create/Update Core Files

Write `README.md` and `CONTRIBUTING.md` from the Step 1 values. Copy `LICENSE` from `assets/LICENSE-MIT` unless one exists or the user names another license. Copy `CODE_OF_CONDUCT.md` (Contributor Covenant 2.0) and `SECURITY.md` from `assets/`. Replace each placeholder with its Step 1 value. Section lists and per-file rules: `references/file-specs.md`.

Take every usage example from the repo's code, scripts or `--help` output. Never invent a command or contact. A section with no source in the code is left out and listed under `Manual review`.

### Step 3: Create GitHub Templates

Copy each missing file from `assets/.github/`: `ISSUE_TEMPLATE/bug_report.md`, `ISSUE_TEMPLATE/feature_request.md`, `PULL_REQUEST_TEMPLATE.md`. Keep every existing file and workflow under `.github/` unchanged.

### Step 4: Create Documentation Structure

Create each missing file. Skip rules and contents: `references/file-specs.md` → *docs/*.

```
docs/
├── ARCHITECTURE.md    # System design, components
├── DEVELOPMENT.md     # Dev setup, debugging
├── DEPLOYMENT.md      # Production deployment
└── CHANGELOG.md       # Version history (skip when a root CHANGELOG.md exists)
```

### Step 5: Update Project Metadata

Add each missing `license`, `description` and `repository` field to the root manifest. Never overwrite a field that has a value. Parse the file after the edit. Per-stack fields and parse commands: `references/file-specs.md` → *Project metadata*.

### Step 6: Ensure .gitignore

Append each missing pattern for the stack from `references/file-specs.md` → *.gitignore*. Check one pattern with `grep -qxF '<pattern>' .gitignore`. Never remove a line.

### Step 7: Verify and Report

1. Run every Acceptance Criteria check. Record `pass`, `fail` or `not applicable` with its reason.
2. Set `PH` as defined in **Placeholder** above. Run the placeholder `grep` on each created file: `grep -nE "$PH" <file>`.
3. Run it on the lines added to each updated file: `git diff -U0 -- <file> | grep -E '^\+' | grep -E "$PH"`.
4. Run `git status --porcelain`. Confirm that no line starts with ` D` or `D `.
5. Print the final report.

Do not commit or push. The user reviews and commits the branch.

## Step Completion Reports

After each of Steps 1-7, print a report in this format (example: `references/final-report.md`):

```
◆ [Step Name] ([step N of 7] — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          × fail — [reason]
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Name each check after what the step validates. Step 0 gets no report. If Step 0 or 1 fails, stop with `BLOCKED`. If one of Steps 2-6 reports `FAIL` or `PARTIAL`, continue; the run ends `PARTIAL`. Step 7 runs whenever a file was written.

## Final Report

Print one final report in the chat after the last step report; write a file only on request. Four parts, in order:

1. **`Result:`** the status word, the repo and branch, and the reason for `PARTIAL` or `BLOCKED`.
2. **`Evidence:`** files created and updated, and the result of each Step 7 check that ran.
3. **`Uncertainty:`** placeholders left, checks not run and why, and untested behavior.
4. **`Decision:`** the approval needed, or `No approval needed.`, then each remaining user action.

Apply the first status rule that matches:

1. **`BLOCKED`**: no file in the target repo was created or changed.
2. **`PARTIAL`**: a file was created or changed, and an applicable check failed or did not run, a placeholder remains, a step reported `FAIL` or `PARTIAL`, or the run stopped before Step 7 finished.
3. **`COMPLETE`**: every applicable check passed, the placeholder `grep` found no match, and Steps 1-7 each reported `PASS`.

`not applicable` is allowed only for a reason listed in `references/final-report.md`, with the outcome table, examples and reader checks. Any other skipped check counts as not run.

## Acceptance Criteria

Step 7 runs each check with `test -f`, `grep`, `git` or a visual check.

- [ ] `LICENSE` exists. A new MIT file passes `grep -c "MIT License" LICENSE` (or the named license's title). An existing one is unchanged: `git diff --quiet -- LICENSE`.
- [ ] `README.md` is at least 40 lines with Installation, Usage, and License sections. In English, `grep -ciE "^#+ .*(install|usage|license)" README.md` returns >= 3; in another language, check the headings visually.
- [ ] `CONTRIBUTING.md` references the issue tracker plus a branching/PR workflow: `grep -iE "issue|pull request|branch" CONTRIBUTING.md`.
- [ ] `CODE_OF_CONDUCT.md` mentions the Contributor Covenant: `grep -i "contributor covenant" CODE_OF_CONDUCT.md`.
- [ ] `SECURITY.md` lists a vulnerability-reporting contact: `grep -E "@|https?://" SECURITY.md`.
- [ ] `.github/ISSUE_TEMPLATE/bug_report.md` and `feature_request.md` exist with YAML frontmatter (`name:`, `about:`).
- [ ] `.github/PULL_REQUEST_TEMPLATE.md` contains a checklist (`- [ ]`).
- [ ] Each `docs/` file the run created starts with a `#` heading: `head -1 <file>`.
- [ ] `.gitignore` contains each Step 6 pattern for the stack.
- [ ] The manifest (`package.json`, `pyproject.toml`, `Cargo.toml`) declares `license`, `description`, and `repository`, and still parses.
- [ ] The placeholder `grep` finds no match.
- [ ] No previously committed file was deleted (Step 7 item 4).
- [ ] The final report starts with `Result:` and a status word, has the other three parts, and passes the reader checks in `references/final-report.md`.

## Expected Output

A complete run on a TypeScript CLI with a partial `README.md` ends like this:

```
Result: COMPLETE — acme/tsgrep on feat/oss-ready
Evidence:
  Created: LICENSE (MIT, 2026 Jane Doe), CONTRIBUTING.md,
           CODE_OF_CONDUCT.md (conduct@acme.dev), SECURITY.md (security@acme.dev),
           .github/ISSUE_TEMPLATE/bug_report.md, feature_request.md,
           .github/PULL_REQUEST_TEMPLATE.md, docs/ (4 files)
  Updated: README.md (+ Quick Start, Usage, License badge),
           package.json (+ license, repository), .gitignore (+ dist/, .env)
  Acceptance criteria: 13/13 pass. Placeholder grep: no matches. No deleted files.
Uncertainty: README commands copied from package.json scripts, not executed.
Decision: No approval needed.
  Remaining action: confirm both contact addresses are monitored.
  Remaining action: review and commit feat/oss-ready.
```

Before printing, confirm each listed file exists (`test -f`).

## Edge Cases

Full table with detection and status effects: `references/edge-cases.md`. In short:

- **Never overwrite** an existing non-MIT LICENSE, `.github/` file, or user content in `CODE_OF_CONDUCT.md` or `SECURITY.md`.
- **Ask first** when the repo is private or internal, has no `origin`, or has no detectable stack.
- **Update only the root manifest** in a monorepo, unless the user names a sub-package.
- **Stop** on a detached HEAD, outside a git repository, or when a stash, sync or restore fails. Never discard changes.
- **Keep** the README's language and a root `CHANGELOG.md`.

## Assets and References

- `assets/`: `LICENSE-MIT`, `CODE_OF_CONDUCT.md` (Contributor Covenant 2.0), `SECURITY.md`, and `.github/` issue and PR templates
- `references/repo-sync.md`: the Repo Sync block
- `references/file-specs.md`: analysis values, per-file content, fill values, metadata, `.gitignore`
- `references/final-report.md`: status rules, outcome table, examples, reader checks
- `references/edge-cases.md`: detection, handling and status per edge case
