# Input discovery: building the app brief

The explorer (Step 1) reads the source and returns the app brief defined in
`agents/app-explorer.md`. This file says where each brief field comes from.
Every field carries its evidence: a `path:line` for code, a section anchor or
quoted text for a landing page. A field without evidence is `null`, never a guess.

## Codebase input

| Brief field | Where to look | Notes |
| --- | --- | --- |
| `name`, `subtitle`, `description` | `metadata/`, `fastlane/metadata/<locale>/`, `*.xcodeproj/project.pbxproj` (`INFOPLIST_KEY_CFBundleDisplayName`), `Info.plist`, README | Listing copy is the ceiling for caption claims |
| `version` | `MARKETING_VERSION` in `project.pbxproj`, `Info.plist` `CFBundleShortVersionString` | Names the output folder |
| `platforms` | See the platform table below | Evidence is the build setting line |
| `brand.accent` | `Assets.xcassets/AccentColor.colorset/Contents.json`, `Color("…")`/`.tint(…)` in views, brand SVGs (`brand/`, `assets/`, `docs/`) | Convert to `#rrggbb`; an empty colorset means the system blue |
| `brand.fonts` | Custom fonts in `Info.plist` `UIAppFonts`, `.font(.custom(…))` | System font if none |
| `screens[]` | SwiftUI `View` structs / UIKit view controllers under `Features/`, `Views/`, `Screens/`, `Scenes/`; Flutter widgets in `lib/`; React Native components | Pick the 5–10 screens that show the core value; record the file and the strings, colors and controls they render, in order |
| `claims[]` | Listing description bullets, README feature list | Each claim maps to the code that implements it, or is marked unsupported |
| `sensitive[]` | `*.entitlements`, `Info.plist` keys, extension targets, App Intents | See the sensitive-features table |
| `captures[]` | `docs/screenshots/`, `fastlane/screenshots/`, `screenshots/`, `metadata/` | Record size and the cleanliness verdict below |

### Platform detection

| Evidence | Platform |
| --- | --- |
| `TARGETED_DEVICE_FAMILY = 1;` | iPhone only |
| `TARGETED_DEVICE_FAMILY = 2;` | iPad only |
| `TARGETED_DEVICE_FAMILY = "1,2";` | iPhone and iPad |
| `SDKROOT = macosx`, a macOS target, `SUPPORTS_MACCATALYST = YES`, or `SDKROOT = auto` with `macosx` in `SUPPORTED_PLATFORMS` (multiplatform SwiftUI) | Mac, in addition to any iPhone/iPad family |
| Flutter (`pubspec.yaml` + `ios/Runner.xcodeproj`, `macos/`) or React Native (`package.json` with `react-native` + `ios/`) | Read the platforms from the `ios/` and `macos/` Xcode projects |
| `.iOS(…)` / `.macOS(…)` in `Package.swift` `platforms:` | iPhone (and iPad unless restricted) / Mac |
| `WATCHOS_DEPLOYMENT_TARGET`, `TVOS_DEPLOYMENT_TARGET`, `XROS_DEPLOYMENT_TARGET` targets | watchOS, tvOS, visionOS: out of scope, report them |
| `build.gradle`, `AndroidManifest.xml`, no Apple target at all | Not an Apple app: stop |

An iPhone-only app running on iPad in compatibility mode needs no iPad screenshots.

### Sensitive features (overclaim sources)

| Feature | Present only when |
| --- | --- |
| CarPlay app UI | `com.apple.developer.carplay-*` entitlement |
| HealthKit data | `com.apple.developer.healthkit` entitlement |
| Widgets, Live Activities | A widget extension target, `NSSupportsLiveActivities` |
| Apple Watch app | A watchOS target |
| iCloud sync | `com.apple.developer.icloud-*` entitlements, CloudKit usage |
| Siri | App Intents / `AppShortcutsProvider`; record the exact registered phrases |
| Sign in with Apple, Apple Pay, Wallet | The matching entitlement |

### Capture cleanliness

A capture is **clean** when all of these hold; otherwise record the failing reasons:

- Exact device resolution of a current class (or the same aspect ratio, at least 1170 px wide).
- Full status bar at 9:41, full battery, not charging; no debug overlays.
- No placeholder or QA strings ("test", "lorem", "Unknown", "logo review", "0.00s").
- No open keyboard unless typing is the point of the frame.
- Shows the current UI version.

## Landing-page input

Fetch the page with the `browse` skill when it is available, otherwise with
the host's web-fetch tool. For a local `.html` file, read it directly.

| Brief field | Where to look |
| --- | --- |
| `name`, `subtitle` | `<title>`, hero heading, App Store badge link text |
| `description`, `claims[]` | Hero subhead, feature sections; quote the exact text |
| `brand.accent`, `brand.fonts` | CSS custom properties, button colors, `font-family`, Google Fonts links |
| `captures[]` | `<img>` and `<picture>` sources showing app UI, device mockups, inline SVG/HTML mock screens |
| `platforms` | "Available on iPhone/iPad/Mac" text, App Store badge, device mockups shown |

Record who publishes the app (footer, App Store badge link, legal name). The
main agent confirms with the user that they publish it before building.

Without a codebase, a screen may only show what a landing-page image or mock
shows. When the page has no app UI at all, set `screens` to `[]`: Step 3 then
asks the user for simulator captures or the codebase instead of inventing UI.
