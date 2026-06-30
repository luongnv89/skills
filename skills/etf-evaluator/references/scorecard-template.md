# ETF Evaluation — Output Report Template

Read this in **Phase 6**. Fill every bracket. Keep cited figures with their source + as-of date.
Any figure you could not verify stays as `Unverified` — do not fill it from memory.

---

```markdown
# ETF Evaluation: [Full Fund Name] ([TICKER])

**ISIN:** [ISIN] · **Share class:** [Acc / Dist] · **Fund currency:** [CCY] · **Listing:** [Exchange]
**Index tracked:** [Index name + provider]
**Evaluated for:** [Core holding / Satellite-thematic] · **Investor context:** [broker / base currency / tax domicile]
**Data as of:** [YYYY-MM-DD] · **Sources:** factsheet/KIID, justETF, Morningstar, etc.

## Verdict: ✅ Invest / 🟡 Consider / ⛔ Avoid

[2–4 sentences: the decision and the single most important reason, tied to the goal. For a thematic
ETF, state the recommended position cap, e.g. "satellite only — cap at 5–15% of portfolio."]

## Scorecard

| # | Criterion | Rating | Value (with source + as-of) | Notes |
|---|-----------|--------|-----------------------------|-------|
| 1 | Tracking Error / Difference | [Good/Fair/Poor/Unverified] | [e.g. −0.18%/yr 3-yr, justETF 2026-06] | [reasoning] |
| 2 | Expense Ratio (TER/OCF) & Cost | [...] | [e.g. 0.22%, KIID] | [vs goal threshold] |
| 3 | AUM & Liquidity | [...] | [e.g. €4.2bn, factsheet] | [closure risk / spread] |
| 4 | Replication & Structure | [...] | [e.g. Physical full, UCITS, IE domicile] | [counterparty note] |
| 5 | Index Quality & Characteristics | [...] | [e.g. 1,400 holdings, top-10 22%] | [concentration] |
| 6 | Historical Performance & Risk | [...] | [1/3/5-yr vs benchmark; max DD] | [stress behaviour] |
| 7 | Dividend Policy & Tax Efficiency | [...] | [Acc, Ireland-domiciled] | [fit for investor] |
| 8 | Provider Reputation & Stability | [...] | [e.g. iShares/BlackRock] | [closure history] |
| 9 | Portfolio Fit & Diversification | [...] | [overlap with holdings] | [marginal risk] |
| 10 | Trading Costs & Accessibility | [...] | [spread, broker, savings plan] | [currency/hedge] |

**Core-5 summary:** [N Good / N Fair / N Poor / N Unverified]
**Bonus-5 summary:** [N Good / N Fair / N Poor / N Unverified]

## Comparison vs Similar ETFs (same / near-identical index)

| Fund (ISIN) | TER | AUM | Replication | Domicile | Tracking | Note |
|-------------|-----|-----|-------------|----------|----------|------|
| **[This fund]** | [..] | [..] | [..] | [..] | [..] | evaluated |
| [Alternative 1](URL) | [..] | [..] | [..] | [..] | [..] | [cheaper/larger/…] |
| [Alternative 2](URL) | [..] | [..] | [..] | [..] | [..] | [..] |

[1–2 sentences: does a twin beat it? Would you pick this one or an alternative, and why?]

## Key Risks

- [Currency / sector-concentration / counterparty (if synthetic) / closure / tax / geopolitical]
- [Stress-test note: how it likely behaves in a 2008- or 2022-style drawdown]

## Bottom Line

[1–3 sentences. Restate verdict, the position-size guidance if thematic, and what (if anything) the
user should verify or watch (e.g. "re-check AUM in 12 months", "confirm it's on your broker's savings
plan").]

---
*Data as of [YYYY-MM-DD]. Figures marked "Unverified" could not be confirmed from a public source and
should be checked on the official factsheet before investing. This is an educational evaluation, **not
personalized financial advice**; past performance does not guarantee future results. Do your own
research.*
```

## Filling rules
- Lead with the **Verdict** — readers want the decision first.
- Keep each scorecard cell's **source + as-of date** so the user can audit any number.
- If the Core-5 contains any `Poor` or multiple `Unverified`, the verdict should not be a clean
  "Invest" — explain the reservation.
- For a **core** fund, weight cost + liquidity + tracking + domicile. For a **thematic** fund, always
  attach a position-size cap and label it a satellite.
