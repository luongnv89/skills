---
name: install-script-generator
description: "Generate cross-platform install scripts for any software or library — a standalone install.sh runnable via a curl/wget one-liner with OS, arch, and package manager detection. Don't use for Dockerfiles, CI/CD pipelines, or one-off shell scripts."
license: MIT
effort: high
metadata:
  version: 2.3.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Install Script Generator

Generate robust, cross-platform installation scripts that users can run with a **single bash command** via GitHub raw URLs. This SKILL.md is a lean index — long templates and tables live under `references/` to protect the agent's context budget.

## When to Use

- The user asks for a `curl | bash` one-liner for their project.
- A repo needs a `install.sh` that auto-detects OS, arch, and package manager.
- A Python/Go/Node/Rust module should be installable in one command from a fresh machine.

Skip this skill for Dockerfiles, CI/CD pipelines, or one-off local shell scripts.

## Prerequisites

- The repo has a known `<owner>/<repo>` (check `git remote -v`) and a default branch.
- The target software's build system is identifiable (`Makefile`, `package.json`, `setup.py`, `Cargo.toml`, `go.mod`, etc.).
- `python3` is available locally for the helper scripts under `scripts/`. If `python3` is missing, skip each helper-script step, record it as `not run (python3 not found)`, and continue; the run then ends `PARTIAL`.

## Reference Files (read on demand to save tokens)

| File | When to read |
|------|--------------|
| `references/install-template.md` | When generating `install.sh` — full bash template with detection helpers, dependency installer, and main entry point |
| `references/readme-snippet.md` | When updating the README — copy-paste install block plus URL format notes |
| `references/edge-cases.md` | When handling unusual OS/sudo/path scenarios and writing step reports |
| `references/final-report.md` | When writing the final report — the four parts, status rules, outcome table, examples, reader checks |
| `scripts/env_explorer.py` | Local environment probe (OS, arch, package managers, sudo) |
| `scripts/plan_generator.py` | Generates `installation_plan.yaml` from env + target |
| `scripts/executor.py` | Dry-runs `installation_plan.yaml` with rollback, before Phase 3 generation |
| `scripts/doc_generator.py` | Renders user-facing `USAGE_GUIDE.md` |

Do not inline these contents into the conversation; link to them to preserve the context window.

## Repo Sync Before Edits (mandatory)

Run this once, before Phase 1. Before creating, updating, or deleting files in an existing repo, sync the current branch with remote:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If the working tree is dirty, `git stash push -u -m pre-sync` first, sync, then `git stash pop`. If `origin` is missing or rebase/stash conflicts occur, stop and ask the user before continuing.

## Workflow

A **fix attempt** is one edit followed by a rerun of the failed check. Stop after 3 fix attempts on the same check, record the check as failed, and continue to the next phase. To **stop with `BLOCKED`**, skip the remaining phases and print the final report.

### Phase 1 — Exploration

1. Identify the target software/module/tool. If the user did not name it and the repo holds more than one buildable project, ask which one.
2. Inspect the repo for build files (`Makefile`, `package.json`, `setup.py`, `Cargo.toml`, `go.mod`, ...).
3. Record the install method: the package name, if the target is published in a package manager, or the build-and-copy commands from its build file. If neither exists, ask the user. If the user gives no install method, stop with `BLOCKED`.
4. List dependencies the software needs to build and run.
5. Run `git remote get-url origin` to read `<owner>/<repo>`.
6. Run `git symbolic-ref --short refs/remotes/origin/HEAD` and strip `origin/` to read the default branch.
7. If step 5 or step 6 fails, ask the user for the value. If the user gives no answer, stop with `BLOCKED`.
8. Run `python3 scripts/env_explorer.py` to capture OS, arch, package managers, shell, and sudo availability into `env_info.json`.

### Phase 2 — Planning

1. Order the dependencies so each one installs before anything that needs it.
2. For each dependency, note the `command -v <dep>` check `install.sh` uses to skip one that is already installed.
3. Run `python3 scripts/plan_generator.py --target "<name>" --env-file env_info.json --deps <dep1> <dep2> ...` (dependencies from step 1, space-separated; omit `--deps` only if there are none) to emit `installation_plan.yaml`.
4. If the target is not published in the detected package manager, edit the `Install <name>` step in `installation_plan.yaml`: set `command`, `verify`, and `rollback` to the commands `install_<tool>` will run.
5. Replace every `# TODO` placeholder in the plan. Add a step for each dependency that `plan_generator.py` warned it left out.
6. Run `python3 scripts/executor.py --plan installation_plan.yaml --dry-run`.
7. Check the dry run: it exits 0, its last summary line starts `DRY RUN:`, stderr has no `placeholder command` warning, the steps follow the step 1 order, and every `Install ...` step has a non-null `rollback`. The package-manager check and final verify steps carry `rollback: null` by design. If a check fails, fix the plan and rerun step 6.

The dry run skips execution, so it checks the plan's shape, not that installation or rollback actually works.

### Phase 3 — Generation (primary output)

If `install.sh` already exists at the repo root, show the user the planned changes and ask before overwriting it. If the user declines, stop with `BLOCKED`.

Generate `install.sh` at the repo root using `references/install-template.md`. The template contains four sections you compose:

1. Header + colour helpers (`info`, `ok`, `warn`, `err`, `die`).
2. Detection helpers (`detect_os`, `detect_arch`, `detect_package_manager`, `need_sudo`).
3. `install_deps` switch covering apt/dnf/yum/pacman/brew/zypper.
4. `install_<tool>` (customised per target), `verify_installation`, and `main`.

