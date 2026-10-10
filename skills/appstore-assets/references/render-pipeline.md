# Render pipeline and kit API

Read this in Step 4 (building `config.js`) and Step 5 (rendering). The three
scripts live in the skill's `scripts/`; the template lives in `assets/template/`.

## Asset set layout

```
<out>/                      e.g. metadata/screenshots/<version>/ or appstore-assets/<version>/
├── src/                    copy of assets/template/ — index.html, kit.css, kit.js, config.js
│   ├── fonts/              display.woff2 + LICENSE.txt (fetch_font.py)
│   └── captures/           clean real captures, when a frame uses ui.capture()
├── iphone-6.9/ iphone-6.3/ ipad-13/ mac/   screenshots, <frame-id>.png
├── creative/               header.png, search.png, universal.png
├── sheets/                 contact sheets for review (not for upload)
└── PLAN.md                 the approved frame plan with evidence per screen
```

## Commands

```bash
SKILL=<this skill's directory>
python3 "$SKILL/scripts/fetch_font.py" "Bricolage Grotesque" <out>/src
python3 "$SKILL/scripts/render.py" <out>/src                 # all frames, all classes, creatives
python3 "$SKILL/scripts/render.py" <out>/src --only 02-siri   # re-render one frame or creative kind
python3 "$SKILL/scripts/check_assets.py" <out> --platforms iphone,ipad --sheet <out>/sheets
python3 "$SKILL/scripts/render.py" --preflight                # tools only: Pillow + Chrome
```

For several languages, render one asset set per locale (`<out>/<locale>/src/`);
captions are per set, so one language never overwrites another.

Inside a project with a Python venv, activate it first; both scripts need
Pillow (`python3 -m pip install pillow`). `render.py` needs Chrome or Chromium
(`--chrome PATH` or `$CHROME` to override detection).

## What render.py does and why

| Behavior | Reason |
| --- | --- |
| Refuses to run while `config.js` contains `TODO:` | Template text must never reach a PNG |
| Builds a manifest first (`index.html?manifest=1` via `--dump-dom`), rendering every screen once | A broken builder, an unknown icon name or a missing image fails with its frame id instead of shipping a blank PNG |
| Checks caption contrast from the brand tokens (3:1 headline, 4.5:1 supporting line, light and dark) | A dark frame with dark text cannot pass |
| After a full render, deletes PNGs whose frame is no longer in `config.js` | A dropped frame cannot ship by accident |
| Passes the stage height explicitly (`&h=`) | Headless Chrome's viewport is about 87 px shorter than `--window-size`; a `100vh` stage gets clipped |
| Renders `iphone-6.3` by zooming the 440 px design to 402 px | One layout serves both iPhone classes with identical proportions |
| Flattens to RGB with Pillow | Chrome writes RGBA; App Store Connect rejects alpha |
| Fails unless the pixel size is exact | A 1 px error is an upload rejection |

Device scale factors: iPhone ×3 (440 × 956 → 1320 × 2868), iPad ×2 (1032 × 1376
→ 2064 × 2752), Mac ×2 (1440 × 900 → 2880 × 1800), creatives ×2.

## Rendering environment

- On macOS, `-apple-system` resolves to SF Pro, so recreated iOS/macOS UI matches
  the system look. On Linux it falls back to another sans-serif: record
  "UI font not SF Pro" under Uncertainty.
- Keep every asset local (fonts, captures, logos). Remote URLs make renders
  slow and nondeterministic.
- Copy app logos and provider marks the UI really shows from the app's asset
  catalog into `src/` and pass them to `sym('<img src="…">')`.

## config.js shape

```js
window.APP_CONFIG = {
  app, version, platforms: ["iphone", "ipad", "mac"],      // only what the app ships
  brand: { brand, brandInk, ink, muted, canvas1, canvas2, glow,
           darkCanvas1, darkCanvas2, darkInk, darkMuted, darkAccent },   // dark* style frames with dark: true
  uiTint: "#3b86f7",                                        // the app's accent inside screens
  css: ".my-card{…}",                                       // optional styles for custom screen HTML
  fonts: { display: { file: "fonts/display.woff2", weight: "200 800" } },
  frames: [{ id, headline, sub, dark?, callout?: { icon, title, text, platforms? },
             screens: { iphone: () => html, ipad: () => html, mac: () => html } }],
  creatives: { enabled /* only when requested */, kinds: ["header", "search", "universal"],
               headline, sub, searchHeadline, searchSub,
               hero: { platform, frame }, sides: [{ platform, frame }] },
};
```

Frame ids sort in upload order (`01-…`, `02-…`). Put a `// Source: path:line`
comment above every screen builder: Step 6's reviewer checks it against the code.

## Kit API (kit.js)

| Helper | Renders |
| --- | --- |
| `ui.screen(body, {bg: "white"\|"grouped", dark, w, h})` | The screen root; pass `w: 1032, h: 1376` for iPad |
| `ui.statusBar({onDark, pad})`, `ui.homeIndicator()` | 9:41 status bar (pad = iPad style), home indicator |
| `ui.navBar({title, left, right})`, `ui.largeTitle(t)` | Inline and large navigation titles |
| `ui.section(t)`, `ui.footnote(t)` | Grouped-list header and footer text |
| `ui.list(rows, {icons})`, `ui.row({icon, iconBg, title, sub, value, accessory})` | Inset grouped list; accessory `chevron`, `check`, `toggle-on`, `toggle-off`, `none` or HTML |
| `ui.search(placeholder)`, `ui.chips(items, active)` | Search field, filter chips |
| `ui.button(label, "filled"\|"tinted"\|"plain")`, `ui.badge(text, fg, bg)` | Buttons and badges |
| `ui.messages([ui.bubble("user"\|"other", html, meta)])`, `ui.composer(placeholder)` | Chat transcript and input bar |
| `ui.tabBar([{icon, label}], active)` | Floating tab bar |
| `ui.card(html)`, `ui.stat(value, label)`, `ui.grid2(cards)` | Cards and stat tiles |
| `ui.split(sidebar, detail)`, `ui.sideItem(label, icon, on)` | iPad split view |
| `ui.capture("captures/x.png")` | A real capture filling the screen (it carries its own status bar) |
| `macui.window({title, tools, sidebar, content, dark})`, `macui.group`, `macui.item`, `macui.table` | Mac window with traffic lights, sidebar, toolbar, table |
| `sym("name")` or `sym('<img src="…">')` | Icon from the built-in set (`I` in kit.js) or raw logo markup |

For screens the primitives do not cover, write plain HTML in the builder and
put its styles in the `css:` string of `config.js`; `kit.js` injects it after
`kit.css`. Leave the marketing-canvas rules in `kit.css` untouched so every
frame keeps the same caption and device placement.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `screen builders threw errors` | The named frame calls a missing helper or has no screen for a platform listed in `creatives` |
| Captions in a system font | `fetch_font.py` was not run, or `fonts.display.file` points elsewhere |
| A blank or black device screen | The builder returned nothing, or a capture path is wrong (paths are relative to `src/`) |
| Text overlaps the device | Shorten the headline to two lines; do not move `LAYOUT` offsets per frame |
