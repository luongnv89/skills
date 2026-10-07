---
name: brand-name-checker
description: "Check product and brand names for conflicts across trademarks, domains, social handles, and package registries. Returns a risk level and Proceed/Modify/Abandon verdict. Don't use for name brainstorming, logo design, or trademark filings."
license: MIT
effort: max
metadata:
  version: 1.5.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Brand Name Checker

Check product and brand names for conflicts across trademarks, domains, social media, and package registries (npm, PyPI, Homebrew, apt).

## When to Use

Use before adopting a product or brand name. To save context budget, queries, edge cases, and templates live in `references/*.md`.

## Subagent Architecture

Workers in `agents/` each return JSON: **social-checker** (6 platforms), **registry-checker** (npm, PyPI, Homebrew, apt), **domain-checker** (TLDs), **trademark-checker** (WIPO, EUIPO, INPI). The **synthesizer** applies the Step 5 risk policy.

- **Flow**: Social → (if no exact handle is taken) → parallel {Registry, Domain, Trademark} → Synthesizer.
- **Early-Exit Rule**: if social-checker finds an exact handle taken on any of the 6 platforms, skip Steps 2-4 and go straight to the synthesizer with an "Abandon" verdict.
- **Without subagents**: run Steps 1-4 inline from `references/source-checks.md`, in the same order.

## Environment Check

1. Before Step 1, confirm the WebSearch and WebFetch tools are available.
2. Run one test query.
3. If either check fails, stop and return the `BLOCKED` report from *Output Format* with the error.

## Repo Sync Before Edits (mandatory)

This skill writes no files by default. Before creating, updating, or deleting files in a repository, run the stash-first sync in `references/repo-sync.md`.

## Input

Read the name from `$ARGUMENTS`; if empty, ask the user. If `prd.md` exists, read it for industry, target registries, and target domains.

## Analysis Protocol

Queries, check URLs, and status rules for Steps 1-4: `references/source-checks.md`. Record every result with its source.

### Step 1: Social Media Check (First Priority)

Search X/Twitter, Instagram, GitHub, LinkedIn, TikTok, and Discord. If an exact handle is taken (Early-Exit Rule), return `NEGATIVE: Exact social handle taken (@platform)` and skip to Step 6.

### Step 2: Package Registry Check (if Step 1 clear)

Check npm, PyPI, Homebrew, and apt as Available, Taken (owner, last publish date), Similar, or Unknown. If target registry intent is missing or unverifiable, record it as unknown rather than treating every registry as clear.

### Step 3: Domain Check (if Step 1 clear)

Check `.com` first, then `.io`, `.app`, `.co`, `.eu`, `.fr`:

- Available: an authoritative availability result confirms the domain is unregistered
- Parked: Domain exists but is for-sale/parking
- Active: In use (flag if same industry)
- Unknown: the source is unavailable or only shows that no active site was found; do not infer availability

### Step 4: Trademark Check (if Step 1 clear)

Search WIPO, EUIPO, and INPI in Nice Classes 9, 35, 42; record each mark as live or expired.

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

Return this compact text report, the only format: it fits on one screen, so it needs no HTML or interactive view. Replace bracketed fields with observed evidence only. Use `Unknown` when a check is unverifiable and `Skipped (not cleared)` for checks omitted by the Early-Exit Rule. The `RISK` line must state the highest matching trigger and its policy rationale, not only the level. Keep `RISK` and `RECOMMEND` as the last two lines; callers read them.

```
RESULT: [COMPLETE | PARTIAL | BLOCKED] - [N/M checks verified; unknown and skipped counts]
SOCIAL: [Clear | NEGATIVE: reason | Unknown: reason]
REGISTRY: npm ([status]) | PyPI ([status]) | Homebrew ([status]) | apt ([status])
DOMAIN: .com ([status]) | .io ([status]) | .app ([status])
TM: WIPO ([status]) | EUIPO ([status]) | INPI ([status])
EVIDENCE: [source queried for each status: URL or search query, and check time]
SKIPPED: [sources, if any; skipped is not cleared]
UNKNOWN: [checks not verified, why, and what would verify them | none]
RISK: [Low | Moderate | High] - [highest matching trigger, evidence, and policy rationale]
RECOMMEND: [Proceed | Modify | Abandon] - [reason and checked or unverified alternatives]; next: [the user's decision and remaining actions]
```

`RESULT` status: **COMPLETE** when every check is verified or skipped by the Early-Exit Rule; **PARTIAL** when any check is Unknown; **BLOCKED** when no name was given or the web tools are unavailable (return only the `RESULT` line with the reason and fix). Before writing the report, read `references/output-contract.md` for the field rules and the `next:` clause. If `prd.md` exists, append the blocks from `references/prd-integration.md`.

## Step Completion Reports

After each major step, emit a status report. The general template and per-step examples (Social, Registry, Domain, Trademark, Risk, Recommendation) live in `references/step-reports.md`. Adapt check names to what the step validates; use `√` for pass and `×` for fail.

## Acceptance Criteria

- Social media check completed across all 6 platforms with explicit available/taken/unknown status
- Package registry status confirmed for npm, PyPI, Homebrew, and apt (unless the Early-Exit Rule fired)
- Domain availability checked for .com and at least two alternative TLDs (unless the Early-Exit Rule fired)
- Trademark search completed against WIPO, EUIPO, and INPI (unless the Early-Exit Rule fired)
- Risk level assigned (Low / Moderate / High) with the highest matching trigger as rationale
- Final recommendation delivered (Proceed / Modify / Abandon) with named alternatives if needed
- Understanding: the first line states the `RESULT` status; verified statuses cite a source on `EVIDENCE` while unverified ones sit on `UNKNOWN`; `RISK` names its trigger; `RECOMMEND` ends with `next:`. Unanswered human review leaves understanding unconfirmed (`references/output-contract.md`)

## Expected Output

Example of an Early-Exit run for `nimbus`; COMPLETE and PARTIAL runs: `references/output-contract.md`.

```text
RESULT: COMPLETE - 6/16 checks verified; 0 unknown, 10 skipped by the Early-Exit Rule
SOCIAL: NEGATIVE: Exact social handle taken (@github)
REGISTRY: Skipped (not cleared)
DOMAIN: Skipped (not cleared)
TM: Skipped (not cleared)
EVIDENCE: github.com/nimbus resolves to an active organization; checked 2026-01-15T10:31Z
SKIPPED: registries, domains, trademarks; skipped is not cleared
UNKNOWN: none
RISK: High - exact social handle collision on GitHub (Early-Exit Rule)
RECOMMEND: Abandon - nimbus-dev, nimbusly (both unverified); next: pick a candidate and run this check on it
```

## Edge Cases

Rate limits, source outages, special characters, very short names, and typosquats: `references/edge-cases.md`. A rate-limited registry gets one retry after 5 seconds, then is marked unknown — do not skip silently or infer availability.

## Final Action

- **Proceed**: Only for a fully verified Low result; state the evidence and limitations, then suggest registration order:
  1. **Package registries first** — claim names on npm/PyPI/Homebrew immediately, even with a placeholder package. These are first-come-first-served and the most vulnerable to namespace squatting.
  2. **Domain** — register the primary domain.
  3. **Social handles** — secure handles on key platforms.
- **Modify**: Recommend a variant addressing confirmed conflicts and list any pending verification. Alternatives not checked are **unverified**, never available by assertion.
- **Abandon**: Recommend the best alternative from suggestions; mark unchecked alternatives **unverified** and do not claim that any option is clear.
