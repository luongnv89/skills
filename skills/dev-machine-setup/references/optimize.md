# Optimize an existing setup

Fix catalog for the `findings[]` array emitted by `scripts/detect_env.py`. Each finding carries a
`fix_ref` pointing at the matching heading below.

Every fix is tagged **additive** (adds something absent — batch-approvable) or **mutating** (changes an
install or config that already works — needs a per-item yes, per `approvals.md` § Human-in-the-loop).

**Before any in-place rc-file edit**, back the file up and show the user the path:

```bash
cp ~/.zshrc ~/.zshrc.bak.$(date +%Y%m%d%H%M%S)   # or ~/.zprofile, ~/.bashrc
```

Windows equivalent: `Copy-Item $PROFILE "$PROFILE.bak"`.

Every command here reaches the user as a **run-block** — `approvals.md` § Presenting commands. Inspect blocks stay
separate from fix blocks, nothing assumes a working directory, and any value that has to come from the user
is collected *before* the block is shown, never left as a `<placeholder>`.

---

## no-package-manager

**additive.** Nothing installs until a manager exists.

macOS — Homebrew (*you run this*: the installer prompts for your password):

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Linux: the distro's manager is already present unless the image is minimal (`linux.md`).

Windows — install **App Installer** from the Microsoft Store (*you run this*: Store GUI), then verify:

```powershell
winget --version
```

## npm-global-bin-not-on-path

**mutating** (edits a shell rc). This is the single most common cause of "installed it, command not
found" — the CLI is on disk but the shim directory is invisible.

Inspect — where npm actually puts global binaries:

```bash
npm prefix -g
```

Persist (mutating; backs the rc file up first):

```bash
cp ~/.zshrc ~/.zshrc.bak.$(date +%Y%m%d%H%M%S)
echo 'export PATH="$(npm prefix -g)/bin:$PATH"' >> ~/.zshrc
```

Verify — in a *fresh* login shell, since the current one never re-reads `~/.zshrc`:

```bash
zsh -l -c 'command -v claude && claude --version'
```

Windows: add the `npm prefix -g` directory itself (no `/bin`) via
`[Environment]::SetEnvironmentVariable('Path', "$env:Path;<prefix>", 'User')`, then open a new shell.

If the prefix is a root-owned directory the user cannot write, re-point it instead of using sudo:
`npm config set prefix ~/.npm-global`, then add that bin dir as above and reinstall global packages.

## brew-bin-not-on-path

**mutating.** Homebrew is installed but its shellenv line never landed:

Persist (mutating — Intel Macs use `/usr/local/bin/brew`; confirm which with `ls /opt/homebrew/bin/brew`
before presenting the block):

```bash
cp ~/.zprofile ~/.zprofile.bak.$(date +%Y%m%d%H%M%S) 2>/dev/null || true
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
```

Reload (*you run this* — it replaces your running shell):

```bash
exec zsh -l
```

## intel-homebrew-on-apple-silicon

**mutating, high effort — default to deferring.** Everything installed under `/usr/local` runs through
Rosetta. Migrating means reinstalling the formulae under `/opt/homebrew`. Report it, list what would
move (`/usr/local/bin/brew list --formula`), and only proceed if the user explicitly asks. Do not
uninstall the x86 prefix — some formulae are x86-only.

## xcode-clt-missing

**additive.** Native builds, many Homebrew formulae, and `node-gyp` fail without it.

*You run this* — it opens a GUI dialog that has to be accepted:

```bash
xcode-select --install
```

Verify:

```bash
xcode-select -p
```

## multiple-node-managers

**mutating.** Two or more Node sources compete for PATH, so `node -v` depends on which rc file won.
Do not uninstall anything automatically. Show the user which one is winning and let them pick:

Inspect — which Node is winning and where it comes from:

```bash
which -a node
type -a node
node -v
```

Keep the version manager if one is in active use (a `.nvmrc`/`.node-version` in their projects is the
tell); otherwise keep the package-manager Node. Removing the loser is a separate, explicitly approved
step — `brew uninstall node` or removing the manager's rc lines, never both blind.

## node-below-min

**mutating.** The floor lives in `NODE_MIN_MAJOR` in `scripts/detect_env.py`. Upgrading a runtime can
break projects pinned to the old major — say so before running anything. Upgrade through whatever
already owns Node, never by adding a second source. Pick the one block matching the owner found by
`multiple-node-managers`'s inspect:

