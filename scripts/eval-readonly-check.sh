#!/usr/bin/env bash
# Validates: codebase-modernizer's read-only contract as a DELTA against a pre-run
#            snapshot of the target repo — not as "git diff --stat is empty", which is
#            unsatisfiable on the stale, already-dirty repos this skill targets.
# Usage: scripts/eval-readonly-check.sh snapshot --target DIR [--manifest DIR]
#        scripts/eval-readonly-check.sh verify   --target DIR [--manifest DIR] [--allow PATH]...
#        scripts/eval-readonly-check.sh restore  --target DIR --dest DIR [--manifest DIR] [--allow PATH]...
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

fail=0
ok()   { printf '[CHECK] %-44s OK\n' "$1"; }
bad()  { printf '[CHECK] %-44s FAIL — %s\n' "$1" "$2"; fail=1; }
man()  { printf '[MANUAL] %-43s SKIPPED (run by operator)\n' "$1"; }

usage() {
  sed -n '2,7p' "$0"
  exit 2
}

# --- Declared-artifact allowlist -------------------------------------------------
# TRANSCRIBED, not invented. Every entry below is quoted from the skill's own
# contract text; the citation is the file:line it came from.
#
#   MODERNIZATION_REPORT.md  skills/codebase-modernizer/SKILL.md:271
#                            ("MODERNIZATION_REPORT.md and MODERNIZATION_PLAN.md
#                             both exist at the target repo root")
#                            also references/report-template.md:122
#   MODERNIZATION_PLAN.md    skills/codebase-modernizer/SKILL.md:271
#                            also references/report-template.md:123
#   CODE_REVIEW.md           skills/codebase-modernizer/SKILL.md:273
#                            ("a **declared delegate artifact** (`CODE_REVIEW.md`)")
#                            also SKILL.md:30, references/delegation-policy.md:26,
#                            references/report-template.md:124
#   obj/ .dart_tool/         skills/codebase-modernizer/SKILL.md:31
#   target/ .gradle/         ("**probe byproducts** (build dirs some dependency probes
#                             create, such as `obj/`, `.dart_tool/`, `target/`, `.gradle/`)")
#                            also references/dependency-audit.md:76-77
#   coverage/ dist/          skills/codebase-modernizer/references/baseline.md:30
#                            ("New *untracked* build output (`coverage/`, `dist/`,
#                             `target/`) is acceptable")
#
# Nothing else. A path outside this list appearing after the run is a contract breach
# (SKILL.md:31 "Nothing else.", SKILL.md:274 "Anything else is a contract breach").
DEFAULT_ALLOW=(
  "MODERNIZATION_REPORT.md"
  "MODERNIZATION_PLAN.md"
  "CODE_REVIEW.md"
  "obj/"
  ".dart_tool/"
  "target/"
  ".gradle/"
  "coverage/"
  "dist/"
)

CMD="${1:-}"
[ -n "$CMD" ] || usage
shift || true

TARGET=""
SNAP=""
DEST=""
EXTRA_ALLOW=()
while [ $# -gt 0 ]; do
  case "$1" in
    --target)   TARGET="${2:-}"; shift 2 ;;
    --manifest) SNAP="${2:-}";   shift 2 ;;
    --dest)     DEST="${2:-}";   shift 2 ;;
    --allow)    EXTRA_ALLOW+=("${2:-}"); shift 2 ;;
    -h|--help)  usage ;;
    *) printf 'unknown argument: %s\n' "$1" >&2; usage ;;
  esac
done

[ -n "$TARGET" ] || { printf -- '--target is required\n' >&2; usage; }
if [ ! -d "$TARGET" ]; then
  printf -- '--target %s is not a directory\n' "$TARGET" >&2
  exit 2
fi
TARGET="$(cd "$TARGET" && pwd)"
[ -n "$SNAP" ] || SNAP="${TMPDIR:-/tmp}/eval-readonly-$(basename "$TARGET")"

ALLOW=("${DEFAULT_ALLOW[@]}")
if [ "${#EXTRA_ALLOW[@]}" -gt 0 ]; then
  ALLOW+=("${EXTRA_ALLOW[@]}")
fi

# --- sha256 shim (coreutils or BSD; no third-party deps) -------------------------
if command -v sha256sum >/dev/null 2>&1; then
  sha256_of() { sha256sum "$1" | cut -d' ' -f1; }
elif command -v shasum >/dev/null 2>&1; then
  sha256_of() { shasum -a 256 "$1" | cut -d' ' -f1; }
elif command -v openssl >/dev/null 2>&1; then
  sha256_of() { openssl dgst -sha256 "$1" | awk '{print $NF}'; }
