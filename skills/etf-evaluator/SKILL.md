---
name: "etf-evaluator"
description: "Vet, review, or compare an ETF / index fund before investing: cite its TER, AUM, tracking, replication, domicile, then score it Invest / Consider / Avoid as an HTML report. Not for individual stocks, active funds, crypto, bonds, or rebalancing."
license: MIT
effort: high
metadata:
  version: 1.2.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# ETF Evaluator

Evaluate an index fund / ETF against a 10-point checklist and produce a **goal-relative** scored
report with a clear **Invest / Consider / Avoid** verdict, rendered as a **single self-contained
HTML file** (no external dependencies). Research every figure from a live source, cite it, and mark
anything you cannot verify as `Unverified` — never guess.

## When to Use

Trigger when the user wants to:
- Evaluate, vet, review, or score an ETF / index fund before buying it
- Decide whether a specific ETF (by name or ISIN) is worth investing in
- Compare similar ETFs tracking the same index (TER, AUM, replication, performance)
- Build a scorecard / due-diligence report for an index fund

Do **not** use for: picking individual stocks, evaluating active (stock-picking) mutual funds or
hedge funds, crypto tokens, single-bond analysis, or rebalancing an existing portfolio. This skill
evaluates **one passive index fund at a time** and reports; it does not place trades or give
personalized financial advice.

## Data Integrity Policy (read first — this is the spine of the skill)

The output drives real money decisions. A fabricated TER, AUM, or domicile can cost the user real
losses. Therefore:

1. **Every figure must come from a live source and be cited.** Acceptable sources: the provider's
   official factsheet / KIID / KID / annual report, justETF, Morningstar, ETF.com, or the exchange
   listing page. No number reaches the scorecard without a source link or document name. **When
   sources conflict, trust them in this order:** provider official document > justETF / Morningstar >
   secondary blogs/forums. A stale snippet that disagrees with the primary source loses — cite the
   primary value and note the discrepancy.
2. **`Unverified` is a valid, expected value.** If you cannot find or confirm a figure, write
   `Unverified` (or `Not found`) in that cell. Admitting a gap is correct; guessing is a defect.
3. **Your training knowledge is stale and off-limits for live figures.** TER, AUM, spreads, and
   holdings drift over time. Do not fill any live figure from memory — fetch it. **Date-stamp every
   data pull** ("as of YYYY-MM-DD") so the user knows the snapshot's age.
4. **Anchor on the ISIN, not the marketing name.** Names like "Amundi MSCI World Financials" are
   ambiguous across share classes (accumulating vs distributing), currencies, and listings. Confirm
   the exact ISIN and share class before evaluating, or you may score the wrong instrument.
5. **Not financial advice.** End every report with the one-line disclaimer (see scorecard template).

If web research tools are unavailable in the current environment, say so plainly and ask the user to
paste the factsheet / KIID text rather than inventing figures.

## Pipeline

Follow these six phases in order. Emit a Step Completion Report after each phase (see "Step Reports").

### Phase 1 — Capture Goal

Establish how the ETF will be used, because the rubric is **goal-relative** (a core holding is judged
on ultra-low cost and liquidity; a thematic/sector bet tolerates higher cost with a capped position).

Ask the user (via AskUserQuestion) — but if they just want a quick read, **default to "core holding"**
and proceed rather than blocking:
- **Role:** core broad-market holding, or satellite / sector / thematic / factor bet?
- **Horizon & risk tolerance:** how long, how much volatility can they stomach?
- **Context:** their broker/platform, base currency, and tax domicile (affects withholding tax &
  which fund domicile is efficient — e.g. Ireland/Luxembourg for many EU investors).

Record the goal; it sets the rating thresholds in Phase 4.

### Phase 2 — Identify the Exact Instrument

- Get the **ISIN** (ask if only a name was given, or resolve it via search and confirm with the user).
- Confirm: full fund name, share class (acc / dist), fund currency, and the exchange/listing the user
  will trade on.
- State what index it tracks and confirm it matches the user's intent (e.g. MSCI World ≠ MSCI World
  Financials). Misidentification here invalidates everything downstream.

