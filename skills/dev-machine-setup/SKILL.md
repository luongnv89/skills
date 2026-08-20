---
name: dev-machine-setup
description: "Set up or tune any machine — factory laptop or daily driver — on macOS, Linux, or Windows: report what's missing, install only that, then fix PATH, duplicate runtimes, shell config. Don't use for Dockerfiles, CI images, or single package installs."
license: MIT
effort: high
compatibility: "macOS, Linux (Debian/Ubuntu/Fedora/Arch), Windows (winget/PowerShell). Needs network and a package manager or permission to install one. Additive by default; anything that changes a working install needs an explicit per-item yes."
metadata:
  version: 0.4.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Dev Machine Setup

Bring **any** machine to a clean, ready-to-develop state — a factory laptop, a half-configured work box,
or a daily driver that has drifted. Never a fresh-install-only script: phase 1 builds a **gap report** of
what is missing and what is misconfigured, and every later phase acts only on that report.

**Gap-driven** is the whole design. Each phase self-skips when its slice of the report is empty, so a
re-run on an already-good machine installs nothing and still verifies. This makes the skill idempotent by
construction and safe to run repeatedly.

This is an orchestrator. Per-OS command tables live in `references/` so only the current platform is
loaded, keeping the context budget small while the full detail stays one link away.

## Modes

Mode comes from the **user's intent**, not from machine state — a machine with gaps is not permission to
fill them when the user only asked for a tune-up.

| Mode | Selected by | Runs |
|------|-------------|------|
| `setup` (default) | "set up this machine", "install my dev environment", "get this laptop ready" | Phases 1 → 6 |
| `tune` | "*just* optimize what's there", "don't install anything, fix my setup", "why is `claude` not found" | Phases 1, 5, 6 only |

**Tie-break:** `setup` is the default and wins whenever the request mentions missing pieces *at all* —
"verify what's missing and optimize it" is `setup`, not `tune`. Choose `tune` only when the ask is limited to
what is already installed. Still unsure once phase 1's gap report is on screen? Ask once, before phase 3.

In `tune`, phases 3 and 4 are skipped entirely — never bulk-install baseline tools or agent CLIs the user
did not ask for. Phase 5 may still install a package when that *is* the approved fix for a reported
finding (e.g. `uv` for `python-externally-managed`).

## Additive vs mutating

The load-bearing distinction for every approval in this skill:

- **Additive** — installs something that is *absent*. Nothing working can break. Batch-approvable per phase.
- **Mutating** — changes something that *already works*: upgrades, removals, `chsh`, rc-file edits,
  `curl | sh`, PATH rewrites, replacing a runtime. Needs an explicit **per-item yes**, with the risk named,
  and any rc file backed up first (`optimize.md` § top).

On a daily driver, mutating steps are the real hazard — not missing packages. A prior yes never carries
forward to another mutating item.

## Human-in-the-loop (mandatory)

Every phase runs a strict four-step loop. Do not skip a step; do not batch phases into one approval.

1. **Present** — exactly what will run: each command, what it changes, and its **additive/mutating** tag.
2. **Approve** — wait for an explicit go-ahead. A blanket "do everything" covers additive steps only.
3. **Execute** — only what was approved. On failure, stop and re-present; never silently widen scope.
4. **Verify** — confirm the phase actually took (version checks, file presence, exit codes).

**Read-only probes are exempt from step 2** — `detect_env.py`, version checks, `winget list`, `brew outdated`.
Say what you are running, then run it. The gate exists to guard *changes*; making the user approve a read that
changes nothing trains them to rubber-stamp the approvals that matter.

Keep a running log of every step's outcome (✓ / ✗ + evidence). The final report is built from that log,
never from memory.

## When to Use

- "set up this new laptop / fresh install"
- "install my dev environment" (Node, Python, agents)
- "optimize / clean up my dev setup", "my machine is a mess"
- "I installed X but the command isn't found"
- Windows OEM bloat, trial antivirus, preinstalled games

Don't use for: Dockerfiles, CI runners, or installing a single named package.

## Prerequisites

- Network.
- Admin/sudo (or winget) for system packages. Without it, only user-level installs are possible — say which
  requests that blocks rather than failing them silently.
- Optional clone of `https://github.com/luongnv89/inbash` — preferred source for Unix/mac scripts this user
  already maintains.

## Reference files (load only what you need)

| File | When |
|------|------|
| `scripts/detect_env.py` | Phase 1 — prints the gap report JSON (inventory + `missing` + `findings`) |
| `references/detect.md` | How to run the probe without `python3` and how to read every JSON key |
| `references/windows.md` | Windows: inventory, conservative debloat, winget stack |
| `references/macos.md` | macOS: Homebrew, Node, Python+uv, zsh |
| `references/linux.md` | Linux: apt/dnf/pacman, NodeSource LTS, python3-pip |
| `references/agent-clis.md` | Phase 4 — Claude Code, Codex, Pi, OpenCode install + verify |
| `references/optimize.md` | Phase 5 — one section per finding id, each tagged additive/mutating |
| `references/edge-cases.md` | No python3, Windows ARM64, WSL, containers, re-runs, inbash distro limits |

