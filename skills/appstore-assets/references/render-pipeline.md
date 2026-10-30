# Render pipeline and kit API

Read this in Step 4 (building `config.js`) and Step 5 (rendering). The three
scripts live in the skill's `scripts/`; the template lives in `assets/template/`.
Header and search videos: see **Video creatives** below.

## Asset set layout

```
<out>/                      e.g. metadata/screenshots/<version>/ or appstore-assets/<version>/
├── src/                    copy of assets/template/ — index.html, kit.css, kit.js, config.js
│   ├── fonts/              display.woff2 + LICENSE.txt (fetch_font.py)
│   └── captures/           clean real captures, when a frame uses ui.capture()
├── iphone-6.9/ iphone-6.3/ ipad-13/ mac/   screenshots, <frame-id>.png
├── creative/               header.png, search.png, universal.png; header.mp4, search.mp4 when video is on
│   ├── .kit-outputs.json   ownership record: the files render.py wrote here (size and sha256) and the variant folders it created
│   └── <variant>/          the same files per Custom Product Page variant (optional)
├── sheets/                 contact sheets and video-*.png sheets for review (not for upload)
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
python3 "$SKILL/scripts/render.py" --preflight --video        # also ffmpeg (libx264) + ffprobe
python3 "$SKILL/scripts/render.py" <out>/src --no-video       # stills only while iterating
python3 "$SKILL/scripts/render.py" <out>/src --only header    # header.png and header.mp4
```

For several languages, render one asset set per locale (`<out>/<locale>/src/`);
captions are per set, so one language never overwrites another.

Inside a project with a Python venv, activate it first; both scripts need
Pillow (`python3 -m pip install pillow`). `render.py` needs Chrome or Chromium
(`--chrome PATH` or `$CHROME` to override detection). Videos also need ffmpeg
4.1 or later (for `setparams` color tags) built with libx264, and ffprobe.

## What render.py does and why

| Behavior | Reason |
| --- | --- |
| Refuses to run while `config.js` contains `TODO:` | Template text must never reach a PNG |
| Builds a manifest first (`index.html?manifest=1` via `--dump-dom`), rendering every screen once | A broken builder, an unknown icon name or a missing image fails with its frame id instead of shipping a blank PNG |
| Checks caption contrast from the brand tokens (3:1 headline, 4.5:1 supporting line, light and dark) | A dark frame with dark text cannot pass |
| After a full render, deletes outputs no longer in `config.js`: `<frame>.png` in the class folders, and in `creative/` only files `.kit-outputs.json` lists (videos only without `--no-video`) whose size and sha256 still match the record, then a variant folder it lists once that folder is empty or holds only `.DS_Store` (removed with it). A listed file changed since gets `WARN: … changed since the kit wrote it, left in place` and leaves the record; a listed variant folder holding anything else is kept with a WARN. Each write records the file's fingerprint atomically right after it lands (`--only` adds to it), so a failed render never adds a file; a file deleted by hand stays listed until the next full render clears it. With no record (a 1.0.0 set), only root `header`/`search`/`universal.png` go, as in 1.0.0. Hidden files are skipped silently; symlinks and anything else in `creative/` get `WARN: … not produced by the kit, left in place`. A file the config still produces is re-rendered over whatever is there, as in 1.0.0: to keep a hand-made asset, remove that kind from the config first; the kit will then leave it in place | A dropped frame, video or variant cannot ship by accident, and a file the kit did not write or that changed since (an App Preview recording, raw art, a hand-replaced `search.png`, `old/header.png`, an empty folder, a symlinked folder) is never deleted |
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
               hero: { platform, frame }, sides: [{ platform, frame }],
               video: { kinds: ["header", "search"], duration: 12, fps: 30, transition: 0.8, searchSize?: "max",
                        beats: [{ headline, sub, searchHeadline?, searchSub?, hero?, sides? }] },
               variants: [{ id: "tiktok-trails", kinds?, headline?, hero?, video?: { … } }] },
};
```

Frame ids sort in upload order (`01-…`, `02-…`). Put a `// Source: path:line`
comment above every screen builder: Step 6's reviewer checks it against the code.

## Video creatives

Header and search videos are the still creative in motion: `header.png` is
frame 0 of `header.mp4`, so the poster frame is the approved still.

