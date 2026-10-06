---
name: dev-machine-setup
description: "Set up or tune any dev machine, fresh or drifted, on macOS, Linux, or Windows: report what's missing, install only that, then fix PATH, duplicate runtimes, and shell config. Don't use for Dockerfiles, CI images, or single package installs."
license: MIT
compatibility: "macOS, Linux (Debian/Ubuntu/Fedora/Arch), Windows (winget/PowerShell). Needs network and a package manager or permission to install one. Additive by default; anything that changes a working install needs an explicit per-item yes."
effort: high
metadata:
  version: 0.10.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Dev Machine Setup

Bring **any** machine to a clean, ready-to-develop state: a factory laptop, a half-configured work box, or a
daily driver that has drifted. Phase 1 builds a **gap report** of what is missing and misconfigured, and every
later phase acts only on that report.

**Gap-driven** is the whole design. Each phase self-skips when its slice of the report is empty, so a re-run
on an already-good machine installs nothing and still verifies: idempotent by construction.

**Self-contained:** no external scripts repo is cloned. The shell config the skill deploys ships in `assets/`.
This SKILL.md is the spine; per-OS command tables and per-phase detail live in `references/`, so only the
current platform loads and the token budget stays on the machine in front of you.

## Modes

Mode comes from the **user's intent**, not from machine state. A machine with gaps is not permission to fill
them when the user only asked for a tune-up.

| Mode | Selected by | Runs |
|------|-------------|------|
| `setup` (default) | "set up this machine", "install my dev environment", "get this laptop ready" | Phases 0 → 6 |
| `tune` | "*just* optimize what's there", "don't install anything, fix my setup", "why is `claude` not found" | Phases 0, 1, 5, 6 only |

