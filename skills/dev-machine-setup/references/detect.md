# Detect OS, arch, and existing tools

Run this first. Do not install anything until the JSON is in hand.

## Preferred

From the skill directory (or any clone of this skill):

```bash
python3 "$HOME/.claude/skills/dev-machine-setup/scripts/detect_env.py"
```

`~/.claude/skills/dev-machine-setup/` is the default install path. If this skill lives somewhere else
(plugin bundle, repo checkout), resolve that directory **once** and present the block with the real absolute
path already substituted — never a relative path and never a `<placeholder>`, per `references/approvals.md` § Presenting
commands.

On Windows PowerShell, if `python3` is missing:

```powershell
py -3 "$HOME\.claude\skills\dev-machine-setup\scripts\detect_env.py"
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
| `tools` | `{name: version_or_null}` for git, node, npm, python3, pip, uv, zsh, starship, claude, codex, pi, opencode |
| `shell` | login shell, whether Oh My Zsh is installed, and `starship_config`: `managed` (the skill's `assets/starship.toml`, identified by its first-line marker) · `foreign` (a distro or hand-rolled toml) · `absent` |
| `node_managers` | nvm / volta / asdf / fnm / n, found by directory (nvm is a shell function, not a binary) |
| `missing.baseline` | baseline tools with no version — **the install list for phase 3** |
| `missing.agents` | agent CLIs with no version — **the install list for phase 4** |
| `findings` | `{id, severity, area, detail, fix_ref}` — **the tune list for phase 5** |
| `notes` | `wsl:<distro>`, `container`, `remote-ssh` |

`missing` and `findings` are what make the run gap-driven: an empty `missing.baseline` means phase 3
has nothing to do and self-skips. `findings` is sorted high → medium → low; each `fix_ref` points at a
heading in `optimize.md`.

The script never writes, never reaches the network, and exits 0 even when probes fail — a probe that
errors contributes nothing rather than aborting the report.

## Routing

- `os=windows` → read `references/windows.md`
- `os=macos` → read `references/macos.md`
- `os=linux` → read `references/linux.md`
- Then `references/agent-clis.md` (phase 4) and `references/optimize.md` (phase 5, one section per finding id)

Apple Silicon is `arm64`. Windows on Snapdragon is `ARM64` / `arm64`. Prefer native packages; mention
x64-emulation only when a tool has no arm64 build.
