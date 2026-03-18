# Publishing to Package Registries

## Detect which registries apply

```bash
# Python package (PyPI)
[ -f pyproject.toml ] || [ -f setup.py ] || [ -f setup.cfg ] && echo "PYPI"

# Node.js package (npm)
[ -f package.json ] && grep -q '"name"' package.json && echo "NPM"
```

## Publish to PyPI

If the project is a Python package:

### Pre-requisites check

```bash
# Ensure build tools are available
pip install --upgrade build twine 2>/dev/null || pip3 install --upgrade build twine

# Check for PyPI credentials
# Token in environment variable
echo "${TWINE_PASSWORD:+PyPI token is set}"

# Or check for .pypirc
[ -f ~/.pypirc ] && echo ".pypirc found"
```

### Build the distribution

If the build step (Step 7) already produced distribution files in `dist/`, reuse them. Otherwise, build now:

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build source distribution and wheel
python -m build
```

### Verify the package

```bash
# Check the built packages
twine check dist/*

# Show what will be uploaded
ls -la dist/
```

### Upload to PyPI

Ask the user before publishing — this is an irreversible action:

"Ready to publish the following to PyPI:
- `dist/package-X.Y.Z.tar.gz`
- `dist/package-X.Y.Z-py3-none-any.whl`

Proceed? (Note: once published, this version cannot be overwritten on PyPI)"

```bash
# Upload to PyPI (production)
twine upload dist/*

# Or upload to Test PyPI first (if user wants to verify)
# twine upload --repository testpypi dist/*
```

After successful upload, share the PyPI URL: `https://pypi.org/project/<package-name>/X.Y.Z/`

## Publish to npm

If the project is a Node.js package:

### Pre-requisites check

```bash
# Check if logged in to npm
npm whoami

# Check package.json for publish config
grep -A5 '"publishConfig"' package.json 2>/dev/null

# Check if package is scoped and has access setting
grep '"name"' package.json
```

### Verify the package

```bash
# Dry run to see what will be published
npm pack --dry-run

# Check for .npmignore or "files" field in package.json
[ -f .npmignore ] && echo ".npmignore found"
grep '"files"' package.json 2>/dev/null && echo "files field found"
```

### Publish to npm

Ask the user before publishing — this is a visible, hard-to-reverse action:

"Ready to publish `<package-name>@X.Y.Z` to npm. Proceed?"

```bash
# Publish to npm
npm publish

# For scoped packages that should be public
# npm publish --access public

# Or publish with a specific tag (e.g., beta, next)
# npm publish --tag <tag>
```

After successful publish, share the npm URL: `https://www.npmjs.com/package/<package-name>/v/X.Y.Z`

## Handle publish failures

If publishing fails:

- **Authentication error** — guide the user to set up credentials:
  - PyPI: `twine upload` requires a PyPI API token (set via `TWINE_USERNAME=__token__` and `TWINE_PASSWORD=<token>`, or configure `~/.pypirc`)
  - npm: run `npm login` or set `NPM_TOKEN` environment variable
- **Version conflict** — the version already exists on the registry. The user must bump the version and re-release.
- **Package name conflict** — the package name is taken. Suggest using a scoped name or choosing a different name.
- **Build error** — re-run the build step (Step 7) and fix any issues before retrying.

## Post-publish verification

```bash
# Verify PyPI publication (check the PyPI JSON API)
curl -sf "https://pypi.org/pypi/<package-name>/X.Y.Z/json" | head -1 && echo "PyPI: OK"

# Verify npm publication
npm view <package-name>@X.Y.Z version 2>/dev/null && echo "npm: OK"
```
