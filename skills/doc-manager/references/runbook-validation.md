# Runbook Validation

How to produce the end-to-end validation script and troubleshooting log for any deploy / release / setup / operational-process doc (path C).

## The check-only contract

The script's job is to **verify that the runbook's steps would succeed** — not to run them. It must be safe to run repeatedly, on any machine, without side effects.

Rules:

1. **Default mode is `--check`**: verify preconditions and assert expected state. No mutation, no outward calls that change anything.
2. **Every destructive or outward-facing step is gated.** Two ways to gate:
   - `--run-destructive` flag — the step only executes when the operator explicitly opts in.
   - `MANUAL:` marker — the step is printed as a manual instruction and skipped by the script entirely (use when the action can't be safely automated at all, e.g. `terraform apply`, a prod cutover).
3. **Idempotent + read-only in check mode.** Checks may read files, test connectivity (`curl -sf`, `nc -z`), confirm a tool is installed (`command -v`), confirm an env var is set (`[ -n "$X" ]`), confirm a port/endpoint responds. They may **not** write, deploy, migrate, delete, or push.
4. **One check per documented step.** The script mirrors the runbook: each numbered step in the doc maps to a `[CHECK]` (or `[MANUAL]`) line, so a passing script proves the doc's preconditions hold.
5. **Exit non-zero on any failed check.** So the run's acceptance criterion (`exits 0 on --check`) is meaningful.

## Placement

- Writable repo: `scripts/validate-<runbook-name>.sh`, `chmod +x`. The runbook section links to it near the top: `> Validate this runbook: \`./scripts/validate-deploy.sh --check\``.
- Read-only repo: emit the script inline in the change summary instead of writing it, **and run it once** so you can report its `--check` exit code — the acceptance criterion requires a known exit status, which you can't have for a script you never executed.

## Template

```bash
#!/usr/bin/env bash
# Validates: docs/deployment.md  (check-only by default)
# Usage: validate-deploy.sh [--check] [--run-destructive]
set -uo pipefail

MODE="check"
[ "${1:-}" = "--run-destructive" ] && MODE="destructive"

fail=0
ok()   { printf '[CHECK] %-32s OK\n' "$1"; }
bad()  { printf '[CHECK] %-32s FAIL — %s\n' "$1" "$2"; fail=1; }
man()  { printf '[MANUAL] %-31s SKIPPED (run by operator)\n' "$1"; }

# --- Step 1: tooling present (docs/deployment.md step 1) ---
command -v docker >/dev/null && ok "docker installed" || bad "docker installed" "not on PATH"

# --- Step 2: required env (docs/deployment.md step 2) ---
[ -n "${DEPLOY_TOKEN:-}" ] && ok '$DEPLOY_TOKEN set' || bad '$DEPLOY_TOKEN set' "unset"

# --- Step 3: target reachable (docs/deployment.md step 3) ---
curl -sf -o /dev/null "${DEPLOY_URL:-http://localhost:8080}/health" \
  && ok "deploy target /health" || bad "deploy target /health" "no 2xx"

# --- Step 4: destructive — gated (docs/deployment.md step 4) ---
if [ "$MODE" = "destructive" ]; then
  # real deploy command goes here, only under explicit opt-in
  echo "[RUN] deploying…"; # ./deploy.sh
else
  man "terraform apply / deploy"
fi

exit $fail
```

Adapt each `[CHECK]` to a real step in the doc, and cite the doc line the check corresponds to in a comment (`# docs/deployment.md step N`). Keep checks that can genuinely fail — a script of trivially-true checks proves nothing.

## Fix → document loop

Run the script in check mode. For each failure:

1. Diagnose the real cause (missing tool, wrong path in the doc, stale env name, unreachable endpoint).
2. Fix the **doc** if the doc was wrong; fix the **check** if the check was wrong. If the failure is an environment gap the operator must close, note it as a prerequisite in the runbook.
3. Append the entry to `docs/troubleshooting.md`:

```markdown
## {symptom, one line}
- **Cause:** {what actually caused it} (`path:line` if code-derived)
- **Fix:** {the exact resolution — command, doc change, or prerequisite}
- **Seen during:** validate-deploy.sh --check
```

4. Re-run until `--check` exits 0.

Only entries for problems **actually encountered** go in `troubleshooting.md` — do not pre-populate it with hypothetical issues (that would be inventing). If validation surfaced no failures, leave the file untouched and say so in the summary.
