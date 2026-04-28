# Brand Showcase Page (Phase 5)

After generating all SVG logos and documenting the design rationale, generate a single self-contained HTML file at `/assets/logo/brand-showcase.html` that presents the complete brand identity. This page serves as a visual reference for the team and stakeholders.

## Requirements

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
   - Create or update `brand_kit.md`
   - Add logo to README
   - Update favicon in HTML/framework config
