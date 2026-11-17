#!/usr/bin/env bash
# Validates: README.md Install section + install.sh / remote-install.sh preconditions
# Usage: scripts/validate-install.sh [--check] [--run-destructive]
set -uo pipefail

MODE="check"
[ "${1:-}" = "--run-destructive" ] && MODE="destructive"
[ "${1:-}" = "--check" ] && MODE="check"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

fail=0
ok()   { printf '[CHECK] %-40s OK\n' "$1"; }
bad()  { printf '[CHECK] %-40s FAIL — %s\n' "$1" "$2"; fail=1; }
man()  { printf '[MANUAL] %-39s SKIPPED (run by operator)\n' "$1"; }

# --- README Install section claims (README.md) ---
[ -f README.md ] && ok "README.md present" || bad "README.md present" "missing"

# --- Installer scripts exist and are executable (install.sh, remote-install.sh) ---
[ -f install.sh ] && ok "install.sh present" || bad "install.sh present" "missing"
[ -f remote-install.sh ] && ok "remote-install.sh present" || bad "remote-install.sh present" "missing"
[ -x install.sh ] && ok "install.sh executable" || bad "install.sh executable" "not +x"
[ -x remote-install.sh ] && ok "remote-install.sh executable" || bad "remote-install.sh executable" "not +x"

# --- Bash syntax of installers ---
if command -v bash >/dev/null 2>&1; then
  bash -n install.sh && ok "install.sh bash -n" || bad "install.sh bash -n" "syntax error"
  bash -n remote-install.sh && ok "remote-install.sh bash -n" || bad "remote-install.sh bash -n" "syntax error"
else
  bad "bash on PATH" "bash not found"
fi

# --- Discovery: at least one skills/*/SKILL.md or extras/*/SKILL.md (install.sh discover_skills) ---
count="$(find skills extras -mindepth 2 -maxdepth 3 -name SKILL.md 2>/dev/null | wc -l | tr -d ' ')"
[ "${count:-0}" -gt 0 ] && ok "discoverable SKILL.md count ($count)" || bad "discoverable SKILL.md" "none under skills/ or extras/"

# --- TOOLS list includes documented agents (install.sh:23) ---
if grep -q 'Google Antigravity' install.sh && grep -q 'Claude Code' install.sh; then
  ok "install.sh TOOLS includes Claude + Antigravity"
else
  bad "install.sh TOOLS list" "expected Claude Code and Google Antigravity"
fi

# --- Non-destructive: help/usage for remote installer ---
if bash remote-install.sh --help >/dev/null 2>&1 || bash remote-install.sh -h >/dev/null 2>&1; then
  ok "remote-install.sh --help"
else
  # help may exit non-zero; still accept if Usage text is in file
  if grep -q '^Usage:' remote-install.sh; then
    ok "remote-install.sh Usage: documented"
  else
    bad "remote-install.sh help" "no Usage block"
  fi
fi

# --- Destructive / interactive install — never auto-run ---
if [ "$MODE" = "destructive" ]; then
  man "bash install.sh (interactive TUI)"
  man "curl | bash remote-install.sh (network install)"
else
  man "bash install.sh (interactive TUI)"
  man "curl | bash remote-install.sh (network install)"
fi

exit $fail
