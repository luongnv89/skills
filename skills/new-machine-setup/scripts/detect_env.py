#!/usr/bin/env python3
"""Print a JSON inventory of OS, CPU arch, package managers, and dev tools.

No third-party deps. Safe to run on a factory machine.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys


def _run(cmd: list[str]) -> str | None:
    try:
        out = subprocess.run(
            cmd, check=False, capture_output=True, text=True, timeout=8
        )
        if out.returncode != 0:
            return None
        return (out.stdout or "").strip() or None
    except (OSError, subprocess.TimeoutExpired):
        return None


def detect_os() -> str:
    sysname = platform.system().lower()
    if sysname == "darwin":
        return "macos"
    if sysname == "windows":
        return "windows"
    if sysname == "linux":
        return "linux"
    return "unknown"


def detect_arch() -> str:
    machine = (platform.machine() or "").lower()
    if machine in {"x86_64", "amd64"}:
        return "x86_64"
    if machine in {"arm64", "aarch64"}:
        return "arm64"
    return machine or "unknown"


def detect_distro() -> str | None:
    path = "/etc/os-release"
    if not os.path.isfile(path):
        return None
    data: dict[str, str] = {}
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if "=" not in line or line.startswith("#"):
                    continue
                key, val = line.rstrip().split("=", 1)
                data[key] = val.strip().strip('"')
    except OSError:
        return None
    return data.get("ID")


def managers() -> list[str]:
    names = ("apt-get", "dnf", "yum", "pacman", "zypper", "apk", "brew", "winget", "choco", "scoop")
    found = []
    for name in names:
        if shutil.which(name):
            found.append("apt" if name == "apt-get" else name)
    return found


def tool_version(names: list[str], args: list[str] | None = None) -> str | None:
    args = args or ["--version"]
    for name in names:
        path = shutil.which(name)
        if not path:
            continue
        ver = _run([path, *args])
        if ver:
            return ver.splitlines()[0][:120]
        return "present"
    return None


def notes(os_name: str) -> list[str]:
    out: list[str] = []
    if os_name == "linux" and os.environ.get("WSL_DISTRO_NAME"):
        out.append(f"wsl:{os.environ['WSL_DISTRO_NAME']}")
    if os_name == "macos" and platform.machine().lower() == "arm64":
        if os.path.isdir("/usr/local/Homebrew") and not os.path.isdir("/opt/homebrew"):
            out.append("intel-homebrew-on-apple-silicon")
    if os_name != "windows" and os.geteuid() != 0 and not shutil.which("sudo"):
        out.append("no-sudo")
    return out


def main() -> int:
    os_name = detect_os()
    payload = {
        "os": os_name,
        "arch": detect_arch(),
        "distro": detect_distro(),
        "package_managers": managers(),
        "tools": {
            "git": tool_version(["git"], ["--version"]),
            "node": tool_version(["node"], ["-v"]),
            "npm": tool_version(["npm"], ["-v"]),
            "python3": tool_version(["python3", "python", "py"], ["--version"]),
            "pip": tool_version(["pip3", "pip"], ["--version"]),
            "uv": tool_version(["uv"], ["--version"]),
            "zsh": tool_version(["zsh"], ["--version"]),
            "claude": tool_version(["claude"], ["--version"]),
            "codex": tool_version(["codex"], ["--version"]),
            "pi": tool_version(["pi"], ["--version"]),
            "opencode": tool_version(["opencode"], ["--version"]),
        },
        "notes": notes(os_name),
    }
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
