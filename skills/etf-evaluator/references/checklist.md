# ETF Evaluation — 10-Point Checklist & Rating Thresholds

Read this in **Phase 3** (to know what to gather) and **Phase 4** (to know how to rate it). Every
figure must be cited or marked `Unverified` — see the Data Integrity Policy in SKILL.md.

The thresholds below are **goal-relative**. "Core" = broad-market core holding (MSCI World, FTSE
All-World, S&P 500). "Thematic" = sector / single-country / factor / niche bet. When a row gives both,
rate against the column that matches the Phase-1 goal. Thresholds are heuristics for consistency, not
hard law — note when a fund is a borderline or special case.

---

## Core 5 (most important)

### 1. Tracking Error & Tracking Difference
- **What it is:** Tracking *difference* = the fund's return minus the index return over a period (the
  figure that actually costs you; can be negative or, rarely, positive). Tracking *error* = the
  volatility/std-dev of that gap (consistency). Together they tell you how faithfully the fund
  delivers the index.
- **Gather:** published tracking difference / error from the factsheet, justETF "tracking difference"
  table, or annual report. If not published, infer roughly from fund-vs-benchmark return columns and
  say so. **Tracking *difference* is frequently absent from free pages while tracking *error* is
  shown — that gap is expected;** mark the missing one `Unverified` rather than forcing a number.
- **Rate (use whichever metric you actually have):**
  - **Good** — tracking difference within roughly ±(TER) of the index; *or*, if only tracking error is
    available, a small (≈≤ TER) and stable error. Rate on the metric you have and say which one.
  - **Fair** — difference a few tenths of a % worse than TER, only one year available, or a noticeably
    elevated error.
  - **Poor** — persistent large drag well beyond TER, or erratic year-to-year.
  - `Unverified` — neither metric found and nothing can be inferred. (Having error but not difference
    is **not** `Unverified` — rate on the error and mark the difference unverified in the value cell.)

