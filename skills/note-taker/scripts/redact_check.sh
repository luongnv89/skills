#!/usr/bin/env bash
set -euo pipefail

# Simple redaction preflight (best-effort).
# Usage: redact_check.sh <file>

FILE=${1:-}
if [[ -z "$FILE" || ! -f "$FILE" ]]; then
  echo "Usage: $0 <file>" >&2
  exit 2
fi

# Common secret-ish patterns (tuned to reduce false positives)
PATTERNS=(
  'AKIA[0-9A-Z]{16}'
  'ASIA[0-9A-Z]{16}'
  '-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----'
  'sk-(live|test|proj)-[0-9A-Za-z]+'
  'xox[baprs]-[0-9A-Za-z-]+'
  '(?i)(api_key|apikey|secret|token|password)\s*[:=]\s*[^\s]+'
)

found=0
for p in "${PATTERNS[@]}"; do
  if grep -P -n "$p" "$FILE" >/dev/null 2>&1; then
    echo "[WARN] Potential secret pattern: $p" >&2
    grep -P -n "$p" "$FILE" | head -n 5 >&2 || true
    found=1
  fi
done

if [[ $found -eq 1 ]]; then
  echo "[WARN] Potential secrets detected in $FILE. Redact before commit." >&2
  exit 3
fi

echo "[OK] No obvious secret patterns found in $FILE" >&2
