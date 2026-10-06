# Check Ownership — design-optimizer

Every canonical check ID has exactly one owner per run. Non-owners receive it in `skip-checks`
and list it as `skipped — owned by <owner>`. The owner map is written to
`evidence/manifest.json` → `owners` and is **final before ux-ax-review runs**.

## The orchestrated-run block

Pass these as plain `key: value` lines after the member invocation:

```text
/ux-ax-review https://example.com
orchestrated-by: design-optimizer
evidence-dir: /abs/output/evidence
skip-checks: clarity,robots-sitemap,structured-data,markdown-pages,llms-txt,crawler-access,ai-actions
output-dir: /abs/output/reports/ux-ax-review
```

Members never skip their own safety gates because of this block.

## AX ownership cases

Decide after website-agent-readiness returns, from evidence — not from consent alone:

| Case | Condition | AX checks owner |
|---|---|---|
| **A** | G1 approved **and** `evidence/agent-readiness/scan.json` exists for the same URL | `website-agent-readiness` |
| **B** | G1 declined, or member not installed, or target is not a public URL | `ux-ax-review` |
| **C** | G1 approved but the scan failed (unreachable, private, password-walled) | `ux-ax-review`; report the scan failure |

AX checks: `robots-sitemap,structured-data,markdown-pages,llms-txt,crawler-access,ai-actions`.

## Matrix

| Check ID | Case A owner | Case B / C owner |
|---|---|---|
| `clarity` | dont-make-me-think | dont-make-me-think |
| `brand`, `responsive`, `accessibility`, `performance`, `conversion` | ux-ax-review | ux-ax-review |
| `robots-sitemap`, `structured-data`, `markdown-pages`, `llms-txt`, `crawler-access`, `ai-actions` | website-agent-readiness | ux-ax-review |
| `agent-readiness-scan` | website-agent-readiness | not covered (reason) |
| `virality` | viral-product-evaluator | viral-product-evaluator |
| `meta-tags` | viral-product-evaluator | viral-product-evaluator |

If viral-product-evaluator is missing, `virality` and `meta-tags` are **not covered**; never
reassign them to a member that does not audit them.

## Skip-checks per member

| Member | Case A | Case B / C |
|---|---|---|
| ux-ax-review | `clarity,robots-sitemap,structured-data,markdown-pages,llms-txt,crawler-access,ai-actions` | `clarity` |
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
    "robots-sitemap": "website-agent-readiness", "structured-data": "website-agent-readiness",
    "markdown-pages": "website-agent-readiness", "llms-txt": "website-agent-readiness",
    "crawler-access": "website-agent-readiness", "ai-actions": "website-agent-readiness",
    "agent-readiness-scan": "website-agent-readiness",
    "virality": "viral-product-evaluator", "meta-tags": "viral-product-evaluator"
  }
}
```

An uncovered check is written as `"not-covered: <reason>"` so a member's skip line still resolves.

## Merge rule

When two members report the same defect (e.g. the scan and viral-product-evaluator both flag a
missing `og:image`), keep **one** row under the check's owner and cite the other member as
corroboration. Findings outside a member's owned checks are kept only if no owner covers them.
