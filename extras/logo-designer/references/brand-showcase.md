# Brand Showcase Page (Phase 5)

After generating all SVG logos and documenting the design rationale, generate a single self-contained HTML file at `/assets/logo/brand-showcase.html` that presents the complete brand identity. This page serves as a visual reference for the team and stakeholders.

## Requirements

The showcase page must:

1. **Be fully self-contained** — load no remote font (no `<link>` or `@import` to a font URL): set the page in a system font stack (`system-ui, -apple-system, "Segoe UI", sans-serif`) and show the wordmark through its outlined SVG; inline all CSS; reference SVGs via relative paths (since they sit in the same directory)
2. **Use the project's brand colors** — apply the detected/chosen palette throughout the page (backgrounds, text, accents)
3. **Follow this section structure:**

   - **Hero section** — the brand background (`references/svg-deliverables.md`), centered logo mark (`<img src="logo-mark.svg">`), product name as heading, and the mark's idea in one sentence
   - **Design Concept** — two-column layout: left column shows an annotated version of the mark (with labels on key visual elements explaining what they represent), right column explains the design rationale in prose (why this shape, why these colors, typography reasoning)
   - **Logo Variants** — grid of cards showing each of the 7 SVG files on its intended background (`references/svg-deliverables.md` variant table):
     - `logo-full.svg` on the brand background (full width)
     - `logo-white.svg` on dark background (full width)
     - `logo-mark.svg` on the brand background
     - `logo-icon.svg` on light background
     - `logo-wordmark.svg` on the brand background
     - `favicon.svg` on dark background (shown at 64px with "16×16px" caption)
     - `logo-black.svg` on light background (full width)
     - Each card shows: a label (top-left), the SVG image, and the filename (bottom-right, monospace)
     - Next to the filename, a download link for each PNG rendered from that SVG in Phase 3b, labeled with its size (e.g. `<a href="png/logo-icon-512.png" download>PNG 512</a>` and `<a href="png/logo-icon-1024.png" download>PNG 1024</a>`). Link only PNGs that exist: when no rasterizer was found, show the SVG filename alone, so the page has no broken links
   - **Color Palette** — grid of color chips, each showing: colored swatch with hex code overlay, color name, and role description
   - **Typography** — `logo-wordmark.svg` as the specimen, with the font family, the weight and the font's licence written beside it
   - **Developer Reference** — Tailwind config as a syntax-highlighted code block, plus a file tree listing all 7 SVG files and the `png/` exports with descriptions
   - **Footer** — product name, "Brand Identity", creator/company name

4. **Design quality guidelines** for the HTML page:
   - System font stack for all page text, no remote font
   - Responsive grid layout (2 columns → 1 column on mobile)
   - Flat cards: a 1px border in the palette's Border color, no shadow on any card
   - No hover movement on cards (no `transform` or `translateY` on `:hover`)
   - Section headings in sentence case, in the Text color, at body size or larger; no small, uppercase, letter-spaced labels
   - Monospace font for filenames and code blocks
   - `max-width: 1100px` container
   - One spacing scale, an aligned grid, no placeholder text or broken images
   - Every `brief.bans` entry holds; a default ban is lifted only when `brief.lifted_bans` names it (`references/design-principles.md`, *AI-default bans*)

5. **Reference SVGs via relative `src` paths** (e.g., `<img src="logo-full.svg">`), not inline SVG, the hero mark included.

6. **Check the written page against the bans** before opening it: search the HTML for `box-shadow`, `text-shadow`, `filter`, `drop-shadow`, `linear-gradient`, `radial-gradient`, a `:hover` rule with `transform`, `text-transform: uppercase`, `letter-spacing`, a `<link` or `@import` to an `http` URL, and each `brief.bans` rule. Remove every hit that no `brief.lifted_bans` entry covers, then cite the result on the Final Report's `Evidence:` line.

7. **Open the file in the browser** after generating: `open /path/to/brand-showcase.html` (macOS) or equivalent.

8. **Screenshot it and look (Gate 3).** A grep finds banned CSS, not a glow baked into an SVG, a clipped grid or a broken image. Take the 1440 px and 390 px screenshots in `references/render-inspect.md` (*Gate 3*), view both, and check them against its ban list before the Final Report says `COMPLETE`.

## Phase 4 Documentation Outputs

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
   - Propose the confirmed decisions (mark idea, layer count, corner radius, wordmark weight) as lines for `brand_kit.md` or the project's design-rules file, for the user to accept; the skill writes a line only on the user's explicit reply (`references/design-principles.md`, *Design-rules file*)
   - Add logo to README
   - Update favicon in HTML/framework config