```bash
brew upgrade node
```

```bash
nvm install --lts && nvm alias default 'lts/*'
```

```powershell
winget upgrade --id OpenJS.NodeJS.LTS
```

Distro path in `linux.md`. Verify: `node -v` and `npm -v`.

## python-below-min

**mutating.** Same rule: upgrade through the owner. Never replace the OS's own `/usr/bin/python3` on
Linux or macOS — install a newer interpreter alongside and leave the system one alone:

```bash
brew install python@3.13
```

```bash
uv python install 3.13
```

Verify: `python3 -V`, or `uv python list` for the uv-managed ones.

## python-externally-managed

**additive.** The system interpreter is PEP 668 marked, so `pip install` into it fails by design. Install
`uv` and work per-project. Never suggest `--break-system-packages`.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Homebrew alternative — `brew install uv`. Windows — `winget install --id astral-sh.uv`. Fuller per-OS
context in `macos.md`, `linux.md`, `windows.md`.

Then, in any project directory (this is the habit to hand the user, not a one-off fix):

```bash
uv venv && source .venv/bin/activate
```

## git-identity-missing

**mutating** (writes `~/.gitconfig`). The values must come from the user and never be invented — **ask for
both first, then present the block with them already filled in.** A block still containing a placeholder is
not a run-block; it makes the user edit before pasting, which is exactly what the format exists to avoid.

```bash
git config --global user.name "Ada Lovelace"
git config --global user.email "ada@example.com"
```

Verify:

```bash
git config --global --get-regexp '^user\.'
```

## path-duplicates

**mutating.** Duplicate entries mean a profile is sourced twice (commonly `.zprofile` *and* `.zshrc`
both adding the same line, or a re-entrant `exec zsh`). Show the offenders first:

Inspect — which entries repeat, and which rc file adds them twice:

```bash
echo "$PATH" | tr ':' '\n' | sort | uniq -d
grep -n 'PATH=' ~/.zshrc ~/.zprofile ~/.zshenv 2>/dev/null
time zsh -i -c exit
```

There is no generic fix command: the fix is deleting one specific line. That also makes it the one finding
whose fix is never stored for later replay — line numbers move. If the run pauses here, record the *inspect*
block and re-derive the edit on resume (`session.md` § Reconciling). Read the `grep -n` output, then
present a fix block naming that exact file and line number, after the backup above. Do not rewrite PATH
wholesale — one bad edit locks the user out of their own tools. Re-run the `time zsh -i -c exit` block
afterwards to show the startup win.

## login-shell-not-zsh

**mutating.** *You run this* — `chsh` asks for your password at a TTY, and a corporate policy or LDAP
directory may refuse it. A denial is not a failure of the phase: record it and move on
(`edge-cases.md` § chsh).

```bash
chsh -s "$(command -v zsh)"
```

Verify in a **newly opened terminal window** (the current one keeps its old shell):

```bash
echo "$SHELL"
```

## oh-my-zsh-missing

Downloads and runs a remote installer, then deploys the shell config this skill ships in
`assets/zshrc-config` — say both before asking.

**The tag depends on the machine, and this is the one place to get it right:**

| State of `~/.zshrc` | Tag | Why |
|---------------------|-----|-----|
| absent | **additive** | nothing working can be lost; batch-approvable |
| exists | **mutating** | the config copy replaces a file the user may have tuned by hand — own yes + backup |

A blanket "do everything" approval covers only the additive case. Check first, in its own inspect block:

```bash
ls -l ~/.zshrc 2>/dev/null || echo "no ~/.zshrc — additive"
```

**1 · framework** (additive — creates `~/.zshrc` only if absent):

```bash
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
```

**2 · plugins** (additive — clones into `$ZSH_CUSTOM/plugins`, re-runnable):

```bash
ZSH_CUSTOM="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"
git clone https://github.com/zsh-users/zsh-syntax-highlighting.git "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting" 2>/dev/null || git -C "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting" pull --ff-only
git clone https://github.com/zsh-users/zsh-autosuggestions.git "$ZSH_CUSTOM/plugins/zsh-autosuggestions" 2>/dev/null || git -C "$ZSH_CUSTOM/plugins/zsh-autosuggestions" pull --ff-only
git clone https://github.com/zsh-users/zsh-completions.git "$ZSH_CUSTOM/plugins/zsh-completions" 2>/dev/null || git -C "$ZSH_CUSTOM/plugins/zsh-completions" pull --ff-only
```

