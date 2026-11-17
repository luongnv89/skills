# Templates

Copy and adapt these snippets into the target repository. Keep paths stable so
the pre-commit hook and CI workflow run the same local runner.

## `.pre-commit-config.yaml`

Merge this local hook into the existing config. Preserve existing repos and hooks.
The entry invokes `python3` directly (no shell wrapper). On macOS and most Linux
distros `python3` resolves to the active interpreter; on Windows the official
Python launcher also exposes `python3`. If a target environment has only bare
`python` available, override the entry locally to `python scripts/security_check.py`.

```yaml
repos:
  - repo: local
    hooks:
      - id: security-check
        name: local security hardening check
        entry: python3 scripts/security_check.py
        language: system
        pass_filenames: false
        stages: [pre-commit]
```

Install the hook:

```bash
pre-commit install
pre-commit run security-check --all-files
```

Force-bypass: run the runner directly (not through `git commit`) and type `YES`
at the prompt, then commit with `--no-verify`. `pre-commit` closes hook stdin,
so `--force` cannot be answered from inside `git commit`. See SKILL.md
§"4. Bypass Policy" for the full policy.

`SECURITY_CHECK_ARGS` is shell-split and appended after `sys.argv[1:]`, so env
flags override CLI flags on conflict (argparse last-wins for booleans). Set
the variable only for the bypass invocation and unset it afterwards.

```bash
# macOS / Linux (bash, zsh)
SECURITY_CHECK_ARGS=--force python3 scripts/security_check.py
git commit --no-verify

# Windows PowerShell
$env:SECURITY_CHECK_ARGS = "--force"; python scripts\security_check.py; Remove-Item Env:SECURITY_CHECK_ARGS
git commit --no-verify

# Windows cmd.exe
set SECURITY_CHECK_ARGS=--force && python scripts\security_check.py && set SECURITY_CHECK_ARGS=
git commit --no-verify
```

## `security/security-tools.json`

Write only the tools selected for the current project. Each check declares
`triggers` so pre-commit only runs the work the staged file set actually
implies. Omit `triggers` to inherit the per-tool defaults baked into
`scripts/security_check.py` for known names (`gitleaks`, `trivy`, `semgrep`,
`bandit`, `cargo-audit`).

```json
{
  "fail_on": ["CRITICAL", "HIGH"],
  "trip_all_paths": [
    ".pre-commit-config.yaml",
    "security/**",
    ".github/workflows/**",
    "Dockerfile",
    "Dockerfile.*",
    "**/Dockerfile",
    "**/Dockerfile.*",
    ".dockerignore",
    "scripts/security_check.py"
  ],
  "checks": [
    {
      "name": "gitleaks",
      "category": "secrets",
      "required": true,
      "triggers": { "always": true },
      "command": ["gitleaks", "detect", "--source", ".", "--redact", "--report-format", "json", "--report-path", "{output}"]
    },
    {
      "name": "trivy",
      "category": "dependencies",
      "required": true,
      "triggers": {
        "paths": [
          "package-lock.json", "pnpm-lock.yaml", "yarn.lock",
          "Cargo.lock", "Cargo.toml",
          "go.mod", "go.sum",
          "requirements*.txt", "pyproject.toml", "Pipfile.lock",
          "composer.lock", "Gemfile.lock", "pom.xml", "build.gradle",
          "**/package-lock.json", "**/pnpm-lock.yaml", "**/yarn.lock",
          "**/Cargo.lock", "**/go.mod", "**/go.sum",
          "**/requirements*.txt", "**/pyproject.toml"
        ]
      },
      "command": ["trivy", "fs", "--scanners", "vuln", "--skip-db-update", "--format", "json", "--exit-code", "0", "."]
    },
    {
      "name": "semgrep",
      "category": "static",
      "required": true,
      "triggers": {
        "paths": [
          "**/*.py", "**/*.js", "**/*.jsx", "**/*.ts", "**/*.tsx",
          "**/*.go", "**/*.rb", "**/*.php", "**/*.java",
          "**/*.rs", "**/*.swift", "**/*.sh", "**/*.bash",
          "**/*.yaml", "**/*.yml", "**/Dockerfile", "**/Dockerfile.*"
        ]
      },
      "command": ["semgrep", "--config", "security/semgrep-rules.yml", "--json", "--error", "."]
    }
  ]
}
```

### Trigger semantics

| Field | Meaning |
|---|---|
| `triggers.always: true` | Run on every commit. Use for secret scanners. |
| `triggers.paths: [globs]` | Run only when at least one staged file matches. |
| `trip_all_paths` (top-level) | Globs that force every applicable check to run when staged. Defaults to `.pre-commit-config.yaml`, `security/**`, `.github/workflows/**`, `Dockerfile*`, `.dockerignore`, `scripts/security_check.py`. |