## Procedure

Every phase runs the four-step loop above. Do not advance until the current phase verifies green, self-skips
on an empty gap set, or is explicitly deferred by the user.

### 1. Detect and build the gap report

- **Present:** "Running `detect_env.py` — read-only, no network, no changes. It reports OS, arch, package
  managers, installed versions, what's missing, and what's misconfigured." Read-only: no approval needed.
- **Execute:** `python3 <skill-dir>/scripts/detect_env.py` — path it from the skill's own directory, never
  assume the user's cwd. Needs Python 3.9+; if `python3` is absent, use the fallbacks in `references/detect.md`.
- **Verify:** the JSON parses and contains `os`, `arch`, `tools`, `missing`, `findings`.

Then **show the user the gap report** as three short lists before doing anything else:

```
Present:  git 2.55 · node v26.7 · python 3.14 · uv 0.11 · zsh · claude · codex
Missing:  baseline → uv          agents → pi, opencode
Findings: 1 high · 0 medium · 2 low   (npm-global-bin-not-on-path, path-duplicates, oh-my-zsh-missing)
```

Read **only** the OS reference that matches (`windows.md` / `macos.md` / `linux.md`). Confirm the mode
(`setup` / `tune`) with the user if their request was ambiguous.

**Phase 1 done when:** the gap report JSON is captured, the three lists are shown, the mode is fixed, and the
matching OS reference is loaded.

### 2. Debloat — fresh Windows only, opt-in

