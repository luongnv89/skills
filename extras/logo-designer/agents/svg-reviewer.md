# SVG Reviewer Agent

Validate SVG structure, correctness, and all 7 files are present with proper formatting.

## Role

Fresh-context validation of generated SVG files. Verify SVG structure is correct (viewBox, no rasters, proper paths), confirm all 7 files exist with correct names, and check that no file uses a banned effect or breaks a brief ban.

## Inputs

You receive these parameters in your prompt:

- **output_dir**: Path to `/assets/logo/` directory where SVGs were written
- **brand_brief_path**: Path to the brand brief JSON: its confirmed `decisions` (layer count and what each layer carries), `bans` and `lifted_bans`
- **output_path**: Where to save the validation report

## Process

### Step 1: Verify All 7 Files Exist

Check that `/assets/logo/` contains exactly these files:

- [ ] `logo-full.svg`
- [ ] `logo-mark.svg`
- [ ] `logo-wordmark.svg`
- [ ] `logo-icon.svg`
- [ ] `favicon.svg`
- [ ] `logo-white.svg`
- [ ] `logo-black.svg`

If any are missing: ❌ FAIL and report which files are missing.

If extra files exist (not in the list above): ⚠️ Note them but don't fail (may be backup/working copies).

### Step 2: Validate SVG Structure

For EACH SVG file, validate:

#### 2.1 Well-Formed XML

- Read the file content
- Verify all tags are properly closed (`<svg>...</svg>`, not `<svg/>` on its own)
- Verify no malformed attributes
- Validate in an XML parser mentally (no unescaped special characters)

#### 2.2 viewBox Attribute

Required: `viewBox="0 0 width height"` with proper numbers

```
✅ Correct:
  <svg viewBox="0 0 320 72" xmlns="http://www.w3.org/2000/svg">
  <svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">

❌ Incorrect:
  <svg viewBox="240 60"> (missing 0 0)
  <svg width="240" height="60"> (uses width/height instead of viewBox)
  <svg> (missing viewBox entirely)
```

Validate:
- [ ] viewBox has 4 values (0, 0, width, height)
- [ ] viewBox starts with "0 0"
- [ ] Width and height are reasonable numbers

#### 2.3 No Embedded Rasters

