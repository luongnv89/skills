---
name: frontend-design
description: "Build production-grade frontend interfaces with distinctive aesthetics and working code. Use for UI components, pages, or frontend features. Don't use for backend/API work or usability-only audits."
license: MIT
effort: high
metadata:
  version: 1.4.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Frontend Design

Create distinctive, production-grade frontend interfaces that avoid generic "AI slop" aesthetics. Implement real working code with deliberate aesthetic choices.

## When to Use

Trigger this skill when the user asks to:
- Build a UI component, page, or full frontend application
- Design or implement a frontend feature (navigation, forms, data tables, dashboards)
- Redesign an existing interface for better aesthetics or usability
- Convert a mockup, wireframe, or spec into working code

## Instructions

1. Record the **explicit brief**: any style preference, color palette, brand kit, or style direction the user gives. If there is none, the Default Style Guide applies.
2. If the request does not state the purpose and the target audience, ask for them before writing code.
3. If the work extends an existing codebase, read its framework, CSS variables, and component patterns before proposing anything.
4. Propose an aesthetic direction (*Design Thinking*). In an existing codebase, also list the files you will create or modify. Emit the Design Thinking step report.
5. Wait for the user to approve the direction before writing code. If the user asks for changes, propose again. If the user says "just build it", state the direction in one line and continue. If the user ends the run without approving, end with a `BLOCKED` Final Report.
6. Read `references/aesthetics-guide.md` and the Quick rules in `references/usability-guide.md`. Run *Repo Sync Before Edits*. Then implement the code. Add a short comment at each non-obvious design decision (font pairing, palette mapping, motion timing).
7. Run the verification checks:
   - **Responsive:** if a browser tool is available, render at 375, 768, and 1280 px and check for horizontal overflow. Otherwise, inspect the breakpoints in the CSS and record responsive rendering as untested.
   - **Contrast:** compute the contrast ratio of each text and background color pair. Each must be at least 4.5:1, or 3:1 for text at 24 px or larger (18.66 px or larger when bold).
   - **Quality and usability:** walk the Default Quality Bar checklist and the six usability Quick rules.
   - **Build:** if the project has a build, lint, or test command, run it and record the exit result. Otherwise record `build: not run (no command)`.
8. If a check fails, fix it and re-run that check. After the second fix cycle, stop fixing and list each remaining failure in the Final Report.
9. Emit the Implementation step report, then the Final Report.

## Repo Sync Before Edits (mandatory)

Run this once, before the first file write in step 6. The sync target is the directory the code is written to.

1. Run `repo="$(git -C "<target dir>" rev-parse --show-toplevel)"`. If it fails, skip the sync and record `sync: skipped (not a git repo)`.
2. Run `git -C "$repo" remote get-url origin`. If it fails, skip steps 3–7 and record `sync: skipped (no origin)`.
3. Run `branch="$(git -C "$repo" rev-parse --abbrev-ref HEAD)"`. If it prints `HEAD`, skip steps 4–7 and record `sync: skipped (detached HEAD)`.
4. Run `git -C "$repo" status --porcelain`. If the output is empty, run `git -C "$repo" fetch origin && git -C "$repo" pull --rebase origin "$branch"`.
5. If the output is not empty, run `git -C "$repo" stash push -u -m "frontend-design pre-sync"`, then the same fetch and pull, then `git -C "$repo" stash pop`.
6. If `fetch` or `pull` fails before a rebase starts (network, authentication, or a missing remote branch), do not retry. Run `git -C "$repo" stash pop` when step 5 stashed, record `sync: failed (<first error line>)`, and continue.
7. If the rebase conflicts, run `git -C "$repo" rebase --abort`, then `git -C "$repo" stash pop` when step 5 stashed. If the stash pop conflicts, leave the stash in place. In both cases write no file; stop and ask the user how to continue. With no answer, the status is `BLOCKED`.

This skill commits nothing.

## Design Thinking

Before coding, identify the active style source and commit to a clear aesthetic direction:
- **Brief precedence**: With an explicit brief, follow it. Without one, the Default Style Guide below is binding: keep its four core colors (with the text-only status-color exception) and its elegant, clear, clean, professional language; make the result distinctive through composition, typography, spacing, depth, and motion rather than extra core colors.
- **Purpose**: What problem does this interface solve? Who uses it?
- **Tone**: With an explicit brief, honor its direction. Without one, choose from directions such as brutally minimal, maximalist, retro-futuristic, organic/natural, luxury/refined, playful, editorial/magazine, brutalist/raw, art deco/geometric, soft/pastel, or industrial/utilitarian, and only when the direction stays compatible with the Default Style Guide.
- **Constraints**: Technical requirements (framework, performance, accessibility).
- **Differentiation**: Name the one thing someone will remember about this interface.

Bold maximalism and refined minimalism both work when they fit the active style source; the key is intentionality, not intensity.

## Default Style Guide

When the user gives no explicit brief, apply this style guide:

