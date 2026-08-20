---
name: new-machine-setup
description: "Set up a clean, ready-to-develop machine on macOS, Linux, or Windows: OS/arch detection, Node/Python bootstrap, Claude Code, Codex, Pi, or OpenCode installs with per-phase approval. Don't use for Dockerfiles, CI images, or one-off package installs."
license: MIT
compatibility: "macOS, Linux (Debian/Ubuntu/Fedora/Arch), Windows (winget/PowerShell). Needs network and a package manager or permission to install one. Never run destructive uninstalls without an explicit yes."
metadata:
  version: 0.3.1
  author: "Luong NGUYEN <luongnv89@gmail.com>"
  effort: high
---

# New Machine Setup

Turn a factory laptop into a **clean, ready-to-develop** machine. Detect OS + CPU arch first, optionally inventory/remove OEM junk (the XFreeze / Grok Build idea), then install a consistent baseline: git, shell, Node.js, Python, and the coding-agent CLIs this user actually uses.

This skill is an orchestrator. Long per-OS command tables live in `references/` so only the current platform is loaded, keeping the agent's context budget small while the full detail stays one link away.

**Do not** pipe remote scripts to a shell until the user has approved that step. Prefer official installers and the user's own [inbash](https://github.com/luongnv89/inbash) scripts when they match the OS.

## Human-in-the-loop (mandatory)

Every phase runs as a strict four-step loop. Do not skip any step, and do not batch multiple phases into one approval.

1. **Present** — show exactly what will be executed for this phase: each command, what it installs/changes, and any risk (especially removals or `curl | sh`).
2. **Approve** — wait for the user's explicit go-ahead (a clear "yes" or "run it"). For removals and remote-script installs, require an explicit per-item yes; a blanket "do everything" only covers non-destructive steps.
3. **Execute** — run only what was approved. If something fails, stop and re-present before retrying; never silently widen scope.
4. **Verify** — after execution, confirm the phase actually succeeded (version checks, file pres:ence, exit-code reads). Record pass/fail in the running log.

Keep a running list of every step's outcome (✓ / ✗ + evidence). The final report is built from this log, never from memory.

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
| `references/edge-cases.md` | ARM64, nvm conflicts, PEP 668, WSL, chsh, inbash distro limits |
| `scripts/detect_env.py` | Print a JSON inventory (OS, arch, package managers, tools) |

## Procedure

Each phase follows the **Human-in-the-loop** loop (present → approve → execute → verify). Begin every phase by presenting the concrete plan for that phase; do not move to the next phase until the current one verifies green (or is explicitly deferred by the user).

### 1. Detect the machine

- **Present:** "I'll run `python3 scripts/detect_env.py` to read OS, arch, package managers, and which dev tools already exist. Read-only, no changes."
- **Approve:** wait.
- **Execute:** run `python3 scripts/detect_env.py` (or the fallback one-liners from `references/detect.md` if `python3` is missing).
- **Verify:** confirm JSON contains `os`, `arch`, a package manager, and the tool map. Read **only** the OS reference that matches (`windows.md` / `macos.md` / `linux.md`).

**Phase 1 done when:** inventory JSON is captured and the correct OS reference is selected.

### 2. Inventory (Windows first; useful everywhere)

