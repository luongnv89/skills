# Agent Skills Brand Kit

## Logo

The Agent Skills logo is built around the **Neural Plug** concept: a hexagonal node representing an AI agent core, with a connector tab on the right representing a skill snapping in. Circuit spokes radiate from the center, suggesting intelligence and connectivity. The design communicates extensibility, precision, and developer-grade quality.

### Logo Files

```
assets/logo/
├── logo-full.svg      # Mark + wordmark (horizontal lockup)
├── logo-mark.svg      # Symbol only (64×64)
├── logo-wordmark.svg  # Text only
├── logo-icon.svg      # App icon (512×512, rounded square)
├── favicon.svg        # 16×16 optimized
├── logo-white.svg     # For dark backgrounds
└── logo-black.svg     # Full monochrome
```

### Usage Guidelines

- Use `logo-full.svg` for headers, READMEs, and documentation
- Use `logo-mark.svg` when space is limited or alongside other text
- Use `logo-icon.svg` for app icons and social media avatars
- Use `logo-white.svg` on dark backgrounds
- Use `logo-black.svg` for monochrome/print applications
- Minimum size: 32px height for the mark, 80px width for the full lockup

## Colors

| Name | Hex | Usage |
|------|-----|-------|
| Black | `#000000` | Hex body, primary text, dark backgrounds |
| Dark | `#0A0A0A` | App icon background |
| Surface | `#111111` / `#1A1A1A` | Hex inner panels (depth) |
| Green | `#22C55E` | Skill plug, agent core ring, "Skills" wordmark, accents |
| Green Dark | `#16A34A` | Plug prong detail, hover states |
| Gray | `#374151` | Circuit spokes, divider |
| White | `#FFFFFF` | Light backgrounds, reversed text |

### Tailwind Config

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        brand: {
          black: '#000000',
          dark: '#0A0A0A',
          green: '#22C55E',
          'green-dark': '#16A34A',
          gray: '#374151',
          white: '#FFFFFF',
        }
      }
    }
  }
}
```

### CSS Variables

```css
:root {
  --brand-black: #000000;
  --brand-dark: #0A0A0A;
  --brand-green: #22C55E;
  --brand-green-dark: #16A34A;
  --brand-gray: #374151;
  --brand-white: #FFFFFF;
}
```

## Typography

- **Primary**: System UI stack (`system-ui, -apple-system, 'Segoe UI', Helvetica, sans-serif`)
- **"Agent"**: Bold (700), letter-spacing -0.8px
- **"Skills"**: Regular (400), letter-spacing -0.4px — the weight contrast reinforces the two-part brand name
- **Style**: Clean, technical, developer-focused

## Design Principles

1. **Geometric** — Hexagon and rectangular forms, no rounded blobs or organic shapes
2. **Layered depth** — Nested hex panels create visual dimension without gradients
3. **Connector metaphor** — The plug tab is the central differentiating element of the mark
4. **Scalable** — Readable from 16px favicon to large hero usage
5. **High contrast** — WCAG AA compliant; green on black exceeds 4.5:1
