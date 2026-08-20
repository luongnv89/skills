---
name: dev-machine-setup
description: "Set up or tune any machine — factory laptop or daily driver — on macOS, Linux, or Windows: report what's missing, install only that, then fix PATH, duplicate runtimes, shell config. Don't use for Dockerfiles, CI images, or single package installs."
license: MIT
effort: high
compatibility: "macOS, Linux (Debian/Ubuntu/Fedora/Arch), Windows (winget/PowerShell). Needs network and a package manager or permission to install one. Additive by default; anything that changes a working install needs an explicit per-item yes."
metadata:
  version: 0.6.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Dev Machine Setup

Bring **any** machine to a clean, ready-to-develop state — a factory laptop, a half-configured work box, or a
daily driver that has drifted. Never a fresh-install-only script: phase 1 builds a **gap report** of what is
missing and misconfigured, and every later phase acts only on that report.

**Gap-driven** is the whole design. Each phase self-skips when its slice of the report is empty, so a re-run
on an already-good machine installs nothing and still verifies — idempotent by construction.

This is an orchestrator: per-OS command tables live in `references/`, so only the current platform loads.

## Modes

Mode comes from the **user's intent**, not from machine state — a machine with gaps is not permission to
fill them when the user only asked for a tune-up.

| Mode | Selected by | Runs |
|------|-------------|------|
| `setup` (default) | "set up this machine", "install my dev environment", "get this laptop ready" | Phases 0 → 6 |
| `tune` | "*just* optimize what's there", "don't install anything, fix my setup", "why is `claude` not found" | Phases 0, 1, 5, 6 only |

**Tie-break:** `setup` wins whenever the request mentions missing pieces *at all* — "verify what's missing
and optimize it" is `setup`. Choose `tune` only when the ask is limited to what is already installed; still
unsure once the gap report is on screen, ask once, before phase 3.

`tune` skips phases 3 and 4 entirely — never bulk-install what the user did not ask for. Phase 5 may still
install a package when that *is* the approved fix for a finding (e.g. `uv` for `python-externally-managed`).

## Additive vs mutating

The load-bearing distinction for every approval in this skill:

- **Additive** — installs something that is *absent*. Nothing working can break. Batch-approvable per phase.
- **Mutating** — changes something that *already works*: upgrades, removals, `chsh`, rc-file edits,
  `curl | sh`, PATH rewrites, replacing a runtime. Needs an explicit **per-item yes**, with the risk named,
  and any rc file backed up first (`optimize.md` § top).

On a daily driver, mutating steps are the real hazard — not missing packages. A prior yes never carries
forward to another mutating item.

## Human-in-the-loop (mandatory)

Every phase runs a strict five-step loop. Do not skip a step; do not batch phases into one approval.

1. **Present** — exactly what will run, as **run-blocks** (§ Presenting commands): each command, what it
   changes, and its **additive/mutating** tag.
2. **Approve** — wait for an explicit go-ahead. A blanket "do everything" covers additive steps only.
3. **Execute** — only what was approved. On failure, stop and re-present; never silently widen scope.
4. **Verify** — confirm the phase actually took (version checks, file presence, exit codes).
5. **Record** — write the outcome to the **session file** (§ Pausing and resuming) before moving on, so a
   pause, a crash, or a closed terminal never loses what was already decided and done.

**Read-only probes are exempt from step 2** — `detect_env.py`, version checks, `winget list`, `brew outdated`.
Say what you are running, then run it. The gate exists to guard *changes*; making the user approve a read that
changes nothing trains them to rubber-stamp the approvals that matter.

The session file *is* the running log (✓ / ✗ + evidence per item). The final report is built from it, never
from memory.

## Presenting commands (run-blocks)

Every command you propose ships as a **run-block**: a fenced block the user can copy whole and run without
editing it first. Every phase, not just phase 5.