**Tie-break:** if the request mentions missing pieces at all, choose `setup` ("verify what's missing and
optimize it" is `setup`). Choose `tune` only when the ask is limited to what is already installed. If the mode
is still unclear after the gap report is shown, ask the user once, before phase 3.

`tune` skips phases 3 and 4 entirely: never bulk-install what the user did not ask for. Phase 5 may still
install a package when that *is* the approved fix for a finding (e.g. `uv` for `python-externally-managed`).

## Approvals

**Read `references/approvals.md` before phase 2.** It holds the rules every phase runs under. The four to hold
from the start:

- **Additive**: installs something *absent*. Nothing working can break. Batch-approvable per phase.
- **Mutating**: changes something that *already works* (upgrades, removals, `chsh`, rc-file edits,
  `curl | sh`, PATH rewrites). Needs an explicit **per-item yes** with the risk named. Back up any rc file
  before editing it. A prior yes never carries forward to another mutating item.
- **Five-step loop, every phase:** Present → Approve → Execute → Verify → Record. Read-only probes
  (`detect_env.py`, version checks, `winget list`) skip the approve step; nothing that changes state does.
- **Run-blocks:** every proposed command ships as a copy-whole fenced block, never inside a table cell, never
  with a `<placeholder>` or an assumed cwd, always tagged `you run this` / `I can run this`.

The session file (`~/.dev-machine-setup/session.json`) *is* the running log. Write it at every Record step.
Build the final report from it, never from memory. Pause protocol: `references/approvals.md` § Pausing and
resuming; schema, reconcile and pause output: `references/session.md`.

## When to Use

- "set up this new laptop / fresh install"
- "install my dev environment" (Node, Python, agents)
- "optimize / clean up my dev setup", "my machine is a mess"
- "I installed X but the command isn't found"
- Windows OEM bloat, trial antivirus, preinstalled games

Don't use for: Dockerfiles, CI runners, or installing a single named package.

## Prerequisites

- **Network.** If a package download fails for lack of network, record that item as `deferred` with the
  reason `no network` and continue. Phases 0, 1, 5 (read-only checks) and 6 still run.
- **Admin/sudo (or winget)** for system packages. Without it, offer the user-level install where the OS
  reference has one. Name each request that the missing access blocks; never fail it silently.

## Reference files (load only what you need)

| File | When |
|------|------|
| `scripts/detect_env.py` | Phase 1 and the phase 5 re-run: prints the gap report JSON (inventory + `missing` + `findings`) |
| `references/approvals.md` | Before phase 2: additive/mutating, the five-step loop, run-blocks, pause/resume |
| `references/procedure.md` | Every phase: what each phase does, step by step |
| `references/detect.md` | Running the probe without `python3`; what every JSON key means |
| `references/windows.md` | Windows: inventory, conservative debloat, winget stack |
| `references/macos.md` | macOS: Homebrew, Node, Python+uv, zsh, starship |
| `references/linux.md` | Linux: apt/dnf/pacman, NodeSource LTS, python3-pip, zsh, starship |
| `references/agent-clis.md` | Phase 4: Claude Code, Codex, Pi, OpenCode install + verify |
| `references/optimize.md` | Phase 5: one section per finding id, each tagged additive/mutating |
| `references/session.md` | Phase 0 and every Record step: session-file schema, write command, reconcile and pause rules |
| `references/report-template.md` | Phase 6: the FINAL REPORT block, status rules, outcome map, reader checks |
| `references/edge-cases.md` | No python3, Windows ARM64, WSL, containers, re-runs, unsupported distros |
| `assets/zshrc-config` | Phases 3 and 5: the `~/.zshrc` deployed by `oh-my-zsh-missing`; owns the theme, plugin list, and starship init |
| `assets/starship.toml` | Phases 3 and 5: the prompt config deployed by `starship-config-*`; `cp` it from the skill dir, never inline its contents |

## Procedure

Read **`references/procedure.md`** at phase 0 and keep it open: it has the full steps for every phase. This
table is the order and the condition to advance. Advance only when the current phase verifies green,
self-skips on an empty gap set, or the user explicitly defers it.

| # | Phase | Done when |
|---|-------|-----------|
| 0 | Resume check | Resuming from a reconciled session file, or starting clean with any discarded session deleted |
| 1 | Detect and build the gap report | Gap report JSON captured, three lists shown, mode fixed, OS reference loaded, session file written |
| 2 | Debloat *(fresh Windows only, opt-in)* | Skipped with a reason logged, or inventory shown and every removal individually confirmed and verified |
| 3 | Baseline gaps *(skipped in `tune`)* | Every item in `missing.baseline` verifies green, or is logged as deferred |
| 4 | Agent CLI gaps *(skipped in `tune`)* | Every requested agent CLI verifies green, or is explicitly declined |
| 5 | Optimize | Verification re-run shows every approved fix gone from `findings`; each remaining one recorded as declined or deferred |
| 6 | Final report | Report printed with a `Result` line first, every gap and finding accounted for, session file marked `complete` |

Three rules that are easy to miss (detail in `procedure.md`):

- **Blocking findings go first, in phase 3:** `no-package-manager`, `no-sudo`, `brew-bin-not-on-path`,
  `npm-global-bin-not-on-path` make installs fail or land invisibly.
- **Phases 3 and 4 act only on `missing.*`.** Never reinstall or upgrade something already present. An upgrade
  is mutating and belongs to phase 5.
- **Phase 5 verifies by re-running `detect_env.py`**, never from memory. PATH and rc-file fixes keep reporting
  until a new shell reads them: re-run in a fresh login shell, or log the finding as *fixed — needs new shell*.

**Zsh config has one source of truth:** `assets/zshrc-config`, deployed by `cp`. Never hand-write its lines
into `~/.zshrc`. Deploying it over an **existing** `~/.zshrc` is mutating (backup plus its own yes), and a
blanket "do everything" never covers it. Detail: `procedure.md` § 3 and `optimize.md#oh-my-zsh-missing`.

## Step Completion Reports

At the end of each phase, print one block. Each check maps to that phase's **Done when** cell; `√` pass,
`×` fail, `—` skipped with its reason:

```
◆ Phase 3 · Baseline gaps
  missing.baseline handled:   √ 2/2 (uv 0.11 · node v22.14)
  blocking findings first:    — none fired
  session file recorded:      √
  Result:                     PASS | PARTIAL | FAIL
```

`PASS` = the Done-when condition holds with nothing deferred. `PARTIAL` = it holds, but an item was deferred,
declined, or failed. `FAIL` = the phase could not run; name why and apply the status rules below.

## Safety

Beyond the additive/mutating rule:

- Never run a third-party "debloat everything" script unattended. OEM audio/chipset tools can be load-bearing.
- Never commit secrets, and never write an API key into a shell rc file. Auth for every agent CLI is its own
  interactive login after install.
- Windows ARM64 (Snapdragon / Copilot+): prefer arm64 winget packages; say so when a tool is x64-only.
- Report a failed step; do not work around it. Silently switching to `sudo`, `--force`, or
  `--break-system-packages` to make a command succeed is out of scope for this skill.

## Final Report

Phase 6 prints the FINAL REPORT block from `references/report-template.md`, sourced from the session file.
It opens with `Result:`, then one line per phase, then `Evidence:`, `Uncertainty:` and `Decision:`. Apply the
**first** status rule that matches (full outcome map in the template):

1. **BLOCKED — reason**: the gap report could not be built (`detect_env.py` and the `detect.md` fallbacks
   both failed), or a blocking finding stayed unfixed so no requested install could run (no package manager
   and its install was declined or failed; no admin/sudo and no user-level path).
2. **PARTIAL — reason**: any step failed and was not fixed; a `high` finding is declined, deferred, or still
   in `findings` after the re-run without being recorded *fixed — needs new shell*; in `setup`, a
   `missing.baseline` item was declined or deferred; or the phase 5 verification re-run could not run.
3. **READY**: none of the above. Declined agent CLIs, declined or deferred low/medium findings, *fixed —
   needs new shell* items, and a run that found nothing to change are all READY.

A user declining a change never produces BLOCKED by itself. A pause is not phase 6: it prints the pause
output from `references/session.md`, which opens with `Result: PARTIAL — paused`.

Example (a tune run with one fix awaiting a new shell):

```
◆ Dev machine setup — FINAL REPORT
  Result:      READY
  Machine:     darwin / arm64 / macOS 15.4   Mode: tune
  ...
  Evidence:    detect_env.py re-run in the same shell: 1 high still listed (the PATH fix);
               export line confirmed in ~/.zshrc, backup ~/.zshrc.bak.20260820094533
  Uncertainty: npm-global-bin-not-on-path fixed — needs new shell (not re-checked in a login shell)
  Decision:    No approval needed.
    Remaining action: open a new terminal, then run `claude --version`
```

## Acceptance Criteria

- `detect_env.py` printed valid JSON with `os`, `arch`, `tools`, `missing`, `findings`, and the phase-1 gap
  report was shown before anything was installed.
- Mode was fixed before phase 3; in `tune`, phases 3 and 4 installed nothing.
- Blocking findings were fixed at the top of phase 3, not deferred.
- Phases 3 and 4 acted **only** on `missing.*`: nothing already present was reinstalled or upgraded.
- Every command reached the user as a run-block: none in a table cell, none with an unresolved
  `<placeholder>` or an assumed cwd, each tagged `you run this` / `I can run this`.
- The session file existed from phase 1 on, was rewritten at every Record step, and is `complete` by phase 6.
- Every mutating step has its own recorded yes; every rc file edited has a backup path in the session file.
- Phase 5 verified by **re-running** `detect_env.py`; the report's counts come from that re-run.
- A Step Completion Report printed after each phase that ran.
- The FINAL REPORT opened with a `Result` chosen by the first matching status rule, accounted for every gap
  and finding as fixed, declined, or deferred, and meets the four reader checks in
  `references/report-template.md`: result findable, facts apart from assumptions, claims traceable, next
  decision clear.

**Expected output:** the FINAL REPORT block (`references/report-template.md`).

## Edge Cases

No `python3`, Windows ARM64, WSL, containers and remote-SSH hosts, interrupted runs, and distros outside the
shipped apt/dnf/pacman tables live in `references/edge-cases.md`. Machine states the probe reports as findings
are in `references/optimize.md`, keyed by finding id.
