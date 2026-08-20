# macOS setup

Self-contained: every command below is a plain Homebrew/system command or copies a file this skill ships in
`assets/`. There is no external scripts repo to clone.

## Homebrew

If `brew` is missing:

```bash
# Confirm URL with the user first
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

On Apple Silicon, add to `~/.zprofile` if the installer says so:

```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
```

Intel Homebrew lives at `/usr/local`. Use `uname -m`: `arm64` vs `x86_64`. Never install x86 brew under Rosetta unless the user is stuck on an x86-only formula.

## Baseline

```bash
brew install git curl wget
```

## Node.js LTS

```bash
brew install node
```

Or pin LTS:

```bash
brew install node@22
brew link --overwrite --force node@22
```

`brew link --overwrite` is **mutating** — it replaces whatever `node` currently resolves to. Needs its own yes.

Verify: `node -v`, `npm -v`. Optionally `corepack enable`.

## Python + uv

```bash
brew install python@3.12 uv
```

Verify: `python3 -V`, `uv --version`. Use `uv venv` for projects; do not `sudo pip3 install`.

## Zsh + Oh My Zsh

macOS ships zsh already; install only if `zsh` is genuinely missing:

```bash
brew install zsh
```

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

Then deploy `assets/zshrc-config` — it pins `ZSH_THEME="wedisagree"`, the four-plugin list, and the starship
init. **Tag depends on the machine:** additive when `~/.zshrc` is absent, **mutating** (backup + its own yes)
when one already exists. See `optimize.md#oh-my-zsh-missing`.

`chsh` may require a password; setup is still a success if zsh + omz exist.

### Starship prompt

`assets/zshrc-config` runs `eval "$(starship init zsh)"` **only** `if command -v starship` — so without the binary the prompt silently degrades to the bare Oh My Zsh theme. Install it:

```bash
brew install starship
```

Then deploy the config the init line reads (`optimize.md#starship-config-missing`, or
`#starship-config-not-managed` when a `~/.config/starship.toml` already exists — that one is mutating and
needs its own yes).

Verify: `starship --version`, then `head -n1 ~/.config/starship.toml`.

## Optional (only if asked)

- Docker Desktop: `brew install --cask docker`
- Xcode CLT: `xcode-select --install` if compile tools are missing

## Agent CLIs

See `agent-clis.md`. On Apple Silicon, npm global bins go under `/opt/homebrew` or `$(npm prefix -g)/bin` — ensure that directory is on PATH.
