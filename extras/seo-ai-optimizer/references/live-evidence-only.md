# Live-Evidence-Only Orchestrated Run

An orchestrator (`search-optimizer`) sends this path for a URL-only target. Nothing here applies
outside an orchestrated run.

## When it applies

All of these hold:

- The orchestrated-run block has `evidence-dir`.
- The first line names no project root.

A project root that is given but is not a git work tree still stops the run as Prerequisites
say, and so does a missing repo when `evidence-dir` is absent.

## Steps

| Step | Live-evidence-only behavior |
|---|---|
| Repo Sync | Skipped: there is no repo, and nothing is written. |
| 1 Detect | Run `python scripts/audit_seo.py <evidence-dir>`. The script audits `page.html` and the root `robots.txt`, `sitemap.xml` and `llms.txt` that intake captured. Report the framework as "generic HTML (live evidence)". |
| 2 Audit | Read `manifest.json` before the script output. A file recorded as `blocked` or unavailable is "not tested", never "missing". Drop every script finding for that file: its body may be an error page. Review `head.json` by hand only when `page.html` is absent. `skip-checks` still applies. |
| 3 Research | Unchanged. |
| 4 Report | Head the report `live evidence only — no source repo`, and write it to `<output-dir>/seo-audit-report.md`. |
| 5 Plan | List every fix with status `needs source repo` and the file it would change (`robots.txt`, `llms.txt`, head tags, JSON-LD). Ask for no approval, since nothing will be applied. |
| 6-7 Implement, Validate | Skipped. Never edit the evidence copies. |
| 8 Agent-readiness | Unchanged: reuse `scan.json`, or skip via `skip-checks`. |

In the subagent workflow, the auditor and researcher write their artifacts to `output-dir`, never
to `evidence-dir`. The implementer and validator are not spawned.

## Done when

- The report names the live-evidence-only path and cites evidence files, not source paths.
- Every fix is listed as `needs source repo`, and no file was written outside `output-dir`.
- Every blocked file is reported as "not tested".
- The approval, Diff & Confirm, validation and file-presence acceptance items are marked
  `n/a — needs source repo`.
