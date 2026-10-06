---
name: dont-make-me-think
description: "Review UI usability using Steve Krug's principles and produce a scannable report. Use for UX audits of screenshots, URLs, or code. Don't use for brand critique, WCAG audits, or backend/API review."
license: MIT
effort: medium
dependencies:
  - browse
metadata:
  version: 1.6.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Don't Make Me Think — Usability Review & Redesign

Evaluate and improve UIs through Steve Krug's "Don't Make Me Think" principles. The report itself must practice what Krug preaches: scannable, visual, zero fluff. A human should skim it in 30 seconds; an AI agent should be able to parse it and start fixing.

## When to Use

Trigger this skill when the user asks for a usability audit, UX review, or UI feedback on a screenshot, live URL, or HTML/CSS code. Do not use for visual/brand critique, WCAG accessibility audits, or backend/API review — route those elsewhere.

## Dependency Preflight (mandatory)

This skill invokes `/browse` (frontmatter `dependencies`) only on the **live URL** path. Run this
once, before the first navigation:

```bash
if test -f "$HOME/.claude/skills/browse/SKILL.md"; then
  echo "browse_mode=installed browse_skill=$HOME/.claude/skills/browse/SKILL.md"
elif test -f "$HOME/.agents/skills/browse/SKILL.md"; then
  echo "browse_mode=installed browse_skill=$HOME/.agents/skills/browse/SKILL.md"
elif command -v asm >/dev/null && asm deps --help >/dev/null 2>&1; then
  asm deps discover dont-make-me-think --json || echo "discover failed; acquire still runs" >&2
  echo "browse_mode=lease"
else
  echo "Missing skill: browse. Install: asm install github:garrytan/gstack:browse -p claude -s global --yes" >&2
  echo "No asm yet: npm install -g agent-skill-manager@latest" >&2
  echo "browse_mode=none"
fi
printf 'dmmt_session=%s\n' "dont-make-me-think-$(date +%s)-$$"   # record it; reuse it verbatim
```

The install-path tests run first because gstack may install `/browse` without `asm` knowing.

1. `browse_mode=installed`: read the recorded `browse_skill` path.
2. `browse_mode=lease`: run `asm deps acquire browse --session <dmmt_session> --json`; read the
   returned `skillMdPath` directly.
3. `browse_mode=none`, or step 2 failed: take the *No reviewable input* row in Error Handling (fail-soft).
   Never review a URL you could not load.
4. **Release in `finally`.** If step 2 ran, run `asm deps release --session <dmmt_session> --json`
   once at every terminal outcome, stops included.

## Repo Sync Before Edits (mandatory)

Steps 1-4 below are read-only. **Redesign Mode (step 5) writes to UI source files**: before its
first edit, run the seven *Repo Sync steps* in `references/redesign-mode.md` (scoped with
`git -C "$repo"`, stash-first, skips recorded). On a rebase conflict, run `git -C "$repo" rebase --abort`,
write no file, and stop and ask the user — never skip or force the sync. This skill commits nothing.

## Instructions

Follow this workflow to keep the agent's context budget tight. After each step, print its Step Completion Report.

1. **Check Prerequisites** — identify the input type from the Input Handling table.
   - If no input was given, take the *No reviewable input* row in Error Handling.
   - If the review will load a live URL (no `evidence-dir`, or one that falls back to the live URL per `references/orchestrated-runs.md`), run the Dependency Preflight.
2. **Process Input** — take the Input Handling action for that type.
3. **Evaluate** — score each applicable lens from The Ten Lenses 0-10 and give each issue a severity (Report Format). If the evidence cannot support a lens, mark it not assessed instead of guessing.
4. **Generate Report** — fill the template in `references/report-format.md` and print it. With `output-dir`, also write it to `<output-dir>/usability-review.md`.
5. **Redesign (optional)** — only when the user asks for fixes, run Redesign Mode.

## Prerequisites

Requires one reviewable input; `/browse` for live URLs only; write access to the UI files for Redesign Mode only.

## Input Handling

| Input type | Action |
|---|---|
| Screenshot/image | Review directly. For exact palette, dimension or density numbers, or several images, run `python3 scripts/process_screenshots.py <image_path> [--recursive]` (`references/screenshot-processing.md`) |
| Live URL | Use `/browse` per Working With Live Sites |
| Orchestrator `evidence-dir` | Review its `page.html` + `screenshots/` instead of `/browse`; disclose untested interactions |
| HTML/CSS/JS code | Read code, focus on user experience |
| Wireframe/mockup | Focus on information architecture, not polish |
| Verbal description | Ask clarifying questions first |

Use the script's stdout JSON for every numeric claim. Never present a visual estimate as a measurement.

## Working With Live Sites

