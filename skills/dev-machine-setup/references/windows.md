# Windows setup

Inspired by [XFreeze / Grok Build](https://x.com/xfreeze/status/2090189407659999603): new Windows laptops often ship trial antivirus, OEM utilities, and partner games. Inventory first. Never mass-uninstall.

## Inventory

Elevated PowerShell:

```powershell
Get-AppxPackage | Select-Object Name, PackageFullName | Sort-Object Name
winget list
```

Flag as **review** (do not auto-remove):

- Names matching `McAfee`, `Norton`, `WildTangent`, `CandyCrush`, `Xbox`, `Spotify`, `Disney`, `TikTok`, `Booking`, `Expedia`, vendor names (`Dell`, `HP`, `Lenovo`, `ASUS`, `Acer`) plus `Support`, `Update`, `Hotkey`
- Trial security suites

**Keep** unless the user says otherwise: GPU control panels, audio/chipset, Bluetooth, camera, OEM firmware updaters, BitLocker, Windows Security.

Present a table. Remove only confirmed rows:

```powershell
# Example — only after an explicit yes for that package
winget uninstall --id <Id> --silent
# or
Get-AppxPackage <Name> | Remove-AppxPackage
```


## Package manager

Prefer **winget** (built into current Windows 10/11). If missing, install App Installer from the Microsoft Store, then retry.

```powershell
winget --version
```

## Baseline

```powershell
winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements
winget install --id OpenJS.NodeJS.LTS -e
winget install --id Python.Python.3.12 -e
```

Open a **new** PowerShell so PATH updates. Then:

```powershell
node -v; npm -v; py -3 --version
```

Install **uv** (user-level, no system pip pollution):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Confirm the URL with the user before running. Alternative: `winget install astral-sh.uv` if the package id resolves.

## Shell

Keep PowerShell 7 if available (`winget install Microsoft.PowerShell`). Oh My Zsh is a Unix skill — if the user wants the full zsh setup, install **WSL2 Ubuntu** and re-run this skill *inside* WSL (then follow `linux.md`).

```powershell
wsl --install -d Ubuntu
```

Requires a reboot. Do not mix Windows-native Node with WSL Node in the same instructions.

## Arch notes

| Arch | Notes |
|------|--------|
| `AMD64` / `x86_64` | Default winget packages |
| `ARM64` | Prefer packages that publish arm64. If a CLI is x64-only, say so and install under emulation only with consent |

## Agent CLIs

After Node is on PATH, follow `agent-clis.md`. `npm install -g` works on Windows if the npm prefix is writable; otherwise use each tool's Windows/native installer from that file.
