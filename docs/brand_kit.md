# Agent Skills Brand Kit

## Logo

The Agent Skills logo represents modular, interlocking skill blocks that extend AI agent capabilities. The abstract "S" shape is formed by two connected blocks with a flow connector, symbolizing how skills plug into and enhance AI workflows.

### Logo Files

```
assets/logo/
├── logo-full.svg      # Mark + wordmark (horizontal)
├── logo-mark.svg      # Symbol only
├── logo-wordmark.svg  # Text only
├── logo-icon.svg      # App icon (square, dark bg)
├── favicon.svg        # 16x16 optimized
├── logo-white.svg     # For dark backgrounds
└── logo-black.svg     # Monochrome version
```

### Usage Guidelines

- Use `logo-full.svg` for headers, READMEs, and documentation
- Use `logo-mark.svg` when space is limited or alongside other text
- Use `logo-icon.svg` for app icons and social media avatars
- Use `logo-white.svg` on dark backgrounds
- Use `logo-black.svg` for monochrome/print applications

## Colors

| Name | Hex | Usage |
|------|-----|-------|
| Black | `#000000` | Primary text, dark backgrounds |
| White | `#FFFFFF` | Light backgrounds, reversed text |
| Green | `#22C55E` | Connector elements, secondary accent |
| Neon Green | `#39FF14` | Primary brand accent, highlights |

### Tailwind Config

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        brand: {
          black: '#000000',
          white: '#FFFFFF',
          green: '#22C55E',
          neon: '#39FF14',
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
  --brand-white: #FFFFFF;
  --brand-green: #22C55E;
  --brand-neon: #39FF14;
}
```

## Typography

- **Primary**: System UI stack (`system-ui, -apple-system, 'Segoe UI', sans-serif`)
- **Weight**: Bold (700) for logo, Medium (500) for headings, Regular (400) for body
- **Style**: Clean, technical, developer-focused

## Design Principles

1. **Minimalist** - Clean lines, strong geometry, no gradients
2. **Technical** - Developer/hacker aesthetic with terminal vibes
3. **High Contrast** - Black and neon green for maximum visibility
4. **Modular** - The logo itself represents extensibility and plugins
