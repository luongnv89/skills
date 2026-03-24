---
name: theme-transformer
description: Transform an existing website/app UI into a futuristic cyberpunk, neon, space, or digital-dark theme with user-adjustable colors. Use when asked to "reskin the UI", "apply a dark theme", "cyberpunk style this app", "make the interface futuristic", "apply neon command center style", or migrate a product to a new visual theme.
effort: medium
license: MIT
metadata:
  version: 1.0.0
  creator: Luong NGUYEN <luongnv89@gmail.com>
---

# Theme Transformer

Transform existing interfaces into a futuristic cyberpunk/neon design system while preserving usability and product clarity.

## Default Style Profile
Use **Neon Command Center** as default visual baseline:
- Futuristic + space + cyberpunk + digital-dark
- Dark-first surfaces
- Electric blue/cyan accents
- Controlled glow (signal, not decoration)

Read these references when running this skill:
- `references/theme-tokens.md` (core tokens + mapping rules)
- `references/neon-command-center.md` (full style language)

If the target repo already has local branding docs (for example `docs/branding.md`, `brand.md`, `design-system.md`), read them first and prioritize user/project brand constraints.

## Mandatory Safety Rule: branch first
Before changing any file, sync with remote and check the current branch. Only create a new branch if on `main` or `master` — otherwise continue on the existing branch (the user likely set it up already or is resuming work):

```bash
current_branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$current_branch"

if [ "$current_branch" = "main" ] || [ "$current_branch" = "master" ]; then
  slug="$(echo "${THEME_SLUG:-theme-transform}" | tr '[:upper:] ' '[:lower:]-' | tr -cd 'a-z0-9-')"
  ts="$(date +%Y%m%d-%H%M%S)"
  git checkout -b "design/${slug}-${ts}"
fi
```

If pull/rebase conflicts happen, stop and resolve with user before edits.

## Mandatory 4-step workflow (approval-gated)

### Step 1) Analyze current style
Produce a concise style audit first.

Audit checklist:
- Color system + contrast
- Typography scale + readability
- Spacing/radius/shadow consistency
- Component states (buttons, inputs, nav, cards, tables, charts)
- Motion behavior
- Visual hierarchy / density

Output format:
- Current strengths
- Current inconsistencies
- Migration risks

Do **not** implement changes before audit is shared.

---

### Step 2) Propose full design transformation
Propose the transformed design for all major elements.

Must include:
- Theme direction statement
- Token updates (color/type/radius/shadow/motion)
- Component-by-component transformation map
- Before/after intent for key screens

Iterate until user is happy:
- Ask for feedback
- Adjust proposal
- Repeat until explicit approval

No implementation before approval.

---

### Step 3) Propose implementation plan (step-by-step)
Create a gradual execution plan with verifiable checkpoints.

Each task must include:
- Goal
- Files/components impacted
- Expected visual result
- Verification method (screenshot/storybook/page checks/contrast checks)
- Rollback note

Plan quality rules:
- Sequence: tokens -> foundations -> shared components -> pages
- Small, reviewable increments
- Include accessibility checks each phase

Iterate the plan with user until approved.

No execution before plan approval.

---

### Step 4) Execute approved plan
Run incremental execution loop:
1. Implement one task.
2. Run checks/build.
3. Provide verification instructions and/or screenshots.
4. Ask for feedback and adjust if requested.

Continue until user confirms satisfaction.

## Color customization (mandatory)
Theme colors must be adjustable based on user input.

Rules:
- Keep dark structure by default (`bg/surface/text`).
- Map user accent color(s) to neon action tokens.
- Preserve semantic colors unless user requests custom semantics.

If user gives one color:
- Use as `primary-500`
- Auto-generate `primary-400` (hover) and glow alpha variants

If user gives two colors:
- 1st color = primary action
- 2nd color = secondary accent/data highlights

If user provides full palette:
- Respect provided palette; skip defaults

## Deliverables (minimum)
- Updated tokens/theme definitions (CSS/Tailwind/theme config)
- Updated shared components
- Updated target screens/pages
- Verification summary (what changed + how to test)
- Branch name + commit summary

## Quality guardrails
- Avoid unreadable neon-on-neon combinations
- Avoid global glow overuse
- Keep dense dashboard information scannable
- Preserve focus states and keyboard accessibility
- Prioritize usability over effects
