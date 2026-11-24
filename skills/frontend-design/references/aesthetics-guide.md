# Frontend Aesthetics Guide

Read the *Avoid* section at Instructions step 4 and the rest before step 6 (implement). `SKILL.md` holds the Default Style Guide and the Default Quality Bar; `references/system-defaults.md` holds the tokens, motion numbers, rules-file protocol and vague-word map; this file holds the craft guidance and the ban table. Precedence, highest first: the user's explicit brief, the project's design-rules file, the Default Style Guide, this guide.

## Focus areas

- **Typography**: Pair a distinctive display font with a refined body font chosen for this brief, never one from the ban table. Use at most two weights (for example 400 and 600) and sentence case for headings, buttons, labels and navigation.
- **Color & Theme**: Declare colors once as semantic tokens (`references/system-defaults.md`) and use only those tokens in components. Surfaces stay neutral; the accent marks only active or selected states. Under the no-brief default, stay within the four-color palette; an explicit brief may override that palette.
- **Motion**: Motion explains a state change: a menu opening, a dialog closing, a selection moving. Follow the motion numbers in `references/system-defaults.md`: interface motion under 300 ms, exits faster than entries, `prefers-reduced-motion` honoured, nothing animating on page load or scroll. Prefer CSS transitions for HTML; use the Motion library for React when the project already has it.
- **Spatial Composition**: Make the layout memorable through structure: asymmetry, a strong grid with one deliberate break, overlap, generous negative space OR controlled density.
- **Backgrounds & Visual Details**: Under the no-brief default, backgrounds are flat token colors. Separate regions with spacing, a 1 px border or an inverted section, not with effects. Shadows go only on elements that float above the page: menus, popovers, dialogs, toasts, and a sticky header once the page scrolls under it.

## Explicit brief or maximalist direction

When the user's explicit brief asks for a bold or maximalist look, or names an element, these techniques are available: gradient meshes, noise and grain textures, geometric patterns, layered transparencies, dramatic shadows, decorative borders, custom cursors, a choreographed page-load sequence, and scroll-triggered effects. Use only the ones the brief names or asks for; each one lifts its ban-table row, so the Quality Bar passes it. Accessibility, contrast, the text-only status-color rule and `prefers-reduced-motion` still apply.

Without an explicit brief, a bold or maximalist direction stays available, and its intensity comes from composition, type scale, density and black-and-white blocking within the palette, not from ban-table elements.

## Avoid

The ban table: the defaults that make interfaces look generated. Each row is banned unless the user's explicit brief or the project's design-rules file asks for that element; then the row passes. A brief item handed over by a calling skill counts as the explicit brief. Accessibility and the text-only status-color rule never change.

| Element | Why it reads as AI-default | Do instead |
|---|---|---|
| Gradients of any color: backgrounds, meshes, text, buttons, tiles (purple on white is the classic case) | The first decoration a model reaches for when nothing else is decided | Flat token colors; hierarchy from size, weight and space |
| Glow: colored `box-shadow` or `text-shadow` halos, neon outlines | Fakes emphasis instead of deciding what matters | Make the important element larger, bolder or first |
| Grain, noise or texture overlays | Adds atmosphere that carries no information | Flat surfaces |
| Dramatic or decorative shadows, and shadows on static cards and sections | Fakes depth on elements that never move above the page | Shadows only on floating elements; spacing or a 1 px border elsewhere |
| Cards inside cards | Doubles borders and padding and hides the hierarchy | One container level; group inside it with spacing or a divider |
| Icon-in-circle feature cards: an icon in a tinted circle above a title and two lines | The generic three-up features grid of generated pages | Lead with the claim, a number or a real screenshot; icons only where they label a control |
| Staggered section reveals: each block fading up with its own `animation-delay` | Delays the content the user came to read | Content visible on load; motion only on a state change |
| Scroll-triggered entrances and hover effects meant to surprise (tilt, magnetic, parallax) | Decoration that makes the page harder to scan and use | Plain hover and focus states that show what is interactive |
| Bounce, spring overshoot or elastic easing | Reads as a toy and slows every interaction | `ease-out` for entries, `ease-in` for exits, no overshoot |
| Sparkle emoji, and emoji used as icons or bullets | Shorthand for "AI" or "magic" that says nothing | Words, or one icon from the project's icon set |
| Eyebrow labels above headings in any font, including uppercase letter-spaced or monospace labels | A label that restates or pre-announces the heading under it | Let the heading stand alone |
| Numbered "01 / 02 / 03" labels on sections, features or cards | Implies an order that is not there | Number only real ordered steps, as plain numerals |
| Title Case in headings, buttons and labels | Reads as a template | Sentence case everywhere except proper nouns |
| More than two font weights | Weight variety flattens the hierarchy it is meant to create | Two weights, for example 400 for body and 600 for headings and buttons |
| Overused fonts: Inter, Roboto, Arial, system font stacks, Space Grotesk | The fonts every generated page already uses | A display and body pairing chosen for this brief |
| Cream or off-white page backgrounds | The generated "warm editorial" default | White `#FFFFFF`, black `#000000`, or the brief's background |
| Italic accent words inside headlines | A styling trick that fakes emphasis | A plain headline; emphasis from word choice |
| Pill-shaped buttons | The fully rounded default button of generated UI | One radius token shared by buttons and inputs, for example 6 px |
| The same choices as the last generation | Converging on one look across runs is itself the tell | Vary composition and typography within the active style source |

The Default Quality Bar in `SKILL.md` checks every row before delivery, and step 7 checks the rendered screenshots against the table.

## Variation

With an explicit brief, vary between light and dark themes, different fonts, and different aesthetics as requested; without one, vary composition and typography while staying within the default palette and the ban table.

## Matching complexity to the vision

Match implementation complexity to the aesthetic vision. Maximalist designs need elaborate code with extensive layout and type work, plus the effects their brief asks for. Minimalist or refined designs need restraint, precision, and careful attention to spacing, typography, and subtle details. Quality comes from executing the vision well.
