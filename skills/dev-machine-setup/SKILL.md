---
name: dev-machine-setup
description: "Set up or tune any dev machine, fresh or drifted, on macOS, Linux, or Windows: report what's missing, install only that, then fix PATH, duplicate runtimes, and shell config. Don't use for Dockerfiles, CI images, or single package installs."
license: MIT
effort: high
compatibility: "macOS, Linux (Debian/Ubuntu/Fedora/Arch), Windows (winget/PowerShell). Needs network and a package manager or permission to install one. Additive by default; anything that changes a working install needs an explicit per-item yes."
metadata:
  version: 0.9.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Dev Machine Setup

Bring **any** machine to a clean, ready-to-develop state — a factory laptop, a half-configured work box, or a
daily driver that has drifted. Never a fresh-install-only script: phase 1 builds a **gap report** of what is
missing and misconfigured, and every later phase acts only on that report.

**Gap-driven** is the whole design. Each phase self-skips when its slice of the report is empty, so a re-run
on an already-good machine installs nothing and still verifies — idempotent by construction.

**Self-contained:** no external scripts repo is cloned. The shell config the skill deploys ships in `assets/`.

This is an orchestrator. Per-OS command tables and per-phase detail live in `references/`, so only the current
platform loads and the token budget stays on the machine in front of you.

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

## Approvals

**Read `references/approvals.md` before phase 2** — it holds the rules every phase runs under, in full. The
four that must be in your head from the start:

- **Additive** — installs something *absent*. Nothing working can break. Batch-approvable per phase.
- **Mutating** — changes something that *already works*: upgrades, removals, `chsh`, rc-file edits,
  `curl | sh`, PATH rewrites. Needs an explicit **per-item yes**, with the risk named, and any rc file backed
  up first. A prior yes never carries forward to another mutating item.
- **Five-step loop, every phase:** Present → Approve → Execute → Verify → Record. Read-only probes
  (`detect_env.py`, version checks, `winget list`) skip the approve step; nothing that changes state does.
- **Run-blocks:** every proposed command ships as a copy-whole fenced block — never inside a table cell, never
  with a `<placeholder>` or an assumed cwd, always tagged `you run this` / `I can run this`.

The session file (`~/.dev-machine-setup/session.json`) *is* the running log. Write it at every Record step;
build the final report from it, never from memory. Pause and resume protocol: `references/approvals.md`.

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

## Reference files (load only what you need)

| File | When |
|------|------|
| `scripts/detect_env.py` | Phase 1 — prints the gap report JSON (inventory + `missing` + `findings`) |
| `references/approvals.md` | Before phase 2 — additive/mutating, the five-step loop, run-blocks, pause/resume |
| `references/procedure.md` | Every phase — what each phase actually does, step by step |
| `references/detect.md` | How to run the probe without `python3` and how to read every JSON key |
| `references/windows.md` | Windows: inventory, conservative debloat, winget stack |
| `references/macos.md` | macOS: Homebrew, Node, Python+uv, zsh, starship |
| `references/linux.md` | Linux: apt/dnf/pacman, NodeSource LTS, python3-pip, zsh, starship |
| `references/agent-clis.md` | Phase 4 — Claude Code, Codex, Pi, OpenCode install + verify |
| `references/optimize.md` | Phase 5 — one section per finding id, each tagged additive/mutating |
| `references/session.md` | Phase 0 and every Record step — session-file schema, write command, reconcile rules |
| `references/report-template.md` | Phase 6 — the FINAL REPORT block and what each line must carry |
| `references/edge-cases.md` | No python3, Windows ARM64, WSL, containers, re-runs, unsupported distros |
| `assets/zshrc-config` | Phases 3 and 5 — the `~/.zshrc` deployed by `oh-my-zsh-missing`; owns the theme, plugin list, and starship init |
| `assets/starship.toml` | Phases 3 and 5 — the prompt config deployed by `starship-config-*`; `cp` it from the skill dir, never inline its contents |

## Procedure

Full step-by-step detail for every phase is in **`references/procedure.md`** — read it at phase 0 and keep it
open. This table is the spine: the order, and the condition that lets you advance. Do not advance until the
current phase verifies green, self-skips on an empty gap set, or is explicitly deferred by the user.

