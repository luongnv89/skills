#!/usr/bin/env bash
# dep_scan.sh — read-only ecosystem + dependency currency probe for codebase-modernizer.
#
# Detects which package ecosystems a repo uses, then runs each one's *read-only* outdated and
# vulnerability probes. Every probe is fail-soft: a missing tool is reported as "Not Assessed"
# with a reason, never a guess and never an abort.
#
# This script NEVER installs, updates, or modifies anything. If you are editing it and reach for
# `npm install`, `pip install`, `go get -u`, `cargo update`, or any sibling — stop. Upgrades are
# planned in MODERNIZATION_PLAN.md and run by a human, not by this scan.
#
# Usage:
#   dep_scan.sh [repo_root] [--offline] [--timeout SECONDS] [--depth N]
#
# Output: a markdown report on stdout. Exit 0 on a completed scan (even with findings),
#         2 on a usage or environment error.

set -uo pipefail   # deliberately not -e: probes are expected to exit non-zero

ROOT=""
OFFLINE=0
TIMEOUT=120
DEPTH=3

die() { printf 'dep_scan.sh: error: %s\n' "$1" >&2; printf 'Run with --help for usage.\n' >&2; exit 2; }

usage() {
  sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
}

while [ $# -gt 0 ]; do
  case "$1" in
    --help|-h) usage ;;
    --offline) OFFLINE=1; shift ;;
    --timeout) [ $# -ge 2 ] || die "--timeout needs a value in seconds"; TIMEOUT="$2"; shift 2 ;;
    --depth)   [ $# -ge 2 ] || die "--depth needs a number"; DEPTH="$2"; shift 2 ;;
    -*) die "unknown flag '$1'" ;;
    *) [ -z "$ROOT" ] || die "more than one repo_root given ('$ROOT' and '$1')"; ROOT="$1"; shift ;;
  esac
done

[ -n "$ROOT" ] || ROOT="$(pwd)"
[ -d "$ROOT" ] || die "repo_root '$ROOT' is not a directory"
case "$TIMEOUT" in ''|*[!0-9]*) die "--timeout must be a whole number of seconds, got '$TIMEOUT'" ;; esac
case "$DEPTH"   in ''|*[!0-9]*) die "--depth must be a whole number, got '$DEPTH'" ;; esac
ROOT="$(cd "$ROOT" && pwd)"

EXCLUDES='-not -path */node_modules/* -not -path */.git/* -not -path */vendor/* -not -path */dist/* -not -path */build/* -not -path */.venv/* -not -path */venv/* -not -path */target/*'

have() { command -v "$1" >/dev/null 2>&1; }

# Run a probe with a timeout when one is available; capture combined output.
run_probe() {
  local label="$1"; shift
  local out rc
  if have timeout; then
    out="$(cd "$ROOT" && timeout "$TIMEOUT" "$@" 2>&1)"; rc=$?
  elif have gtimeout; then
    out="$(cd "$ROOT" && gtimeout "$TIMEOUT" "$@" 2>&1)"; rc=$?
  else
    out="$(cd "$ROOT" && "$@" 2>&1)"; rc=$?
  fi
  printf '\n**%s** — `%s`\n\n' "$label" "$*"
  if [ $rc -eq 124 ]; then
    printf '> Not Assessed — probe exceeded %ss timeout.\n' "$TIMEOUT"
    return
  fi
  if [ -z "$out" ]; then
    printf '> No output (exit %s) — nothing reported by this probe.\n' "$rc"
    return
  fi
  printf '```\n%s\n```\n' "$(printf '%s' "$out" | head -c 20000)"
  if [ "${#out}" -gt 20000 ]; then
    printf '\n> _Output truncated at 20000 of %s chars — re-run `%s` directly for the full list._\n' \
      "${#out}" "$*"
  fi
}

skip_tool() { printf '\n**%s** — Not Assessed: `%s` not installed.\n' "$1" "$2"; }
skip_net()  { printf '\n**%s** — Not Assessed: offline mode, network probe skipped.\n' "$1"; }

# shellcheck disable=SC2086
found() { find "$ROOT" -maxdepth "$DEPTH" -name "$1" $EXCLUDES -print 2>/dev/null | head -20; }

ECOSYSTEMS=""
note_eco() { ECOSYSTEMS="$ECOSYSTEMS $1"; }

printf '# Dependency Scan — %s\n\n' "$ROOT"
printf '_Read-only probe. Offline: %s. Timeout: %ss. Search depth: %s._\n' \
  "$([ $OFFLINE -eq 1 ] && echo yes || echo no)" "$TIMEOUT" "$DEPTH"