Globs are matched with `fnmatch` against the POSIX path returned by
`git diff --cached --name-only --diff-filter=ACMR -z`. Use `**/foo` to match
in any subdirectory.

`SECURITY_CHECK_SCOPE=all` (env) or `--all` (flag) forces a full scan.
`SECURITY_CHECK_SCOPE=staged` or `--staged-only` requires staged files and
errors otherwise.

## `security/semgrep-rules.yml`

Start small. Add project-specific rules as real findings appear.

```yaml
rules:
  - id: python-dangerous-subprocess-shell
    languages: [python]
    severity: WARNING
    message: Avoid shell=True with dynamic command input.
    metadata:
      cwe: "CWE-78"
      owasp: "A03:2021-Injection"
    patterns:
      - pattern: subprocess.$FUNC(..., shell=True, ...)

  - id: javascript-eval
    languages: [javascript, typescript]
    severity: ERROR
    message: Avoid eval-like execution of dynamic strings.
    metadata:
      cwe: "CWE-95"
      owasp: "A03:2021-Injection"
    pattern-either:
      - pattern: eval(...)
      - pattern: new Function(...)

  - id: javascript-child-process-exec-dynamic
    languages: [javascript, typescript]
    severity: ERROR
    message: Avoid child_process.exec with a dynamic command. Use execFile or spawn with an args array.
    metadata:
      cwe: "CWE-78"
      owasp: "A03:2021-Injection"
    patterns:
      - pattern-either:
          - pattern: child_process.exec($CMD, ...)
          - pattern: require('child_process').exec($CMD, ...)
          - pattern: |
              import { exec } from 'child_process'
              ...
              exec($CMD, ...)
      # Filter out string-literal calls like exec("ls -la") — only flag dynamic input.
      - metavariable-pattern:
          metavariable: $CMD
          pattern-not-regex: ^(['"`]).*\1$

  - id: hardcoded-debug-mode
    languages: [python, javascript, typescript]
    severity: WARNING
    message: Hard-coded debug mode can expose internals in production.
    metadata:
      cwe: "CWE-489"
    pattern-either:
      - pattern: debug=True
      - pattern: DEBUG = true
```

## `.github/workflows/security.yml`

Create this only when the user requests `--ci` and Phase 1 passes.

```yaml
name: Security

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read
  # Add `security-events: write` only if you also add a SARIF upload step
  # (e.g. github/codeql-action/upload-sarif). See SKILL.md "Phase 2".

jobs:
  local-security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.x"

      - name: Install selected tools
        run: |
          python -m pip install --upgrade pip
          python -m pip install semgrep
          # Install gitleaks/trivy using package-manager steps selected for this repo.

      - name: Compute weekly cache stamp
        id: cache-stamp
        run: echo "week=$(date -u +%Y-%V)" >> "$GITHUB_OUTPUT"

      - name: Cache trivy vulnerability DB
        uses: actions/cache@v4
        with:
          path: ~/.cache/trivy
          # Rotate weekly so DB stays fresh without writing a new cache entry on
          # every run. Avoid keys based on github.run_id — they grow unbounded.
          key: trivy-db-${{ runner.os }}-${{ steps.cache-stamp.outputs.week }}
          restore-keys: |
            trivy-db-${{ runner.os }}-

      - name: Warm vulnerability databases
        run: |
          trivy fs --download-db-only . || true

      - name: Run local security checks
        # CI is the safety net: always full-scan, never apply staged-file
        # scoping. Developers get fast scoped scans locally; CI verifies
        # nothing slipped through.
        run: python3 scripts/security_check.py --all

      - name: Upload security reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: security-reports
          path: |
            security/security-report.json
            security/security-report.md
```

## `SECURITY.md` Summary Section

```markdown
## Local Security Checks

This repository uses local-first security checks through pre-commit.

### Selected Tools

| Category | Tool | Why selected | Runtime network |
|---|---|---|---|
| Secrets | gitleaks | Single binary, scans repository content locally | No |
| Dependencies | trivy | Reads project lockfiles with local vulnerability DB | No, uses warmed DB |
| Static analysis | semgrep | Local rules under `security/semgrep-rules.yml` | No |

### Run Locally

```bash
python3 scripts/security_check.py
pre-commit run security-check --all-files
```

### Explicit Bypass

Bypass is discouraged. When necessary, run the runner directly with
`--force`, type `YES` at the prompt, then commit with `--no-verify`.
`pre-commit` closes hook stdin, so the prompt cannot be answered from
inside `git commit`.

```bash
SECURITY_CHECK_ARGS=--force python3 scripts/security_check.py
# Type YES at the prompt, then:
git commit --no-verify
```

You must type the literal string `YES`. Record the bypass in this file
(date, reason, link to the report) so the override is auditable.
```
