# Approvals and interaction protocol

Loaded by SKILL.md § Approvals. Every phase of `dev-machine-setup` runs under these rules — the
additive/mutating split, the five-step loop, run-block formatting, and how a run pauses without losing state.

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
