---
name: "viral-product-evaluator"
description: "Review a product codebase and landing page against 32 viral principles and produce a Virality Score plus ranked fixes. Use to audit virality or prioritize growth. Don't use for SEO, ASO, copywriting, or code review."
license: MIT
effort: high
metadata:
  version: 1.6.0
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
turning a README into a page (`landing-page-generator`), or bug-hunting code review
(`code-review`). This skill
**evaluates and prioritizes**; it does not rewrite the product.

## Prerequisites

- Read access to the target codebase directory.
- Landing page signal: public URL, local file, or auto-detectable in the tree.
- The skill's `references/*.md` files present for the rubric and output shape.

Missing prerequisites → stop and report before gathering evidence.

## What this skill does and does not touch

It **reads** the codebase, **fetches** the landing page, and **writes one report file**
(`viral-evaluation.md`). It does **not** edit the user's source, change copy, or commit
anything — so no repo-sync/branch guardrail is needed. If the user then asks you to *apply*
fixes, that is a separate task (hand off to a copy/frontend skill); this skill stops at the
prioritized plan.

## Dependency Preflight (mandatory)

This skill invokes `/browse`, and only on the **live URL** path — a local file, an
auto-detected page, or an orchestrator's `evidence-dir` needs nothing installed. Resolve it before fetching anything:

```bash
test -d "$HOME/.claude/skills/browse" || asm list -p claude --json | grep -q '"browse"' || {
  echo "Missing required skill: browse" >&2
  echo "Install it:      asm install github:garrytan/gstack:browse -p claude -s global --yes" >&2
  echo "No asm yet:      npm install -g agent-skill-manager" >&2
  echo "Verify:          asm list -p claude --json | grep 'browse'" >&2
}
```

The install-path test runs first because `/browse` ships in gstack and may be present without
`asm` knowing about it. `-p claude -s global` is required: `asm install` will not guess a provider
non-interactively, and a project-scoped install lands where the `$HOME` test cannot see it.

A missing `/browse` is **fail-soft**, not fatal: print the commands above, then ask the user for a
local file or saved HTML of the page. Never score a URL you could not load — do not invent one.

## Repo Sync Before Edits (mandatory)

Phase 3 writes `viral-evaluation.md` to the repo root or current working directory. When that path lives inside a git worktree, sync before the write to avoid clobbering remote work:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If the working tree is dirty: stash → sync → pop. If `origin` is missing or a conflict occurs: **stop and ask the user.** Skip this section only when the output path is outside any git repository.

## Inputs

Accept any combination the user provides; ask only for what's missing and truly needed.

1. **Landing page** — one of:
   - a **live URL** → fetch it with the `/browse` skill (headless). Capture rendered copy,
     headline, CTAs, pricing section, testimonials, nav, and `<head>` meta (`og:image`,
     `twitter:image`, `description`, `<title>`).
   - a **local file** (`index.html`, a JSX/TSX/MDX page, a built `dist/`) → read it directly.
   - an orchestrator's **`evidence-dir`** → read its `page.html` + `head.json`; no `/browse`.
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

- Resolve the landing page input (`evidence-dir` → saved files; URL → `/browse`; file → read; else auto-detect).
- Locate the codebase and find **monetization evidence**: billing SDKs (Stripe, Paddle,
  LemonSqueezy, RevenueCat, Chargebee), pricing config/constants, plan & tier definitions,
  paywall/auth gating, trial logic. Grep for `price`, `plan`, `tier`, `checkout`,
  `subscription`, `free`, `trial`, `stripe`, `paddle`.
- Skim the **feature surface** (routes, nav items, top-level modules) to judge "does one thing".
- For a large codebase, use **grep/read** (or a one-off **Agent** task scoped to pricing +
  feature evidence) so the main context stays clean. Collect: tier list, billing type (one-time
  vs subscription), free-plan yes/no, and a one-line feature inventory.
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
- Compute the **Virality Score** with `scripts/virality_score.py`: pass every verdict as
  `{"verdicts": {"<principle number>": "PASS|PARTIAL|FAIL", ...}}` and use the helper's
  `counts`, `score`, and `tier` (contract in `references/principles.md` → Scoring). Do not
  tally or round in prose.

### Phase 3 — Prioritize fixes & write the report

- Read `references/report-template.md` and produce the report in that exact shape:
  **verdict block → scorecard (all 32) → top fixes (prioritized) → what's working → caveats**.
- The **top fixes** list is the core deliverable. Order by **impact × ease**, hero/paywall/
  headline/proof/single-CTA first. Merge principles that share a root cause into one fix. Make
  each fix concrete enough to act on (give the actual proposed headline, the tier to cut, the
  CTA label) — quote what it is **Now** and what to **Change** it to.
- Always write the report to `viral-evaluation.md` — `output-dir` when given, else repo root, or
  the current working directory when there is no repo — and also print the verdict block + top
  fixes inline.

## Orchestrated Runs

With `orchestrated-by`, `evidence-dir`, `skip-checks` or `output-dir` lines, follow
`references/orchestrated-runs.md`; without them nothing changes. All 32 principles are
always scored.

## Honest evaluation

This is a critique tool — its value is candor: never inflate scores, never invent flaws, label low-confidence verdicts. The full candor rules are in `references/honest-evaluation.md`.

## Step Completion Reports

After each phase, emit the report from `references/step-reports.md`. The three phases are
**Gather Evidence**, **Evaluate**, and **Prioritize & Report**.

## Acceptance Criteria

- All 32 principles scored with specific evidence quoted from the product.
- Virality Score and tier come from `scripts/virality_score.py` over all 32 verdicts
  (PASS=1, PARTIAL=0.5, FAIL=0); per-principle verdicts and evidence remain model-owned.
- Top fixes are concrete, prioritized by impact×ease, with before/after suggestions.
- Report always written to viral-evaluation.md (`output-dir`, else repo root, else the current working directory) and
  also printed inline; Step Completion Reports emitted per phase.
- Negative-trigger domains respected (no SEO/ASO/copy/code-review work).

## Expected output

A report containing:
- Overall verdict + Virality Score (e.g. 68 — Promising)
- Scorecard table for all 32 principles
- Top 5-8 prioritized fixes with exact copy or code recommendations
- What's already working
- Caveats / low-confidence items

## Edge cases

- No landing page detectable: ask for URL or file; do not fabricate.
- Codebase only (no public page): still score what can be inferred from code (pricing etc).
- Strategic deviation justified by user (e.g. no testimonials by design): score as written, note the trade-off in caveats.
- Partial evidence: mark affected principles low-confidence, never guess a PASS.

---

## Reference files

- `references/principles.md` — the 32-principle rubric: per-principle checks, evidence source,
  PASS/PARTIAL/FAIL bars, confidence flags, and the `scripts/virality_score.py` scoring
  contract. **Load every run.**
- `references/report-template.md` — exact output shape (verdict block, scorecard, prioritized
  fixes, strengths, caveats) with a calibration example.
- `references/step-reports.md` — Step Completion Report formats for the three phases.
- `references/honest-evaluation.md` — the full candor rules: no inflation, no invented flaws,
  labelled low-confidence, stop on fetch/read failure.
- `scripts/virality_score.py` — deterministic Virality Score + tier helper (`tests/` holds its
  stdlib fixtures).
