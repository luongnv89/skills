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

## Install Commands

Prefer existing project package managers. Use only what the detected project needs.

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
