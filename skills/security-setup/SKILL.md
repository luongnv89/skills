---
name: security-setup
description: "Install local-first security hardening: pre-commit secret detection, offline dependency scans, static analysis, reports, and gated free CI. Use when hardening repos or adding security hooks. Don't use for incident response or cloud security reviews."
license: MIT
compatibility: "Cross-platform (macOS, Linux, Windows). Requires git, Python 3.8+, and project write access. Uses pre-commit plus free local tools such as gitleaks, trivy, semgrep, bandit, or cargo-audit when appropriate. Semgrep on Windows requires WSL2."
effort: high
metadata:
  version: 1.4.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Security Setup

Install a local-first security hardening stack for a project. Favor checks that run
offline at hook time, produce machine-readable output, and give developers a clear
summary before code leaves their machine.

Keep the orchestrator short for the agent's context budget: detailed matrices, templates,
and long verification scenarios live in `references/`. Link, don't inline.

This skill may trigger automatically per its description, but it never writes
silently: Phase 1 always dry-runs the planned changes and waits for explicit
user confirmation before touching files, and Phase 2 (CI) only runs when the
user explicitly asks for it (e.g. `--ci`).

## Prerequisites

- Git repo with a branch you can commit to.
- Python 3.8+ and pip.
- Permission to create `.pre-commit-config.yaml`, `scripts/`, `security/`, `SECURITY.md`.
- (Optional for `--ci`) GitHub Actions enabled on the repo.
- Network for initial tool/db installs (subsequent hook runs are offline).

Confirm these before Phase 1. If a tool cannot be made offline, document the gap instead of pretending.

## Repo Sync Before Edits (mandatory)

Before creating/updating/deleting files in an existing repository, sync the current
branch with remote:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If the working tree is not clean, stash first as a backup, sync, then restore:

```bash
git stash push -u -m "pre-sync"           # backup local changes
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin && git pull --rebase origin "$branch"
git stash pop                              # rollback by restoring the backup
```

If `origin` is missing, pull is unavailable, or rebase/stash conflicts occur, stop
and ask the user before continuing. Never use `--force` rollback options without
confirmation.

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

#### Supply-chain install guardrail

When the repo uses package managers, recommend Socket Firewall as a lightweight
local guardrail for day-to-day dependency installs. This does not replace lockfile
scanning with `trivy`/`cargo-audit`; it shifts risk left by making risky installs
harder before a new dependency reaches the repo.

For macOS/Linux users on `zsh` or `bash`, suggest adding these aliases to the
developer shell profile:

```bash
alias npm="sfw npm"
alias yarn="sfw yarn"
alias pnpm="sfw pnpm"
alias pip="sfw pip"
alias uv="sfw uv"
alias cargo="sfw cargo"
```

Only include aliases for package managers the project actually uses, and document
the guardrail in `SECURITY.md` as optional local developer setup. If Socket
Firewall is not installed, print the official install instructions or link to
the official docs; do not add failing hooks that require `sfw`.

The hook must not call cloud services at runtime. If a scanner needs a local
database, warm that database during setup and run with offline flags in the hook.
If offline dependency scanning cannot be configured for an ecosystem, document the
gap in `SECURITY.md` and do not pretend the criterion is satisfied.

#### File-aware scoping (per-check triggers)

Pre-commit must be fast on small commits without losing coverage. Each check
declares **its own relevance rule** — never a global "skip on .md only" filter.

Trigger semantics in `security/security-tools.json`:

| Trigger | Behavior |
|---|---|
| `"always": true` | Always run. Use for secret scanners — secrets land in `.md`, `.json`, `.env.example`, `Dockerfile`, anywhere. |
| `"paths": [globs]` | Run only when at least one staged file matches a glob. Use for lockfile-driven (`trivy`, `cargo-audit`) or language-driven (`semgrep`, `bandit`) checks. |
| (omitted) | Runner falls back to the per-tool defaults baked into `scripts/security_check.py` for the recognized tool name. |

A repo-wide `trip_all_paths` list (default: `.pre-commit-config.yaml`, `security/**`,
`.github/workflows/**`, `Dockerfile*`, `.dockerignore`, `scripts/security_check.py`)
forces every applicable check to run when any of those files is staged. This
catches workflow-injection edits, hook-tampering, and Dockerfile RCE that would
otherwise slip past purely category-based scoping.