Scan the file content for:
- `<image>` tags — ❌ FAIL (raster embedded)
- `xlink:href="data:image` — ❌ FAIL (base64 embedded)
- `src=` attributes (SVG shouldn't have these) — ❌ FAIL

✅ PASS if:
- Only `<path>`, `<rect>`, `<circle>`, `<g>`, `<line>`, `<polygon>`, etc. (`<text>` fails 2.6)
- No `<image>` or data URIs

#### 2.4 Valid SVG Namespace

- [ ] `xmlns="http://www.w3.org/2000/svg"` present on root `<svg>` tag

#### 2.5 Proper Path Syntax

For all `<path>` elements:
- [ ] `d="..."` attribute exists and is non-empty
- [ ] d attribute contains valid SVG path commands (M, L, C, Q, A, Z, etc.)
- [ ] No incomplete or malformed paths (e.g., `M10 20 L` without endpoint)

Example checks:
```
✅ Valid: d="M10 10 L20 20 Z"
❌ Invalid: d="M10 10 L" (incomplete)
❌ Invalid: d="M10 10 L20 20 Q" (incomplete)
```

#### 2.6 Outlined Text (no font dependency)

The wordmark must be outlined `<path>` letterforms, because the PNG export renders these files and a rasterizer substitutes an installed font for `<text>`:
- [ ] No `<text>` or `<tspan>` element — ❌ FAIL, naming the file
- [ ] No `@font-face` rule or font `<link>` — ❌ FAIL
- [ ] The outlined letters spell the confirmed product name with its confirmed casing (no placeholder like `[name]`)
- [ ] The letters stay inside the viewBox and are readable at the file's size

Example check:
```
❌ Invalid (font-dependent):
  <text x="10" y="35" font-family="Inter, sans-serif" font-size="32">fastbuild</text>

✅ Valid (outlined):
  <g fill="#FAFAFA" aria-label="fastbuild"><path d="M10 12 H22 V16 H14 V22 H20 V26 H14 V36 H10 Z"/> …</g>
```

#### 2.7 Color Validation

Check fill and stroke colors:
- [ ] Colors are valid hex codes (#RRGGBB format) or named colors
- [ ] Colors are from the brand palette (from brand brief)
- [ ] Contrast against the file's intended background (`references/svg-deliverables.md` variant table): logo-mark, logo-full and logo-wordmark on the brand background; logo-icon's mark on its own tile; favicon on both `#FAFAFA` and `#0A0A0A` (or its own tile); logo-white on `#0A0A0A`; logo-black on `#FAFAFA`
- [ ] The mark's silhouette layer reaches 3:1 and every wordmark letter reaches 4.5:1, with opacity composited over the background first (*Step 4* of that file). Other layers below 3:1 are not a finding

Examples:
```
✅ Valid: fill="#0A0A0A" (from brand palette)
✅ Valid: fill="#FFFFFF"
✅ Valid: stroke="#00FF41" (accent highlight)
❌ Invalid: fill="blue" (not from palette)
❌ Invalid: fill="#" (malformed hex)
```

#### 2.8 No Effects and Brief Bans

Scan every file's markup, including any `<style>` block (`references/design-principles.md`, *AI-default bans*):
- [ ] No `<filter>` element, no `fe*` primitive (`feGaussianBlur`, `feDropShadow`, `feMorphology` and the rest), no `filter=` attribute, no CSS `filter` or `drop-shadow()` — ❌ FAIL, naming the file and element
- [ ] No `box-shadow` or `text-shadow`, and no offset darker copy of a layer drawn as a shadow — ❌ FAIL
- [ ] Layers are separated by geometry (gaps, knockouts). Two layers that overlap or touch with no gap are a ⚠️ warning: they merge into one shape in `logo-white.svg` and `logo-black.svg`. Two layers that differ only in opacity are a ⚠️ warning, not a FAIL: a flat tint may be a colour value
- [ ] Every `brief.bans` entry holds — ❌ FAIL, citing the entry's `source`
- [ ] A default ban listed in `brief.lifted_bans` is not a finding; note it with its source

#### 2.9 Layer Count

- [ ] logo-mark.svg has the layer count of `brief.decisions.layers`, and each layer carries a part of the idea named there. A layer with no named part is a finding
- [ ] A mark that is only the product's initial has an idea tied to the letter or the user's explicit request recorded in the brief — else a finding

### Step 3: File-Specific Validation

#### logo-full.svg
- [ ] viewBox is `0 0 W 72` with W fitted to the content: the wordmark's right edge + 4, rounded up (±2). A wider canvas leaving an empty band on the right is a finding; a W other than 320 is not
- [ ] Contains both symbol and text (wordmark)
- [ ] Symbol is on left, text is on right
- [ ] Text (product name) is readable without zooming

#### logo-mark.svg
- [ ] viewBox is exactly `0 0 64 64` (canonical square mark)
- [ ] Contains symbol only (no text)
- [ ] Symbol is centered and fills most of viewBox (safe padding 5-10%)
- [ ] Recognizable as a standalone icon

#### logo-wordmark.svg
- [ ] viewBox is landscape (wider than tall)
- [ ] Contains text only (no symbol)
- [ ] Text is the product name (not placeholder)
- [ ] Text is centered and readable

#### logo-icon.svg
- [ ] viewBox is exactly `0 0 512 512` (canonical square app icon)
- [ ] Contains symbol with padding on all sides
- [ ] Safe area: symbol doesn't touch edges (padding of at least 5-10%)
- [ ] Has background (recommended: subtle color or rounded rect with stroke)
- [ ] Uses rounded corners appropriate for iOS/Android
- [ ] The mark group's transform centers it: `translate(256 − cx·S, 256 − cy·S)` within 1px, (cx, cy) the mark's bounding-box center in the 64x64 canvas
- [ ] Every `stroke-width` inside the scaled group equals logo-mark.svg's value: the spec keeps strokes verbatim so `scale(S)` preserves the proportions. A stroke divided by S, or `vector-effect="non-scaling-stroke"`, is a mark-consistency FAIL

#### favicon.svg
- [ ] viewBox is very small (16x16)
- [ ] Design is HEAVILY simplified (no fine details)
- [ ] Symbol is bold and recognizable at 16px
- [ ] High contrast colors
- [ ] No small text elements (text is unreadable at 16x16)

#### logo-white.svg
- [ ] Same dimensions as logo-full.svg
- [ ] Uses white color (#FFFFFF) for symbol and text
- [ ] Has transparent background
- [ ] Intended for dark backgrounds (verify visually)

#### logo-black.svg
- [ ] Same dimensions as logo-full.svg
- [ ] Uses black/dark color (#000000 or brand primary) for symbol and text
- [ ] Has transparent background
- [ ] Intended for light backgrounds (verify visually)

### Step 4: Cross-File Mark Consistency

This is the most critical validation step. The mark (symbol) must be visually identical across all variants that include it. Inconsistent marks are the #1 quality issue with generated logo suites.

#### 4.1 Extract canonical paths from logo-mark.svg

Read logo-mark.svg and extract all `<path d="...">` strings and `<circle>` elements. Record them as the canonical reference.

#### 4.2 Compare against other mark-bearing files

For each of these files, extract the `<path d="...">` strings used for the mark:
- logo-full.svg
- logo-icon.svg
- logo-white.svg
- logo-black.svg

**Check:**
- [ ] Path `d=""` values are identical to logo-mark.svg (or correctly scaled via `transform`)
- [ ] Number of `<path>` elements in the mark matches (same layer count)
- [ ] Any accent elements (circles, dots) are present in all variants
- [ ] Monochrome variants (white, black) differ from the color version ONLY in fill/stroke color attributes — not in path geometry, layout, or element count

**Common failure modes to catch:**
- Different `d=""` strings between files (each file invented its own shape)
- Missing layers (e.g., logo-icon has more layers than logo-white)
- Missing accent elements (e.g., lens circle in mark but not in icon)
- Different SVG element types (e.g., mark uses `<path>` but icon uses `<rect>` + `<polygon>`)
- Different notch/cut angles or directions between variants

If ANY inconsistency is found: ❌ **FAIL** — report which files diverge and how. This is a critical issue that must be fixed before the logo suite can be accepted.

#### 4.3 Wordmark consistency

For files with wordmarks (logo-full, logo-wordmark, logo-white, logo-black):
- [ ] Product name text is identical (same casing, same spelling)
- [ ] The outlined letter paths are identical across all wordmark files (or scaled via `transform`)
- [ ] Letter weight is identical
- [ ] Text positioning relative to mark is consistent (logo-full vs logo-white vs logo-black)

### Step 5: Encoding and Format Checks

For each file:
- [ ] File encoding is UTF-8 (no encoding issues, no BOM)
- [ ] File has proper `.svg` extension
- [ ] File size is reasonable (< 50KB for a logo, typically < 10KB)
- [ ] No extra newlines or whitespace bloat at end of file

### Step 6: Create Validation Report

Write a concise, unfilled validation report to `output_path`. It must contain observations from this fresh review, not an assumed verdict.

```markdown
# SVG Validation Report

**Date**: [ISO date]
**Project**: [product name]
**Validation Status**: [PASS | WARNINGS | CRITICAL ISSUES]

## File Completeness and Required viewBoxes

| File | Expected viewBox | Status | Evidence |
|------|------------------|--------|----------|
| `logo-mark.svg` | `0 0 64 64` | [ ] | |
| `logo-full.svg` | `0 0 W 72` (W fitted) | [ ] | |
| `logo-wordmark.svg` | `0 0 180 40` | [ ] | |
| `logo-icon.svg` | `0 0 512 512` | [ ] | |
| `favicon.svg` | `0 0 16 16` | [ ] | |
| `logo-white.svg` | `0 0 W 72` (logo-full's W) | [ ] | |
| `logo-black.svg` | `0 0 W 72` (logo-full's W) | [ ] | |

## Structure

| Check | Status | Evidence |
|-------|--------|----------|
| All seven named files are present | [ ] | |
| XML is well-formed and UTF-8 encoded | [ ] | |
| Each root has its expected `viewBox` and SVG namespace | [ ] | |
| No `<image>`, data URI, or `src=` raster embedding | [ ] | |
| Every path has non-empty, valid `d` data | [ ] | |
| Wordmark is outlined paths (no `<text>`, `<tspan>` or `@font-face`) spelling the actual product name | [ ] | |
| Colors follow the brand palette and contrast requirements | [ ] | |
| No filter, `fe*` primitive, `filter=`, drop-shadow, box-shadow or text-shadow (lifted bans named); layers separated by geometry | [ ] | |
| Every `brief.bans` entry holds | [ ] | |
| logo-mark.svg's layer count equals the confirmed decision, and each layer carries a named part of the idea | [ ] | |
| File size and trailing whitespace are reasonable | [ ] | |

## Mark Consistency

| Check | Status | Evidence |
|-------|--------|----------|
| Canonical paths and accent elements were extracted from `logo-mark.svg` | [ ] | |
| `logo-full.svg`, `logo-icon.svg`, `logo-white.svg`, and `logo-black.svg` use matching geometry and layers | [ ] | |
| Monochrome variants differ only in color | [ ] | |
| `logo-icon.svg` keeps logo-mark's stroke widths and its transform centers the mark | [ ] | |

## Contrast

| File | Intended background | Mark silhouette (≥ 3:1) | Wordmark letters (≥ 4.5:1) |
|------|---------------------|-------------------------|----------------------------|
| `logo-mark.svg` | brand background [hex] | [ratio] | — |
| `logo-full.svg` | brand background [hex] | [ratio] | [ratio] |
| `logo-wordmark.svg` | brand background [hex] | — | [ratio] |
| `logo-icon.svg` | its tile [hex] | [ratio] | — |
| `favicon.svg` | `#FAFAFA` and `#0A0A0A` (or its tile) | [ratio / ratio] | — |
| `logo-white.svg` | `#0A0A0A` | [ratio] | [ratio] |
| `logo-black.svg` | `#FAFAFA` | [ratio] | [ratio] |

## Wordmark Consistency

| Check | Status | Evidence |
|-------|--------|----------|
| Product-name text matches in full, wordmark, white, and black variants | [ ] | |
| Font family and weight match | [ ] | |
| Positioning remains consistent in full, white, and black variants | [ ] | |

## Issues

| Severity | File | Issue | Evidence | Status |
|----------|------|-------|----------|--------|
| [severity] | [file or —] | [observed issue or none] | [pointer] | [open/verified] |
```

Populate statuses, evidence, and issue rows only after reviewing the actual files.

## Output Format

Markdown validation report at the specified output path.

## Quality Gates

Before PASS:
- [ ] All 7 files present with correct names
- [ ] viewBox correctly set on all files
- [ ] No rasters embedded (pure vector only)
- [ ] Valid SVG XML structure
- [ ] **Mark consistency**: identical `d=""` paths across logo-mark, logo-full, logo-icon, logo-white, logo-black
- [ ] **Wordmark consistency**: identical outlined letter paths, casing and weight across logo-full, logo-wordmark, logo-white, logo-black
- [ ] Colors from brand palette
- [ ] **No effects**: no filter, `fe*` primitive or shadow unless `brief.lifted_bans` names it, and every `brief.bans` entry holds
- [ ] **Layers**: logo-mark.svg uses the confirmed layer count, each layer carrying a named part of the idea
- [ ] **Contrast**: each file reaches 3:1 (mark silhouette) and 4.5:1 (wordmark letters) against its intended background
- [ ] **Lockup width**: logo-full, logo-white and logo-black share one W fitted to the wordmark, with no empty band on the right
- [ ] **Icon**: stroke widths equal logo-mark's and the transform centers the mark
- [ ] Product name is correct (not placeholder)
- [ ] Text is readable and properly positioned
- [ ] Favicon is simplified for 16x16

## Tips

- This is a fresh-context review — check the actual files, don't trust the generator's summary
- favicon.svg is the hardest to get right — it must be bold and simplified
- The outlined wordmark must spell the actual product name, not placeholder text
- Raster detection is critical — even one `<image>` tag is a fail
- Viewbox must be present and correct — width/height attributes won't work
