# File Templates

The canonical markdown structure for `idea.md` and `validate.md`, plus the Phase 3 method. Read this when creating or updating either file (Setup steps 4-5, and each phase's "Update `idea.md`/`validate.md`" instruction), and before the Phase 3 searches and the Phase 4 write-up (_Phase 4 shape_). The phase instructions in SKILL.md own what each section must contain; this file owns header names, order, placeholder format, and the Phase 3 how-to (_Phase 3 research method_, _Phase 3 capture fields_, _Market players & share method_). Do not restate other phase guidance here.

### idea.md
```markdown
# Idea: [Name]

## Original Concept
[From $ARGUMENTS]

## Clarified Understanding
[After Phase 1]
- Plans to charge: [yes: who pays, pricing model / no: free, or ads or donations only / unknown]

## Target Audience
[Specific user profile]

## Goals & Objectives
[Success criteria]

## Technical Context
- Stack:
- Timeline:
- Team:
- Budget:
- Existing assets:
- Constraints:

## Discussion Notes
[Updates from conversation]
```

### validate.md

Each section has one owning phase: Phase 3 writes `## Competitive Landscape` and its subsections, Phase 4 the sections in _Phase 4 shape_ (plus its gap-fill row in the Research Log), and Phase 5 `## How to Strengthen`, `## Enhanced Version` and `## Implementation Roadmap`. Add no other section.

```markdown
# Validation: [Name]

## Quick Verdict
**[Build it / Maybe / Skip it]**

## Why
**Rule [1 / 2 / 3]:** [each clause of that verdict rule that matched]
[2-3 sentence rationale]

## Competitive Landscape

| Competitor | Type | What They Do | Pricing / License | Traction / Health | Reuse Potential | Key Weakness |
|---|---|---|---|---|---|---|
| [Name](URL) | [Commercial / OSS / Hybrid / Adjacent / Failed] | [One sentence] | [Model or license] | [Evidence] | [Fork/build-on/plugin/reference/not suitable] | [Gap to exploit] |

### Market Players & Share (paid products)

| Role | Player | Positioning & segment | Sourced figures | Est. share / relative size | Confidence | Derived from |
|---|---|---|---|---|---|---|
| Leader | [Name](URL) | [Who it targets, how] | [Figure, year ([source](URL)); one per signal] | [~N% of basis, or "~3x next player"] | [high / medium / low] | [Revenue / paying customers / users / downloads or reviews / traffic or employees] |
| Challenger | [Name](URL) | ... | ... | ... | ... | ... |
| Long tail | [Names](URLs) | [Shared pattern] | [Representative figure or "no public figures"] | [Small, combined] | [label] | [basis] |

**Pricing tiers** (from pricing pages, checked [YYYY-MM-DD]):

| Player | Free | Entry | Pro | Enterprise | Unit | Source |
|---|---|---|---|---|---|---|
| [Name] | [Limits or —] | [Price/mo, listed currency] | [Price/mo] | [Price or Contact sales] | [per seat / per monitor / flat] | [pricing page](URL) |

**Market structure:** [Dominated / Oligopoly / Fragmented] on [basis], confidence [label] — [evidence]. **For a newcomer:** [what it means].

**Market size (estimate):** [Figure] [TAM / proxy: what it measures], [source](URL), [year] — confidence [label]. [Or: No credible public figure found; bottom-up proxy: [buyers] × [annual price] ≈ [figure], or, for an idea that does not charge, [target users] ≈ [count], inputs: [sources].]

### Open-source Alternatives & Reuse Potential
[Maintained OSS projects, license/health, and whether to build on, fork, contribute, or avoid rebuilding]

### White Space Analysis
[What's missing in the current market]

### Differentiation Assessment
[The differentiator the user named in Phase 1, or `none named`; is it real or imagined given existing commercial and open-source competitors?]

### Build vs. Base Recommendation
[Whether to build from scratch, build on existing OSS, fork, contribute, or narrow the idea]

### Failed Predecessors
[Products or OSS projects that tried and failed, stalled, or were abandoned — and why]

### Research Log

A query is one web-search call. Page fetches that read a result support its query but are never logged or counted as queries.

| Side | Web-search queries run | Count |
|---|---|---|
| Open source | "[query]"; "[query]" | [N] |
| Paid & market | Players: "[query]". Share/size: "[query]" | [N] ([p] players + [s] share/size) |
| Adjacent | "[query]" | [N] |
| Failed attempts | "[query]" | [N] |
| Phase 4 gap-fill | "[query]" or none | [N] |
| **Total** | | **[N]** |

## Evaluation

### Market
[Findings, citing the Phase 3 section or link each rests on]

### Demand
[...]

### Feasibility
[...]

### Monetization
**Plans to charge:** [yes: who pays, pricing model / no: free, or ads or donations only / unknown, treated as yes]
[...]

### Technical Risk
**Hard blockers:** [blocker: why it is certain, and why the stated team and budget cannot remove it] or none
- `[hard / soft]` [risk]: [what stops working if it materializes]; mitigation within the stated team, budget and timeline: [mitigation or none]

### Duplication / Reuse Risk
**Near-identical product:** [[Name](URL): same core job, target user and delivery model, and covers the named differentiator] or [none found; closest: [Name](URL), differs on [the element it misses]; one entry per product that misses only one element]
[...]

## Strengths
-

## Concerns
-

## Ratings

| Rating | Score | Reason |
|---|---|---|
| Creativity | [N]/10 | [One line] |
| Feasibility | [N]/10 | [One line] |
| Market Impact | [N]/10 | [One line] |
| Technical Execution | [N]/10 | [One line] |

## How to Strengthen
[Actionable improvements]

## Enhanced Version
[Optimized concept]

## Implementation Roadmap
[Phased approach]
```

## Phase 4 shape

Phase 4 writes these `validate.md` sections, keeping each heading name exactly as shown in the template above:
- `## Quick Verdict`: the bold verdict alone on the first line under the heading, with no rule or reason on that line. `product-planner` reads the verdict from this line.
- `## Why`: the `**Rule N:**` line naming the first verdict rule that matched and every clause of it that matched, then the 2-3 sentence rationale.
- `## Evaluation`: one `###` heading per evaluation area, in the order shown in the template (Market, Demand, Feasibility, Monetization, Technical Risk, Duplication / Reuse Risk). Each area cites the Phase 3 evidence it reuses; write `none found` rather than dropping a heading. Duplication / Reuse Risk opens with the near-identical verdict: name the product and the elements it matches, or write `none found` and name every product that misses only one element (or, if none does, the one matching the most), with the element each misses.
  - Monetization opens with the `Plans to charge` line, copied from `idea.md` (SKILL.md → Terms). For `no`, still give the revenue path, and write `Willingness to pay: not assessed, the idea does not charge`; verdict rule 2's willingness-to-pay clause then does not apply, and its demand clause still does.
  - Technical Risk opens with the `Hard blockers` line, then gives every risk its own line with a label. Take the first match: certain to stop the MVP, and the stated team and budget cannot remove it however long it takes → move it to `Hard blockers` (verdict rule 1); would stop the MVP from working as described if it materializes, with no mitigation within the stated team, budget and timeline → `hard` (rule 2); anything else → `soft` (no verdict effect). A mitigation counts only if it fits the team, budget and timeline as `idea.md` records them. Where one of them is `unknown`, assume one developer, no paid spend and a 4-week MVP, and list each assumption on `Uncertainty:`. A hard blocker needs the team and budget to be stated: when either is `unknown`, an item that would otherwise be a blocker is labelled `hard` (rule 2) instead.
- `## Strengths` and `## Concerns`: the lists the Final Report takes its top 3 from. `## Concerns` names every hard blocker and `hard` risk.
- `## Ratings`: the four-row table, each score out of 10 with a one-line reason.

`prd-generator` and `product-planner` read `## Quick Verdict`, `## Why`, `## Ratings`, `## Strengths`, `## Concerns`, `## Competitive Landscape`, `## Enhanced Version` and `## Implementation Roadmap`; never rename or drop them. When a stop skips a phase, keep its headings and write `Not run — [reason]` under each.

## Phase 3 research method

Vary the wording across queries; each query goes in the Research Log under exactly one side.

| Side | Query patterns |
|---|---|
| Open source | `[problem] open source`, `[problem] self-hosted`, `[problem] GitHub`, `[category] OSS alternative to [paid leader]`, package-registry names (npm, PyPI, crates) |
| Paid & market — players | `[problem] SaaS pricing`, `[problem] platform`, `[problem] startup`, `best [category] tools [year]`, `[leader] alternatives`, `[category] app for [audience]`. Cover every commercial offering type: SaaS products, mobile apps, enterprise platforms, paid APIs, agencies, and marketplaces |
| Paid & market — share or size | `[category] market size [year]`, `[category] market share`, `[leader] revenue` or `ARR`, `[leader] customers`, `[leader] raises` or `funding` |
| Adjacent | `how [audience] [does the job] today`, `[related problem] tool` |
| Failed attempts | `[concept] startup failed`, `[concept] post-mortem`, `[concept] shut down`, `[concept] abandoned GitHub`; also check product directories |

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

**Sources.** Use only free, public sources: company sites, pricing pages, press releases, funding announcements and news, app-store listings, GitHub, public filings, and public reports or articles. A data provider's public page counts only when it is readable without payment, a trial, or a login. A paid report's free public summary counts for its headline figure: cite the summary page and never imply the full report was read. A figure from a paid provider quoted by a free page is cited as `[provider] via [free page]`, links the free page, and caps that row at `medium`. Never use a paid data service, and never write that one was used. Cite every figure with its link and year. A figure with no link is an assumption: it goes on the Final Report's `Uncertainty:` line and stays out of the Sourced figures column. The year is the one the source attaches to the figure; a page-modified or fetch date is not. When the source gives no year, keep the link, write `undated (checked YYYY-MM-DD)`, and rate that row `low`.

**Figures.** Prefer, in order: the company's own statement (annual filing, press release, about page, investor letter); reputable news reporting it; third-party estimates (app-store ranks, traffic estimators, review counts). Label a third-party figure as an estimate. Do not average or divide figures from different years or bases (for example, 2026 users against 2024 developers).

**Share or relative size.** Pick the first basis in this order that most players have: revenue, then paying customers, then users, then downloads or reviews, then traffic or employees. Name it in "Derived from". Rank roles (leader, challenger, long tail) on the same basis as the shares; a sub-market qualifier names a segment, not a basis.
- Write a precise share (`32%`) only when a source states it, and link that source.
- Otherwise derive it: player's figure ÷ the market-size estimate (share of market) or ÷ the sum over listed players (share of listed players; say so). Round to a range or `~N%`; never use decimals.
- When players lack a common basis, give relative size instead (`~3x the next player by paying customers`, `smallest of the four by reviews`). Never infer a share from relative size.

**Confidence labels.** Take the first row that matches, top to bottom, so the lowest applicable label wins. A credible source is the first two tiers of the **Figures** order (the company's own statement, or reputable news reporting it); a third-party estimate is the third tier, and so is a market-research firm's free public summary unless a credible source corroborates it.

| Label | Use when |
|---|---|
| `low` | Any of: the basis is a mixed or partial proxy (traffic, reviews, employees, funding); a key figure is undated or older than 3 years; the share rests on one uncorroborated third-party estimate |
| `medium` | Any of: exactly one credible source states the share; this row's share is derived over listed players, most but not all of whom have figures on a comparable basis; the share is derived from a sourced market-size estimate; a key figure is a paid provider's figure quoted by a free page |
| `high` | Two or more credible sources agree on the share, or every listed player has a figure on the same basis from the same year |

If no row matches (for example, credible sources disagree on the share), use `medium`.

**Market structure.** Judge it on the same basis as the shares, and state any different reading another basis gives. Its confidence is the lowest confidence among the Market Players & Share rows the signal compares (Dominated: the leader and the next player; otherwise every row with a figure). Take the first row that matches, top to bottom.

| Structure | Signal | For a newcomer |
|---|---|---|
| Dominated | The leader holds about half or more, or holds at least about a third and is about 3x or more the next player | Compete only on a segment the leader underserves, or integrate with it; head-on entry needs a real differentiator |
| Oligopoly | No single player holds about half, and 2-4 players together hold most of the market | Expect feature-matching; win on a segment, price point, or distribution channel they ignore |
| Fragmented | Anything else: no clear leader, or many small players | Entry is open, but willingness to pay may be low and distribution is the bottleneck |

**Relative size only.** When the shares fall back to relative size (no common basis), neither share signal can be checked, so use this rule instead of the table. Whichever label applies, the structure confidence is always `low`, whatever the rows' labels, and you write `shares not comparable` on the Market structure line and on the Final Report's `Uncertainty:` line.
- The leader is the player the comparisons show as largest.
- **Dominated**, only when the leader is about 5x or more (at least 4.5x) every other listed player, each comparison made on one basis: the same kind of figure for both players, named. When the two players share more than one basis, compare on the first in the basis order above (revenue, paying customers, users, downloads or reviews, traffic or employees). The long-tail row counts only when it has a figure, compared as its combined total.
- **Fragmented** otherwise, including when a listed player other than the long tail has no figure on a basis the leader also has.
- Never Oligopoly: it needs shares.

The verdict rules read the label with its confidence: `Dominated` at `medium` or `high` can trigger rule 1 (`Skip it`); at `low` it can trigger only rule 2 (`Maybe`), when there is no genuine differentiator or it is unevidenced. A Dominated label from relative size alone is therefore never a rule 1 trigger.

**Market size.** Give TAM, or a credible proxy for it (a public report's segment figure, the leader's revenue as a floor), with the source and year, labelled an estimate. If sources disagree, show the range and both sources. Label a broad category figure (for example "all IT operations software") as a ceiling, not the idea's TAM. If no credible figure exists, write so, then build a bottom-up proxy: target buyers (sourced count) × annual price (from the pricing table) ≈ size, with every input shown. For an idea that does not plan to charge, the proxy is the sourced count of target users. When no count of the exact target buyers is public, use the closest broader sourced count as a ceiling and label the narrowing an assumption.

**No paid players found.** Write `none found` in the players table with the paid queries tried, skip share and structure, still give a bottom-up market-size proxy, and treat willingness to pay as unproven in Phase 4 (it counts toward the verdict only for an idea that plans to charge).

**Size.** List up to 6 rows: the leader, the main challengers, and the long tail rolled up into one row. When the paid side splits into sub-markets the idea straddles, qualify the role per sub-market (`Leader (incident response)`), never per basis (not `Leader (reach)`).
