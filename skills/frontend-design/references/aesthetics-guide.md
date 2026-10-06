# Frontend Aesthetics Guide

Read this before Instructions step 6 (implement). `SKILL.md` holds the Default Style Guide and the Default Quality Bar; this file holds the craft guidance they apply to. When this guide and the Default Style Guide disagree, the Default Style Guide wins unless the user gave an explicit brief.

## Focus areas

- **Typography**: Choose fonts that are beautiful, unique, and interesting. Avoid generic fonts like Arial and Inter; opt instead for distinctive choices that elevate the frontend's aesthetics; unexpected, characterful font choices. Pair a distinctive display font with a refined body font.
- **Color & Theme**: Commit to a cohesive aesthetic. Use CSS variables for consistency. Under the no-brief default, stay within its four-color palette; an explicit brief may override that palette. Dominant colors with sharp accents outperform timid, evenly-distributed palettes.
- **Motion**: Use animations for effects and micro-interactions. Prioritize CSS-only solutions for HTML. Use Motion library for React when available. Focus on high-impact moments: one well-orchestrated page load with staggered reveals (animation-delay) creates more delight than scattered micro-interactions. Use scroll-triggering and hover states that surprise.
- **Spatial Composition**: Unexpected layouts. Asymmetry. Overlap. Diagonal flow. Grid-breaking elements. Generous negative space OR controlled density.
- **Backgrounds & Visual Details**: Create atmosphere and depth rather than defaulting to solid colors. Add contextual effects and textures that match the overall aesthetic. Under the no-brief default, keep gradients, textures, and other effects within the four-color palette; transparency and depth effects are fine. Apply creative forms like gradient meshes, noise textures, geometric patterns, layered transparencies, dramatic shadows, decorative borders, custom cursors, and grain overlays.

## Avoid

Avoid the defaults that make interfaces look generated: overused fonts (Inter, Roboto, Arial, system stacks, Space Grotesk), purple gradients on white, cream/off-white page backgrounds, italic accent words inside headlines, numbered "01 / 02 / 03" section labels, monospace eyebrow labels, and pill-shaped buttons. Do not converge on the same choices across generations.

The Default Quality Bar in `SKILL.md` checks this list before delivery: a design that uses any item above fails that check unless the user's explicit brief asked for it.

## Variation

With an explicit brief, vary between light and dark themes, different fonts, and different aesthetics as requested; without one, vary composition and typography while remaining within the default palette and elegant, clear, clean style.

## Matching complexity to the vision

Match implementation complexity to the aesthetic vision. Maximalist designs need elaborate code with extensive animations and effects. Minimalist or refined designs need restraint, precision, and careful attention to spacing, typography, and subtle details. Elegance comes from executing the vision well.
