---
name: "viral-product-evaluator"
description: "Grade a product's codebase and landing page against 32 viral-product principles into a Virality Score and ranked fix list. Use to make a product more viral, audit a landing page, or score a SaaS. Not for SEO, ASO, writing copy, or code review."
license: MIT
effort: high
metadata:
  version: 1.1.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Viral Product Evaluator

Grade a product against the 32 principles of viral products. Two inputs — a **codebase** and a
**landing page** — produce one output: a scored report of **what's already satisfied** and, in
**priority order, what to do next to make it more viral**.

## When to Use

Trigger when the user wants to:
- Make a product, SaaS, or indie app "more viral" or more shareable
- Score / audit a landing page against viral-marketing or conversion principles
- Get a prioritized, ordered list of changes to improve a product's pull
- Check a product against "the 32 principles" (Marc Lou-style viral-product rules)

Do **not** use for: technical SEO (`seo-ai-optimizer`), App Store ASO (`aso-marketing`),
writing landing-page copy from scratch (`landing-page-copywriter`), turning a README into a
page (`readme-to-landing-page`), or bug-hunting code review (`code-review`). This skill
**evaluates and prioritizes**; it does not rewrite the product.

## What this skill does and does not touch

It **reads** the codebase, **fetches** the landing page, and **writes one report file**
(`viral-evaluation.md`). It does **not** edit the user's source, change copy, or commit
anything — so no repo-sync/branch guardrail is needed. If the user then asks you to *apply*
fixes, that is a separate task (hand off to a copy/frontend skill); this skill stops at the
prioritized plan.

## Inputs

Accept any combination the user provides; ask only for what's missing and truly needed.

1. **Landing page** — one of:
   - a **live URL** → fetch it with the `/browse` skill (headless). Capture rendered copy,
     headline, CTAs, pricing section, testimonials, nav, and `<head>` meta (`og:image`,
     `twitter:image`, `description`, `<title>`).
   - a **local file** (`index.html`, a JSX/TSX/MDX page, a built `dist/`) → read it directly.
   - **auto-detect** from the codebase → search for the landing/marketing page (common spots:
     `index.html`, `app/page.tsx`, `pages/index.*`, `src/App.*`, `landing/`, `marketing/`,
     `public/`). Confirm the candidate with the user if ambiguous.
2. **Codebase** — a path to the repo (defaults to the current working directory). Used for the
   pricing/paywall/subscription principles, the feature surface ("does one thing"), and to
   locate the landing page if no URL/file was given.
3. **Extra instructions** (optional) — strategic context such as "we keep a free tier on
   purpose", "target audience is developers", "we must stay subscription". Honor these when
   *interpreting* a verdict (note the deliberate deviation) but still score the principle as
   written so the number stays comparable.

If neither a URL, a file, nor a detectable page exists, stop and ask the user where the landing
page lives — do not invent one.

## Pipeline (3 phases, in order)

Run these in sequence. Emit the matching Step Completion Report (see
`references/step-reports.md`) after each.

### Phase 1 — Resolve inputs & gather evidence

- Resolve the landing page input (URL → `/browse`; file → read; else auto-detect).
- Locate the codebase and find **monetization evidence**: billing SDKs (Stripe, Paddle,
  LemonSqueezy, RevenueCat, Chargebee), pricing config/constants, plan & tier definitions,
  paywall/auth gating, trial logic. Grep for `price`, `plan`, `tier`, `checkout`,
  `subscription`, `free`, `trial`, `stripe`, `paddle`.
- Skim the **feature surface** (routes, nav items, top-level modules) to judge "does one thing".
- For a large codebase, spawn an **Explore** subagent to collect the pricing + feature evidence
  so the main context stays clean. Give it the grep targets above and ask for: tier list,
  billing type (one-time vs subscription), free-plan yes/no, and a one-line feature inventory.
- Note any extra instructions from the user.

### Phase 2 — Evaluate against the 32 principles

- Read `references/principles.md` — the full rubric. Score **every** principle PASS / PARTIAL /
  FAIL using its criteria. Do not skip any; absence of a thing a viral product would ship
  (pricing, testimonials, demo) is a real **FAIL**, not "unknown".
- For each verdict, capture **specific evidence from THIS product** — quote the actual headline,
  name the actual tier, cite the file/line. Generic findings are not acceptable.
- Tag every `judgment`/`visual` principle (hero punch, emotional headline, OG-image design,
  founder presence, novelty, price-vs-competitor) as **low-confidence** and record what a human
  must eyeball.
- Compute the **Virality Score**: `PASS=1, PARTIAL=0.5, FAIL=0`, summed over 32, ×100/32,
  rounded. Assign the tier (Viral-ready / Promising / Needs work / Not viral yet).

### Phase 3 — Prioritize fixes & write the report

- Read `references/report-template.md` and produce the report in that exact shape:
  **verdict block → scorecard (all 32) → top fixes (prioritized) → what's working → caveats**.
- The **top fixes** list is the core deliverable. Order by **impact × ease**, hero/paywall/
  headline/proof/single-CTA first. Merge principles that share a root cause into one fix. Make
  each fix concrete enough to act on (give the actual proposed headline, the tier to cut, the
  CTA label) — quote what it is **Now** and what to **Change** it to.
- Write the report to `viral-evaluation.md` (repo root or beside the landing-page source) and
  also print the verdict block + top fixes inline.

## Honest evaluation

This is a critique tool — its value is candor. Do not inflate scores to be encouraging. If the
hero fails, say it fails and show the fix. At the same time, do not invent flaws: a genuine PASS
is a PASS. Low-confidence verdicts must be labeled, never laundered into false certainty. When
extra instructions justify a deliberate deviation (e.g. a strategic free tier), score the
principle as written and explain the trade-off in the caveats — don't silently pass it.

## Step Completion Reports

After each phase, emit the report from `references/step-reports.md`. The three phases are
**Gather Evidence**, **Evaluate**, and **Prioritize & Report**.

## Reference files

- `references/principles.md` — the 32-principle rubric: per-principle checks, evidence source,
  PASS/PARTIAL/FAIL bars, confidence flags, and the scoring formula. **Load every run.**
- `references/report-template.md` — exact output shape (verdict block, scorecard, prioritized
  fixes, strengths, caveats) with a calibration example.
- `references/step-reports.md` — Step Completion Report formats for the three phases.
