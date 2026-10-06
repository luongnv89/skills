# Final Report — oss-ready

Print the final report once per run, after the last Step Completion Report. The step reports score each check. The final report tells the user what changed, what proves it, what is still unknown, and what they must decide.

Format: plain text in the chat. Do not write a report file unless the user asks for one. If the user asks for a file, write the same four parts to the path they name. Never add the report to the target repo.

## Four required parts, in this order

1. **`Result:`** the status word first, then the target repo and the branch.
2. **`Evidence:`** only checks that ran, each with its command or file and the observed result:
   - each file created, and each file updated with a short note of what was added
   - each Acceptance Criteria check with `pass`, `fail` or `not applicable` and its reason
   - the placeholder `grep` result: `no matches`, or each `file:line` found
   - the deletion check result (`git status --porcelain` shows no deleted file)

   Never list a check that did not run.
3. **`Uncertainty:`** what is unknown or untested, labeled apart from verified facts:
   - each placeholder left, and the value it needs
   - each check that did not run, and why (for example, `python3` missing for the Step 5 parse check)
   - `Repo Sync skipped (no origin)` when the user approved working without `origin`
   - `visibility unknown` when `gh repo view` could not run
   - `README commands not executed`: the run copies commands from the repo but does not run them
   - each section left out because the code gave no source for it (`Manual review`)

   Write `none` only when every item above is empty.
4. **`Decision:`** the action that needs the user's approval, or `No approval needed.` Name each other remaining action on its own line: each value to fill, each `Manual review` item, and reviewing and committing the branch. The run does not commit or push.

## Status rules

Apply the first rule that matches. SKILL.md *Final Report* carries the same three rules.

| Order | Status | When |
|-------|--------|------|
| 1 | `BLOCKED — <reason>` | No file in the target repo was created or changed. |
| 2 | `PARTIAL — <reason>` | At least one file was created or changed, and at least one of these holds: an applicable Acceptance Criteria check failed or did not run; the placeholder `grep` found a match; a step reported `Result: FAIL` or `Result: PARTIAL`; the run stopped before Step 7 finished. |
| 3 | `COMPLETE` | Every applicable Acceptance Criteria check passed, the placeholder `grep` found no match, and every step from 1 to 7 reported `Result: PASS`. |

**Not applicable** is allowed only for these reasons. Any other skipped check counts as "did not run".

- The repo is private or internal, and the user declined `SECURITY.md` or the GitHub templates.
- The manifest format has no such fields (`go.mod`), or the repo has no manifest.
- A root `CHANGELOG.md` exists, so `docs/CHANGELOG.md` was not created.
- The user approved working without an `origin` remote, so the `repository` metadata field has no source.

An existing non-MIT `LICENSE` is not a skip. Its check is "the file is unchanged", and it passes or fails like any other check.

## How each run outcome maps

| Outcome | Status |
|---------|--------|
| Not a git repository, or detached HEAD | `BLOCKED` |
| Stash, fetch, pull or stash restore fails | `BLOCKED` |
| No `origin` remote, and the user does not approve working without it | `BLOCKED` |
| Branch creation fails, or the user declines every branch option | `BLOCKED` |
| No detectable language, and the user gives no stack | `BLOCKED` |
| The user stops the run before Step 2 writes a file | `BLOCKED` |
| The user gives no security or conduct contact, so a placeholder remains | `PARTIAL` |
| No copyright holder found, and the user gives none | `PARTIAL` |
| A manifest edit fails to parse and is written back (Step 5 `FAIL`) | `PARTIAL` |
| `python3` missing, so the Step 5 parse check did not run | `PARTIAL` |
| The user stops the run after Step 2 wrote a file | `PARTIAL` |
| The deletion check finds a deleted file | `PARTIAL`, even after the file is restored. Restore it before reporting and list it under `Uncertainty:` |
| Private repo; the user declined `SECURITY.md` and templates; every other check passes | `COMPLETE` (list the declined files under `Evidence:` as not applicable) |
| Existing Apache-2.0 `LICENSE` kept unchanged; every other check passes | `COMPLETE` |
| `gh` unavailable, so visibility is unknown; every other check passes | `COMPLETE` (list it under `Uncertainty:`) |
| `docs/DEPLOYMENT.md` skipped because the repo has no deploy or publish step; every other check passes | `COMPLETE` (list it under `Manual review`) |

Map a step report to the status. A step `Result: PASS` does not by itself make the run `COMPLETE`. A step `Result: FAIL` or `Result: PARTIAL` gives `BLOCKED` when no file was written yet, otherwise `PARTIAL`.

## Example: a partial run

```text
Result: PARTIAL — acme/linkcheck on feat/oss-ready: 2 placeholders remain
Evidence:
  Created: LICENSE (MIT, 2026 Jane Doe), CONTRIBUTING.md, CODE_OF_CONDUCT.md,
           SECURITY.md, .github/ISSUE_TEMPLATE/bug_report.md,
           .github/ISSUE_TEMPLATE/feature_request.md,
           .github/PULL_REQUEST_TEMPLATE.md, docs/ARCHITECTURE.md,
           docs/DEVELOPMENT.md, docs/CHANGELOG.md
  Updated: README.md (+ Installation, Usage, License), .gitignore (+ *.exe, .env)
  Acceptance criteria: 10 pass, 2 fail (SECURITY.md contact, placeholder grep),
    1 not applicable (metadata: go.mod has no license field)
  Placeholder grep: CODE_OF_CONDUCT.md:47 [INSERT CONTACT METHOD],
                    SECURITY.md:16 [INSERT SECURITY EMAIL]
  Deletion check: no deleted files
Uncertainty:
  Conduct and security contacts not given.
  README commands copied from the Makefile, not executed.
  docs/DEPLOYMENT.md not created: no deploy or publish step in the repo.
Decision: No approval needed.
  Remaining action: replace [INSERT CONTACT METHOD] in CODE_OF_CONDUCT.md:47.
  Remaining action: replace [INSERT SECURITY EMAIL] in SECURITY.md:16.
  Remaining action: review and commit feat/oss-ready.
```

## Example: a blocked run

```text
Result: BLOCKED — /work/notes: not a git repository
Evidence:
  git rev-parse --git-dir: exit 128
  No file created or changed.
Uncertainty: none
Decision: No approval needed.
  Remaining action: run `git init`, or point the skill at the repository root.
```

## Example: a Step Completion Report

Each of Steps 1-7 prints one before the final report:

```text
◆ Analysis (step 1 of 7 — project profiling)
··································································
  Language detected:       √ pass — TypeScript (primary)
  Project type identified: √ pass — CLI tool
  Existing docs found:     √ pass — README.md (partial), no LICENSE
  [Criteria]:              √ 3/3 met
  ____________________________
  Result:                  PASS
```

## Reader checks

Judge the final report against these four checks, alongside the Acceptance Criteria in SKILL.md:

- **Main result is findable.** The first line states the status, the repo and the branch, without scrolling through step reports.
- **Facts and assumptions are separated.** Every `Evidence:` line names a check that ran and its observed result. Untested behavior, such as README commands that were not executed, appears only under `Uncertainty:`.
- **Claims are traceable.** A created file is not reported as filled in while the placeholder `grep` still finds a match. A step `PASS` is not reported as a `COMPLETE` run.
- **Next decision is clear.** `Decision:` names the approval needed, or says `No approval needed.`, and lists each value to fill and the commit left to the user.

When a human reviews the report, ask whether they could find the result, separate facts from assumptions, trace each claim, and name the next decision. Without a response, human understanding is unconfirmed. Agent inspection cannot confirm it.
