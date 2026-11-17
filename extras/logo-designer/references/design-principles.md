# Design Principles & Default Style Guide

Use this reference during Phase 2 (Logo Design).

## Style Selection (auto-select based on project type)

| Project Type | Style | Examples |
|--------------|-------|----------|
| Developer/CLI/Open Source | Clean, technical, monochrome | GitHub, Linear, Vercel |
| SaaS/Productivity | Ultra-minimal, Apple-style | Notion, Stripe, Figma |
| Startup | Bold, distinctive, high-contrast | YC-style companies |
| Enterprise/B2B | Professional, trustworthy | Salesforce, IBM |
| Consumer/Mobile | Friendly, vibrant, icon-first | Instagram, Spotify |

## Visual

- Minimalist, clean, strong geometry
- Abstract symbol or monogram related to core purpose
- Works at all sizes (16px favicon to hero banner)
- Flat or semi-flat design — no fill gradients. Use cards, lines, borders, and box shadows for visual depth.

## Colors

- Use detected brand colors if available, OR user-provided palette
- If neither exists, apply the **Default Style Guide** below
- High contrast, WCAG AA compliant (4.5:1 minimum)
- Always provide light, dark, and transparent versions

## Default Style Guide (used when user provides no style preference)

- **Palette**: Dark base with neon green accent — Background (`#0A0A0A`), Surface (`#111111`), Border (`#262626`), Muted text (`#A1A1A1`), Text (`#FAFAFA`), and Neon Green (`#00FF41`)
- **Aesthetic**: Elegant, clear, clean, and professional
- **Neon Green constraint**: Reserved for highlights only (text, borders, lines, CTAs) — never as a background fill
- **System status colors**: Danger (`#EF4444`), Warning (`#F59E0B`), Info (`#3B82F6`) may only be applied to text elements, never to backgrounds or primary UI components

## Typography

- Modern sans-serif (Inter, system-ui, sans-serif as default; or match detected fonts)
- Medium to Bold weight
- Confident and readable at small sizes

## Product name formatting

Ask the user how they want the product name styled in the wordmark (e.g., all-caps "FASTBUILD", camelCase "fastBuild", lowercase "fastbuild"). Do not assume the README casing is the wordmark casing — the user may prefer a different stylization for the logo. If the user specifies a format, use it consistently across all wordmark-bearing variants (logo-full, logo-wordmark, logo-white, logo-black).