printf '\n## Manifests detected\n\n'
MANIFESTS=""
NESTED_DIRS=""
for m in package.json pyproject.toml requirements.txt setup.py Pipfile go.mod Cargo.toml Gemfile \
         pom.xml build.gradle build.gradle.kts composer.json pubspec.yaml Package.swift mix.exs \
         Dockerfile docker-compose.yml; do
  hits="$(found "$m")"
  if [ -n "$hits" ]; then
    MANIFESTS="$MANIFESTS $m"
    total="$(find "$ROOT" -maxdepth "$DEPTH" -name "$m" -not -path '*/node_modules/*' -not -path '*/.git/*' \
             -not -path '*/vendor/*' -not -path '*/dist/*' -not -path '*/build/*' -not -path '*/.venv/*' \
             -not -path '*/venv/*' -not -path '*/target/*' 2>/dev/null | wc -l | tr -d ' ')"
    printf -- '- `%s`\n' "$m"
    printf '%s\n' "$hits" | sed "s|^$ROOT/\{0,1\}|    - |"
    [ "$total" -gt 20 ] && printf -- '    - _… %s more not shown (raise `--depth` or re-run per package)_\n' "$((total - 20))"
    # Record directories of non-root manifests so the summary can flag unprobed packages.
    while IFS= read -r hit; do
      [ -z "$hit" ] && continue
      d="$(dirname "$hit")"
      [ "$d" = "$ROOT" ] && continue
      case " $NESTED_DIRS " in *" $d "*) ;; *) NESTED_DIRS="$NESTED_DIRS $d" ;; esac
    done <<EOF
$hits
EOF
  fi
done
NESTED_DIRS="$(printf '%s' "$NESTED_DIRS" | tr ' ' '\n' | sed '/^$/d')"
[ -n "$(found '*.csproj')" ] && { MANIFESTS="$MANIFESTS csproj"; printf -- '- `*.csproj`\n'; }
[ -d "$ROOT/.github/workflows" ] && { MANIFESTS="$MANIFESTS actions"; printf -- '- `.github/workflows/`\n'; }

if [ -z "$MANIFESTS" ]; then
  printf '\n> **Not Assessed — no manifest found.** No dependency surface to audit at depth %s.\n' "$DEPTH"
  printf '> If this repo vendors its dependencies or nests them deeper, re-run with `--depth 5`.\n'
fi

# ---------- npm / pnpm / yarn ----------
if [ -f "$ROOT/package.json" ]; then
  note_eco npm
  printf '\n## npm / node\n'
  for lf in package-lock.json pnpm-lock.yaml yarn.lock; do
    [ -f "$ROOT/$lf" ] && printf -- '\n- Lockfile: `%s`\n' "$lf"
  done
  if [ ! -f "$ROOT/package-lock.json" ] && [ ! -f "$ROOT/pnpm-lock.yaml" ] && [ ! -f "$ROOT/yarn.lock" ]; then
    printf -- '\n- **Finding: no lockfile committed** — builds are not reproducible.\n'
  fi
  if [ -f "$ROOT/pnpm-lock.yaml" ] && have pnpm; then
    [ $OFFLINE -eq 1 ] && skip_net "pnpm outdated" || run_probe "pnpm outdated" pnpm outdated
    [ $OFFLINE -eq 1 ] && skip_net "pnpm audit"    || run_probe "pnpm audit" pnpm audit
  elif [ -f "$ROOT/yarn.lock" ] && have yarn; then
    [ $OFFLINE -eq 1 ] && skip_net "yarn outdated" || run_probe "yarn outdated" yarn outdated
    [ $OFFLINE -eq 1 ] && skip_net "yarn audit"    || run_probe "yarn audit" yarn npm audit
  elif have npm; then
    [ $OFFLINE -eq 1 ] && skip_net "npm outdated" || run_probe "npm outdated" npm outdated
    [ $OFFLINE -eq 1 ] && skip_net "npm audit"    || run_probe "npm audit" npm audit
  else
    skip_tool "npm probes" npm
  fi
fi

# ---------- Python ----------
if [ -f "$ROOT/pyproject.toml" ] || [ -f "$ROOT/requirements.txt" ] || [ -f "$ROOT/setup.py" ] || [ -f "$ROOT/Pipfile" ]; then
  note_eco python
  printf '\n## Python\n'
  if have uv && [ -f "$ROOT/uv.lock" ]; then
    run_probe "uv outdated" uv pip list --outdated
  elif have poetry && [ -f "$ROOT/poetry.lock" ]; then
    run_probe "poetry outdated" poetry show --outdated
  elif have pip; then
    [ $OFFLINE -eq 1 ] && skip_net "pip outdated" || run_probe "pip outdated" pip list --outdated --format=json
  else
    skip_tool "Python outdated" pip
  fi
  if have pip-audit; then
    [ $OFFLINE -eq 1 ] && skip_net "pip-audit" || run_probe "pip-audit" pip-audit
  else
    skip_tool "Python vulnerabilities" pip-audit
  fi
