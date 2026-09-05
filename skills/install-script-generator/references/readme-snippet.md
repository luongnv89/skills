# README Installation Snippet

Drop this block into the project README after `install.sh` is generated.

````markdown
## Installation

### Quick Install (one command)

```bash
curl -sSL https://raw.githubusercontent.com/<owner>/<repo>/main/install.sh | bash
```

Or with wget:

```bash
wget -qO- https://raw.githubusercontent.com/<owner>/<repo>/main/install.sh | bash
```

### Advanced Options

```bash
# Install to a custom prefix
curl -sSL https://raw.githubusercontent.com/<owner>/<repo>/main/install.sh | INSTALL_PREFIX=~/.local bash

# Download and inspect before running
curl -sSL https://raw.githubusercontent.com/<owner>/<repo>/main/install.sh -o install.sh
less install.sh   # review the script
bash install.sh
```
````

## Windows one-liner

```powershell
irm https://raw.githubusercontent.com/<owner>/<repo>/main/install.ps1 | iex
```

## Raw URL format

```
https://raw.githubusercontent.com/<owner>/<repo>/<branch>/install.sh
```

If the script lives in a subdirectory, append the path: `.../<branch>/path/to/install.sh`.