Inspired by [XFreeze](https://x.com/xfreeze/status/2090189407659999603): factory Windows boxes ship trial AV, OEM utilities, and partner games. **List before delete.**

- **Present:** the inventory commands (e.g. `winget list`, `Get-AppxPackage`). State this is read-only.
- **Approve:** wait.
- **Execute:** follow `references/windows.md` § Inventory (or list GUI apps / vendor agents on macOS/Linux).
- **Verify:** you have a complete list; build a `keep / review / remove-candidate` table.

Then, **per removal**:
- **Present** each removal candidate with its exact command and the risk (e.g. losing a vendor utility).
- **Approve:** explicit per-item yes. No removal without it.
- **Execute** only confirmed rows.
- **Verify** the package is gone (`winget list` / `Get-AppxPackage` no longer shows it).

**Phase 2 done when:** inventory shown; removals are either skipped or confirmed one-by-one and verified.

### 3. Baseline toolchain

- **Present:** the full list of what will be installed for this machine, drawn from the table below, with the exact commands (Homebrew/inbash/winget). Flag anything that overwrites an existing Node/Python.
- **Approve:** wait.
- **Execute:** install **missing** pieces only (idempotent):
  - Package manager — Homebrew (mac), winget (Windows), distro pkg (Linux)
  - CLI baseline — git, curl, wget, vim/editor (inbash `unix/basic.sh` on Debian)
  - Shell — zsh + Oh My Zsh + inbash `setup-ohMyZsh.sh` (mac/linux); Windows keeps PowerShell, optional WSL2
  - Node.js LTS — inbash `unix/nodejs.sh` / `mac/nodejs.sh`; Windows `winget install OpenJS.NodeJS.LTS`
  - Python — mac: inbash `mac/python-pip-uv.sh`; Linux: `unix/python3-pip.sh` + **uv**; Windows: `winget install Python.Python.3.12` + **uv**
- **Verify:** `git --version`, `node -v`, `npm -v`, `python3 --version` (and `uv --version`) succeed for the target OS. Prefer LTS Node and a venv/uv workflow.

**Phase 3 done when:** baseline verification commands all pass (or deferred items are recorded).

### 4. Coding-agent CLIs

- **Present:** the install order and exact commands from `references/agent-clis.md` (Claude Code, Codex, Pi, OpenCode), noting any `curl | sh` URL that needs explicit approval.
- **Approve:** wait. Per-tool yes is fine; a blanket yes covers all non-destructive installs.
- **Execute:** install in order, skipping any already present:
  1. Claude Code
  2. Codex
  3. Pi (`@mariozechner/pi-coding-agent`)
  4. OpenCode
- **Verify:** each requested CLI prints a version (`claude --version`, `codex --version`, `pi --version`, `opencode --version`). Never store API keys in the skill or shell history.

**Phase 4 done when:** each requested CLI verifies green (or explicitly skipped by the user).

### 5. Final report

- **Present:** nothing to execute here — this is the consolidated deliverable.
- **Execute/Verify:** assemble the report from the running step log (built across phases 1–4), not from memory.
- Print the report (template below). Offer optional extras from inbash (Docker, C/C++, SSH, MongoDB) only if the user asks.

**Phase 5 done when:** the report is shown and any gaps are either fixed or explicitly deferred by the user.

## Safety

- Never run a third-party "debloat everything" script unattended. OEM audio/chipset tools can be load-bearing.
- Never `curl | bash` without naming the URL and getting a yes.
- Never commit secrets. Auth for Claude/Codex is interactive login after install.
- Windows ARM64 (Snapdragon / Copilot+): prefer arm64 winget packages; say so when a tool is x64-only.
- **Approval is per-phase and, for removals/remote scripts, per-item.** A prior yes does not carry forward.

## Verification report

Always print a consolidated report built from the running log:

```
◆ New machine setup — FINAL REPORT
  Machine:   <os> / <arch> / <distro or build>
  Manager:   <package manager>

  Phase 1 · Detect
    ✓ inventory captured (os/arch/tools)
  Phase 2 · Inventory
    ✓ listed N packages; removed K (names: …) / skipped
  Phase 3 · Baseline
    ✓ git <v>   ✓ node <v>   ✓ npm <v>
    ✓ python <v>   ✓ uv <v>
    ✓ zsh + Oh My Zsh  / skipped (Windows host)
  Phase 4 · Agent CLIs
    ✓ Claude Code <v>   ✓ Codex <v>   ✓ Pi <v>   ✓ OpenCode <v>
    (skipped: …)

  Result:    READY | PARTIAL | BLOCKED
  Deferred:  <optional extras the user declined>
```

`READY` = baseline + Node + Python verify green. Agents may be skipped and still READY if the user declined them. `PARTIAL` = some verification failed but non-fatal; `BLOCKED` = a required phase could not be approved or executed.

## Acceptance Criteria

The skill is done when all of these hold:

- `python3 scripts/detect_env.py` prints valid JSON with `os`, `arch`, a package manager, and a tool map.
- Every phase ran the present → approve → execute → verify loop, and each approval is recorded in the running log.
- No removal or `curl | sh` ran without an explicit, per-item yes.
- Phase 3 verifies green: `git --version`, `node -v`, `npm -v`, `python3 --version`, `uv --version` succeed (or deferred items are logged).
- Each requested agent CLI (Claude Code, Codex, Pi, OpenCode) verifies via its `--version` (or is explicitly skipped).
- The FINAL REPORT (template above) is printed, built from the running log — not from memory — with a `Result` of READY / PARTIAL / BLOCKED.
- `quick_validate.py` exits 0 on the shipped SKILL.md.

**Expected output:** the consolidated FINAL REPORT block shown under "Verification report" above.

## Edge Cases

Environment-specific gotchas (ARM64, nvm conflicts, PEP 668, WSL, `chsh` denial, inbash distro limits) live in `references/edge-cases.md` — read it when a phase hits an unusual machine.

## Pitfalls

- **PEP 668 on Linux:** do not `pip install` into the system Python. Use `uv` or a venv.
- **Node via both nvm and apt/brew:** pick one; prefer the inbash path unless nvm is already in use.
- **Oh My Zsh `chsh`:** needs a login session; don't fail the whole setup if `chsh` is denied.
- **WSL vs native Windows:** if the user wants Linux-native agents, set up WSL2 Ubuntu and re-run this skill *inside* WSL rather than mixing paths.
- **inbash scripts are Debian/mac-oriented.** On Fedora/Arch, follow `references/linux.md` package-manager switches, not the `.sh` files blindly.
