# Templates

Copy and adapt these snippets into the target repository. Keep paths stable so
the pre-commit hook and CI workflow run the same local runner.

## `.pre-commit-config.yaml`

Merge this local hook into the existing config. Preserve existing repos and hooks.
The entry invokes Python directly (no shell wrapper) so it works the same on
macOS, Linux, and Windows. The runner reads extra args from the
`SECURITY_CHECK_ARGS` environment variable, which all three OSes support.

```yaml
repos:
  - repo: local
    hooks:
      - id: security-check
        name: local security hardening check
        entry: python scripts/security_check.py
        language: system
        pass_filenames: false
        stages: [pre-commit]
```

Install the hook:

```bash
pre-commit install
pre-commit run security-check --all-files
```

Force-bypass invocation by OS (only after a typed `YES` confirmation):

```bash
# macOS / Linux (bash, zsh)
SECURITY_CHECK_ARGS=--force git commit

# Windows PowerShell
$env:SECURITY_CHECK_ARGS = "--force"; git commit; Remove-Item Env:SECURITY_CHECK_ARGS

# Windows cmd.exe
set SECURITY_CHECK_ARGS=--force && git commit && set SECURITY_CHECK_ARGS=
```

## `security/security-tools.json`

Write only the tools selected for the current project.

```json
{
  "fail_on": ["CRITICAL", "HIGH"],
  "checks": [
    {
      "name": "gitleaks",
      "category": "secrets",
      "required": true,
      "command": ["gitleaks", "detect", "--source", ".", "--redact", "--report-format", "json", "--report-path", "{output}"]
    },
    {
      "name": "trivy",
      "category": "dependencies",
      "required": true,
      "command": ["trivy", "fs", "--scanners", "vuln", "--skip-db-update", "--format", "json", "--exit-code", "0", "."]
    },
    {
      "name": "semgrep",
      "category": "static",
      "required": true,
      "command": ["semgrep", "--config", "security/semgrep-rules.yml", "--json", "--error", "."]
    }
  ]
}
```

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

      - name: Warm vulnerability databases
        run: |
          trivy fs --download-db-only . || true

      - name: Run local security checks
        run: python3 scripts/security_check.py

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

Bypass is discouraged. When it is necessary, it requires an interactive
confirmation:

```bash
SECURITY_CHECK_ARGS=--force git commit
```

You must type `YES` at the prompt.
```
