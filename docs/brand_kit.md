# Agent Skills Brand Kit

## Logo

The Agent Skills logo is built around the **Keyed Slot** concept: a chamfered skill memory card seated in an open agent ring, together forming the universal power-on symbol — *Plug in. Power up.* Inspired by The Matrix: Tank loads a program, Neo opens his eyes — "I know kung fu." A skill plugs in and the agent is instantly capable; the keyed cut in the ring (parallel to the card, uniform clearance) says the fit is engineered, not decorative.

### Logo Files

Files on disk under `assets/logo/` (verified 2026-09-27):

```
assets/logo/
├── logo-full.svg        # Mark + wordmark (horizontal lockup, light backgrounds)
├── logo-mark.svg        # Symbol only — canonical source of truth
├── logo-wordmark.svg    # Outlined caps wordmark
├── logo-icon.svg        # App icon (512, ink tile + phosphor card)
├── favicon.svg          # 16px redraw: tile + ring + card, contacts dropped
├── logo-white.svg       # Full lockup, all white (dark backgrounds)
├── logo-black.svg       # Full lockup, all black (mono/print)
└── brand-showcase.html  # Brand identity showcase page
```

Root README uses `assets/logo/logo-icon.svg` (`README.md:2`). The GitHub Pages site serves byte-identical copies of all eight files from `docs/assets/logo/`, so the showcase is live at https://luongnv89.github.io/skills/assets/logo/brand-showcase.html. Re-copy them whenever `assets/logo/` changes.

### Usage Guidelines

- Use `logo-full.svg` on light backgrounds; `logo-white.svg` on dark
- Use `logo-icon.svg` for square avatars, the README, and the docs nav
- Use `favicon.svg` for browser tabs
- Use `logo-black.svg` for monochrome/print applications
- Use `logo-mark.svg` when the name is already present nearby
- Minimum sizes: mark 24px tall (use `favicon.svg` below that); full lockup 120px wide
- Clear space: at least the card width (about ¼ of mark height) on all sides

Don'ts:

- Don't recolor the ring
- Don't put `#00FF41` on light backgrounds — use Phosphor Deep `#008F11`
- Don't separate, rotate, or re-space the card and ring
- No effects — the phosphor glow is only for the showcase hero
- Don't retype the wordmark as live text; it is outlined in every SVG

## Colors

| Name | Hex | Role |
|------|-----|------|
| Ink | `#0A0A0A` | Ring & wordmark on light; page background |
| Surface | `#111111` | Dark cards, elevated panels |
| Border | `#262626` | Hairlines, dark card borders |
| Muted | `#A3A3A3` | Secondary text, captions |
| Paper | `#FAFAFA` | Light surfaces; ring on dark |
| Phosphor | `#00FF41` | The card on dark — powered-on signal, Matrix code green |
| Phosphor Deep | `#008F11` | The card on light — `#00FF41` is too weak there |

### Tailwind Config

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        brand: {
          ink: '#0A0A0A',
          surface: '#111111',
          border: '#262626',
          muted: '#A3A3A3',
          paper: '#FAFAFA',
          phosphor: '#00FF41',
          'phosphor-deep': '#008F11',
        }
      }
    }
  }
}
```

### CSS Variables

```css
:root {
  --brand-ink: #0A0A0A;
  --brand-surface: #111111;
  --brand-border: #262626;
  --brand-muted: #A3A3A3;
  --brand-paper: #FAFAFA;
  --brand-phosphor: #00FF41;
  --brand-phosphor-deep: #008F11;
}
```

## Typography

- **Wordmark**: Instrument Sans Medium (500), all caps, +0.16em tracking — converted to outlines in every SVG
- **UI**: Instrument Sans 400–700
- **Code**: IBM Plex Mono

Both are OFL-licensed Google Fonts.

## Design Principles

1. **One idea** — Card + ring = the power-on symbol; plug in, power up
2. **Engineered fit** — 3.25-unit clearance, softened r=1 cut corners and r=0.75 chamfer corners
3. **Color as signal** — green only ever appears on the card
4. **Scales to 16px** — the favicon drops the contacts and adds a tile
5. **High contrast** — Ink/Paper 18.97:1, Phosphor/Ink 14.50:1, Phosphor Deep/Paper 4.08:1 (WCAG relative luminance)

The GitHub Pages landing page (`docs/index.html`) uses these tokens directly. Phosphor appears there only as a signal (the mark's card, status dots, eyebrow labels, focus rings), never as a button fill or body text.
