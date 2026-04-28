# install.sh Template

Use this as the skeleton for the generated `install.sh`. Customise the `install_<tool>` function and dependency list per target.

```bash
#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# <Software Name> Installer
# Usage: curl -sSL https://raw.githubusercontent.com/<owner>/<repo>/<branch>/install.sh | bash
# ============================================================================

# --- Configuration ---
TOOL_NAME="<software_name>"
REPO_OWNER="<owner>"
REPO_NAME="<repo>"
DEFAULT_BRANCH="<branch>"
INSTALL_PREFIX="${INSTALL_PREFIX:-/usr/local}"

# --- Color Output ---
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; NC='\033[0m'

info()  { printf "${BLUE}[INFO]${NC}  %s\n" "$*"; }
ok()    { printf "${GREEN}[ OK ]${NC}  %s\n" "$*"; }
warn()  { printf "${YELLOW}[WARN]${NC}  %s\n" "$*"; }
err()   { printf "${RED}[ERR ]${NC}  %s\n" "$*" >&2; }
die()   { err "$@"; exit 1; }
```

## Detection helpers

```bash
detect_os() {
    local os; os="$(uname -s | tr '[:upper:]' '[:lower:]')"
    case "$os" in
        linux*)  echo "linux" ;;
        darwin*) echo "macos" ;;
        mingw*|msys*|cygwin*) echo "windows" ;;
        *)       die "Unsupported operating system: $os" ;;
    esac
}

detect_arch() {
    local arch; arch="$(uname -m)"
    case "$arch" in
        x86_64|amd64)  echo "x86_64" ;;
        aarch64|arm64) echo "arm64" ;;
        armv7l)        echo "armv7" ;;
        *)             die "Unsupported architecture: $arch" ;;
    esac
}

detect_package_manager() {
    if   command -v apt-get &>/dev/null; then echo "apt"
    elif command -v dnf     &>/dev/null; then echo "dnf"
    elif command -v yum     &>/dev/null; then echo "yum"
    elif command -v pacman  &>/dev/null; then echo "pacman"
    elif command -v brew    &>/dev/null; then echo "brew"
    elif command -v zypper  &>/dev/null; then echo "zypper"
    else echo "unknown"
    fi
}

need_sudo() {
    if [ "$(id -u)" -ne 0 ]; then
        command -v sudo &>/dev/null && echo "sudo" \
            || die "Requires root. Run as root or install sudo."
    else
        echo ""
    fi
}
```

## Dependency installer

```bash
install_deps() {
    local pm="$1" sudo_cmd="$2"; shift 2; local deps=("$@")
    [ ${#deps[@]} -eq 0 ] && return 0
    info "Installing dependencies: ${deps[*]}"
    case "$pm" in
        apt)    $sudo_cmd apt-get update -qq && $sudo_cmd apt-get install -y -qq "${deps[@]}" ;;
        dnf)    $sudo_cmd dnf install -y -q "${deps[@]}" ;;
        yum)    $sudo_cmd yum install -y -q "${deps[@]}" ;;
        pacman) $sudo_cmd pacman -Sy --noconfirm "${deps[@]}" ;;
        brew)   brew install "${deps[@]}" ;;
        zypper) $sudo_cmd zypper install -y "${deps[@]}" ;;
        *)      die "Unsupported package manager '$pm'" ;;
    esac
    ok "Dependencies installed"
}
```

## Main entry point

```bash
install_<tool>() {
    # Tool-specific install steps. Customise per target.
    :
}

verify_installation() {
    info "Verifying installation..."
    if command -v "$TOOL_NAME" &>/dev/null; then
        ok "$TOOL_NAME $(${TOOL_NAME} --version 2>/dev/null || echo '') installed"
    else
        die "$TOOL_NAME installation could not be verified"
    fi
}

main() {
    info "Installing $TOOL_NAME"
    local os arch pm sudo_cmd
    os="$(detect_os)"; arch="$(detect_arch)"
    pm="$(detect_package_manager)"; sudo_cmd="$(need_sudo)"
    info "OS: $os | Arch: $arch | Package Manager: $pm"
    # install_deps "$pm" "$sudo_cmd" dep1 dep2
    install_<tool>
    verify_installation
    ok "Installation complete!"
}

main "$@"
```

## Script requirements checklist

- Starts with `#!/usr/bin/env bash` and `set -euo pipefail`.
- Self-contained; no external script dependencies.
- Auto-detects OS (Linux/macOS/Windows-MSYS), architecture, and package manager.
- Handles `sudo` gracefully with a clear error if unavailable.
- Uses colored output for readability.
- Verifies the installation at the end.
- Exits non-zero on any failure.
- Includes the one-liner command in the header comment.
- Honours `INSTALL_PREFIX` env override where applicable.
