# SVG Reviewer Agent

Validate SVG structure, correctness, and all 7 files are present with proper formatting.

## Role

Fresh-context validation of generated SVG files. Verify SVG structure is correct (viewBox, no rasters, proper paths), confirm all 7 files exist with correct names, and validate visual quality.

## Inputs

You receive these parameters in your prompt:

- **output_dir**: Path to `/assets/logo/` directory where SVGs were written
- **brand_brief_path**: Path to the brand brief JSON (for reference)
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
- Only `<path>`, `<rect>`, `<circle>`, `<text>`, `<g>`, `<line>`, `<polygon>`, etc.
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

#### 2.6 Proper Text Elements

For all `<text>` elements:
- [ ] `x`, `y` attributes present
- [ ] `font-family` specified (e.g., "Inter, sans-serif")
- [ ] `font-size` specified
- [ ] Content is the product name (no Lorem Ipsum, no placeholders like `[name]`)
- [ ] Text is readable (not overflowing viewBox)

Example check:
```
❌ Invalid (placeholder):
  <text x="10" y="35" font-family="Inter" font-size="32">
    [Product Name]
  </text>

✅ Valid (actual name):
  <text x="10" y="35" font-family="Inter, sans-serif" font-size="32" fill="#FAFAFA" font-weight="600">
    fastbuild
  </text>
```

#### 2.7 Color Validation

Check fill and stroke colors:
- [ ] Colors are valid hex codes (#RRGGBB format) or named colors
- [ ] Colors are from the brand palette (from brand brief)
- [ ] High contrast with background (4.5:1 minimum for text)

Examples:
```
✅ Valid: fill="#0A0A0A" (from brand palette)
✅ Valid: fill="#FFFFFF"
✅ Valid: stroke="#00FF41" (accent highlight)
❌ Invalid: fill="blue" (not from palette)
❌ Invalid: fill="#" (malformed hex)
```

### Step 3: File-Specific Validation

#### logo-full.svg
- [ ] viewBox width >= 200 (landscape, has room for mark + text)
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
- Missing layers (e.g., logo-icon has 3 layers but logo-white has 2)
- Missing accent elements (e.g., lens circle in mark but not in icon)
- Different SVG element types (e.g., mark uses `<path>` but icon uses `<rect>` + `<polygon>`)
- Different notch/cut angles or directions between variants

If ANY inconsistency is found: ❌ **FAIL** — report which files diverge and how. This is a critical issue that must be fixed before the logo suite can be accepted.

#### 4.3 Wordmark consistency

For files with wordmarks (logo-full, logo-wordmark, logo-white, logo-black):
- [ ] Product name text is identical (same casing, same spelling)
- [ ] Font family is identical across all wordmark files
- [ ] Font weight is identical
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
| `logo-full.svg` | `0 0 320 72` | [ ] | |
| `logo-wordmark.svg` | `0 0 180 40` | [ ] | |
| `logo-icon.svg` | `0 0 512 512` | [ ] | |
| `favicon.svg` | `0 0 16 16` | [ ] | |
| `logo-white.svg` | `0 0 320 72` | [ ] | |
| `logo-black.svg` | `0 0 320 72` | [ ] | |

## Structure

| Check | Status | Evidence |
|-------|--------|----------|
| All seven named files are present | [ ] | |
| XML is well-formed and UTF-8 encoded | [ ] | |
| Each root has its expected `viewBox` and SVG namespace | [ ] | |
| No `<image>`, data URI, or `src=` raster embedding | [ ] | |
| Every path has non-empty, valid `d` data | [ ] | |
| Text elements have coordinates, font, size, and the actual product name | [ ] | |
| Colors follow the brand palette and contrast requirements | [ ] | |
| File size and trailing whitespace are reasonable | [ ] | |

## Mark Consistency

| Check | Status | Evidence |
|-------|--------|----------|
| Canonical paths and accent elements were extracted from `logo-mark.svg` | [ ] | |
| `logo-full.svg`, `logo-icon.svg`, `logo-white.svg`, and `logo-black.svg` use matching geometry and layers | [ ] | |
| Monochrome variants differ only in color | [ ] | |

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
- [ ] **Wordmark consistency**: identical text, font, weight across logo-full, logo-wordmark, logo-white, logo-black
- [ ] Colors from brand palette
- [ ] Product name is correct (not placeholder)
- [ ] Text is readable and properly positioned
- [ ] Favicon is simplified for 16x16

## Tips

- This is a fresh-context review — check the actual files, don't trust the generator's summary
- favicon.svg is the hardest to get right — it must be bold and simplified
- Text elements must have the actual product name, not placeholder text
- Raster detection is critical — even one `<image>` tag is a fail
- Viewbox must be present and correct — width/height attributes won't work
