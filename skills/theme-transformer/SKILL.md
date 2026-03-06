---
name: theme-transformer
description: "Transform an existing website or app UI into a futuristic, space, cyberpunk, neon, digital-dark theme with user-adjustable color accents. Use when users ask to redesign current interfaces/styles, reskin an existing product, or apply a full theme transformation. Enforce a safe workflow: always create a new git branch first, analyze current style, propose changes, create a step-by-step implementation plan with verification points, then execute iteratively until user is satisfied."
---

# Theme Transformer

Transform existing interfaces into a futuristic cyberpunk/neon design system without breaking functionality.

## Repo Safety Rule (mandatory)
Before changing any file, create a new branch.

1. Verify this is a git repository.
2. Ensure local branch is synced.
3. Create a dedicated branch for the theme transformation.

Use:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"

slug="$(echo "${THEME_SLUG:-theme-transform}" | tr '[:upper:] ' '[:lower:]-' | tr -cd 'a-z0-9-')"
ts="$(date +%Y%m%d-%H%M%S)"
git checkout -b "design/${slug}-${ts}"
```

If pull/rebase conflicts happen, stop and resolve with the user before continuing.

## Workflow (mandatory)
Follow this exact sequence.

### 1) Analyze the current style
Produce a concise style audit before proposing changes.

Audit checklist:
- Color tokens and contrast
- Typography scale and font pairing
- Spacing/radius/shadow system
- Component styles (buttons, cards, inputs, nav, tables, charts)
- Motion/interaction patterns
- Visual density and hierarchy

Output format:
- Current strengths
- Current inconsistencies
- Risks during theme migration (contrast, readability, complexity)

### 2) Propose design transformation for all elements
Propose a complete transformation plan, covering all core UI elements.

Must include:
- Theme direction statement (futuristic/space/cyberpunk/digital dark)
- Updated design tokens (colors, type, radius, shadows, motion)
- Component-by-component changes
- Before/after intent for major screens

Use `references/theme-tokens.md` for default token structure.

Iterate until user is happy:
- Ask for feedback after proposal.
- Adjust palette/style details based on user input.
- Repeat proposal updates until explicitly approved.

### 3) Propose implementation plan with verifiable steps
Create a gradual task plan with checkpoints.

Each task must contain:
- Goal
- Files/components to change
- Expected visual result
- Verification method (screenshot, storybook route, page check, contrast check)
- Rollback note (how to revert this step)

Plan quality rules:
- Start from tokens/foundation, then shared components, then pages.
- Keep each task small enough to review safely.
- Include accessibility checks (contrast, focus state, readable text).

Iterate plan until user approves.

### 4) Execute the approved plan
Implement tasks step-by-step and verify after each step.

Execution loop:
1. Apply one task.
2. Run relevant checks/build.
3. Show what changed and how to verify.
4. Ask for feedback and adjust if requested.

Continue until user confirms satisfaction.

## Color customization rule
Always allow accent color customization from user input while preserving dark cyberpunk structure.

Default behavior:
- Keep dark base surfaces.
- Map user-selected accent hue to primary/secondary neon tokens.
- Preserve semantic colors (success/warning/danger) unless user asks to change them.

If user gives only one color:
- Use it as primary neon accent.
- Auto-generate lighter hover and softer glow variants.

If user gives full palette:
- Respect provided palette and skip defaults.

## Deliverables
At minimum, produce:
- Updated design token definitions (CSS/Tailwind/theme file)
- Updated shared components
- Updated target screens/pages
- Verification summary (what changed, how to test)
- Branch name and commit summary

## Quality guardrails
- Do not ship unreadable neon-on-neon contrast.
- Do not overuse glow on every element.
- Keep information hierarchy clear for dense dashboard screens.
- Preserve usability over visual effects.
