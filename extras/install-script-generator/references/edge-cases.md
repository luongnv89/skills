# Step Reports, Edge Cases, and Platform Notes

## Step completion reports

After completing each major step, output a status report:

```
◆ [Step Name] ([step N of M] — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          √ pass (note if relevant)
  [Check 3]:          × fail — [reason]
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Use `√` for pass, `×` for fail, `—` for context. The "Criteria" line summarises acceptance criteria met.

### Phase-specific check templates

Phase 1 (Exploration): target identified, install method recorded, dependencies listed, `<owner>/<repo>` and default branch read, `env_info.json` written (or `not run`).

Phase 2 (Planning): `installation_plan.yaml` written, no `# TODO` left, dry run exited 0 and printed its `DRY RUN:` line with no placeholder warning, every `Install ...` step has a rollback.

Phase 3 (Generation): `install.sh` written, `bash -n` exit 0, placeholder `grep` empty, `shellcheck -S error` exit 0 (or `not run`), `install.sh` executed (`yes` only after an approved run, else `no`).

Phase 4 (Documentation): README one-liner found by `grep`, `USAGE_GUIDE.md` written, raw URL status recorded (HTTP status or `not live until pushed`).

A phase's `Result:` is `PASS` when every check passed, `PARTIAL` when a check is `not run`, and `FAIL` when a check failed. The run's status comes from the rules in `final-report.md`, not from the phase results alone.

## Edge cases the install.sh must handle

- **Unsupported OS** — `die "Unsupported operating system: $os"`; exits non-zero, tells user which OS was detected.
- **Missing package manager** — `detect_package_manager` returns `unknown`; `install_deps` calls `die "Unsupported package manager 'unknown'"`.
- **No sudo access** — `need_sudo` checks `id -u` and `sudo`; if neither root nor sudo is available, exit with "Requires root. Run as root or install sudo."
- **Windows without PowerShell** — `main` in `install.sh` detects MSYS/Cygwin and calls `warn`; an `install.ps1` is generated separately for native Windows.
- **Non-standard repo structure** — adjust the URL path and document it in the README snippet.

## Platform-specific notes

### Windows
- Prefer `winget` over `choco` when available.
- Use PowerShell (`install.ps1`); handle UAC elevation.
- One-liner: `irm https://raw.githubusercontent.com/<owner>/<repo>/main/install.ps1 | iex`.

### Linux
- Detect distro family (Debian/RedHat/Arch) and pick the right package manager.
- Handle sudo gracefully; support both `curl` and `wget` for the one-liner.

### macOS
- Use Homebrew as the primary package manager.
- Handle Apple Silicon vs Intel differences.
- Respect Gatekeeper / notarization for signed binaries.

## Error handling guarantees

- All scripts exit non-zero on failure (`set -e`).
- Each step logs what it's doing before execution.
- Failed dependency installs show the exact missing package and package manager.
- Verification failure at the end gives clear remediation steps.
- Coloured output makes errors easy to spot in terminal.
