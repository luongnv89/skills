# Tool Selection

Choose the smallest set of tools that covers the project without adding cloud
runtime dependencies.

## Detection Matrix

| Evidence | Secrets | Dependencies | Static Analysis |
|---|---|---|---|
| Any git repo | `gitleaks` | `trivy fs --skip-db-update` | `semgrep` with local rules |
| `pyproject.toml`, `requirements.txt` | `gitleaks` or existing `detect-secrets` | `trivy fs --skip-db-update` | `semgrep`, optional `bandit` |
| `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock` | `gitleaks` | `trivy fs --skip-db-update` | `semgrep`, existing ESLint security rules if present |
| `Cargo.lock` | `gitleaks` | `cargo audit` or `trivy fs --skip-db-update` | `semgrep`, `cargo clippy` if already used |
| `go.mod` | `gitleaks` | `trivy fs --skip-db-update` | `semgrep`, optional `gosec` |

## Offline Runtime Rules

- Hook runtime must use scanner caches and local rule files.
- Do dependency database downloads during setup, not inside the hook.
- Use `trivy fs --skip-db-update` in hooks after the DB is warmed.
- Use `semgrep --config security/semgrep-rules.yml` to avoid registry fetches.
- Do not use hosted scanners or tools that require API keys for the local hook.

## Scoping Rules

Pre-commit must be fast on small commits without dropping coverage. Each tool
declares its own relevance rule via `triggers` in `security/security-tools.json`.

| Tool | Trigger | Why |
|---|---|---|
| gitleaks (or detect-secrets) | `always: true` | Secrets land in `.md`, `.json`, `.env.example`, `Dockerfile`, anywhere. Never path-restrict the secret scanner. |
| trivy | lockfiles + manifests (`package-lock.json`, `Cargo.lock`, `go.mod`, etc.) | Dep scanners are lockfile-driven; running on a commit that touches no lockfile produces no signal. |
| semgrep | source-language extensions (`**/*.py`, `**/*.ts`, `**/Dockerfile`, etc.) | Rules apply to specific languages — match the staged set against rule `languages:`. |
| bandit | `**/*.py` | Python-only. |
| cargo-audit | `Cargo.lock`, `Cargo.toml` | Crate advisories require Cargo metadata. |

A repo-wide `trip_all_paths` list catches files where category-based scoping is
unsafe — `.pre-commit-config.yaml`, `security/**`, `.github/workflows/**`,
`Dockerfile*`, `.dockerignore`, `scripts/security_check.py`. When any of those
is staged, every applicable check runs (workflow injection and Dockerfile RCE
must not slip past because no `.py` happened to be in the same commit).

CI always runs `python3 scripts/security_check.py --all`. Scoping is a
developer-experience win on commits, not a coverage compromise overall.

## Install Commands

Prefer existing project package managers. Use only what the detected project needs.

### Optional supply-chain install guardrail

Socket Firewall can be used as a lightweight local default path for everyday
dependency installs. It complements, but does not replace, lockfile scanning.
Recommend it only as developer shell setup; the generated pre-commit hook must
not require `sfw` unless the user explicitly asks for that policy.

For macOS/Linux users on `zsh` or `bash`, add only the aliases relevant to the
project's package managers:

```bash
alias npm="sfw npm"
alias yarn="sfw yarn"
alias pnpm="sfw pnpm"
alias pip="sfw pip"
alias uv="sfw uv"
alias cargo="sfw cargo"
```

If Socket Firewall is missing, link to the official install instructions rather
than pasting an unverified install command.

### macOS

```bash
brew install pre-commit gitleaks trivy semgrep
python3 -m pip install bandit detect-secrets
cargo install cargo-audit
```

### Linux

```bash
python3 -m pip install pre-commit semgrep bandit detect-secrets
```

Install `gitleaks` and `trivy` from the official package repository for the
distribution when possible. If no package exists, print the official install
instructions instead of pasting an unverified curl pipe.

### Windows

Use a package manager (winget, Chocolatey, or Scoop) for the binary tools.
Semgrep does not support native Windows yet — install it inside WSL2 or skip
it on Windows-only workstations and rely on language-native scanners (`bandit`,
ESLint security rules, `cargo audit`).

```powershell
# winget (preferred on Windows 11)
winget install --id gitleaks.gitleaks
winget install --id AquaSecurity.Trivy
python -m pip install pre-commit bandit detect-secrets
```

```powershell
# Chocolatey
choco install gitleaks trivy
python -m pip install pre-commit bandit detect-secrets
```

```powershell
# Scoop
scoop install gitleaks trivy
python -m pip install pre-commit bandit detect-secrets
```

For semgrep on Windows, run from WSL2:

```bash
# Inside WSL2 Ubuntu
python3 -m pip install semgrep
```

If WSL2 is not available, document the gap in `SECURITY.md` and keep the other
local checks — do not pretend semgrep coverage exists.

### Project-local Python Tools

When the repo already uses Python virtual environments, prefer:

```bash
python3 -m pip install pre-commit semgrep bandit detect-secrets
```

## Database Warming

Run these during setup or in a manually triggered maintenance step:

```bash
trivy fs --download-db-only .
cargo audit fetch
```

If a command is unavailable or needs network access, document the failure in
`SECURITY.md` and keep hook runtime offline.

## Tool Selection Notes

- Prefer `gitleaks` over `detect-secrets` for general repos because it is a
  single binary and works without Python.
- Prefer `trivy` for mixed-language dependency scanning because it reads many
  lockfiles from one command.
- Use `semgrep` with local rules for a small static baseline; do not fetch remote
  rules during pre-commit.
- Add language-specific tools only when they materially improve coverage and are
  already common in that ecosystem.
