---
name: frontend-design
description: "Build production-grade frontend interfaces with distinctive aesthetics and working code. Use when asked to create a UI, component, page, or frontend feature. Skip for backend/API work or usability-only audits."
license: MIT
effort: high
metadata:
  version: 1.2.2
  author: Luong NGUYEN <luongnv89@gmail.com>
---

# Frontend Design

Create distinctive, production-grade frontend interfaces that avoid generic "AI slop" aesthetics. Implement real working code with exceptional attention to aesthetic details and creative choices.

## When to Use

Trigger this skill when the user asks to:
- Build a UI component, page, or full frontend application
- Design or implement a frontend feature (navigation, forms, data tables, dashboards)
- Redesign an existing interface for better aesthetics or usability
- Convert a mockup, wireframe, or spec into working code

## Instructions

1. Clarify the requirements (component type, framework, target audience, design constraints)
2. Propose an aesthetic direction and get user approval before coding
3. Implement the full working code with distinctive visual choices
4. Validate responsiveness and accessibility basics
5. Deliver the code with inline annotations for key design decisions

## Repo Sync Before Edits (mandatory)
Before creating/updating/deleting files in an existing repository, sync the current branch with remote:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If the working tree is not clean, stash first, sync, then restore:

```bash
git stash push -u -m "pre-sync"
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin && git pull --rebase origin "$branch"
git stash pop
```

If `origin` is missing, pull is unavailable, or rebase/stash conflicts occur, stop and ask the user before continuing.

## Design Thinking

Before coding, understand the context and commit to a BOLD aesthetic direction:
- **Purpose**: What problem does this interface solve? Who uses it?
- **Tone**: Pick an extreme: brutally minimal, maximalist chaos, retro-futuristic, organic/natural, luxury/refined, playful/toy-like, editorial/magazine, brutalist/raw, art deco/geometric, soft/pastel, industrial/utilitarian, etc. There are so many flavors to choose from. Use these for inspiration but design one that is true to the aesthetic direction.
- **Constraints**: Technical requirements (framework, performance, accessibility).
- **Differentiation**: What makes this UNFORGETTABLE? What's the one thing someone will remember?

**CRITICAL**: Choose a clear conceptual direction and execute it with precision. Bold maximalism and refined minimalism both work - the key is intentionality, not intensity.

Then implement working code (HTML/CSS/JS, React, Vue, etc.) that is:
- Production-grade and functional
- Visually striking and memorable
- Cohesive with a clear aesthetic point-of-view
- Meticulously refined in every detail

## Default Style Guide

When the user does **not** provide a specific style preference, color palette, or brand guidelines, apply this default style guide:

1. **Color Palette (Strictly Limited):** Use only four core colors — Black (`#000000`), White (`#FFFFFF`), Gray (`#6B7280`), and Bright Green (`#22C55E`).
2. **Aesthetic:** Maintain an elegant, clear, clean, and professional design language.
3. **Visual Depth:** Incorporate visual depth using elements like cards, lines, borders, and subtle shadows.
4. **Bright Green Usage Constraint:** The Bright Green color is strictly reserved for highlights (text, borders, or lines); it must *never* be used as a background color.
5. **System Status Colors:** Danger (`#EF4444`), Warning (`#F59E0B`), and Info (`#3B82F6`) may only be applied to text elements, not backgrounds or primary UI components.

If the user provides their own colors, brand kit, or style direction, use those instead and ignore this default guide.

## Usability Principles — "Don't Make Me Think"

Every design MUST follow these usability rules derived from Steve Krug's principles. These are non-negotiable regardless of aesthetic direction.

### 1. Design for Scanning, Not Reading
- Users scan pages — they do not read them. Use clear headings, short paragraphs, bullet points, and visual hierarchy (bigger/bolder = more important).
- Highlight keywords. Apply the **billboard rule**: if a user can't grasp the page purpose in 5 seconds, simplify.

### 2. Follow Conventions
- Place navigation at the top, logo upper-left, search top-right. Use familiar icons (magnifying glass for search, hamburger for mobile menu).
- Use straightforward labels: "Books" not "Library Vault". Clicks are fine if each is unambiguous.

### 3. Make Interactions Self-Evident
- Buttons must look clickable (shaded, bordered, with hover states). Links must be visually distinct from body text.
- CTAs use action verbs ("Shop Now", "Get Started") and are prominently placed. Forms have no unnecessary fields.

### 4. Eliminate Cognitive Load
- Edit ruthlessly — cut half the words, then half again. Use plain language, no jargon.
- Ensure consistency across pages: same button styles, same spacing patterns, same color semantics.
- Design error states gracefully: clear messages with recovery suggestions (e.g., "No results found. Try a broader search.").