fi

# ---------- Go ----------
if [ -f "$ROOT/go.mod" ]; then
  note_eco go
  printf '\n## Go\n'
  if have go; then
    [ $OFFLINE -eq 1 ] && skip_net "go outdated" || run_probe "go outdated" go list -u -m all
  else
    skip_tool "Go outdated" go
  fi
  if have govulncheck; then
    [ $OFFLINE -eq 1 ] && skip_net govulncheck || run_probe govulncheck govulncheck ./...
  else
    skip_tool "Go vulnerabilities" govulncheck
  fi
fi

# ---------- Rust ----------
if [ -f "$ROOT/Cargo.toml" ]; then
  note_eco rust
  printf '\n## Rust\n'
  if have cargo; then
    if cargo outdated --version >/dev/null 2>&1; then
      [ $OFFLINE -eq 1 ] && skip_net "cargo outdated" || run_probe "cargo outdated" cargo outdated
    else
      skip_tool "cargo outdated" "cargo-outdated"
    fi
    if cargo audit --version >/dev/null 2>&1; then
      [ $OFFLINE -eq 1 ] && skip_net "cargo audit" || run_probe "cargo audit" cargo audit
    else
      skip_tool "cargo audit" "cargo-audit"
    fi
  else
    skip_tool "Rust probes" cargo
  fi
fi

# ---------- Ruby ----------
if [ -f "$ROOT/Gemfile" ]; then
  note_eco ruby
  printf '\n## Ruby\n'
  if have bundle; then
    [ $OFFLINE -eq 1 ] && skip_net "bundle outdated" || run_probe "bundle outdated" bundle outdated --parseable
  else
    skip_tool "Ruby probes" bundle
  fi
fi

# ---------- Java ----------
if [ -f "$ROOT/pom.xml" ]; then
  note_eco maven
  printf '\n## Java (Maven)\n'
  if have mvn; then
    [ $OFFLINE -eq 1 ] && skip_net "maven updates" || run_probe "maven updates" mvn -q versions:display-dependency-updates
  else
    skip_tool "Maven probes" mvn
  fi
fi
if [ -f "$ROOT/build.gradle" ] || [ -f "$ROOT/build.gradle.kts" ]; then
  note_eco gradle
  printf '\n## Java (Gradle)\n'
  printf '\n> `./gradlew dependencyUpdates` requires the ben-manes versions plugin. Check `build.gradle` for it before running; if absent, mark Not Assessed rather than adding the plugin.\n'
fi

# ---------- PHP ----------
if [ -f "$ROOT/composer.json" ]; then
  note_eco php
  printf '\n## PHP\n'
  if have composer; then
    [ $OFFLINE -eq 1 ] && skip_net "composer outdated" || run_probe "composer outdated" composer outdated --format=json
    [ $OFFLINE -eq 1 ] && skip_net "composer audit"    || run_probe "composer audit" composer audit --format=json
  else
    skip_tool "PHP probes" composer
  fi
fi

# ---------- .NET ----------
if [ -n "$(found '*.csproj')" ]; then
  note_eco dotnet
  printf '\n## .NET\n'
  if have dotnet; then
    [ $OFFLINE -eq 1 ] && skip_net "dotnet outdated"   || run_probe "dotnet outdated" dotnet list package --outdated
    [ $OFFLINE -eq 1 ] && skip_net "dotnet vulnerable" || run_probe "dotnet vulnerable" dotnet list package --vulnerable
  else
    skip_tool ".NET probes" dotnet
  fi
fi

# ---------- Dart / Flutter ----------
if [ -f "$ROOT/pubspec.yaml" ]; then
  note_eco dart
  printf '\n## Dart / Flutter\n'
  if have flutter; then
    [ $OFFLINE -eq 1 ] && skip_net "flutter pub outdated" || run_probe "flutter pub outdated" flutter pub outdated
  elif have dart; then
    [ $OFFLINE -eq 1 ] && skip_net "dart pub outdated" || run_probe "dart pub outdated" dart pub outdated
  else
    skip_tool "Dart probes" "flutter/dart"
  fi
fi