Skip this phase entirely unless the machine is Windows **and** the user asked to clean OEM junk. Never on a
daily driver, a container, or a remote host. Inspired by
[XFreeze](https://x.com/xfreeze/status/2090189407659999603): factory Windows boxes ship trial AV, OEM
utilities, and partner games. **List before delete.**

- **Present** the read-only inventory commands (`winget list`, `Get-AppxPackage`).
- **Execute** `references/windows.md` § Inventory; build a `keep / review / remove-candidate` table.
- Then **per removal** (mutating): present the exact command and what is lost, get an explicit yes for that
  one package, execute, and verify it no longer lists.

**Phase 2 done when:** skipped with a reason logged, or the inventory is shown and every removal is
individually confirmed and verified.

### 3. Baseline gaps  *(skipped in `tune`)*

**Blocking findings first.** Four findings make installs fail or land invisibly, so they are fixed *here*,
before anything else, rather than waiting for phase 5: `no-package-manager`, `no-sudo`,
`brew-bin-not-on-path`, `npm-global-bin-not-on-path`. Fix per `references/optimize.md`, then continue. (A
missing package manager arrives as a finding, not as a `missing.baseline` entry.)

Then act only on `missing.baseline`. **If that list is empty, print `✓ baseline complete — nothing to install`
and skip to phase 4.** Never reinstall or upgrade a tool that is already present — an upgrade is mutating
and belongs to phase 5.

| Missing item | Install command lives in |
|--------------|--------------------------|
| `git` (+ curl, wget, editor) | the OS reference § Baseline |
| `zsh` / Oh My Zsh | `macos.md` / `linux.md` § Zsh (Unix only; Windows keeps PowerShell) |
| `node`, `npm` | the OS reference § Node.js LTS |
| `python3`, `uv` | the OS reference § Python |

- **Present:** the exact command for each missing item, tagged additive. Flag anything that would touch an
  existing Node or Python — that is mutating and needs its own yes.
- **Verify:** `git --version`, `node -v`, `npm -v`, `python3 --version`, `uv --version` succeed for the items
  just installed. On Unix, `zsh --version`.

**Phase 3 done when:** every item that was in `missing.baseline` verifies green, or is logged as deferred.

### 4. Agent CLI gaps  *(skipped in `tune`)*

Acts only on `missing.agents`, in this order: Claude Code → Codex → Pi → OpenCode. **Empty list → print
`✓ all agent CLIs present` and skip.** Ask which the user actually wants; do not assume all four.

- **Present:** the commands from `references/agent-clis.md`, naming any `curl | sh` URL (mutating — needs its
  own yes).
- **Execute:** install only the requested missing ones. Requires Node on PATH from phase 3.
- **Verify:** each prints a version (`claude --version`, `codex --version`, `pi --version`,
  `opencode --version`). If a just-installed CLI is "not found", that is
  `optimize.md#npm-global-bin-not-on-path` — carry it into phase 5 rather than reinstalling.

Auth is the first interactive run of each CLI. Never write API keys into the log or into `~/.zshrc`.

**Phase 4 done when:** every requested agent CLI verifies green, or is explicitly declined.

### 5. Optimize

Acts on `findings[]`, highest severity first. Each finding's `fix_ref` names its section in
`references/optimize.md`; read only the sections for findings that actually fired.

- **Present** one table: finding id · severity · what breaks today · the fix · **additive/mutating**.
- **Approve:** additive fixes can be batched. **Every mutating fix needs its own yes** — and back up any rc
  file before editing it.
- **Execute** approved fixes only. A declined finding is recorded, not retried.
- **Verify** by re-running `detect_env.py` and confirming the fixed ids are gone from `findings`. This re-run
  is the phase's proof — never verify from memory. **PATH and rc-file fixes keep reporting until a new shell
  reads them:** re-run inside a fresh login shell (`zsh -l -c '<skill-dir>/scripts/detect_env.py'`, or a new
  PowerShell window). If no fresh shell is available, confirm the rc file now contains the line and log the
  finding as *fixed — needs new shell*.

Optional deep checks (`brew outdated`, `winget upgrade`, `npm outdated -g`) need network and are opt-in;
see `optimize.md` § Deep checks. Never volunteer disk cleanup during a setup run.

**Phase 5 done when:** the verification re-run shows every approved fix gone from `findings` — or logged as
*fixed — needs new shell* — and each remaining finding is recorded as declined or deferred with its severity.

### 6. Final report

Nothing executes here. Assemble the report below from the running log built across phases 1–5.

**Phase 6 done when:** the report is printed with a `Result` line, and every gap and finding is accounted for
as fixed, declined, or deferred.

## Safety

Beyond the additive/mutating rule above:

- Never run a third-party "debloat everything" script unattended. OEM audio/chipset tools can be load-bearing.
- Never commit secrets, and never write an API key into a shell rc file. Auth for every agent CLI is its own
  interactive login after install.
- Windows ARM64 (Snapdragon / Copilot+): prefer arm64 winget packages; say so when a tool is x64-only.
- A failed step is reported, not worked around. Silently switching to `sudo`, `--force`, or
  `--break-system-packages` to make a command succeed is out of scope for this skill.

## Verification report

```
◆ Dev machine setup — FINAL REPORT
  Machine:   <os> / <arch> / <distro or build>   Mode: setup | tune
  Manager:   <package manager>

  Phase 1 · Gap report
    ✓ present N · missing B baseline, A agents · findings H high / M med / L low
  Phase 2 · Debloat
    ✓ skipped (not fresh Windows) | listed N, removed K (names: …)
  Phase 3 · Baseline gaps
    ✓ nothing missing | installed: uv 0.11 · node v22.14  (deferred: …)
  Phase 4 · Agent CLI gaps
    ✓ nothing missing | installed: pi 0.84 · opencode 1.18  (declined: …)
  Phase 5 · Optimize
    ✓ fixed:    npm-global-bin-not-on-path (high) · path-duplicates (low)
    ○ declined: intel-homebrew-on-apple-silicon (medium) — user deferred migration
    verified by re-running detect_env.py: 0 high remaining

  Result:    READY | PARTIAL | BLOCKED
  Next:      <what the user should do — open a new shell, run `claude` to log in, …>
```

- **READY** — no unresolved `high` findings, and in `setup` no baseline gap left unfilled. Declined agent CLIs
  and deferred low/medium findings are still READY.
- **PARTIAL** — a step failed non-fatally, or a `high` finding was declined.
- **BLOCKED** — a required phase could not run: no package manager, no sudo for a needed system install, or
  approval withheld for a step everything else depends on.

## Acceptance Criteria

- `python3 scripts/detect_env.py` prints valid JSON with `os`, `arch`, `tools`, `missing`, and `findings`.
- The phase-1 gap report (present / missing / findings) was shown to the user before anything was installed.
- Mode was fixed before phase 3; in `tune`, phases 3 and 4 installed nothing.
- Blocking findings (`no-package-manager`, `no-sudo`, `brew-bin-not-on-path`, `npm-global-bin-not-on-path`)
  were fixed at the top of phase 3, not deferred.
- Phases 3 and 4 acted **only** on `missing.*` — no tool that was already present was reinstalled or upgraded.
- Every mutating step has its own recorded yes; every rc file edited has a backup path in the log.
- Phase 5 verified by **re-running** `detect_env.py`, and the report's finding counts come from that re-run.
- The FINAL REPORT is printed from the running log with a `Result` of READY / PARTIAL / BLOCKED, and every gap
  and finding is fixed, declined, or deferred — none unaccounted for.
- `quick_validate.py` exits 0 on the shipped SKILL.md.

**Expected output:** the FINAL REPORT block above.

## Edge Cases

No `python3`, Windows ARM64, WSL, containers and remote-SSH hosts, interrupted runs, and inbash distro limits
live in `references/edge-cases.md`. Machine states the probe reports as findings are in `references/optimize.md`,
keyed by finding id.
