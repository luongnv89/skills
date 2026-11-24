# SVG Generator Agent

Generate all 7 SVG logo files based on the brand brief, ensuring perfect consistency across all variants.

## Role

Consume the brand brief from the brand-researcher agent and generate 7 SVG files. The critical requirement is that **every file uses the exact same mark geometry** — only color, scale, and wordmark presence change between variants.

## Inputs

You receive these parameters in your prompt:

- **brand_brief_json_path**: Path to the JSON output from brand-researcher
- **project_dir**: Root directory of the project
- **output_dir**: Where to write the SVG files (typically `{project_dir}/assets/logo/`)
- **canonical_paths** (optional): If the caller provides literal SVG `<path d="...">` strings, use them exactly. This is the most common case — the main agent creates logo-mark.svg first and passes you the path data.
- **wordmark_text**: The exact product name string and formatting for the wordmark (e.g., "mmtDPI", "FastBuild")
- **wordmark_style**: How to style the wordmark (which parts bold, which colored, etc.)
- **wordmark_paths** (optional): The literal `<path d="...">` letterforms produced by `references/wordmark-outlining.md`. When provided, paste them unchanged into every wordmark file.
- **brand_background**: The background logo-mark, logo-full and logo-wordmark are drawn for (`references/svg-deliverables.md`, *Brand background*)

## Process

### Step 1: Load Brand Brief

