#!/usr/bin/env bash
# Validates: codebase-modernizer's read-only contract as a DELTA against a pre-run
#            snapshot of the target repo — not as "git diff --stat is empty", which is
#            unsatisfiable on the stale, already-dirty repos this skill targets.
# Usage: scripts/eval-readonly-check.sh snapshot --target DIR [--manifest DIR]
#        scripts/eval-readonly-check.sh verify   --target DIR [--manifest DIR] [--allow PATH]...
#        scripts/eval-readonly-check.sh restore  --target DIR --dest DIR [--manifest DIR] [--allow PATH]...
set -uo pipefail

# Relative --target/--manifest/--dest must resolve against the CALLER's cwd, not this
# repo's root, or a relative --manifest silently creates a directory inside the skills
# catalog (CLAUDE.md rule 7). Capture the invocation cwd before the cd.
INVOCATION_PWD="$PWD"
ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"
cd "$ROOT"

NL='
'
TAB="$(printf '\t')"

fail=0
ok()   { printf '[CHECK] %-44s OK\n' "$1"; }
bad()  { printf '[CHECK] %-44s FAIL — %s\n' "$1" "$2"; fail=1; }
man()  { printf '[MANUAL] %-43s SKIPPED (run by operator)\n' "$1"; }

usage() {
  cat >&2 <<'USAGE'
Usage:
  eval-readonly-check.sh snapshot --target DIR [--manifest DIR]
  eval-readonly-check.sh verify   --target DIR [--manifest DIR] [--allow PATH]...
  eval-readonly-check.sh restore  --target DIR --dest DIR [--manifest DIR] [--allow PATH]...

  --target    the repo under test (must be a git work tree)
  --manifest  snapshot directory (default: $TMPDIR/eval-readonly-<name>-<hash>)
  --dest      where `restore` moves the run's artifacts
  --allow     extra declared-artifact path; repeatable. A trailing slash means a
              directory AT THE REPO ROOT and everything under it.

Exit: 0 contract held · 1 contract breach · 2 harness misuse or environment error
USAGE
  exit 2
}

# --- Declared-artifact allowlist -------------------------------------------------
# TRANSCRIBED, not invented. Every entry below is quoted from the skill's own
# contract text; the citation is the file:line it came from.
#
#   MODERNIZATION_REPORT.md  skills/codebase-modernizer/SKILL.md:279
#                            ("MODERNIZATION_REPORT.md and MODERNIZATION_PLAN.md
#                             both exist at the target repo root")
#                            also references/report-template.md:122
#   MODERNIZATION_PLAN.md    skills/codebase-modernizer/SKILL.md:279
#                            also references/report-template.md:123
#   CODE_REVIEW.md           skills/codebase-modernizer/SKILL.md:285-286
#                            ("a **declared delegate artifact** (`CODE_REVIEW.md`)")
#                            also SKILL.md:32, references/delegation-policy.md:26,
#                            references/report-template.md:124
#   obj/ .dart_tool/         skills/codebase-modernizer/SKILL.md:33-34
#   target/ .gradle/         ("**probe byproducts** (build dirs some dependency probes
#                             create, such as `obj/`, `.dart_tool/`, `target/`,
#                             `.gradle/`)")
#                            also references/dependency-audit.md:76-77
#   coverage/ dist/          skills/codebase-modernizer/references/baseline.md:30
#                            ("New *untracked* build output (`coverage/`, `dist/`,
#                             `target/`) is acceptable")
#
# Nothing else. A path outside this list appearing after the run is a contract breach
# (SKILL.md:34 "Nothing else.", SKILL.md:287 "Anything else is a contract breach").
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

# --- sha256 shim (coreutils or BSD; no third-party deps) -------------------------
if command -v sha256sum >/dev/null 2>&1; then
  sha256_of()     { sha256sum "$1" | cut -d' ' -f1; }
  sha256_string() { printf '%s' "$1" | sha256sum | cut -d' ' -f1; }
elif command -v shasum >/dev/null 2>&1; then
  sha256_of()     { shasum -a 256 "$1" | cut -d' ' -f1; }
  sha256_string() { printf '%s' "$1" | shasum -a 256 | cut -d' ' -f1; }
elif command -v openssl >/dev/null 2>&1; then
  sha256_of()     { openssl dgst -sha256 "$1" | awk '{print $NF}'; }
  sha256_string() { printf '%s' "$1" | openssl dgst -sha256 | awk '{print $NF}'; }
else
  printf 'no sha256 tool found (sha256sum, shasum, openssl)\n' >&2
  exit 2
fi

