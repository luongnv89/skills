# Phase procedure — full detail

Loaded by SKILL.md § Procedure, which carries the phase list and each phase's done-condition. This file
carries what each phase actually does. Every phase runs the five-step loop in `references/approvals.md`.

## 0. Resume check

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

## 1. Detect and build the gap report

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

## 2. Debloat — fresh Windows only, opt-in

Skip entirely unless the machine is Windows **and** the user asked to clean OEM junk — never on a daily
driver, container, or remote host. Factory Windows boxes ship trial AV, OEM utilities, and partner games
(inspired by [XFreeze](https://x.com/xfreeze/status/2090189407659999603)). **List before delete.**

- **Present** the read-only inventory commands (`winget list`, `Get-AppxPackage`) as a run-block.
- **Execute** `references/windows.md` § Inventory; build a `keep / review / remove-candidate` table.
- Then **per removal** (mutating): one run-block per package naming what is lost, an explicit yes for that
  one package, then execute, verify it no longer lists, and record it.

**Phase 2 done when:** skipped with a reason logged, or the inventory is shown and every removal is
individually confirmed and verified.

## 3. Baseline gaps  *(skipped in `tune`)*

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
| `starship` | `macos.md` / `linux.md` § Zsh → Starship prompt (Unix only) |
| `node`, `npm` | the OS reference § Node.js LTS |
| `python3`, `uv` | the OS reference § Python |

- **Present:** one run-block per missing item, tagged additive. Flag anything that would touch an existing
  Node or Python — that is mutating and needs its own yes.
- **Verify:** `git --version`, `node -v`, `npm -v`, `python3 --version`, `uv --version` (Unix also
  `zsh --version` and `starship --version`) succeed for the items just installed.

**The skill is self-contained — no external scripts repo is cloned.** `ZSH_THEME="wedisagree"`, the
four-plugin list, and the `starship init zsh` line all live in `assets/zshrc-config`, which this skill ships
and deploys by `cp`. Never hand-write those lines into `~/.zshrc` instead — edit the asset, so there stays one
source of truth. `assets/zshrc-config` is a vendored **fork** of `luongnv89/inbash`'s config: upstream fixes do
not flow in, which is the price of having no dependency.

**Deploying it is not always additive.** `cp assets/zshrc-config ~/.zshrc` overwrites an existing `~/.zshrc`,
so it is additive only when no `~/.zshrc` is present and **mutating** — backup plus its own yes — when one is.
A blanket "do everything" approval never covers the mutating case. Full split in
`optimize.md#oh-my-zsh-missing`.

**Phase 3 done when:** every item that was in `missing.baseline` verifies green, or is logged as deferred.

## 4. Agent CLI gaps  *(skipped in `tune`)*

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

## 5. Optimize

Acts on `findings[]`, highest severity first. Each finding's `fix_ref` names its section in
`references/optimize.md`; read only the sections for findings that actually fired.

- **Present** one table — finding id · severity · what breaks today · **additive/mutating** — then one
  run-block per finding beneath it (`approvals.md` § Presenting commands). No command goes in the table.
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

## 6. Final report

Nothing executes. Assemble the report from the session file (`references/report-template.md`), then set its
`status` to `complete` so the next run starts clean instead of offering a resume.

**Phase 6 done when:** the report is printed with a `Result` line, every gap and finding is accounted for as
fixed, declined, or deferred, and the session file is marked `complete`.