### Phase 3 — Acquire & Cite Data

Research the web and pull figures for the 10-point checklist. Read `references/checklist.md` for the
full list of what each point requires. For each data point: fetch from a real source, record the
**value + source + as-of date**, or mark `Unverified`. Prioritise the official factsheet/KIID, then
justETF / Morningstar, then the provider site and exchange page.

Minimum to gather: TER, AUM, replication method (physical full/sampled vs synthetic), fund domicile &
structure (e.g. UCITS), distribution policy (acc/dist), index name + holdings count + top-10
concentration, tracking difference/error if published, 1/3/5-yr & since-inception performance vs
benchmark, bid-ask spread / average volume, provider, and inception date.

Several fields are **routinely not on free pages** — tracking *difference* (vs tracking error),
max drawdown, explicit fund-vs-benchmark return columns, and broker/savings-plan availability. Marking
these `Unverified` is **expected, not a failure**; only the official annual report or a paid data
service usually carries them. Don't let a few expected gaps make Phase 3 look like it failed.

### Phase 4 — Evaluate Against the 10-Point Checklist

Rate each criterion **Good / Fair / Poor / Unverified** using the goal-relative thresholds in
`references/checklist.md` (e.g. core broad-market TER < 0.20% = Good; AUM > €100M healthy, > €500M
closure-safe). Note the reasoning and the source for each rating. Apply the Phase-1 goal: the same TER
can be "Good" for a niche thematic ETF and "Fair" for a core index fund.

### Phase 5 — Compare Similar ETFs

Surface **1–2 alternatives tracking the same (or near-identical) index** and compare them on TER, AUM,
replication, domicile, and tracking. This is often the highest-value section — a cheaper, larger,
better-domiciled twin can flip the decision. Cite each alternative's figures too.

### Phase 6 — Score, Decide & Deliver

- Fill the scorecard data model in `references/scorecard-template.md` (this defines **what** to
  collect; it is not the output format).
- Give a clear verdict: **Invest / Consider / Avoid**, justified by the goal and the ratings.
- For thematic/sector ETFs, recommend a position-size cap (e.g. 5–15% of portfolio) when conviction is
  required.
- Include the data-as-of date, source list, and the not-financial-advice disclaimer.
- **Render the full report as a single self-contained HTML file** using the template in
  `references/html-output-template.md`. Follow every rule in that template (no external deps, escape
  all dynamic text, use verdict/rating CSS classes, replace every placeholder).
- Save the file to `~/etf-evaluations/<ISIN>_etf_evaluation.html` (or `~/etf-evaluations/<TICKER>_etf_evaluation.html`
  if no ISIN was confirmed). Create the directory if it does not exist.
- Echo the absolute file path to the user. Do not render the Markdown in chat — the HTML file is
  the deliverable.

## Step Reports

After each phase, emit a Step Completion Report so the user can follow the due-diligence trail:

```
◆ [Phase Name] (step N of 6)
··································································
  [Check 1]:          √ pass
  [Check 2]:          √ pass (note)
  [Check 3]:          × fail — [reason]
  ____________________________
  Result:             PASS | PARTIAL | FAIL
```

Suggested checks per phase — **Capture Goal:** `Role defined`, `Horizon/tax captured`; **Identify:**
`ISIN confirmed`, `Index matches intent`, `Share class confirmed`; **Acquire Data:** `Sources cited`,
`As-of dates recorded`, `Gaps marked Unverified`; **Evaluate:** `All 10 rated`, `Thresholds applied`,
`Goal-relative`; **Compare:** `≥1 alternative cited`; **Deliver:** `Verdict given`, `Disclaimer
present`, `HTML file saved`, `Path echoed`.

## Reference Files

- `references/checklist.md` — the 10-point checklist in full, plus the Good/Fair/Poor rating
  thresholds (read this in Phase 3 and Phase 4).
- `references/scorecard-template.md` — the data model for the scorecard (what to collect).
- `references/html-output-template.md` — the HTML rendering contract (how to present it). Read this
  in Phase 6.