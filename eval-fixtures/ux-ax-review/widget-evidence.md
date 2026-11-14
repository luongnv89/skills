# Synthetic evidence: hand-rolled widgets — not a real-site scan

Target: https://widgets-fixture.invalid (documentation-only, never fetch). Audience: account owners managing team members. Goal: change a member's role. One surface: the Team settings page in widget-page.html (saved HTML excerpt).

Stack, from the supplied `package.json` excerpt: React 18.3, Vite 5. No component or headless UI library is installed (no Radix, React Aria, Headless UI, Ark UI or `@ui-sdk/*`).

Supplied manual keyboard notes (written by the site owner on 2026-11-10, Chrome 131, macOS; synthetic provided data, not observations by the auditor):
- "Role" dropdown: the trigger is a `div` with `onClick`; it can't be reached with Tab. Opened by mouse, the list ignores ArrowUp/ArrowDown and Escape, and clicking outside does not close it.
- "Remove member" dialog: Tab moves focus to the page behind the dialog; Escape does nothing; on close, focus goes to the top of the page instead of the button that opened it.
- No screen-reader test was run. No automated scan was run.

No rendered screenshots, no viewport test, no performance data, no analytics. robots.txt, sitemap, structured data, Markdown pages, llms.txt and crawler access were not supplied: they are unknown. The page has no copy/share/open-in-AI actions.
