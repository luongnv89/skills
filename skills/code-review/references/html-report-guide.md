# HTML Report Guide

How to turn `references/report-template.html` into a delivered `CLEAN_CODE_AUDIT.html`. The template is a single self-contained file (no CDNs, no chart library, offline-safe) using a refined dark-IDE aesthetic. You fill placeholders — there is no build step.

## Procedure

1. Copy `references/report-template.html` to the repo root as `CLEAN_CODE_AUDIT.html`.
2. **Delete the leading `<!-- Clean Code Audit — HTML report template … -->` instruction comment** (it contains literal `{{…}}` tokens that are documentation, not data).
3. Replace every `{{PLACEHOLDER}}` with real audit data (table below).
4. For each `<!-- REPEAT:name --> … <!-- /REPEAT:name -->` block: duplicate the inner markup once per item, fill it, then **delete the `REPEAT` comment markers** in the final file.
5. Delete any optional element that doesn't apply (snippet `<pre>`, multi-site `<p class="sites">`).
6. **Verify zero `{{` tokens remain** (`grep -c '{{' CLEAN_CODE_AUDIT.html` must return 0) and that the severity tile counts equal the donut legend counts equal the `## Summary` table in the `.md` report.

The HTML is a sibling of `CLEAN_CODE_AUDIT.md`, not a replacement — same data, visual form. Keep them consistent (same counts, same findings).

## Scalar placeholders

| Placeholder | Fill with |
| --- | --- |
| `{{PROJECT_NAME}}` | Repo/app name, e.g. `ask-milo`. Used in title, chrome, and the localStorage key — keep it stable. |
| `{{DATE}}` | Audit date `YYYY-MM-DD`. |
| `{{SCOPE}}` | Short scope string, e.g. `Full audit — 70 Swift files`. |
| `{{FILES_AUDITED}}` | e.g. `70 (63 source + 7 test)`. |
| `{{SOURCE_STANDARD}}` | `bbv Clean Code Cheat Sheet V2.2`. |
| `{{HEADLINE_HTML}}` | The headline sentence(s). May contain `<strong>`. One or two sentences naming the dominant theme(s). |
| `{{CRITICAL_COUNT}}` `{{MAJOR_COUNT}}` `{{MINOR_COUNT}}` `{{INFO_COUNT}}` | Consolidated counts per severity. |
| `{{TOTAL_COUNT}}` | Sum of the four (consolidated, not raw). |
| `{{RAW_COUNT}}` | Raw findings before consolidation (e.g. `124`). |

## Distribution

- `{{PCT_CRITICAL}}` `{{PCT_MAJOR}}` `{{PCT_MINOR}}` `{{PCT_INFO}}` — each severity as a **percentage of total**, integers that sum to ~100. Example for 6/19/12/3 of 40: `15`, `48`, `30`, `7`. The donut is a CSS conic-gradient driven by these.
- Effort bars per phase:
  - `{{P1_EFFORT}}` `{{P2_EFFORT}}` `{{P3_EFFORT}}` — human-readable effort sum, e.g. `~18d`. Sum each phase's task efforts (treat `~15m≈0.03d`, `~1h≈0.12d`, `~3h≈0.4d`, `~1d=1d`; round sensibly).
  - `{{P1_BARPCT}}` `{{P2_BARPCT}}` `{{P3_BARPCT}}` — bar width as a percentage of the **largest** phase effort (the biggest phase = `100`).

## Findings (`REPEAT:sevgroup` → `REPEAT:finding`)

One `sevgroup` per severity that has findings (order: Critical, Major, Minor, Info). Per group:

| Placeholder | Fill |
| --- | --- |
| `{{SEV_CLASS}}` | `crit` \| `major` \| `minor` \| `info` (drives color). |
| `{{SEV_LABEL}}` | `Critical` \| `Major` \| `Minor` \| `Info`. |
| `{{SEV_COUNT}}` | Number of findings in this group. |

Per `finding` inside the group:

| Placeholder | Fill |
| --- | --- |
| `{{SEV_CLASS}}` / `{{SEV_LABEL}}` | Same as the group (used by the badge). |
| `{{FINDING_TITLE}}` | Short title, e.g. `UserService does too much`. |
| `{{FILE_LINE}}` | `path/to/file.ext:line`. For consolidated findings, the primary site. |
| `{{PRINCIPLE}}` | Named principle/smell, e.g. `Single Responsibility Principle`. |
| `{{DESCRIPTION}}` | One-sentence violation description. |
| `{{FIX_DIRECTION}}` | One-sentence fix (the `Fix →` line). |
| `{{CODE_SNIPPET}}` | Optional. A short before/after or offending snippet. **Delete the whole `<pre class="snippet">…</pre>` if none.** Escape `<`,`>`,`&` as `&lt;`,`&gt;`,`&amp;`. |
| `{{SITE_LIST}}` | Optional. Comma-separated extra `file:line` sites for a consolidated finding. **Delete the whole `<p class="sites">…</p>` for single-site findings.** |

For Minor/Info themed groups (where the `.md` uses bullet groups), make each themed group one `finding` with the theme as the title and the sites in `{{SITE_LIST}}`.

## Implementation Plan (`REPEAT:phase` → `REPEAT:task`)

One `.phase` per phase. Per phase:

| Placeholder | Fill |
| --- | --- |
| `{{PHASE_CLASS}}` | `p1` \| `p2` \| `p3` (color of the left border + bar). |
| `{{PHASE_NUM}}` | `1` \| `2` \| `3` (groups the progress counter — must match the tasks' `data-phase`). |
| `{{PHASE_TITLE}}` | e.g. `Phase 1 — Critical (do first)`. |
| `{{PHASE_TASK_COUNT}}` | Number of tasks in the phase (the `0/N done` denominator; JS recomputes live). |
| `{{PHASE_EFFORT}}` | Phase effort sum, e.g. `~18d`. |

Per `task`:

| Placeholder | Fill |
| --- | --- |
| `{{TASK_ID}}` | Stable id `1.1`, `2.3`… Used as the localStorage key and the `data-task` attribute — keep unique. |
| `{{PHASE_NUM}}` | The owning phase number (also on the `<input data-phase>`). |
| `{{TASK_TITLE}}` | Imperative task title. |
| `{{TASK_FILE}}` | Target `file:line` (or short multi-file note). |
| `{{TASK_PRINCIPLE}}` | Principle the task fixes. |
| `{{TASK_EFFORT}}` | e.g. `~3h`. |
| `{{TASK_DEPS}}` | Other task IDs that must precede it, or `none`. |
| `{{TASK_ACCEPTANCE}}` | The verifiable done-check. |

The checkbox state persists in `localStorage` under `cleanaudit:{{PROJECT_NAME}}`; the phase `… done` counters update live. No server needed.

## Notes (`REPEAT:note`)

One `.note` per methodology/caveat line. `{{NOTE_HTML}}` may contain inline `<code>`/`<strong>`. Cover: consolidation ratio, headline-claim verification, dependency-chain ordering, language scope/exclusions, and "no source modified".

## Self-check before delivering

- `grep -c '{{' CLEAN_CODE_AUDIT.html` → `0`.
- Open the file: donut renders, bars animate, severity counts match across tiles/legend/`.md`.
- Checkboxes toggle and the phase counter updates.
- Responsive: no horizontal overflow at 375px (the grids collapse via the media queries already in the template).
- All four severity colors appear only on text/borders — never as a fill behind text (per the design's status-color rule).
