---
name: security-setup
description: "Install local-first security hardening: pre-commit secret detection, offline dependency scans, static analysis, reports, and gated free CI. Use when hardening repos or adding security hooks. Don't use for incident response or cloud security reviews."
license: MIT
compatibility: "Cross-platform (macOS, Linux, Windows). Requires git, Python 3.8+, and project write access. Uses pre-commit plus free local tools such as gitleaks, trivy, semgrep, bandit, or cargo-audit when appropriate. Semgrep on Windows requires WSL2."
effort: high
metadata:
  version: 1.1.0
  author: Luong NGUYEN <luongnv89@gmail.com>
---

# Security Setup

Install a local-first security hardening stack for a project. Favor checks that run
offline at hook time, produce machine-readable output, and give developers a clear
summary before code leaves their machine.

## Repo Sync Before Edits (mandatory)

Before creating/updating/deleting files in an existing repository, sync the current
branch with remote:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If the working tree is not clean, stash first, sync, then restore:

```bash
git stash push -u -m "pre-sync"
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin && git pull --rebase origin "$branch"
git stash pop
```

If `origin` is missing, pull is unavailable, or rebase/stash conflicts occur, stop
and ask the user before continuing.

## Operating Model

Work in two gated phases:

1. **Local security baseline** - install a pre-commit hook that checks secrets,
   dependency vulnerabilities, and static analysis issues locally.
2. **CI/CD mirror** - only when the user asks for `--ci`, create a free-tier
   GitHub Actions workflow that runs the same local runner on pull requests.

Do not create CI files until Phase 1 is installed and passing.

## Phase 1 - Local Security Baseline

### 1. Detect the Project

Inspect the repo before choosing tools. The runner and skill instructions work
on macOS, Linux, and Windows; pick the matching shell snippet.

**macOS / Linux (bash, zsh):**

```bash
ls -la package.json package-lock.json pnpm-lock.yaml yarn.lock pyproject.toml requirements.txt Cargo.toml Cargo.lock go.mod pom.xml build.gradle 2>/dev/null
ls -la .pre-commit-config.yaml SECURITY.md .github/workflows/security.yml 2>/dev/null
command -v gitleaks trivy semgrep detect-secrets bandit cargo-audit pre-commit 2>/dev/null
```

**Windows PowerShell:**

```powershell
Get-ChildItem -Force -ErrorAction SilentlyContinue package.json,package-lock.json,pnpm-lock.yaml,yarn.lock,pyproject.toml,requirements.txt,Cargo.toml,Cargo.lock,go.mod,pom.xml,build.gradle
Get-ChildItem -Force -ErrorAction SilentlyContinue .pre-commit-config.yaml,SECURITY.md,.github\workflows\security.yml
foreach ($t in 'gitleaks','trivy','semgrep','detect-secrets','bandit','cargo-audit','pre-commit') { Get-Command $t -ErrorAction SilentlyContinue }
```

Identify:
- Languages and lockfiles
- Existing pre-commit config and security docs
- Available local tools
- Whether the repo is public or private, if CI/SARIF upload is requested

Use `references/tool-selection.md` for the tool matrix and install commands.

### 2. Select the Minimal Tool Set

Choose the smallest useful set:

- **Secrets**: prefer `gitleaks`; use `detect-secrets` when it already exists in
  a Python-heavy repo.
- **Dependencies**: prefer `trivy fs --skip-db-update` for offline hook runtime;
  add `cargo-audit` only for Rust repos that already use Cargo.
- **Static analysis**: prefer `semgrep` with local rules under `security/`.
  Add language-native scanners only when the language is present (`bandit` for
  Python, `gosec` for Go, `cargo clippy`/`cargo audit` for Rust).

The hook must not call cloud services at runtime. If a scanner needs a local
database, warm that database during setup and run with offline flags in the hook.
If offline dependency scanning cannot be configured for an ecosystem, document the
gap in `SECURITY.md` and do not pretend the criterion is satisfied.

### 3. Generate Local Files

Create or update these files:

- `.pre-commit-config.yaml` - merge a local `security-check` hook into existing
  config; do not overwrite user hooks.
- `scripts/security_check.py` - copy from `scripts/security_check.py` in this
  skill, then adjust tool config if needed.
- `security/semgrep-rules.yml` - local Semgrep rules so runtime scans are offline.
- `security/security-tools.json` - selected tools and command overrides.
- `SECURITY.md` - summary of selected tools, why they were chosen, and how to run
  or bypass checks.

