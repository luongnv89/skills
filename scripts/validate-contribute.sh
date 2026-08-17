#!/usr/bin/env bash
# Validates: CONTRIBUTING.md Development Setup preconditions
# Usage: scripts/validate-contribute.sh [--check] [--run-destructive]
set -uo pipefail

MODE="check"
[ "${1:-}" = "--run-destructive" ] && MODE="destructive"
[ "${1:-}" = "--check" ] && MODE="check"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

fail=0
ok()   { printf '[CHECK] %-44s OK\n' "$1"; }
bad()  { printf '[CHECK] %-44s FAIL — %s\n' "$1" "$2"; fail=1; }
man()  { printf '[MANUAL] %-43s SKIPPED (run by operator)\n' "$1"; }

# --- Repo layout claimed by CONTRIBUTING ---
[ -f CONTRIBUTING.md ] && ok "CONTRIBUTING.md present" || bad "CONTRIBUTING.md present" "missing"
[ -d skills ] && ok "skills/ directory" || bad "skills/ directory" "missing"
[ -f CLAUDE.md ] && ok "CLAUDE.md present" || bad "CLAUDE.md present" "missing"
[ -f .github/PULL_REQUEST_TEMPLATE.md ] && ok "PR template" || bad "PR template" "missing .github/PULL_REQUEST_TEMPLATE.md"

# --- Tooling on PATH (CONTRIBUTING Development Setup) ---
command -v git >/dev/null 2>&1 && ok "git on PATH" || bad "git on PATH" "not found"
command -v python3 >/dev/null 2>&1 && ok "python3 on PATH" || bad "python3 on PATH" "not found"

# --- skill-creator scripts (CLAUDE.md:7-9; not vendored under skills/) ---
SC="${HOME}/.claude/skills/skill-creator/scripts"
for s in init_skill.py package_skill.py quick_validate.py; do
  if [ -f "$SC/$s" ]; then
    ok "skill-creator $s"
  else
    bad "skill-creator $s" "missing at $SC/$s — install skill-creator for your agent"
  fi
done

# --- skill-creator is NOT under this repo's skills/ (CONTRIBUTING correction) ---
if [ ! -d skills/skill-creator ]; then
  ok "no in-repo skills/skill-creator (expected)"
else
  bad "skills/skill-creator" "unexpected in-repo copy; CONTRIBUTING documents external path"
fi

# --- Spot-check: validate one known skill if quick_validate exists ---
if [ -f "$SC/quick_validate.py" ] && [ -f skills/doc-manager/SKILL.md ]; then
  if python3 "$SC/quick_validate.py" skills/doc-manager >/dev/null 2>&1; then
    ok "quick_validate.py skills/doc-manager"
  else
    bad "quick_validate.py skills/doc-manager" "non-zero exit"
  fi
fi

# --- Skill count parity: docs/index.html vs the catalog on disk ---
# Counting rule (stated in full in the docs/index.html <head> comment): every
# tracked SKILL.md anywhere under skills/, nested suite sub-skills included,
# because install.sh installs those children independently. Directories with no
# SKILL.md (e.g. *-workspace/) never count.
if [ -f docs/index.html ]; then
  on_disk="$(git ls-files skills | grep -c '/SKILL\.md$' | tr -d '[:space:]')"
  # Every site that advertises the count matches "<n> skills" or "<n> installable".
  # The <head> comment enumerates them; a site reworded out of that shape would
  # otherwise go unchecked, so the number of matches is asserted as well.
  expected_sites=6
  sites="$(grep -oE '[0-9]+ (skills|installable)' docs/index.html | grep -oE '^[0-9]+')"
  n_sites="$(printf '%s\n' "$sites" | grep -c '[0-9]' | tr -d '[:space:]')"
  bad_sites="$(printf '%s\n' "$sites" | grep '[0-9]' | grep -vx "$on_disk" | sort -u | tr '\n' ' ')"
  if [ -z "$on_disk" ] || [ "$on_disk" = "0" ]; then
    bad "docs/index.html skill count" "could not derive the count from git ls-files"
  elif [ "$n_sites" -eq 0 ]; then
    bad "docs/index.html skill count" "no '<n> skills'/'<n> installable' literal found — update this check if the copy was reworded"
  elif [ "$n_sites" -lt "$expected_sites" ]; then
    bad "docs/index.html skill count" "only $n_sites of the $expected_sites documented sites still match '<n> skills'/'<n> installable' — a reworded site would go unchecked"
  elif [ -n "$bad_sites" ]; then
    bad "docs/index.html skill count" "advertises ${bad_sites}but ${on_disk} SKILL.md files are tracked under skills/"
  else
    ok "docs/index.html skill count ($on_disk in $n_sites places)"
  fi
else
  bad "docs/index.html present" "missing"
fi

# --- Destructive scaffold — gated ---
if [ "$MODE" = "destructive" ]; then
  man "init_skill.py my-skill --path skills/ (creates files)"
  man "package_skill.py (writes dist/)"
else
  man "init_skill.py my-skill --path skills/ (creates files)"
  man "package_skill.py (writes dist/)"
fi

exit $fail