# Resolve a possibly-relative path against the caller's cwd (no filesystem access).
abs_arg() {
  case "$1" in
    /*) printf '%s\n' "$1" ;;
    *)  printf '%s/%s\n' "$INVOCATION_PWD" "$1" ;;
  esac
}

# Canonical form of an existing directory; the literal string otherwise. `pwd -P`
# resolves symlinks so /tmp and /private/tmp compare equal on macOS.
canon_dir() {
  if [ -d "$1" ]; then ( cd "$1" && pwd -P ); else printf '%s\n' "$1"; fi
}

CMD="${1:-}"
[ -n "$CMD" ] || usage
shift || true

TARGET=""
SNAP=""
DEST=""
EXTRA_ALLOW=()
need_value() {
  # $1 = remaining argc, $2 = flag name
  [ "$1" -ge 2 ] || { printf -- '%s requires a value\n' "$2" >&2; usage; }
}
while [ $# -gt 0 ]; do
  case "$1" in
    --target)   need_value $# "$1"; TARGET="$2";            shift 2 ;;
    --manifest) need_value $# "$1"; SNAP="$2";              shift 2 ;;
    --dest)     need_value $# "$1"; DEST="$2";              shift 2 ;;
    --allow)    need_value $# "$1"; EXTRA_ALLOW+=("$2");    shift 2 ;;
    -h|--help)  usage ;;
    *) printf 'unknown argument: %s\n' "$1" >&2; usage ;;
  esac
done

[ -n "$TARGET" ] || { printf -- '--target is required\n' >&2; usage; }
TARGET="$(abs_arg "$TARGET")"
if [ ! -d "$TARGET" ]; then
  printf -- '--target %s is not a directory\n' "$TARGET" >&2
  exit 2
fi
TARGET="$(cd "$TARGET" && pwd -P)"

# A non-git --target makes `git status`, `git ls-files` and `git diff` all fail to
# stderr, leaving three EMPTY derivations that compare equal to each other — three
# OKs and exit 0 while the tree changed underneath. Refuse up front, for every
# subcommand (restore derives a manifest before it ever reaches do_verify).
if ! git -C "$TARGET" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  printf -- '--target %s is not a git work tree\n' "$TARGET" >&2
  exit 2
fi

[ -z "$SNAP" ] || SNAP="$(abs_arg "$SNAP")"
[ -z "$DEST" ] || DEST="$(abs_arg "$DEST")"
# basename alone collides: /a/repo and /b/repo would share one snapshot directory.
[ -n "$SNAP" ] || SNAP="${TMPDIR:-/tmp}/eval-readonly-$(basename "$TARGET")-$(sha256_string "$TARGET" | cut -c1-12)"

ALLOW=("${DEFAULT_ALLOW[@]}")
if [ "${#EXTRA_ALLOW[@]}" -gt 0 ]; then
  ALLOW+=("${EXTRA_ALLOW[@]}")
fi

# --- allowlist matching ----------------------------------------------------------
# is_allowed MODE PATH
#
# A trailing-slash entry means a directory AT THE REPO ROOT and everything under it.
# It is deliberately NOT matched at arbitrary depth: `*/dist/*` would let a delegate
# drop `src/dist/evil.js` into the source tree and still pass. Per-project build dirs
# (dotnet writes an `obj/` beside every .csproj — dependency-audit.md:76) therefore
# need an explicit `--allow path/to/obj/`.
#
# MODE distinguishes the two callers:
#   porcelain — `git status --porcelain` collapses a wholly-new directory to a single
#               `?? coverage/` entry, so the BARE name must match there.
#   manifest  — enumerates files. A bare name here is a FILE literally called `dist`
#               or `target`, which the contract text never blesses (it names build
#               *directories*), so the bare name must NOT match.
#
# A plain entry matches that path at the repo root only, which is where the contract
# places the two reports and CODE_REVIEW.md (SKILL.md:279-286).
is_allowed() {
  local mode="$1" p="${2#./}" a d
  [ -z "$p" ] && return 1
  [ "$p" = "." ] && return 1
  for a in "${ALLOW[@]}"; do
    case "$a" in
      */)
        d="${a%/}"
        case "$p" in
          "$d"/*) return 0 ;;
        esac
        if [ "$mode" = "porcelain" ] && [ "$p" = "$d" ]; then
          return 0
        fi
        ;;
      *)
        [ "$p" = "$a" ] && return 0
        ;;
    esac
  done
  return 1
}

# Reads a stream on stdin, drops every line whose path field is allowlisted.
# mode=manifest → tab-separated manifest (kind, hash, path). mode=porcelain → git status.
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
    is_allowed "$mode" "$path" || printf '%s\n' "$line"
  done
}

# --- the three derivations -------------------------------------------------------
derive_status() { git -C "$TARGET" status --porcelain; }
derive_diff()   { git -C "$TARGET" diff; }

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
#
# `-z` is load-bearing. Without it git C-quotes any path holding non-ASCII bytes,
# a newline, a quote or a backslash (core.quotePath defaults to true), the `[ -e ]`
# test on the quoted literal `"caf\303\251.txt"` fails, and the real path never
# reaches the manifest — in snapshot OR verify, so modifying it passes silently.
#
# Output line format is UNCHANGED (kind \t hash \t path) and paths are emitted in
# LC_ALL=C order, so a snapshot taken by an earlier revision stays readable.
derive_manifest() {
  local paths rc
  paths="$(mktemp)" || { printf 'mktemp failed\n' >&2; return 2; }
  (
    cd "$TARGET" || exit 2
    git ls-files -z --cached --others --exclude-standard |
      while IFS= read -r -d '' p; do
        # A tab or newline cannot be represented in this line-oriented format.
        # Refuse loudly rather than emit a manifest that silently mis-parses.
        case "$p" in
          *"$NL"*|*"$TAB"*)
            printf 'manifest: path contains a newline or tab, cannot be represented: %s\n' "$p" >&2
            exit 3 ;;
        esac
        printf '%s\n' "$p"
      done
  ) > "$paths"
  rc=$?
  [ "$rc" -eq 0 ] || { rm -f "$paths"; return "$rc"; }

  LC_ALL=C sort "$paths" -o "$paths" || { rm -f "$paths"; return 2; }

  (
    cd "$TARGET" || exit 2
    while IFS= read -r p; do
      if [ -L "$p" ]; then
        printf 'symlink\t%s\t%s\n' "$(readlink "$p")" "$p"
      elif [ -d "$p" ]; then
        printf 'dir\t-\t%s\n' "$p"
      elif [ -f "$p" ]; then
        h="$(sha256_of "$p")" || {
          printf 'manifest: listed path %s cannot be read\n' "$p" >&2
          exit 3
        }
        printf 'file\t%s\t%s\n' "$h" "$p"
      elif [ -e "$p" ]; then
        printf 'other\t-\t%s\n' "$p"
      else
        # Tracked-but-deleted (or unstattable) — recorded, never skipped. Dropping
        # it silently is how a path disappears from both sides of the comparison.
        printf 'missing\t-\t%s\n' "$p"
      fi
    done < "$paths"
  )
  rc=$?
  rm -f "$paths"
  return "$rc"
}

derive_manifest_or_die() {
  derive_manifest || { printf 'manifest derivation failed\n' >&2; exit 2; }
}

# Splits a unified diff read on stdin into $1/<n>.part files, printing "<n>\t<path>"
# per file section on stdout. Used to compare a stored diff against a fresh one
# per-path, so an allowlisted TRACKED artifact (a MODERNIZATION_REPORT.md that was
# already committed) can be exempted without touching the stored diff.txt format.
split_diff() {
  awk -v dir="$1" '
    /^diff --git / {
      n++
      line = $0
      sub(/^diff --git a\//, "", line)
      i = index(line, " b/")
      p = (i > 0) ? substr(line, i + 3) : line
      print n "\t" p
    }
    n > 0 { print > (dir "/" n ".part") }
  '
}

# Writes to $2 the concatenation of every section of diff file $1 whose path is NOT
# allowlisted, preserving git's own section order.
filter_diff() {
  local src="$1" out="$2" dir idx n p
  dir="$(mktemp -d)" || { printf 'mktemp failed\n' >&2; exit 2; }
  idx="$dir/index"
  split_diff "$dir" < "$src" > "$idx"
  : > "$out"
  while IFS="$TAB" read -r n p; do
    [ -n "${n:-}" ] || continue
    is_allowed manifest "$p" && continue
    cat "$dir/$n.part" >> "$out"
  done < "$idx"
  rm -rf "$dir"
}

do_snapshot() {
  mkdir -p "$SNAP" || { printf 'cannot create snapshot dir %s\n' "$SNAP" >&2; exit 2; }
  derive_status > "$SNAP/status.txt" || { printf 'git status failed on %s\n' "$TARGET" >&2; exit 2; }
  derive_diff   > "$SNAP/diff.txt"   || { printf 'git diff failed on %s\n' "$TARGET" >&2; exit 2; }
  derive_manifest > "$SNAP/manifest.txt" || { printf 'manifest derivation failed on %s\n' "$TARGET" >&2; exit 2; }
  printf '%s\n' "$TARGET" > "$SNAP/target.txt"

  local paths
  paths="$(wc -l < "$SNAP/manifest.txt" | tr -d ' ')"
  # An empty manifest means git enumerated nothing. On a real target that is an
  # environment failure, not a statistic: every later comparison would be
  # empty-against-empty and report OK no matter what changed.
  if [ "$paths" -eq 0 ]; then
    printf 'snapshot of %s enumerated 0 paths — refusing to record a vacuous snapshot\n' "$TARGET" >&2
    exit 2
  fi

  printf '[SNAPSHOT] target   %s\n' "$TARGET"
  printf '[SNAPSHOT] snapshot %s\n' "$SNAP"
  printf '[SNAPSHOT] %s porcelain lines, %s diff lines, %s manifest paths\n' \
    "$(wc -l < "$SNAP/status.txt" | tr -d ' ')" \
    "$(wc -l < "$SNAP/diff.txt" | tr -d ' ')" \
    "$paths"
}

# $1 = "allow" (exempt the declared artifacts) | "strict" (exempt nothing)
do_verify() {
  local mode="${1:-allow}"
  if [ ! -f "$SNAP/manifest.txt" ]; then
    bad "snapshot present" "no snapshot at $SNAP — run 'snapshot' before the run"
    return
  fi

  # target.txt is written by `snapshot` precisely so a snapshot cannot be verified
  # against a different repo. Comparing canonical forms keeps /tmp vs /private/tmp
  # from reading as a mismatch.
  if [ -f "$SNAP/target.txt" ]; then
    local recorded
    recorded="$(head -n 1 "$SNAP/target.txt")"
    if [ "$(canon_dir "$recorded")" != "$TARGET" ]; then
      printf 'snapshot %s was taken against %s, not %s\n' "$SNAP" "$recorded" "$TARGET" >&2
      exit 2
    fi
  else
    printf 'snapshot %s has no target.txt — refusing to verify a snapshot of unknown provenance\n' "$SNAP" >&2
    exit 2
  fi

  local work
  work="$(mktemp -d)" || { printf 'mktemp failed\n' >&2; exit 2; }

  derive_diff > "$work/diff.now" || { printf 'git diff failed on %s\n' "$TARGET" >&2; exit 2; }

  local diff_name diff_pre diff_now
  if [ "$mode" = "allow" ]; then
    derive_status | filter_allowed porcelain > "$work/status.now" \
      || { printf 'git status failed on %s\n' "$TARGET" >&2; exit 2; }
    filter_allowed porcelain < "$SNAP/status.txt" > "$work/status.pre"
    derive_manifest_or_die | filter_allowed manifest > "$work/manifest.now"
    filter_allowed manifest < "$SNAP/manifest.txt" > "$work/manifest.pre"
    # A declared artifact that is already TRACKED (a MODERNIZATION_REPORT.md
    # committed by a previous audit) shows up in `git diff`, not in the untracked
    # sets. Comparing raw diffs would FAIL on a write the contract permits.
    diff_name="git diff unchanged outside allowlist"
    filter_diff "$SNAP/diff.txt"  "$work/diff.pre.f"
    filter_diff "$work/diff.now"  "$work/diff.now.f"
    diff_pre="$work/diff.pre.f"; diff_now="$work/diff.now.f"
  else
    derive_status > "$work/status.now" \
      || { printf 'git status failed on %s\n' "$TARGET" >&2; exit 2; }
    cp "$SNAP/status.txt" "$work/status.pre"
    derive_manifest_or_die > "$work/manifest.now"
    cp "$SNAP/manifest.txt" "$work/manifest.pre"
    diff_name="git diff byte-identical"
    diff_pre="$SNAP/diff.txt"; diff_now="$work/diff.now"
  fi

  if diff -q "$work/status.pre" "$work/status.now" >/dev/null 2>&1; then
    ok "git status --porcelain unchanged"
  else
    bad "git status --porcelain unchanged" \
      "$(diff "$work/status.pre" "$work/status.now" | grep -c '^[<>]' | tr -d ' ') differing line(s)"
    diff "$work/status.pre" "$work/status.now" | sed 's/^/         /'
  fi

  if diff -q "$diff_pre" "$diff_now" >/dev/null 2>&1; then
    ok "$diff_name"
  else
    bad "$diff_name" \
      "$(diff "$diff_pre" "$diff_now" | grep -c '^[<>]' | tr -d ' ') differing line(s) — a TRACKED file changed"
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
  DEST="$(cd "$DEST" && pwd -P)"

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

  local candidates now
  candidates="$(mktemp)" || { printf 'mktemp failed\n' >&2; exit 2; }
  now="$(mktemp)" || { printf 'mktemp failed\n' >&2; exit 2; }
  derive_manifest > "$now" || { printf 'manifest derivation failed\n' >&2; exit 2; }
  cut -f3- "$now" | sed 's#^\./##' | while IFS= read -r rel; do
      is_allowed manifest "$rel" && printf '%s\n' "$rel"
      true
    done | LC_ALL=C sort | awk '
      # keep only the topmost path of any allowlisted subtree
      { keep = 1
        for (i = 1; i <= n; i++) if (index($0, kept[i] "/") == 1) { keep = 0; break }
        if (keep) { kept[++n] = $0; print } }' > "$candidates"

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
  done < "$candidates"
  rm -f "$pre" "$candidates" "$now"
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
