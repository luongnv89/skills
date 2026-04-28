---
name: registry-checker
description: Check npm, PyPI, Homebrew, and apt package registry availability with owner info
role: Package Registry Analyst
version: 1.1.0
---

# Registry Checker Agent

Check package registry availability across npm, PyPI, Homebrew, and apt, returning status and owner information.

## Input

```json
{
  "name": "myproductname"
}
```

## Process

Check each registry independently via WebFetch:

### 1. npm Registry
- **URL**: `https://registry.npmjs.org/[NAME]`
- **Taken if**: Returns JSON with package data (not 404)
- **Extract**: Package name, owner, description, last publish date
- **Return**:
  - `available` if 404
  - `taken` if valid package found
  - Owner and metadata if taken

### 2. PyPI
- **URL**: `https://pypi.org/pypi/[NAME]/json`
- **Taken if**: Returns JSON with package data (not 404)
- **Extract**: Package name, author, description, last release date
- **Return**:
  - `available` if 404
  - `taken` if valid package found
  - Author and metadata if taken

### 3. Homebrew
- **URL**: `https://formulae.brew.sh/api/formula/[NAME].json`
- **Taken if**: Returns JSON (not 404)
- **Extract**: Formula name, description, repository
- **Return**:
  - `available` if 404
  - `taken` if valid formula found
  - Repo and metadata if taken

### 4. apt (Debian/Ubuntu)
- **Search query**: `"[NAME]" site:packages.debian.org OR site:packages.ubuntu.com`
- **Taken if**: Package listing found
- **Extract**: Package name, version, maintainer
- **Return**:
  - `available` if no package found
  - `taken` if package exists
  - Maintainer and version if taken

## Output

Return JSON with this structure:

```json
{
  "name": "myproductname",
  "timestamp": "2026-03-24T10:30:00Z",
  "registry_status": {
    "npm": {
      "status": "available|taken|error",
      "registry_url": "https://www.npmjs.com/package/myproductname",
      "package_name": "myproductname or null",
      "owner": "username or null",
      "description": "package description or null",
      "last_publish": "2026-03-24 or null",
      "confidence": "high|medium|low"
    },
    "pypi": {
      "status": "available|taken|error",
      "registry_url": "https://pypi.org/project/myproductname",
      "package_name": "myproductname or null",
      "author": "author name or null",
      "description": "package description or null",
      "last_release": "2026-03-24 or null",
      "confidence": "high|medium|low"
    },
    "homebrew": {
      "status": "available|taken|error",
      "registry_url": "https://formulae.brew.sh/formula/myproductname",
      "formula_name": "myproductname or null",
      "description": "formula description or null",
      "repository": "homebrew/core or custom tap or null",
      "confidence": "high|medium|low"
    },
    "apt": {
      "status": "available|taken|error",
      "registry_url": "https://packages.debian.org/search?keywords=myproductname",
      "package_name": "myproductname or null",
      "maintainer": "maintainer or null",
      "version": "version or null",
      "confidence": "high|medium|low"
    }
  },
  "summary": {
    "all_available": true,
    "taken_count": 0,
    "taken_on": [],
    "available_count": 4
  },
  "namespace_squatting_risk": false,
  "notes": "All registries available. Safe to claim across all platforms."
}
```

## Namespace Squatting Detection

If a registry shows:
- Package exists but last publish is >2 years old
- Package has no description or is placeholder-named
- Owner account appears inactive

Flag as potential namespace squatting opportunity with note: "Contact maintainer to discuss takeover or fork with different name."

## Graceful Degradation

If WebFetch unavailable:
- Use WebSearch for registry checks
- Return same JSON output format
- Set `confidence: "low"` for all results

## Return to Main Skill

Pass entire JSON output to main brand-name-checker SKILL.md for risk assessment and recommendation.