Read `references/install-template.md` for the exact code; do not paste it into chat. If Windows support is needed, also generate `install.ps1` (one-liner: `irm <raw_url> | iex`).

Then check the script. If a check fails, fix `install.sh` and rerun that check:

1. `bash -n install.sh` exits 0.
2. `grep -nE '<owner>|<repo>|<branch>|<software_name>|<Software Name>|install_<tool>' install.sh` prints nothing.
3. If `shellcheck` is on PATH, `shellcheck -S error install.sh` exits 0. Otherwise record `shellcheck not run (not on PATH)`.

Do not run `install.sh` on the user's machine: it installs software and may call `sudo`. Run it only when the user asks for a local run or approves a disposable container. When it runs, its last line must be `[ OK ]  Installation complete!`.

### Phase 4 — Documentation

1. Insert the install block from `references/readme-snippet.md` into the project README, substituting `<owner>/<repo>/<branch>`. If the repo has no README, create `README.md` holding only that block.
2. Run `python3 scripts/doc_generator.py --target "<name>" --plan installation_plan.yaml` to emit `USAGE_GUIDE.md`.
3. Run `grep -n "raw.githubusercontent.com/<owner>/<repo>/<branch>/install.sh" <README>` with the real values; it must print one or more lines.
4. If `git ls-tree --name-only origin/<branch> install.sh` prints `install.sh`, run `curl -fsSI <raw-url>` and record the HTTP status. Otherwise record `raw URL not live until install.sh is pushed`.
5. Print the final report.

## Final Report

Print it once, as plain text in the chat, after the last Step Completion Report. Four parts, in order: `Result:` (status, target, one-liner), `Evidence:` (only checks that ran, with results), `Uncertainty:` (untested behavior, including `install.sh was not executed`), and `Decision:` (the approval needed, or `No approval needed.`, then the push and cleanup actions). Read `references/final-report.md` for each part's contents, the outcome table, and examples.

Apply the first status rule that matches:

1. `BLOCKED — <reason>` — `install.sh` was not written.
2. `PARTIAL — <reason>` — `install.sh` was written, and a required check failed or did not run: `bash -n`, the placeholder `grep`, `shellcheck -S error` (when on PATH), the Phase 2 dry run, the README one-liner, `USAGE_GUIDE.md`, or an approved run of `install.sh` that did not end with `[ OK ]  Installation complete!`.
3. `COMPLETE` — every required check passed. `COMPLETE` does not mean `install.sh` ran.

## Output Files

| File | Description |
|------|-------------|
| `install.sh` | Primary output — standalone installer for `curl \| bash` |
| `install.ps1` | Optional Windows PowerShell installer |
| `USAGE_GUIDE.md` | User-facing docs |
| `env_info.json` | Local environment probe (working file) |
| `installation_plan.yaml` | Ordered install steps (working file) |
| `install_report.md` | Dry-run report from `executor.py` (working file) |

The three working files hold this machine's home path and `PATH`. Do not commit them unless the user asks; list them under `Decision:` for cleanup.

## Acceptance Criteria

- `install.sh` exists at repo root, starts with `#!/usr/bin/env bash` and `set -euo pipefail`, and passes the three Phase 3 checks.
- Auto-detects OS, architecture, and package manager; exits non-zero with a clear message on unsupported targets.
- Handles `sudo` gracefully (root, sudo, or fail-fast).
- Verifies the installation at the end (`command -v $TOOL_NAME` plus `--version` when available).
- README contains a `curl -sSL ... | bash` one-liner that points at the raw GitHub URL for `<owner>/<repo>/<branch>`.
- When `install.sh` runs successfully, its last line is `[ OK ]  Installation complete!`.
- The final report opens with `Result:` and a status from the rules above, and meets the four reader checks in `references/final-report.md`: result findable, facts apart from assumptions, claims traceable, next decision clear.

## Edge Cases

See `references/edge-cases.md` for the full list. Highlights:

- **Unsupported OS / architecture** — `die` with the detected value; user sees what failed.
- **No package manager** — `install_deps` aborts with `Unsupported package manager 'unknown'`.
- **No sudo** — `need_sudo` exits with `Requires root. Run as root or install sudo.`
- **Windows native** — generate `install.ps1` separately; `install.sh` warns under MSYS/Cygwin.
- **Script in subdirectory** — adjust the raw URL path; note it in the README snippet.
- **Target not in a package manager** — edit its plan step (Phase 2 step 4) and write `install_<tool>` from the build file.

## Step Completion Reports

After each phase, emit a `◆` block with `√`/`×` checks and a `Result: PASS | FAIL | PARTIAL` line; the format and per-phase checks are in `references/edge-cases.md`.

## Expected Output

The final report for a complete run (full example in `references/final-report.md`):

```text
Result: COMPLETE — mytool installer
  curl -sSL https://raw.githubusercontent.com/owner/mytool/main/install.sh | bash
Evidence:
  bash -n install.sh: exit 0; placeholder grep: no matches; shellcheck -S error: exit 0
  executor.py --dry-run: "DRY RUN: 5 step(s) listed for mytool; nothing was executed."
Uncertainty:
  install.sh was not executed. Raw URL not live until install.sh is pushed to main.
Decision: No approval needed.
  Remaining action: commit and push install.sh; delete the three working files.
```

When a user later runs the one-liner, the script's banner ends:

```
[INFO]  OS: linux | Arch: x86_64 | Package Manager: apt
[ OK ]  Dependencies installed
[ OK ]  mytool 1.2.0 installed
[ OK ]  Installation complete!
```