CI runs full scans (`--all`). Scoping only applies on developer commits; the CI
mirror is the safety net.

**Mandatory invariant:** secret scanning runs on every commit. Do not move
gitleaks (or its replacement) into a path-restricted trigger.

### 3. Generate Local Files

Before writing files, dry-run the changes: list every target path, diff any
existing file against the planned content, and confirm with the user. If a
target file already exists, back it up to `<path>.bak` so the user can
rollback. Treat any overwrite of `.pre-commit-config.yaml` or `SECURITY.md`
as destructive and require explicit confirmation.

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

Never add a silent bypass. Bypass cannot be performed through `git commit`
because `pre-commit` redirects hook stdin to `/dev/null`, so the runner's
TTY check refuses `--force` from inside the hook. The approved bypass is a
two-step, explicit override:

1. Run the runner directly with `--force` and type `YES` at the prompt:

   ```bash
   # macOS / Linux
   SECURITY_CHECK_ARGS=--force python3 scripts/security_check.py
   ```

   ```powershell
   # Windows PowerShell
   $env:SECURITY_CHECK_ARGS = "--force"; python scripts\security_check.py; Remove-Item Env:SECURITY_CHECK_ARGS
   ```

   ```bat
   :: Windows cmd.exe
   set SECURITY_CHECK_ARGS=--force && python scripts\security_check.py && set SECURITY_CHECK_ARGS=
   ```

   The runner prints the prompt:

   ```text
   Type YES to override security checks and force-push:
   ```

   It accepts only the literal string `YES`. Any other input, EOF, or a
   non-TTY context exits non-zero and refuses the bypass.

2. After the override is recorded in the report, commit with
   `git commit --no-verify`. Document the bypass in `SECURITY.md` (date,
   reason, link to the recorded report) so the override is auditable.

Do not add `--force` to the pre-commit hook entry, and do not wrap
`git commit` in a script that opens `/dev/tty` for the hook — both routes
hide the bypass from review.

### 5. Verify Locally

Run the local checks after writing files. Use `python3` on macOS/Linux and
`python` on Windows (the Python launcher routes to the active interpreter).
Verification uses `--all` so every configured check runs regardless of what
happens to be staged.

```bash
# macOS / Linux
python3 scripts/security_check.py --all --no-fail-on-missing-tools
pre-commit run security-check --all-files
```

```powershell
# Windows PowerShell
python scripts\security_check.py --all --no-fail-on-missing-tools
pre-commit run security-check --all-files
```

When run from a `pre-commit` hook with no flags, the runner inspects
`git diff --cached` and scopes checks to the staged file set per the trigger
table in §2. `--all` overrides this for verification or one-off full scans;
`--staged-only` errors if no staged files are found (useful for guarded
hooks).

If `pre-commit` is not installed, print the install command and stop:

```bash
python3 -m pip install pre-commit   # use `python` on Windows
pre-commit install
```

#### Expected output

A successful first run prints a summary to stdout and exits 0. See
"Report Requirements" below for the exact shape and content of that summary.

Assert: a clean run exits 0, both report paths exist, and
`security-report.json` parses as valid JSON with a top-level `summary`
object. Any `HIGH` or `CRITICAL` finding exits non-zero unless the bypass
in §"4. Bypass Policy" was completed.

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

A successful full run looks like this (exact counts vary):

```text
Security Check Summary
======================
Mode: full
Checks run: 3 of 3 (skipped: 0)
Findings: 1
Severity: HIGH=1
Categories: dependencies=1
JSON report: security/security-report.json
Markdown report: security/security-report.md

Top findings:
- HIGH [dependencies/trivy] CVE-XXXX-XXXX in <pkg> (<lockfile>)
  Hint: Upgrade to <version>.
```

A scoped run on a docs-only commit looks like:

```text
Mode: staged
Staged files: 2
Checks run: 1 of 3 (skipped: 2)
Skipped: trivy, semgrep
```

Skipped checks are recorded in both reports with their scope reason — they
are not silent.

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
- [ ] File-aware scoping has been walked through manually against the
      no-blindspot scenarios in `references/verification-scenarios.md`.

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
- `references/verification-scenarios.md` - no-blindspot manual verification scenarios
- `scripts/security_check.py` - reusable local security summary runner
