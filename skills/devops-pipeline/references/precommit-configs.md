# Pre-commit Configurations by Language

Philosophy: **run as much as possible locally**. Commit-stage hooks catch issues immediately; push-stage hooks run the full test suite and E2E tests before code leaves the machine. GitHub Actions becomes a thin safety net.

## Table of Contents

- [JavaScript/TypeScript](#javascripttypescript)
- [Python](#python)
- [Go](#go)
- [Rust](#rust)
- [Java](#java)
- [Multi-language](#multi-language)
- [CLI End-to-End Testing](#cli-end-to-end-testing)
- [Common Options](#common-options)

## JavaScript/TypeScript

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
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

      - id: eslint
        name: eslint
        entry: npx eslint --fix
        language: system
        files: \.(js|jsx|ts|tsx)$

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

      # Full test suite + E2E on push
      - id: test-full
        name: full test suite
        entry: npm test
        language: system
        pass_filenames: false
        stages: [push]

      # If this is a CLI tool, add E2E hook on push stage:
      # - id: e2e-cli
      #   name: CLI end-to-end tests
      #   entry: bash scripts/e2e_test.sh
      #   language: system
      #   pass_filenames: false
      #   stages: [push]
```

> **Note on unit vs full tests**: split your test script into `test:unit` (fast, no I/O) and `test` (all). If you can't split them, run all tests on commit — slow feedback is still better than no feedback.

## Python

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
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

      # Full suite (unit + integration) on push
      - id: pytest-full
        name: pytest full suite
        entry: pytest --tb=short -q
        language: system
        pass_filenames: false
        stages: [push]

      # CLI E2E tests on push (if this is a CLI tool)
      # - id: e2e-cli
      #   name: CLI end-to-end tests
      #   entry: bash scripts/e2e_test.sh
      #   language: system
      #   pass_filenames: false
      #   stages: [push]
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
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
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
        stages: [push]

      # CLI E2E on push (if this is a CLI tool)
      # - id: e2e-cli
      #   name: CLI end-to-end tests
      #   entry: bash scripts/e2e_test.sh
      #   language: system
      #   pass_filenames: false
      #   stages: [push]
```

## Rust

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
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
        stages: [push]

      # CLI E2E on push (if this is a CLI tool)
      # - id: e2e-cli
      #   name: CLI end-to-end tests
      #   entry: bash scripts/e2e_test.sh
      #   language: system
      #   pass_filenames: false
      #   stages: [push]
```

## Java

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
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
        stages: [push]
```

## Multi-language

For monorepos or projects with multiple languages:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-toml
      - id: check-added-large-files
      - id: detect-private-key

  # Add language-specific hooks from sections above
  # Use `files:` patterns to scope hooks to specific directories
  # Example: scope Go hooks to backend/, Node hooks to frontend/
```

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

Wire this into pre-commit on push stage:
```yaml
- id: e2e-cli
  name: CLI end-to-end tests
  entry: pytest tests/e2e/ -v
  language: system
  pass_filenames: false
  stages: [push]
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

```yaml
hooks:
  - id: pytest-full
    stages: [push]  # Only on git push, not commit
```

### Install push-stage hooks

```bash
pre-commit install                         # install commit-msg and pre-commit hooks
pre-commit install --hook-type pre-push    # also install push hooks
```

### Run push-stage hooks manually

```bash
pre-commit run --all-files --hook-stage push
```
