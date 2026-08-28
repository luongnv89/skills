#!/usr/bin/env bash
# Scan a live URL for agent readiness. Writes scan.json (structured) and fixes.md
# (remediation prose) into the output directory.
#
# Usage: scan_site.sh <url> [outdir]
set -euo pipefail

API="https://isitagentready.com/api/scan"
url="${1:-}"
outdir="${2:-.agent-ready}"

if [ -z "$url" ]; then
  echo "✗ usage: scan_site.sh <url> [outdir]" >&2
  exit 2
fi

case "$url" in
  http://*|https://*) ;;
  *) echo "✗ url must start with http:// or https:// — got: $url" >&2; exit 2 ;;
esac

for bin in curl python3; do
  command -v "$bin" >/dev/null 2>&1 || { echo "✗ required tool not found: $bin" >&2; exit 1; }
done

mkdir -p "$outdir"

# Build the request body with python3 so the URL is never typed into shell/JSON syntax.
body="$(URL="$url" python3 -c 'import json,os; print(json.dumps({"url": os.environ["URL"]}))')"
body_agent="$(URL="$url" python3 -c 'import json,os; print(json.dumps({"url": os.environ["URL"], "format": "agent"}))')"

echo "→ scanning $url (structured) ..." >&2
code="$(curl -sS --max-time 120 -X POST "$API" \
  -H 'Content-Type: application/json' \
  --data-binary "$body" \
  -o "$outdir/scan.json" -w '%{http_code}')"

if [ "$code" != "200" ]; then
  echo "✗ scan failed: HTTP $code" >&2
  head -c 400 "$outdir/scan.json" >&2 || true
  echo >&2
  echo "  The scanner must be able to reach the site publicly. Check the URL is live and not firewalled." >&2
  exit 1
fi

python3 -c "
import json,sys
d=json.load(open('$outdir/scan.json'))
if 'level' not in d or 'checks' not in d:
    print('✗ unexpected response shape: missing level/checks', file=sys.stderr); sys.exit(1)
" || exit 1

echo "→ scanning $url (remediation prose) ..." >&2
code="$(curl -sS --max-time 120 -X POST "$API" \
  -H 'Content-Type: application/json' \
  --data-binary "$body_agent" \
  -o "$outdir/fixes.md" -w '%{http_code}')"

if [ "$code" != "200" ]; then
  echo "⚠ agent-format request failed (HTTP $code) — falling back to nextLevel prompts only" >&2
  : > "$outdir/fixes.md"
fi

echo "✓ wrote $outdir/scan.json and $outdir/fixes.md" >&2