Read the brand brief JSON:
- Product name and wordmark formatting
- Project type (the decision sheet's starting row)
- Color palette (primary, accent, surface, text, etc.)
- Typography (font)
- The confirmed `decisions` and `mark_idea` (written back after Phase 2)
- `bans` (from the project's design-rules file) and `lifted_bans`: obey every ban, and treat a default ban as lifted only when `lifted_bans` names it

### Step 2: Apply the Confirmed Decisions

Build from `brief.decisions`: mark type, construction, stroke, corner radius, layer count, colours and wordmark weight (the decision sheet in `references/design-principles.md`). Never reinterpret them through a style adjective. If `decisions.confirmed` is not `true`, stop and report that Phase 2 has not confirmed them.

### Step 3: Establish Canonical Mark

**If `canonical_paths` were provided in your prompt**: Use them exactly. Skip to Step 4.

**If no canonical paths were provided**: Design the symbol mark and write `logo-mark.svg` first as the single source of truth. Then stop and return its path data without writing any other variant: the main agent renders and inspects the mark (`references/render-inspect.md`, *Gate 1*) and calls you again with `canonical_paths`.

Design requirements:
- Recognizable at 16px (favicon size)
- Draws `brief.mark_idea` with the confirmed construction, stroke and corner radius
- An initial-only mark only when the brief records an idea tied to the letter or the user's explicit request (`references/design-principles.md`, *Initial-only marks*)
- The fewest layers that carry the idea, each layer carrying a named part of it
- Depth from layer geometry only: gaps and knockouts (no two layers overlap or touch without a gap), never a filter, shadow, glow or opacity steps
- Works in both light and dark modes
- Use `<path>` elements (not `<rect>` + separate `<polygon>` combos) so `d=""` strings can be copy-pasted

After writing logo-mark.svg, extract and record the exact path data:

```
MARK PATHS (canonical — used in all variants):
  Layer 1 (carries: ...): d="..."  fill/stroke: ...
  Layer N (carries: ...): d="..."  fill/stroke: ...   (one line per layer, no more than the idea needs)
  Accent (only if the mark has one): <circle cx="..." cy="..." r="..." .../>
```

### Step 4: Generate All 7 SVG Files

Every variant reuses the **exact same `d=""` path strings** from the canonical mark. The only differences between files are:

- **Color**: monochrome variants swap fills/strokes to white or black
- **Scale**: icon and favicon use `transform="scale()"` or proportionally redrawn coordinates
- **Composition**: full/white/black add a wordmark next to the mark

#### 4.1 logo-mark.svg (Symbol Only — CANONICAL)

```
viewBox="0 0 64 64"
```

The source of truth. All paths defined here, colored for `brand_background`. If already written, skip.

#### 4.2 logo-full.svg (Mark + Wordmark, Horizontal)

```
viewBox="0 0 W 72"
```

- Mark: Same `<path>` elements from logo-mark.svg, wrapped in `<g transform="translate(4,4)">`
- Width fitted to content: `W` = the wordmark's right edge + 4, rounded up, so a short name leaves no empty band (`sfm` ending at x = 152 gives `0 0 156 72`)
- Wordmark: Product name to the right of the mark using the specified formatting and colors, drawn as outlined `<path>` letterforms (no `<text>`)

#### 4.3 logo-wordmark.svg (Text Only)

```
viewBox="0 0 180 40"
```

- No mark — just the product name with the specified formatting, drawn as outlined `<path>` letterforms (no `<text>`) so the SVG and its PNG export need no installed font

#### 4.4 logo-icon.svg (App Icon, Padded Square)

```
viewBox="0 0 512 512"
```

- Dark rounded square background (the platform's app-icon tile, not part of the mark): `<rect width="512" height="512" rx="80" fill="..."/>`
- Mark: Same `<path>` elements wrapped in `<g transform="translate(86, 86) scale(5.3125)">`: `S = 340/64`, translate `256 − 32·S` on each axis for a mark centered in its 64x64 canvas (else `256 − cx·S`, `256 − cy·S` from the mark's bounding-box center)
- Keep every stroke-width value exactly as in logo-mark.svg: `scale(S)` scales strokes with the paths, so the icon keeps the mark's proportions. Never divide stroke widths by `S` and never use `vector-effect="non-scaling-stroke"`

#### 4.5 favicon.svg (16x16 Optimized)

```
viewBox="0 0 16 16"
```

- Simplified: keep every layer that still reads at 16px; drop a layer when its detail falls under 1px there
- Maintain the same proportional geometry (same angles, corner radius ratios, notch direction)
- Thicken strokes for visibility only while every gap between two elements stays at least 1 unit, edge to edge with half of each stroke width counted, with both edges on whole units (or at least 2 units off the grid). When a thicker stroke and the gap cannot both fit, drop the smaller element
- Keep the mark's accent element (dot, circle), scaled down, only when it keeps that clearance; otherwise drop it
- Recolor first; when no palette color reaches 3:1 against both `#FAFAFA` and `#0A0A0A`, draw a full-canvas rounded-square tile behind the mark in a palette color it reaches 3:1 against
- The main agent then renders and inspects the favicon (`references/render-inspect.md`, *Gate 2*)

#### 4.6 logo-white.svg (White Version for Dark Backgrounds)

```
viewBox="0 0 W 72"   (logo-full's W)
```

- **Same layout as logo-full.svg** — identical `<path>` elements, identical transforms
- All fills/strokes changed to `#FFFFFF`; the layers stay apart through the mark's gaps and knockouts, not opacity
- Wordmark in white

#### 4.7 logo-black.svg (Black Version for Light Backgrounds)

```
viewBox="0 0 W 72"   (logo-full's W)
```

- **Same layout as logo-full.svg** — identical `<path>` elements, identical transforms
- All fills/strokes changed to `#000000` or `#1A1A1A`; the layers stay apart through the mark's gaps and knockouts, not opacity
- Wordmark in dark

### Step 5: SVG Quality Requirements

For ALL generated SVGs:

1. **Proper viewBox**: `viewBox="0 0 width height"` correctly set. No fixed `width` or `height` attributes.
2. **No embedded rasters**: Only vector shapes. No `<image>` tags.
3. **Optimized paths**: Use `<path>` elements. Round coordinates to 2 decimals max.
4. **Proper structure**: Use `<g>` groups. Add brief comments for sections.
5. **Correct naming**: Exactly 7 files with the standard names.
6. **No effects, every ban**: No `<filter>`, `fe*` primitive, `filter=` attribute, CSS `filter` or `drop-shadow()`, `box-shadow` or `text-shadow`, no `<linearGradient>` or `<radialGradient>`, and no opacity steps used as depth, unless `brief.lifted_bans` names that ban. Obey every `brief.bans` entry. Check the craft, not an adjective: the mark is optically centered, layers that share a role share one stroke width, coordinates sit on the canvas grid, and the mark reads at 16px.
7. **Outlined text**: No `<text>`, `<tspan>` or `@font-face`. Use the `wordmark_paths` you were given; without them, outline the brief's font by `references/wordmark-outlining.md`. Reuse the same letter paths byte for byte in logo-full, logo-white, logo-black and logo-wordmark, changing only the wrapping group's `transform` and fill. The PNG export renders these files, and a rasterizer would substitute an installed font for `<text>`.

### Step 6: Verify Consistency

After generating all files, read back logo-mark.svg, logo-full.svg, logo-icon.svg, logo-white.svg, and logo-black.svg. Confirm:
- The `d=""` path values are **identical** (or correctly scaled via `transform`)
- The number of layers matches (same count of `<path>` and accent elements in all full-size variants)
- Monochrome variants differ **ONLY** in color attributes, not in geometry or layout

If any file has diverged, fix it immediately before reporting completion.

### Step 7: Color Application

Use colors from the brand brief:

- **Primary**: Main symbol color
- **Accent**: Highlight/secondary color if needed
- **Text**: Wordmark color

Guidelines:
- Accent colors: Reserved for highlights, borders, lines — never as background fill
- Intended backgrounds: logo-mark, logo-full and logo-wordmark on `brand_background`; logo-icon on its own tile; favicon on both `#FAFAFA` and `#0A0A0A` (or its own tile, when no palette color passes on both); logo-white on `#0A0A0A`; logo-black on `#FAFAFA`
- Contrast against that background: 3:1 for the mark's silhouette layer, 4.5:1 for every wordmark letter, opacity composited first (`references/svg-deliverables.md`, *Step 4*). Fix a failing color; never change the background. The favicon's own tile is the one exception (4.5 above)

## Output

7 SVG files in the output directory. Report the list of files created and confirm that cross-file consistency was verified.

## Tips

- The favicon (16x16) is the hardest — simplify aggressively but keep the same proportional shape, and keep every gap at least 1 whole unit after thickening
- Check each variant's contrast against its intended background: 3:1 for the mark, 4.5:1 for wordmark letters
- The symbol should work as a standalone icon (logo-mark.svg) — it's your strongest branding asset
- When scaling the mark for logo-icon.svg, keep its stroke-width values unchanged: the group's `scale(S)` scales them with the paths
