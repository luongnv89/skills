# CLI End-to-End Testing

Use this when the skill's target project is a CLI tool. The goal: verify the CLI actually works end-to-end, not just that the code compiles.

## Discover all commands

```bash
# For Python click/typer apps:
python -m myapp --help
python -m myapp <subcommand> --help

# For Go cobra/urfave apps:
./myapp --help
./myapp <subcommand> --help

# For Node.js commander/yargs:
node cli.js --help
```

## Script template

Create `scripts/e2e_test.sh` (or `scripts/e2e_test.py` for Python) that:

1. Builds/installs the CLI in a temp environment
2. Runs each command with representative inputs (including edge cases: empty input, invalid flags, `--help`)
3. Asserts exit codes and key output patterns
4. Cleans up temp artifacts

Example structure for a Python CLI:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== E2E: CLI smoke tests ==="
# Test each command/subcommand
python -m myapp --version
python -m myapp --help
python -m myapp subcommand1 --help
python -m myapp subcommand1 --input tests/fixtures/sample.txt
python -m myapp subcommand2 --flag value
# Test error paths
python -m myapp unknown-command 2>&1 | grep -q "Error" && echo "unknown command error path verified"
echo "=== E2E: All passed ==="
```

## Pre-commit wiring (push stage)

```yaml
- repo: local
  hooks:
    - id: e2e-cli
      name: CLI end-to-end tests
      entry: bash scripts/e2e_test.sh
      language: system
      pass_filenames: false
      stages: [push]
```
