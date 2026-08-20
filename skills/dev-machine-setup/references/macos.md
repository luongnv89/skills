# macOS setup

Prefer [inbash](https://github.com/luongnv89/inbash) mac scripts. Clone once:

```bash
git clone https://github.com/luongnv89/inbash.git ~/.inbash 2>/dev/null || git -C ~/.inbash pull --ff-only
```

Every inbash command below then runs from any directory via its `~/.inbash/` path.

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

inbash:

```bash
~/.inbash/mac/nodejs.sh --yes --formula node
```

Or pin LTS:

```bash
~/.inbash/mac/nodejs.sh --yes --formula node@22 --force-link
```

Verify: `node -v`, `npm -v`. Optionally `corepack enable`.

## Python + uv

inbash (Homebrew `python@3.12`, pip, **uv**):

```bash
~/.inbash/mac/python-pip-uv.sh --yes --python-formula python@3.12
```

Verify: `python3 -V`, `uv --version`. Use `uv venv` for projects; do not `sudo pip3 install`.

## Zsh + Oh My Zsh

```bash
~/.inbash/install-zsh.sh --yes --set-default
~/.inbash/setup-ohMyZsh.sh --yes
```

`setup-ohMyZsh.sh` installs `zsh-syntax-highlighting`, `zsh-autosuggestions`, `zsh-completions` and deploys inbash `zshrc-config`. If the user already has a custom `~/.zshrc`, skip the config copy and only add plugins.

`chsh` may require a password; setup is still a success if zsh + omz exist.

## Optional (only if asked)

- Docker Desktop: `~/.inbash/mac/docker.sh --yes`
- Xcode CLT: `xcode-select --install` if compile tools are missing

## Agent CLIs

See `agent-clis.md`. On Apple Silicon, npm global bins go under `/opt/homebrew` or `$(npm prefix -g)/bin` — ensure that directory is on PATH.
