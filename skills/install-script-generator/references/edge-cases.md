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

Phase 1 (Exploration): target identified, dependencies mapped, OS compatibility checked.

Phase 2 (Planning): install order defined, rollback planned.

Phase 3 (Generation): script created, cross-platform tested.

Phase 4 (Documentation): README updated, one-liner verified.

## Edge cases the install.sh must handle

- **Unsupported OS** — `die "Unsupported operating system: $os"`; exits non-zero, tells user which OS was detected.
- **Missing package manager** — `detect_package_manager` returns `unknown`; `install_deps` calls `die` listing the missing manager.
- **No sudo access** — `need_sudo` checks `id -u` and `sudo`; if neither root nor sudo is available, exit with "Please run as root or install sudo."
- **Windows without PowerShell** — `install.sh` detects MSYS/Cygwin and warns; an `install.ps1` is generated separately for native Windows.
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
