# Linux setup

inbash Unix scripts target **Debian/Ubuntu** (`apt`). On Fedora/RHEL/Arch, use the same *intent* with the native package manager — do not run the `.sh` files blindly.

Clone when apt-based:

```bash
git clone https://github.com/luongnv89/inbash.git
cd inbash
```

## Package manager

| Distro | Install |
|--------|---------|
| Debian/Ubuntu | `sudo apt-get update && sudo apt-get install -y git curl wget vim build-essential` or `./unix/basic.sh --yes` |
| Fedora | `sudo dnf install -y git curl wget vim gcc gcc-c++ make` |
| Arch | `sudo pacman -Syu --needed git curl wget vim base-devel` |

## Node.js LTS

**Debian/Ubuntu (inbash):**

```bash
./unix/nodejs.sh --yes
```

Uses NodeSource `setup_lts.x`. Review the downloaded setup script if the user is cautious.

**Fedora:** `sudo dnf module install -y nodejs:lts` or NodeSource's rpm script (same review rule).

**Arch:** `sudo pacman -S nodejs npm`.

Prefer one Node. If `nvm`/`fnm` already exists, use it instead of adding a second copy.

## Python

**Debian/Ubuntu (inbash):**

```bash
./unix/python3-pip.sh --yes
```

Then **uv** (do not `pip install` into the system interpreter — PEP 668):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Confirm the URL first. Verify: `python3 --version`, `uv --version`.

**Fedora:** `sudo dnf install -y python3 python3-pip` then uv.
**Arch:** `sudo pacman -S python python-pip` then uv.

## Zsh + Oh My Zsh

```bash
./install-zsh.sh --yes --set-default
./setup-ohMyZsh.sh --yes
```

`install-zsh.sh` already switches on apt/dnf/yum/pacman/apk/zypper. Works on WSL.

## Arch notes

| Arch | Notes |
|------|--------|
| `x86_64` | Default NodeSource / distro packages |
| `aarch64` / `arm64` | Use distro aarch64 packages. NodeSource supports arm64; confirm the setup script's arch list if it fails |
| `riscv64` | Distro packages only; skip NodeSource |

## Optional (only if asked)

inbash: `unix/docker.sh`, `unix/c_cpp.sh`, `unix/setup-ssh.sh`, `unix/install-mongodb.sh`.

## Agent CLIs

See `agent-clis.md`. Global npm prefix: `npm prefix -g` must be on PATH (often `~/.npm-global` if the user cannot write `/usr/lib`).
