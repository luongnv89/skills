# Final Report — install-script-generator

Print the final report once per run, after the last Step Completion Report. The step reports score each check; the final report tells the user what was generated, what proves it, what is still unknown, and what they must decide.

Format: plain text in the chat. Do not write a report file unless the user asks for one. If the user asks for a file, write the same four parts to the path they name.

## Four required parts, in this order

1. **`Result:`** — the status word first, then the target name and the one-liner.
2. **`Evidence:`** — only checks that ran, each with its command and the observed result:
   - each file created or modified (`install.sh`, `install.ps1`, the README, `USAGE_GUIDE.md`)
   - `bash -n install.sh` exit code
   - the placeholder `grep` result (`no matches`, or the lines found)
   - `shellcheck -S error install.sh` exit code, or `shellcheck not run (not on PATH)`
   - the `executor.py --dry-run` summary line (`DRY RUN: N step(s) listed ...`) and any placeholder warning it printed
   - the README line holding the one-liner
   - `curl -fsSI <raw-url>` status, only when it was run (Phase 4 runs it only when `install.sh` is already on `origin/<branch>`)
   - the last line of `install.sh` output, only when an approved run happened

   Never list a check that did not run.
3. **`Uncertainty:`** — what is unknown or untested, labeled apart from verified facts:
   - `install.sh was not executed` when no approved run happened
   - each OS, architecture, and package manager the script handles but no run covered
   - `raw URL not live until install.sh is pushed to <branch>` when the `curl` check did not return 200. A 200 shows only that a file exists at that URL, not that it matches the local `install.sh`
   - `install.ps1 not verified` when it was generated and not run
   - each helper script recorded as `not run`, and why
   - each value the user did not confirm (target name, install method, branch)

   Write `none` only when every item above is empty.
4. **`Decision:`** — the action that needs the user's approval, or `No approval needed.` A pending approval is a local or container run of `install.sh`. Name each other remaining user action on its own line: committing and pushing `install.sh` so the one-liner resolves, and deleting or ignoring the local working files (`env_info.json`, `installation_plan.yaml`, `install_report.md`), which hold this machine's home path and `PATH`.

## Status rules

Apply the first rule that matches. SKILL.md *Final Report* carries the same three rules.

| Order | Status | When |
|-------|--------|------|
| 1 | `BLOCKED — <reason>` | `install.sh` was not written. |
| 2 | `PARTIAL — <reason>` | `install.sh` was written, and at least one required check failed or did not run (list below). |
| 3 | `COMPLETE` | `install.sh` passes `bash -n`, the placeholder `grep`, and `shellcheck -S error` (or shellcheck is not on PATH); the dry run printed its `DRY RUN:` line with no placeholder warning; the README holds the one-liner; `USAGE_GUIDE.md` was written. |

The required checks for rule 2: `bash -n`; the placeholder `grep`; `shellcheck -S error` when shellcheck is on PATH; the Phase 2 dry run; the README one-liner; `USAGE_GUIDE.md`. An approved run of `install.sh` is optional, but once it runs, its last line must be `[ OK ]  Installation complete!`.

`COMPLETE` means generated and statically checked. It does not mean `install.sh` ran; `Uncertainty:` says whether it did.

How each run outcome maps:

| Outcome | Status |
|---------|--------|
| Target or `<owner>/<repo>` unknown and the user gives no answer | `BLOCKED` |
| No install method found (no package, no build file) and the user gives none | `BLOCKED` |
| Repo Sync conflict, or missing `origin` the user did not approve working around | `BLOCKED` |
| `install.sh` already exists and the user declines overwriting it | `BLOCKED` |
| `bash -n` or the placeholder `grep` still fails after 3 fix attempts | `PARTIAL` |
| `shellcheck -S error` still exits non-zero after 3 fix attempts | `PARTIAL` |
| `python3` missing, so the plan, dry run, and `USAGE_GUIDE.md` did not run | `PARTIAL` |
| A helper script exits non-zero and the error is not fixed | `PARTIAL` |
| Dry run still warns about a placeholder command | `PARTIAL` |
| An approved run of `install.sh` does not end with `[ OK ]  Installation complete!` | `PARTIAL` |
| shellcheck not on PATH; every other check passes | `COMPLETE` (list it under `Uncertainty:`) |
| No README existed, so `README.md` was created with the install block; every other check passes | `COMPLETE` |
| `install.sh` not executed; every other check passes | `COMPLETE` (list it under `Uncertainty:`) |

Map a step report to the status: a phase `Result: PASS` does not by itself make the run `COMPLETE`. A phase `Result: FAIL` gives `BLOCKED` when `install.sh` was not written, otherwise `PARTIAL`.

## Example: a complete run

```text
Result: COMPLETE — mytool installer
  curl -sSL https://raw.githubusercontent.com/owner/mytool/main/install.sh | bash
Evidence:
  Files: install.sh (created), README.md (Installation section added), USAGE_GUIDE.md (created)
  bash -n install.sh: exit 0
  Placeholder grep: no matches
  shellcheck -S error install.sh: exit 0
  executor.py --dry-run: "DRY RUN: 5 step(s) listed for mytool; nothing was executed." No placeholder warning.
  README.md:42 holds the curl one-liner
Uncertainty:
  install.sh was not executed.
  apt, dnf, yum, pacman, zypper and brew branches untested; only the macOS arm64 environment was probed.
  Raw URL not live until install.sh is pushed to main.
Decision: No approval needed.
  Remaining action: commit and push install.sh, README.md and USAGE_GUIDE.md to main.
  Remaining action: delete env_info.json, installation_plan.yaml and install_report.md, or add them to .gitignore.
```

## Example: a partial run

```text
Result: PARTIAL — mytool installer; python3 is not installed, so the plan dry run and USAGE_GUIDE.md did not run
  curl -sSL https://raw.githubusercontent.com/owner/mytool/main/install.sh | bash
Evidence:
  Files: install.sh (created), README.md (Installation section added)
  bash -n install.sh: exit 0
  Placeholder grep: no matches
Uncertainty:
  env_explorer.py, plan_generator.py, executor.py and doc_generator.py not run: python3 not found.
  shellcheck not run (not on PATH).
  install.sh was not executed.
Decision: No approval needed.
  Remaining action: install python3 and rerun Phases 2 and 4, or write USAGE_GUIDE.md by hand.
```

## Reader checks

Judge the final report against these four checks, alongside the Acceptance Criteria in SKILL.md:

- **Main result is findable.** The first line states the status and the one-liner without scrolling through step reports.
- **Facts and assumptions are separated.** Every `Evidence:` line names a check that ran and its observed result; untested behavior appears only under `Uncertainty:`.
- **Claims are traceable.** A dry run or `bash -n` pass is not reported as a working installation, and the one-liner is not called live without a 200 from `curl -fsSI`.
- **Next decision is clear.** `Decision:` names the approval needed, or says `No approval needed.`, and lists the push and cleanup actions left to the user.

When a human reviews the report, ask whether they could find the result, separate facts from assumptions, trace each claim, and name the next decision. Without a response, human understanding is unconfirmed; agent inspection cannot confirm it.