Use `references/templates.md` for starter snippets.

### 4. Bypass Policy

Never add a silent bypass. The only approved bypass path sets the
`SECURITY_CHECK_ARGS` environment variable for one `git commit` invocation:

```bash
# macOS / Linux
SECURITY_CHECK_ARGS=--force git commit
```

```powershell
# Windows PowerShell
$env:SECURITY_CHECK_ARGS = "--force"; git commit; Remove-Item Env:SECURITY_CHECK_ARGS
```

```bat
:: Windows cmd.exe
set SECURITY_CHECK_ARGS=--force && git commit && set SECURITY_CHECK_ARGS=
```

The runner reads `SECURITY_CHECK_ARGS` itself (no shell wrapper required) and
prompts the user to type exactly:

```text
YES
```

using the prompt:

```text
Type YES to override security checks and force-push:
```

If the user does not type `YES`, or the hook is running without a TTY (CI,
piped input), the hook exits non-zero.

### 5. Verify Locally

Run the local checks after writing files. Use `python3` on macOS/Linux and
`python` on Windows (the Python launcher routes to the active interpreter).

```bash
# macOS / Linux
python3 scripts/security_check.py --no-fail-on-missing-tools
pre-commit run security-check --all-files
```

```powershell
# Windows PowerShell
python scripts\security_check.py --no-fail-on-missing-tools
pre-commit run security-check --all-files
```

If `pre-commit` is not installed, print the install command and stop:

```bash
python3 -m pip install pre-commit   # use `python` on Windows
pre-commit install
```

## Phase 2 - CI/CD Mirror (`--ci`)

Only run this phase when the user asks for CI/CD, for example
`/security-setup --ci`.

Preconditions:
- Phase 1 files exist
- `python3 scripts/security_check.py --no-fail-on-missing-tools` runs locally
- `.pre-commit-config.yaml` contains the `security-check` hook

Then create `.github/workflows/security.yml` using `references/templates.md`.
Keep the workflow free-tier friendly:

- Trigger on `pull_request` and `push` to the default branch.
- Install only the selected tools.
- Cache scanner databases where supported.
- Run `python3 scripts/security_check.py`.
- Upload SARIF only when the repo can use GitHub Code Scanning; otherwise keep
  the job summary only.

## Report Requirements

The local runner must print a concise report with:

- Total checks run
- Findings by category: secrets, dependencies, static analysis, tool errors
- Severity breakdown: critical, high, medium, low, info
- Actionable fix hints
- Paths to JSON and Markdown report artifacts

The default exit behavior is strict: any `HIGH` or `CRITICAL` finding exits
non-zero.

## Acceptance Criteria

A completed setup passes when:

- [ ] `.pre-commit-config.yaml` contains a local `security-check` hook.
- [ ] `scripts/security_check.py` exists and prints the required summary.
- [ ] Secret detection, dependency scanning, and static analysis are configured
      for the detected project where offline local tooling is available.
- [ ] Hook runtime uses offline flags and does not require cloud credentials.
- [ ] `--force` requires the exact `YES` confirmation before bypassing failures.
- [ ] `SECURITY.md` documents selected tools, omissions, run commands, and CI
      status.
- [ ] `--ci` creates `.github/workflows/security.yml` only after Phase 1 passes.

## Edge Cases

- **Existing hooks**: merge the new hook; preserve all existing hooks and revs.
- **Monorepo**: use path filters in `security/security-tools.json` and document
  per-package coverage.
- **Missing tools**: install the minimal missing set or tell the user the exact
  command; do not silently skip required categories.
- **Private repo SARIF**: GitHub Code Scanning may require a paid plan. Keep the
  summary report and skip SARIF upload unless available.
- **Network-restricted setup**: create configs and report the commands that must
  be run later to warm vulnerability databases.

## Step Completion Report

After each phase, report:

```text
◆ Security Setup ([phase] - [context])
................................................................
  Project detection:      pass | fail - detail
  Tool selection:         pass | fail - detail
  Local hook:             pass | fail - detail
  Security report:        pass | fail - detail
  CI mirror:              pass | skipped | fail - detail
  Criteria:               N/M met
  ____________________________
  Result:                 PASS | PARTIAL | FAIL
```

## Resources

- `references/tool-selection.md` - offline-first tool matrix and install notes
- `references/templates.md` - target repo file templates
- `scripts/security_check.py` - reusable local security summary runner
