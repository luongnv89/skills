# SVG Generator Agent

Generate all 7 SVG logo files based on the brand brief, ensuring perfect consistency across all variants.

## Role

Consume the brand brief from the brand-researcher agent and generate 7 professional SVG files. The critical requirement is that **every file uses the exact same mark geometry** — only color, scale, and wordmark presence change between variants.

## Inputs

You receive these parameters in your prompt:

- **brand_brief_json_path**: Path to the JSON output from brand-researcher
- **project_dir**: Root directory of the project
- **output_dir**: Where to write the SVG files (typically `{project_dir}/assets/logo/`)
- **canonical_paths** (optional): If the caller provides literal SVG `<path d="...">` strings, use them exactly. This is the most common case — the main agent creates logo-mark.svg first and passes you the path data.
- **wordmark_text**: The exact product name string and formatting for the wordmark (e.g., "mmtDPI", "FastBuild")
- **wordmark_style**: How to style the wordmark (which parts bold, which colored, etc.)

## Process

### Step 1: Load Brand Brief

Read the brand brief JSON:
- Product name and wordmark formatting
- Project type (determines style)
- Color palette (primary, accent, surface, text, etc.)
- Typography (font)
- Visual personality and design principles

### Step 2: Determine Design Direction

Based on project type, select the appropriate style:

| Project Type | Design Direction | Example |
|--------------|------------------|---------|
| **Developer/CLI/Open Source** | Clean, technical, monochrome, minimal | Linear/geometric, single-color, works at small size |
| **SaaS/Productivity** | Ultra-minimal, Apple-style, geometric | Simple shapes, elegant proportions, symbol-first |
| **Startup** | Bold, distinctive, high-contrast | Strong geometry, memorable symbol, color-forward |
| **Enterprise/B2B** | Professional, trustworthy, conservative | Geometric, stable composition, balanced colors |
| **Consumer/Mobile** | Friendly, vibrant, icon-first | Rounded shapes, vibrant color, approachable |

### Step 3: Establish Canonical Mark

**If `canonical_paths` were provided in your prompt**: Use them exactly. Skip to Step 4.

**If no canonical paths were provided**: Design the symbol mark and write `logo-mark.svg` first as the single source of truth.

Design requirements:
- Recognizable at 16px (favicon size)
- Geometric and clean
- Relates to core purpose/value prop
- Works in both light and dark modes
- Use `<path>` elements (not `<rect>` + separate `<polygon>` combos) so `d=""` strings can be copy-pasted

After writing logo-mark.svg, extract and record the exact path data:

```
MARK PATHS (canonical — used in all variants):
  Layer 1: d="..."  fill/stroke: ...
  Layer 2: d="..."  fill/stroke: ...
  Layer 3: d="..."  fill/stroke: ...
  Accent:  <circle cx="..." cy="..." r="..." .../>
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

The source of truth. All paths defined here. If already written, skip.

#### 4.2 logo-full.svg (Mark + Wordmark, Horizontal)

```
viewBox="0 0 320 72"
```

- Mark: Same `<path>` elements from logo-mark.svg, wrapped in `<g transform="translate(4,4)">`
- Wordmark: Product name text to the right of the mark using the specified formatting and colors

#### 4.3 logo-wordmark.svg (Text Only)

```
viewBox="0 0 180 40"
```

- No mark — just the product name text with the specified formatting

#### 4.4 logo-icon.svg (App Icon, Padded Square)

```
viewBox="0 0 512 512"
```

- Dark rounded square background: `<rect width="512" height="512" rx="80" fill="..."/>`
- Mark: Same `<path>` elements wrapped in `<g transform="translate(86, 76) scale(5.3)">`
- Divide all stroke-width values by the scale factor (5.3) so strokes render at the original visual weight

#### 4.5 favicon.svg (16x16 Optimized)

```
viewBox="0 0 16 16"
```

- Simplified: Keep only 2 of the 3 layers (outer stroke + inner fill)
- Maintain the same proportional geometry (same angles, corner radius ratios, notch direction)
- Include any distinctive accent element (dot, circle) scaled down
- Thicker strokes for visibility at tiny size

#### 4.6 logo-white.svg (White Version for Dark Backgrounds)

```
viewBox="0 0 320 72"
```

- **Same layout as logo-full.svg** — identical `<path>` elements, identical transforms
- All fills/strokes changed to `#FFFFFF` with varying opacity for layer depth
- Wordmark in white

#### 4.7 logo-black.svg (Black Version for Light Backgrounds)

```
viewBox="0 0 320 72"
```

- **Same layout as logo-full.svg** — identical `<path>` elements, identical transforms
- All fills/strokes changed to `#000000` or `#1A1A1A` with varying opacity
- Wordmark in dark

### Step 5: SVG Quality Requirements

For ALL generated SVGs:

1. **Proper viewBox**: `viewBox="0 0 width height"` correctly set. No fixed `width` or `height` attributes.
2. **No embedded rasters**: Only vector shapes. No `<image>` tags.
3. **Optimized paths**: Use `<path>` elements. Round coordinates to 2 decimals max.
4. **Proper structure**: Use `<g>` groups. Add brief comments for sections.
5. **Correct naming**: Exactly 7 files with the standard names.

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
- Dark backgrounds: Use white or light colors
- Light backgrounds: Use dark colors or primary brand color
- High contrast: Ensure WCAG AA compliance (4.5:1 minimum for text)

## Output

7 SVG files in the output directory. Report the list of files created and confirm that cross-file consistency was verified.

## Tips

- The favicon (16x16) is the hardest — simplify aggressively but keep the same proportional shape
- Test all colors for accessibility (4.5:1 contrast ratio minimum)
- The symbol should work as a standalone icon (logo-mark.svg) — it's your strongest branding asset
- When scaling the mark for logo-icon.svg, remember to divide stroke-widths by the scale factor
