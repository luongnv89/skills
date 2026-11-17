# HTML Report Guide

How to build the optional `CLEAN_CODE_AUDIT.html`. There is no template file: write one self-contained HTML file from this spec. Use inline `<style>` and one inline `<script>`, with no CDNs, web fonts or chart library, so it works offline. It is a sibling of `CLEAN_CODE_AUDIT.md`, not a replacement: same data in visual form, with the same counts and findings.

## Look

A refined dark-IDE aesthetic. Define these tokens on `:root`:

| Token | Value | Use |
| --- | --- | --- |
| `--bg` / `--panel` / `--panel-2` | `#0d1117` / `#161b22` / `#1c232c` | page, cards, nested cards |
| `--line` | `#283039` | borders and rules |
| `--ink` / `--ink-soft` / `--ink-faint` | `#e6edf3` / `#aab2bd` / `#6e7681` | text levels |
| `--green` | `#3fb950` | accent highlight only |
| `--crit` / `--major` / `--minor` / `--info` | `#f85149` / `#f0883e` / `#d29922` / `#58a6ff` | severity |
| `--mono` | `ui-monospace, "SFMono-Regular", Menlo, monospace` | file paths, code, numbers |
| `--sans` | `"Segoe UI", -apple-system, "Helvetica Neue", Arial, sans-serif` | body |

Severity and accent colors go on text, borders, dots and bars only, never as a fill behind text. Max content width is about 1180px. Grids collapse to one column below 720px, with no horizontal overflow at 375px.

## Structure, in order

1. **Window chrome bar**: three dots, the crumb `<b>PROJECT</b> / CLEAN_CODE_AUDIT.html`, and the tag `bbv Clean Code V2.2`.
2. **Hero**: the eyebrow `Clean Code Audit · Static Analysis Report` and the title `Clean Code Audit`. Under them, a definition grid with Project, Date (`YYYY-MM-DD`), Scope (e.g. `Full audit — 70 Swift files`), Files audited (e.g. `70 (63 source + 7 test)`) and Standard (`bbv Clean Code Cheat Sheet V2.2`). Then a headline callout of one or two sentences naming the dominant themes; `<strong>` is allowed.
3. **Table of contents**: anchor links to the four numbered sections below.
4. **01 Metrics**: five tiles: Critical, Major, Minor, Info, and Consolidated (the total, with the subline `from N raw findings`).
5. **02 Distribution**:
   - A donut built from a CSS `conic-gradient` over the four severity percentages. These are integers that sum to 100; for 6/19/12/3 of 40 they are 15, 48, 30 and 7. Put the total in the center and a legend with counts beside it.
   - Effort bars for Phase 1, 2 and 3. Sum each phase's task efforts, treating `~15m≈0.03d`, `~1h≈0.12d`, `~3h≈0.4d` and `~1d=1d`. Label each bar with the rounded sum, e.g. `~18d`. The largest phase is 100% width and the others are scaled to it.
6. **03 Findings**:
   - A filter bar of buttons `All`, `Critical`, `Major`, `Minor`, `Info` (using `aria-pressed`) and `Reset`, plus a live `Showing N of M findings` count (`aria-live="polite"`).
   - One `<details open>` group per severity that has findings, in the order Critical, Major, Minor, Info. Each group shows a dot, its label and its count.
   - Each finding is an `<article class="finding" data-sev="crit|major|minor|info">` containing:
     - a severity badge and a title
     - its `file:line`, linked to `…/blob/<sha>/path#Lline` when the repo has a web remote, plain text otherwise
     - the principle
     - a one-sentence description
     - a `Fix →` line
     - a short snippet in `<pre>` with `<`, `>` and `&` escaped. Without one, write `Snippet: unavailable` so missing evidence isn't mistaken for a clean site.
     - for a consolidated finding, a `Sites:` list of its other `file:line` sites
   - A Minor or Info themed group from the `.md` becomes one finding, titled with the theme, with its sites listed.
7. **04 Implementation Plan**: one block per phase, with a left border in the phase color. Its header shows the phase title (e.g. `Phase 1 — Critical (do first)`), the effort sum, and a live `k/N done` counter. Each task has:
   - a checkbox
   - a stable ID (`1.1`, `2.3`, …)
   - an imperative title
   - the target `file:line`
   - the principle it fixes
   - the effort
   - its dependencies (task IDs or `none`)
   - its acceptance check
8. **Notes**: one line each on the consolidation ratio, how the headline claims were verified, dependency-chain ordering, language scope and exclusions, and that no source was modified.

## Behavior (the inline script)

- Filter: show only the selected severity's findings and hide groups left empty. Update `Showing N of M`, where M is the number of `article.finding` elements. `All` and `Reset` restore every finding.
- Checkboxes: save checkbox state in `localStorage` under `cleanaudit:<project>`, keyed by task ID. Wrap every `localStorage` call in try/catch so the page still works when storage is blocked. Recompute each phase's `k/N done` counter on every change.

## Self-check before delivering

- The severity counts match across the tiles, the donut legend and the `## Summary` table in the `.md`.
- The donut renders and the bars have the right relative widths.
- Each filter button shows only its severity, and `Reset` and `All` restore everything.
- Checkboxes toggle, the counters update, and the state survives a reload.
- Every `file:line` link opens the cited line. If a link can't be opened (no network, private remote), report it as untested.
- The page has no horizontal overflow at 375px.
