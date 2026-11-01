# Input discovery: building the app brief

The explorer (Step 1) reads the source and returns the app brief defined in
`agents/app-explorer.md`. This file says where each brief field comes from.
Every field carries its evidence: a `path:line` for code, a section anchor or
quoted text for a landing page. A field without evidence is `null`, never a guess.

## Codebase input

| Brief field | Where to look | Notes |
| --- | --- | --- |
| `name`, `subtitle`, `description` | `metadata/`, `fastlane/metadata/<locale>/`, `store/` (for example `store/listing-<locale>.md`), `*.xcodeproj/project.pbxproj` (`INFOPLIST_KEY_CFBundleDisplayName`), `Info.plist`, README | Listing copy is the ceiling for caption claims |
| `version` | Flutter: `version:` in `pubspec.yaml`, without the `+build` part (`1.0.0+1` → `1.0.0`). Otherwise `MARKETING_VERSION` in `project.pbxproj`, then `Info.plist` `CFBundleShortVersionString` | Names the output folder. `$(FLUTTER_BUILD_NAME)` or `$(MARKETING_VERSION)` in `Info.plist` is a reference, not a version: follow it |
| `platforms` | See the platform table below | Evidence is the build setting line |
| `orientation` | `UISupportedInterfaceOrientations` and `UISupportedInterfaceOrientations~ipad` in `Info.plist` (or `INFOPLIST_KEY_UISupportedInterfaceOrientations_iPhone` / `_iPad` in `project.pbxproj`); Flutter `SystemChrome.setPreferredOrientations([...])` in `lib/main.dart`; SwiftUI apps that lock rotation in an `AppDelegate` | `landscape` when every supported orientation is `…Landscape…`, else `portrait`, per platform; the Dart call wins over `Info.plist` because it runs last. Sets `orientation` in `config.js` |
| `limits[]` | Purchases: StoreKit product ids, `in_app_purchase`/`purchases_flutter`/RevenueCat, unlock flags and paywalls (what a free user cannot open). Fallbacks: a code path that skips a check (`_fallback`, `catch`, retry loops). Exceptions: entity types a rule excludes. Counts: the content lists (levels, chapters, dives) and which part is paid | One row per feature a caption may name, with `path:line`. The reviewer checks every caption against these |
| `listing_findings[]` | Each sentence of the listing copy (`store/`, `fastlane/metadata/`, `metadata/`) that the code does not support, such as a session length or a count the content does not have | Optional listing check: report it; this skill never edits the listing |
| `brand.accent` | `Assets.xcassets/AccentColor.colorset/Contents.json`, `Color("…")`/`.tint(…)` in views, brand SVGs (`brand/`, `assets/`, `docs/`) | Convert to `#rrggbb`; an empty colorset means the system blue |
| `brand.fonts` | Custom fonts in `Info.plist` `UIAppFonts`, `.font(.custom(…))` | System font if none |
| `screens[]` | SwiftUI `View` structs / UIKit view controllers under `Features/`, `Views/`, `Screens/`, `Scenes/`; Flutter widgets in `lib/`; React Native components | Pick the 5–10 screens that show the core value; record the file and the strings, colors and controls they render, in order |
| `claims[]` | Listing description bullets, README feature list | Each claim maps to the code that implements it, or is marked unsupported |
| `sensitive[]` | `*.entitlements`, `Info.plist` keys, extension targets, App Intents | See the sensitive-features table |
| `captures[]` | `docs/screenshots/`, `fastlane/screenshots/`, `screenshots/`, `store/screenshots/`, `metadata/` | Record size and the cleanliness verdict below |
| `existing_sets[]` | See "Existing asset sets" below | An existing kit set selects the Update branch |

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

## Existing asset sets

Earlier runs leave sets under different names (`appstore-assets/1.0/`,
`appstore-assets/1.0.0/`, `store/screenshots/`, `metadata/screenshots/<v>/`),
sometimes with `src/` in one folder and the PNGs in another (rendered with
`--out`). Find every kit set by its config, and every rendered set by its class
folders:

```bash
grep -rl --include=config.js "APP_CONFIG" . --exclude-dir={node_modules,build,.dart_tool,Pods,.git,DerivedData}
find . \( -name iphone-6.9 -o -name iphone-6.3 -o -name ipad-13 \) -type d -not -path "*/node_modules/*" -not -path "*/build/*"
```

