# Phase 0 — Baseline Protocol

Establish **baseline-green**: the recorded, reproducible state of "this project builds and its tests
run to a known pass rate". Everything downstream — every upgrade wave, every refactor task — is
verified against it. Without it the plan is unfalsifiable.

All probes here are **read-only** and **fail-soft**: check the tool exists, run it, record the result
or record **Not Assessed** with the reason. A missing tool never aborts Phase 0.

## Rule: probe before you run

```bash
command -v <tool> >/dev/null 2>&1 || echo "Not Assessed — <tool> not installed"
```

Never install anything. Never modify a lockfile to make a command work. If a build needs
`npm install` first, record **Not Assessed — dependencies not installed** rather than installing
them; "needs a clean install to build" is itself a finding worth reporting.

## Rule: prove the probes changed nothing

Snapshot before and after Phase 0:

```bash
git status --porcelain > /tmp/pre_baseline.txt
# ... run the probes ...
git status --porcelain | diff /tmp/pre_baseline.txt - || echo "PROBE MUTATED THE TREE"
```

New *untracked* build output (`coverage/`, `dist/`, `target/`) is acceptable — list it in the report's
Artifacts section. A changed **tracked** file is not: report it as a finding ("the test suite rewrites
committed snapshots on every run", "the build refreshes a stale lockfile") and note that the probe was
not reproducible. Do not revert it silently and do not let it pass unremarked.

Cap every probe with a timeout so a hanging build does not stall the run:

```bash
timeout 300 <build command>   # macOS: brew install coreutils, or drop the timeout and note it
```

## Baseline evidence table

Fill every row. `Value` must come from a command; `Evidence` is that command plus the decisive line
of its output.

| Row | What to record | Verdict input |
|---|---|---|
| **Build** | exit code + duration of the project's build command | non-zero → RED |
| **Tests — runnable** | whether the suite starts at all | cannot start → RED |
| **Tests — pass rate** | `passed/total`, plus skipped count | any failure → AMBER at best |
| **Coverage** | line/branch % if a coverage tool is configured | absent → note, not a verdict input |
| **Lint / typecheck** | exit code + error count | errors → AMBER |
| **CI** | workflow files present? last run status if `gh` is authenticated | absent → note |
| **Runtime versions** | declared (`engines`, `.nvmrc`, `.python-version`, `go.mod`, `rust-toolchain`) vs installed | mismatch → note, feeds `DEP` |
| **Lockfile** | present and committed? | missing → note, feeds P0 sprint |
| **Repo activity** | `git log -1 --format=%cd`, commit count last 12 months | context only |

### Verdict

| Verdict | Meaning |
|---|---|
| **GREEN** | builds, suite runs, 100% of non-skipped tests pass |
| **AMBER** | builds, suite runs, some tests fail or are skipped, or lint/typecheck errors |
| **RED** | does not build, or the test suite cannot start, or there is no test suite at all |
| **RED** | **the build could not be probed at all** — dependencies not installed, toolchain missing, no shell. This is the modal state of a long-neglected repo, and it is RED for the same reason a failing build is: nothing downstream is verifiable. The P0 task becomes "produce a reproducible build from a clean checkout" |

A **RED** baseline never stops the audit. It sets the plan's Sprint 0 to "restore baseline-green" and
makes every later task depend on that sprint.

## Per-stack probe commands

Run only those whose manifest is present. Substitute the project's own scripts when they differ —
read `package.json` scripts, `Makefile` targets, `pyproject.toml`, `justfile`, or CONTRIBUTING before
assuming a default.

**Use the non-mutating form of every command.** The defaults rewrite files: `cargo build` refreshes a
stale `Cargo.lock`, `bundle install` writes `.bundle/config`, and `npm test` on a Jest project writes
new `.snap` files into committed `__snapshots__`. On the stale repo this skill targets, that is the
common case, not an edge case.

| Stack | Build | Test | Coverage | Lint / types |
|---|---|---|---|---|
| Node / TS | `npm run build` (or `pnpm`/`yarn`) | `npm test -- --ci` (Jest `--ci` refuses to write new snapshots) | `npm test -- --ci --coverage` | `npx tsc --noEmit`, `npm run lint` |
| Python | `python -m build` or import check | `pytest -q -p no:cacheprovider` | `pytest --cov` | `ruff check .`, `mypy .` |
| Go | `go build ./...` | `go test ./...` | `go test -cover ./...` | `go vet ./...` |
| Rust | `cargo build --locked` | `cargo test --locked` | `cargo llvm-cov` | `cargo clippy --locked` |
| Java (Maven) | `mvn -q -o -DskipTests package` | `mvn -o test` | `mvn jacoco:report` | `mvn -q -o verify -DskipTests` |
| Java (Gradle) | `./gradlew assemble --offline` | `./gradlew test --offline` | `./gradlew jacocoTestReport` | `./gradlew check -x test` |
| Ruby | `bundle check` (reports without installing) | `bundle exec rspec` | `COVERAGE=1 bundle exec rspec` | `bundle exec rubocop` |
| PHP | `composer validate` | `vendor/bin/phpunit` | `phpunit --coverage-text` | `vendor/bin/phpstan analyse` |
| .NET | `dotnet build` | `dotnet test` | `dotnet test --collect:"XPlat Code Coverage"` | `dotnet format --verify-no-changes` |
| Flutter / Dart | `flutter build --debug` or `dart compile` | `flutter test` | `flutter test --coverage` | `dart analyze` |
| Swift | `swift build` | `swift test` | `swift test --enable-code-coverage` | `swiftlint` |
| Elixir | `mix compile` | `mix test` | `mix test --cover` | `mix credo` |

## App-runnable check (feeds the UX branch)

Determine whether the app can be started, without starting a long-lived process:

1. Look for a dev/start script or entry point (`package.json` scripts, `Procfile`, `docker-compose.yml`,
   `main.py`, `cmd/`).
2. Record **runnable** only if such an entry exists *and* the build row is not RED.
3. If not runnable, the `UX` dimension is static-only — review markup, components, and flows from
   source, and state the limitation in the report.

Do not launch servers, open browsers, or run migrations. This skill is read-only.

## Output of Phase 0

A completed baseline table plus the verdict, written into the report's Baseline section by Phase 3.
Carry forward to later phases:

- the exact **test command** (every planned task's acceptance criteria reference it),
- the **pass rate** at audit time (the "still green" bar tasks must not regress below),
- the list of rows marked **Not Assessed** (they become P0 tasks: add coverage tooling, add CI, and
  so on).
