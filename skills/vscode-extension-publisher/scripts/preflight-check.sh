#!/usr/bin/env bash
# Pre-flight check for VS Code extension publishing
# Validates environment, tools, and package.json before publishing

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; ERRORS=$((ERRORS + 1)); }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; WARNINGS=$((WARNINGS + 1)); }

echo "=== VS Code Extension Publishing Pre-flight Check ==="
echo ""

# --- Check Node.js ---
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    NODE_MAJOR=$(echo "$NODE_VERSION" | sed 's/v//' | cut -d. -f1)
    if [ "$NODE_MAJOR" -ge 18 ]; then
        pass "Node.js $NODE_VERSION"
    else
        fail "Node.js $NODE_VERSION found but v18+ is required"
    fi
else
    fail "Node.js is not installed (install from https://nodejs.org)"
fi

# --- Check npm ---
if command -v npm &> /dev/null; then
    pass "npm $(npm --version)"
else
    fail "npm is not installed"
fi

# --- Check vsce ---
if command -v vsce &> /dev/null; then
    pass "vsce $(vsce --version)"
else
    warn "@vscode/vsce not found globally"
    echo "     Install with: npm install -g @vscode/vsce"
fi

# --- Check package.json exists ---
echo ""
echo "--- Checking package.json ---"

if [ ! -f "package.json" ]; then
    fail "package.json not found in current directory"
    echo ""
    echo "=== Pre-flight check complete: $ERRORS error(s), $WARNINGS warning(s) ==="
    exit 1
fi

pass "package.json found"

# --- Validate required fields ---
check_field() {
    local field="$1"
    local value
    value=$(node -e "
        const pkg = require('./package.json');
        const parts = '$field'.split('.');
        let val = pkg;
        for (const p of parts) { val = val ? val[p] : undefined; }
        if (val !== undefined && val !== null && val !== '') {
            console.log(typeof val === 'object' ? JSON.stringify(val) : val);
        }
    " 2>/dev/null || true)

    if [ -n "$value" ]; then
        pass "$field: $value"
    else
        fail "$field is missing or empty"
    fi
}

REQUIRED_FIELDS=("name" "displayName" "description" "version" "publisher" "engines.vscode")

for field in "${REQUIRED_FIELDS[@]}"; do
    check_field "$field"
done

# --- Check categories ---
CATEGORIES=$(node -e "
    const pkg = require('./package.json');
    if (Array.isArray(pkg.categories) && pkg.categories.length > 0) {
        console.log(pkg.categories.join(', '));
    }
" 2>/dev/null || true)

if [ -n "$CATEGORIES" ]; then
    pass "categories: $CATEGORIES"
else
    warn "categories is missing (recommended for marketplace discoverability)"
fi

# --- Check icon ---
echo ""
echo "--- Checking assets ---"

ICON=$(node -e "const pkg = require('./package.json'); if (pkg.icon) console.log(pkg.icon);" 2>/dev/null || true)

if [ -n "$ICON" ]; then
    if [[ "$ICON" == *.svg ]]; then
        fail "Icon is SVG — marketplace requires PNG (min 128x128px)"
    elif [ -f "$ICON" ]; then
        pass "Icon: $ICON"
    else
        fail "Icon file not found: $ICON"
    fi
else
    warn "No icon specified (recommended for marketplace presence)"
fi

# --- Check README ---
if [ -f "README.md" ]; then
    pass "README.md found"
else
    warn "README.md not found (used as marketplace homepage)"
fi

# --- Check LICENSE ---
if [ -f "LICENSE" ] || [ -f "LICENSE.md" ] || [ -f "LICENSE.txt" ]; then
    pass "LICENSE file found"
else
    LICENSE_FIELD=$(node -e "const pkg = require('./package.json'); if (pkg.license) console.log(pkg.license);" 2>/dev/null || true)
    if [ -n "$LICENSE_FIELD" ]; then
        pass "License in package.json: $LICENSE_FIELD"
    else
        warn "No LICENSE file or license field in package.json"
    fi
fi

# --- Check keywords count ---
KEYWORD_COUNT=$(node -e "
    const pkg = require('./package.json');
    if (Array.isArray(pkg.keywords)) console.log(pkg.keywords.length);
    else console.log(0);
" 2>/dev/null || true)

if [ "$KEYWORD_COUNT" -gt 30 ]; then
    fail "Too many keywords ($KEYWORD_COUNT) — maximum is 30"
elif [ "$KEYWORD_COUNT" -gt 0 ]; then
    pass "Keywords: $KEYWORD_COUNT entries"
fi

# --- Summary ---
echo ""
echo "========================================="
if [ "$ERRORS" -eq 0 ]; then
    echo -e "${GREEN}Pre-flight check passed!${NC} ($WARNINGS warning(s))"
    echo "Ready to package: vsce package"
    echo "Ready to publish: vsce publish"
    exit 0
else
    echo -e "${RED}Pre-flight check failed: $ERRORS error(s), $WARNINGS warning(s)${NC}"
    echo "Fix the errors above before publishing."
    exit 1
fi