1. **Color Palette (Strictly Limited):** Use only four core colors — Black (`#000000`), White (`#FFFFFF`), Gray (`#6B7280`), and Bright Green (`#22C55E`).
2. **Aesthetic:** Maintain an elegant, clear, clean, and professional design language.
3. **Visual Depth:** Incorporate visual depth using elements like cards, lines, borders, and subtle shadows.
4. **Bright Green Usage Constraint:** The Bright Green color is strictly reserved for highlights (text, borders, or lines); it must *never* be used as a background color.
5. **System Status Colors:** Danger (`#EF4444`), Warning (`#F59E0B`), and Info (`#3B82F6`) may only be applied to text elements, not backgrounds or primary UI components.

An explicit brief overrides only the palette and aesthetic defaults. It never overrides the accessibility requirements or the text-only rule for system status colors.

## Default Quality Bar

Every final design must be professional, production-ready, elegant, and premium, even unasked and regardless of aesthetic direction. The brief sets the style; this bar sets the finish. Premium comes from craft and execution, not from the clichés listed under *Avoid* in `references/aesthetics-guide.md`. Check before delivery:
- Consistent spacing rhythm and type scale; pixel-aligned edges
- Intentional palette; coherent radii, borders, and shadows
- Every interactive state: hover, focus, active, disabled, plus loading/empty/error where relevant
- No placeholder, lorem ipsum, TODO, or broken asset; nothing looks like a draft
- None of the defaults listed under *Avoid*, unless the explicit brief asked for one

## Usability and Aesthetics References

- **Usability:** apply the six Quick rules in `references/usability-guide.md` to every design; the full step-by-step guideline follows them.
- **Aesthetics:** `references/aesthetics-guide.md` holds the typography, color, motion, composition, and background guidance and the *Avoid* list.

Read both in step 6, not earlier, to keep the context window small during the brief and approval steps.

## Expected Output

Production-ready frontend code delivered as one or more files. Example for a landing page request:

- **`index.html`** — fully self-contained HTML with embedded CSS and JS (or separate files if a framework is used)
- Implemented features: hero section, CTA button, responsive navigation, and a features grid
- Typography: a distinctive display/body font pairing (e.g., Playfair Display + DM Sans), not Inter/Roboto
- Color palette: strictly four colors per the Default Style Guide, or the explicit brief's palette
- Interactions: CSS-only hover states on buttons, a staggered reveal animation on page load
- WCAG AA contrast on all text elements
- Mobile-responsive layout checked at 375px, 768px, and 1280px

## Final Report

End every run, stops included, with this compact text block. Status is `COMPLETE` (code written, no check failed), `PARTIAL` (code written, a check still fails after the second fix cycle), or `BLOCKED` (no code written). A question that awaits the user's answer does not end the run; if the user ends the run without answering, the status is `BLOCKED`. Fill rules, `PARTIAL` and `BLOCKED` examples, and reader checks: `references/final-report.md`. Example:

```text
Result: COMPLETE. Wrote index.html (landing page: hero, CTA, nav, features grid).
Evidence: Contrast lowest 4.8:1 (Gray on White). Quality Bar and usability Quick rules passed. build: not run (no command). sync: skipped (not a git repo)
Uncertainty: Responsive rendering untested: no browser available; breakpoints at 375/768/1280 px inspected in CSS. Assumed a developer audience; the brief did not say.
Decision: No approval needed. Replace the placeholder logo with your own asset.
```

## Acceptance Criteria

A run passes when **all** of the following are true:

- [ ] The user approved the aesthetic direction, or said "just build it", before any code was written.
- [ ] Delivered code runs without errors in the target framework (HTML/CSS/JS, React, Vue, etc.); the build command passed when one exists.
- [ ] Layout has no horizontal overflow at 375px, 768px, and 1280px, or the Final Report records responsive rendering as untested.
- [ ] Accessibility basics covered: semantic HTML, every text pair at WCAG AA contrast, keyboard focus states, and `alt`/`aria-label` where applicable.
- [ ] Without an explicit brief, only the Default Style Guide colors are used, and Bright Green is never a background.
- [ ] Every Default Quality Bar item and every usability Quick rule passes, or the Final Report lists the failure.
- [ ] The Final Report opens with `Result:` and its status, and has `Evidence:`, `Uncertainty:`, and `Decision:` lines. `Evidence:` cites only checks that ran.
- [ ] The Final Report passes the four reader checks in `references/final-report.md` (result findable, facts and assumptions separated, claims traceable, next decision clear). Without a human reviewer's answer, human understanding is unconfirmed.

## Edge Cases

- **Conflicting style constraints** (e.g., user says "minimalist" but also "lots of animations"): Name the conflict and ask which constraint takes priority; do not pick one silently.
- **Existing codebase to extend**: Never introduce a second design system next to the one read in step 3.
- **Framework mismatch** (e.g., user says "React" but the repo uses Vue): Confirm the framework before generating; never output React JSX into a Vue project.
- **More than 5 distinct page sections**: Offer to deliver in phases — core layout first, then secondary sections — rather than one oversized artifact.
- **Accessibility conflict with aesthetic direction**: Never drop below WCAG AA contrast for aesthetic reasons; change the color pairing instead.
- **No internet/CDN access in deployment**: If the user indicates an offline or air-gapped environment, use locally bundled assets or inline critical CSS/JS instead of CDN links.

## Step Completion Reports

Emit the Design Thinking report at step 4 and the Implementation report at step 9, then the Final Report. See `references/step-reports.md` for the template, symbol legend, and per-phase checks. Keep these reports concise to preserve the agent's context budget.
