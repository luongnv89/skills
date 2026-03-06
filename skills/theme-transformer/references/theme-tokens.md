# Theme Tokens Reference — Futuristic Cyberpunk Dark

Use this reference when proposing or implementing the transformation.

## 1) Base palette (default)

- `bg-950`: `#030B1F`
- `bg-900`: `#071633`
- `surface-800`: `#0A1F45`
- `surface-700`: `#102B5A`
- `line-500`: `#1F5EFF`
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

## 2) Mapping rules

When user provides custom accent colors:
- Keep base dark tokens (`bg/surface/text`) unless user explicitly asks to change.
- Map user color to `primary-500`.
- Generate:
  - `primary-400` = lighter/hover variant
  - glow variant = alpha tint of primary

If user provides two accent colors:
- Use first for primary actions.
- Use second for secondary highlights/charts.

## 3) Component token mapping

- Primary button: `primary-500` + optional gradient glow
- Secondary button: dark fill + `line-500` border
- Card/panel: `surface-800` with subtle neon border
- Input focus: neon ring around dark input surface
- Links/highlights: `accent-cyan-400`

## 4) Motion defaults

- Micro interactions: `120-180ms`, ease-out
- Panel transitions: `220-280ms`
- Glow pulse: low amplitude, only for critical indicators

## 5) Accessibility baseline

- Keep body text >= 4.5:1 contrast against dark backgrounds.
- Do not encode status with color only.
- Preserve visible focus rings for keyboard users.
