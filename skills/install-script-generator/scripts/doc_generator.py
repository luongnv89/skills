#!/usr/bin/env python3
"""
Documentation Generator - Creates user documentation after successful installation.
Generates a comprehensive USAGE_GUIDE.md file.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Try to use PyYAML if available
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def yaml_load(content):
    """Load YAML content."""
    if HAS_YAML:
        return yaml.safe_load(content)
    else:
        # Basic YAML parsing for simple structures
        result = {}
        for line in content.split('\n'):
            if ':' in line and not line.strip().startswith('-'):
                key, _, value = line.partition(':')
                key = key.strip()
                value = value.strip()
                if value and not value.startswith('{') and not value.startswith('['):
                    result[key] = value
        return result


def get_software_info(target):
    """Try to get information about the installed software."""
    info = {
        "version": None,
        "location": None,
        "help_output": None,
    }

    # Try common version commands
    for cmd in [f"{target} --version", f"{target} -v", f"{target} version"]:
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                info["version"] = result.stdout.strip().split('\n')[0]
                break
        except Exception:
            pass

    # Try to find location
    for cmd in [f"which {target}", f"command -v {target}", f"where {target}"]:
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                info["location"] = result.stdout.strip().split('\n')[0]
                break
        except Exception:
            pass

    # Try to get help output
    for cmd in [f"{target} --help", f"{target} -h", f"{target} help"]:
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                info["help_output"] = result.stdout[:2000]  # Truncate
                break
        except Exception:
            pass

    return info


def generate_usage_guide(target, plan, env_info=None, report=None):
    """Generate the usage guide markdown."""
    software_info = get_software_info(target)

    lines = [
        f"# {target.title()} Usage Guide",
        "",
        f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        "",
        "---",
        "",
        "## Installation Summary",
        "",
    ]

    # Installation details
    if software_info["version"]:
        lines.append(f"**Version installed:** {software_info['version']}")
    if software_info["location"]:
        lines.append(f"**Installation location:** `{software_info['location']}`")
    if plan:
        lines.append(f"**Platform:** {plan.get('platform', 'Unknown')}")
        lines.append(f"**Package manager used:** {plan.get('package_manager', 'Unknown')}")

    lines.extend(["", "---", "", "## Quick Start", ""])

    # Quick start section
    lines.append(f"### Verify Installation")
    lines.append("")
    lines.append("```bash")
    lines.append(f"{target} --version")
    lines.append("```")
    lines.append("")

    # Common commands section
    lines.extend([
        "### Basic Usage",
        "",
        f"```bash",
        f"# Check {target} help",
        f"{target} --help",
        f"```",
        "",
    ])

    # Help output if available
    if software_info["help_output"]:
        lines.extend([
            "---",
            "",
            "## Available Commands",
            "",
            "```",
            software_info["help_output"][:1500],
            "```",
            "",
        ])

    # Platform-specific notes
    lines.extend([
        "---",
        "",
        "## Platform-Specific Notes",
        "",
    ])

    if env_info:
        os_info = env_info.get("os", {})
        system = os_info.get("system", "").lower()

        if system == "darwin":
            lines.extend([
                "### macOS",
                "",
                "- Configuration files are typically in `~/.config/` or `~/Library/`",
                "- Use `brew upgrade` to update the package",
                "- Use `brew info` to see package details",
                "",
            ])
        elif system == "linux":
            distro = os_info.get("distro_id", "linux")
            pm = env_info.get("summary", {}).get("primary_package_manager", "")

            lines.append(f"### {distro.title()}")
            lines.append("")

            if pm == "apt":
                lines.extend([
                    "- Use `sudo apt update && sudo apt upgrade` to update packages",
                    f"- Configuration files may be in `/etc/{target}/` or `~/.config/{target}/`",
                    f"- Use `apt show {target}` for package information",
                ])
            elif pm in ["dnf", "yum"]:
                lines.extend([
                    f"- Use `sudo {pm} update` to update packages",
                    f"- Configuration files may be in `/etc/{target}/`",
                ])
            lines.append("")

        elif system == "windows":
            lines.extend([
                "### Windows",
                "",
                "- Configuration files may be in `%APPDATA%` or `%LOCALAPPDATA%`",
                "- Use `winget upgrade` to update packages",
                "- Run commands in PowerShell or Command Prompt as Administrator if needed",
                "",
            ])

    # Troubleshooting section
    lines.extend([
        "---",
        "",
        "## Troubleshooting",
        "",
        "### Common Issues",
        "",
        f"**Command not found:** Ensure `{target}` is in your PATH. You may need to:",
        "- Restart your terminal/shell",
        "- Source your profile: `source ~/.bashrc` or `source ~/.zshrc`",
        "- Add the installation directory to your PATH",
        "",
        "**Permission denied:** Try running with elevated privileges:",
        "- Linux/macOS: `sudo <command>`",
        "- Windows: Run as Administrator",
        "",
        "**Package not working correctly:** Try reinstalling:",
    ])

    if plan:
        pm = plan.get("package_manager", "")
        if pm == "brew":
            lines.append(f"```bash")
            lines.append(f"brew reinstall {target}")
            lines.append(f"```")
        elif pm == "apt":
            lines.append(f"```bash")
            lines.append(f"sudo apt remove {target} && sudo apt install {target}")
            lines.append(f"```")

    lines.append("")

    # Uninstallation section
    lines.extend([
        "---",
        "",
        "## Uninstallation",
        "",
        f"To remove {target}:",
        "",
    ])

    if plan:
        pm = plan.get("package_manager", "")
        uninstall_cmds = {
            "brew": f"brew uninstall {target}",
            "apt": f"sudo apt remove {target}",
            "dnf": f"sudo dnf remove {target}",
            "yum": f"sudo yum remove {target}",
            "pacman": f"sudo pacman -R {target}",
            "winget": f"winget uninstall {target}",
            "choco": f"choco uninstall {target}",
        }
        if pm in uninstall_cmds:
            lines.append("```bash")
            lines.append(uninstall_cmds[pm])
            lines.append("```")
    else:
        lines.append("```bash")
        lines.append(f"# Use your package manager to remove {target}")
        lines.append("```")

    lines.extend([
        "",
        "---",
        "",
        "## Additional Resources",
        "",
        f"- Official documentation: Search for \"{target} documentation\"",
        f"- Community forums: Search for \"{target} forum\" or \"{target} community\"",
        f"- Issue tracker: Search for \"{target} github\" or \"{target} issues\"",
        "",
        "---",
        "",
        "*This guide was automatically generated. Some commands may need adjustment for your specific setup.*",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate usage documentation")
    parser.add_argument("--target", required=True, help="Target software name")
    parser.add_argument("--plan", default="installation_plan.yaml", help="Installation plan file")
    parser.add_argument("--env-file", default="env_info.json", help="Environment info file")
    parser.add_argument("--report", default="install_report.md", help="Installation report file")
    parser.add_argument("--output", default="USAGE_GUIDE.md", help="Output documentation file")

    args = parser.parse_args()

    # Load files if they exist
    plan = None
    env_info = None
    report = None

    plan_file = Path(args.plan)
    if plan_file.exists():
        with open(plan_file) as f:
            plan = yaml_load(f.read())

    env_file = Path(args.env_file)
    if env_file.exists():
        with open(env_file) as f:
            env_info = json.load(f)

    # Generate documentation
    doc = generate_usage_guide(args.target, plan, env_info, report)

    # Write output
    output_file = Path(args.output)
    with open(output_file, "w") as f:
        f.write(doc)

    print(f"Usage guide saved to: {output_file}", file=sys.stderr)
    print(doc)

    return 0


if __name__ == "__main__":
    sys.exit(main())
