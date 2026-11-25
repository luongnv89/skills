# Tool catalog (Step 2)

Free tools only. Each row gives the licence, whether the tool can check an explicit file list (needed for a staged-file hook), its cache, a rough cost class and the default placement. Cost classes are rough guides for the estimate, not measurements: **fast** usually under 1 s for a typical commit, **medium** 1 to 5 s, **slow** over 5 s or whole-repo by design. Step 5 measures the real time.

Placement: **hook** = pre-commit on staged files; **CI** = pull requests and the default branch; **sched** = a weekly scheduled workflow. Flags shown are a starting point: confirm them against the installed version's `--help` (*SKILL.md → Rules 8*).

## Lint

| Language | Tool | Licence | File list | Cache | Cost | Place |
|---|---|---|---|---|---|---|
| Python | Ruff (`ruff check`, `ruff format --check`) | MIT | yes | yes, `.ruff_cache/` | fast | hook + CI |
| JS / TS | ESLint (`eslint --cache`) | MIT | yes | yes, `.eslintcache` | medium | hook + CI |
| JS / TS | Biome (`biome check`) | MIT or Apache-2.0 | yes | n/a (fast without one) | fast | hook + CI, instead of ESLint only when the repo has no ESLint |
| Go | `go vet` | BSD-3-Clause | package-based | Go build cache | medium | CI |
| Go | golangci-lint | GPL-3.0 | package-based; `--new-from-rev` limits output to new issues | yes | medium to slow | CI; hook only with a fast-linter subset |
| Swift | SwiftLint (`swiftlint lint --quiet <paths>`) | MIT | yes | yes, `--cache-path` | fast | hook + CI |
| Rust | Clippy (`cargo clippy`) | MIT or Apache-2.0 | crate-based | cargo target dir | slow | CI |
| Ruby | RuboCop | MIT | yes | yes | medium | hook + CI |
| Shell | ShellCheck | GPL-3.0 | yes | no | fast | hook + CI |
| Dockerfile | hadolint | GPL-3.0 | yes | no | fast | hook + CI |
| GitHub Actions | actionlint | MIT | yes | no | fast | hook + CI |
| GitHub Actions | zizmor (workflow security) | MIT | yes | no | fast | CI |

Prefer the linter a project already has. Never add a second linter for the same language and job (ESLint and Biome, Ruff and flake8) unless the user asks.

## SAST

| Scope | Tool | Licence | File list | Cost | Place | Notes |
|---|---|---|---|---|---|---|
| Many languages | Semgrep Community Edition (`semgrep scan`) | engine LGPL-2.1 | yes | slow | CI | Registry rules (`--config p/...`) are fetched from semgrep.dev and are published under the Semgrep Rules License, which is not OSI open source (check its current terms); say so in the plan, or use a local rules file. Pass `--metrics=off`: with registry configs, metrics are sent by default. On pull requests, `--baseline-commit <base sha>` reports only new findings. No login needed |
| Python | Bandit | Apache-2.0 | yes | fast | hook + CI | `-b <baseline.json>` compares against a baseline report |
| Go | gosec | Apache-2.0 | package-based | medium | CI | |
| Many languages | CodeQL | GitHub CodeQL terms, not open source | n/a | slow | CI | **Public GitHub repos only.** Private repos need a paid GitHub Advanced Security licence: never plan it there |
| Apps handling personal data | Bearer CLI | Elastic License 2.0, **not open source** | n/a | slow | CI | **Off by default.** Offer it only when the app stores or processes personal data, labelled "Elastic License 2.0, not open source". Never enable it without an explicit yes |

## Secrets

| Tool | Licence | Hook command | CI command | Baseline | Notes |
|---|---|---|---|---|---|
| gitleaks | MIT | pre-commit hook id `gitleaks` from the gitleaks repo (runs a staged-diff scan), or `gitleaks git --pre-commit --staged --redact` | `gitleaks git --redact` (history; checkout with `fetch-depth: 0`) or `gitleaks dir --redact .` | `.gitleaksignore` of fingerprints (*merge-and-baseline.md → Baselines*) | Run the CLI in CI rather than `gitleaks-action`: its README asks organization accounts for a licence key, which is a sign-up (check the current README) |
| detect-secrets | Apache-2.0 | `detect-secrets-hook --baseline .secrets.baseline` | `detect-secrets-hook --baseline .secrets.baseline <tracked files>` (`detect-secrets scan --baseline` rewrites the baseline, so it is not the CI check) | `.secrets.baseline`, which stores hashed secrets | Use instead of gitleaks only when the repo already has it |
| TruffleHog | AGPL-3.0 | not in the hook | `trufflehog git file://. --no-verification` | none | Verification sends each candidate secret to its provider's API, so the plan always passes `--no-verification`. Offer only when the user asks |

The detect-secrets and TruffleHog commands are marked `verify on install` in the plan. One secret scanner per repo. security-setup's `security-tools.json` listing `gitleaks` counts as that scanner.

## Dependencies

Advisories change without any commit, so dependency scans run in CI and on a weekly schedule, never in the hook.

| Ecosystem | Tool | Licence | Network | Place |
|---|---|---|---|---|
| Any lockfile | OSV-Scanner | Apache-2.0 | queries the OSV.dev API with package names and versions | CI + sched |
| Python | pip-audit | Apache-2.0 | PyPI or OSV advisories | CI + sched |
| Node | `npm audit` / `pnpm audit` | ships with the package manager | the registry's advisory endpoint | CI + sched |
| Go | govulncheck | BSD-3-Clause | the Go vulnerability database | CI + sched |
| Rust | cargo-audit | MIT or Apache-2.0 | the RustSec advisory database | CI + sched |
| Many | Trivy (`trivy fs`) | Apache-2.0 | downloads its vulnerability DB | CI + sched |
| GitHub | Dependabot alerts | free GitHub feature | GitHub | a repository setting the user turns on; the plan lists it, the skill does not change it |

Pick one scanner per ecosystem. OSV-Scanner covers most lockfiles in one job.

## Excluded by default

Name each in the plan's *Left out* list when it would otherwise apply:

- Paid or account-bound services (SonarCloud, Snyk, Codacy, DeepSource, Semgrep AppSec Platform, GitHub Advanced Security on private repos): Rule 2.
- Tools whose licence restricts use and that are not listed above: not open source.
- Slow whole-repo scanners in the hook: over budget, moved to CI.
- A second tool for a job already covered: duplicate.

## Placement summary

| Category | Hook | CI | Scheduled |
|---|---|---|---|
| Lint (file-level) | staged files, check mode, cache on | full repo or changed files | no |
| SAST | only fast, file-level tools (Bandit) | full scan, new findings on PRs | optional |
| Secrets | staged diff | full history or tree | no |
| Dependencies | no | yes | weekly |

Every CI job the plan adds has `permissions: contents: read`, actions pinned the way the repo pins them, `timeout-minutes` on each job, a `concurrency` group on pull-request workflows, locked or pinned tool installs, and no path filter on a workflow whose check is required.
