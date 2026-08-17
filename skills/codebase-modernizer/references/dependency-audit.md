# DEP — Dependency and Runtime Currency

The dimension this skill owns outright. Output: one **finding record** per dependency that is behind,
vulnerable, unmaintained, or duplicated — plus the **upgrade wave** assignment that the plan turns
into sprints.

## Non-negotiable: read-only

Every command below reads. None of these are ever run by this skill:

```
npm update / npm install / ncu -u / yarn upgrade / pnpm up
pip install -U / poetry update / uv pip install
go get -u / cargo update / bundle update / composer update
mvn versions:use-latest-versions / dotnet add package
```

Upgrades are **planned**, executed later by the user against the plan. A bulk upgrade on a stale tree
yields a broken build and an unreviewable diff.

## Step 1 — Detect ecosystems

Presence of a manifest means the ecosystem is in scope. In a monorepo, each workspace package is its
own row.

| Ecosystem | Manifest | Lockfile |
|---|---|---|
| npm / yarn / pnpm | `package.json` | `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml` |
| Python | `pyproject.toml`, `requirements*.txt`, `setup.py`, `Pipfile` | `poetry.lock`, `uv.lock`, `Pipfile.lock` |
| Go | `go.mod` | `go.sum` |
| Rust | `Cargo.toml` | `Cargo.lock` |
| Ruby | `Gemfile` | `Gemfile.lock` |
| Java | `pom.xml`, `build.gradle(.kts)` | `gradle.lockfile` |
| PHP | `composer.json` | `composer.lock` |
| .NET | `*.csproj`, `Directory.Packages.props` | `packages.lock.json` |
| Dart / Flutter | `pubspec.yaml` | `pubspec.lock` |
| Swift | `Package.swift` | `Package.resolved` |
| Elixir | `mix.exs` | `mix.lock` |
| Containers | `Dockerfile`, `docker-compose.yml` | pinned base-image tags |
| CI actions | `.github/workflows/*.yml` | pinned `uses:` refs |

`scripts/dep_scan.sh` performs this detection and runs the probes below. Prefer it over hand-running
commands; read its markdown output and turn each row into a finding record.

## Step 2 — Probe, fail-soft

For each detected ecosystem: `command -v <tool>` first. If absent, record
**Not Assessed — `<tool>` not installed** for that ecosystem and move on.

| Ecosystem | Outdated | Vulnerabilities |
|---|---|---|
| npm | `npm outdated --json` | `npm audit --json` |
| pnpm | `pnpm outdated --format json` | `pnpm audit --json` |
| yarn (v1) | `yarn outdated --json` | `yarn audit --json` |
| yarn (berry) | `yarn upgrade-interactive --dry-run` *(read-only listing)* | `yarn npm audit --json` |
| Python (pip) | `pip list --outdated --format=json` | `pip-audit -f json` |
| Python (poetry) | `poetry show --outdated` | `poetry run pip-audit -f json` |
| Python (uv) | `uv pip list --outdated` | `uv pip audit` |
| Go | `go list -u -m -json all` | `govulncheck ./...` |
| Rust | `cargo outdated --format json` | `cargo audit --json` |
| Ruby | `bundle outdated --parseable` | `bundle exec bundler-audit check` |
| Maven | `mvn versions:display-dependency-updates` | `mvn org.owasp:dependency-check-maven:check` |
| Gradle | `./gradlew dependencyUpdates` *(needs ben-manes plugin)* | `./gradlew dependencyCheckAnalyze` |
| PHP | `composer outdated --format=json` | `composer audit --format=json` |
| .NET | `dotnet list package --outdated` | `dotnet list package --vulnerable` |
| Dart / Flutter | `flutter pub outdated --json` | `dart pub audit` if available |
| Elixir | `mix hex.outdated` | `mix deps.audit` |
| Swift | `swift package show-dependencies --format json` | no first-party tool — Not Assessed |
| Containers | compare `FROM` tags to the image's current stable tag | `trivy image <tag>` if installed |
| CI actions | grep `uses: owner/repo@ref` and compare to the action's latest release | — |

Most of these need network access. **Offline** → record installed versions from the lockfile and mark
currency **Not Assessed — offline**. Never guess a latest version.

