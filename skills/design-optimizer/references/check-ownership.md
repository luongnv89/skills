# Check Ownership — design-optimizer

Every canonical check ID has exactly one owner per run. Non-owners that support `skip-checks`
receive it and list it as `skipped — owned by <owner>` (see the per-member table); other
overlaps are merged at merge time. The owner map is written to
`evidence/manifest.json` → `owners` and is **final before ux-ax-review runs**.

## The orchestrated-run block

Pass these as plain `key: value` lines after the member invocation:

```text
/ux-ax-review https://example.com
orchestrated-by: design-optimizer
evidence-dir: /abs/output/evidence
skip-checks: clarity,robots-sitemap,markdown-pages,crawler-access
output-dir: /abs/output/reports/ux-ax-review
```

Members never skip their own safety gates because of this block.

## AX ownership cases

Decide after website-agent-readiness returns, from evidence — not from consent alone:

| Case | Condition | Scan-covered AX checks owner |
|---|---|---|
| **A** | G1 approved **and** `evidence/agent-readiness/scan.json` exists for the same URL | `website-agent-readiness` |
| **B** | G1 declined, or member not installed, or target is not a public URL | `ux-ax-review` |
| **C** | G1 approved but the scan failed (unreachable, private, password-walled) | `ux-ax-review`; report the scan failure |

AX checks: `robots-sitemap,structured-data,markdown-pages,llms-txt,crawler-access,ai-actions`.
Only three of them are evaluated by the isitagentready.com scan (inventory in
website-agent-readiness `references/scan-api.md`), so only these can move to it in case A:

| Scan category / check | AX check |
|---|---|
| `discoverability`: `robotsTxt`, `sitemap` | `robots-sitemap` |
| `contentAccessibility`: `markdownNegotiation` | `markdown-pages` |
| `botAccessControl`: `robotsTxtAiRules`, `contentSignals` | `crawler-access` |

`structured-data` (JSON-LD) and `ai-actions` are not scanned, and llms.txt is scanned only
conditionally, so `structured-data`, `llms-txt` and `ai-actions` stay with ux-ax-review in every
case; any scan result for them is cited as corroboration on ux-ax-review's row.

## Matrix

| Check ID | Case A owner | Case B / C owner |
|---|---|---|
| `clarity` | dont-make-me-think | dont-make-me-think |
| `brand`, `responsive`, `accessibility`, `performance`, `conversion` | ux-ax-review | ux-ax-review |
| `robots-sitemap`, `markdown-pages`, `crawler-access` | website-agent-readiness | ux-ax-review |
| `structured-data`, `llms-txt`, `ai-actions` | ux-ax-review | ux-ax-review |
| `agent-readiness-scan` | website-agent-readiness | not covered (reason) |
| `virality` | viral-product-evaluator | viral-product-evaluator |
| `meta-tags` | viral-product-evaluator | viral-product-evaluator |

If viral-product-evaluator is missing, `virality` and `meta-tags` are **not covered**; never
reassign them to a member that does not audit them.

## Skip-checks per member

| Member | Case A | Case B / C |
|---|---|---|
| ux-ax-review | `clarity,robots-sitemap,markdown-pages,crawler-access` | `clarity` |
| dont-make-me-think | — (owns `clarity`, no skips) | — |
| viral-product-evaluator | — | — |
| website-agent-readiness | — (takes no skip-checks; runs its full scan once) | not run / scan failed |

## Owners map example (case A)

```json
{
  "owners": {
    "clarity": "dont-make-me-think",
    "brand": "ux-ax-review", "responsive": "ux-ax-review", "accessibility": "ux-ax-review",
    "performance": "ux-ax-review", "conversion": "ux-ax-review",
    "robots-sitemap": "website-agent-readiness", "markdown-pages": "website-agent-readiness",
    "crawler-access": "website-agent-readiness",
    "structured-data": "ux-ax-review", "llms-txt": "ux-ax-review", "ai-actions": "ux-ax-review",
    "agent-readiness-scan": "website-agent-readiness",
    "virality": "viral-product-evaluator", "meta-tags": "viral-product-evaluator"
  }
}
```

An uncovered check is written as `"not-covered: <reason>"` so a member's skip line still resolves.

## Merge rule

When two members report the same defect (e.g. dont-make-me-think's `clarity` and
ux-ax-review's `conversion` both flag a vague primary CTA, or the scan and ux-ax-review both flag
a missing llms.txt), keep **one** row under the check's owner and cite the other member as
corroboration. dont-make-me-think and viral-product-evaluator take no skip-checks here, so their
overlaps are removed at this merge step, not before the audit. Findings outside a member's owned checks are kept only if no owner covers them.