### 5. Self-Test Every Design
- Before delivering, simulate user paths: role-play 3-5 task scenarios (e.g., "Find and buy a product"). Flag any point of hesitation.
- Verify mobile responsiveness — the design must adapt without losing core functionality.

### 6. Accessibility Is Mandatory
- Alt text on all images, WCAG AA contrast (4.5:1 minimum), keyboard navigable.
- Site identity (logo, tagline) visible on every page.

For the full step-by-step guideline, see `references/usability-guide.md`.

## Frontend Aesthetics Guidelines

Focus on:
- **Typography**: Choose fonts that are beautiful, unique, and interesting. Avoid generic fonts like Arial and Inter; opt instead for distinctive choices that elevate the frontend's aesthetics; unexpected, characterful font choices. Pair a distinctive display font with a refined body font.
- **Color & Theme**: Commit to a cohesive aesthetic. Use CSS variables for consistency. Dominant colors with sharp accents outperform timid, evenly-distributed palettes.
- **Motion**: Use animations for effects and micro-interactions. Prioritize CSS-only solutions for HTML. Use Motion library for React when available. Focus on high-impact moments: one well-orchestrated page load with staggered reveals (animation-delay) creates more delight than scattered micro-interactions. Use scroll-triggering and hover states that surprise.
- **Spatial Composition**: Unexpected layouts. Asymmetry. Overlap. Diagonal flow. Grid-breaking elements. Generous negative space OR controlled density.
- **Backgrounds & Visual Details**: Create atmosphere and depth rather than defaulting to solid colors. Add contextual effects and textures that match the overall aesthetic. Apply creative forms like gradient meshes, noise textures, geometric patterns, layered transparencies, dramatic shadows, decorative borders, custom cursors, and grain overlays.

NEVER use generic AI-generated aesthetics like overused font families (Inter, Roboto, Arial, system fonts), cliched color schemes (particularly purple gradients on white backgrounds), predictable layouts and component patterns, and cookie-cutter design that lacks context-specific character.

Interpret creatively and make unexpected choices that feel genuinely designed for the context. No design should be the same. Vary between light and dark themes, different fonts, different aesthetics. NEVER converge on common choices (Space Grotesk, for example) across generations.

**IMPORTANT**: Match implementation complexity to the aesthetic vision. Maximalist designs need elaborate code with extensive animations and effects. Minimalist or refined designs need restraint, precision, and careful attention to spacing, typography, and subtle details. Elegance comes from executing the vision well.

## Expected Output

Production-ready frontend code delivered as one or more files. Example for a landing page request:

- **`index.html`** — fully self-contained HTML with embedded CSS and JS (or separate files if a framework is used)
- Implemented features: hero section, CTA button, responsive navigation, and a features grid
- Typography: a distinctive display/body font pairing (e.g., Playfair Display + DM Sans), not Inter/Roboto
- Color palette: strictly four colors per the default style guide, or user-provided palette
- Interactions: CSS-only hover states on buttons, a staggered reveal animation on page load
- WCAG AA contrast on all text elements
- Mobile-responsive layout verified at 375px, 768px, and 1280px breakpoints

After delivery, the skill emits a step-completion report confirming design thinking choices, style guide adherence, and usability self-test results. See `references/step-reports.md` for the full report template and phase-specific check formats.

## Edge Cases

- **No description provided**: Ask the user for purpose, target audience, and any brand/style constraints before writing a single line of code.
- **Conflicting style constraints** (e.g., user says "minimalist" but also "lots of animations"): Surface the tension and ask which constraint takes priority; don't silently pick one.
- **Existing codebase to extend**: Read existing CSS variables and component patterns before adding new code; match the existing style vocabulary rather than introducing a second design system.
- **Framework mismatch** (e.g., user says "React" but the repo uses Vue): Confirm the framework before generating; never output React JSX into a Vue project.
- **Very large or complex UIs** (>5 distinct page sections): Offer to deliver in phases — core layout first, then secondary sections — rather than one oversized artifact.
- **Accessibility conflict with aesthetic direction**: Never sacrifice WCAG AA contrast for aesthetic reasons; adapt the palette instead of dropping the requirement.
- **No internet/CDN access in deployment**: Use locally bundled assets or inline critical CSS/JS rather than CDN links, if the user indicates an offline or air-gapped environment.

## Step Completion Reports

After completing each major step (Design Thinking, Implementation), emit a structured status report. See `references/step-reports.md` for the full template, symbol legend, and phase-specific check lists. Keep these reports concise to preserve the agent's context budget.
