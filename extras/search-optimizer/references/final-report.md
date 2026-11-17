# Final Response — search-optimizer

The closing chat response of every search-optimizer run, early stops included. It comes after
the lease release (SKILL.md → *Dependency Preflight*, step 6) and sits beside
`search-optimization.md`; it never replaces the merged report and never repeats its rows.

## Format

A compact text block, one line per item, in this order: `Result`, `Evidence`, `Uncertainty`,
`Decision`. If the user asks for a different format, keep the four items and present them in
that format.

## Status

Apply the first row that matches:

| Status | When |
|---|---|
| `BLOCKED` | No merged report was written: a required member was missing at preflight, the user did not answer the branch question, Repo Sync stopped before any member ran, or intake failed. |
| `PARTIAL` | The merged report is written, but a member ended `PARTIAL`, `BLOCKED` or errored, or the user ended the run at a member's approval gate (seo-ai-optimizer Step 5 or Step 6, aso-marketing's plan gate). |
| `PASS` | The merged report is written and every member that ran ended `COMPLETE` (seo-ai-optimizer, aso-marketing) or `PASS` (website-agent-readiness, viral-product-evaluator). |

An optional member skipped at preflight is a declared scope reduction: list it under
"Not covered" and on the `Uncertainty:` line. It does not by itself make the run `PARTIAL`.

## Fill rules

- `Result:` — the status first, then the target and branch (web, store or both) and the merged
  report's finding counts, or `No merged report` with the reason.
- `Evidence:` — the manifest path, the scan case (A, B or C), each member report path with that
  member's own `Result:` line, and the merged report path. Cite only checks that ran.
- `Uncertainty:` — skipped members and their uncovered checks, `ai-actions` (never covered
  here), a scan that predates seo-ai-optimizer fixes, member caveats, and any failed lease
  release. Label assumptions as assumptions.
- `Decision:` — each pending member approval, relayed verbatim with its owner, or
  `No approval needed.` followed by any remaining user action (deploy, then re-scan as a new G1).

## PARTIAL example

```text
Result: PARTIAL. https://app.example.com + ./ios (both): search-optimization.md written, 2 P0 · 4 P1 · 5 P2 · 1 P3.
Evidence: evidence/manifest.json (case A); seo-ai-optimizer COMPLETE (reports/seo-ai-optimizer/seo-audit-report.md); website-agent-readiness PASS 3/5; viral-product-evaluator PASS; aso-marketing PARTIAL (reports/aso-marketing/summary.md).
Uncertainty: ai-actions not covered (run /ux-ax-review); the scan predates any seo-ai-optimizer fixes; store ranking impact is untested.
Decision: Approve aso-marketing's plan items 1-6 to let Phase 4 write the store metadata.
```

## BLOCKED example

```text
Result: BLOCKED. ./ios (store): No merged report — aso-marketing is not installed.
Evidence: Dependency Preflight, so_mode=installed; no SKILL.md under ~/.claude/skills/aso-marketing or ~/.agents/skills/aso-marketing; nothing was fetched or written.
Uncertainty: Listing quality is unknown; no member ran.
Decision: No approval needed. Install aso-marketing (asm install github:luongnv89/skills:skills/aso-marketing -p claude --yes), then rerun.
```

## Reader checks

| Check | Pass when |
|---|---|
| Result is findable | The first line states the status, target and branch without reading the member reports. |
| Facts and assumptions are separated | Verified claims name a member `Result:` line or a report path; untested checks and assumptions are on the `Uncertainty:` line. |
| Claims are traceable | Each member outcome cites its report path; `PASS` appears only when every member that ran ended `COMPLETE` or `PASS`. |
| Next decision is clear | The `Decision:` line relays each pending approval or says `No approval needed.` and names any remaining user action. |

A heading's presence alone does not pass a check. Without a human reviewer's answer, human
understanding is unconfirmed; agent inspection cannot confirm it. Negative-trigger evals are
excluded from these checks.
