# VS Code Extension Publishing Guide

Detailed reference for publishing VS Code extensions to the Visual Studio Marketplace.

## Table of Contents

- [Personal Access Token (PAT)](#personal-access-token-pat)
- [Publisher Identity](#publisher-identity)
- [package.json Configuration](#packagejson-configuration)
- [Packaging](#packaging)
- [Publishing](#publishing)
- [.vscodeignore](#vscodeignore)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

## Personal Access Token (PAT)

### Creating a PAT

1. Sign in at https://dev.azure.com
2. Navigate to **User Settings** > **Personal Access Tokens**
3. Click **+ New Token**:
   - **Name:** Descriptive name (e.g., `vsce-publish`)
   - **Organization:** "All accessible organizations" (required!)
   - **Expiration:** Up to 1 year
   - **Scopes:** Custom defined > **Marketplace** > **Manage**

### Common PAT Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| 401 Unauthorized | Wrong scope | Recreate with Marketplace > Manage |
| 403 Forbidden | Specific org selected | Use "All accessible organizations" |
| Token expired | Past expiration date | Generate new token |
| Login succeeds but publish fails | Token has read-only scope | Ensure "Manage" is checked |

## Publisher Identity

### Creating a Publisher

1. Go to https://marketplace.visualstudio.com/manage
2. Sign in with the same Microsoft account used for PAT
3. Click **Create publisher**
4. Required fields:
   - **ID:** Unique identifier — **cannot be changed after creation**
   - **Name:** Display name (can be changed later)

### Verified Publisher

Requirements (both must be met):
- Extension published for minimum 6 months
- Domain registered for minimum 6 months

Process:
1. Marketplace management > Publisher Details tab
2. Enter eligible domain (no subdomains like github.io)
3. Add TXT record to DNS
4. Submit for validation (~5 business days)

## package.json Configuration

### Required Fields

```json
{
  "name": "my-extension",
  "displayName": "My Extension",
  "description": "A brief description of what it does",
  "version": "1.0.0",
  "publisher": "my-publisher-id",
  "engines": {
    "vscode": "^1.80.0"
  },
  "categories": ["Other"]
}
```

### Marketplace Enhancement Fields

```json
{
  "icon": "images/icon.png",
  "galleryBanner": {
    "color": "#1e1e1e",
    "theme": "dark"
  },
  "repository": {
    "type": "git",
    "url": "https://github.com/user/repo"
  },
  "keywords": ["keyword1", "keyword2"],
  "license": "MIT",
  "bugs": {
    "url": "https://github.com/user/repo/issues"
  },
  "homepage": "https://github.com/user/repo#readme"
}
```

### Valid Categories

- `Programming Languages`
- `Snippets`
- `Linters`
- `Themes`
- `Debuggers`
- `Formatters`
- `Keymaps`
- `SCM Providers`
- `Other`
- `Extension Packs`
- `Language Packs`
- `Data Science`
- `Machine Learning`
- `Visualization`
- `Notebooks`
- `Education`
- `Testing`

### Pre-publish Script

Run build steps automatically before packaging:

```json
{
  "scripts": {
    "vscode:prepublish": "npm run compile"
  }
}
```

### Pricing and Sponsorship

```json
{
  "pricing": "Free",
  "sponsor": {
    "url": "https://github.com/sponsors/username"
  }
}
```

## Packaging

### Basic Packaging

```bash
vsce package
```

Generates `<name>-<version>.vsix` in the current directory.

### Platform-Specific Packaging

Build for specific OS/architecture:

```bash
vsce package --target win32-x64
vsce package --target linux-x64
vsce package --target darwin-arm64
```

Available targets: `win32-x64`, `win32-arm64`, `linux-x64`, `linux-arm64`, `linux-armhf`, `alpine-x64`, `alpine-arm64`, `darwin-x64`, `darwin-arm64`, `web`

### Pre-release Packaging

```bash
vsce package --pre-release
```

Requirements:
- Version must be `major.minor.patch` (no semver pre-release tags)
- Recommended: even minor for release (`0.2.*`), odd minor for pre-release (`0.3.*`)
- `engines.vscode` must be `>= 1.63.0`

### Testing Locally

```bash
code --install-extension my-extension-1.0.0.vsix
```

Or in VS Code: Extensions view > ... > "Install from VSIX..."

## Publishing

### First-Time Login

```bash
vsce login <publisher-id>
# Enter PAT when prompted
```

### Publish Commands

```bash
# Publish current version
vsce publish

# Auto-increment version
vsce publish patch    # 1.0.0 → 1.0.1
vsce publish minor    # 1.0.0 → 1.1.0
vsce publish major    # 1.0.0 → 2.0.0

# Set exact version
vsce publish 2.0.0

# Custom commit message (git repos)
vsce publish minor -m "Release v%s"

# Pre-release publish
vsce publish --pre-release

# Platform-specific publish
vsce publish --target win32-x64 linux-x64 darwin-arm64
```

### Unpublishing

```bash
vsce unpublish <publisher>.<extension-name>
```

Or via https://marketplace.visualstudio.com/manage > More Actions > Unpublish

**Warning:** Removing an extension (vs unpublishing) is irreversible and deletes all statistics.

## .vscodeignore

Controls which files are excluded from the `.vsix` package. Works like `.gitignore`:

```
# Source files (ship compiled output instead)
**/*.ts
**/tsconfig.json
src/

# Development files
.vscode/
.github/
node_modules/
**/*.map

# Tests
**/test/**
**/tests/**

# Config files
.eslintrc*
.prettierrc*
```

Development dependencies (`devDependencies`) are automatically excluded.

## CI/CD Integration

### GitHub Actions

See `assets/github-actions-publish.yml` for the complete workflow template.

Key setup steps:
1. Add `VSCE_PAT` as a repository secret
2. Tag releases: `git tag v1.0.0 && git push origin v1.0.0`
3. Workflow triggers on `v*` tags

### Azure DevOps Pipeline

```yaml
trigger:
  tags:
    include:
      - v*

pool:
  vmImage: 'ubuntu-latest'

steps:
  - task: NodeTool@0
    inputs:
      versionSpec: '18.x'
  - script: npm install -g @vscode/vsce
  - script: npm install
  - script: vsce publish -p $(VSCE_PAT)
```

### GitLab CI

```yaml
publish:
  image: node:18
  only:
    - tags
  script:
    - npm install -g @vscode/vsce
    - npm install
    - vsce publish -p $VSCE_PAT
```

## Troubleshooting

### Authentication Errors

| Error | Fix |
|-------|-----|
| `401 Unauthorized` | Regenerate PAT with correct scope |
| `403 Forbidden` | Use "All accessible organizations" in PAT |
| `The Personal Access Token used has expired` | Create a new PAT |

### Packaging Errors

| Error | Fix |
|-------|-----|
| `Missing publisher name` | Add `publisher` to package.json |
| `Extension icon must be of type PNG` | Replace SVG with PNG (128x128px min) |
| `ENOENT: README.md` | Create a README.md file |
| `Exceeded keyword limit` | Reduce `keywords` array to 30 max |

### Publishing Errors

| Error | Fix |
|-------|-----|
| `Extension already exists` | Change `name` in package.json |
| `Version already exists` | Bump version number |
| `File attributes lost` | Publish from Linux/macOS for POSIX file attributes |

### Image Restrictions

The marketplace has strict SVG policies for security:
- Extension `icon` must be PNG (not SVG)
- Badge images cannot be SVG (except from trusted providers)
- README/CHANGELOG images must use HTTPS URLs