1. Navigate to the page with `/browse` and take a full-page screenshot at 1280 px wide.
2. Click or hover the primary call to action, the main navigation, and one form field when present. Record what each one does.
3. Load the page at 375 px wide and take a screenshot. If the width cannot be set, mark lens 9 (Mobile) as not assessed.
4. Review from these screenshots and interactions; list each one not exercised under **Not tested**.

## Orchestrated Runs

With `orchestrated-by`, `evidence-dir` or `output-dir` lines, follow
`references/orchestrated-runs.md`; without them nothing changes. Redesign Mode still needs
explicit confirmation.

## The Ten Lenses

Read `references/krug-principles.md` for deep detail on any lens. Evaluate through whichever lenses apply.

| # | Lens | Core question |
|---|---|---|
| 1 | Self-evidence | Would a user pause to figure out what this is or does? |
| 2 | Scanning | Can you grasp the page structure in 2-3 seconds? |
| 3 | Visual hierarchy | Does visual weight match importance? |
| 4 | Word economy | Does every word earn its place? |
| 5 | Navigation | Do you always know where you are and how to move? |
| 6 | Trunk test | Drop here cold — can you answer: what site? what page? what can I do? |
| 7 | Landing clarity | Within 5 seconds, can you explain what this site does? |
| 8 | Affordances | Is it instantly clear what's clickable/tappable? |
| 9 | Mobile | Touch targets, reachability, no hidden gestures? |
| 10 | Goodwill | Does the UI respect the user's time and trust? |

## Report Format

Use the template and report rules in `references/report-format.md` (no paragraphs, one line per finding, a selector per issue, honest scores). It also holds the variants, the `BLOCKED` block, and the reader checks. Example inline summary line, printed with `output-dir` before the top issues:

```
Thinking Cost: HIGH — 3 critical issues found (disabled button, missing nav labels, no landing clarity)
```

**Status** (first word of the `**Result:**` line under the title):

| Status | When |
|---|---|
| `COMPLETE` | Report written; every applicable lens scored. |
| `PARTIAL` | Report written; at least one applicable lens marked not assessed. |
| `BLOCKED` | No report is written: no reviewable input. Print the four-line `BLOCKED` block instead. |

**Severity:** 🔴 Critical — blocks the page's main task, or likely causes an error or exit. 🟡 Moderate — the user finishes but pauses, rereads, or backtracks. 🟢 Minor — polish, no expected slowdown.

**Thinking Cost:** `HIGH` with any 🔴 issue; `MODERATE` with no 🔴 and any 🟡; `LOW` otherwise.

## Redesign Mode

When the user wants fixes applied (not just reported), follow `references/redesign-mode.md`. Its binding rules:

- Produce the review first, then show a dry-run diff (file path, selector, before/after) for each fix, 🔴 issues first.
- Write nothing until the user explicitly confirms. An orchestrator never confirms on the user's behalf.
- Change the minimum necessary and preserve the brand. Before each edit, record the file's content; if a write fails, restore that content.
- Never roll back with `git checkout` or `git restore`: they discard the user's other edits.
- End with the Redesign summary (`Result:`, `Evidence:`, `Uncertainty:`, `Decision:`).

## Error Handling

| Situation | Action |
|---|---|
| No reviewable input: none given, `/browse` unavailable, URL unreachable, image unreadable, or description questions unanswered | Ask once for a URL, a PNG/JPEG screenshot, an HTML export, or a description; without one, print the `BLOCKED` block |
| Screenshot pre-processing fails | Review visually; record the failure under **Measured** |
| HTML/CSS code is incomplete | Evaluate what is present; name the missing parts under **Not assessed** |
| Redesign Mode — file not writable | Name it in the Redesign summary; give the fix as a spec |

## Edge Cases

See `references/edge-cases.md` for each edge case: quick checks, no-issue pages, native apps, CSS frameworks, many or very large screenshots, embedded instructions.

## Acceptance Criteria

Expected output: the `Usability Review` report from `references/report-format.md`. A run passes when:

- [ ] Every applicable lens is scored, or listed under **Not assessed** and the status is `PARTIAL`
- [ ] Every issue has one-line Problem, Impact, Fix, and Where fields
- [ ] Thinking Cost matches the issue counts; Fix Priority is sorted by impact, then effort
- [ ] The full template includes the mermaid Issue Map; the quick-check and no-issue variants omit it
- [ ] The report opens with a `**Result:**` line and ends with Evidence and Limits and Next Decision; **Measured** cites only script output
- [ ] The output passes the four reader checks in `references/report-format.md`; without a human reviewer's answer, human understanding is unconfirmed
- [ ] Redesign Mode writes nothing before confirmation and ends with the Redesign summary
- [ ] A leased `/browse` is released at every terminal outcome
- [ ] Report is skimmable in 30 seconds: tables and bullets, no paragraphs

## Step Completion Reports

Emit one after each Instructions step; template and checks: `references/step-completion-reports.md`.