| # | Phase | Done when |
|---|-------|-----------|
| 0 | Resume check | Resuming from a reconciled session file, or starting clean with any discarded session deleted |
| 1 | Detect and build the gap report | Gap report JSON captured, three lists shown, mode fixed, OS reference loaded, session file written |
| 2 | Debloat *(fresh Windows only, opt-in)* | Skipped with a reason logged, or inventory shown and every removal individually confirmed and verified |
| 3 | Baseline gaps *(skipped in `tune`)* | Every item in `missing.baseline` verifies green, or is logged as deferred |
| 4 | Agent CLI gaps *(skipped in `tune`)* | Every requested agent CLI verifies green, or is explicitly declined |
| 5 | Optimize | Verification re-run shows every approved fix gone from `findings`; each remaining one recorded as declined or deferred |
| 6 | Final report | Report printed with a `Result` line, every gap and finding accounted for, session file marked `complete` |

Three things bite often enough to belong here rather than only in the detail file:

- **Blocking findings go first, in phase 3** — `no-package-manager`, `no-sudo`, `brew-bin-not-on-path`,
  `npm-global-bin-not-on-path` make installs fail or land invisibly.
- **Phases 3 and 4 act only on `missing.*`.** Never reinstall or upgrade something already present; an upgrade
  is mutating and belongs to phase 5.
- **Phase 5 verifies by re-running `detect_env.py`**, never from memory. PATH and rc-file fixes keep reporting
  until a new shell reads them — re-run in a fresh login shell, or log the finding as *fixed — needs new shell*.

### Zsh: one source of truth

`ZSH_THEME="wedisagree"`, the four-plugin list, and the `starship init zsh` line all live in
`assets/zshrc-config`, which this skill ships and deploys by `cp`. Never hand-write those lines into
`~/.zshrc` instead — edit the asset. It is a vendored **fork** of `luongnv89/inbash`'s config: upstream fixes
do not flow in, which is the price of having no dependency.

**Deploying it is not always additive.** `cp assets/zshrc-config ~/.zshrc` overwrites an existing `~/.zshrc`,
so it is additive only when none is present and **mutating** — backup plus its own yes — when one is. A
blanket "do everything" approval never covers the mutating case. Full split in
`optimize.md#oh-my-zsh-missing`.

## Safety

Beyond the additive/mutating rule:

- Never run a third-party "debloat everything" script unattended. OEM audio/chipset tools can be load-bearing.
- Never commit secrets, and never write an API key into a shell rc file. Auth for every agent CLI is its own
  interactive login after install.
- Windows ARM64 (Snapdragon / Copilot+): prefer arm64 winget packages; say so when a tool is x64-only.
- A failed step is reported, not worked around. Silently switching to `sudo`, `--force`, or
  `--break-system-packages` to make a command succeed is out of scope for this skill.

## Verification report

Phase 6 prints the FINAL REPORT block from `references/report-template.md` — one line per phase, sourced from
the session file. `Result` is one of:

- **READY** — no unresolved `high` findings, and in `setup` no baseline gap left unfilled. Declined agent CLIs
  and deferred low/medium findings are still READY.
- **PARTIAL** — a step failed non-fatally, or a `high` finding was declined.
- **BLOCKED** — a required phase could not run: no package manager, no sudo for a needed system install, or
  approval withheld for a step everything else depends on.

## Acceptance Criteria

- `detect_env.py` printed valid JSON with `os`, `arch`, `tools`, `missing`, `findings`, and the phase-1 gap
  report was shown before anything was installed.
- Mode was fixed before phase 3; in `tune`, phases 3 and 4 installed nothing.
- Blocking findings were fixed at the top of phase 3, not deferred.
- Phases 3 and 4 acted **only** on `missing.*` — nothing already present was reinstalled or upgraded.
- Every command reached the user as a run-block: none in a table cell, none with an unresolved
  `<placeholder>` or an assumed cwd, each tagged `you run this` / `I can run this`.
- The session file existed from phase 1 on, was rewritten at every Record step, and is `complete` by phase 6.
- Every mutating step has its own recorded yes; every rc file edited has a backup path in the session file.
- Phase 5 verified by **re-running** `detect_env.py`; the report's counts come from that re-run.
- The FINAL REPORT printed with a `Result` of READY / PARTIAL / BLOCKED and every gap and finding accounted
  for as fixed, declined, or deferred.
- `quick_validate.py` exits 0 on the shipped SKILL.md.

**Expected output:** the FINAL REPORT block (`references/report-template.md`).

## Edge Cases

No `python3`, Windows ARM64, WSL, containers and remote-SSH hosts, interrupted runs, and distros outside the
shipped apt/dnf/pacman tables live in `references/edge-cases.md`. Machine states the probe reports as findings
are in `references/optimize.md`, keyed by finding id.