# ---------- Elixir ----------
if [ -f "$ROOT/mix.exs" ]; then
  note_eco elixir
  printf '\n## Elixir\n'
  if have mix; then
    [ $OFFLINE -eq 1 ] && skip_net "mix hex.outdated" || run_probe "mix hex.outdated" mix hex.outdated
  else
    skip_tool "Elixir probes" mix
  fi
fi

# ---------- Swift ----------
if [ -f "$ROOT/Package.swift" ]; then
  note_eco swift
  printf '\n## Swift\n'
  printf '\n> SwiftPM has no first-party outdated command. Compare `Package.resolved` pins to each upstream release manually; mark Not Assessed if that is not possible.\n'
fi

# ---------- Runtime / toolchain declarations ----------
printf '\n## Runtime and toolchain declarations\n\n'
RT=0
emit_rt() { RT=1; printf -- '- **%s**: `%s`\n' "$1" "$2"; }
[ -f "$ROOT/.nvmrc" ]            && emit_rt ".nvmrc" "$(tr -d '\n' < "$ROOT/.nvmrc")"
[ -f "$ROOT/.python-version" ]   && emit_rt ".python-version" "$(tr -d '\n' < "$ROOT/.python-version")"
[ -f "$ROOT/rust-toolchain.toml" ] && emit_rt "rust-toolchain.toml" "$(grep -m1 channel "$ROOT/rust-toolchain.toml" 2>/dev/null || echo present)"
[ -f "$ROOT/go.mod" ]            && emit_rt "go.mod go directive" "$(grep -m1 '^go ' "$ROOT/go.mod" 2>/dev/null || echo 'not declared')"
if [ -f "$ROOT/package.json" ] && grep -q '"engines"' "$ROOT/package.json" 2>/dev/null; then
  emit_rt "package.json engines" "$(grep -A3 '"engines"' "$ROOT/package.json" | tr '\n' ' ' | tr -s ' ' | cut -c1-120)"
fi
if [ -f "$ROOT/Dockerfile" ]; then
  while IFS= read -r line; do emit_rt "Dockerfile FROM" "$line"; done < <(grep -i '^FROM ' "$ROOT/Dockerfile" 2>/dev/null)
fi
if [ -d "$ROOT/.github/workflows" ]; then
  all_pins="$(grep -rhoE 'uses: *[^ ]+' "$ROOT/.github/workflows" 2>/dev/null | sort -u)"
  pins="$(printf '%s' "$all_pins" | head -30)"
  if [ -n "$pins" ]; then
    RT=1
    n_all="$(printf '%s\n' "$all_pins" | sed '/^$/d' | wc -l | tr -d ' ')"
    printf -- '- **GitHub Actions pins**:\n'
    printf '%s\n' "$pins" | sed 's/^/    - `/; s/$/`/'
    [ "$n_all" -gt 30 ] && printf -- '    - _… %s more not shown_\n' "$((n_all - 30))"
  fi
fi
[ $RT -eq 0 ] && printf '> Not Assessed — no runtime or toolchain version is declared anywhere. That is itself a finding: the required versions are undocumented.\n'

# ---------- Summary ----------
printf '\n## Scan summary\n\n'
if [ -z "$ECOSYSTEMS" ] && [ -n "$MANIFESTS" ]; then
  # Manifests exist but none at the repo root: this is a monorepo / nested layout.
  printf -- '- Ecosystems probed at repo root: **none**\n'
  printf -- '\n> **Not Assessed — manifests found only in subdirectories.** This scan probes the repo\n'
  printf -- '> root only. The manifests listed above are in nested packages, so no outdated or\n'
  printf -- '> vulnerability probe ran and the runtime section above reflects the root only.\n'
  printf -- '> **Re-run this script once per package directory** and merge the results:\n>\n'
  printf '%s\n' "$NESTED_DIRS" | sed 's|^|>     dep_scan.sh |'
elif [ -z "$ECOSYSTEMS" ]; then
  printf -- '- Ecosystems detected: **none**\n'
else
  printf -- '- Ecosystems detected:%s\n' "$ECOSYSTEMS"
  if [ -n "$NESTED_DIRS" ]; then
    printf -- '\n> **Partial coverage — nested manifests were not probed.** Only the repo root was\n'
    printf -- '> probed. Re-run per package directory and merge:\n>\n'
    printf '%s\n' "$NESTED_DIRS" | sed 's|^|>     dep_scan.sh |'
  fi
fi
printf -- '- Offline mode: %s\n' "$([ $OFFLINE -eq 1 ] && echo 'yes — currency is Not Assessed; installed versions only' || echo 'no')"
printf -- '- Nothing was installed, updated, or modified by this scan.\n'
printf -- '- Turn each row above into a finding record per `references/dependency-audit.md`.\n'
