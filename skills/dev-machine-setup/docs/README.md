<!--
  DO NOT READ THIS FILE - This README.md is for human catalog browsing only.
  It ships inside the .skill package but is NEVER auto-loaded into agent context.
  The runtime loader only reads SKILL.md + references/ + scripts/ + agents/ when the skill triggers.
  If you're an AI agent, read the SKILL.md file instead for skill instructions.
-->

# Dev Machine Setup

Set up **or tune** any machine (macOS, Linux, Windows) — a factory laptop, a half-configured work box, or a
daily driver that has drifted.

Inspired by [XFreeze on new Windows boxes](https://x.com/xfreeze/status/2090189407659999603) (inventory OEM
junk before installing anything). Self-contained: no external scripts repo is cloned — the shell config it
deploys ships in the skill's own `assets/`.

## How it works

It runs **gap-driven**. A read-only probe (`scripts/detect_env.py`) reports three things:

- **Present** — what's already installed, with versions
- **Missing** — baseline tools (git, Node, Python, uv, zsh) and agent CLIs (Claude Code, Codex, Pi, OpenCode)
- **Findings** — what's misconfigured: npm global bin off PATH, two Node version managers fighting, Homebrew
  without its shellenv line, PEP 668 Python with no uv, duplicate PATH entries, missing git identity

Every phase then acts *only* on that report and self-skips when its slice is empty — so re-running on an
already-good machine installs nothing and simply verifies. Optional first phase on factory Windows: inventory
OEM bloat and remove it one confirmed package at a time.

## Two modes

| Mode | Ask for it with | Does |
|------|-----------------|------|
| `setup` | "set up this machine", "install my dev environment" | Fills every gap, then optimizes |
| `tune` | "optimize my dev setup", "why is `claude` not found" | Optimizes only — installs nothing you didn't ask for |

## Copy-paste, not narration

Every command it proposes arrives as its own fenced block you can copy whole and run — never a command
wedged into a table cell, never a `<placeholder>` you have to fill in, never a snippet that only works if
you happen to be in the right directory. Blocks that need *your* terminal (a `chsh` password prompt, a GUI
dialog, a browser login) are labelled as such, so it's always clear who runs what.

## Pause anywhere, resume by asking again

Long setups get interrupted. Progress — mode, what you approved, what you declined, which rc files were
backed up and where — is written to `~/.dev-machine-setup/session.json` after every step. Say "stop here"
and you get the file path, what's left, and one paste-once block of the remaining approved commands in case
you'd rather finish by hand.

To resume, just trigger the skill again. It re-probes the machine first and reconciles against what you
already did — including anything you ran yourself while it wasn't watching — so nothing is re-asked and
nothing is run twice.

## Usage

Ask an agent that has this skill:

> Set up this new machine for development.

> My dev setup is a mess — verify what's missing and optimize it.

> Fresh Windows ARM laptop — debloat then install Node, Python, and Claude Code.

## Safety

**Additive** work (installing something absent) is approved per phase. **Mutating** work — upgrading a
runtime, `chsh`, editing your `~/.zshrc`, uninstalling anything, piping a remote script to a shell — needs an
explicit yes per item, names its risk first, and backs up any rc file it touches. The skill never
mass-uninstalls OEM tools and never replaces a working install as a side effect of filling a gap.
