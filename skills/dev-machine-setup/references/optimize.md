# Optimize an existing setup

Fix catalog for the `findings[]` array emitted by `scripts/detect_env.py`. Each finding carries a
`fix_ref` pointing at the matching heading below.

Every fix is tagged **additive** (adds something absent — batch-approvable) or **mutating** (changes an
install or config that already works — needs a per-item yes, per SKILL.md § Human-in-the-loop).

**Before any in-place rc-file edit**, back the file up and show the user the path:

```bash
cp ~/.zshrc ~/.zshrc.bak.$(date +%Y%m%d%H%M%S)   # or ~/.zprofile, ~/.bashrc
```

Windows equivalent: `Copy-Item $PROFILE "$PROFILE.bak"`.

---

## no-package-manager

**additive.** Nothing installs until a manager exists. Install the one for the OS — macOS: Homebrew
(`macos.md` § Homebrew), Linux: the distro's manager is already present unless the image is minimal
(`linux.md`), Windows: App Installer from the Microsoft Store, then re-run `winget --version`.

## npm-global-bin-not-on-path

**mutating** (edits a shell rc). This is the single most common cause of "installed it, command not
found" — the CLI is on disk but the shim directory is invisible.

```bash
npm prefix -g                       # e.g. /Users/me/.npm-global
export PATH="$(npm prefix -g)/bin:$PATH"          # verify in this shell first
echo 'export PATH="$(npm prefix -g)/bin:$PATH"' >> ~/.zshrc   # then persist
```

Windows: add the `npm prefix -g` directory itself (no `/bin`) via
`[Environment]::SetEnvironmentVariable('Path', "$env:Path;<prefix>", 'User')`, then open a new shell.

If the prefix is a root-owned directory the user cannot write, re-point it instead of using sudo:
`npm config set prefix ~/.npm-global`, then add that bin dir as above and reinstall global packages.

## brew-bin-not-on-path

**mutating.** Homebrew is installed but its shellenv line never landed:

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile   # Intel: /usr/local/bin/brew
exec zsh -l
```

## intel-homebrew-on-apple-silicon

**mutating, high effort — default to deferring.** Everything installed under `/usr/local` runs through
Rosetta. Migrating means reinstalling the formulae under `/opt/homebrew`. Report it, list what would
move (`/usr/local/bin/brew list --formula`), and only proceed if the user explicitly asks. Do not
uninstall the x86 prefix — some formulae are x86-only.

## xcode-clt-missing

**additive.** `xcode-select --install` (opens a GUI dialog; tell the user to accept it). Native builds,
many Homebrew formulae, and `node-gyp` fail without it.

## multiple-node-managers

**mutating.** Two or more Node sources compete for PATH, so `node -v` depends on which rc file won.
Do not uninstall anything automatically. Show the user which one is winning and let them pick:

```bash
which -a node && node -v
type -a node          # zsh/bash: shows function/alias shims too
```

Keep the version manager if one is in active use (a `.nvmrc`/`.node-version` in their projects is the
tell); otherwise keep the package-manager Node. Removing the loser is a separate, explicitly approved
step — `brew uninstall node` or removing the manager's rc lines, never both blind.

## node-below-min

**mutating.** The floor lives in `NODE_MIN_MAJOR` in `scripts/detect_env.py`. Upgrading a runtime can
break projects pinned to the old major — say so before running anything. Upgrade through whatever
already owns Node (`brew upgrade node`, `nvm install --lts`, `winget upgrade OpenJS.NodeJS.LTS`,
distro path in `linux.md`), never by adding a second source.

## python-below-min

**mutating.** Same rule: upgrade through the owner. Never replace the OS's own `/usr/bin/python3` on
Linux or macOS — install a newer interpreter alongside (`brew install python@3.13`, `uv python install
3.13`) and leave the system one alone.

## python-externally-managed

**additive.** The system interpreter is PEP 668 marked, so `pip install` into it fails by design.
Install `uv` and use `uv venv` / `uv pip` per-project. Commands per OS in `macos.md`, `linux.md`,
`windows.md`. Never suggest `--break-system-packages`.

## git-identity-missing

**mutating** (writes `~/.gitconfig`) — and the values must come from the user, never invented:

```bash
git config --global user.name "<ask the user>"
git config --global user.email "<ask the user>"
```

## path-duplicates

**mutating.** Duplicate entries mean a profile is sourced twice (commonly `.zprofile` *and* `.zshrc`
both adding the same line, or a re-entrant `exec zsh`). Show the offenders first:

```bash
echo "$PATH" | tr ':' '\n' | sort | uniq -d
grep -n 'PATH=' ~/.zshrc ~/.zprofile ~/.zshenv 2>/dev/null
time zsh -i -c exit          # startup cost, before and after
```

Fix the duplicated export in the rc file (after the backup above). Do not rewrite PATH wholesale — one
bad edit locks the user out of their own tools.

## login-shell-not-zsh

**mutating.** `chsh -s "$(command -v zsh)"` needs a password and may be denied by policy or by an LDAP
directory. A denial is not a failure of the phase — record it and move on (`edge-cases.md` § chsh).

## oh-my-zsh-missing

**additive.** `setup-ohMyZsh.sh` from inbash (`macos.md` / `linux.md`). If the user already has a
hand-written `~/.zshrc`, install the framework and plugins but skip the config copy.

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