Record each as `{"src": "…/src", "out": "…", "version": "…"}`; `out` is the
folder holding the class folders (the parent of `src/` unless `PLAN.md` or the
class folders say otherwise). A kit set for the same version, under any
spelling (`1.0` and `1.0.0` are the same version), means the Update branch with
that `out`, never a second folder. Rendered PNGs with no `src/` are an older,
hand-made set: list them as captures, and back the folder up before writing
into it.

## Capture recipes

Clean captures beat recreated screens, so capture the real app when the
project can run. Each run used to invent its own harness; use these instead.

**Where captures live.** Write them straight to `<out>/src/captures/`
(`<screen>-iphone.png`, `<screen>-ipad.png`) and keep them in git: a re-render
needs them, and a gitignored folder forced one run to recapture 14 screens.
Check with `git check-ignore -v <out>/src/captures/x.png`; if a rule matches,
report it and ask before editing `.gitignore`. Put a harness the project wants
to keep under `tool/` (Flutter) or `<out>/src/capture/`, never under `test/`,
where it would join the app's test suite.

**Sizes.** Capture at the kit's device screen so a capture fills it exactly:
iPhone 402 × 874 pt at @3x (1206 × 2622 px), iPad 1032 × 1376 pt at @2x
(2064 × 2752 px); landscape swaps them. Safe-area insets in points: iPhone
portrait top 62, bottom 34; iPhone landscape left and right 62, bottom 21;
iPad bottom 20, top 24 (0 when the app hides the status bar).

**Flutter.** A `flutter test` harness renders real widgets with no simulator:

- `tester.view.physicalSize = const Size(1206, 2622)`, `devicePixelRatio = 3`,
  and `padding` and `viewPadding` set to the insets above (× the ratio) with
  `FakeViewPadding`; `addTearDown(tester.view.reset)`.
- Load the real fonts first (`FontLoader` over the app's font assets, plus
  `MaterialIcons`), or every glyph renders as a test-font box.
- `MaterialApp(debugShowCheckedModeBanner: false, …)`; no network images.
- Freeze time: build the screen under `withClock(Clock.fixed(DateTime(2026, 1, 13, 9, 41)), …)`
  when the app reads `clock.now()` (package `clock`), or pass a fixed date to the
  widget; a postmark or a "today" label must never show the capture date. If the
  app calls `DateTime.now()` directly, say so in `PLAN.md` and choose a frame
  where no date shows.
- Pump fixed durations (`tester.pump(const Duration(milliseconds: 90))`), never
  `pumpAndSettle` on an endless animation; wrap the app in a `RepaintBoundary`
  and save `boundary.toImage(pixelRatio: 3)` as PNG inside `tester.runAsync`.
- A web build (`flutter build web -t <capture main>` opened in headless Chrome)
  works too, but Flutter web reports no safe area: inject the insets through
  `MediaQuery`. Size the viewport over CDP, not with `--window-size`: from
  Chrome 156 headless clamps `--window-size` to a 500 px minimum width, so a
  402 × 874 `--screenshot` comes out 500 × 787 and clipped on the right. Use
  `Emulation.setDeviceMetricsOverride` (`width: 402, height: 874,
  deviceScaleFactor: 3, mobile: false`, as `render.py`'s video path does), then
  `Page.captureScreenshot`; check the PNG is exactly 1206 × 2622 before using it.
  One batch run measured a 0.02 % difference from a known-good capture.

**Simulator.** Record the state before changing it and restore it after, even
when the run stops early:

```bash
dev=<udid>; xcrun simctl spawn "$dev" defaults read -g AppleLocale > /tmp/aa-sim-locale.txt
xcrun simctl spawn "$dev" defaults read -g AppleLanguages > /tmp/aa-sim-languages.txt
xcrun simctl status_bar "$dev" override --time "2026-01-13T09:41:00" --batteryState charged \
  --batteryLevel 100 --wifiBars 3 --cellularBars 4 --dataNetwork wifi
# … capture with `xcrun simctl io "$dev" screenshot <out>/src/captures/<name>.png` …
xcrun simctl status_bar "$dev" clear
```

- An ISO date in `--time` also fixes the date the iPad status bar shows, so it
  never reads the capture day.
- Prefer per-launch language arguments over a device-wide change:
  `xcrun simctl launch "$dev" <bundle id> -AppleLanguages "(en)" -AppleLocale en_US`.
  If you did change the device locale, write the recorded values back with
  `defaults write -g` and reboot the simulator; report it if that fails.
- Uninstall a capture build you installed only for this run.

**Cleanup.** Delete scratch files you created (temporary tests, `build/`
outputs you added, `/tmp` captures) and list in the report what you deleted
and what you kept on purpose (a harness under `tool/`).

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
