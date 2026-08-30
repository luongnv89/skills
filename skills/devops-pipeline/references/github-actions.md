# GitHub Actions Workflow Templates

Philosophy: **lean CI**. pre-commit already handles format, lint, type-check, unit tests, and E2E tests locally, so GitHub Actions carries only the four responsibilities the SKILL's Check Routing Table assigns it: a diff-scoped bypass guard, multi-version matrix testing, secrets-dependent work, and deployment.

## The one rule every template here follows

`pre-commit run` executes **commit-stage hooks only**. Hooks on `stages: [pre-push]` — the full test suite, coverage threshold, and CLI E2E — are silently skipped unless you also pass `--hook-stage pre-push`. `pre-commit/action@v3.0.1` shares this blind spot, which is why these templates call the CLI directly instead:

```yaml
      - name: Verify hooks were not bypassed
        run: |
          pip install pre-commit
          base="${{ github.event.pull_request.base.sha || github.event.before }}"
          pre-commit run --from-ref "$base" --to-ref HEAD
          pre-commit run --hook-stage pre-push --from-ref "$base" --to-ref HEAD
```

Scoping to the diff with `--from-ref`/`--to-ref` is what keeps the guard cheap. Running `--all-files` in CI re-checks the entire repository on every push and is the cost blow-up this skill exists to avoid.

## Table of Contents

