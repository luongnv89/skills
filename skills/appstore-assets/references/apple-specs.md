# Apple asset specifications

Snapshot fetched **2026-10-10**. Apple revises these pages (iPhone Duo and the
creative assets arrived in 2026), so Step 2 re-fetches the sources every run
and the fetched page wins over this file.

Sources:
- Screenshots: https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications/
- Creative assets: https://developer.apple.com/help/app-store-connect/reference/app-information/creative-assets-specifications/
- Best practices: https://developer.apple.com/app-store/asset-best-practices/
- App previews (codec reference only): https://developer.apple.com/help/app-store-connect/reference/app-information/app-preview-specifications/

## Screenshot rules that apply to every class

- 1 to 10 screenshots per display class, `.png`, `.jpg` or `.jpeg`.
- No alpha channel and no transparency.
- When the UI is the same across sizes, upload only the highest required
  resolution; App Store Connect scales it down for smaller classes.
- In portrait, search results show up to the first three screenshots.

## Required classes (as of the snapshot)

| Platform | Required class | Folder |
| --- | --- | --- |
| iPhone | iPhone with Dynamic Island, medium display | `iphone-6.3/` |
| iPad (only if the app runs on iPadOS) | iPad 13-inch display | `ipad-13/` |
| Mac | Mac, 16:10 | `mac/` |

## Sizes the kit renders and the checker accepts

| Folder | Display class | Kit renders | Also accepted (portrait; landscape is the rotation) |
| --- | --- | --- | --- |
| `iphone-6.9/` | Dynamic Island, large (17/18 Pro Max, Air, 16 Plus …) | 1320 × 2868 | 1290 × 2796, 1260 × 2736 |
| `iphone-6.3/` | Dynamic Island, medium (17/18 Pro, 17, 16 …) | 1206 × 2622 | 1179 × 2556 |
| `ipad-13/` | iPad Pro (M5, M4), iPad Air 13" | 2064 × 2752 | 2048 × 2732 |
| `mac/` | Mac | 2880 × 1800 | 1280 × 800, 1440 × 900, 2560 × 1600 |

## Classes the kit does not render

Report these as out of scope instead of approximating them:

| Class | Size | Note |
| --- | --- | --- |
| iPhone Duo | 1398 × 2034 (outer), 2007 × 2853 (inner) | Required from April 2027 for apps built with the iOS 27.1 SDK or later |
| iPhone 6.5" / 6.1" / 5.5" / 4.7" | 1284 × 2778 … 750 × 1334 | Scaled from the classes above |
| iPad 11" / 12.9" / 10.5" / 9.7" | 1668 × 2420 … | Scaled from 13" |
| Apple TV | 1920 × 1080, 3840 × 2160 | Required for tvOS apps |
| Apple Vision Pro | 3840 × 2160 | Required for visionOS apps |
| Apple Watch | 422 × 514 … 312 × 390 | Required for watchOS apps; one size across all localizations |

## Creative assets (iOS 27 / iPadOS 27 App Store)

Creative-asset rows re-fetched **2026-10-29** from the creative assets page,
the best-practices page, the news post https://developer.apple.com/news/?id=ljpl7kyn
(October 5, 2026) and Apple's Photoshop templates (linked from best practices).

| Placement | Ratio | Size | Formats |
| --- | --- | --- | --- |
| Product page header image | 21:9 | 3840 × 1646 | .jpeg, .jpg, .png |
| Search results image | 3:2 | min 1920 × 1280, max 3840 × 2560 | .jpeg, .jpg, .png |
| Universal image (header and search) | 16:9 | 5244 × 2950 | .png only |
| **Product page header video** | 21:9 | 3840 × 1646 | .mov, .m4v, .mp4; 30 or 60 fps; 5–30 s |
| **Search results video** | 3:2 | min 1920 × 1280, max 3840 × 2560 | .mov, .m4v, .mp4; 30 or 60 fps; 5–30 s |

Apple's words: "Images can't include alpha channels or transparencies."
"Videos are muted by default in search results and can't currently be
unmuted. On your product page, videos are also muted by default, but people
can unmute them. Videos loop continuously in both placements." There is no
16:9 universal video. The kit renders the header video at 3840 × 1646 and the
search video at 3744 × 2496 (see the encoding decisions below).

Best practices (video): "Select an impactful poster frame" (the first image
before playback), "Start strong", avoid quick cuts and fast-moving visuals,
"Loop seamlessly … without visible jumps or breaks", and audio is muted by
default, so "your creative must work silently first"; sound, if any, is "brand
texture rather than information delivery". Assets go through App Store Connect
"either alongside a new app version, or in your Asset Library", and creative
assets can be used on custom product pages.

### Art safe area

Best practices says to keep key art "within the safe area defined in each
template" but states no size. The "Art Safe Area" layer in Apple's Photoshop
templates (`creative_assets-product_page_header_template-static.psd`,
`creative_assets-search_results_template-static.psd`, read 2026-10-29) is:

| Template | Canvas | Art Safe Area (x, y, w × h) |
| --- | --- | --- |
| Product page header | 3840 × 1646 | 1097, 493, 1646 × 661 (centered) |
| Search results | 3840 × 2560 | 836, 765, 2168 × 1030 (centered) |

The templates are for stills; the kit applies the same area to videos of the
same placement (assumption: the placement and its crops are the same).

### Video encoding decisions

| Question | Apple states | Kit choice |
| --- | --- | --- |
| Codec and profile | Nothing for creative videos. App previews: H.264 (up to High Profile Level 4.0) or ProRes 422 HQ; no HEVC | **Assumption:** H.264 High, 8-bit yuv420p, BT.709. Level 4.0 cannot hold 3840 px frames, so x264 picks Level 5.1 or 5.2. `check_assets.py` fails other codecs, warns on HEVC and ProRes |
| Audio track | Allowed implicitly: header audio can be unmuted, search audio never plays | **Kit rule:** render no audio track. A track in a supplied file is a WARN, never a FAIL |
| File size | Nothing for creative videos (In-App Event images: 500 MB; app previews: 500 MB) | **Assumption:** fail above 500 MB; rendered loops are a few MB |
| Constant frame rate | "30 fps or 60 fps" only | **Assumption:** CFR (frames piped at a fixed `-framerate`, encoded with `-r`), checked from packet timestamps |
| Container | .mov, .m4v or .mp4 | MP4 with `+faststart`, no metadata |
| Search video size | Any 3:2 from 1920 × 1280 to 3840 × 2560 | **Assumption:** 3744 × 2496, the largest 3:2 size within H.264 Level 5.2 (3840 × 2560 needs Level 6.0, which many hardware decoders do not support). The still stays 3840 × 2560 |
| Color | Nothing | BT.709 primaries, transfer and matrix, limited range, tagged in the stream |

## Out of scope

- **App previews** (device-recorded app footage with audio, 15–30 s, up to
  three per product page, its own spec page): not made by this skill, even
  when the user asks for "an App Store video". Header and search videos are
  creative assets, not app previews.
- **In-App Event** cards (16:9, 1920 × 1080 to 3840 × 2160) and detail pages
  (9:16), as images or 15–30 s videos.
