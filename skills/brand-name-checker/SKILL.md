---
name: brand-name-checker
description: "Check product and brand names for conflicts across trademarks, domains, social handles, and package registries. Returns a risk level and Proceed/Modify/Abandon recommendation. Skip for name brainstorming, logo design, or trademark filings."
license: MIT
effort: max
metadata:
  version: 1.4.2
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Brand Name Checker

Check product and brand names for conflicts across trademarks, domains, social media, and package registries (npm, PyPI, Homebrew, apt).

## When to Use

Use this skill before adopting a product or brand name. To stay within the agent's context budget, lean sections (templates, examples) live in `references/*.md` and per-source workers live in `agents/*.md` — only the orchestrator instructions are inlined here.

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

- **Early-Exit Rule**: If social-checker finds an exact handle taken on any of the 6 platforms, skip steps 2-4 (Registry, Domain, Trademark) and jump straight to the synthesizer with an "Abandon" verdict. This is referenced elsewhere in this file simply as the Early-Exit Rule.
- **Independent Workers**: Registry, domain, trademark checkers run in parallel without dependencies
- **Sequential Flow**: Social → (if clear) → Parallel {Registry, Domain, Trademark} → Synthesizer

**Speedup**: ~4x faster than sequential approach (13+ web fetches parallelized into 2-3 waves).

## Environment Check

Before executing:
1. Verify WebSearch and WebFetch tools are available
2. Confirm internet connectivity for external service queries
3. Check rate limits on social platforms and registries

## Repo Sync Before Edits (mandatory)

Before creating/updating/deleting files in an existing repository, sync the current branch with remote. See `references/repo-sync.md` for the exact `git fetch` / `git pull --rebase` commands and stash recovery flow.

## Input

Name to analyze provided in `$ARGUMENTS`. If empty, ask user for the name.

Optionally check for `prd.md` in project to understand product context.

## Analysis Protocol

**Early-Exit Rule applies** (see Subagent Architecture above): an exact social handle taken on any of the 6 platforms skips Steps 2-4 straight to Step 6 (Recommendation) with an "Abandon" verdict.

### Step 1: Social Media Check (First Priority)

Use WebSearch to check handles on:
- X/Twitter: `"@[NAME]" site:twitter.com OR site:x.com`
- Instagram: `"@[NAME]" site:instagram.com`
- GitHub: `"[NAME]" site:github.com/[NAME]`
- LinkedIn: `"[NAME]" site:linkedin.com/company`
- TikTok: `"@[NAME]" site:tiktok.com`
- Discord: `"[NAME]" site:discord.com`

**If exact handle taken (Early-Exit Rule):** Return `NEGATIVE: Exact social handle taken (@platform)` and STOP. Suggest different name.

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
- **Available**: 404 / not found from the registry source — record the source evidence and scope
- **Taken**: Package exists — note the owner, description, and last publish date (a recently claimed but empty package could indicate namespace squatting)
- **Similar**: No exact match but close variants exist (e.g., `name-js`, `py-name`) — worth noting

**If the name is taken on any target registry**, flag it prominently and suggest variants (e.g., `name-cli`, `name-py`, `name-lib`, prefixed with org scope like `@org/name` for npm). If target registry intent is missing or unverifiable, record it as unknown rather than treating every registry as clear.

### Step 3: Domain Check (if Step 1 clear)

Use WebSearch to check:
- `.com` (highest priority)
- `.io`, `.app`, `.co`
- Regional: `.eu`, `.fr`

Search: `site:[NAME].com` and `"[NAME].com" domain availability`

**Status:**
- Available: an authoritative availability result confirms the domain is unregistered
- Parked: Domain exists but is for-sale/parking
- Active: In use (flag if same industry)
- Unknown: the source is unavailable or only shows that no active site was found; do not infer availability

### Step 4: Trademark Check (if Step 1 clear)

Use WebSearch for trademark databases:

| Database | Search Query |
|----------|--------------|
| WIPO | `"[NAME]" site:branddb.wipo.int` |
| EUIPO | `"[NAME]" site:euipo.europa.eu` |
| INPI (France) | `"[NAME]" site:inpi.fr` |

Focus on Nice Classes 9, 35, 42 (software/technology). Note if marks are live or expired.

### Step 5: Risk Assessment

This section is the single authority for qualitative risk policy. The synthesizer must read and follow this section rather than inventing a second matrix. Classify each source result as confirmed, clear, or unknown/unverifiable. Upstream worker labels and severity fields are evidence only; re-check their underlying facts and do not blindly trust numeric severity.

#### Qualitative risk matrix

Risk precedence is **High > Moderate > Low**. Select the highest matching trigger; never average findings. "Multiple handles" means **two or more** confirmed non-exact handle collisions on distinct platforms.

| Risk level | Highest matching trigger |
|------------|--------------------------|
| **High** | Exact social handle collision on any of the 6 platforms (the Early-Exit Rule); two or more confirmed non-exact social handle collisions; a confirmed collision on **any target registry**; an active `.com` in the same industry; an active trademark conflict in Nice Classes 9, 35, 42; a well-known-brand/typosquat conflict; or the existing elevated trademark-collision risk for a very short name. |
| **Moderate** | No High trigger, but one confirmed non-exact social handle collision; a different-industry active `.com`; a similar trademark; a confirmed collision on a non-target registry; or any unknown/unverifiable check or target intent. |
| **Low** | Every required check and target intent is explicitly verified, with no High or Moderate trigger and no unknown result; `.com` is verified available or parked. |

