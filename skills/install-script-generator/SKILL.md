---
name: install-script-generator
description: "Generate cross-platform installation scripts for any software, library, or module. Produces a standalone install.sh runnable via a single curl/wget one-liner, with automatic OS, architecture, and package manager detection. Don't use for authoring Dockerfiles, CI/CD pipelines, or one-off local shell scripts."
license: MIT
effort: high
metadata:
  version: 2.1.0
  author: Luong NGUYEN <luongnv89@gmail.com>
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
- `python3` is available locally if you plan to run the helper scripts under `scripts/`.

## Reference Files (read on demand to save tokens)

| File | When to read |
|------|--------------|
| `references/install-template.md` | When generating `install.sh` — full bash template with detection helpers, dependency installer, and main entry point |
| `references/readme-snippet.md` | When updating the README — copy-paste install block plus URL format notes |
| `references/edge-cases.md` | When handling unusual OS/sudo/path scenarios and writing step reports |
| `scripts/env_explorer.py` | Local environment probe (OS, arch, package managers, sudo) |
| `scripts/plan_generator.py` | Generates `installation_plan.yaml` from env + target |
| `scripts/doc_generator.py` | Renders user-facing `USAGE_GUIDE.md` |

Do not inline these contents into the conversation; link to them. Keeping SKILL.md short preserves the context window for the actual install logic.

## Repo Sync (mandatory before edits)

Before creating, updating, or deleting files in an existing repo, sync the current branch with remote:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If the working tree is dirty, `git stash push -u -m pre-sync` first, sync, then `git stash pop`. If `origin` is missing or rebase/stash conflicts occur, stop and ask the user before continuing.

## Workflow

### Phase 1 — Exploration

1. Identify the target software/module/tool.
2. Inspect the repo for build files (`Makefile`, `package.json`, `setup.py`, `Cargo.toml`, `go.mod`, ...).
3. List dependencies the software needs to build and run.
4. Capture `<owner>/<repo>` and the default branch from `git remote -v` and `git branch --show-current`. Ask the user if missing.
5. Run `python3 scripts/env_explorer.py` to capture OS, arch, package managers, shell, and sudo availability into `env_info.json`.

### Phase 2 — Planning

1. Resolve the dependency graph and order operations.
2. Detect existing installations to avoid duplicate work.
3. Plan a verification step for each phase.
4. Plan rollback / cleanup on failure.
5. Run `python3 scripts/plan_generator.py --target "<name>" --env-file env_info.json` to emit `installation_plan.yaml`.

### Phase 3 — Generation (primary output)

Generate `install.sh` at the repo root using `references/install-template.md`. The template contains four sections you compose:

1. Header + colour helpers (`info`, `ok`, `warn`, `err`, `die`).
2. Detection helpers (`detect_os`, `detect_arch`, `detect_package_manager`, `need_sudo`).
3. `install_deps` switch covering apt/dnf/yum/pacman/brew/zypper.
4. `install_<tool>` (customised per target), `verify_installation`, and `main`.

Read `references/install-template.md` for the exact code; do not paste it into chat. If Windows support is needed, also generate `install.ps1` (one-liner: `irm <raw_url> | iex`).

### Phase 4 — Documentation

1. Insert the install block from `references/readme-snippet.md` into the project README, substituting `<owner>/<repo>/<branch>`.
2. Run `python3 scripts/doc_generator.py --target "<name>" --plan installation_plan.yaml` to emit `USAGE_GUIDE.md`.
3. Print the final one-liner so the user can copy it.

## Output Files

| File | Description |
|------|-------------|
| `install.sh` | Primary output — standalone installer for `curl \| bash` |
| `install.ps1` | Optional Windows PowerShell installer |
| `env_info.json` | Local environment probe |
| `installation_plan.yaml` | Ordered install steps |
| `USAGE_GUIDE.md` | User-facing docs |

## Acceptance Criteria

- `install.sh` exists at repo root, starts with `#!/usr/bin/env bash` and `set -euo pipefail`.
- Auto-detects OS, architecture, and package manager; exits non-zero with a clear message on unsupported targets.
- Handles `sudo` gracefully (root, sudo, or fail-fast).
- Verifies the installation at the end (`command -v $TOOL_NAME` plus `--version` when available).
- README contains a `curl -sSL ... | bash` one-liner that resolves to the raw GitHub URL.
- Expected output on success ends with `[ OK ]  Installation complete!`.

## Edge Cases

See `references/edge-cases.md` for the full list. Highlights:

- **Unsupported OS / architecture** — `die` with the detected value; user sees what failed.
- **No package manager** — `install_deps` aborts with the manager it expected.
- **No sudo** — `need_sudo` exits with `Run as root or install sudo`.
- **Windows native** — generate `install.ps1` separately; `install.sh` warns under MSYS/Cygwin.
- **Script in subdirectory** — adjust the raw URL path; note it in the README snippet.

## Step Completion Reports

After each phase, emit a `◆` block with `√`/`×` checks and a `Result: PASS | FAIL | PARTIAL` line. The exact templates for the four phases live in `references/edge-cases.md` so you can copy them verbatim without bloating SKILL.md.

## Example One-Liner Output

```bash
curl -sSL https://raw.githubusercontent.com/owner/mytool/main/install.sh | bash
```

Expected runtime banner:

```
[INFO]  OS: linux | Arch: x86_64 | Package Manager: apt
[ OK ]  Dependencies installed
[ OK ]  mytool 1.2.0 installed successfully
[ OK ]  Installation complete!
```
