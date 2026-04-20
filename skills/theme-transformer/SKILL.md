---
name: theme-transformer
description: "Transform an existing website/app UI into a futuristic cyberpunk, neon, space, or digital-dark theme with user-adjustable colors. Use when asked to reskin the UI, dark theme, cyberpunk style, or make the interface futuristic. Don't use for building a UI from scratch, pure light/minimal themes, or backend/API changes."
effort: medium
license: MIT
metadata:
  version: 1.0.2
  author: Luong NGUYEN <luongnv89@gmail.com>
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

## Prerequisites

- **Git** with write access to the repository (branching is mandatory before any file changes)
- **Reference files present**: `references/theme-tokens.md` and `references/neon-command-center.md` in the repo; the skill reads these before generating any token proposals
- **Build tooling available**: the project must be buildable locally (e.g., `npm run build` or equivalent) so the execution phase can verify changes compile without errors
- **Optional**: an existing design system or branding doc (`docs/branding.md`, `brand.md`, `design-system.md`) — if present, the skill reads it first to honor brand constraints

## Expected Output

After completing all four workflow steps on a React/Tailwind project, you should see:
- A new git branch named `design/theme-transform-<timestamp>` with all changes committed
- Updated design tokens file (e.g., `tailwind.config.js`, `tokens.css`, or equivalent) with the full Neon Command Center color, typography, radius, shadow, and motion values
- Updated shared component files (buttons, inputs, nav, cards, tables, charts) with the new visual treatment applied
- Updated target pages/screens applying the theme end-to-end
- A verification summary listing every changed file, the before/after intent, and instructions for visual QA (contrast ratios, focus states, responsive checks)

## Edge Cases

- **No design token system exists**: Introduce a minimal tokens file (CSS custom properties or JS theme object) and migrate existing hardcoded values into it before applying the new theme.
- **User provides a custom accent color**: Derive `primary-400` hover and glow alpha variants automatically; do not override `bg/surface/text` dark structure unless explicitly requested.
- **Project uses a CSS-in-JS runtime theme**: Apply tokens through the runtime's theme API rather than static files; verify hot-reload picks up changes during execution.
- **Accessibility conflict**: If a proposed neon color combination fails WCAG AA contrast, replace with a higher-contrast variant and note the substitution in the verification summary.
- **Existing local branding docs found**: Treat them as hard constraints — do not override brand colors or typography unless the user explicitly asks.
- **Large codebase with hundreds of components**: Scope Step 4 execution to the highest-traffic pages first; create a follow-up task list for remaining components rather than attempting everything in one pass.

## Step Completion Reports

After completing each major step, output a status report in this format:

```
◆ [Step Name] ([step N of M] — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          √ pass (note if relevant)
  [Check 3]:          × fail — [reason]
  [Check 4]:          √ pass
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Adapt the check names to match what the step actually validates. Use `√` for pass, `×` for fail, and `—` to add brief context. The "Criteria" line summarizes how many acceptance criteria were met. The "Result" line gives the overall verdict.

**Branch & Sync phase checks:** `Branch created`, `Remote synced`, `Working tree clean`

**Audit phase checks:** `Current styles analyzed`, `Components cataloged`, `Color palette extracted`

**Design phase checks:** `Theme proposed`, `Color scheme defined`, `User approved`

**Execution phase checks:** `Styles applied`, `Components updated`, `Visual consistency verified`

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
