# Edge cases & environment-specific notes

These handle the non-happy-path situations `new-machine-setup` may hit. The orchestrator SKILL.md links here to keep its body lean.

## No `python3` on a factory machine

Use the fallback one-liners in `detect.md` to determine OS/arch, then proceed. `detect_env.py` only needs `python3`.

## Windows ARM64 (Snapdragon / Copilot+)

Prefer arm64 winget packages. If a CLI has no arm64 build, say so and install under x64 emulation only with the user's consent.

## Node present via nvm/fnm AND a system install

Pick one path; prefer inbash unless nvm is already in use. Do not create two conflicting installs.

## `chsh` denied

Setup still succeeds if zsh + Oh My Zsh exist. Note the denial rather than failing the phase.

## Linux PEP 668

Never `pip install` into the system interpreter — use `uv` or a venv.

## WSL vs native Windows

For Linux-native agents, set up WSL2 Ubuntu and re-run this skill *inside* WSL. Don't mix Windows-native and WSL Node paths.

## inbash scripts are Debian/mac-oriented

On Fedora/Arch, use `linux.md` package-manager switches instead of the `.sh` files blindly.