else
  printf 'no sha256 tool found (sha256sum, shasum, openssl)\n' >&2
  exit 2
fi

# --- allowlist matching ----------------------------------------------------------
# A trailing-slash entry matches that directory and everything under it, at ANY depth
# (dotnet writes obj/ per project, not only at the root — dependency-audit.md:76).
# A plain entry matches that path at the repo root only, which is where the contract
# places the two reports and CODE_REVIEW.md (SKILL.md:271-273).
is_allowed() {
  local p="${1#./}" a
  [ -z "$p" ] && return 1
  [ "$p" = "." ] && return 1
  for a in "${ALLOW[@]}"; do
    case "$a" in
      */)
        local d="${a%/}"
        case "$p" in
          "$d"|"$d"/*|*/"$d"|*/"$d"/*) return 0 ;;
        esac
        ;;
      *)
        [ "$p" = "$a" ] && return 0
        ;;
    esac
  done
  return 1
}

# Reads a stream on stdin, drops every line whose path field is allowlisted.
# FIELD=3 → tab-separated manifest (kind, hash, path). FIELD=porcelain → git status.
filter_allowed() {
  local mode="$1" line path
  while IFS= read -r line; do
    case "$mode" in
      manifest)  path="$(printf '%s' "$line" | cut -f3-)" ;;
      porcelain) path="${line:3}" ;;
    esac
    # `git status` renders renames as "old -> new"; judge on the destination.
    case "$path" in *' -> '*) path="${path##* -> }" ;; esac
    path="${path%/}"
    is_allowed "$path" || printf '%s\n' "$line"
  done
}

# --- the three derivations -------------------------------------------------------
derive_status() { ( cd "$TARGET" && git status --porcelain ); }
derive_diff()   { ( cd "$TARGET" && git diff ); }

# SHA-256 manifest of every tracked and untracked-but-not-ignored path. Untracked
# files are the reason this exists: `git diff --stat` cannot see them, so a delegate
# that writes a new .github/workflows/ci.yml or a new test file would otherwise pass
# unnoticed — and neither is gitignored, so both stay in scope here.
#
# `--exclude-standard` deliberately honours the TARGET's own .gitignore. Hashing
# node_modules/, .venv/, or vendor/ would mean tens of thousands of subprocesses per
# derivation and a spurious breach the moment a probe touched an ignored cache file
# (npm rewrites node_modules/.package-lock.json on any read). The contract has teeth
# exactly where git can see: baseline.md:30 already tolerates untracked build output.
derive_manifest() {
  ( cd "$TARGET" && git ls-files --cached --others --exclude-standard 2>/dev/null |
    LC_ALL=C sort | while IFS= read -r p; do
      [ -e "$p" ] || [ -L "$p" ] || continue
      if [ -L "$p" ]; then
        printf 'symlink\t%s\t%s\n' "$(readlink "$p")" "$p"
      elif [ -d "$p" ]; then
        printf 'dir\t-\t%s\n' "$p"
      elif [ -f "$p" ]; then
        printf 'file\t%s\t%s\n' "$(sha256_of "$p")" "$p"
      else
        printf 'other\t-\t%s\n' "$p"
      fi
    done )
}

do_snapshot() {
  mkdir -p "$SNAP" || { printf 'cannot create snapshot dir %s\n' "$SNAP" >&2; exit 2; }
  derive_status   > "$SNAP/status.txt"
  derive_diff     > "$SNAP/diff.txt"
  derive_manifest > "$SNAP/manifest.txt"
  printf '%s\n' "$TARGET" > "$SNAP/target.txt"
  printf '[SNAPSHOT] target   %s\n' "$TARGET"
  printf '[SNAPSHOT] snapshot %s\n' "$SNAP"
  printf '[SNAPSHOT] %s porcelain lines, %s diff lines, %s manifest paths\n' \
    "$(wc -l < "$SNAP/status.txt" | tr -d ' ')" \
    "$(wc -l < "$SNAP/diff.txt" | tr -d ' ')" \
    "$(wc -l < "$SNAP/manifest.txt" | tr -d ' ')"
}

# $1 = "allow" (exempt the declared artifacts) | "strict" (exempt nothing)
do_verify() {
  local mode="${1:-allow}"
  if [ ! -f "$SNAP/manifest.txt" ]; then
    bad "snapshot present" "no snapshot at $SNAP — run 'snapshot' before the run"
    return
  fi

  local work
  work="$(mktemp -d)" || { printf 'mktemp failed\n' >&2; exit 2; }

  if [ "$mode" = "allow" ]; then
    derive_status         | filter_allowed porcelain > "$work/status.now"
    filter_allowed porcelain < "$SNAP/status.txt"    > "$work/status.pre"
    derive_manifest       | filter_allowed manifest  > "$work/manifest.now"
    filter_allowed manifest  < "$SNAP/manifest.txt"  > "$work/manifest.pre"
  else
    derive_status   > "$work/status.now";   cp "$SNAP/status.txt"   "$work/status.pre"
    derive_manifest > "$work/manifest.now"; cp "$SNAP/manifest.txt" "$work/manifest.pre"
  fi
  derive_diff > "$work/diff.now"

  if diff -q "$work/status.pre" "$work/status.now" >/dev/null 2>&1; then
    ok "git status --porcelain unchanged"
  else
    bad "git status --porcelain unchanged" \
      "$(diff "$work/status.pre" "$work/status.now" | grep -c '^[<>]' | tr -d ' ') differing line(s)"
    diff "$work/status.pre" "$work/status.now" | sed 's/^/         /'
  fi

  if diff -q "$SNAP/diff.txt" "$work/diff.now" >/dev/null 2>&1; then
    ok "git diff byte-identical"
  else
    bad "git diff byte-identical" \
      "$(diff "$SNAP/diff.txt" "$work/diff.now" | grep -c '^[<>]' | tr -d ' ') differing line(s) — a TRACKED file changed"
  fi

  if diff -q "$work/manifest.pre" "$work/manifest.now" >/dev/null 2>&1; then
    ok "sha256 path manifest unchanged"
  else
    bad "sha256 path manifest unchanged" \
      "$(diff "$work/manifest.pre" "$work/manifest.now" | grep -c '^[<>]' | tr -d ' ') differing path(s)"
    diff "$work/manifest.pre" "$work/manifest.now" | sed 's/^/         /'
  fi

  # Transcript-level expectations are real assertions that no filesystem diff can
  # settle. Report them honestly rather than silently dropping them.
  man "delegate invocations named, not run"
  man "dont-make-me-think in review mode only"
  man "artifacts enumerated in report Artifacts"
  man "no upgrade command executed"

  rm -rf "$work"
}

do_restore() {
  [ -n "$DEST" ] || { printf -- '--dest is required for restore\n' >&2; usage; }
  mkdir -p "$DEST" || { printf 'cannot create %s\n' "$DEST" >&2; exit 2; }
  DEST="$(cd "$DEST" && pwd)"

  if [ ! -f "$SNAP/manifest.txt" ]; then
    bad "snapshot present" "no snapshot at $SNAP — run 'snapshot' before the run"
    exit $fail
  fi

  # Allowlisted paths that were ALREADY there before the run belong to the target,
  # not to the run. Moving them out would leave `restore`'s strict re-verify staring
  # at a snapshot that still lists them, and report a breach that never happened.
  local pre
  pre="$(mktemp)" || { printf 'mktemp failed\n' >&2; exit 2; }
  cut -f3- "$SNAP/manifest.txt" | sed 's#^\./##' | LC_ALL=C sort > "$pre"

  local moved=0 skipped=0 p rel
  while IFS= read -r rel; do
    p="$TARGET/$rel"
    [ -e "$p" ] || [ -L "$p" ] || continue
    if grep -Fxq "$rel" "$pre"; then
      printf '[RESTORE] kept  %s (pre-existing in the snapshot)\n' "$rel"
      skipped=$((skipped + 1))
      continue
    fi
    mkdir -p "$DEST/$(dirname "$rel")"
    if mv "$p" "$DEST/$rel" 2>/dev/null; then
      printf '[RESTORE] moved %s -> %s\n' "$rel" "$DEST/$rel"
      moved=$((moved + 1))
      # rmdir only ever removes a directory that is already empty.
      rmdir -p "$(dirname "$p")" 2>/dev/null || true
    else
      bad "restore $rel" "mv failed"
    fi
  done < <(
    derive_manifest | cut -f3- | sed 's#^\./##' | while IFS= read -r rel; do
      is_allowed "$rel" && printf '%s\n' "$rel"
    done | LC_ALL=C sort | awk '
      # keep only the topmost path of any allowlisted subtree
      { keep = 1
        for (i = 1; i <= n; i++) if (index($0, kept[i] "/") == 1) { keep = 0; break }
        if (keep) { kept[++n] = $0; print } }'
  )
  rm -f "$pre"
  printf '[RESTORE] %d artifact path(s) moved out, %d pre-existing path(s) kept\n' \
    "$moved" "$skipped"
  do_verify strict
}

case "$CMD" in
  snapshot) do_snapshot ;;
  verify)   do_verify allow ;;
  restore)  do_restore ;;
  *) printf 'unknown subcommand: %s\n' "$CMD" >&2; usage ;;
esac

exit $fail
