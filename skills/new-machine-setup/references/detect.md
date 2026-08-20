# Detect OS, arch, and existing tools

Run this first. Do not install anything until the JSON is in hand.

## Preferred

From the skill directory (or any clone of this skill):

```bash
python3 scripts/detect_env.py
```

On Windows PowerShell, if `python3` is missing:

```powershell
py -3 scripts/detect_env.py
```

## Fallback one-liners

**Unix**

```bash
uname -s; uname -m
command -v apt-get dnf pacman brew git node python3 zsh
```

**Windows**

```powershell
[System.Environment]::OSVersion.VersionString
$env:PROCESSOR_ARCHITECTURE
Get-Command winget, git, node, python, py -ErrorAction SilentlyContinue
```

## How to read the JSON

| Field | Meaning |
|-------|---------|
| `os` | `macos` / `linux` / `windows` / `unknown` |
| `arch` | `x86_64` / `arm64` / raw uname |
| `distro` | Linux ID from `/etc/os-release` (ubuntu, fedora, arch, …) |
| `package_managers` | present managers (`apt`, `dnf`, `pacman`, `brew`, `winget`, `choco`, `scoop`) |
| `tools` | `{name: version_or_null}` for git, node, npm, python3, pip, uv, zsh, claude, codex, pi, opencode |
| `notes` | WSL, Rosetta, missing sudo |

## Routing

- `os=windows` → read `references/windows.md`
- `os=macos` → read `references/macos.md`
- `os=linux` → read `references/linux.md`
- Then `references/agent-clis.md` for step 4

Apple Silicon is `arm64`. Windows on Snapdragon is `ARM64` / `arm64`. Prefer native packages; mention x64-emulation only when a tool has no arm64 build.
