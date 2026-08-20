#!/usr/bin/env python3
"""Print a JSON inventory + gap report for the current machine.

Read-only. No third-party deps. Safe on a factory machine and on a machine
that is already someone's daily driver.

Output keys:
  os, arch, distro, package_managers, tools, shell  -> what is here
  missing {baseline, agents}                        -> what to install
  findings [{id, severity, area, detail, fix_ref}]  -> what to tune
  notes                                             -> free-form flags

Every probe is fail-soft: a probe that errors contributes nothing rather than
crashing the report.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys

# --- Manually bumped floors -------------------------------------------------
# These two constants are the only version facts in this file. They rot; bump
# them by hand when the oldest maintained release moves. Everything else is
# computed from the machine.
NODE_MIN_MAJOR = 20  # oldest Node LTS still receiving security fixes
PYTHON_MIN_MINOR = 10  # oldest CPython 3.x still receiving security fixes

BASELINE_UNIX = ("git", "node", "npm", "python3", "uv", "zsh")
BASELINE_WINDOWS = ("git", "node", "npm", "python3", "uv")
AGENTS = ("claude", "codex", "pi", "opencode")


def _run(cmd: list[str]) -> str | None:
    try:
        out = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=8)
        if out.returncode != 0:
            return None
        return (out.stdout or "").strip() or None
    except (OSError, subprocess.TimeoutExpired):
        return None


def _home(*parts: str) -> str:
    return os.path.join(os.path.expanduser("~"), *parts)


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
    names = (
        "apt-get", "dnf", "yum", "pacman", "zypper", "apk",
        "brew", "winget", "choco", "scoop",
    )
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


def _first_int(text: str | None) -> int | None:
    """Pull the first integer out of a version string ('v22.11.0' -> 22)."""
    if not text:
        return None
    digits = ""
    for ch in text:
        if ch.isdigit():
            digits += ch
        elif digits:
            break
    return int(digits) if digits else None


def _python_minor(text: str | None) -> int | None:
    """'Python 3.12.4' -> 12."""
    if not text:
        return None
    parts = [p for p in text.replace("Python", "").strip().split(".") if p]
    if len(parts) < 2:
        return None
    return _first_int(parts[1])


def path_entries() -> list[str]:
    raw = os.environ.get("PATH", "")
    return [p for p in raw.split(os.pathsep) if p]


def _on_path(directory: str) -> bool:
    target = os.path.normcase(os.path.normpath(directory))
    return any(os.path.normcase(os.path.normpath(p)) == target for p in path_entries())


def npm_global_bin() -> str | None:
    """Directory npm puts global CLI shims in, or None if npm is absent."""
    if not shutil.which("npm"):
        return None
    prefix = _run([shutil.which("npm"), "prefix", "-g"])
    if not prefix:
        return None
    prefix = prefix.splitlines()[0].strip()
    if not prefix:
        return None
    # Windows drops shims straight in the prefix; Unix uses <prefix>/bin.
    return prefix if detect_os() == "windows" else os.path.join(prefix, "bin")


def node_managers() -> list[str]:
    """Node version managers, found by directory (nvm is a shell function, not a binary)."""
    found = []
    if os.path.isdir(os.environ.get("NVM_DIR") or _home(".nvm")):
        found.append("nvm")
    if os.path.isdir(_home(".volta")):
        found.append("volta")
    if os.path.isdir(_home(".asdf")):
        found.append("asdf")
    if os.path.isdir(_home(".local", "share", "fnm")) or shutil.which("fnm"):
        found.append("fnm")
    if shutil.which("n"):
        found.append("n")
    return found


def shell_info(os_name: str) -> dict[str, object]:
    login = os.environ.get("SHELL") if os_name != "windows" else os.environ.get("ComSpec")
    return {
        "login_shell": login,
        "oh_my_zsh": os.path.isdir(_home(".oh-my-zsh")),
    }


def externally_managed() -> bool:
    """True when the system Python refuses `pip install` (PEP 668)."""
    try:
        import sysconfig

        stdlib = sysconfig.get_path("stdlib")
    except Exception:
        return False
    if not stdlib:
        return False
    return os.path.isfile(os.path.join(os.path.dirname(stdlib), "EXTERNALLY-MANAGED")) or os.path.isfile(
        os.path.join(stdlib, "EXTERNALLY-MANAGED")
    )


def find(fid: str, severity: str, area: str, detail: str) -> dict[str, str]:
    return {
        "id": fid,
        "severity": severity,
        "area": area,
        "detail": detail,
        "fix_ref": f"references/optimize.md#{fid}",
    }


def findings(os_name: str, arch: str, tools: dict[str, str | None], mgrs: list[str]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []

    if not mgrs:
        brew_prefix = "/opt/homebrew/bin" if os_name == "macos" and arch == "arm64" else (
            "/usr/local/bin" if os_name == "macos" else None)
        brew_installed = brew_prefix is not None and os.path.isfile(os.path.join(brew_prefix, "brew"))
        if not brew_installed and not tools.get("npm"):
            out.append(find("no-package-manager", "high", "packaging",
                            "No package manager found; nothing can be installed until one exists."))

    if tools.get("npm"):
        bindir = npm_global_bin()
        if bindir and not _on_path(bindir):
            out.append(find("npm-global-bin-not-on-path", "high", "path",
                            f"npm global bin '{bindir}' is not on PATH; globally installed CLIs will not resolve."))

    if os_name == "macos":
        brew_bin = "/opt/homebrew/bin" if arch == "arm64" else "/usr/local/bin"
        if os.path.isfile(os.path.join(brew_bin, "brew")) and not _on_path(brew_bin):
            out.append(find("brew-bin-not-on-path", "high", "path",
                            f"Homebrew is installed at {brew_bin} but not on PATH; shellenv line is missing."))
        if arch == "arm64" and os.path.isdir("/usr/local/Homebrew") and not os.path.isdir("/opt/homebrew"):
            out.append(find("intel-homebrew-on-apple-silicon", "medium", "packaging",
                            "Only the x86 Homebrew prefix exists on an arm64 Mac; formulae run under Rosetta."))
        if not _run(["xcode-select", "-p"]):
            out.append(find("xcode-clt-missing", "medium", "toolchain",
                            "Xcode Command Line Tools are absent; native builds and some formulae will fail."))

    sources = list(node_managers())
    if tools.get("node") and _system_node():
        sources.append("system/package-manager node")
    if len(sources) > 1:
        out.append(find("multiple-node-managers", "medium", "runtime",
                        f"More than one Node source present ({', '.join(sources)}); they will fight over PATH."))

    node_major = _first_int((tools.get("node") or "").lstrip("v"))
    if node_major is not None and node_major < NODE_MIN_MAJOR:
        out.append(find("node-below-min", "medium", "runtime",
                        f"Node major {node_major} is below the supported floor ({NODE_MIN_MAJOR}); agent CLIs may refuse to run."))

    py_minor = _python_minor(tools.get("python3"))
    if py_minor is not None and py_minor < PYTHON_MIN_MINOR:
        out.append(find("python-below-min", "medium", "runtime",
                        f"Python 3.{py_minor} is below the supported floor (3.{PYTHON_MIN_MINOR})."))

    if os_name in {"linux", "macos"} and externally_managed() and not tools.get("uv"):
        out.append(find("python-externally-managed", "medium", "runtime",
                        "System Python is PEP 668 externally-managed and uv is absent; pip installs will fail or need --break-system-packages."))

    if tools.get("git"):
        if not _run(["git", "config", "--global", "user.name"]) or not _run(["git", "config", "--global", "user.email"]):
            out.append(find("git-identity-missing", "medium", "vcs",
                            "git global user.name/user.email is unset; commits will be misattributed or rejected."))

    entries = [os.path.normcase(os.path.normpath(p)) for p in path_entries()]
    dupes = len(entries) - len(set(entries))
    if dupes:
        out.append(find("path-duplicates", "low", "path",
                        f"PATH has {dupes} duplicate entr{'y' if dupes == 1 else 'ies'}; shell startup re-sources a profile."))

    if os_name != "windows" and tools.get("zsh"):
        shell = os.environ.get("SHELL") or ""
        if shell and not shell.endswith("zsh"):
            out.append(find("login-shell-not-zsh", "low", "shell",
                            f"zsh is installed but the login shell is '{shell}'."))
        if not os.path.isdir(_home(".oh-my-zsh")):
            out.append(find("oh-my-zsh-missing", "low", "shell",
                            "zsh is installed without Oh My Zsh; no plugin/completion baseline."))

    if os_name != "windows" and getattr(os, "geteuid", lambda: 0)() != 0 and not shutil.which("sudo"):
        out.append(find("no-sudo", "medium", "packaging",
                        "Not root and sudo is absent; system-wide installs will fail."))

    order = {"high": 0, "medium": 1, "low": 2}
    out.sort(key=lambda f: order.get(f["severity"], 3))
    return out


def _system_node() -> bool:
    """True when Node resolves from a system/package-manager prefix rather than a version manager."""
    node = shutil.which("node")
    if not node:
        return False
    real = os.path.realpath(node)
    vm_roots = (_home(".nvm"), _home(".volta"), _home(".asdf"), _home(".local", "share", "fnm"), _home(".fnm"))
    return not any(real.startswith(root) for root in vm_roots)


def notes(os_name: str) -> list[str]:
    out: list[str] = []
    if os_name == "linux" and os.environ.get("WSL_DISTRO_NAME"):
        out.append(f"wsl:{os.environ['WSL_DISTRO_NAME']}")
    if os.path.exists("/.dockerenv"):
        out.append("container")
    if os.environ.get("SSH_CONNECTION"):
        out.append("remote-ssh")
    return out


def main() -> int:
    os_name = detect_os()
    arch = detect_arch()
    tools = {
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
    }
    mgrs = managers()
    baseline = BASELINE_WINDOWS if os_name == "windows" else BASELINE_UNIX

    payload = {
        "os": os_name,
        "arch": arch,
        "distro": detect_distro(),
        "package_managers": mgrs,
        "tools": tools,
        "shell": shell_info(os_name),
        "node_managers": node_managers(),
        "missing": {
            "baseline": [t for t in baseline if not tools.get(t)],
            "agents": [t for t in AGENTS if not tools.get(t)],
        },
        "findings": findings(os_name, arch, tools, mgrs),
        "notes": notes(os_name),
    }
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
