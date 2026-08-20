<!--
  DO NOT READ THIS FILE - This README.md is for human catalog browsing only.
  It ships inside the .skill package but is NEVER auto-loaded into agent context.
  The runtime loader only reads SKILL.md + references/ + scripts/ + agents/ when the skill triggers.
  If you're an AI agent, read the SKILL.md file instead for skill instructions.
-->

# New Machine Setup

Bootstrap a **clean, ready-to-develop** laptop (macOS, Linux, or Windows).

Inspired by [XFreeze on new Windows boxes](https://x.com/xfreeze/status/2090189407659999603) (inventory OEM junk before installing anything) and this user's [inbash](https://github.com/luongnv89/inbash) scripts.

## What it installs

1. Detects OS + CPU architecture
2. Optionally inventories / removes OEM bloat (Windows; confirm each removal)
3. Baseline: git, curl, package manager
4. Node.js LTS + npm
5. Python 3 + uv (no system-pip pollution)
6. Oh My Zsh (Unix) via inbash
7. Agent CLIs: Claude Code, Codex, Pi, OpenCode

## Usage

Ask an agent that has this skill:

> Set up this new machine for development.

Or point it at a specific OS:

> Fresh Windows ARM laptop — debloat then install Node, Python, and Claude Code.

## Safety

The skill never mass-uninstalls OEM tools and never pipes a remote script to the shell without an explicit yes.
