---
name: "viral-product-evaluator"
description: "Review a product codebase and landing page against 32 viral principles and produce a Virality Score plus ranked fixes. Use to audit virality or prioritize growth. Don't use for SEO, ASO, copywriting, or code review."
license: MIT
effort: high
dependencies:
  - browse
metadata:
  version: 1.7.0
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

Do **not** use for: technical SEO (`seo-ai-optimizer`), App Store ASO (`aso-marketing`),
turning a README into a page (`landing-page-generator`), or bug-hunting code review
(`code-review`).

## Prerequisites

- Read access to the target codebase directory.
- Landing page signal: public URL, local file, auto-detectable in the tree, or an
  orchestrator's `evidence-dir`.
- The skill's `references/*.md` files present.

Missing prerequisites after the one ask in Edge cases → stop with a BLOCKED response
(`references/final-report.md`) before gathering evidence.

## What this skill does and does not touch

It **reads** the codebase, **fetches** the landing page, and **writes one report file**
(`viral-evaluation.md`) — it never edits source, changes copy, or commits. Applying fixes is
a separate task for a copy/frontend skill; this skill stops at the prioritized plan.

## Dependency Preflight (mandatory)

This skill invokes `/browse` (frontmatter `dependencies`), and only on the **live URL** path;
every other input needs nothing installed. Run once, before the first fetch:

```bash
if test -f "$HOME/.claude/skills/browse/SKILL.md"; then
  echo "browse_mode=installed browse_skill=$HOME/.claude/skills/browse/SKILL.md"
elif test -f "$HOME/.agents/skills/browse/SKILL.md"; then
  echo "browse_mode=installed browse_skill=$HOME/.agents/skills/browse/SKILL.md"
elif command -v asm >/dev/null && asm deps --help >/dev/null 2>&1; then
  asm deps discover viral-product-evaluator --json || echo "discover failed; acquire still runs" >&2
  echo "browse_mode=lease"
else
  echo "Missing skill: browse. Install: asm install github:garrytan/gstack:browse -p claude -s global --yes" >&2
  echo "No asm yet: npm install -g agent-skill-manager@latest" >&2
  echo "browse_mode=none"
fi
printf 'vpe_session=%s\n' "viral-product-evaluator-$(date +%s)-$$"   # record it; reuse it verbatim
```

The install-path tests run first because gstack may install `/browse` without `asm` knowing.

1. `browse_mode=installed`: read the recorded `browse_skill` path.
2. `browse_mode=lease`: run `asm deps acquire browse --session <vpe_session> --json`; read the
   returned `skillMdPath` directly.
3. `browse_mode=none`, or step 2 failed: **fail-soft** — print the install lines, then ask the
   user for a local file or saved HTML of the page. Never score a URL you could not load.
4. **Release in `finally`.** If step 2 ran, run `asm deps release --session <vpe_session> --json`
   once at every terminal outcome, stops included.

## Repo Sync Before Edits (mandatory)

Phase 3 writes `viral-evaluation.md`. An inline-only run never syncs or stashes a checkout.
When the output path is inside a git worktree, follow `references/repo-sync.md`: confirm with
the user, then stash, sync and pop before the write.

## Inputs

1. **Landing page** — resolve in this order:
   - an orchestrator's **`evidence-dir`** → read its `page.html` + `head.json`; no `/browse`.
   - a **live URL** → run the Dependency Preflight, confirm the fetch with the user, then load
     it with the `/browse` skill (headless). Capture rendered copy, headline, CTAs, pricing
     section, testimonials, nav, and `<head>` meta (`og:image`, `twitter:image`, `description`,
     `<title>`).
   - a **local file** (`index.html`, a JSX/TSX/MDX page, a built `dist/`) → read it directly.
   - **auto-detect** from the codebase → search the common spots (`index.html`, `app/page.tsx`,
     `pages/index.*`, `src/App.*`, `landing/`, `marketing/`, `public/`). If exactly one
     candidate is found, use it. If none or several are found, ask the user.
2. **Codebase** — a path to the repo (defaults to the current working directory). Used for the
   pricing/paywall principles, the feature surface, and landing-page auto-detection.
3. **Extra instructions** (optional) — strategic context such as "we keep a free tier on
   purpose". Honor these when *interpreting* a verdict (note the deliberate deviation) but
   still score the principle as written so the number stays comparable.

## Pipeline (3 phases, in order)

### Phase 1 — Resolve inputs & gather evidence

1. Resolve the landing page per *Inputs*.
2. Locate the codebase (default: the current working directory).
3. Grep it for `price`, `plan`, `tier`, `checkout`, `subscription`, `free`, `trial`, `stripe`,
   `paddle` and read the matches.
4. Record the monetization evidence section A of the rubric lists (`references/principles.md`).
   When nothing matches, record "no billing evidence found" — that is itself evidence.
5. Skim routes, nav items and top-level modules; record a one-line feature inventory.
6. When the codebase is too large for the context budget, delegate steps 3–5 to a one-off
   **Agent** task scoped to pricing and feature evidence.
