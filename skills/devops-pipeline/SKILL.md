---
name: devops-pipeline
description: "Configure pre-commit hooks and lean GitHub Actions for shift-left quality assurance. Use when adding or auditing CI/CD on a Git repo to maximize local test coverage and minimize CI cost. Skip for Terraform/K8s, deployment pipelines, or non-GitHub CI providers."
license: MIT
effort: medium
metadata:
  version: 2.0.1
  author: Luong NGUYEN <luongnv89@gmail.com>
---

# DevOps Pipeline

Implement comprehensive DevOps quality gates adapted to project type, with a **shift-left philosophy**: run as many checks as possible locally via pre-commit so developers get fast feedback and CI is a safety net rather than the primary gate.

**Core principle**: If a check can run locally in under ~60 seconds, it belongs in pre-commit. GitHub Actions should handle things that can't run locally: matrix version testing, secrets-based security scans, deployment, and reporting.

To stay within the agent's context budget, this SKILL keeps templates short and links to `references/*.md` for language-specific configs, workflow templates, and the CLI E2E script.

## Repo Sync Before Edits (mandatory)
Before creating/updating/deleting files in an existing repository, sync the current branch with remote:

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

If `origin` is missing, pull is unavailable, or rebase/stash conflicts occur, stop and ask the user before continuing.

## Workflow

### 1. Analyze Project

Detect project characteristics:

```bash
# Check for package files and configs
ls -la package.json pyproject.toml Cargo.toml go.mod pom.xml build.gradle *.csproj 2>/dev/null
ls -la .eslintrc* .prettierrc* tsconfig.json mypy.ini setup.cfg ruff.toml 2>/dev/null
ls -la .pre-commit-config.yaml .github/workflows/*.yml 2>/dev/null
```

Identify:
- **Languages**: JS/TS, Python, Go, Rust, Java, C#, etc.
- **Frameworks**: React, Next.js, Django, FastAPI, etc.
- **Build system**: npm, yarn, pnpm, pip, poetry, cargo, go, maven, gradle
- **Existing tooling**: Linters, formatters, type checkers already configured
- **Is this a CLI tool?** — if yes, enumerate all commands/subcommands (check README, `--help`, `click`/`argparse`/`cobra` source) to build an E2E test suite

### 2. Configure Pre-commit Hooks (maximize local coverage)

Install pre-commit framework:

```bash
pip install pre-commit  # or brew install pre-commit
```

Create `.pre-commit-config.yaml` based on detected stack. See [references/precommit-configs.md](references/precommit-configs.md) for language-specific configurations.

**What to put in pre-commit (run on every commit):**
- Format checks (Prettier, Black/Ruff, gofmt, rustfmt)
- Lint (ESLint, Ruff, golangci-lint, Clippy)
- Type checks (tsc, mypy)
- Security scans that work offline (Bandit, cargo-audit, gosec, `detect-secrets`)
- Unit tests (fast, <10s) — always on `commit` stage
- Build/compile verification (catches import errors, compile failures early)

**What to put in pre-commit on `push` stage (run on git push):**
- Full test suite (unit + integration)
- **End-to-end tests for every CLI command** (see below)
- Coverage checks
- Slower linters (full golangci-lint ruleset)

**What stays in GitHub Actions only:**
- Matrix version testing (multiple Node/Python/Go versions)
- Secrets-based scans (Snyk, SAST tools needing tokens)
- Deployment / release workflows
- Flaky or environment-sensitive tests that need a clean VM

#### CLI End-to-End Testing

If the project is a CLI tool, create `scripts/e2e_test.sh` that exercises every command/subcommand to verify the CLI works end-to-end (not just compiles). Wire it into pre-commit on the `push` stage.

See [references/cli-e2e.md](references/cli-e2e.md) for command discovery patterns, the script template, and the pre-commit hook snippet.

Install hooks:

```bash
pre-commit install
pre-commit install --hook-type pre-push  # also install push-stage hooks
pre-commit run --all-files  # Test on existing code
```

### 3. Create GitHub Actions Workflows (lean CI)

Create `.github/workflows/ci.yml` — but keep it lean since pre-commit already catches most issues. See [references/github-actions.md](references/github-actions.md) for workflow templates.

