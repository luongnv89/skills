# Apply — visual fixes through frontend-design

Load in Phase 5, only after the user opted in by finding ID. design-optimizer carries a brief and
a member's re-check; it never edits UI itself, never judges the result itself, and never restates
or relaxes `frontend-design`'s quality bar.

## The brief

The brief is input to `frontend-design`'s step 1 (its explicit brief) only. It never replaces
frontend-design's direction approval or its diff-and-confirm gate. Per finding, it carries:

- **Starting reference**: the evidence screenshots for the affected views, `desktop.png` /
  `mobile.png` and, when `files["screenshots-dark"]` is `ok`, `desktop-dark.png` /
  `mobile-dark.png`, plus the manifest's `build` line. With no screenshots (repo-only target,
  `/browse` missing), carry the finding's evidence citation (file:line) instead and record the gap.
- **The ban**, stated as a ban: "remove <element>; do not add <a substitute effect> in its place",
  with the finding ID and the member's reason quoted as data. A Cut-list item is briefed the same
  way.
- **Nothing else.** Never a style adjective from the request or from the opt-in ("apply D-03 and
  make it modern"): an explicit brief can lift frontend-design's ban rows, so a relayed adjective
  could bring back the defaults the finding removes. Record such words as untestable instead.

Example:

```text
Brief (from design-optimizer D-03, ux-ax-review F3): remove the "New" badge beside the hero CTA;
do not add another badge, glow or accent in its place. Reason: competes with the primary action.
Reference: evidence/screenshots/desktop.png, mobile.png, desktop-dark.png. Build: production.
```

## Re-check before "done"

A member runs the re-check, never design-optimizer:

1. **frontend-design's own visual check.** It passes only when its Final Report `Result:` is
   `COMPLETE` (no verification check failed; its `references/final-report.md`) and its
   `Evidence:` line lists the widths and modes it screenshotted for the affected views (dark
   included when dark shots were briefed). Its check inspects against the explicit brief, so the
   briefed ban is covered.
2. **Otherwise** (`Result: PARTIAL` with a check still failing, `Visual check untested: <reason>`
   on its `Uncertainty:` line, or the affected views or dark mode missing from `Evidence:`): re-run `ux-ax-review` on the changed surface with a fresh capture
   in its own directory (e.g. `<output>/recheck-<ID>/evidence/`, with `build` recorded, usually
   `dev`; never the pre-fix evidence-dir) and a separate
   `output-dir: <output>/reports/ux-ax-review-recheck-<ID>/`, so the audit's evidence and report
   are not overwritten. Scope it to the row's aspect with `skip-checks` listing the other eleven.
   For `brand`:
   `clarity,responsive,accessibility,performance,conversion,robots-sitemap,structured-data,markdown-pages,llms-txt,crawler-access,ai-actions`;
   for an `accessibility` or `responsive` row, swap that aspect out of the list and `brand` in.
   It passes only when both hold in the re-run's `ux-ax-findings.json`: the scoped aspect's
   `coverage` entry is tested (status `pass` or `issues`, never `not-tested`), and no finding
   names the banned element. Without a screenshot in the fresh capture, ux-ax-review leaves
   brand, responsive and contrast `not-tested`, so that re-run cannot pass the fix.
3. **Neither passed**: report the fix as `applied, not verified: <reason>`, never "done", naming
   what fell short (e.g. "frontend-design PARTIAL; re-run left brand not-tested: no screenshot").

Report each finding's re-check result in the Apply step report and the final `Decision:` line.
