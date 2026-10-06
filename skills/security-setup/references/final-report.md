# Final report

Every security-setup run ends with one final report, printed after the last
Step Completion Report. A run that stops early still prints it. The report is
plain text: a setup run is a quick operation, so there is nothing to filter or
expand.

A **repository write** is any of: creating or changing `.pre-commit-config.yaml`,
`scripts/security_check.py`, `security/semgrep-rules.yml`,
`security/security-tools.json`, `SECURITY.md`, or `.github/workflows/security.yml`;
creating a `<path>.bak`; or running `pre-commit install`.

## Four required parts, in this order

1. **`Result:`** — the status word first, then one line on what changed or was found. Pick the first status whose rule matches:
   - `BLOCKED — <reason>` — the run stopped before its first repository write. Causes: a failed prerequisite (no git repository, no Python 3.8+), Repo Sync stopped (missing `origin`, a rebase or stash conflict) and the user did not approve continuing, or the user declined every file in the Step 3 dry run.
   - `PARTIAL — <reason>` — the run was not blocked, and any of these holds: the user declined some files; `pre-commit` is not installed; a verification command exited non-zero (exit `1` with `HIGH` or `CRITICAL` findings, or exit `2` because the runner could not run); a selected tool is still missing, so its category is uncovered; a scanner database is not warmed (network-restricted setup); or `--ci` was requested and the workflow was not created because a Phase 2 precondition failed.
   - `COMPLETE` — none of the above holds: every confirmed file was written, every selected tool is installed, `python3 scripts/security_check.py --all --no-fail-on-missing-tools` and `pre-commit run security-check --all-files` both exited 0, both report files exist, and `security/security-report.json` parses with a top-level `summary` object. With `--ci`, `.github/workflows/security.yml` was also written. A run on a repository that already matches the planned content, so it writes nothing, is `COMPLETE` when both verification commands exit 0.
2. **`Evidence:`** — only checks that ran, each with its command or file and the observed result: the detected languages and lockfiles, the selected tools, each file written (with its `.bak` path when one was made), the exit code of each verification command, the report paths, and the finding counts by severity. Never list a check that did not run.
3. **`Uncertainty:`** — what is unknown or untested, labeled apart from verified facts: each missing tool and its uncovered category, each offline gap recorded in `SECURITY.md`, each declined file, and each check that did not run. Verification uses `--all`, so state that staged-file scoping was not exercised by a real commit unless one was made. With `--ci`, state that the workflow has not run on GitHub yet.
4. **`Decision:`** — the action that needs the user's approval, or `No approval needed.` Pending approvals include: confirming a declined or pending overwrite, installing a missing tool, deleting a `<path>.bak`, and choosing between fixing `HIGH`/`CRITICAL` findings and the `YES`-confirmed bypass (only the user can type `YES`). Name each other remaining user action on its own line, such as committing the new files or warming a scanner database once the network is available.

Map the Step Completion Report to the status: `Result: PASS` → `COMPLETE`; `PARTIAL` → `PARTIAL`; `FAIL` → `BLOCKED` when one of the `BLOCKED` causes stopped the run, otherwise `PARTIAL`.
If a run matches none of the rules above, report `PARTIAL` and name the unmatched
outcome in `Uncertainty:`; never report `COMPLETE` by default.

## Example: a complete setup

```text
Result: COMPLETE — local security hook added for a Python repo
Evidence:
  Detected: Python (pyproject.toml, requirements.txt); no existing .pre-commit-config.yaml
  Tools: gitleaks (secrets), trivy (dependencies), semgrep + bandit (static analysis)
  Wrote: .pre-commit-config.yaml, scripts/security_check.py, security/semgrep-rules.yml,
         security/security-tools.json, SECURITY.md (all new, no .bak needed)
  python3 scripts/security_check.py --all --no-fail-on-missing-tools: exit 0
  pre-commit run security-check --all-files: exit 0
  Reports: security/security-report.json (valid, has summary), security/security-report.md
  Findings: 0
Uncertainty:
  Staged-file scoping was not exercised by a real commit; verification used --all.
Decision:
  No approval needed.
  Commit the new files.
```

## Example: a partial setup

```text
Result: PARTIAL — hook installed, but 1 HIGH dependency finding blocks commits
Evidence:
  Wrote: .pre-commit-config.yaml (merged; backup .pre-commit-config.yaml.bak), SECURITY.md (new), ...
  python3 scripts/security_check.py --all --no-fail-on-missing-tools: exit 1
  Findings: HIGH=1 (dependencies/trivy, CVE-XXXX-XXXX in <pkg>, package-lock.json)
Uncertainty:
  semgrep is not installed, so static analysis is not covered yet.
Decision:
  Choose: upgrade <pkg> to <version>, or run the YES-confirmed bypass in SKILL.md §4.
  Approve installing semgrep (python3 -m pip install semgrep).
  Delete .pre-commit-config.yaml.bak once the merged config is confirmed.
```

## Reader checks

A reader of the report can:

- find the status and what changed on the first line, without reading logs;
- tell verified checks (`Evidence:`) from assumptions and untested behavior (`Uncertainty:`);
- trace each claim to a command, exit code, or file;
- name the next decision, or see `No approval needed.`

An agent can check that the report meets these points. Only the user's
feedback confirms that a human understood it; without that feedback, report
human understanding as unconfirmed.
