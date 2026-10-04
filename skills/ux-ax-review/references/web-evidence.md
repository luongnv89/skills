# Web and repository evidence

## Live-web

Use existing retrieval tools for response status/headers/body and a browser for DOM and
safe navigation. Record redirect chains and which tool saw which response. If a graphical
browser is unavailable (e.g. Lightpanda/DOM-only), request screenshots for visual checks or
mark brand/reflow/contrast subchecks not-tested. Saved screenshots are still a partial
sample. Never equate DOM extraction with rendered/interactive verification.

Bound collection to the scoped surfaces plus robots.txt, referenced sitemap, llms.txt and
supplied/documented public machine-readable routes. Prefer fetching known routes; inspect
one representative sitemap subset rather than crawling the whole site. Do not run load
scans, recursively enumerate private routes, fabricate status codes, spoof bots or bypass
access controls. On 403/CAPTCHA, stop that path and request authorized saved artifacts.

For performance, use supplied metrics or an already available authorized profiler; record
lab/field, date/window, URL, environment and tool version when known. Missing tooling is
an evidence gap, not permission to install or report Lighthouse-like invented scores.

## Repo (source-only)

Read routes, components, content, metadata, robots/sitemap generators, schema markup,
styles, export/share code and existing tests; cite file:line. Never execute untrusted repo
scripts or a dev server without explicit permission. Source-level risks can be observed
in code, but live crawl status, rendered behavior and performance remain unverified.

Before collection, snapshot target state including tracked and untracked files. Existing
repo checkers may be used when available; otherwise hash the inspected files and enumerate
changes within the declared scope. Do not claim a whole-repo no-change check if only a
sample was hashed. Artifacts outside the target avoid mutating the audited checkout.
