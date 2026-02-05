#!/usr/bin/env python3
"""
Installation Plan Generator - Creates a platform-specific installation plan.
Reads environment info and generates a YAML plan with verification steps.
"""

import argparse
import json
import sys
from pathlib import Path

# Try to use PyYAML if available, otherwise use simple YAML output
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def simple_yaml_dump(data, indent=0):
    """Simple YAML serializer for when PyYAML is not available."""
    lines = []
    prefix = "  " * indent

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{prefix}{key}:")
                lines.append(simple_yaml_dump(value, indent + 1))
            elif value is None:
                lines.append(f"{prefix}{key}: null")
            elif isinstance(value, bool):
                lines.append(f"{prefix}{key}: {'true' if value else 'false'}")
            elif isinstance(value, str) and ('\n' in value or ':' in value or '"' in value):
                lines.append(f'{prefix}{key}: "{value}"')
            else:
                lines.append(f"{prefix}{key}: {value}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                first = True
                for key, value in item.items():
                    if first:
                        lines.append(f"{prefix}- {key}:")
                        first = False
                    else:
                        lines.append(f"{prefix}  {key}:")
                    if isinstance(value, (dict, list)):
                        lines.append(simple_yaml_dump(value, indent + 2))
                    elif value is None:
                        lines[-1] = f"{lines[-1]} null"
                    elif isinstance(value, str) and ('\n' in value or ':' in value):
                        lines[-1] = f'{lines[-1]} "{value}"'
                    else:
                        lines[-1] = f"{lines[-1]} {value}"
            else:
                lines.append(f"{prefix}- {item}")

    return "\n".join(lines)


def yaml_dump(data):
    """Dump data to YAML format."""
    if HAS_YAML:
        return yaml.dump(data, default_flow_style=False, sort_keys=False)
    else:
        return simple_yaml_dump(data)


def get_install_commands(target, env_info):
    """Generate platform-specific installation commands."""
    os_info = env_info.get("os", {})
    system = os_info.get("system", "").lower()
    pm = env_info.get("summary", {}).get("primary_package_manager")

    # Common software installation patterns
    # This is a template - Claude will customize based on actual target
    commands = {
        "darwin": {
            "brew": {
                "install": f"brew install {target}",
                "verify": f"brew list {target}",
                "rollback": f"brew uninstall {target}",
            }
        },
        "linux": {
            "apt": {
                "pre": "sudo apt-get update",
                "install": f"sudo apt-get install -y {target}",
                "verify": f"dpkg -l | grep {target}",
                "rollback": f"sudo apt-get remove -y {target}",
            },
            "dnf": {
                "install": f"sudo dnf install -y {target}",
                "verify": f"rpm -q {target}",
                "rollback": f"sudo dnf remove -y {target}",
            },
            "yum": {
                "install": f"sudo yum install -y {target}",
                "verify": f"rpm -q {target}",
                "rollback": f"sudo yum remove -y {target}",
            },
            "pacman": {
                "install": f"sudo pacman -S --noconfirm {target}",
                "verify": f"pacman -Q {target}",
                "rollback": f"sudo pacman -R --noconfirm {target}",
            },
        },
        "windows": {
            "winget": {
                "install": f"winget install --id {target} --accept-source-agreements --accept-package-agreements",
                "verify": f"winget list --id {target}",
                "rollback": f"winget uninstall --id {target}",
            },
            "choco": {
                "install": f"choco install {target} -y",
                "verify": f"choco list --local-only | findstr {target}",
                "rollback": f"choco uninstall {target} -y",
            },
        }
    }

    if system in commands and pm in commands[system]:
        return commands[system][pm]

    return None


def generate_plan(target, env_info, dependencies=None):
    """Generate installation plan for the target software."""
    os_info = env_info.get("os", {})
    system = os_info.get("system", "").lower()
    summary = env_info.get("summary", {})
    pm = summary.get("primary_package_manager")
    has_sudo = summary.get("has_sudo", False)

    plan = {
        "target": target,
        "platform": summary.get("platform", system),
        "architecture": summary.get("architecture", "unknown"),
        "package_manager": pm,
        "generated_at": env_info.get("timestamp", "unknown"),
        "requires_elevation": system != "darwin" and not env_info.get("permissions", {}).get("is_root", False),
        "steps": []
    }

    step_num = 0

    # Step: Check package manager
    if pm:
        step_num += 1
        plan["steps"].append({
            "step": step_num,
            "name": f"Verify {pm} is available",
            "command": get_pm_version_command(pm),
            "verify": get_pm_version_command(pm),
            "rollback": None,
            "critical": True,
        })

    # Step: Update package index (for apt-based systems)
    if pm in ["apt", "apt-get"]:
        step_num += 1
        plan["steps"].append({
            "step": step_num,
            "name": "Update package index",
            "command": "sudo apt-get update",
            "verify": "echo 'Package index updated'",
            "rollback": None,
            "critical": False,
        })

    # Step: Install dependencies
    if dependencies:
        for dep in dependencies:
            step_num += 1
            cmds = get_install_commands(dep, env_info)
            if cmds:
                plan["steps"].append({
                    "step": step_num,
                    "name": f"Install dependency: {dep}",
                    "command": cmds.get("install"),
                    "verify": cmds.get("verify"),
                    "rollback": cmds.get("rollback"),
                    "critical": True,
                })

    # Step: Install main target
    step_num += 1
    cmds = get_install_commands(target, env_info)
    if cmds:
        plan["steps"].append({
            "step": step_num,
            "name": f"Install {target}",
            "command": cmds.get("install"),
            "verify": cmds.get("verify"),
            "rollback": cmds.get("rollback"),
            "critical": True,
        })
    else:
        # Generic installation step - Claude will customize
        plan["steps"].append({
            "step": step_num,
            "name": f"Install {target}",
            "command": f"# TODO: Add installation command for {target}",
            "verify": f"# TODO: Add verification command for {target}",
            "rollback": f"# TODO: Add rollback command for {target}",
            "critical": True,
        })

    # Step: Verify installation
    step_num += 1
    plan["steps"].append({
        "step": step_num,
        "name": f"Verify {target} installation",
        "command": f"which {target} || command -v {target} || where {target}",
        "verify": f"{target} --version || {target} -v || {target} version",
        "rollback": None,
        "critical": True,
    })

    return plan


def get_pm_version_command(pm):
    """Get version check command for package manager."""
    commands = {
        "brew": "brew --version",
        "apt": "apt --version",
        "apt-get": "apt-get --version",
        "dnf": "dnf --version",
        "yum": "yum --version",
        "pacman": "pacman --version",
        "winget": "winget --version",
        "choco": "choco --version",
        "scoop": "scoop --version",
    }
    return commands.get(pm, f"{pm} --version")


def main():
    parser = argparse.ArgumentParser(description="Generate installation plan")
    parser.add_argument("--target", required=True, help="Target software to install")
    parser.add_argument("--env-file", default="env_info.json", help="Environment info JSON file")
    parser.add_argument("--output", default="installation_plan.yaml", help="Output plan file")
    parser.add_argument("--deps", nargs="*", help="Dependencies to install first")

    args = parser.parse_args()

    # Load environment info
    env_file = Path(args.env_file)
    if not env_file.exists():
        print(f"Error: Environment file not found: {env_file}", file=sys.stderr)
        print("Run env_explorer.py first to generate environment info.", file=sys.stderr)
        return 1

    with open(env_file) as f:
        env_info = json.load(f)

    # Generate plan
    plan = generate_plan(args.target, env_info, args.deps)

    # Write plan
    output_file = Path(args.output)
    with open(output_file, "w") as f:
        f.write(yaml_dump(plan))

    print(f"Installation plan saved to: {output_file}", file=sys.stderr)
    print(yaml_dump(plan))

    return 0


if __name__ == "__main__":
    sys.exit(main())
