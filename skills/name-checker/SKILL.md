---
name: name-checker
description: "Check product and brand names for conflicts across trademarks, domains, social media handles, and package registries (npm, PyPI, Homebrew, apt). Delivers a risk assessment and actionable Proceed, Modify, or Abandon recommendation. Don't use for brainstorming name ideas from scratch, logo design, or filing/registering a trademark."
effort: max
license: MIT
metadata:
  version: 1.1.2
  author: Luong NGUYEN <luongnv89@gmail.com>
---

# Name Checker

Check product and brand names for conflicts across trademarks, domains, social media, and package registries (npm, PyPI, Homebrew, apt).

## Subagent Architecture

This skill uses parallel subagents to handle 13+ sequential web fetches across independent sources. **Pattern**: B (Parallel Workers) + D (Research+Synthesis).

### Agents

| Agent | Role | Output |
|-------|------|--------|
| **social-checker** | Search 6 platforms (Twitter, Instagram, GitHub, LinkedIn, TikTok, Discord) in parallel | JSON: per-platform availability status |
| **registry-checker** | Check npm, PyPI, Homebrew, apt availability with owner info | JSON: per-registry status and owner details |
| **domain-checker** | Check .com, .io, .app, .co, regional TLDs availability | JSON: per-TLD registration status |
| **trademark-checker** | Search WIPO, EUIPO, INPI trademark databases | JSON: conflict analysis per database |
| **synthesizer** | Apply risk matrix and produce final recommendation | Markdown + JSON: Risk level, verdict, alternatives |

### Parallelization Strategy

- **Early Exit Logic**: If social-checker finds exact handle taken on main platform, skip steps 2-4 and jump to synthesizer with "Abandon" verdict
- **Independent Workers**: Registry, domain, trademark checkers run in parallel without dependencies
- **Sequential Flow**: Social → (if clear) → Parallel {Registry, Domain, Trademark} → Synthesizer

**Speedup**: ~4x faster than sequential approach (13+ web fetches parallelized into 2-3 waves).

## Environment Check

Before executing:
1. Verify WebSearch and WebFetch tools are available
2. Confirm internet connectivity for external service queries
3. Check rate limits on social platforms and registries

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

## Step Completion Reports

After completing each major step, output a status report in this format:

```
◆ [Step Name] ([step N of M] — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          √ pass (note if relevant)
  [Check 3]:          × fail — [reason]
  [Check 4]:          √ pass
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Adapt the check names to match what the step actually validates. Use `√` for pass, `×` for fail, and `—` to add brief context. The "Criteria" line summarizes how many acceptance criteria were met. The "Result" line gives the overall verdict.

### Social Media Check (step 1 of 5)

```
◆ Social Media Check (step 1 of 5 — handle availability)
··································································
  Twitter available:      √ pass
  GitHub available:       √ pass
  Reddit available:       × fail — r/[name] subreddit exists
  [Criteria]:             √ 2/3 met
  ____________________________
  Result:                 PARTIAL
```

### Package Registry (step 2 of 5)

```
◆ Package Registry (step 2 of 5 — namespace availability)
··································································
  npm clear:              √ pass
  PyPI clear:             × fail — package exists (owner: example)
  Homebrew clear:         √ pass
  [Criteria]:             √ 2/3 met
  ____________________________
  Result:                 PARTIAL
```

### Domain Check (step 3 of 5)

```
◆ Domain Check (step 3 of 5 — domain availability)
··································································
  .com available:         × fail — active site in same industry
  .dev available:         √ pass
  .io available:          √ pass
  [Criteria]:             √ 2/3 met
  ____________________________
  Result:                 PARTIAL
```

### Trademark Check (step 4 of 5)

```
◆ Trademark Check (step 4 of 5 — trademark conflicts)
··································································
  WIPO clear:              √ pass — no conflicts in classes 9/35/42
  EUIPO clear:             √ pass
  INPI clear:              × fail — similar mark in class 42
  [Criteria]:              √ 2/3 met
  ____________________________
  Result:                  PARTIAL
```

### Risk Assessment (step 5 of 5)

```
◆ Risk Assessment (step 5 of 5 — final verdict)
··································································
  Trademark risk level:   √ pass — Low, no conflicts in classes 9/35/42
  Overall risk score:     √ pass — Moderate
  Recommendation generated: √ pass — Modify: use variant
  [Criteria]:             √ 3/3 met
  ____________________________
  Result:                 PASS
```

## Acceptance Criteria

- Social media check completed across all 6 platforms with clear available/taken status
- Package registry status confirmed for npm, PyPI, Homebrew, and apt
- Domain availability checked for .com and at least two alternative TLDs
- Trademark search completed against WIPO, EUIPO, and INPI
- Risk level assigned (Low / Moderate / High) with supporting rationale
- Final recommendation delivered (Proceed / Modify / Abandon) with named alternatives if needed

## Expected Output

```
SOCIAL: Clear (Twitter, Instagram, GitHub, LinkedIn, TikTok, Discord all available)
REGISTRY: npm (available) | PyPI (TAKEN — owner: example-org, last publish: 2022-03) | Homebrew (available) | apt (available)
DOMAIN: .com (active — unrelated industry) | .io (available) | .app (available)
TM: WIPO (clear) | EUIPO (clear) | INPI (similar mark in class 42 — "Acme Tools SAS", filed 2021)
RISK: Moderate — PyPI name taken on a target registry; .com parked; minor trademark similarity in France
RECOMMEND: Modify — use "acme-cli" (npm/PyPI clear, .com available, no TM conflicts)
```

## Edge Cases

- **Exact social handle taken on primary platform**: Skip all remaining checks and immediately return an Abandon recommendation with alternative name suggestions.
- **Rate-limited registry API**: Retry once after 5 seconds; if still blocked, mark the registry as "unchecked" and note it in the report — do not skip silently.
- **Trademark database unavailable**: Note the outage per database; downgrade risk only if all three TM sources are inaccessible (warn user).
- **Name contains special characters or spaces**: Normalize to slug form (e.g., `my tool` → `my-tool`) before all checks; report both the original and normalized forms.
- **Very short names (1–3 characters)**: Flag high trademark collision risk upfront; abbreviations are almost always claimed across social and TM databases.
- **Name already in use by a well-known brand (typosquat risk)**: Escalate to High risk even if all technical checks pass.

## Final Action

- **Proceed**: Confirm safe to use, suggest registration order:
  1. **Package registries first** — claim names on npm/PyPI/Homebrew immediately, even with a placeholder package. These are first-come-first-served and the most vulnerable to namespace squatting.
  2. **Domain** — register the primary domain.
  3. **Social handles** — secure handles on key platforms.
- **Modify**: Recommend best variant with explanation
- **Abandon**: Recommend best alternative from suggestions