Unknown policy: if checks or target intent are missing or unverifiable and there is no known High finding, use **provisional Moderate + Modify** pending verification. Unknown is not a confirmed collision and never Low clearance. An existing High finding remains High. No averaging or mitigation reduces High. Checks skipped by the Early-Exit Rule remain skipped, not cleared.

The exact-handle Early-Exit Rule is unchanged: an exact handle collision on any of the 6 platforms immediately returns an Abandon recommendation and skips the remaining checks. Report those checks as skipped, not clear.

#### Recommendation semantics

- **Proceed**: only for a fully verified Low result; state the evidence and limitations, and never represent unknown checks as clearance.
- **Modify**: for Moderate, including provisional Moderate; suggest variants that address confirmed conflicts and identify pending verification.
- **Abandon**: for High; mitigation or available alternatives cannot lower the High result.
- Any alternative that was not checked through the applicable sources must be labeled **unverified**; never invent availability or a Low assessment.

### Step 6: Recommendation

Follow the recommendation semantics above and the registration order in Final Action.

## Output Format

Return this compact text report. Replace bracketed fields with observed evidence only; use `Unknown` when a check is unverifiable and `Skipped (not cleared)` for checks omitted by the Early-Exit Rule. The `RISK` line must state the highest matching trigger and its policy rationale, not only the level.

```
SOCIAL: [Clear | NEGATIVE: reason | Unknown: reason]
REGISTRY: npm ([status]) | PyPI ([status]) | Homebrew ([status]) | apt ([status])
DOMAIN: .com ([status]) | .io ([status]) | .app ([status])
TM: WIPO ([status]) | EUIPO ([status]) | INPI ([status])
SKIPPED: [sources, if any; skipped is not cleared]
RISK: [Low | Moderate | High] - [highest matching trigger, evidence, and policy rationale]
RECOMMEND: [Proceed | Modify | Abandon] - [reason and checked or unverified alternatives]
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

After each major step, emit a status report. The general template, plus per-step examples (Social, Registry, Domain, Trademark, Risk, Recommendation), live in `references/step-reports.md`. Adapt check names to what the step actually validates; use `√` for pass, `×` for fail.

## Acceptance Criteria

- Social media check completed across all 6 platforms with explicit available/taken/unknown status
- Package registry status confirmed for npm, PyPI, Homebrew, and apt (unless the Early-Exit Rule fired)
- Domain availability checked for .com and at least two alternative TLDs (unless the Early-Exit Rule fired)
- Trademark search completed against WIPO, EUIPO, and INPI (unless the Early-Exit Rule fired)
- Risk level assigned (Low / Moderate / High) with supporting rationale
- Final recommendation delivered (Proceed / Modify / Abandon) with named alternatives if needed

## Expected Output

For `check "acme-flow"` where no hard conflicts surface but `.com` is parked:

```text
SOCIAL: Clear
REGISTRY: npm (available) | PyPI (available) | Homebrew (available) | apt (available)
DOMAIN: .com (taken) | .io (available) | .app (available)
TM: WIPO (clear) | EUIPO (clear) | INPI (clear)
RISK: Moderate - .com held by unrelated parked page; socials and registries clear
RECOMMEND: Proceed - pair the .io domain with the clear social handles
```

## Edge Cases

- **Exact social handle taken on any of the 6 platforms**: Early-Exit Rule (see Subagent Architecture) — skip all remaining checks and return an Abandon recommendation with alternative name suggestions.
- **Rate-limited registry API**: Retry once after 5 seconds; if still blocked, mark the registry as "unchecked"/unknown and note it in the report — do not skip silently. Apply the unknown policy; do not infer availability.
- **Trademark database unavailable**: Note the outage per database and mark the affected check unknown. Do not downgrade a known High finding; without a known High finding, use provisional Moderate + Modify pending verification.
- **Name contains special characters or spaces**: Normalize to slug form (e.g., `my tool` → `my-tool`) before all checks; report both the original and normalized forms.
- **Very short names (1–3 characters)**: Flag high trademark collision risk upfront; abbreviations are almost always claimed across social and TM databases.
- **Name already in use by a well-known brand (typosquat risk)**: Escalate to High risk even if all technical checks pass.

## Final Action

- **Proceed**: Only for a fully verified Low result; state the evidence and limitations, then suggest registration order:
  1. **Package registries first** — claim names on npm/PyPI/Homebrew immediately, even with a placeholder package. These are first-come-first-served and the most vulnerable to namespace squatting.
  2. **Domain** — register the primary domain.
  3. **Social handles** — secure handles on key platforms.
- **Modify**: Recommend a variant addressing confirmed conflicts and list any pending verification. Alternatives not checked are **unverified**, never available by assertion.
- **Abandon**: Recommend the best alternative from suggestions; mark unchecked alternatives **unverified** and do not claim that any option is clear.