**Probe byproducts.** A few probes create untracked build directories as a side effect —
`dotnet list package` triggers a restore into `obj/`, `flutter pub outdated` writes `.dart_tool/`,
cargo touches `target/`, Gradle writes `.gradle/`. These modify no tracked file, so they are not a
contract breach, but they must be listed in the report's Artifacts section so `git status` stays
explainable. If creating them is unacceptable for the target repo, skip that ecosystem's probe and
mark it **Not Assessed — probe would write build output**.

## Step 3 — Runtime and toolchain currency

Separate from packages, and usually the higher-impact finding on a neglected repo.

| Check | Where declared | Finding when |
|---|---|---|
| Language runtime | `engines.node`, `.nvmrc`, `.python-version`, `go.mod` go directive, `rust-toolchain.toml`, `<LangVersion>` | version is past end-of-life, or ≥ 2 majors behind current LTS/stable |
| Framework major | the framework dep itself (React, Django, Rails, Spring, Laravel, Flutter…) | a supported major exists above the pinned one |
| Build toolchain | bundler, compiler, test runner versions | unmaintained, or blocking a runtime upgrade |
| Base images | `FROM` tags | tag is EOL or `:latest` (unpinned is its own finding) |
| CI runner images | `runs-on:` | deprecated runner label |

An **EOL runtime is always `Critical`** — it stops receiving security fixes, and every other upgrade
is blocked behind it.

## Step 4 — Classify each dependency

| Field | Values |
|---|---|
| `Gap` | `current` · `patch` · `minor` · `major` · `major×N` (N majors behind) |
| `Risk` | `vuln-critical` · `vuln-high` · `eol` · `unmaintained` (no release ≥ 24 months) · `deprecated` · `none` |
| `Blast radius` | count of import sites (`grep -rl` the package name) |
| `Wave` | see below |
| `Breaking` | for majors: named breaking changes, from the migration source |

Severity mapping for the report:

| Severity | When |
|---|---|
| `Critical` | `vuln-critical`, or an EOL runtime, or a dependency with a known exploited CVE |
| `High` | `vuln-high`, `major×2+` on a high-blast-radius dep, deprecated with no successor pinned |
| `Medium` | single `major` behind, `unmaintained`, unpinned base image |
| `Low` | `patch`/`minor` gaps, cosmetic version drift |

## Step 5 — Assign upgrade waves

An **upgrade wave** is one batch that ships and is verified together. Waves are ordered; each wave's
acceptance criterion is that baseline-green still holds after it.

| Wave | Contents | Sizing |
|---|---|---|
| `W0` | lockfile creation/commit, tooling needed to verify anything | P0 |
| `W1` | security patches — anything with `vuln-critical` / `vuln-high`, smallest version bump that clears the advisory | P1, one task |
| `W2` | all `patch` + `minor` gaps, batched per ecosystem | P1, one task per ecosystem |
| `W3` | runtime / toolchain upgrade | P2, its own task, usually first in P2 |
| `W4+` | **one major per task**, ordered by blast radius ascending, dependents after their dependencies | P2 |

Never batch majors. Never put a major in the same task as the patch/minor batch — when the suite goes
red you must know which bump did it.

## Step 6 — Migration source for every major

Every `major` task must name where its breaking changes came from. In order of preference:

1. **Context7 MCP** when available — `resolve-library-id` then `query-docs` for the migration or
   upgrade guide. Prefer this over model memory; library APIs change faster than training data.
2. The project's own `CHANGELOG.md` / release notes in the installed package.
3. The upstream repository's migration guide (fetch only if the user permits network access).

If none is reachable, the task says **migration guide not retrieved — spike required**, and its first
acceptance criterion is producing that guide. Never invent breaking changes from memory.

## Finding record shape

```markdown
| ID | Package | Ecosystem | Installed | Latest | Gap | Risk | Blast | Wave | Severity | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|
| F-DEP-01 | react | npm | 16.14.0 | 19.2.0 | major×3 | none | 84 files | W5 | High | package.json:31 |
| F-DEP-02 | lodash | npm | 4.17.19 | 4.17.21 | patch | vuln-high | 12 files | W1 | Critical | package-lock.json:2841 (GHSA-35jh-r3h4-6jhm) |
```

`Evidence` is the manifest or lockfile path plus line, and the advisory ID when risk is a vuln.
