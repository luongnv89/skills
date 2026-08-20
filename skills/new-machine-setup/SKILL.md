---
name: new-machine-setup
description: "Set up a clean, ready-to-develop machine across macOS, Linux, and Windows with OS/arch detection. Use when the user bought a new laptop, wants a fresh dev box, asks to bootstrap Node/Python, install Claude Code, Codex, Pi, OpenCode, or Oh My Zsh, or mentions OEM bloat / Grok Build-style cleanup. Don't use for Dockerfiles, CI images, or one-off package installs."
license: MIT
compatibility: "macOS, Linux (Debian/Ubuntu/Fedora/Arch), Windows (winget/PowerShell). Needs network and a package manager or permission to install one. Never run destructive uninstalls without an explicit yes."
metadata:
  version: 0.1.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
  effort: high
---

# New Machine Setup

Turn a factory laptop into a **clean, ready-to-develop** machine. Detect OS + CPU arch first, optionally inventory/remove OEM junk (the XFreeze / Grok Build idea), then install a consistent baseline: git, shell, Node.js, Python, and the coding-agent CLIs this user actually uses.

This skill is an orchestrator. Long per-OS command tables live in `references/` so only the current platform is loaded.

**Do not** pipe remote scripts to a shell until the user has approved that step. Prefer official installers and the user's own [inbash](https://github.com/luongnv89/inbash) scripts when they match the OS.

## When to Use

- "set up this new laptop / new machine / fresh install"
- "install my dev environment" (Node, Python, agents)
- Windows OEM bloat, trial antivirus, preinstalled games
- Need Claude Code, Codex, Pi, OpenCode, and Oh My Zsh on a clean box

Don't use for: Dockerfiles, CI runners, or installing a single package.

## Prerequisites

- Network.
- Admin/sudo (or winget) for system packages.
- User confirmation before: removing apps, changing the default shell, or `curl | sh` installers.
- Optional clone of `https://github.com/luongnv89/inbash` — preferred source for Unix/mac scripts this user already maintains.

## Reference files (load only what you need)

| File | When |
|------|------|
| `references/detect.md` | Always first — how to probe OS/arch and interpret `scripts/detect_env.py` |
| `references/windows.md` | Windows: inventory, conservative debloat, winget stack |
| `references/macos.md` | macOS: Homebrew, Node, Python+uv, zsh |
| `references/linux.md` | Linux: apt/dnf/pacman, NodeSource LTS, python3-pip |
| `references/agent-clis.md` | Claude Code, Codex, Pi, OpenCode install + verify |
| `scripts/detect_env.py` | Print a JSON inventory (OS, arch, package managers, tools) |

## Procedure

### 1. Detect the machine

Run:

```bash
python3 scripts/detect_env.py
```

If `python3` is missing, use the one-liners in `references/detect.md`.

**Done when:** you have `os` (`macos` | `linux` | `windows`), `arch` (`x86_64` | `arm64` | other), package manager, and which of `{git,node,npm,python3,zsh,brew,winget}` already exist.

Then read **only** the matching OS reference (`windows.md` / `macos.md` / `linux.md`).

### 2. Inventory (Windows first; useful everywhere)

Inspired by [XFreeze](https://x.com/xfreeze/status/2090189407659999603): factory Windows boxes ship trial AV, OEM utilities, and partner games. **List before delete.**

On Windows, follow `references/windows.md` § Inventory. On macOS/Linux, list unexpected GUI apps and leftover vendor agents, but do not uninstall by default.

Present a short table: keep / review / remove-candidate. Wait for an explicit yes on every removal.

**Done when:** the user has seen the inventory. Removals are either skipped or confirmed one-by-one.

### 3. Baseline toolchain

Install missing pieces only (idempotent):

| Layer | Purpose |
|-------|---------|
| Package manager | Homebrew (mac), winget (Windows), distro pkg (Linux) |
| CLI baseline | git, curl, wget, vim/editor — inbash `unix/basic.sh` on Debian |
| Shell | zsh + Oh My Zsh + inbash `setup-ohMyZsh.sh` (mac/linux). Windows: keep PowerShell; optional WSL2 + same Unix path |
| Node.js LTS | inbash `unix/nodejs.sh` / `mac/nodejs.sh`; Windows: `winget install OpenJS.NodeJS.LTS` |
| Python | mac: inbash `mac/python-pip-uv.sh` (Homebrew python + **uv**). Linux: `unix/python3-pip.sh` then install **uv**. Windows: `winget install Python.Python.3.12` + uv |

Prefer **LTS Node** and a **venv/uv** workflow. Do not overwrite a working Node/Python without asking.

**Done when:** `git --version`, `node -v`, `npm -v`, `python3 --version` succeed for the target OS.

### 4. Coding-agent CLIs

Read `references/agent-clis.md` and install, in this order (Node is already on PATH):

1. Claude Code
2. Codex
3. Pi (`@mariozechner/pi-coding-agent`)
4. OpenCode

Skip any the user already has. Do not store API keys in the skill or in shell history snippets.

**Done when:** each requested CLI prints a version (`claude --version`, `codex --version`, `pi --version`, `opencode --version`).

### 5. Ready-to-develop check

Print a verification report (see below). Offer optional extras from inbash only if asked: Docker, C/C++, SSH server, MongoDB.

**Done when:** the report is shown and gaps are either fixed or explicitly deferred.

## Safety

- Never run a third-party "debloat everything" script unattended. OEM audio/chipset tools can be load-bearing.
- Never `curl | bash` without naming the URL and getting a yes.
- Never commit secrets. Auth for Claude/Codex is interactive login after install.
- Windows ARM64 (Snapdragon / Copilot+): prefer arm64 winget packages; say so when a tool is x64-only.

## Verification report

Always print:

```
◆ New machine setup
  OS / arch:          …
  Package manager:    …
  Inventory:          √ listed (N removal candidates, K removed)
  git / curl:         √ / ×
  Node LTS + npm:     √ version …
  Python + uv:        √ version …
  zsh + Oh My Zsh:    √ / skipped (Windows host)
  Claude Code:        √ / skipped
  Codex:              √ / skipped
  Pi:                 √ / skipped
  OpenCode:           √ / skipped
  Result:             READY | PARTIAL | BLOCKED
```

`READY` = baseline + Node + Python work. Agents may be skipped and still READY if the user declined them.

## Pitfalls

- **PEP 668 on Linux:** do not `pip install` into the system Python. Use `uv` or a venv.
- **Node via both nvm and apt/brew:** pick one; prefer the inbash path unless nvm is already in use.
- **Oh My Zsh `chsh`:** needs a login session; don't fail the whole setup if `chsh` is denied.
- **WSL vs native Windows:** if the user wants Linux-native agents, set up WSL2 Ubuntu and re-run this skill *inside* WSL rather than mixing paths.
- **inbash scripts are Debian/mac-oriented.** On Fedora/Arch, follow `references/linux.md` package-manager switches, not the `.sh` files blindly.
