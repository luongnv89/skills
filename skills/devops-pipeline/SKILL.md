---
name: devops-pipeline
description: "Configure pre-commit hooks and lean GitHub Actions for shift-left quality assurance. Use when adding or auditing CI/CD to maximize local test coverage and minimize CI cost. Skip for Terraform/K8s, deployment pipelines, or non-GitHub CI providers."
license: MIT
effort: medium
metadata:
  version: 2.2.1
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# DevOps Pipeline

Implement comprehensive DevOps quality gates adapted to project type, with a **shift-left philosophy**: run as many checks as possible locally via pre-commit so developers get fast feedback and CI is a safety net rather than the primary gate.

**Core principle**: if a check can run on a developer's machine, it runs there. GitHub Actions runs only what a laptop genuinely cannot — matrix version testing, secrets-dependent scans, deployment, coverage publishing — plus one cheap job proving the hooks were not bypassed.

## Check Routing Table

Every check lands in exactly one lane. This table is the single source of truth: workflow steps 2 and 3, the reference files, and any config this skill generates must agree with it.

| Lane | Time budget | What runs there |
|------|-------------|-----------------|
| `pre-commit` stage (every commit) | < 10s, changed files only | Format, lint, type-check, offline security scans, fast unit tests, compile/import check |
| `pre-push` stage (every push) | < 60s, whole repo | Full test suite, CLI E2E, coverage threshold, slow lint rulesets |
| GitHub Actions | billed per minute | Version matrix, secrets-dependent scans, coverage upload, deploy/release, bypass guard |

A check that fits an earlier lane must not be repeated in a later one. CI re-running the whole hook set on every push is the failure mode this skill exists to prevent.

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

## Safety Rails

This skill writes config into someone else's repository and installs git hooks. Observe all of these:

- **Never overwrite an existing `.pre-commit-config.yaml` or `.github/workflows/*.yml`.** Write a `<file>.bak` backup first, merge the new hooks into the existing file, show the user the diff, and ask them to confirm before writing. Preserve user-defined hooks and pinned `rev:` values, and leave the backup in place until the user confirms the merge.
- **Do a dry run before you write.** Validate the proposed config with `pre-commit validate-config`, and run `pre-commit run --all-files` *before* installing the hooks — findings surface without any commit being blocked. Show the generated workflow as a diff; never land a file the user has not seen.
- **Check for an existing git hook before installing.** `pre-commit install` preserves a foreign hook by moving it to `.git/hooks/pre-commit.legacy` and running in migration mode. Never pass `-f`/`--overwrite`, which removes that hook silently — if the user wants it gone, have them confirm the deletion explicitly.
- **Never run `git commit --no-verify` or `git push --no-verify` on the user's behalf.** A failing hook is a finding to report, not an obstacle to route around.
- **Surface failures, never suppress them.** Do not add a hook id to `SKIP`, relax a lint rule, or lower a coverage threshold to turn a run green. Report the failure and let the user decide.
- **Stop rather than guess** when the stack is undetected, `pre-commit` is absent, or `origin` is missing — see Edge Cases for each.

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

**`pre-commit` stage — every commit, under 10 seconds on changed files:**
- Format checks (Prettier, Black/Ruff, gofmt, rustfmt)
- Lint (ESLint, Ruff, golangci-lint, Clippy)
- Type checks (tsc, mypy)
- Security scans that work offline (Bandit, cargo-audit, gosec, `detect-secrets`)
- Fast unit tests
- Build/compile verification (catches import errors, compile failures early)

**`pre-push` stage — every `git push`, under 60 seconds:**
- Full test suite (unit + integration)
- **End-to-end tests for every CLI command** (see below)
- Coverage threshold enforcement
- Slower linters (full golangci-lint ruleset)

**GitHub Actions only — what a laptop cannot do:**
- Matrix version testing (multiple Node/Python/Go versions)
- Secrets-based scans (Snyk, SAST tools needing tokens)
- Deployment / release workflows
- Coverage upload to an external service
- Flaky or environment-sensitive tests that need a clean VM

