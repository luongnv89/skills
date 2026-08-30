# Step Completion Reports

After completing each major step, output a status report in this format:

```
◆ [Step Name] ([step N of M] — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          √ pass (note if relevant)
  [Check 3]:          × fail — [reason]
  [Check 4]:          √ pass
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Adapt the check names to match what the step actually validates. Use `√` for pass, `×` for fail, and `—` to add brief context. The "Criteria" line summarizes how many acceptance criteria were met. The "Result" line gives the overall verdict.

## Phase-specific checks

**Step 1 — Detection**
```
◆ Detection (step 1 of 8 — project scan)
··································································
  Framework identified:     √ pass (Next.js | Nuxt | Astro | ...)
  File structure mapped:    √ pass (N HTML/template files found)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Step 2 — Audit**
```
◆ Audit (step 2 of 8 — SEO analysis)
··································································
  Meta tags checked:        √ pass (N files scanned)
  Structured data validated: √ pass (JSON-LD present/valid)
  AI bot access verified:   √ pass (robots.txt + llms.txt checked)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Step 3 — Research**
```
◆ Research (step 3 of 8 — best practices lookup)
··································································
  Web searches completed:   √ pass (N queries executed)
  Latest practices fetched: √ pass (current year updates noted)
  Gaps identified:          √ pass | × fail — [missing coverage areas]
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Step 4 — Report**
```
◆ Report (step 4 of 8 — findings presentation)
··································································
  Issues categorized:       √ pass (critical/warning/info grouped)
  Project-level findings:   √ pass (robots.txt, sitemap, llms.txt, JSON-LD)
  Report presented:         √ pass
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Step 5 — Plan**
```
◆ Plan (step 5 of 8 — improvement planning)
··································································
  Priorities ranked:        √ pass (critical → warnings → enhancements)
  New files identified:     √ pass (N files to create)
  User approval received:   √ pass | × fail — [awaiting approval]
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Step 6 — Implementation**
```
◆ Implementation (step 6 of 8 — applying fixes)
··································································
  Fixes applied:            √ pass (N issues resolved)
  Sitemaps updated:         √ pass
  Schema.org added:         √ pass (Organization + Article JSON-LD)
  Safety protocol followed: √ pass (diffs shown + confirmed)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Step 7 — Validation**
```
◆ Validation (step 7 of 8 — post-fix verification)
··································································
  SEO score improved:       √ pass (critical issues: N → 0)
  No regressions:           √ pass
  AI crawl accessible:      √ pass (llms.txt + GPTBot/ClaudeBot allowed)
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

**Step 8 — Agent-readiness handoff**
```
◆ Agent-readiness handoff (step 8 of 8 — live-site scan)
··································································
  Preflight (website-agent-readiness):  √ pass
  Live URL supplied and approved:       √ pass ({url})
  Scan completed:                       √ pass (score N/5)
  agent-ready-plan.md written:          √ pass
  ____________________________
  Result:             PASS | SKIPPED | FAIL
```
A `SKIPPED` result is a valid outcome — name the unmet condition (no live URL, no
approval, or the preflight miss) on the line that reports it.