**Never put a command in a table cell** — cells wrap mid-token and produce something nobody can copy. Tables
carry `finding id · severity · what breaks today · additive/mutating` and *name* the mechanism ("Oh My Zsh
installer, `curl | sh`"); the command goes in the block underneath.

A run-block is:

- **One item per block**, headed by the finding id or item name and its additive/mutating tag.
- **Self-contained** — no assumed cwd (`cd` inside the block, or use an absolute path), no `$` prompt
  prefixes, no `<placeholders>`. If a value must come from the user (git identity, an npm prefix), **ask
  first, then present the block with it filled in.**
- **One purpose per block.** Inspect and fix never share a block — pasting one must not run the other.
- **Tagged with who runs it.** `you run this` for anything needing a password prompt (`chsh`), a GUI dialog
  (`xcode-select --install`), a browser login, or a shell replacement (`exec zsh -l`); otherwise
  `I can run this`. Says *where it runs*, never a substitute for additive/mutating, which says *what it risks*.
- Followed by its **verify** block where one is worth running.

Ask for approval as a numbered list, so the user answers `1` or `1,3` instead of retyping ids. Approved
`you run this` blocks may then be concatenated into one paste-once block — built **only** from items that
each already got their own yes, in approval order. A combined block is never the thing being approved.

**Example** — two low findings, presented right:

````markdown
| Finding | Sev | What breaks today | Tag |
|---------|-----|-------------------|-----|
| `login-shell-not-zsh` | low | zsh is installed but bash is still your login shell | mutating |
| `oh-my-zsh-missing` | low | no completion/plugin baseline for zsh | additive |

**1 · `login-shell-not-zsh`** — mutating · you run this (asks for your password; corporate policy or LDAP
may refuse it, which is not a failure — we just skip it)

```bash
chsh -s "$(command -v zsh)"
```

**2 · `oh-my-zsh-missing`** — additive · I can run this (downloads and runs the installer from
github.com/ohmyzsh, and creates `~/.zshrc`)

```bash
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
```

Approve which — `1`, `2`, `1,2`, or `none`?
````

## Pausing and resuming

Machine setup is long, interruptible work, so state lives on disk rather than in the conversation.

**Session file:** `~/.dev-machine-setup/session.json` (PowerShell: `$HOME\.dev-machine-setup\session.json`).
Create it at the end of phase 1 and rewrite it at every **Record** step — after each phase, and after each
individual approve/decline/execute inside phases 2–5. Schema and the write command are in
`references/session.md`.

The user can say "pause" at any point. Answer with three things and nothing else: the session file path, what
is left, and a **paste-once block of the remaining approved commands** so they can finish by hand if they
never come back. Never leave a half-applied rc edit behind at a pause.

Resuming needs no arguments — triggering the skill again is enough (phase 0).

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
| `references/session.md` | Phase 0 and every **Record** step — session-file schema, write command, reconcile rules |
| `references/report-template.md` | Phase 6 — the FINAL REPORT block and what each line must carry |
| `references/edge-cases.md` | No python3, Windows ARM64, WSL, containers, re-runs, inbash distro limits |

## Procedure

Every phase runs the five-step loop above. Do not advance until the current phase verifies green, self-skips
on an empty gap set, or is explicitly deferred by the user.

### 0. Resume check

- Read `~/.dev-machine-setup/session.json`. **Absent, or `status: complete`** → say nothing, start at phase 1.
- **Present and unfinished** → show one screen (mode, phases done, items done / approved-but-not-run /
  declined, next step) and offer **resume** (default) · **start fresh** · **discard**.
- On resume, **always re-run `detect_env.py` first and reconcile** — the machine moved on while you were away,
  possibly because the user pasted the remaining blocks themselves. Rules in `references/session.md`.
- Stale — `machine` mismatches this host, or the file is over 30 days old — say so and default to start fresh.
- **Discard** deletes the file immediately; a discarded session left on disk is what makes a later resume
  replay decisions the user threw away. **Start fresh** keeps it until phase 1 overwrites it.

**Phase 0 done when:** the run is resuming from a reconciled session file, or starting clean with any
discarded session deleted.

### 1. Detect and build the gap report

- **Present:** say what it does — read-only, no network, no changes; reports OS, arch, package managers,
  installed versions, what's missing, what's misconfigured. Read-only, so no approval needed.
- **Execute:** `python3 <skill-dir>/scripts/detect_env.py`, pathed from the skill's own directory, never the
  user's cwd. Needs Python 3.9+; without `python3`, use the fallbacks in `references/detect.md`.
- **Verify:** the JSON parses and contains `os`, `arch`, `tools`, `missing`, `findings`.

Then **show the gap report** as three short lists before doing anything else:

```
Present:  git 2.55 · node v26.7 · python 3.14 · uv 0.11 · zsh · claude · codex
Missing:  baseline → uv          agents → pi, opencode
Findings: 1 high · 0 medium · 2 low   (npm-global-bin-not-on-path, path-duplicates, oh-my-zsh-missing)
```

Read **only** the matching OS reference (`windows.md` / `macos.md` / `linux.md`), and confirm the mode if the
request was ambiguous.

**Phase 1 done when:** the gap report JSON is captured, the three lists are shown, the mode is fixed, the
matching OS reference is loaded, and the session file exists with phase 1 recorded `done`.

### 2. Debloat — fresh Windows only, opt-in

Skip entirely unless the machine is Windows **and** the user asked to clean OEM junk — never on a daily
driver, container, or remote host. Factory Windows boxes ship trial AV, OEM utilities, and partner games
(inspired by [XFreeze](https://x.com/xfreeze/status/2090189407659999603)). **List before delete.**

- **Present** the read-only inventory commands (`winget list`, `Get-AppxPackage`) as a run-block.
- **Execute** `references/windows.md` § Inventory; build a `keep / review / remove-candidate` table.
- Then **per removal** (mutating): one run-block per package naming what is lost, an explicit yes for that
  one package, then execute, verify it no longer lists, and record it.

**Phase 2 done when:** skipped with a reason logged, or the inventory is shown and every removal is
individually confirmed and verified.

### 3. Baseline gaps  *(skipped in `tune`)*

**Blocking findings first.** Four findings make installs fail or land invisibly, so they are fixed *here*
rather than in phase 5: `no-package-manager`, `no-sudo`, `brew-bin-not-on-path`, `npm-global-bin-not-on-path`.
Fix per `references/optimize.md`, then continue. (A missing package manager arrives as a finding, not as a
`missing.baseline` entry.)

Then act only on `missing.baseline`. **Empty list → print `✓ baseline complete — nothing to install` and skip
to phase 4.** Never reinstall or upgrade something already present — an upgrade is mutating, and belongs to
phase 5.

| Missing item | Install command lives in |
|--------------|--------------------------|
| `git` (+ curl, wget, editor) | the OS reference § Baseline |
| `zsh` / Oh My Zsh | `macos.md` / `linux.md` § Zsh (Unix only; Windows keeps PowerShell) |
| `node`, `npm` | the OS reference § Node.js LTS |
| `python3`, `uv` | the OS reference § Python |

- **Present:** one run-block per missing item, tagged additive. Flag anything that would touch an existing
  Node or Python — that is mutating and needs its own yes.
- **Verify:** `git --version`, `node -v`, `npm -v`, `python3 --version`, `uv --version` (Unix also
  `zsh --version`) succeed for the items just installed.

**Phase 3 done when:** every item that was in `missing.baseline` verifies green, or is logged as deferred.

### 4. Agent CLI gaps  *(skipped in `tune`)*

Acts only on `missing.agents`, in this order: Claude Code → Codex → Pi → OpenCode. **Empty list → print
`✓ all agent CLIs present` and skip.** Ask which the user actually wants; do not assume all four.

- **Present:** one run-block per CLI from `references/agent-clis.md`, with any `curl | sh` URL visible inside
  the block (mutating — needs its own yes).
- **Execute:** install only the requested missing ones. Requires Node on PATH from phase 3.
- **Verify:** each prints a version (`claude --version`, `codex --version`, `pi --version`,
  `opencode --version`). If a just-installed CLI is "not found", that is
  `optimize.md#npm-global-bin-not-on-path` — carry it into phase 5 rather than reinstalling.

Auth is the first interactive run of each CLI. Never write API keys into the log or into `~/.zshrc`.

**Phase 4 done when:** every requested agent CLI verifies green, or is explicitly declined.

### 5. Optimize

Acts on `findings[]`, highest severity first. Each finding's `fix_ref` names its section in
`references/optimize.md`; read only the sections for findings that actually fired.

- **Present** one table — finding id · severity · what breaks today · **additive/mutating** — then one
  run-block per finding beneath it (§ Presenting commands). No command goes in the table.
- **Approve:** ask as a numbered list. Additive fixes can be batched. **Every mutating fix needs its own
  yes** — and back up any rc file before editing it. Record each decision as it is made, not at the end.
- **Execute** approved fixes only. A declined finding is recorded, not retried.
- **Verify** by re-running `detect_env.py` and confirming the fixed ids are gone from `findings`. That re-run
  is the phase's proof — never verify from memory. **PATH and rc-file fixes keep reporting until a new shell
  reads them:** re-run in a fresh login shell (`zsh -l -c '<skill-dir>/scripts/detect_env.py'`, or a new
  PowerShell window); with no fresh shell available, confirm the rc file contains the line and log the finding
  as *fixed — needs new shell*.

Deep checks (`brew outdated`, `winget upgrade`, `npm outdated -g`) need network and are opt-in — `optimize.md`
§ Deep checks. Never volunteer disk cleanup during a setup run.

**Phase 5 done when:** the verification re-run shows every approved fix gone from `findings` — or logged as
*fixed — needs new shell* — and each remaining finding is recorded as declined or deferred with its severity.

### 6. Final report

Nothing executes. Assemble the report from the session file (`references/report-template.md`), then set its
`status` to `complete` so the next run starts clean instead of offering a resume.

**Phase 6 done when:** the report is printed with a `Result` line, every gap and finding is accounted for as
fixed, declined, or deferred, and the session file is marked `complete`.

## Safety

Beyond the additive/mutating rule above:

- Never run a third-party "debloat everything" script unattended. OEM audio/chipset tools can be load-bearing.
- Never commit secrets, and never write an API key into a shell rc file. Auth for every agent CLI is its own
  interactive login after install.
- Windows ARM64 (Snapdragon / Copilot+): prefer arm64 winget packages; say so when a tool is x64-only.
- A failed step is reported, not worked around. Silently switching to `sudo`, `--force`, or
  `--break-system-packages` to make a command succeed is out of scope for this skill.

## Verification report

Phase 6 prints the FINAL REPORT block from `references/report-template.md` — one line per phase, sourced from
the session file. `Result` is decided by these three rules:

- **READY** — no unresolved `high` findings, and in `setup` no baseline gap left unfilled. Declined agent CLIs
  and deferred low/medium findings are still READY.
- **PARTIAL** — a step failed non-fatally, or a `high` finding was declined.
- **BLOCKED** — a required phase could not run: no package manager, no sudo for a needed system install, or
  approval withheld for a step everything else depends on.

## Acceptance Criteria

- `detect_env.py` printed valid JSON with `os`, `arch`, `tools`, `missing`, `findings`, and the phase-1 gap
  report was shown before anything was installed.
- Mode was fixed before phase 3; in `tune`, phases 3 and 4 installed nothing.
- Blocking findings (`no-package-manager`, `no-sudo`, `brew-bin-not-on-path`, `npm-global-bin-not-on-path`)
  were fixed at the top of phase 3, not deferred.
- Phases 3 and 4 acted **only** on `missing.*` — nothing already present was reinstalled or upgraded.
- Every command reached the user as a run-block: none in a table cell, none with an unresolved
  `<placeholder>` or an assumed cwd, each tagged `you run this` / `I can run this`.
- The session file existed from phase 1 on, was rewritten at every Record step, and is `complete` by phase 6 —
  an interrupted run resumes by triggering the skill again.
- Every mutating step has its own recorded yes; every rc file edited has a backup path in the session file.
- Phase 5 verified by **re-running** `detect_env.py`; the report's counts come from that re-run. On a resumed
  run that re-run and its reconcile happened before any new work.
- The FINAL REPORT printed with a `Result` of READY / PARTIAL / BLOCKED and every gap and finding accounted
  for as fixed, declined, or deferred.
- `quick_validate.py` exits 0 on the shipped SKILL.md.

**Expected output:** the FINAL REPORT block (`references/report-template.md`).

## Edge Cases

No `python3`, Windows ARM64, WSL, containers and remote-SSH hosts, interrupted runs, and inbash distro limits
live in `references/edge-cases.md`. Machine states the probe reports as findings are in `references/optimize.md`,
keyed by finding id.
