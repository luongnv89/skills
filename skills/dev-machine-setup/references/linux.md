# Linux setup

Self-contained: every command below is a native package-manager command or copies a file this skill ships in
`assets/`. There is no external scripts repo to clone.

Tables cover **Debian/Ubuntu (apt), Fedora (dnf), Arch (pacman)**. On any other distro, use the same *intent*
with that distro's manager and say so in the report rather than guessing a package name.

## Package manager

| Distro | Install |
|--------|---------|
| Debian/Ubuntu | `sudo apt-get update && sudo apt-get install -y git curl wget vim build-essential` |
| Fedora | `sudo dnf install -y git curl wget vim gcc gcc-c++ make` |
| Arch | `sudo pacman -Syu --needed git curl wget vim base-devel` |

## Node.js LTS

**Debian/Ubuntu** — NodeSource LTS (**mutating**: pipes a remote script to bash; confirm the URL first):

```bash
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**Fedora:** `sudo dnf module install -y nodejs:lts` or NodeSource's rpm script (same review rule).

**Arch:** `sudo pacman -S --needed nodejs npm`.

Prefer one Node. If `nvm`/`fnm` already exists, use it instead of adding a second copy.

## Python

| Distro | Install |
|--------|---------|
| Debian/Ubuntu | `sudo apt-get install -y python3 python3-pip python3-venv` |
| Fedora | `sudo dnf install -y python3 python3-pip` |
| Arch | `sudo pacman -S --needed python python-pip` |

Then **uv** (do not `pip install` into the system interpreter — PEP 668). Arch and Fedora package it:

```bash
sudo pacman -S --needed uv      # Arch
sudo dnf install -y uv          # Fedora
```

Elsewhere, the installer (**mutating** — `curl | sh`; confirm the URL first):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify: `python3 --version`, `uv --version`.

## Zsh + Oh My Zsh

| Distro | Install |
|--------|---------|
| Debian/Ubuntu | `sudo apt-get install -y zsh` |
| Fedora | `sudo dnf install -y zsh` |
| Arch | `sudo pacman -S --needed zsh` |

Oh My Zsh framework (**additive** — the installer creates `~/.zshrc` only when absent):

```bash
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
```

Plugins — the three the shipped config expects, cloned into `$ZSH_CUSTOM`:

```bash
ZSH_CUSTOM="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"
git clone https://github.com/zsh-users/zsh-syntax-highlighting.git "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting" 2>/dev/null || git -C "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting" pull --ff-only
git clone https://github.com/zsh-users/zsh-autosuggestions.git "$ZSH_CUSTOM/plugins/zsh-autosuggestions" 2>/dev/null || git -C "$ZSH_CUSTOM/plugins/zsh-autosuggestions" pull --ff-only
git clone https://github.com/zsh-users/zsh-completions.git "$ZSH_CUSTOM/plugins/zsh-completions" 2>/dev/null || git -C "$ZSH_CUSTOM/plugins/zsh-completions" pull --ff-only
```

Then deploy `assets/zshrc-config`, which pins `ZSH_THEME="wedisagree"`, the four-plugin list, and a
`command -v starship`-guarded prompt init. **Tag depends on the machine:** additive when `~/.zshrc` is absent,
**mutating** (backup + its own yes) when one already exists. See `optimize.md#oh-my-zsh-missing`.

Making zsh the login shell is `optimize.md#login-shell-not-zsh` (`chsh`). Works on WSL.

### Starship prompt

Because that init line is guarded, a missing binary produces no prompt at all rather than an error:

| Distro | Install |
|--------|---------|
| Debian/Ubuntu | `sudo apt-get install -y starship` (older releases lack it — fall back to the installer below) |
| Fedora | `sudo dnf install -y starship` |
| Arch | `sudo pacman -S --needed starship` |

Fallback where no distro package exists (**mutating** — `curl | sh`; confirm the URL first):

```bash
curl -sS https://starship.rs/install.sh | sh
```

Then deploy the config (`optimize.md#starship-config-missing`). Arch spins such as Omarchy ship their **own** `~/.config/starship.toml` — that fires `starship-config-not-managed`, which is mutating and needs a per-item yes plus a backup.

Verify: `starship --version`, then `head -n1 ~/.config/starship.toml`.

## Arch notes

| Arch | Notes |
|------|--------|
| `x86_64` | Default NodeSource / distro packages |
| `aarch64` / `arm64` | Use distro aarch64 packages. NodeSource supports arm64; confirm the setup script's arch list if it fails |
| `riscv64` | Distro packages only; skip NodeSource |

## Optional (only if asked)

Docker, C/C++ toolchains, SSH keys, MongoDB — install from the distro's own packages; this skill does not
bundle recipes for them.

## Agent CLIs

See `agent-clis.md`. Global npm prefix: `npm prefix -g` must be on PATH (often `~/.npm-global` if the user cannot write `/usr/lib`).
