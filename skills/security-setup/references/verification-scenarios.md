# File-Aware Scoping — No-Blindspot Verification Scenarios

Walk through these manually after install. Each one is a real failure mode
naive scoping creates.

1. **Docs-only with leaked key.** Stage a `README.md` containing a synthetic
   `AKIA…` AWS key. Hook fails HIGH (gitleaks ran).
2. **Docs-only clean.** Stage a `README.md` with no secrets. Exit 0;
   `trivy`/`semgrep`/`bandit` reported as skipped with reason; runtime is
   measurably faster than `--all`.
3. **Lockfile change.** Stage `package-lock.json`. `trivy` runs.
4. **Source code with anti-pattern.** Stage a `.py` file containing
   `eval(user_input)`. `semgrep` and `bandit` run; exit non-zero.
5. **Workflow tampering.** Stage `.github/workflows/foo.yml` with
   `${{ github.event.issue.title }}` interpolated into a `run:` step. The
   trip-all rule fires; `semgrep` runs.
6. **Full scan.** `python3 scripts/security_check.py --all` behaves like
   pre-1.3.0 (every configured check executes).
