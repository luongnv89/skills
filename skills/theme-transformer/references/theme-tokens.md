# Theme Tokens Reference — Futuristic Cyberpunk Dark

Use this file when proposing and implementing theme migration tokens.

## 1) Base palette (default structure)

- `bg-950`: `#030B1F`
- `bg-900`: `#071633`
- `surface-800`: `#0A1F45`
- `surface-700`: `#102B5A`
- `line-500`: `#1F5EFF`

Text tokens:
- `text-100`: `#EAF4FF`
- `text-300`: `#B8D2FF`
- `text-500`: `#7CA1D9`

Accent defaults:
- `primary-500`: `#1E7BFF`
- `primary-400`: `#33A2FF`
- `accent-cyan-400`: `#32E6FF`

Semantic defaults:
- `success-400`: `#3BFFB8`
- `warning-400`: `#FFC857`
- `danger-400`: `#FF4D6D`

## 2) Accent customization rules

### Single color input
Map user color to:
- `primary-500` = user color
- `primary-400` = lighter hover variant
- `primary-glow` = alpha tint for focus/shadow

### Two-color input
- Color 1 -> primary action system (`primary-*`)
- Color 2 -> secondary highlights/charts (`accent-*`)

### Full palette input
- Respect user palette tokens exactly
- Keep fallback only for missing semantic tokens

## 3) Component token mapping

- **App background:** `bg-950`
- **Panel/card fill:** `surface-800`
- **Panel border:** `line-500` (reduced opacity)
- **Primary button:** `primary-500`
- **Primary hover:** `primary-400`
- **Input focus ring:** `primary-glow` or `accent-cyan-400`
- **Links/data highlights:** `accent-cyan-400`
- **Table dense rows:** dark neutral with clear highlighted active cells

## 4) Motion defaults

- Micro interactions: `120-180ms`, ease-out
- Panel transitions: `220-280ms`, smooth cubic-bezier
- Glow pulse: low-amplitude and only for high-priority indicators

## 5) Accessibility baseline

- Body text contrast >= 4.5:1 against dark backgrounds
- Preserve visible keyboard focus ring
- Avoid status-by-color-only design
- Keep readable fallback for all neon accent states

## 6) Verification checklist

- [ ] Accent color applied consistently to primary actions
- [ ] Contrast checks pass on key screens
- [ ] Focus state remains visible in all components
- [ ] Glow effects are restrained and purposeful
- [ ] Dashboard/table readability preserved
