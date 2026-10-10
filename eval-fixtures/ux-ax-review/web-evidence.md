# Synthetic web evidence — not a real-site scan

Target: https://audit-fixture.invalid (documentation-only, never fetch). Audience: solo developers evaluating a paid tool. Goal: understand the offering and choose a plan. Two surfaces: entry and pricing within supplied saved HTML. Read synthetic-demo.html.

Provided response capture for robots.txt: HTTP 200, text/plain:
User-agent: GPTBot
Disallow: /
User-agent: OAI-SearchBot
Allow: /
Sitemap: https://audit-fixture.invalid/sitemap.xml
Owner policy: public search discovery is desired; training access is deliberately denied. Preserve this decision.
Provided sitemap capture: HTTP 200, XML with home and pricing canonical public URLs. Validity beyond these supplied captures was not tested.
Provided llms.txt capture: HTTP 404. No Markdown export was inspected; absence is unknown.
Provided lab report for entry: LCP 4.2 seconds, CLS 0.06, mobile emulation; no field data, no INP measurement, no exact tool/version/date available. These numbers are synthetic provided data, not measurements by the auditor.
No rendered screenshots, no keyboard/screen-reader test, no visual viewport test, no analytics, no crawler logs. Browser HTTP for the home page was 200 in the provided capture, which does not prove real crawler access.
There are no copy/share/open-in-AI actions in the supplied HTML excerpt; full product coverage is unknown. Missing optional actions are not a critical defect.