**Use the modern stage names.** pre-commit 3.2 renamed `commit` to `pre-commit` and `push` to `pre-push`; the old names emit a deprecation warning on 4.x and are scheduled for removal. Always emit the new names, and run `pre-commit migrate-config` against any pre-existing config still using the old ones.

#### CLI End-to-End Testing

If the project is a CLI tool, create `scripts/e2e_test.sh` that exercises every command/subcommand to verify the CLI works end-to-end (not just compiles). Wire it into pre-commit on the `pre-push` stage.

See [references/cli-e2e.md](references/cli-e2e.md) for command discovery patterns, the script template, and the pre-commit hook snippet.

Install hooks:

```bash
pre-commit install
pre-commit install --hook-type pre-push  # pre-push hooks are NOT installed by default
pre-commit run --all-files  # test commit-stage hooks against existing code
```

`git commit --no-verify` and `git push --no-verify` skip every hook, and nothing local can prevent that. The CI bypass guard in step 3 is what keeps these gates enforceable — do not drop it when trimming CI.

### 3. Create GitHub Actions Workflows (lean CI)

Create `.github/workflows/ci.yml`. Keep it thin: the hooks already ran everything that runs locally, so CI covers the third lane of the routing table plus one guard. See [references/github-actions.md](references/github-actions.md) for workflow templates.

CI runs exactly four kinds of thing:

1. **Bypass guard** — re-runs both hook stages, scoped to the pull request's diff so it costs seconds, not minutes. This is the one deliberate overlap with pre-commit, and it exists because `--no-verify` otherwise makes local gates optional.
2. **Version matrix** — the only lane that genuinely needs several runners.
3. **Secrets-dependent work** — scans and uploads needing tokens a laptop should not hold.
4. **Deploy / release** — on merge to the default branch.

The bypass guard, in full:

```yaml
  hooks:
    name: Verify hooks were not bypassed
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      # ... set up the project toolchain and Python here ...
      - name: Run both hook stages over the PR diff
        run: |
          pip install pre-commit
          base="${{ github.event.pull_request.base.sha }}"
          pre-commit run --from-ref "$base" --to-ref HEAD
          pre-commit run --hook-stage pre-push --from-ref "$base" --to-ref HEAD
```

Four details are load-bearing; drop any one and the job fails on its first run:

- **Both `pre-commit run` lines.** The first executes commit-stage hooks *only* — the full suite and the CLI E2E tests live on `pre-push` and are silently skipped without the second. `pre-commit/action@v3.0.1` shares this blind spot, so call the CLI directly.
- **`fetch-depth: 0`.** `actions/checkout` clones at depth 1, so the base SHA is absent and `--from-ref` dies on a bad object.
- **`if: github.event_name == 'pull_request'`.** On a `push` event `github.event.before` is all zeros for a branch's first push and stale after a force-push.
- **The project toolchain in the same job.** Hooks declared `language: system` shell out to `npm`, `mypy`, `go`, or `cargo`.

Keep the matrix off the hot path: gate it on `push` to the default branch or on a release tag, not on every PR commit. A three-version matrix on every push is triple the bill for a signal the hooks already gave locally.

### 4. Verify Pipeline

```bash
# Commit-stage hooks
pre-commit run --all-files

# Push-stage hooks (full suite, includes E2E) — not covered by the line above
pre-commit run --all-files --hook-stage pre-push

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

Which lane each of these belongs to is fixed by the Check Routing Table above — do not re-split checks differently here.

## Expected Output

After running the skill, the repository contains:

1. **`.pre-commit-config.yaml`** — formatting, linting, type-checking, and fast unit tests on the `pre-commit` stage; full test suite, coverage threshold, and E2E tests on the `pre-push` stage.
2. **`.github/workflows/ci.yml`** — CI carrying only the four responsibilities from step 3: diff-scoped bypass guard, version matrix, secrets-dependent work, deploy. No standalone lint, format, type-check, or test steps duplicating a hook.
3. **`scripts/e2e_test.sh`** (CLI projects only) — executable script exercising every CLI command/subcommand.

Example `.pre-commit-config.yaml` snippet for a Python project:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.4
    hooks:
      - id: ruff
        stages: [pre-commit]
      - id: ruff-format
        stages: [pre-commit]
  - repo: local
    hooks:
      - id: mypy
        name: mypy type check
        entry: mypy src/
        language: system
        stages: [pre-commit]
      - id: pytest-fast
        name: fast unit tests
        entry: pytest tests/unit -x -q
        language: system
        stages: [pre-commit]
      - id: pytest-full
        name: full test suite
        entry: pytest --cov=src --cov-report=xml
        language: system
        stages: [pre-push]
```