- [Minimal (pre-commit already covers everything)](#minimal-pre-commit-already-covers-everything)
- [JavaScript/TypeScript](#javascripttypescript)
- [Python](#python)
- [Go](#go)
- [Rust](#rust)
- [Java (Maven)](#java-maven)
- [Multi-language](#multi-language)
- [Common Additions](#common-additions)

---

## Minimal (pre-commit already covers everything)

If your pre-commit setup runs format, lint, type-check, unit tests, and E2E tests, CI shrinks to a single bypass guard:

```yaml
name: CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      # Bypass guard: the ONLY overlap with pre-commit. Diff-scoped, so it costs
      # seconds. Both invocations are required — `pre-commit run` alone executes
      # commit-stage hooks only and silently skips the pre-push suite and E2E.
      - name: Verify hooks were not bypassed
        run: |
          pip install pre-commit
          base="${{ github.event.pull_request.base.sha || github.event.before }}"
          pre-commit run --from-ref "$base" --to-ref HEAD
          pre-commit run --hook-stage pre-push --from-ref "$base" --to-ref HEAD
```

This job proves the hooks actually ran on the incoming commits — the one thing local tooling cannot prove about itself, since `--no-verify` skips hooks entirely. It checks only the diff, so it stays in the seconds range no matter how large the repository grows.

---

## JavaScript/TypeScript

Add matrix version testing — the part pre-commit can't do locally:

```yaml
name: CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      # Bypass guard: the ONLY overlap with pre-commit. Diff-scoped, so it costs
      # seconds. Both invocations are required — `pre-commit run` alone executes
      # commit-stage hooks only and silently skips the pre-push suite and E2E.
      - name: Verify hooks were not bypassed
        run: |
          pip install pre-commit
          base="${{ github.event.pull_request.base.sha || github.event.before }}"
          pre-commit run --from-ref "$base" --to-ref HEAD
          pre-commit run --hook-stage pre-push --from-ref "$base" --to-ref HEAD

  matrix-test:
    runs-on: ubuntu-latest
    # Only run matrix test on push to main (not every PR commit)
    if: github.event_name == 'push'

    strategy:
      matrix:
        node-version: [18, 20, 22]

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm test

      - name: Build
        run: npm run build

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        if: matrix.node-version == 20  # upload once
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
```

### With pnpm

```yaml
      - name: Setup pnpm
        uses: pnpm/action-setup@v2
        with:
          version: 8

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'pnpm'

      - name: Install dependencies
        run: pnpm install --frozen-lockfile
```

---

## Python

```yaml
name: CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Install dependencies
        run: pip install -e ".[dev]"

      # Bypass guard: the ONLY overlap with pre-commit. Diff-scoped, so it costs
      # seconds. Both invocations are required — `pre-commit run` alone executes
      # commit-stage hooks only and silently skips the pre-push suite and E2E.
      - name: Verify hooks were not bypassed
        run: |
          pip install pre-commit
          base="${{ github.event.pull_request.base.sha || github.event.before }}"
          pre-commit run --from-ref "$base" --to-ref HEAD
          pre-commit run --hook-stage pre-push --from-ref "$base" --to-ref HEAD

  matrix-test:
    runs-on: ubuntu-latest
    if: github.event_name == 'push'

    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Run tests with coverage
        run: pytest --cov --cov-report=xml -q

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        if: matrix.python-version == '3.12'
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
```

### With Poetry

```yaml
      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: 1.7.1
          virtualenvs-create: true
          virtualenvs-in-project: true

      - name: Load cached venv
        uses: actions/cache@v4
        with:
          path: .venv
          key: venv-${{ runner.os }}-${{ matrix.python-version }}-${{ hashFiles('**/poetry.lock') }}

      - name: Install dependencies
        run: poetry install --no-interaction
```

---

## Go

```yaml
name: CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version: '1.22'
          cache: true

      # Bypass guard: the ONLY overlap with pre-commit. Diff-scoped, so it costs
      # seconds. Both invocations are required — `pre-commit run` alone executes
      # commit-stage hooks only and silently skips the pre-push suite and E2E.
      - name: Verify hooks were not bypassed
        run: |
          pip install pre-commit
          base="${{ github.event.pull_request.base.sha || github.event.before }}"
          pre-commit run --from-ref "$base" --to-ref HEAD
          pre-commit run --hook-stage pre-push --from-ref "$base" --to-ref HEAD

  matrix-test:
    runs-on: ubuntu-latest
    if: github.event_name == 'push'

    strategy:
      matrix:
        go-version: ['1.21', '1.22']

    steps:
      - uses: actions/checkout@v4

      - name: Set up Go ${{ matrix.go-version }}
        uses: actions/setup-go@v5
        with:
          go-version: ${{ matrix.go-version }}
          cache: true

      - name: Run tests with coverage
        run: go test -race -coverprofile=coverage.out ./...

      - name: Build
        run: go build ./...

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        if: matrix.go-version == '1.22'
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: coverage.out
```

---

## Rust

```yaml
name: CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Rust
        uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt, clippy

      - name: Cache cargo
        uses: Swatinem/rust-cache@v2

      # Bypass guard: the ONLY overlap with pre-commit. Diff-scoped, so it costs
      # seconds. Both invocations are required — `pre-commit run` alone executes
      # commit-stage hooks only and silently skips the pre-push suite and E2E.
      - name: Verify hooks were not bypassed
        run: |
          pip install pre-commit
          base="${{ github.event.pull_request.base.sha || github.event.before }}"
          pre-commit run --from-ref "$base" --to-ref HEAD
          pre-commit run --hook-stage pre-push --from-ref "$base" --to-ref HEAD

  matrix-test:
    runs-on: ubuntu-latest
    if: github.event_name == 'push'

    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        rust: [stable, beta]

    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4

      - name: Setup Rust ${{ matrix.rust }}
        uses: dtolnay/rust-toolchain@master
        with:
          toolchain: ${{ matrix.rust }}

      - name: Cache cargo
        uses: Swatinem/rust-cache@v2

      - name: Run tests
        run: cargo test --all-features

      - name: Build release
        run: cargo build --release
```

---

## Java (Maven)

```yaml
name: CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up JDK 21
        uses: actions/setup-java@v4
        with:
          java-version: '21'
          distribution: 'temurin'
          cache: 'maven'

      # Bypass guard: the ONLY overlap with pre-commit. Diff-scoped, so it costs
      # seconds. Both invocations are required — `pre-commit run` alone executes
      # commit-stage hooks only and silently skips the pre-push suite and E2E.
      - name: Verify hooks were not bypassed
        run: |
          pip install pre-commit
          base="${{ github.event.pull_request.base.sha || github.event.before }}"
          pre-commit run --from-ref "$base" --to-ref HEAD
          pre-commit run --hook-stage pre-push --from-ref "$base" --to-ref HEAD

  matrix-test:
    runs-on: ubuntu-latest
    if: github.event_name == 'push'

    strategy:
      matrix:
        java-version: ['17', '21']

    steps:
      - uses: actions/checkout@v4

      - name: Set up JDK ${{ matrix.java-version }}
        uses: actions/setup-java@v4
        with:
          java-version: ${{ matrix.java-version }}
          distribution: 'temurin'
          cache: 'maven'

      - name: Run tests
        run: mvn test -q

      - name: Build
        run: mvn package -DskipTests -q
```

---

## Multi-language

For monorepos, use path filters to only run relevant jobs:

```yaml
name: CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      frontend: ${{ steps.changes.outputs.frontend }}
      backend: ${{ steps.changes.outputs.backend }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: changes
        with:
          filters: |
            frontend:
              - 'frontend/**'
            backend:
              - 'backend/**'

  frontend:
    needs: changes
    if: needs.changes.outputs.frontend == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - name: Verify hooks were not bypassed (frontend)
        run: |
          pip install pre-commit
          base="${{ github.event.pull_request.base.sha || github.event.before }}"
          pre-commit run --from-ref "$base" --to-ref HEAD
          pre-commit run --hook-stage pre-push --from-ref "$base" --to-ref HEAD

  backend:
    needs: changes
    if: needs.changes.outputs.backend == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -e "backend/[dev]"
      - name: Verify hooks were not bypassed (backend)
        run: |
          pip install pre-commit
          base="${{ github.event.pull_request.base.sha || github.event.before }}"
          pre-commit run --from-ref "$base" --to-ref HEAD
          pre-commit run --hook-stage pre-push --from-ref "$base" --to-ref HEAD
```

---

## Common Additions

### Upload coverage to Codecov

```yaml
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
```

### PR status comment

```yaml
      - name: Comment PR
        uses: actions/github-script@v7
        if: github.event_name == 'pull_request'
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '✅ All checks passed!'
            })
```

### Deployment (on merge to main)

```yaml
  deploy:
    needs: [quality, matrix-test]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # Add deployment steps
```

### Skipping specific pre-commit hooks in CI

Some hooks (like interactive formatters) may not make sense in CI. Skip them with the `SKIP` env var:

```yaml
      - name: Verify hooks were not bypassed
        env:
          SKIP: "no-commit-to-branch"  # comma-separated hook IDs to skip
        run: |
          pip install pre-commit
          base="${{ github.event.pull_request.base.sha || github.event.before }}"
          pre-commit run --from-ref "$base" --to-ref HEAD
          pre-commit run --hook-stage pre-push --from-ref "$base" --to-ref HEAD
```

Skip sparingly. Every skipped hook is a check that now runs nowhere, since the guard is the only place CI re-verifies hook output.

---

### Keeping the matrix off the hot path

Every template here gates `matrix-test` on `if: github.event_name == 'push'`. Keep that. A three-version matrix on every pull request commit triples the bill to re-confirm a signal the hooks already gave locally; running it on merges to the default branch catches version-specific breakage before release at a fraction of the cost. For a library where version skew is the main risk, widen it to `pull_request` only on the release branch, never on every push to a feature branch.
