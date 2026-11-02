# File Templates

The canonical markdown structure for `idea.md` and `validate.md`, plus the Phase 3 method. Read this when creating or updating either file (Setup steps 4-5, and each phase's "Update `idea.md`/`validate.md`" instruction), and before the Phase 3 searches. The phase instructions in SKILL.md own what each section must contain; this file owns header names, order, placeholder format, and the Phase 3 how-to (_Phase 3 research method_, _Phase 3 capture fields_, _Market players & share method_). Do not restate other phase guidance here.

### idea.md
```markdown
# Idea: [Name]

## Original Concept
[From $ARGUMENTS]

## Clarified Understanding
[After Phase 1]

## Target Audience
[Specific user profile]

## Goals & Objectives
[Success criteria]

## Technical Context
- Stack:
- Timeline:
- Budget:
- Constraints:

## Discussion Notes
[Updates from conversation]
```

### validate.md
```markdown
# Validation: [Name]

## Quick Verdict
**[Build it / Maybe / Skip it]**

## Why
[2-3 sentence explanation]

## Competitive Landscape

| Competitor | Type | What They Do | Pricing / License | Traction / Health | Reuse Potential | Key Weakness |
|---|---|---|---|---|---|---|
| [Name](URL) | [Commercial / OSS / Hybrid / Adjacent / Failed] | [One sentence] | [Model or license] | [Evidence] | [Fork/build-on/plugin/reference/not suitable] | [Gap to exploit] |

### Market Players & Share (paid products)

| Role | Player | Positioning & segment | Sourced figures | Est. share / relative size | Confidence | Derived from |
|---|---|---|---|---|---|---|
| Leader | [Name](URL) | [Who it targets, how] | [Figure, year ([source](URL)); one per signal] | [~N% of basis, or "~3x next player"] | [high / medium / low] | [Revenue / customers / downloads / reviews / traffic] |
| Challenger | [Name](URL) | ... | ... | ... | ... | ... |
| Long tail | [Names](URLs) | [Shared pattern] | [Representative figure or "no public figures"] | [Small, combined] | [label] | [basis] |

**Pricing tiers** (from pricing pages, checked [YYYY-MM-DD]):

| Player | Free | Entry | Pro | Enterprise | Unit | Source |
|---|---|---|---|---|---|---|
| [Name] | [Limits or —] | [Price/mo, listed currency] | [Price/mo] | [Price or Contact sales] | [per seat / per monitor / flat] | [pricing page](URL) |

**Market structure:** [Dominated / Oligopoly / Fragmented] — [evidence]. **For a newcomer:** [what it means].

**Market size (estimate):** [Figure] [TAM / proxy: what it measures], [source](URL), [year] — confidence [label]. [Or: No credible public figure found; bottom-up proxy: [buyers] × [annual price] ≈ [figure], inputs: [sources].]

### Open-source Alternatives & Reuse Potential
[Maintained OSS projects, license/health, and whether to build on, fork, contribute, or avoid rebuilding]

### White Space Analysis
[What's missing in the current market]

### Differentiation Assessment
[Is the proposed differentiation real or imagined given existing commercial and open-source competitors?]

### Build vs. Base Recommendation
[Whether to build from scratch, build on existing OSS, fork, contribute, or narrow the idea]

### Failed Predecessors
[Products or OSS projects that tried and failed, stalled, or were abandoned — and why]

### Research Log

| Side | Queries run | Count |
|---|---|---|
| Open source | "[query]"; "[query]" | [N] |
| Paid & market | "[query]"; "[query]" | [N] |
| Adjacent | "[query]" | [N] |
| Failed attempts | "[query]" | [N] |
| Phase 4 gap-fill | "[query]" or none | [N] |
| **Total** | | **[N]** |

## Similar Products
[Competitors]

## Differentiation
[Unique angle]

## Strengths
-

## Concerns
-

## Ratings
- Creativity: /10
- Feasibility: /10
- Market Impact: /10
- Technical Execution: /10

## How to Strengthen
[Actionable improvements]

## Enhanced Version
[Optimized concept]

## Implementation Roadmap
[Phased approach]
```

## Phase 3 research method

Vary the wording across queries; each query goes in the Research Log under exactly one side.

| Side | Query patterns |
|---|---|
| Open source | `[problem] open source`, `[problem] self-hosted`, `[problem] GitHub`, `[category] OSS alternative to [paid leader]`, package-registry names (npm, PyPI, crates) |
| Paid & market — players | `[problem] SaaS pricing`, `best [category] tools [year]`, `[leader] alternatives`, `[category] app for [audience]` |
| Paid & market — share or size | `[category] market size [year]`, `[category] market share`, `[leader] revenue` or `ARR`, `[leader] customers`, `[leader] raises` or `funding` |
| Adjacent | `how [audience] [does the job] today`, `[related problem] tool` |
| Failed attempts | `[concept] startup failed`, `[concept] post-mortem`, `[concept] shut down`, `[concept] abandoned GitHub` |

If a side finds no credible result, keep its queries in the log and write `none found` in that side's section; for open source, say that no maintained open-source baseline was found.

## Phase 3 capture fields

For each competitor or OSS project found, capture:
- **Name and URL**
- **Type** (commercial, open-source, hybrid, adjacent, failed/abandoned)
- **What they do** (one sentence)
- **Pricing or license** (free, freemium, paid, enterprise, OSS license if available)
- **Traction or health** (reviews, ratings, users, funding, GitHub stars/forks, recent commits, open issues, community activity)
- **Key weakness or gap** the user's idea could exploit
- **Reuse/build-on potential** for open-source options (fork, plugin, library dependency, contribution path, or not suitable)

For each player in the Market Players & Share table, also capture:
- **Role**: leader, challenger, or long tail
- **Sourced figures**, each with its value, year, and link: revenue or ARR, users or customers, funding, employee count, app-store rank or review count, traffic estimate
- **Pricing tiers**: the cheapest price in each of free, entry, pro, enterprise; the unit (per seat, per monitor, flat); monthly or annual billing
- **Positioning and target segment**

## Market players & share method

**Sources.** Use only free, public sources: company sites, pricing pages, press releases, funding announcements and news, app-store listings, GitHub, public filings, and public reports or articles. A data provider's public page counts only when it is readable without payment, a trial, or a login. A paid report's free public summary counts for its headline figure: cite the summary page and never imply the full report was read. Never use a paid data service, and never write that one was used. Cite every figure with its link and year; a figure with no link is an assumption and goes on the Final Report's `Uncertainty:` line. When the source gives no year, keep the link, write `undated`, and rate that row `low`.

**Figures.** Prefer, in order: the company's own statement (press release, about page, investor letter); reputable news reporting it; third-party estimates (app-store ranks, traffic estimators, review counts). Label a third-party figure as an estimate. Do not average figures from different years or bases into one number.

**Share or relative size.** Pick the best basis available for most players (revenue, then customers or users, then downloads or reviews, then traffic or employees), and name it in "Derived from".
- Write a precise share (`32%`) only when a source states it, and link that source.
- Otherwise derive it: player's figure ÷ the market-size estimate (share of market) or ÷ the sum over listed players (share of listed players; say so). Round to a range or `~N%`; never use decimals.
- When players lack a common basis, give relative size instead (`~3x the next player by customers`, `smallest of the four by reviews`).

**Confidence labels.**

| Label | Use when |
|---|---|
| `high` | A credible source states the share, or every listed player has a figure on the same basis from the same year |
| `medium` | Most players have comparable figures, or the share is derived from a sourced market-size estimate |
| `low` | Mixed or partial proxies (traffic, reviews, employees, funding), a single source, or a figure older than 3 years |

**Market structure.** Judge it on the same basis as the shares, and carry their confidence. When bases disagree (claimed free users against paying customers or revenue), judge on the paying basis and state the other reading.

| Structure | Signal | For a newcomer |
|---|---|---|
| Dominated | One player holds about half or more, or is roughly 3x+ the next | Compete only on a segment the leader underserves, or integrate with it; head-on entry needs a real differentiator |
| Oligopoly | 2-4 players together hold most of the market | Expect feature-matching; win on a segment, price point, or distribution channel they ignore |
| Fragmented | No clear leader; many small players | Entry is open, but willingness to pay may be low and distribution is the bottleneck |

**Market size.** Give TAM, or a credible proxy for it (a public report's segment figure, the leader's revenue as a floor), with the source and year, labelled an estimate. If sources disagree, show the range and both sources. Label a broad category figure (for example "all IT operations software") as a ceiling, not the idea's TAM. If no credible figure exists, write so, then build a bottom-up proxy: target buyers (sourced count) × annual price (from the pricing table) ≈ size, with every input shown. When no count of the exact target buyers is public, use the closest broader sourced count as a ceiling and label the narrowing an assumption.

**No paid players found.** Write `none found` in the players table with the paid queries tried, skip share and structure, still give a bottom-up market-size proxy, and treat willingness to pay as unproven in Phase 4.

**Size.** List up to 6 rows: the leader, the main challengers, and the long tail rolled up into one row. When the paid side splits into sub-markets the idea straddles, qualify the role per sub-market (`Leader (incident response)`).
