---
name: logo-designer
description: Design professional, modern logos with automatic project context detection. Use when users ask to "create a logo", "design a logo", "generate brand identity", "make a favicon", or need visual brand assets. Analyzes project files (README, package.json, etc.) to understand product name, purpose, and existing brand colors before generating logo concepts.
effort: medium
license: MIT
metadata:
  version: 1.2.0
  creator: Luong NGUYEN <luongnv89@gmail.com>
---

## Environment Check

Before running this skill, verify:
- [ ] You're in a project directory with a README or package.json
- [ ] You have write access to create `/assets/logo/` directory
- [ ] The project directory is a git repository (optional, but recommended)

If any check fails, the skill will stop and ask for clarification.

## Subagent Architecture

This skill uses an **Explorer+Executor (A) + Review Loop (C)** architecture:

```
Phase 1: Brand Research
  ↓ (brand-researcher agent)
  ↓
Phase 2-3: SVG Generation (Interactive Style Selection)
  ↓ Main agent: interactive style selection with user
  ↓
Phase 3: Generate All 7 SVGs
  ↓ (svg-generator agent)
  ↓
Phase 4: SVG Validation
  ↓ (svg-reviewer agent)
  ↓
Final Output: 7 SVG files in /assets/logo/ + brand-showcase.html + Design Rationale
```

**Agents**:
1. `agents/brand-researcher.md` — Reads project files, produces structured brand brief
2. `agents/svg-generator.md` — Generates all 7 SVG files (mark, wordmark, full, icon, favicon, white, black)
3. `agents/svg-reviewer.md` — Validates SVG structure (viewBox, no rasters, all files present, correct names)

**Key Insight**: 7 SVG files generated inline is the single biggest context cost. Brand research across multiple project files adds to the burden. The reviewer acts as a quality gate to catch SVG structure issues before files are committed.

---

# Logo Designer

Design modern, professional logos by analyzing project context and generating SVG-based brand assets.

## Repo Sync Before Edits (mandatory)
Before creating/updating/deleting files in an existing repository, sync the current branch with remote:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If the working tree is not clean, stash first, sync, then restore:

```bash
git stash push -u -m "pre-sync"
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin && git pull --rebase origin "$branch"
git stash pop
```

If `origin` is missing, pull is unavailable, or rebase/stash conflicts occur, stop and ask the user before continuing.

## Workflow

### Phase 1: Project Analysis

Automatically analyze the current project to understand brand context:

1. **Detect product identity** - Check these files in order:
   - `README.md` - Product name, description, tagline
   - `package.json` - Name, description, keywords
   - `pyproject.toml` - Project name and description
   - `Cargo.toml` - Package name and description
   - `go.mod` - Module name

2. **Find existing brand assets** - Search for:
   - `/docs/brand_kit.md`, `/.docs/brand_kit.md`, `brand_kit.md`
   - `/docs/prd.md`, `prd.md` - Product requirements with brand info
   - `/assets/logo/`, `/public/logo`, `/static/logo` - Existing logos
   - Tailwind config for existing color palette

3. **Identify project type** from codebase structure:
   - Developer/CLI/Open Source - `.github/`, CLI entry points, MIT license
   - SaaS/Productivity - Web app structure, auth, dashboard patterns
   - Startup - Lean structure, MVP patterns
   - Enterprise/B2B - Complex architecture, integrations
   - Consumer/Mobile - React Native, Flutter, mobile-first patterns

4. **Summarize findings** before proceeding:
   ```
   Product: [name]
   Type: [Developer Tool / SaaS / Startup / Enterprise / Consumer]
   Purpose: [1-sentence description]
   Audience: [target users]
   Existing colors: [hex codes if found, or "None detected"]
   Assets found: [list or "None"]
   ```

### Phase 2: Logo Design

Generate logo based on project type and context.

#### Style Selection (auto-select based on project type)

| Project Type | Style | Examples |
|--------------|-------|----------|
| Developer/CLI/Open Source | Clean, technical, monochrome | GitHub, Linear, Vercel |
| SaaS/Productivity | Ultra-minimal, Apple-style | Notion, Stripe, Figma |
| Startup | Bold, distinctive, high-contrast | YC-style companies |
| Enterprise/B2B | Professional, trustworthy | Salesforce, IBM |
| Consumer/Mobile | Friendly, vibrant, icon-first | Instagram, Spotify |

#### Design Principles