7. Note any extra instructions from the user.

### Phase 2 — Evaluate against the 32 principles

1. Read `references/principles.md` — the full rubric.
2. Score **every** principle PASS / PARTIAL / FAIL; never skip one. Absence of a thing a viral
   product would ship (pricing, testimonials, demo) is a real **FAIL**, not "unknown".
3. Quote product-specific evidence for each verdict — the actual headline, the actual tier,
   the file/line. Generic findings are not acceptable.
4. Tag every `judgment`/`visual` principle (hero punch, emotional headline, OG-image design,
   founder presence, novelty, price-vs-competitor) **low-confidence** and record what a human
   must eyeball. When a principle's evidence source was unavailable (no codebase access, a
   failed fetch), tag it low-confidence as well and say why.
5. Compute the **Virality Score** with `scripts/virality_score.py` — pass every verdict as
   `{"verdicts": {"<n>": "PASS|PARTIAL|FAIL", ...}}` (contract in `references/principles.md` →
   Scoring). Do not tally or round in prose.

### Phase 3 — Prioritize fixes & write the report

1. Read `references/report-template.md` and build the report in that exact shape: verdict
   block → scorecard (all 32) → top fixes → what's working → caveats.
2. Order the top fixes by **impact × ease**, hero/paywall/headline/proof/single-CTA first;
   merge principles sharing a root cause into one fix.
3. Make each fix concrete enough to act on — the actual proposed headline, the tier to cut,
   the CTA label — quoting **Now** and **Change**.
4. Print the verdict block and top fixes inline, then ask the user to confirm writing the
   report. One confirmation covers the write and, when the output path is inside a git
   worktree, the sync.
5. On confirmation: run `references/repo-sync.md` when needed, then write
   `viral-evaluation.md` to `output-dir`, else the repo root, else the current working
   directory.
6. When the user declines, return the full report inline and mark the run PARTIAL.
7. Close with the final response from `references/final-report.md`, including its status rule.

## Orchestrated Runs

With `orchestrated-by`, `evidence-dir`, `skip-checks` or `output-dir` lines, follow
`references/orchestrated-runs.md`; without them nothing changes. All 32 principles are
always scored.

## Honest evaluation

This is a critique tool — its value is candor. The full candor rules are in
`references/honest-evaluation.md`.

## Step Completion Reports

After each phase, emit the report from `references/step-reports.md` — **Gather Evidence**,
**Evaluate**, **Prioritize & Report**.

## Acceptance Criteria

- All 32 principles scored with product-specific evidence quoted.
- Virality Score and tier come from `scripts/virality_score.py` over all 32 verdicts;
  verdicts and evidence remain model-owned.
- Top fixes are concrete, prioritized by impact×ease, with before/after suggestions.
- Report written to viral-evaluation.md after the user's confirmation, or returned inline when
  declined; Step Completion Reports emitted per phase.
- The final response follows `references/final-report.md`: `Result: PASS | PARTIAL | BLOCKED`
  first, then Evidence, Uncertainty and Decision.
- Reader checks: main result findable in the first line, facts separated from assumptions,
  claims traceable to evidence, next decision clear.
- Negative-trigger domains respected (no SEO/ASO/copy/code-review work).

## Expected output

A `viral-evaluation.md` report (plus an inline summary and a `Result:`-first final response)
containing:
- Overall verdict + Virality Score (e.g. 68 — Promising)
- Scorecard table for all 32 principles
- Top 5-8 prioritized fixes with exact copy or code recommendations
- What's already working
- Caveats / low-confidence items

## Edge cases

- No landing page: ask once for a URL or file; if the user confirms none exists, score
  codebase-only (LP principles FAIL with a caveat); without an answer, end BLOCKED. Never
  fabricate a page.
- `/browse` missing for a live URL: fail-soft per the Dependency Preflight.
- Strategic deviation (e.g. no testimonials by design): score as written, note the trade-off
  in caveats.
- Partial evidence (a fetch failed mid-run): mark affected principles low-confidence, never
  guess a PASS.
- User declines the report write: return the report inline; the run is PARTIAL.
- Output path inside a git worktree: confirm, then sync per `references/repo-sync.md` before
  writing.

---

## Reference files

- `references/principles.md` — the 32-principle rubric: per-principle checks, evidence source,
  PASS/PARTIAL/FAIL bars, confidence flags, and the `scripts/virality_score.py` scoring
  contract. **Load every run.**
- `references/report-template.md` — the exact report shape, with a calibration example.
- `references/final-report.md` — the final chat response: status rule (PASS / PARTIAL /
  BLOCKED), response shapes, and the reader-check criteria.
- `references/repo-sync.md` — the confirm-first sync procedure for an output path inside a git
  worktree.
- `references/step-reports.md` — Step Completion Report formats for the three phases.
- `references/honest-evaluation.md` — the candor rules: no inflation, no invented flaws,
  labelled low-confidence.
- `scripts/virality_score.py` — deterministic Virality Score + tier helper (`tests/` holds its
  stdlib fixtures).