**3 · shell config** — resolve `<skill-dir>` to the skill's own absolute path before showing the block. When
`~/.zshrc` already exists this is **mutating**: back it up, name the backup path out loud, and get its own yes.

```bash
cp ~/.zshrc ~/.zshrc.bak.$(date +%Y%m%d%H%M%S) 2>/dev/null || true
cp <skill-dir>/assets/zshrc-config ~/.zshrc
```

Declining step 3 is a normal outcome — a hand-written `.zshrc` the user likes beats a uniform one. Install the
framework and plugins, record the decline, and move on.

Verify the framework *and* that the config actually took — `ls -d ~/.oh-my-zsh` alone passes on a machine
whose theme and plugins never loaded:

```bash
ls -d ~/.oh-my-zsh
grep -nE 'ZSH_THEME|^plugins=' ~/.zshrc
ls ~/.oh-my-zsh/custom/plugins
zsh -i -c 'echo "theme=$ZSH_THEME"'
```

Expect `ZSH_THEME="wedisagree"` and the four plugins `git zsh-syntax-highlighting zsh-autosuggestions
zsh-completions`. `assets/zshrc-config` is the source of truth for those values, so a mismatch means step 3
was skipped or declined — not that anything needs editing here.

## starship-config-missing

**additive.** No `~/.config/starship.toml` exists, so starship renders its stock prompt.
`assets/zshrc-config` already carries the `command -v starship` guard and the `eval "$(starship init zsh)"`
line — this fix supplies only the config that line reads.

Deploy the skill's config (resolve `<skill-dir>` to the skill's own absolute path before showing the block —
`approvals.md` § Presenting commands):

```bash
mkdir -p ~/.config
cp <skill-dir>/assets/starship.toml ~/.config/starship.toml
```

Verify — the marker line is what `detect_env.py` reads, so check it, not just the file:

```bash
head -n1 ~/.config/starship.toml
starship --version
```

## starship-config-not-managed

**mutating.** A `starship.toml` is already there and working — a distro default (Omarchy, Manjaro), a
Homebrew example, or the user's own. Overwriting it changes a prompt they may have tuned deliberately.

Show them what they have before asking:

```bash
head -n 20 ~/.config/starship.toml
wc -l ~/.config/starship.toml
```

If they want the skill's config, **back the existing one up first** and say the backup path out loud:

```bash
cp ~/.config/starship.toml ~/.config/starship.toml.bak.$(date +%Y%m%d%H%M%S)
cp <skill-dir>/assets/starship.toml ~/.config/starship.toml
```

Declining is a normal outcome — a working prompt the user likes beats a uniform one. Record the decline and
move on; do not re-offer it on the next phase.

Verify:

```bash
head -n1 ~/.config/starship.toml
ls ~/.config/starship.toml.bak.*
```

## no-sudo

**not fixable from here.** Report it. Only user-level installs are possible: `uv`, `nvm`, npm with a
`~/.npm-global` prefix, and the agent CLIs. Say which requested items are blocked instead of failing
them silently.

---

## Deep checks (need network — run only with approval)

`detect_env.py` stays offline and fast, so "what is outdated" is a separate, opt-in step. All of these
are read-only; the upgrade command next to each is **mutating**.

| Scope | Read-only check | Upgrade (mutating) |
|-------|-----------------|--------------------|
| Homebrew | `brew outdated` · `brew doctor` | `brew upgrade [formula]` |
| apt | `apt list --upgradable` | `sudo apt-get upgrade` |
| dnf | `dnf check-update` | `sudo dnf upgrade` |
| pacman | `pacman -Qu` | `sudo pacman -Syu` |
| winget | `winget upgrade` | `winget upgrade --id <Id>` |
| npm globals | `npm outdated -g --depth=0` | `npm install -g <pkg>@latest` |

Disk reclamation (`brew cleanup`, `sudo apt-get autoremove`, `npm cache clean --force`) is **mutating and
optional** — always run the dry-run form first (`brew cleanup -n`, `apt-get autoremove --dry-run`) and
present what it would delete. Never volunteer it as part of a setup run.

**Agent CLIs:** prefer each tool's own updater when it has one (`claude update`, `opencode upgrade`);
otherwise reinstall through the channel it came from — see `agent-clis.md`. Check `which claude` first:
a CLI installed by the native installer and *also* present via npm global is the same duplicate-source
problem as `multiple-node-managers`.
