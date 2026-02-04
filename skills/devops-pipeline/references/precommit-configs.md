# Pre-commit Configurations by Language

## Table of Contents

- [JavaScript/TypeScript](#javascripttypescript)
- [Python](#python)
- [Go](#go)
- [Rust](#rust)
- [Java](#java)
- [Multi-language](#multi-language)

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
        types: [javascript, tsx, ts]
        files: \.(js|jsx|ts|tsx)$

      - id: typecheck
        name: typecheck
        entry: npx tsc --noEmit
        language: system
        types: [ts, tsx]
        pass_filenames: false

      - id: test
        name: test
        entry: npm test
        language: system
        pass_filenames: false
        stages: [push]
```

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
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        stages: [push]
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

      - id: go-test
        name: go test
        entry: go test ./...
        language: system
        pass_filenames: false
        stages: [push]
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

      - id: cargo-test
        name: cargo test
        entry: cargo test
        language: system
        pass_filenames: false
        stages: [push]
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
        entry: mvn checkstyle:check
        language: system
        pass_filenames: false

      - id: spotbugs
        name: spotbugs
        entry: mvn spotbugs:check
        language: system
        pass_filenames: false

      - id: test
        name: test
        entry: mvn test
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
```

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
  - id: pytest
    stages: [push]  # Only on git push, not commit
```