**How it renders.** `kit.js` computes every frame as a pure function of `t`
(no CSS animation, no clock), so re-rendering a config gives the same frames
and, with the same ffmpeg build, the same bytes. `render.py` starts one
headless Chrome with `--remote-debugging-pipe` (CDP over fds 3/4, standard
library only), seeks with `window.__seek(i / fps)`, captures each frame with
`Page.captureScreenshot`, and pipes the PNGs to ffmpeg: libx264 High, CRF 18,
yuv420p, BT.709 (tagged), constant frame rate, no audio, `+faststart`. The
search video is 3744 × 2496 at 30 fps (the stage at ×1.95) and 3600 × 2400
at 60 fps (×1.875), the largest 3:2 sizes within H.264 Level 5.2 at each
rate; `render.py` passes the level to x264 explicitly (5.1 for the header at
30 fps, 5.2 otherwise, 6.0 for `searchSize: "max"`). `searchSize: "max"` in `creatives.video` renders
3840 × 2560 instead, which needs Level 6.0 and is untested with App Store
Connect. The search still stays 3840 × 2560. Open
`src/index.html?creative=header&t=3.2` in Chrome to see any moment.

Alternatives rejected: one `--screenshot` Chrome launch per frame (about a
second of startup per frame), and an ffmpeg pan/zoom/crossfade over stills
(cannot crossfade the screen inside a floating device, and a zoom that
returns to its start is a visible yo-yo).

**Timeline.** Beat 0 is the still (headline, sub, hero, sides; search uses
`searchHeadline`). Each entry in `video.beats` adds a beat built only from
existing frames. The header shows the hero and one side device, search the
hero and two. A beat holds, then crossfades (`transition`, default 0.8 s:
the caption fades out, then the next fades in; each device crossfades its
screen). The last crossfade returns to beat 0 half a second before the end,
so the loop seam falls inside beat 0's hold. Devices drift ±8 px and the arcs
breathe 2 % on one sine period over the whole video, so the last frame flows
into the first.

| Rule | Bar |
| --- | --- |
| First impression | Frame 0 shows beat 0 complete: no fade-in, the headline is readable from 0 s |
| Dwell | Each beat holds at least max(2.5 s, 1 s + words / 4) of its caption (beat 0 before the first crossfade); `render.py` fails with the needed time otherwise |
| Safe area | Caption, and for search the hero device, sit inside Apple's art safe area (`references/apple-specs.md`) |
| Timing | `duration` 5–30 s (default 12), `fps` 30 or 60, `duration × fps` a whole number |
| Loop | `check_assets.py` fails when the last→first difference exceeds twice the neighboring frame steps |

Rough budget: two beats fit 10 s, three need about 15 s. Render cost is about
0.7 s per 3840 × 1646 frame and 1.1 s per 3744 × 2496 frame on a 2-core Linux
VM (faster on Apple silicon), so render stills with `--no-video` while
iterating and render the videos last.

**Custom Product Page variants.** Each `variants[]` entry has an `id`
(lowercase, digits, hyphens) and overrides any `creatives` key; `video` merges
key by key, except `beats`, which a variant never inherits. A variant
`headline` or `sub` also replaces the base search wording unless the variant
sets `searchHeadline` or `searchSub`. It renders to `creative/<id>/` (for example one header per ad
creative). Upload each variant to its custom product page in App Store Connect.

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
| `ffmpeg and ffprobe not found` | Install ffmpeg 4.1 or later with libx264, set `FFMPEG`/`FFPROBE`, or pass `--no-video` |
| `header video: 2 beats in 5 s hold beat 0 for 1.27 s, its caption needs 3.25 s` (`<kind> video: N beats in D s hold beat i for X s, its caption needs Y s`) | Raise `video.duration` (up to 30), shorten that beat's caption, or drop a beat |
| `WARN: <path> not produced by the kit, left in place` | `render.py` keeps any file `creative/.kit-outputs.json` does not list; `check_assets.py` adds a WARN row saying not to upload it. Leave it, or move it out of `creative/` yourself |
| A file the kit rendered earlier is no longer pruned | It changed since the kit wrote it (the render printed `changed since the kit wrote it`), or `.kit-outputs.json` was deleted, edited by hand or unreadable (`WARN: … is unreadable`); delete the stale file yourself if it is not wanted, and the next render rebuilds the record |
| Chrome stops answering during a video | Pass `--chrome` with Chrome or Chromium 75+; on Linux, `chrome-headless-shell` works too |