**Visual:**
- Minimalist, clean, strong geometry
- Abstract symbol or monogram related to core purpose
- Works at all sizes (16px favicon to hero banner)
- Flat or semi-flat design — no fill gradients. Use cards, lines, borders, and box shadows for visual depth.

**Colors:**
- Use detected brand colors if available, OR user-provided palette
- If neither exists, apply the **Default Style Guide** below
- High contrast, WCAG AA compliant (4.5:1 minimum)
- Always provide light, dark, and transparent versions

**Default Style Guide** (used when user provides no style preference):
- **Palette**: Dark base with neon green accent — Background (`#0A0A0A`), Surface (`#111111`), Border (`#262626`), Muted text (`#A1A1A1`), Text (`#FAFAFA`), and Neon Green (`#00FF41`)
- **Aesthetic**: Elegant, clear, clean, and professional
- **Neon Green constraint**: Reserved for highlights only (text, borders, lines, CTAs) — never as a background fill
- **System status colors**: Danger (`#EF4444`), Warning (`#F59E0B`), Info (`#3B82F6`) may only be applied to text elements, never to backgrounds or primary UI components

**Typography:**
- Modern sans-serif (Inter, system-ui, sans-serif as default; or match detected fonts)
- Medium to Bold weight
- Confident and readable at small sizes

**Product name formatting:** Ask the user how they want the product name styled in the wordmark (e.g., all-caps "FASTBUILD", camelCase "fastBuild", lowercase "fastbuild"). Do not assume the README casing is the wordmark casing — the user may prefer a different stylization for the logo. If the user specifies a format, use it consistently across all wordmark-bearing variants (logo-full, logo-wordmark, logo-white, logo-black).

### Phase 3: Deliverables

#### Critical: Canonical mark → derive all variants

Every logo variant must use the **exact same mark geometry**. The svg-generator agent (or any parallel generation) must not invent shapes independently per file — this produces inconsistent marks across variants. The workflow below prevents this.

#### Step 1: Create the canonical mark (logo-mark.svg)

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

#### Step 2: Derive all variants from the canonical paths

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

#### Step 3: Verify consistency

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

**SVG Requirements:**
- Vector-style, crisp edges
- No embedded rasters
- Optimized paths — use `<path>` elements, not `<rect>` + separate `<polygon>` combos
- viewBox properly set
- All marks use `<path>` with the canonical `d` strings (scaled via `transform` where needed)

### Phase 4: Documentation

After generating logos, provide:

1. **Design Rationale**
   - Why these colors were chosen
   - Symbol meaning and connection to product
   - Typography choice reasoning

2. **Color Specification**
   ```
   Primary: #HEXCODE
   Surface: #HEXCODE (cards, elevated elements)
   Border: #HEXCODE
   Muted: #HEXCODE (secondary text)
   Text: #HEXCODE
   Accent/Highlight: #HEXCODE (for borders, lines, highlight text, CTAs)
   Background Light: #FAFAFA
   Background Dark: #0A0A0A
   ```

3. **Tailwind Config Addition**
   ```js
   colors: {
     brand: {
       primary: '#HEXCODE',
       surface: '#HEXCODE',
       border: '#HEXCODE',
       muted: '#HEXCODE',
       accent: '#HEXCODE',
     }
   }
   ```

4. **Next Steps**
   - Create or update `brand_kit.md`
   - Add logo to README
   - Update favicon in HTML/framework config

### Phase 5: Brand Showcase Page

After generating all SVG logos and documenting the design rationale, generate a single self-contained HTML file at `/assets/logo/brand-showcase.html` that presents the complete brand identity. This page serves as a visual reference for the team and stakeholders.

The showcase page must:

1. **Be fully self-contained** — embed Google Fonts via `<link>`, inline all CSS, reference SVGs via relative paths (since they sit in the same directory)
2. **Use the project's brand colors** — apply the detected/chosen palette throughout the page (backgrounds, text, accents)
3. **Follow this section structure:**

   - **Hero section** — dark background, centered logo mark (inline SVG), product name as heading, "Brand Identity" label, and design concept tagline
   - **Design Concept** — two-column layout: left column shows an annotated version of the mark (with labels on key visual elements explaining what they represent), right column explains the design rationale in prose (why this shape, why these colors, typography reasoning)
   - **Logo Variants** — grid of cards showing each of the 7 SVG files on appropriate backgrounds:
     - `logo-full.svg` on light background (full width)
     - `logo-white.svg` on dark background (full width)
     - `logo-mark.svg` on dark background
     - `logo-icon.svg` on light background
     - `logo-wordmark.svg` on light background
     - `favicon.svg` on dark background (shown at 64px with "16×16px" caption)
     - `logo-black.svg` on light background (full width)
     - Each card shows: a label (top-left), the SVG image, and the filename (bottom-right, monospace)
   - **Color Palette** — grid of color chips, each showing: colored swatch with hex code overlay, color name, and role description
   - **Typography** — specimen block showing the font at different weights (Bold for headings, Regular for body) with sample text
   - **Developer Reference** — Tailwind config as a syntax-highlighted code block, plus a file tree listing all 7 SVG files with descriptions
   - **Footer** — product name, "Brand Identity", creator/company name

4. **Design quality guidelines** for the HTML page:
   - Inter font via Google Fonts (with system fallbacks)
   - Responsive grid layout (2 columns → 1 column on mobile)
   - Subtle shadows on light cards, no shadows on dark cards
   - Hover effect on logo cards (slight translateY)
   - Section labels: small, uppercase, letter-spaced, accent-colored
   - Monospace font for filenames and code blocks
   - `max-width: 1100px` container

5. **Reference SVGs via relative `src` paths** (e.g., `<img src="logo-full.svg">`), not inline SVG — except for the hero mark which should be inline for the glow/filter effect.

6. **Open the file in the browser** after generating: `open /path/to/brand-showcase.html` (macOS) or equivalent.

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

### Phase-specific checks

**Phase 1 — Analysis**
```
◆ Analysis (step 1 of 4 — [project name])
··································································
  Product identity detected:  √ pass ([name and purpose found])
  Brand colors found:         √ pass ([hex codes]) | × fail — using defaults
  Project type identified:    √ pass ([Developer/SaaS/Startup/etc.])
  ____________________________
  Result:                     PASS | FAIL | PARTIAL
```

**Phase 2 — Design**
```
◆ Design (step 2 of 4 — [project name])
··································································
  Style selected:             √ pass ([aesthetic direction])
  Typography chosen:          √ pass ([font name and weight])
  SVG valid:                  √ pass | × fail — [validation errors]
  ____________________________
  Result:                     PASS | FAIL | PARTIAL
```

**Phase 3 — Deliverables**
```
◆ Deliverables (step 3 of 4 — [project name])
··································································
  7 variants generated:       √ pass | × fail — [missing files]
  Files written:              √ pass (/assets/logo/ populated)
  ____________________________
  Result:                     PASS | FAIL | PARTIAL
```

**Phase 4 — Documentation**
```
◆ Documentation (step 4 of 4 — [project name])
··································································
  Rationale documented:       √ pass | × fail — [missing sections]
  Colors specified:           √ pass ([N] hex codes documented)
  Showcase created:           √ pass (brand-showcase.html written)
  ____________________________
  Result:                     PASS | FAIL | PARTIAL
```

## Example Output

For a CLI tool called "fastbuild":

```
## Analysis Summary
Product: fastbuild
Type: Developer/CLI Tool
Purpose: Fast incremental build system for large codebases
Audience: Software developers, DevOps engineers
Existing colors: None detected
Assets found: None

## Design Rationale
- **Symbol**: Abstract "F" formed by stacked horizontal bars suggesting speed and layered builds
- **Colors**: Default style guide — dark base with Neon Green highlight on the speed bars
- **Typography**: Inter for clean, modern readability

## Colors
Primary: #0A0A0A
Surface: #111111
Border: #262626
Muted: #A1A1A1
Text: #FAFAFA
Accent: #00FF41 (highlights only — borders, lines, CTAs)
Background Light: #FAFAFA
Background Dark: #0A0A0A
```

## Notes

- Always show logo previews on both light (#FAFAFA) and dark (#0A0A0A) backgrounds
- Ask the user how they want the product name formatted in the wordmark before generating — do not assume README casing
- If no project context is found, ask the user for: product name, type, and purpose
- Prefer simplicity — a logo should be recognizable at 16x16 pixels
- **Consistency is non-negotiable**: every variant must be visually recognizable as the same logo. The mark shape, number of layers, and accent elements must match across all files. The only things that change between variants are: color (monochrome), scale (favicon, icon), and presence of wordmark. If you cannot verify that paths match, the deliverable is incomplete.
