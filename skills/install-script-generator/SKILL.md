---
name: install-script-generator
version: 1.0.0
description: |
  Generate cross-platform installation scripts for any software, library, or module. Use when users ask to "create an installer", "generate installation script", "automate installation", "setup script for X", "install X on any OS", or need automated deployment across Windows, Linux, and macOS. The skill follows a three-phase approach: (1) Environment exploration - detect OS, gather system info, check dependencies; (2) Installation planning - propose steps with verification; (3) Execution with documentation generation.
---

# Install Script Generator

Generate robust, cross-platform installation scripts with automatic environment detection, verification, and documentation.

## Workflow

### Phase 1: Environment Exploration

Gather comprehensive system information:

```bash
# Run the environment explorer script
python3 scripts/env_explorer.py
```

The script detects:
- Operating system (Windows/Linux/macOS) and version
- CPU architecture (x86_64, ARM64, etc.)
- Package managers available (apt, yum, brew, choco, winget)
- Shell environment (bash, zsh, powershell, cmd)
- Existing dependencies and versions
- User permissions (admin/sudo availability)

Output: JSON summary of system capabilities and constraints.

### Phase 2: Installation Planning

Based on the environment analysis and target software:

1. **Identify dependencies** - List all required packages/libraries
2. **Check existing installations** - Avoid reinstalling what exists
3. **Order operations** - Resolve dependency graph
4. **Add verification steps** - Each step must be verifiable
5. **Plan rollback** - Define cleanup on failure

Create the plan using:

```bash
python3 scripts/plan_generator.py --target "<software_name>" --env-file env_info.json
```

Plan structure:
```yaml
target: "<software_name>"
platform: "detected_os"
steps:
  - name: "Install dependency X"
    command: "..."
    verify: "command to verify success"
    rollback: "cleanup command if failed"
  - name: "Configure system"
    command: "..."
    verify: "..."
```

### Phase 3: Execution

Execute the plan with real-time verification:

```bash
python3 scripts/executor.py --plan installation_plan.yaml
```

Execution behavior:
- Run each step sequentially
- Verify success after each step
- On failure: execute rollback, report error, stop
- Log all output for debugging
- Generate installation report

### Phase 4: Documentation Generation

After successful installation, generate usage documentation:

```bash
python3 scripts/doc_generator.py --target "<software_name>" --plan installation_plan.yaml
```

Output includes:
- Installation summary (what was installed, where)
- Quick start guide
- Common commands/usage examples
- Troubleshooting tips
- Uninstallation instructions

## Output Files

The skill generates these files in the current directory:

| File | Description |
|------|-------------|
| `env_info.json` | System environment analysis |
| `installation_plan.yaml` | Detailed installation steps |
| `install_report.md` | Execution log and status |
| `USAGE_GUIDE.md` | User documentation |

## Platform-Specific Notes

### Windows
- Prefer `winget` over `choco` when available
- Use PowerShell for script execution
- Handle UAC elevation requirements

### Linux
- Detect distro family (Debian/RedHat/Arch)
- Use appropriate package manager
- Handle sudo requirements gracefully

### macOS
- Use Homebrew as primary package manager
- Handle Apple Silicon vs Intel differences
- Respect Gatekeeper and notarization

## Example Usage

User request: "Create an installation script for Node.js"

1. Run env_explorer.py to detect system
2. Generate plan with Node.js as target
3. Execute plan (installs Node.js + npm)
4. Generate USAGE_GUIDE.md with npm commands

## Error Handling

- All scripts exit with non-zero codes on failure
- Verification failures trigger rollback
- Detailed error messages include remediation hints
- Partial installations are cleaned up automatically
