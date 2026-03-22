---
name: name-checker
description: Check product/brand names for trademark, domain, social media, and package registry conflicts. Use when users ask to "check this name", "validate a product name", "is this name available", "is this package name taken", or need to assess naming risks before publishing to npm, PyPI, Homebrew, or apt. Provides risk assessment and alternative suggestions. Also use when users want to secure a name early across registries to prevent namespace squatting, or ask "can I publish under this name".
effort: low
license: MIT
metadata:
  version: 1.1.0
  creator: Luong NGUYEN <luongnv89@gmail.com>
---

# Name Checker

Check product and brand names for conflicts across trademarks, domains, social media, and package registries (npm, PyPI, Homebrew, apt).

## Repo Sync Before Edits (mandatory)

Before creating/updating/deleting files in an existing repository, sync the current branch with remote:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If the working tree is not clean, stash first, sync, then restore:

```bash
git stash push -u -m "pre-sync"
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin && git pull --rebase origin "$branch"
git stash pop
```

If `origin` is missing, pull is unavailable, or rebase/stash conflicts occur, stop and ask the user before continuing.

## Input

Name to analyze provided in `$ARGUMENTS`. If empty, ask user for the name.

Optionally check for `prd.md` in project to understand product context.

## Analysis Protocol

**If an exact social handle is taken, skip Steps 2-4 and jump directly to Step 6 (Recommendation) with an "Abandon" verdict.**

### Step 1: Social Media Check (First Priority)

Use WebSearch to check handles on:
- X/Twitter: `"@[NAME]" site:twitter.com OR site:x.com`
- Instagram: `"@[NAME]" site:instagram.com`
- Facebook: `"[NAME]" site:facebook.com`
- LinkedIn: `"[NAME]" site:linkedin.com/company`
- YouTube: `"[NAME]" site:youtube.com`
- TikTok: `"@[NAME]" site:tiktok.com`

**If exact handle taken:** Return `NEGATIVE: Exact social handle taken (@platform)` and STOP. Suggest different name.

### Step 2: Package Registry Check (if Step 1 clear)

Package registries are first-come-first-served namespaces. Unlike GitHub (which allows duplicate project names), registries enforce unique names — once someone claims "your-name" on PyPI or npm, you cannot publish under that name. This makes registry checks urgent: if the name is taken on a registry you plan to publish to, you either need a different name or a naming variant (e.g., prefix/suffix).

Use WebFetch to check these registries directly:

| Registry | Check URL | Taken if... |
|----------|-----------|-------------|
| **npm** | `https://registry.npmjs.org/[NAME]` | Returns JSON with package data (not a 404) |
| **PyPI** | `https://pypi.org/pypi/[NAME]/json` | Returns JSON with package data (not a 404) |
| **Homebrew** | `https://formulae.brew.sh/api/formula/[NAME].json` | Returns JSON (not a 404) |
| **apt** | Search: `"[NAME]" site:packages.debian.org OR site:packages.ubuntu.com` | Package listing found |

For each registry, report:
- **Available**: 404 / not found — safe to claim
- **Taken**: Package exists — note the owner, description, and last publish date (a recently claimed but empty package could indicate namespace squatting)
- **Similar**: No exact match but close variants exist (e.g., `name-js`, `py-name`) — worth noting

**If the name is taken on a registry the user plans to publish to**, flag it prominently and suggest variants (e.g., `name-cli`, `name-py`, `name-lib`, prefixed with org scope like `@org/name` for npm).

### Step 3: Domain Check (if Step 1 clear)

Use WebSearch to check:
- `.com` (highest priority)
- `.io`, `.app`, `.co`
- Regional: `.eu`, `.fr`

Search: `site:[NAME].com` and `"[NAME].com" domain availability`

**Status:**
- Available: No active site
- Parked: Domain exists but for-sale/parking
- Active: In use (flag if same industry)

### Step 4: Trademark Check (if Step 1 clear)

Use WebSearch for trademark databases:

| Database | Search Query |
|----------|--------------|
| WIPO | `"[NAME]" site:branddb.wipo.int` |
| EUIPO | `"[NAME]" site:euipo.europa.eu` |
| INPI (France) | `"[NAME]" site:inpi.fr` |

Focus on Nice Classes 9, 35, 42 (software/technology). Note if marks are live or expired.

### Step 5: Risk Assessment

| Risk Level | Criteria |
|------------|----------|
| **Low** | Social handles available, .com available/parked, no trademark conflicts, package registries available |
| **Moderate** | Some handles taken (not exact), .com taken but alternatives available, similar trademarks exist, or name taken on a registry the user doesn't plan to use |
| **High** | Multiple handles taken, .com active in same industry, active trademarks in classes 9/35/42, or name taken on a target package registry |

### Step 6: Recommendation

- **Proceed**: Low risk - name is viable
- **Modify**: Moderate risk - suggest 1-2 variants addressing conflicts
- **Abandon**: High risk - suggest completely different alternatives

## Output Format

```
SOCIAL: Clear | NEGATIVE: [reason]
REGISTRY: npm (status) | PyPI (status) | Homebrew (status) | apt (status)
DOMAIN: .com (status) | .io (status) | .app (status)
TM: WIPO (status) | EUIPO (status) | INPI (status)
RISK: [Low/Moderate/High] - [reason]
RECOMMEND: [Proceed/Modify/Abandon] (+ variants if needed)
```

## PRD Integration

If `prd.md` found, add:

**Name Fit Assessment:**
- Alignment with product vision
- Memorability, pronunciation, spelling
- Target audience fit

**Alternative Suggestions:**

| Name | Rationale | Quick Risk |
|------|-----------|------------|
| Name1 | Why it fits | Availability |
| Name2 | Why it fits | Availability |
| Name3 | Why it fits | Availability |

## Final Action

- **Proceed**: Confirm safe to use, suggest registration order:
  1. **Package registries first** — claim names on npm/PyPI/Homebrew immediately, even with a placeholder package. These are first-come-first-served and the most vulnerable to namespace squatting.
  2. **Domain** — register the primary domain.
  3. **Social handles** — secure handles on key platforms.
- **Modify**: Recommend best variant with explanation
- **Abandon**: Recommend best alternative from suggestions
