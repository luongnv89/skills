# Project analysis (Step 1)

Everything here is read-only: `git` read commands, file reads and directory listings. Never run a project script, install, fetch, stash, hook or scanner in this step; finding counts come after approval (Step 4). Record each fact with the file or command it came from.

## 1. Locate the repository

| Command | Use |
|---|---|
| `git -C <input> rev-parse --show-toplevel` | The repo root. Fails: the input is not in a git repo |
| `git -C <input> rev-parse --show-prefix` | Non-empty: the input is a subfolder of that repo |
| `git -C <top> remote get-url origin` | Fails: the plan says `sync: skipped (no origin)` |
| `git -C <top> rev-parse --abbrev-ref HEAD` | `HEAD` means detached: the plan says the install will stop and ask |
| `git -C <top> status --porcelain --untracked-files=all` | The pre-sync dirty list |
| `git -C <top> config --get core.hooksPath` | Set: git calls hooks from that folder, not `.git/hooks` |

Three outcomes, each stated in the plan:

- **Toplevel:** analyse and plan normally.
- **Subfolder:** flag it as `input is a subfolder of <top>`. Config files and CI jobs can be scoped to the subfolder. Hook config and hook installs live at the toplevel and are separate plan items the user must approve explicitly; they affect every project in that repo.
- **No repo:** drop hooks and history metrics. The plan says `hooks: left out (not a git repo)` and `history: left out (not a git repo)`. Config files and a CI workflow can still be planned.

Several inputs in the same repo are merged into one repository entry with several project roots.

## 2. Languages and their share

- `git -C <top> ls-files` (or a directory walk outside git), grouped by extension; count lines with `wc -l` on the tracked files of each language.
- Skip vendored and generated paths: `vendor/`, `node_modules/`, `third_party/`, `dist/`, `build/`, `*.min.js`, lockfiles, and paths listed as `linguist-vendored` or `linguist-generated` in `.gitattributes`.
- Report each language with its share of lines. A language under 5% gets no tools unless the user asks (*SKILL.md → Edge Cases*).

## 3. Frameworks and package managers

| Signal | Means |
|---|---|
| `pyproject.toml`, `requirements*.txt`, `uv.lock`, `poetry.lock`, `Pipfile.lock` | Python; package manager from the lockfile |
| `package.json` + `package-lock.json` / `pnpm-lock.yaml` / `yarn.lock` / `bun.lock*` | Node; framework from dependencies (`react`, `next`, `vue`, `express`) |
| `go.mod` | Go modules |
| `Cargo.toml` | Rust |
| `Package.swift`, `*.xcodeproj`, `Podfile` | Swift (SwiftPM, Xcode, CocoaPods) |
| `Gemfile`, `pom.xml`, `build.gradle*` | Ruby, Java/Kotlin |
| `Dockerfile*`, `*.sh`, `.github/workflows/*.yml` | Container, shell and workflow files get their own linters |

## 4. Hook manager

Check in this order and record every match; more than one is a conflict to report.

| Signal | Manager |
|---|---|
| `core.hooksPath` = `.husky/_` or `.husky`, or a `.husky/` folder with a `pre-commit` file | husky |
| `lefthook.yml`, `lefthook.yaml`, `.lefthook.yml` | lefthook |
| `.pre-commit-config.yaml` | pre-commit |
| `.git/hooks/pre-commit` that is not a sample file | a hand-written hook; read it, do not replace it |
| none | none: the plan proposes pre-commit |

Also record `lint-staged` config (`package.json` key or `.lintstagedrc*`), since husky setups often call it.

## 5. CI workflows and analyzers already configured

- List `.github/workflows/*.yml` (and `.gitlab-ci.yml` or others, which this skill reports but does not edit). For each job: triggers, `permissions:`, every `uses:` and every tool named in `run:`.
- List analyzer config files: `ruff.toml`, `[tool.ruff]`, `.flake8`, `eslint.config.*`, `.eslintrc*`, `biome.json`, `.golangci.yml`, `.swiftlint.yml`, `.semgrep.yml`, `.gitleaks.toml`, `.gitleaksignore`, `.secrets.baseline`, `.bandit`, `osv-scanner.toml`, `.github/dependabot.yml`.
- **security-setup footprint:** a `security-check` hook id in `.pre-commit-config.yaml`, `scripts/security_check.py`, `security/security-tools.json`, or `.github/workflows/security.yml`. When the JSON exists, read its `checks[].name` and `checks[].category`: those tools count as configured for their category, in the hook and in CI.
- For every configured tool, record where it runs (hook id, workflow and job) and its entry command. The dedup in Step 2 matches on these.

## 6. Test runner

Record the test command and where it comes from (`package.json` scripts, `pyproject.toml`, `Makefile`, CI steps). This skill does not add tests; the plan only avoids placing analyzers that would duplicate a test step.

## 7. Size and history

| Metric | Command |
|---|---|
| Tracked files | `git ls-files \| wc -l` |
| Commits in the last 90 days | `git rev-list --count --since=90.days HEAD` |
| Files per commit (median of the last 50 non-merge commits) | `git log --no-merges -50 --name-only --format=` grouped by commit |

The median files per commit sizes the timing sample and the hook estimate. A repo with no commits gets an estimate of 5 files, marked as an assumption.

## 8. Monorepo signals

`workspaces` in `package.json`, `pnpm-workspace.yaml`, `go.work`, a Cargo `[workspace]`, `nx.json`, `turbo.json`, or several manifests in separate subfolders. In a monorepo, each package root is a project in the plan, and the hook config stays single at the toplevel.

## Output of Step 1

One block per input:

```text
P1 api  (/work/api, toplevel)
  languages: Python 88%, Shell 7%, YAML 5%
  package manager: uv (uv.lock)   framework: FastAPI
  hook manager: pre-commit (.pre-commit-config.yaml: trailing-whitespace, ruff)
  CI: .github/workflows/ci.yml (test job: pytest)
  analyzers configured: ruff (hook ruff, ruff.toml)
  security-setup footprint: none
  size: 214 tracked files · 63 commits / 90 days · 3 files per commit (median)
  origin: yes · branch: main · dirty: 1 path (kept out of the sample)
```
