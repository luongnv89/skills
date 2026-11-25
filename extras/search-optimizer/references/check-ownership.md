# Check Ownership — search-optimizer

Every canonical check ID has exactly one owner per run. Non-owners that support `skip-checks`
receive it and list it as `skipped — owned by <owner>` (see the per-member table); other
overlaps are merged at merge time. The map is written to `evidence/manifest.json` →
`owners` and is **final before seo-ai-optimizer runs**.

## The orchestrated-run block

```text
/seo-ai-optimizer /abs/path/to/repo
orchestrated-by: search-optimizer
evidence-dir: /abs/output/evidence
skip-checks: agent-readiness-scan
output-dir: /abs/output/reports/seo-ai-optimizer
```

URL only, no codebase: omit the repo path (`/seo-ai-optimizer` alone on the first line). With
`evidence-dir` set, seo-ai-optimizer runs live-evidence-only, so it audits the evidence dir and
lists fixes as "needs source repo".

Search data the user gave at intake (`manifest.json` → `search_data`) goes after the block as
plain request lines, one per input, e.g. `Search Console data: /abs/path/to/export` and
`AI-citation log: /abs/path/to/log.md`. They are request text that seo-ai-optimizer's Step 2
reads, not block keys. With no line, it reports both checks `not covered` itself.

Members never skip their own gates because of this block. Never pass `skip-checks` to
website-agent-readiness (its scan is atomic) or to dont-make-me-think. `aso-marketing` is not a
contract member: invoke it normally, without the block.

## Scan cases (web branch)

Decide after website-agent-readiness returns, from evidence — not from consent alone:

| Case | Condition |
|---|---|
| **A** | G1 approved **and** `evidence/agent-readiness/scan.json` exists for the same URL |
| **B** | G1 declined, member not installed, or no public URL |
| **C** | G1 approved but the scan failed (localhost, private, password-walled, timeout) |

## Matrix (web)

| Check ID | Case A owner | Case B / C owner |
|---|---|---|
| `meta-tags`, `robots-sitemap`, `structured-data`, `llms-txt` | seo-ai-optimizer | seo-ai-optimizer |
| `crawler-access` | seo-ai-optimizer (GPTBot/ClaudeBot directives) | seo-ai-optimizer |
| `markdown-pages` | website-agent-readiness | not covered (reason) |
| `ai-actions` | not covered — no web-branch member evaluates it; run `/ux-ax-review` or `/design-optimizer` for it | not covered (same pointer) |
| `agent-readiness-scan` | website-agent-readiness | not covered (reason) |
| `virality` | viral-product-evaluator | viral-product-evaluator |
| `search-performance` | seo-ai-optimizer when a Search Console export, API rows or the Generative AI performance report was supplied; else not covered: no Search Console export supplied | same |
| `ai-citations` | seo-ai-optimizer when a by-hand AI-citation log was supplied; else not covered: no AI-citation log supplied | same |

`search-performance` and `ai-citations` follow the data in `manifest.json` → `search_data`,
never the scan case, and each is decided on its own: an export alone leaves `ai-citations` not
covered.

Fix routes (website-agent-readiness never fixes):

- seo-owned checks, `crawler-access` included → seo-ai-optimizer's Step 5 plan and Step 6 diff
  approval in this run. The scan's crawler-access results are cited on seo's row, never re-fixed.
- `search-performance`, `ai-citations` → recommendations the user writes, listed under
  *Recommendations for You to Write* in seo-ai-optimizer's Step 5 plan; never a Step 6 diff.
- `markdown-pages` → website-agent-readiness's `agent-ready-plan.md` (G3) or issues (G4); no
  member applies it automatically.
- `ai-actions` → none in this run. Neither seo-ai-optimizer nor the isitagentready.com scan
  evaluates copy/share/open-in-AI actions, so it is listed under "Not covered" in every case with
  the pointer: run `/ux-ax-review` or `/design-optimizer` for it.

## Skip-checks per member

| Member | Case A | Case B / C |
|---|---|---|
| seo-ai-optimizer | — (it audits neither `markdown-pages` nor `ai-actions`; keeps `crawler-access`) | `agent-readiness-scan` (asks Step 8 not to repeat the scan) |
| viral-product-evaluator | `meta-tags` | `meta-tags` |
| website-agent-readiness | — (takes no skip-checks; full scan once) | not run / failed |

Never put `search-performance` or `ai-citations` in `skip-checks`: without data seo-ai-optimizer
reports them `not covered`, and a skip would read `skipped — owned by …` instead.

In case A, seo-ai-optimizer Step 8 records the existing `scan.json` as `REUSED` and does not
invoke website-agent-readiness again. Member report files: seo-ai-optimizer →
`seo-audit-report.md`; viral-product-evaluator → `viral-evaluation.md` (a skip only drops that
fix from Top Fixes; all 32 principles stay scored).

## Store branch

aso-marketing owns the whole store listing (title, subtitle, keywords, description, screenshots
copy, localization). Report these rows with check label `store-listing`; it is a report label,
not a skip-check ID. aso-marketing takes no `output-dir`: the orchestrator saves its Phase 7 Summary
Report and Final Report into `reports/aso-marketing/summary.md`. viral-product-evaluator owns `virality` for the app. No web member runs on
store metadata.

## Owners map example (case B)

```json
{
  "owners": {
    "meta-tags": "seo-ai-optimizer", "robots-sitemap": "seo-ai-optimizer",
    "structured-data": "seo-ai-optimizer", "llms-txt": "seo-ai-optimizer",
    "crawler-access": "seo-ai-optimizer",
    "markdown-pages": "not-covered: user declined third-party scan",
    "ai-actions": "not-covered: no web-branch member evaluates it; run /ux-ax-review or /design-optimizer",
    "agent-readiness-scan": "not-covered: user declined third-party scan",
    "virality": "viral-product-evaluator",
    "search-performance": "not-covered: no Search Console export supplied",
    "ai-citations": "not-covered: no AI-citation log supplied"
  }
}
```

## Merge rule

The scan cannot skip checks, so it also reports robots/sitemap, crawler directives and, when the
scanner runs it, llms.txt. Merge those results into seo-ai-optimizer's row for the same check and cite the scan as corroboration — one
row, never two.
