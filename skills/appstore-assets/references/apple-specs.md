# Apple asset specifications

Snapshot fetched **2026-10-10**. Apple revises these pages (iPhone Duo and the
creative assets arrived in 2026), so Step 2 re-fetches the sources every run
and the fetched page wins over this file.

Sources:
- Screenshots: https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications/
- Creative assets: https://developer.apple.com/help/app-store-connect/reference/app-information/creative-assets-specifications/
- Best practices: https://developer.apple.com/app-store/asset-best-practices/

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

| Placement | Ratio | Size | Formats |
| --- | --- | --- | --- |
| Product page header | 21:9 | 3840 × 1646 | .jpeg, .jpg, .png |
| Search results | 3:2 | min 1920 × 1280, max 3840 × 2560 | .jpeg, .jpg, .png |
| Universal (header and search) | 16:9 | 5244 × 2950 | .png only |

No alpha. Video versions exist (5–30 s, 30 or 60 fps, muted by default, loop)
but are out of scope for this skill. In-App Event cards (16:9, 1920 × 1080 to
3840 × 2160) and detail pages (9:16) are also out of scope.

## App previews

Up to three per product page; out of scope. Mention them as a possible
follow-up only when the user asks about video.
