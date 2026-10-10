# Design direction and polish

How this skill applies `frontend-design` (Step 3 and Step 4) and
`emil-design-eng` (Step 6) to static App Store assets, plus the fallback rules
used when either skill is unavailable.

## Two surfaces, two rule sets

| Surface | Follows | Why |
| --- | --- | --- |
| **Marketing canvas**: background, captions, callouts, device frame, creative layout | `frontend-design`: Design Thinking, Default Quality Bar, contrast check, its Avoid list | This is the designed part; it should look intentional, not templated |
| **On-device UI**: everything inside the device screen | The app itself: its tint, system font (SF Pro), its real controls and copy | Guideline 2.3 accuracy outranks style: a pill button or a system font the app really uses stays |

## Applying frontend-design

- **Purpose and audience are known.** The purpose is an App Store listing and
  the audience is App Store shoppers, so skip frontend-design's question about them.
- **The app's brand is the explicit brief.** Accent colors, fonts and logo
  from the app brief replace frontend-design's default black/white/gray/green
  palette. Say so in one line in the plan so it does not read as a skill violation.
- **Approval gate.** The single Step 3 question satisfies frontend-design's
  approval step. A pre-authorized run satisfies it with the one-line direction.
- **Repo sync.** This skill syncs once in its own preflight; skip
  frontend-design's sync section.
- **Report.** Fold frontend-design's Final Report fields into this skill's
  final report; do not print two reports.
- **Contrast.** `render.py` checks every caption pair derived from the brand
  tokens, including the `dark*` tokens when a frame is dark: headlines are large
  text (3:1), supporting lines need 4.5:1. Pick tokens that pass on both canvas stops.

## Direction options

Offer two or three, each in the app's palette:

| Direction | Canvas | Best for |
| --- | --- | --- |
| Editorial light | Cool blue-gray gradient (never cream), ink headline, brand-colored accent line. frontend-design's Avoid list flags off-white canvases, so use it only when the user picks it | Apps with light UI; calm, premium |
| Bold brand | Every frame `dark: true`: brand-color gradient from the `dark*` tokens, light captions | Standing out in search; apps with a strong brand color |
| Alternating | `dark: true` on every other frame | Rhythm across the carousel |

Pick a **caption face** with character that suits the brand (fetch it with
`fetch_font.py`); avoid Inter, Roboto, Arial and Space Grotesk on the canvas.
Keep one face for headline and supporting line unless the brand already pairs two.

## Static polish checklist

Use this when `emil-design-eng` is unavailable, and as the scope for its
review when it is available. Each row is a check on the rendered contact sheets.

| Check | Pass when |
| --- | --- |
| Layered depth | Device and callouts use two stacked shadows (a wide soft one plus a tight contact one), tinted toward the brand hue, never pure black |
| Hairlines | Borders are 1 px at 6–10 % ink opacity; separators inside UI are 0.5 pt |
| Radii | One radius family: device corner, callout (≈ 22 px), screen cards (≈ 26 pt); no mixed sharp and round corners |
| Optical alignment | Headline centered on the device's center line; callout centered to the stage; nothing 1–2 px off |
| Caption rhythm | Same headline size, line height and top offset on every frame of a class |
| Breathing room | At least 24 px between the caption block and the device at 440 px stage width |
| Focal point | The key UI sits in the middle third; nothing important under a callout or the Dynamic Island |
| Restraint | One accent color on the canvas; decorative motifs only on wide stages |

## emil-design-eng slice

Its `SKILL.md` is mostly animation guidance and opens with an
**Initial Response** section that tells the agent to reply with a canned line
and wait. Tell the worker to **ignore that section**. Hand it only these
sections: *Core Philosophy* (taste, unseen details, beauty is leverage),
*Review Format (Required)*, and *The Sonner Principles* → *Cohesion matters*
and *Review your work the next day*. Its task: review the contact sheets
against the static polish checklist above and return a Before/After table, in
its required format, where every After is a change to `config.js` only: the
`css` string (which overrides `kit.css`) or a brand token. Animation advice
does not apply to static PNGs. After applying rows, re-render (Step 5).

## Creative composition

- Center the hero device; side devices sit lower and smaller, behind it.
- Headline above, centered; one line on 21:9, up to two on 3:2.
- The arc motif radiates from the hero device on wide stages only.
- For a Mac-first app, the hero is the Mac window and a phone may flank it.
- The caption names only the devices the image shows ("for iPhone and iPad"
  needs an iPad in the composition), and `kinds` lists only the placements
  the user asked for.
