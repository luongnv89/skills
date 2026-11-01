# Pre-commit Configurations by Language

Philosophy: **run as much as possible locally, with the fastest free tools**. `pre-commit`-stage hooks catch issues immediately (budget: under 10 seconds on changed files); `pre-push`-stage hooks run the whole test suite while it fits, then only the tests the push affects, plus E2E tests, before code leaves the machine (budget: under 60 seconds). GitHub Actions keeps only the version matrix, secrets-dependent work, deploys, and a diff-scoped bypass guard.

**Stage names.** pre-commit 3.2 renamed `commit` to `pre-commit` and `push` to `pre-push`. The old names still work on 4.x but emit a deprecation warning and are scheduled for removal, so every config below uses the new names, and pins `pre-commit-hooks` v6.0.0, whose manifest uses them too. To upgrade an existing file in place:

```bash
pre-commit migrate-config
```

**Default stages.** A hook with no `stages:` runs in every stage, including `pre-push`, so without `default_stages: [pre-commit]` each push (and the CI guard's push-stage leg) re-runs the whole commit stage. Six `pre-commit-hooks` hooks (`trailing-whitespace`, `end-of-file-fixer`, `check-added-large-files`, and three more) declare their own stages in their manifest, which `default_stages` does not override. They take milliseconds on changed files; give them `stages: [pre-commit]` only if the repeat matters.

## Table of Contents

- [Tool selection by language](#tool-selection-by-language)
- [JavaScript/TypeScript](#javascripttypescript)
- [Python](#python)
- [Go](#go)
- [Rust](#rust)
- [Java](#java)
- [Multi-language](#multi-language)
- [Fast linters and type checkers](#fast-linters-and-type-checkers)
- [Fast checks belong in hooks, not in AGENTS.md](#fast-checks-belong-in-hooks-not-in-agentsmd)
- [Fast test runs](#fast-test-runs)
- [CLI End-to-End Testing](#cli-end-to-end-testing)
- [Common Options](#common-options)
- [Sources](#sources)

## Tool selection by language

| Language | Formatter | Linter | Type Check | Security | Tests |
|----------|-----------|--------|------------|----------|-------|
| JS/TS | Prettier | Oxlint (+ ESLint for rules it lacks) | tsc 7 (benchmark `bun check`, `tsrs`) | npm audit | Vitest |
| Python | Ruff/Black | Ruff | mypy (benchmark Pyrefly, ty) | Bandit + detect-secrets | pytest + pytest-xdist (a dev dependency) |
| Go | gofmt | golangci-lint | built-in | gosec | go test |
| Rust | rustfmt | Clippy | built-in | cargo-audit | cargo test |
| Java | google-java-format | Checkstyle | - | SpotBugs | mvn test |

Lanes come from the SKILL's Check Routing Table; do not re-split them here.

## JavaScript/TypeScript

```yaml
# Hooks with no `stages:` run in EVERY stage; this keeps them on commit only.
default_stages: [pre-commit]
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files

  - repo: local
    hooks:
      - id: prettier
        name: prettier
        entry: npx prettier --write --ignore-unknown
        language: system
        types: [text]
        files: \.(js|jsx|ts|tsx|json|css|scss|md)$

      # Oxlint first. Its default severity is "warning" with exit code 0, so the
      # hook fails only because .oxlintrc.json sets categories to "error".
      - id: oxlint
        name: oxlint
        entry: npx oxlint --fix
        language: system
        files: \.(js|jsx|ts|tsx|mjs|cjs)$

      # ESLint only for rules Oxlint lacks, with eslint-plugin-oxlint turning off
      # every rule Oxlint already runs:
      # - id: eslint
      #   name: eslint (rules Oxlint lacks)
      #   entry: npx eslint --fix
      #   language: system
      #   files: \.(js|jsx|ts|tsx)$

      # TypeScript 7's native tsc; benchmark faster checkers before swapping
      # (see "Fast linters and type checkers").
      - id: typecheck
        name: typecheck
        entry: npx tsc --noEmit
        language: system
        pass_filenames: false

      # Unit tests run on every commit (keep them fast)
      - id: test-unit
        name: unit tests
        entry: npm run test:unit
        language: system
        pass_filenames: false

      # Full test suite on push while it fits the 60-second budget. Past that,
      # swap in the affected-tests hook below (see "Fast test runs").
      - id: test-full
        name: full test suite
        entry: npm test
        language: system
        pass_filenames: false
        stages: [pre-push]

      # - id: test-affected
      #   name: affected tests
      #   entry: bash scripts/affected-tests.sh
      #   language: system
      #   pass_filenames: false
      #   stages: [pre-push]

      # The build on push: with the matrix nightly, nothing else builds a PR.
      - id: build
        name: build
        entry: npm run build
        language: system
        pass_filenames: false
        stages: [pre-push]

      # If this is a CLI tool, add E2E hook on push stage:
      # - id: e2e-cli
      #   name: CLI end-to-end tests
      #   entry: bash scripts/e2e_test.sh
      #   language: system
      #   pass_filenames: false
      #   stages: [pre-push]
```

> **Note on unit vs full tests**: split your test script into `test:unit` (fast, no I/O) and `test` (all). If you can't split them, run all tests on commit — slow feedback is still better than no feedback.

> **Install every hook tool as a devDependency** (`prettier`, `oxlint`, `typescript`, `vitest`). `npx` then resolves the local copy instead of downloading the tool on every run, and the CI guard's npm cache covers it.

## Python

```yaml
# Hooks with no `stages:` run in EVERY stage; this keeps them on commit only.
default_stages: [pre-commit]
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-added-large-files
      - id: debug-statements

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: []  # Add type stubs as needed

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.7
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]
        additional_dependencies: ["bandit[toml]"]

  - repo: local
    hooks:
      # Unit tests on every commit
      - id: pytest-unit
        name: pytest unit tests
        entry: pytest tests/unit -x -q
        language: system
        pass_filenames: false

      # Full suite (unit + integration) on push; pytest-xdist runs one worker
      # per physical core.
      - id: pytest-full
        name: pytest full suite
        entry: pytest -n auto --tb=short -q
        language: system
        pass_filenames: false
        stages: [pre-push]

      # CLI E2E tests on push (if this is a CLI tool)
      # - id: e2e-cli
      #   name: CLI end-to-end tests
      #   entry: bash scripts/e2e_test.sh
      #   language: system
      #   pass_filenames: false
      #   stages: [pre-push]
```

### Alternative: Black instead of Ruff formatter

```yaml
  - repo: https://github.com/psf/black
    rev: 24.2.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
```

## Go

```yaml
# Hooks with no `stages:` run in EVERY stage; this keeps them on commit only.
default_stages: [pre-commit]
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml

  - repo: local
    hooks:
      - id: go-fmt
        name: go fmt
        entry: gofmt -w
        language: system
        types: [go]

      - id: go-vet
        name: go vet
        entry: go vet ./...
        language: system
        pass_filenames: false

      - id: golangci-lint
        name: golangci-lint
        entry: golangci-lint run --fix
        language: system
        types: [go]
        pass_filenames: false

      - id: gosec
        name: gosec
        entry: gosec ./...
        language: system
        pass_filenames: false

      # Fast unit tests on every commit
      - id: go-test-unit
        name: go unit tests
        entry: go test -short ./...
        language: system
        pass_filenames: false

      # Full tests (including integration) on push
      - id: go-test-full
        name: go full test suite
        entry: go test -race ./...
        language: system
        pass_filenames: false
        stages: [pre-push]

      # CLI E2E on push (if this is a CLI tool)
      # - id: e2e-cli
      #   name: CLI end-to-end tests
      #   entry: bash scripts/e2e_test.sh
      #   language: system
      #   pass_filenames: false
      #   stages: [pre-push]
```

## Rust

```yaml
# Hooks with no `stages:` run in EVERY stage; this keeps them on commit only.
default_stages: [pre-commit]
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml

  - repo: local
    hooks:
      - id: cargo-fmt
        name: cargo fmt
        entry: cargo fmt --
        language: system
        types: [rust]

      - id: cargo-clippy
        name: cargo clippy
        entry: cargo clippy --all-targets --all-features -- -D warnings
        language: system
        types: [rust]
        pass_filenames: false

      - id: cargo-audit
        name: cargo audit
        entry: cargo audit
        language: system
        pass_filenames: false

      # Unit tests on every commit
      - id: cargo-test-unit
        name: cargo unit tests
        entry: cargo test --lib
        language: system
        pass_filenames: false

      # All tests (unit + integration + doc tests) on push
      - id: cargo-test-full
        name: cargo full test suite
        entry: cargo test --all-features
        language: system
        pass_filenames: false
        stages: [pre-push]

      # CLI E2E on push (if this is a CLI tool)
      # - id: e2e-cli
      #   name: CLI end-to-end tests
      #   entry: bash scripts/e2e_test.sh
      #   language: system
      #   pass_filenames: false
      #   stages: [pre-push]
```

## Java

```yaml
# Hooks with no `stages:` run in EVERY stage; this keeps them on commit only.
default_stages: [pre-commit]
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-xml

  - repo: https://github.com/macisamuele/language-formatters-pre-commit-hooks
    rev: v2.12.0
    hooks:
      - id: pretty-format-java
        args: [--autofix]

  - repo: local
    hooks:
      - id: checkstyle
        name: checkstyle
        entry: mvn checkstyle:check -q
        language: system
        pass_filenames: false

      - id: spotbugs
        name: spotbugs
        entry: mvn spotbugs:check -q
        language: system
        pass_filenames: false

      # Unit tests on commit
      - id: test-unit
        name: unit tests
        entry: mvn test -pl . -Dtest="**/unit/**" -q
        language: system
        pass_filenames: false

      # Full tests on push
      - id: test-full
        name: full test suite
        entry: mvn test -q
        language: system
        pass_filenames: false
        stages: [pre-push]
```

## Multi-language

For monorepos or projects with multiple languages. pre-commit always execs from the **repo root**; `files:` only filters which files trigger the hook, it does not change cwd. Copy remote hooks from the language sections above and scope them with `files:`. Rewrite local `language: system` entries so they target the package dir — a bare `npm test` will not see `frontend/package.json` or `frontend/node_modules`.

```yaml
# Hooks with no `stages:` run in EVERY stage; this keeps them on commit only.
default_stages: [pre-commit]
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-toml
      - id: check-added-large-files
      - id: detect-private-key

  - repo: local
    hooks:
      # `npx --prefix` resolves frontend/node_modules; it does not change cwd,
      # so name the Oxlint config explicitly.
      - id: oxlint
        name: oxlint
        entry: npx --prefix frontend oxlint -c frontend/.oxlintrc.json --fix
        language: system
        files: ^frontend/.*\.(js|jsx|ts|tsx)$

      - id: typecheck
        name: typecheck
        entry: npx --prefix frontend tsc --noEmit -p frontend
        language: system
        files: ^frontend/
        pass_filenames: false

      - id: test-unit
        name: frontend unit tests
        entry: npm --prefix frontend run test:unit
        language: system
        files: ^frontend/
        pass_filenames: false

      - id: test-full
        name: frontend full test suite
        entry: npm --prefix frontend test
        language: system
        files: ^frontend/
        pass_filenames: false
        stages: [pre-push]

      - id: pytest-unit
        name: pytest unit tests
        entry: pytest backend/tests/unit -x -q
        language: system
        files: ^backend/
        pass_filenames: false

      - id: pytest-full
        name: pytest full suite
        entry: pytest backend/tests --tb=short -q
        language: system
        files: ^backend/
        pass_filenames: false
        stages: [pre-push]
```

---

## Fast linters and type checkers

Pick the fastest free tool the stack supports, benchmark it on the repository, and keep the established tool as the arbiter until the fast one reports the same findings. Vendor numbers are claims to verify, not guarantees.

### Oxlint for JavaScript/TypeScript

Oxlint (oxc project, 1.x, MIT) implements ESLint core plus the typescript-eslint, React, Jest, Vitest, import, unicorn, and jsx-a11y rule families natively in Rust; the project reports 50–100× ESLint's speed. Type-aware rules run through TypeScript 7's native checker (`--type-aware`), and JS plugins for existing ESLint plugins are alpha.

- **Replace ESLint** when Oxlint covers the rules the repository uses. `npx @oxlint/migrate` converts an existing ESLint configuration.
- **Keep ESLint only for rules Oxlint lacks**: run Oxlint first and add `eslint-plugin-oxlint`, which turns off every ESLint rule Oxlint already runs.
- **Make it fail.** Oxlint reports findings as warnings and exits 0 by default (checked with oxlint 1.90.0: `debugger` and `x == NaN` both passed), so set the categories to `error` or pass `--deny-warnings`.
- **Agents don't mind strict rules.** On a new repository, turn on `suspicious` too. On an existing one, propose stricter categories in the diff with the count of new findings; never enable them silently, and never relax a rule to get green.

```json
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": ["typescript", "unicorn", "oxc", "import", "vitest"],
  "categories": {
    "correctness": "error",
    "suspicious": "error",
    "perf": "warn"
  }
}
```

Save it as `.oxlintrc.json`. Setting `plugins` replaces the default plugin set, so list every plugin the repository needs (`react`, `jsx-a11y`, `jest`, and so on). A `warn` category is advisory: it prints findings but never fails the hook, so only the `error` categories gate a commit.

### TypeScript checkers

| Checker | Status (2026-11-01) | Use |
|---|---|---|
| `tsc` from TypeScript 7 | Stable since 7.0 (July 2026): the native Go compiler in the regular `typescript` package; Microsoft reports 8–12× faster full builds than 6.0 | Default, and the arbiter |
| `bun check` | Bun 1.4.3 and later: reads `tsconfig.json`, reports TypeScript 7's errors, uses every core, and pins one exact TypeScript version | Candidate when the repository already uses Bun |
| `tsrs` (oxc-project) | Pre-1.0 Rust port of the TypeScript 7 checker, tracking 7.1; aims at full conformance | Local experiments only until it reaches 1.0 |

```bash
# Benchmark on this repository, warm, three runs each; keep the fastest one that
# reports the same errors as tsc.
time npx tsc --noEmit
time bun check
time npx tsrs --noEmit --fast
```

- TypeScript 7.0 ships no programmatic API. Tools that embed TypeScript (typescript-eslint's type-aware rules, Volar for Vue, Astro, and Svelte, Angular templates) need 6.0 next to it: `@typescript/typescript6` provides `tsc6`.
- `tsc --checkers` (default 4) sets the number of checker workers; on a 2-vCPU runner, benchmark `--checkers 2`. The flag is experimental.
- `bun check` runs a `check` script from `package.json` instead of the checker when one exists, so name the script `typecheck`.

### Python

Ruff already covers lint and format. For types, mypy stays the arbiter; benchmark Pyrefly (Meta, 1.x) and ty (Astral, beta, 0.0.x versions) on the repository, and adopt one locally only when it reports the same errors.

## Fast checks belong in hooks, not in AGENTS.md

A line in AGENTS.md such as "run lint and typecheck before pushing" is advice. An agent deep in a long task skips steps, and nothing notices. A git hook runs on every commit or push, blocks it on failure, and prints the error the agent then fixes; the CI bypass guard catches the `--no-verify` cases. So:

- Put the fast checks in hooks. If the repository has an AGENTS.md (or CLAUDE.md), propose one line saying the hooks exist and must not be bypassed, instead of a list of commands; don't create the file just for that line.
- Keep the budgets: commit stage under 10 seconds on changed files, push stage under 60 seconds. When a commit-stage check outgrows its budget, such as a type-check over 10 seconds, move it to `pre-push` rather than dropping it. On `pre-push`, file-based hooks receive only the files changed in the pushed range, so they stay fast.

## Fast test runs

### Affected tests on push and in the CI guard (Vitest)

Use it when the whole suite no longer fits the 60-second push budget. pre-commit exports `PRE_COMMIT_FROM_REF` and `PRE_COMMIT_TO_REF` to hooks on `pre-push`, and in the CI guard's `--from-ref`/`--to-ref` run. This script runs only the tests that range affects, runs everything when there is no range, and fails closed:

```bash
#!/usr/bin/env bash
# scripts/affected-tests.sh: run the tests a push or PR affects, and fail closed.
# `vitest run --changed` exits 0 when it selects nothing, so a broken selection
# would otherwise report green with zero tests.
set -euo pipefail
# Paths that may change without selecting a test. Everything else is code.
skip_re='^(docs/|\.github/)|\.md$'
base="${PRE_COMMIT_FROM_REF:-}"
to="$(git rev-parse "${PRE_COMMIT_TO_REF:-HEAD}")"
# No range (a push that includes the root commit, the nightly --all-files run),
# or a push of a branch other than the checked-out one: run everything.
if [ -z "$base" ] || [ "$to" != "$(git rev-parse HEAD)" ]; then
  exec npx vitest run
fi
code_changed="$(git diff --name-only "$base" "$to" | grep -Ev "$skip_re" || true)"
selected="$(npx vitest list --changed "$base" --filesOnly | wc -l)"
if [ -n "$code_changed" ] && [ "$selected" -eq 0 ]; then
  echo "affected-tests: these changed files selected no test:" >&2
  echo "$code_changed" >&2
  echo "Add a test that imports them, add them to forceRerunTriggers, or extend skip_re." >&2
  exit 1
fi
exec npx vitest run --changed "$base" --passWithNoTests
```

`skip_re` lists what may be skipped, never what must run: a new directory or config file counts as code until someone adds it. Verified with Vitest 5.0.5: a change to an untested module selects no test and `vitest run --changed` exits 0 (the script exits 1 instead), and a tsconfig-only change selects no test unless tsconfig files are in `forceRerunTriggers`. The script catches an empty selection, not a partial one (untracked local test files also count as changed for Vitest); the nightly full run catches the rest. Monorepos use `nx affected` or `turbo run test --affected` the same way; see [github-actions.md](github-actions.md#affected-only-on-pull-requests-full-suite-nightly).

### Vitest: `isolate: false`

By default Vitest runs every test file in a fresh worker, child process, or VM context, re-importing the module graph each time. `isolate: false` (CLI `--no-isolate`) reuses workers: imported modules stay cached, so the app is imported once per worker instead of once per file. The report that prompted this section saw shards drop from 100 s to 35 s; measure on the repository before claiming a number.

Adopt it when a benchmark on the repository shows it faster and the suite passes with the reset hook below; otherwise keep isolation. The cost is shared state. Module-level singletons, spies, environment and global stubs, fake timers, and the DOM leak from one file into the next. (Checked with Vitest 5.0.5: two files that each push to a module-level store pass with isolation and fail without it, and pass again with the reset hook.) Setup files run before every test file even with isolation off, so a top-level `afterAll` in a setup file is a per-file reset hook:

```ts
// test/reset-state.ts — in test.setupFiles; runs before EVERY test file.
// Contract: a test leaves no module state, timer, env or global stub, mock,
// server, or DOM node behind. The config restores mocks and stubs; this file
// resets each module-level singleton the app keeps.
import { afterAll, vi } from "vitest";
import { resetStore } from "../src/store";

afterAll(() => {
  resetStore();
  vi.useRealTimers();
});
```

```ts
// vitest.config.ts
import { configDefaults, defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    isolate: false, // import the app once per worker
    setupFiles: ["test/reset-state.ts"], // per-file reset hook
    restoreMocks: true, // vi.restoreAllMocks() before each test
    unstubEnvs: true,
    unstubGlobals: true,
    forceRerunTriggers: [
      ...configDefaults.forceRerunTriggers,
      "**/tsconfig*.json",
      "**/package-lock.json",
      "**/pnpm-lock.yaml",
      "test/reset-state.ts",
    ],
  },
});
```

- Write the cleanup contract down: the comment at the top of the reset file, linked from the repository's testing docs.
- `isolate` has no effect on the `vmThreads` and `vmForks` pools; use `threads` or `forks`.
- `restoreMocks` can break async concurrent tests: one finishing test restores the spies others still use.
- Files that genuinely need a fresh environment go into a separate Vitest project with `isolate: true` (for example `**/*.isolated.test.ts`).
- A test that fails only with `isolate: false` has found a leak. Fix the leak or move the file to the isolated project; never delete or skip the test to get green.
- Workers: `maxWorkers` defaults to all available parallelism in run mode (4 on a public GitHub runner, 2 on a private one, more on a laptop). Benchmark `--maxWorkers=50%` before hard-coding anything.

### pytest

pytest already runs every file in one process, so there is no per-file re-import to remove. The equivalent speedup is parallel workers:

- `pytest -n auto` (pytest-xdist) starts one worker per physical core; `-n logical` one per logical core (needs `psutil`).
- `--dist loadfile` keeps each file's tests on one worker (module fixtures built once); `--dist worksteal` rebalances uneven files.
- Avoid per-test process isolation (`pytest-forked`'s `--forked`) unless a test needs it; mark those tests and run them separately.

The leak risk is the same, since tests share a process. The per-file reset is an autouse fixture scoped to the module:

```python
# conftest.py: runs after every test module, like Vitest's per-file reset hook.
import pytest

from myapp import cache, settings


@pytest.fixture(autouse=True, scope="module")
def reset_global_state():
    yield
    cache.clear()
    settings.reset()
```

Prefer `monkeypatch` for environment variables and attributes inside a test; it undoes itself after each test.

---

## CLI End-to-End Testing

When the project is a CLI tool, create `scripts/e2e_test.sh` to smoke-test every command before pushing. This catches regressions that unit tests miss (argument parsing bugs, output format changes, exit code issues).

### Discovering all CLI commands

```bash
# Python (click / typer / argparse):
python -m myapp --help
python -m myapp <subcommand> --help

# Go (cobra / urfave/cli):
./bin/myapp --help
./bin/myapp <subcommand> --help

# Node.js (commander / yargs / meow):
node cli.js --help
node cli.js <subcommand> --help

# Rust (clap):
./target/debug/myapp --help
./target/debug/myapp <subcommand> --help
```

### E2E test script template (Bash)

```bash
#!/usr/bin/env bash
# scripts/e2e_test.sh — CLI end-to-end smoke tests
# Runs every command/subcommand with representative inputs.
# Exit code 0 = all passed. Non-zero = something broke.
set -euo pipefail

# Colors for output
RED='\033[0;31m'; GREEN='\033[0;32m'; NC='\033[0m'
PASS=0; FAIL=0

check() {
  local desc="$1"; shift
  if "$@" > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} $desc"
    ((PASS++))
  else
    echo -e "  ${RED}✗${NC} $desc (cmd: $*)"
    ((FAIL++))
  fi
}

check_output() {
  local desc="$1"; local pattern="$2"; shift 2
  local out; out=$("$@" 2>&1)
  if echo "$out" | grep -q "$pattern"; then
    echo -e "  ${GREEN}✓${NC} $desc"
    ((PASS++))
  else
    echo -e "  ${RED}✗${NC} $desc — expected '$pattern' in output"
    ((FAIL++))
  fi
}

echo "=== CLI E2E Tests ==="

# --- Version / help ---
check "--version flag"       myapp --version
check "--help flag"          myapp --help
check_output "--help output" "Usage" myapp --help

# --- Subcommand: list ---
check "list --help"          myapp list --help
check "list (no args)"       myapp list
check "list --format json"   myapp list --format json

# --- Subcommand: create ---
check "create --help"        myapp create --help
check "create with input"    myapp create --name "e2e-test" --dry-run

# --- Error handling ---
check_output "unknown command exits non-zero" "error\|Error\|unknown" \
  bash -c 'myapp totally-invalid-cmd 2>&1; true'

# --- Cleanup (if any temp artifacts were created) ---
# rm -rf /tmp/e2e-test-*

echo ""
echo "=== Results: ${PASS} passed, ${FAIL} failed ==="
[ "$FAIL" -eq 0 ] || exit 1
```

### E2E test script template (Python)

For Python projects where `bash` scripting is awkward, use pytest with subprocess:

```python
# tests/e2e/test_cli.py
import subprocess, sys, pytest

CLI = [sys.executable, "-m", "myapp"]

def run(*args, **kwargs):
    return subprocess.run([*CLI, *args], capture_output=True, text=True, **kwargs)

def test_version():
    r = run("--version")
    assert r.returncode == 0
    assert r.stdout.strip()

def test_help():
    r = run("--help")
    assert r.returncode == 0
    assert "Usage" in r.stdout

def test_subcommand_list():
    r = run("list", "--help")
    assert r.returncode == 0

def test_subcommand_list_runs():
    r = run("list")
    assert r.returncode == 0

def test_subcommand_create_dry_run():
    r = run("create", "--name", "e2e-test", "--dry-run")
    assert r.returncode == 0

def test_unknown_command_exits_nonzero():
    r = run("totally-invalid-command")
    assert r.returncode != 0
```

Wire this into pre-commit on the `pre-push` stage:
```yaml
- id: e2e-cli
  name: CLI end-to-end tests
  entry: pytest tests/e2e/ -v
  language: system
  pass_filenames: false
  stages: [pre-push]
```

---

## Common Options

### Run only on specific files

```yaml
hooks:
  - id: eslint
    files: ^frontend/  # Only frontend directory
```

### Skip specific files

```yaml
hooks:
  - id: prettier
    exclude: ^vendor/|\.min\.js$
```

### Run only on specific stages

Valid stage names on pre-commit 3.2+ are the git hook names themselves — `pre-commit`, `pre-push`, `pre-merge-commit`, `commit-msg`, `post-checkout`, `manual`, and the rest. A hook with no `stages:` key runs in every stage unless the top-level `default_stages` narrows it, which is why every template here sets `default_stages: [pre-commit]`.

```yaml
hooks:
  - id: pytest-full
    stages: [pre-push]  # only on git push, not on every commit
```

### Install push-stage hooks

`pre-commit install` wires up the `pre-commit` git hook only. Push-stage hooks need a second call, and forgetting it is the most common reason a carefully staged test suite never runs:

```bash
pre-commit install                         # installs the pre-commit git hook
pre-commit install --hook-type pre-push    # installs the pre-push git hook
```

### Run push-stage hooks manually

`pre-commit run` covers commit-stage hooks only. To exercise the push stage — locally or in the CI bypass guard — name it explicitly:

```bash
pre-commit run --all-files --hook-stage pre-push
```

### Bypass

`git commit --no-verify` and `git push --no-verify` skip every hook, and no configuration can prevent it. Treat local hooks as fast feedback, and keep the diff-scoped CI guard in [github-actions.md](github-actions.md) as the enforcement point.

---

## Sources

Fetched 2026-11-01; tool versions move fast, so re-check before changing a template.

- Oxlint usage and rule coverage: https://oxc.rs/docs/guide/usage/linter.html
- Oxlint configuration (`.oxlintrc.json`, categories, plugins): https://oxc.rs/docs/guide/usage/linter/config.html
- Oxlint releases (oxlint 1.90.0, 2026-10-27): https://github.com/oxc-project/oxc/releases
- Announcing TypeScript 7.0 (2026-07-08: native compiler in `typescript`, 8–12× full builds, no API in 7.0, `@typescript/typescript6`, `--checkers`): https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/
- `bun check` (Bun 1.4.3, 2026-10-10): https://bun.com/docs/runtime/check
- `tsrs` README (oxc-project, 0.20.x, pre-1.0, tracking TypeScript 7.1): https://github.com/oxc-project/tsrs
- Vitest `isolate`: https://vitest.dev/config/isolate
- Vitest `setupFiles` (run before each test file; with isolation off, modules are cached and the setup file re-runs): https://vitest.dev/config/setupfiles
- Vitest `maxWorkers` (all available parallelism in run mode): https://vitest.dev/config/maxworkers
- Vitest `forceRerunTriggers` (defaults; full run with `--changed`): https://vitest.dev/config/forcereruntriggers
- Vitest `restoreMocks` (async concurrent caveat): https://vitest.dev/config/restoremocks
- Vitest improving performance (pools, isolation, sharding): https://vitest.dev/guide/improving-performance
- pytest-xdist distribution modes and `-n auto`/`-n logical`: https://pytest-xdist.readthedocs.io/en/stable/distribution.html
- ty (Astral, beta): https://github.com/astral-sh/ty
- Pyrefly (Meta, 1.4.0): https://github.com/facebook/pyrefly
- pre-commit (`PRE_COMMIT_FROM_REF`/`PRE_COMMIT_TO_REF`): https://pre-commit.com/
