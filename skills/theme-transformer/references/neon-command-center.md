# Neon Command Center — Reference Style Guide

Use this as the default transformation target when user asks for futuristic/cyberpunk/dark design.

## 1) Theme identity
- Mood: futuristic, high-contrast, technical, immersive
- Visual language: dark depth + electric neon accents
- Best contexts: dashboards, devtools, data-heavy interfaces

## 2) Design principles
1. Dark-first surfaces
2. Glow as signal, not decoration
3. Strong hierarchy for dense data layouts
4. Readability before effects
5. Fast, precise motion

## 3) Token baseline

| Token | Hex | Purpose |
|---|---|---|
| bg-950 | #030B1F | Main app background |
| bg-900 | #071633 | Secondary background |
| surface-800 | #0A1F45 | Panels/cards |
| surface-700 | #102B5A | Elevated surfaces |
| line-500 | #1F5EFF | Borders/dividers |
| primary-500 | #1E7BFF | Primary action |
| primary-400 | #33A2FF | Hover/active |
| cyan-400 | #32E6FF | Accent highlights |
| success-400 | #3BFFB8 | Success state |
| warning-400 | #FFC857 | Warning state |
| danger-400 | #FF4D6D | Error state |
| text-100 | #EAF4FF | Primary text |
| text-300 | #B8D2FF | Secondary text |
| text-500 | #7CA1D9 | Tertiary text |

## 4) Typography
- Primary: Inter / SF Pro / Manrope
- Monospace: JetBrains Mono / SF Mono
- Numeric/data UI should use stronger weight and tighter hierarchy

Recommended scale:
- H1: 36/44, 700
- H2: 28/36, 700
- H3: 22/30, 600
- Body: 15/24, 400-500
- Caption: 12/18, 500

## 5) Spacing + shape system
- 4px base grid
- Common spacing: 8, 12, 16, 20, 24, 32
- Radius: 10 (controls), 16 (cards), 20 (modal)
- Borders: 1px standard, 2px emphasis

## 6) Component behavior
- Cards: dark fill + subtle neon edge + soft deep shadow
- Buttons:
  - Primary: blue-cyan glow gradient
  - Secondary: dark fill + neon border
  - Danger: deep red fill + red/pink outline
- Inputs: dark fill + clear neon focus ring

## 7) Motion
- Micro interaction: 120-180ms, ease-out
- Panel transition: 220-280ms
- Glow pulse: low amplitude, reserved for important state

## 8) Accessibility
- Body text contrast meets WCAG AA
- Never encode status by color alone
- Preserve visible focus indicators
- Support reduced motion mode

## 9) Do/Don't

Do:
- Keep layout clean and structured
- Use accent colors to guide attention
- Keep chart/table readability high

Don't:
- Over-glow everything
- Use low-contrast text on dark panels
- Introduce distracting motion loops
