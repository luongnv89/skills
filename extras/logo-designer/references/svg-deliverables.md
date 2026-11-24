# SVG Deliverables — Variant Specifications and Derivation Rules

This reference covers Phase 3 of the logo-designer workflow: how to derive 7 consistent SVG variants from a single canonical mark.

## Critical: Canonical mark → derive all variants

Every logo variant must use the **exact same mark geometry**. The svg-generator agent (or any parallel generation) must not invent shapes independently per file — this produces inconsistent marks across variants. The workflow below prevents this.

## Step 1: Create the canonical mark (logo-mark.svg)

Generate `logo-mark.svg` first — this is the **single source of truth** for the mark's geometry. Use a `viewBox="0 0 64 64"` base canvas. Design the mark using `<path>` elements so the exact `d=""` attribute strings can be copy-pasted into every other variant.

Use the fewest layers that carry the idea, and separate them by geometry (gaps, overlaps, knockouts), never by a filter, shadow or opacity steps (`references/design-principles.md`, *Fewest layers* and *AI-default bans*). The depth lives in these paths, so every variant inherits it.

After creating `logo-mark.svg`, extract and record the exact path data, with the part of the idea each layer carries. For example:

```
MARK PATHS (canonical — copy these exactly into all other variants):
  Layer 1 (carries: the unchanged build): d="M8,30 H48 V56 H8 Z"
  Layer 2 (carries: the changed part moving forward): d="M16,8 H56 V26 H16 Z"
  (plus an accent element only if the idea needs one)
```

These exact strings must be reused verbatim in every subsequent file.

## Step 2: Derive all variants from the canonical paths

Generate the remaining 6 files. If using the svg-generator agent, its prompt **must include the literal `d=""` path strings** from Step 1. Do not describe the shape in words — paste the actual path data.

**When prompting the svg-generator agent, include:**
1. The exact `<path d="...">` elements from logo-mark.svg (copy-paste, not paraphrase)
2. The exact fill/stroke/opacity values for each layer
3. The exact wordmark text and formatting (casing, font, weight, colors), plus the literal `<path>` letterforms from `references/wordmark-outlining.md`
4. The target viewBox and any transform/scale needed
5. The brand background (below), as `brand_background`

**Variant specifications:**

| File | viewBox | Mark treatment | Wordmark | Intended background |
|------|---------|----------------|----------|---------------------|
| `logo-mark.svg` | `0 0 64 64` | The canonical paths (Step 1) | None | Brand background |
| `logo-full.svg` | `0 0 W 72` (W fitted, below) | Same paths, `translate(4,4)` to fit 72px height | Product name to the right of mark | Brand background |
| `logo-wordmark.svg` | `0 0 180 40` | None | Product name text only, centered | Brand background |
| `logo-icon.svg` | `0 0 512 512` | Same paths wrapped in `<g transform="translate(X,Y) scale(S)">`, centered in a rounded square background | None | Its own opaque tile |
| `favicon.svg` | `0 0 16 16` | Simplified: the layers that still read at 16px, with scaled-down coordinates, same proportional shape | None | Browser tabs: both `#FAFAFA` and `#0A0A0A`, unless it draws its own tile |
| `logo-white.svg` | `0 0 W 72` (same W as logo-full) | Same paths as logo-full, all fills/strokes changed to `#FFFFFF` | Same as logo-full but white text | Dark, `#0A0A0A` |
| `logo-black.svg` | `0 0 W 72` (same W as logo-full) | Same paths as logo-full, all fills/strokes changed to `#000000`/`#1A1A1A` | Same as logo-full but dark text | Light, `#FAFAFA` |

**Brand background** is the one background the brand-colored files (mark, full, wordmark) are drawn for, fixed before generation: `#0A0A0A` under the Default Style Guide (its dark base); with detected or user-given brand colors, the brand kit's page background, else `#FAFAFA`. The three files share colors, so they share this background.

