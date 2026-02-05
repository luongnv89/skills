#!/usr/bin/env python3
"""
Environment Explorer - Detects system information for cross-platform installations.
Outputs a JSON file with comprehensive system details.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_command(cmd, shell=False):
    """Run a command and return output, or None on failure."""
    try:
        result = subprocess.run(
            cmd if isinstance(cmd, list) else cmd,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def detect_os():
    """Detect operating system details."""
    system = platform.system().lower()
    info = {
        "system": system,
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }

    if system == "darwin":
        info["friendly_name"] = "macOS"
        mac_ver = platform.mac_ver()
        info["mac_version"] = mac_ver[0]
        # Detect if Apple Silicon
        info["is_apple_silicon"] = platform.machine() == "arm64"
    elif system == "linux":
        info["friendly_name"] = "Linux"
        # Try to get distro info
        if Path("/etc/os-release").exists():
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("ID="):
                        info["distro_id"] = line.split("=")[1].strip().strip('"')
                    elif line.startswith("ID_LIKE="):
                        info["distro_family"] = line.split("=")[1].strip().strip('"')
                    elif line.startswith("VERSION_ID="):
                        info["distro_version"] = line.split("=")[1].strip().strip('"')
                    elif line.startswith("PRETTY_NAME="):
                        info["distro_name"] = line.split("=", 1)[1].strip().strip('"')
    elif system == "windows":
        info["friendly_name"] = "Windows"
        info["windows_edition"] = platform.win32_edition() if hasattr(platform, 'win32_edition') else "Unknown"

    return info


def detect_package_managers():
    """Detect available package managers."""
    managers = {}

    # Universal package managers
    checks = {
        "pip": ["pip", "--version"],
        "pip3": ["pip3", "--version"],
        "npm": ["npm", "--version"],
        "cargo": ["cargo", "--version"],
        "go": ["go", "version"],
    }

    # OS-specific package managers
    system = platform.system().lower()

    if system == "darwin":
        checks.update({
            "brew": ["brew", "--version"],
            "port": ["port", "version"],
        })
    elif system == "linux":
        checks.update({
            "apt": ["apt", "--version"],
            "apt-get": ["apt-get", "--version"],
            "yum": ["yum", "--version"],
            "dnf": ["dnf", "--version"],
            "pacman": ["pacman", "--version"],
            "zypper": ["zypper", "--version"],
            "snap": ["snap", "--version"],
            "flatpak": ["flatpak", "--version"],
        })
    elif system == "windows":
        checks.update({
            "winget": ["winget", "--version"],
            "choco": ["choco", "--version"],
            "scoop": ["scoop", "--version"],
        })

    for name, cmd in checks.items():
        version = run_command(cmd)
        if version:
            # Extract just the version number
            managers[name] = {
                "available": True,
                "version": version.split("\n")[0]
            }

    return managers


def detect_shell():
    """Detect the current shell environment."""
    system = platform.system().lower()
    shell_info = {
        "current": os.environ.get("SHELL", "unknown"),
    }

    if system == "windows":
        # Check for PowerShell
        ps_version = run_command(["powershell", "-Command", "$PSVersionTable.PSVersion.ToString()"])
        if ps_version:
            shell_info["powershell"] = ps_version

        # Check for cmd
        shell_info["cmd_available"] = shutil.which("cmd") is not None
    else:
        # Check common shells
        for shell in ["bash", "zsh", "fish", "sh"]:
            path = shutil.which(shell)
            if path:
                version = run_command([shell, "--version"])
                shell_info[shell] = {
                    "path": path,
                    "version": version.split("\n")[0] if version else "unknown"
                }

    return shell_info


def detect_permissions():
    """Detect user permission level."""
    system = platform.system().lower()
    perms = {
        "user": os.environ.get("USER", os.environ.get("USERNAME", "unknown")),
    }

    if system == "windows":
        # Check for admin rights
        try:
            import ctypes
            perms["is_admin"] = ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            perms["is_admin"] = False
    else:
        perms["uid"] = os.getuid()
        perms["is_root"] = os.getuid() == 0
        # Check sudo availability
        perms["sudo_available"] = shutil.which("sudo") is not None
        if perms["sudo_available"] and not perms["is_root"]:
            # Check if user can sudo without password (for automated scripts)
            sudo_check = run_command(["sudo", "-n", "true"])
            perms["sudo_nopasswd"] = sudo_check is not None

    return perms


def detect_common_tools():
    """Detect common development tools."""
    tools = {}

    tool_checks = {
        "git": ["git", "--version"],
        "curl": ["curl", "--version"],
        "wget": ["wget", "--version"],
        "python": ["python", "--version"],
        "python3": ["python3", "--version"],
        "node": ["node", "--version"],
        "java": ["java", "-version"],
        "docker": ["docker", "--version"],
        "make": ["make", "--version"],
        "cmake": ["cmake", "--version"],
        "gcc": ["gcc", "--version"],
        "clang": ["clang", "--version"],
    }

    for name, cmd in tool_checks.items():
        version = run_command(cmd)
        if version:
            tools[name] = version.split("\n")[0]

    return tools


def detect_paths():
    """Detect important system paths."""
    system = platform.system().lower()
    paths = {
        "home": str(Path.home()),
        "cwd": os.getcwd(),
        "path_dirs": os.environ.get("PATH", "").split(os.pathsep),
    }

    if system == "darwin":
        paths["applications"] = "/Applications"
        paths["local_bin"] = "/usr/local/bin"
        paths["homebrew"] = "/opt/homebrew" if platform.machine() == "arm64" else "/usr/local"
    elif system == "linux":
        paths["local_bin"] = "/usr/local/bin"
        paths["opt"] = "/opt"
    elif system == "windows":
        paths["program_files"] = os.environ.get("ProgramFiles", "C:\\Program Files")
        paths["appdata"] = os.environ.get("APPDATA", "")
        paths["localappdata"] = os.environ.get("LOCALAPPDATA", "")

    return paths


def main():
    """Main function to gather all environment info."""
    print("Exploring environment...", file=sys.stderr)

    env_info = {
        "timestamp": datetime.now().isoformat(),
        "os": detect_os(),
        "package_managers": detect_package_managers(),
        "shell": detect_shell(),
        "permissions": detect_permissions(),
        "tools": detect_common_tools(),
        "paths": detect_paths(),
    }

    # Add summary
    os_info = env_info["os"]
    pm = env_info["package_managers"]

    # Determine primary package manager
    primary_pm = None
    if os_info["system"] == "darwin":
        primary_pm = "brew" if "brew" in pm else None
    elif os_info["system"] == "linux":
        for mgr in ["apt", "dnf", "yum", "pacman", "zypper"]:
            if mgr in pm:
                primary_pm = mgr
                break
    elif os_info["system"] == "windows":
        primary_pm = "winget" if "winget" in pm else ("choco" if "choco" in pm else None)

    env_info["summary"] = {
        "platform": os_info.get("friendly_name", os_info["system"]),
        "architecture": os_info["machine"],
        "primary_package_manager": primary_pm,
        "has_sudo": env_info["permissions"].get("sudo_available", False) or env_info["permissions"].get("is_admin", False),
    }

    # Output to file
    output_file = Path("env_info.json")
    with open(output_file, "w") as f:
        json.dump(env_info, f, indent=2)

    print(f"Environment info saved to: {output_file}", file=sys.stderr)
    print(json.dumps(env_info, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