### 2. Expense Ratio (TER / OCF) & Total Cost
- **What it is:** Annual ongoing charge. The single most reliable predictor of long-run net return for
  a passive fund. Total cost also includes spread + brokerage + tax drag (covered in #10 and #7).
- **Gather:** TER / OCF from KIID/KID or factsheet.
- **Rate (core):** **Good** < 0.20% · **Fair** 0.20–0.40% · **Poor** > 0.40%.
- **Rate (thematic):** **Good** < 0.35% · **Fair** 0.35–0.60% · **Poor** > 0.60%.
  (Thematic/active-ish ETFs run pricier; judge against peers on the *same* theme.)

### 3. Assets Under Management (AUM) & Liquidity
- **What it is:** Fund size. Small funds are likelier to be closed/merged (forcing a taxable exit) and
  often have wider spreads. Liquidity = how easily you can trade at a fair price.
- **Gather:** AUM (note currency and whether it's the share-class or whole-fund figure), fund age,
  average daily volume.
- **Rate:** **Good** > €/$500M (closure-safe) · **Fair** €/$100–500M (healthy but watch) · **Poor** <
  €/$100M, especially if also > ~3–5 yrs old and still tiny (closure risk). A brand-new fund from a
  major issuer with fast inflows can be "Fair" despite low AUM — note the trajectory.

### 4. Replication Method & Fund Structure
- **What it is:** *Physical full* (holds all index constituents), *physical sampled/optimised* (holds
  a representative subset), or *synthetic* (swap-based — introduces counterparty risk but can track
  tightly and access hard markets). Structure = legal wrapper (e.g. **UCITS** = EU-regulated, strong
  investor protections; US-domiciled ≠ UCITS).
- **Gather:** replication method, UCITS yes/no, fund structure from factsheet/KIID.
- **The common middle case:** providers label the same fund inconsistently — "physical full" vs
  "optimized sampling" — for a broad index where the fund holds the top ~85–95% of constituents and
  skips the micro-cap tail. **Resolve it with the holdings ratio, not the label:** report "holds X of Y
  index stocks" and treat ≳85% physical coverage as effectively full replication (no counterparty
  risk). Only call it true "sampled" when coverage is materially lower. This is **not** synthetic.
- **Rate:** **Good** — physical full or well-run sampled (≳85% coverage), UCITS (for EU investors).
  **Fair** — synthetic from a reputable issuer with disclosed swap counterparties / collateral, or
  heavy sampling (low coverage). **Poor** — opaque synthetic, undisclosed counterparty, or a structure
  that doesn't fit the user's jurisdiction. Synthetic is not "bad" per se — flag the counterparty risk
  and let the goal decide.

### 5. Index Quality & Fund Characteristics
- **What it is:** What the index actually tracks, its methodology, breadth, and concentration. A
  100-stock cap-weighted tech index behaves very differently from a 1,500-stock world index.
- **Gather:** index name + provider (MSCI, FTSE, S&P, Solactive…), number of holdings, top-10 weight,
  sector/country weights, rebalancing frequency.
- **Rate:** **Good** — broad, transparent, rules-based, well-diversified for its mandate, low
  single-name concentration. **Fair** — narrower or more concentrated but still rules-based. **Poor** —
  tiny holdings count, extreme single-name/sector concentration the user isn't aware of, or an opaque
  proprietary index. (For a *thematic* fund, concentration is expected — judge whether it's reasonable
  for the theme, not against a world index.)

---

## Bonus 5 (important context)

### 6. Historical Performance & Risk Metrics
Returns vs benchmark over 1/3/5-yr and since inception; volatility, max drawdown, Sharpe if available;
behaviour in past stress (2008, 2020 COVID, 2022 bear). **Past performance ≠ future returns** — use it
to check tracking and risk character, not to predict. **Explicit fund-vs-benchmark return columns and
max drawdown are often not on free pages** — if you only have *absolute* returns, say so and rate on
tracking faithfulness rather than dressing absolute returns up as benchmark-relative data; mark the
missing pieces `Unverified`. **Good** — tracks benchmark closely with risk in line with the asset
class. **Poor** — large unexplained underperformance or risk far above peers.

### 7. Dividend Policy & Tax Efficiency
**Accumulating** (reinvests dividends — simpler compounding, often better for growth/EU investors) vs
**Distributing** (pays out — useful for income). Check **domicile** (Ireland/Luxembourg are often most
tax-efficient for Europeans via favourable US withholding-tax treaties) and how the user's residence
taxes the chosen structure. **Good** — domicile + distribution type fit the user's goal and tax
situation. **Poor** — tax-inefficient domicile for this investor (e.g. a US-domiciled fund triggering
extra withholding/estate exposure for an EU resident).

### 8. Provider Reputation & ETF Stability
Issuer track record (Vanguard, iShares/BlackRock, Amundi, SPDR/State Street, Invesco, Xtrackers…),
history of closures/mergers, reporting quality. **Good** — large, established issuer, clean record.
**Fair** — smaller/newer issuer, thin history. **Poor** — issuer with frequent closures or poor
disclosure.

### 9. Portfolio Fit & Diversification Impact
How this ETF overlaps with what the user already holds (sector/country/single-name overlap),
correlation, and its marginal risk contribution. A second S&P 500 fund adds little; a world ex-US fund
might fill a gap. Flag overlap and concentration the addition would create. (If the user shared no
existing holdings, note this is assessed in isolation.)

### 10. Trading Costs & Accessibility
Bid-ask spread, availability on the user's broker, exchange/currency (and whether a **hedged** vs
**unhedged** share class fits their currency view), minimum investment, and savings-plan eligibility.
**Broker / savings-plan availability has no neutral primary source** — no factsheet publishes it; you'll
only find secondary blogs or the in-app catalog. Cite what you can and tell the user to **confirm in
their broker app** — that's the honest answer, not a defect.
**Good** — tight spread, available on their broker in their currency, savings-plan compatible. **Poor**
— wide spread, not on their platform, or wrong-currency-only.

---

## Putting it together

- Weight the **Core 5** more heavily than the **Bonus 5** in the verdict.
- A single **Poor** on a Core item (e.g. closure-risk AUM, or a tax-toxic domicile for this investor)
  can justify **Avoid** or **Consider** even if everything else is Good.
- **Core holdings:** prioritise ultra-low TER + high liquidity + faithful tracking + efficient
  domicile. Be strict.
- **Thematic/sector holdings:** accept higher cost/volatility *only* with genuine conviction, and
  recommend a position cap (typically 5–15% of portfolio). Be explicit that it's a satellite, not a
  core.