## Acceptance Criteria

A run passes when **all** of the following are true:

- [ ] `.pre-commit-config.yaml` exists at the repo root and lists at least one hook for the detected primary language (formatter, linter, or type checker).
- [ ] Every check sits in exactly one lane of the Check Routing Table: no hook `id` from `.pre-commit-config.yaml` appears in a workflow `run:` step other than the bypass guard, and no check runnable on a laptop is CI-only.
- [ ] Hook `stages:` use the modern names (`pre-commit`, `pre-push`, `manual`); no generated config emits the deprecated `commit` or `push`.
- [ ] Both hook types are installed: `pre-commit install` **and** `pre-commit install --hook-type pre-push`.
- [ ] At least one `.github/workflows/*.yml` exists and carries only the four CI responsibilities from step 3.
- [ ] CI's sole overlap with pre-commit is the bypass guard, and that guard is diff-scoped (`--from-ref`/`--to-ref`) and runs **both** stages.
- [ ] `pre-commit run --all-files` and `pre-commit run --all-files --hook-stage pre-push` both succeed (or their failures are surfaced explicitly to the user, not auto-suppressed).
- [ ] For CLI projects, the E2E script is wired to the `pre-push` stage per the language reference files.

## Edge Cases

- **No package manager detected**: Prompt the user for the language/build system before generating hooks; never guess silently.
- **Pre-commit not installed**: Emit the install command (`pip install pre-commit` or `brew install pre-commit`) and stop; don't generate config files for a tool that isn't present.
- **Existing `.pre-commit-config.yaml`**: Merge new hooks into the existing file rather than overwriting; preserve user-defined hooks and pinned revs.
- **Monorepo with multiple languages**: Generate one config with per-language hook sections and `files:` path filters so hooks only run on relevant subdirectories. Local `language: system` entries must also target the package dir (`npm --prefix frontend`, `pytest backend/tests`) — `files:` only filters which files trigger the hook, not cwd.
- **No `origin` remote**: Skip the repo-sync step and inform the user; proceed with local-only setup.
- **Tests take >60 seconds**: Demote to the next lane — `pre-commit` to `pre-push`, or `pre-push` to CI — and record the reason in a comment on the hook so the next reader knows it was measured, not guessed.
- **Legacy config with deprecated stage names**: Run `pre-commit migrate-config` before merging new hooks in, so the file does not end up half-migrated.
- **Team bypasses hooks with `--no-verify`**: Local gates cannot stop this. Keep the CI bypass guard, and report the bypass rate rather than adding more hooks.
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

**Phase: Pre-commit Configuration** — checks: `Pre-commit setup`, `Commit-stage hooks installed`, `Push-stage hooks installed`, `Modern stage names used`, `E2E script created (if CLI)`

**Phase: GitHub Actions Setup** — checks: `GitHub Actions config`, `CI limited to the four responsibilities`, `Bypass guard runs both stages`, `Matrix off the per-commit path`

**Phase: Pipeline Verification** — checks: `Commit-stage hooks pass`, `Push-stage hooks pass`, `E2E tests pass (if CLI)`, `No check duplicated across lanes`

## Resources

- [references/precommit-configs.md](references/precommit-configs.md) — pre-commit configs by language, with `pre-push` tests and E2E hooks
- [references/github-actions.md](references/github-actions.md) — GitHub Actions templates: bypass guard, matrix, deploy
- [references/cli-e2e.md](references/cli-e2e.md) — CLI command discovery, the E2E script template, and its `pre-push` hook
