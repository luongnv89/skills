# SVG Deliverables — Variant Specifications and Derivation Rules

This reference covers Phase 3 of the logo-designer workflow: how to derive 7 consistent SVG variants from a single canonical mark.

## Critical: Canonical mark → derive all variants

Every logo variant must use the **exact same mark geometry**. The svg-generator agent (or any parallel generation) must not invent shapes independently per file — this produces inconsistent marks across variants. The workflow below prevents this.

## Step 1: Create the canonical mark (logo-mark.svg)

Generate `logo-mark.svg` first — this is the **single source of truth** for the mark's geometry. Use a `viewBox="0 0 64 64"` base canvas. Design the mark using `<path>` elements so the exact `d=""` attribute strings can be copy-pasted into every other variant.

After creating `logo-mark.svg`, extract and record the exact path data. For example:

```
MARK PATHS (canonical — copy these exactly into all other variants):
  Layer 1: d="M10,6 H44 L56,18 V52 Q56,58 50,58 H16 Q10,58 10,52 Z"
  Layer 2: d="M14,10 H42 L52,20 V50 Q52,54 48,54 H20 Q14,54 14,50 Z"
  Layer 3: d="M18,14 H40 L48,22 V48 Q48,50 46,50 H24 Q18,50 18,48 Z"
  (plus any circles, dots, or accent elements)
```

These exact strings must be reused verbatim in every subsequent file.

## Step 2: Derive all variants from the canonical paths

Generate the remaining 6 files. If using the svg-generator agent, its prompt **must include the literal `d=""` path strings** from Step 1. Do not describe the shape in words — paste the actual path data.

**When prompting the svg-generator agent, include:**
1. The exact `<path d="...">` elements from logo-mark.svg (copy-paste, not paraphrase)
2. The exact fill/stroke/opacity values for each layer
3. The exact wordmark text and formatting (casing, font, weight, colors)
4. The target viewBox and any transform/scale needed

**Variant specifications:**

| File | viewBox | Mark treatment | Wordmark |
|------|---------|----------------|----------|
| `logo-full.svg` | `0 0 320 72` | Same paths, `translate(4,4)` to fit 72px height | Product name to the right of mark |
| `logo-wordmark.svg` | `0 0 180 40` | None | Product name text only |
| `logo-icon.svg` | `0 0 512 512` | Same paths wrapped in `<g transform="translate(X,Y) scale(S)">` to fit centered in a rounded square background | None |
| `favicon.svg` | `0 0 16 16` | Simplified: use 2 of the 3 layers (outer + inner) with scaled-down coordinates, same proportional shape | None |
| `logo-white.svg` | `0 0 320 72` | Same paths as logo-full, all fills/strokes changed to `#FFFFFF` with varying opacity | Same as logo-full but white text |
| `logo-black.svg` | `0 0 320 72` | Same paths as logo-full, all fills/strokes changed to `#000000`/`#1A1A1A` with varying opacity | Same as logo-full but dark text |

**For logo-icon.svg**, compute the scale factor from the base 64x64 mark:
- Target mark area: ~340x340 centered in 512
- Scale: `340/64 ≈ 5.3`
- Translate to center: `translate(86, 76) scale(5.3)`
- Divide stroke-width values by the scale factor so strokes render at the same visual weight

**For favicon.svg**, redraw the shape at 16x16 but maintain the same proportional geometry (same angles, same corner radius ratios). Simplify by dropping the middle layer — keep only outer (stroke) and inner (fill). Include any distinctive accent element (dot, circle) scaled down.

## Step 3: Verify consistency

After all files are written, read back logo-mark.svg, logo-full.svg, logo-icon.svg, logo-white.svg, and logo-black.svg. Confirm:
- The `d=""` path values are identical (or correctly scaled via `transform`)
- The number of layers matches across all full-size variants
- Monochrome variants differ ONLY in color, not in geometry

If any file has diverged, fix it before proceeding.

```
/assets/logo/
├── logo-mark.svg          # Symbol/icon only (CANONICAL — all others derive from this)
├── logo-full.svg          # Mark + wordmark (horizontal)
├── logo-wordmark.svg      # Text only
├── logo-icon.svg          # App icon (square, padded)
├── favicon.svg            # 16x16 simplified
├── logo-white.svg         # Full logo in white (for dark backgrounds)
├── logo-black.svg         # Full logo in black (for light backgrounds)
└── brand-showcase.html    # Self-contained brand identity presentation page
```

## SVG Requirements

- Vector-style, crisp edges
- No embedded rasters
- Optimized paths — use `<path>` elements, not `<rect>` + separate `<polygon>` combos
- viewBox properly set
- All marks use `<path>` with the canonical `d` strings (scaled via `transform` where needed)
