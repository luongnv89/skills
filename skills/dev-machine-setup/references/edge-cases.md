# Edge cases & environment-specific notes

Non-happy-path situations `dev-machine-setup` may hit. Machine states that `detect_env.py` reports as
`findings[]` are **not** here — those live in `optimize.md`, keyed by finding id.

## No `python3` on a factory machine

`detect_env.py` needs `python3`. Without it, use the fallback one-liners in `detect.md` to get OS/arch,
build the gap list by hand from the baseline table in SKILL.md, and install Python early so later runs
get the full report.

## Windows ARM64 (Snapdragon / Copilot+)

Prefer arm64 winget packages. If a CLI has no arm64 build, say so and install under x64 emulation only
with the user's consent.

## WSL vs native Windows

For Linux-native agents, set up WSL2 Ubuntu and re-run this skill *inside* WSL. Don't mix Windows-native
and WSL Node paths — a gap report from one side says nothing about the other.

## Container / remote-SSH hosts

`notes` reports `container` or `remote-ssh`. Both are valid targets, with two adjustments: skip the
debloat phase entirely, and skip `chsh` (containers usually have no login shell and the change dies with
the container). Prefer user-level installs so the setup survives an image rebuild.

## Distros outside the shipped tables

`linux.md` carries explicit commands for **apt, dnf, and pacman** only. On anything else (Alpine, openSUSE,
Void, NixOS) do not guess a package name: translate the *intent* using that distro's own manager, verify the
binary afterwards, and say in the report which distro the commands were adapted for. NixOS in particular
rejects imperative installs — declare the packages in the user's configuration instead, and record the finding
as deferred rather than failed.

## Partial or interrupted runs

Trigger the skill again — phase 0 picks the run back up from `~/.dev-machine-setup/session.json`
(`references/session.md`). Two rules keep that honest:

- The session file carries **decisions** (mode, what was approved, what was declined, backup paths). It never
  carries machine state.
- Machine state always comes from a fresh `detect_env.py` on resume. Anything that already succeeded drops
  out of `missing` and is skipped; anything that regressed comes back. **Never resume from an old gap
  report.**

With no session file — a different machine, or the user discarded it — a plain re-run is still safe, just
chattier: phase 1 rebuilds everything from scratch and re-asks the questions.