**For logo-full.svg, logo-white.svg and logo-black.svg**, fit the canvas width to the content so a short name leaves no empty band:
- Keep the 72px height and the mark at `translate(4,4)`, then place the wordmark
- `W` = the wordmark's right edge + 4 (the mark's left inset), rounded up to a whole number
- logo-white and logo-black reuse logo-full's `W`
- Example: `sfm` ending at x = 152 gives `viewBox="0 0 156 72"`. A long name may go past 320

**For logo-icon.svg**, scale and center the 64x64 mark in the 512 tile:
- Target mark size ~340px: `S = 340/64 = 5.3125`
- Center: `translate(256 − cx·S, 256 − cy·S)`, where (cx, cy) is the center of the mark's bounding box in the 64x64 canvas: (32, 32) for a centered mark
- Example: `translate(86, 86) scale(5.3125)`
- Keep every `stroke-width` exactly as in logo-mark.svg. The group's `scale(S)` scales strokes with the paths, so the icon keeps the mark's stroke-to-size proportions. Never divide stroke widths by `S` (that leaves hairlines at 512px), and never add `vector-effect="non-scaling-stroke"`

**For favicon.svg**, redraw the shape at 16x16 but maintain the same proportional geometry (same angles, same corner radius ratios). Keep every layer that still reads at 16px, and drop a layer only when its detail falls under 1px there. Keep the mark's accent element (dot, circle), scaled down, when it has one.

## Step 3: Verify consistency

After all files are written, read back logo-mark.svg, logo-full.svg, logo-icon.svg, logo-white.svg, and logo-black.svg. Confirm:
- The `d=""` path values are identical (or correctly scaled via `transform`)
- The number of layers matches across all full-size variants
- Monochrome variants differ ONLY in color, not in geometry

If any file has diverged, fix it before proceeding.

## Step 4: Check contrast against each intended background

Measure every variant against its background in the table above and record each ratio:
- **Graphics, 3:1:** the mark layer that draws the silhouette (the outer outline or main fill). Other layers and accents may fall below 3:1 while that layer passes.
- **Text, 4.5:1:** every wordmark letter. Outlined letter paths still count as text.
- **logo-icon.svg:** measure the mark against the tile fill, not the page.
- **favicon.svg:** measure against both `#FAFAFA` and `#0A0A0A`, or against its tile when it draws one.
- **Opacity:** composite first, `c = a·fg + (1 − a)·bg` per channel, then measure.
- **Ratio:** `(L1 + 0.05) / (L2 + 0.05)`, L1 the lighter luminance. `L = 0.2126 R + 0.7152 G + 0.0722 B` on linearized channels: `v = c/255`, then `v/12.92` when `v ≤ 0.04045`, else `((v + 0.055)/1.055)^2.4`.

A variant below its ratio gets a darker or lighter palette color before PNG export. Never change its intended background to make it pass.

```
/assets/logo/
├── logo-mark.svg          # Symbol/icon only (CANONICAL — all others derive from this)
├── logo-full.svg          # Mark + wordmark (horizontal)
├── logo-wordmark.svg      # Text only
├── logo-icon.svg          # App icon (square, padded)
├── favicon.svg            # 16x16 simplified
├── logo-white.svg         # Full logo in white (for dark backgrounds)
├── logo-black.svg         # Full logo in black (for light backgrounds)
├── png/                   # PNG exports of every variant (references/png-export.md)
└── brand-showcase.html    # Self-contained brand identity presentation page
```

## SVG Requirements

- Vector-style, crisp edges
- No embedded rasters
- No `<text>`, `<tspan>` or `@font-face`: draw the wordmark as outlined `<path>` letterforms (`references/wordmark-outlining.md`), so the SVG and its PNG render the same without an installed font
- No `<filter>`, `fe*` primitive, `filter=` attribute, CSS `filter` or `drop-shadow()`, `box-shadow` or `text-shadow`: depth comes from layer geometry, unless the brief's `lifted_bans` names the effect
- Every `brief.bans` entry from the project's design-rules file holds
- Optimized paths — use `<path>` elements, not `<rect>` + separate `<polygon>` combos
- viewBox properly set
- All marks use `<path>` with the canonical `d` strings (scaled via `transform` where needed)