GitHub Actions responsibilities (things pre-commit can't do):
- Matrix testing across language versions (important for libraries)
- Upload coverage reports (Codecov, etc.)
- Deployment on merge to main
- PR status comments/badges
- Secrets-dependent scans

Since pre-commit already runs lint, format, type-check, unit tests, and E2E tests — the CI workflow can be simpler: install deps → run pre-commit → run tests with coverage upload → build artifact.

```yaml
# Minimal CI when pre-commit covers everything locally:
- name: Run pre-commit
  run: pre-commit run --all-files

- name: Run tests with coverage
  run: <test-command> --cov --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v4
```

### 4. Verify Pipeline

```bash
# Test all pre-commit hooks (commit stage)
pre-commit run --all-files

# Test push-stage hooks (includes E2E)
pre-commit run --all-files --hook-stage push

# Verify the CLI E2E script directly
bash scripts/e2e_test.sh
```

If all local checks pass, GitHub Actions becomes a thin verification layer, not the primary quality gate.

## Tool Selection by Language

| Language | Formatter | Linter | Type Check | Security | Tests |
|----------|-----------|--------|------------|----------|-------|
| JS/TS | Prettier | ESLint | tsc | npm audit | Jest/Vitest |
| Python | Ruff/Black | Ruff | mypy | Bandit + detect-secrets | pytest |
| Go | gofmt | golangci-lint | built-in | gosec | go test |
| Rust | rustfmt | Clippy | built-in | cargo-audit | cargo test |
| Java | google-java-format | Checkstyle | - | SpotBugs | mvn test |

## What Runs Where

| Check | Pre-commit (commit) | Pre-commit (push) | GitHub Actions |
|-------|---------------------|-------------------|----------------|
| Formatting | ✓ | — | — |
| Linting | ✓ | — | — |
| Type checking | ✓ | — | — |
| Security scan (offline) | ✓ | — | — |
| Unit tests (fast) | ✓ | — | — |
| Full test suite | — | ✓ | ✓ (coverage upload) |
| CLI E2E tests | — | ✓ | — |
| Multi-version matrix | — | — | ✓ |
| Deploy | — | — | ✓ |

## Expected Output

After running the skill, the repository contains:

1. **`.pre-commit-config.yaml`** — hooks for formatting, linting, type-checking, and unit tests on `commit` stage; full test suite and E2E tests on `push` stage.
2. **`.github/workflows/ci.yml`** — lean CI that re-runs pre-commit and uploads coverage; no duplicate lint/format steps.
3. **`scripts/e2e_test.sh`** (CLI projects only) — executable script exercising every CLI command/subcommand.

Example `.pre-commit-config.yaml` snippet for a Python project:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.4
    hooks:
      - id: ruff
        stages: [commit]
      - id: ruff-format
        stages: [commit]
  - repo: local
    hooks:
      - id: mypy
        name: mypy type check
        entry: mypy src/
        language: system
        stages: [commit]
      - id: pytest-fast
        name: fast unit tests
        entry: pytest tests/unit -x -q
        language: system
        stages: [commit]
      - id: pytest-full
        name: full test suite
        entry: pytest --cov=src --cov-report=xml
        language: system
        stages: [push]
```

## Acceptance Criteria

A run passes when **all** of the following are true:

- [ ] `.pre-commit-config.yaml` exists at the repo root and lists at least one hook for the detected primary language (formatter, linter, or type checker).
- [ ] All checks runnable locally in under ~60 seconds are configured in pre-commit, not GitHub Actions.
- [ ] At least one `.github/workflows/*.yml` exists and runs only the things pre-commit cannot (matrix builds, secret-scanning, deployment, or release).
- [ ] `pre-commit run --all-files` succeeds (or its failures are surfaced explicitly to the user, not auto-suppressed).
- [ ] For CLI projects, an E2E test step is wired into either pre-commit or CI per the language reference files.
- [ ] No duplication: the same check (e.g., `eslint`, `ruff`) does not run in both pre-commit and CI on the same trigger.

## Edge Cases

- **No package manager detected**: Prompt the user for the language/build system before generating hooks; never guess silently.
- **Pre-commit not installed**: Emit the install command (`pip install pre-commit` or `brew install pre-commit`) and stop; don't generate config files for a tool that isn't present.
- **Existing `.pre-commit-config.yaml`**: Merge new hooks into the existing file rather than overwriting; preserve user-defined hooks and pinned revs.
- **Monorepo with multiple languages**: Generate one config with per-language hook sections and `files:` path filters so hooks only run on relevant subdirectories.
- **No `origin` remote**: Skip the repo-sync step and inform the user; proceed with local-only setup.
- **Tests take >60 seconds**: Move slow tests to `push` stage or GitHub Actions only; note the decision explicitly in the generated config with a comment.
- **Windows-only repo**: Substitute PowerShell-compatible hook entries and flag any Unix-specific commands.

## Step Completion Reports

After completing each major step, output a status report in this format:

```
◆ [Step Name] ([step N of M] — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          √ pass (note if relevant)
  [Check 3]:          × fail — [reason]
  [Check 4]:          √ pass
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Adapt the check names to match what the step actually validates. Use `√` for pass, `×` for fail, and `—` to add brief context. The "Criteria" line summarizes how many acceptance criteria were met. The "Result" line gives the overall verdict.

### Skill-specific checks per phase

**Phase: Project Analysis** — checks: `Project detection`, `Existing tooling scan`, `CLI detection`, `Command enumeration`

**Phase: Pre-commit Configuration** — checks: `Pre-commit setup`, `Hook installation`, `Push-stage hooks installed`, `E2E script created (if CLI)`

**Phase: GitHub Actions Setup** — checks: `GitHub Actions config`, `CI lean (pre-commit deduplication)`, `Matrix testing configured`

**Phase: Pipeline Verification** — checks: `Commit-stage hooks pass`, `Push-stage hooks pass`, `E2E tests pass (if CLI)`

## Resources

- [references/precommit-configs.md](references/precommit-configs.md) - Pre-commit configurations by language (with push-stage tests and E2E hooks)
- [references/github-actions.md](references/github-actions.md) - GitHub Actions workflow templates (lean CI variants)
