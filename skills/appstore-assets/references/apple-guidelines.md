# Apple asset guidance: rules, overclaim traps, story and captions

Distilled from Apple's App Store asset best practices and App Review
Guideline 2.3 (Accurate Metadata). Step 3 plans against this file; the
reviewer in Step 6 checks every frame against it. A **blocking** rule makes
the frame unshippable; an **advisory** rule is a quality note.

## Content rules (blocking)

| # | Rule | Check on each frame |
| --- | --- | --- |
| C1 | No specific prices, discounts, website URLs, or © symbols | Scan captions and in-screen text. A URL that is a field value inside the app's own UI is allowed only as a reserved example host (`example.com`, `server.example`) |
| C2 | No unverifiable claims: awards, rankings, "#1", "best", press quotes the app never received | Scan captions and callouts |
| C3 | No Apple recognitions: Editor's Choice, App of the Day, Apple Design Award | Scan captions and callouts |
| C4 | No logos of, or references to, other platforms or marketplaces (Android, Google Play, Windows) | Scan imagery and captions |
| C5 | Imagery fits a 4+ rating even when the app is rated higher | Sample content: no violence, profanity, drugs, sexual content, stereotypes |
| C6 | Every screen shows the app in use, and only what the shipped build does (Guideline 2.3) | The screen traces to a source view or a clean capture; see the overclaim traps |
| C7 | No placeholder or QA data on screen: "lorem", "test", "Unknown", "0.00s", debug labels, an open keyboard covering content | Read every visible string |
| C8 | Third-party brand logos appear only where the app itself shows them, at in-app size | Logos inside recreated UI: allowed; a logo enlarged as a marketing graphic: blocking |
| C9 | In-app purchases and locked content (Guideline 2.3.2: screenshots say which featured items, levels or subscriptions cost extra). Capture free content by default: the state a new player or user sees. A frame that shows paid content (an unlocked "All Chapters" list, premium items, a subscriber-only screen) says so in its caption or supporting line ("Chapter 1 is free; one purchase opens the rest"). Never show a price, a sale or a "Buy" amount, in a caption or on screen (C1) | Compare each screen with the brief's `limits` (free vs paid). Paid content shown without disclosure, or any price: blocking. Locked items drawn as locked are fine |

## Overclaim traps (blocking, Guideline 2.3)

An **overclaim** is anything the listing shows that the shipped build cannot
do. The usual sources:

- **Unentitled capabilities.** Never draw CarPlay dashboards, Apple Watch
  faces, Live Activities, widgets, HealthKit charts, or Wallet passes unless
  the project has the matching entitlement or target. Siri reached through an
  App Shortcut is not a CarPlay app; say "with Siri" or the listing's existing
  approved wording.
- **Flows the code does not support.** A Siri transcript must match a
  registered App Shortcut phrase or just show the question. A "sync across
  devices" frame needs iCloud/CloudKit in the code.
- **Copy that outruns the metadata.** A caption claim ("200+ models", "works
  offline") must already appear in, or be supported by, the description or code.
- **Claims that outrun the code's limits.** The brief's `limits` record where a
  feature stops: paid-only content, a fallback path, an exception, the real
  count. Check every caption against them. Counts must match the content a
  player can reach, saying which part is paid ("Nine dives" fails when six of
  them need a purchase and the frame does not say so). Absolutes ("every",
  "always", "never", "all") fail when the code has one exception ("Every
  critter is a step" when spikebacks cannot be stomped). A guarantee ("checked
  to be solvable") fails when a fallback path skips the check. Say the
  narrower true thing ("Stomp critters into steps").
- **Fidelity.** A recreated system surface (Siri, notifications, share sheet)
  is an approximation; the final report lists it for checking against a build.

## Quality rules (advisory)

- **Lead with the best features.** The first three frames carry the core
  promise because search shows them; sequence the rest as the story of using
  the app.
- **A full set per platform.** Aim for at least three frames on each platform
  the grounded screens support; a thinner set is fine when the app has fewer
  real screens. Never pad it with invented ones.
- **One idea per frame,** with a clear focal point inside the center of the
  composition so device crops never cut it.
- **Short text that adds to the visual.** Two-line headline, at most one
  supporting sentence. Never caption what the screen already says.
- **Legible at search size.** Headlines at the kit's layout size (about 9 % of
  the frame width), or the size its fit chose for a wide face: `render.py`
  prints `fit headline …` when it shrank one to keep two lines, down to 75 %
  (about 7 %), and that fitted size passes. WCAG contrast at least 3:1 for
  headline text and 4.5:1 for the supporting line.
- **Consistent set.** Same palette, type, device frame, and caption position on
  every frame; the creative assets reuse the same look.
- **Current UI.** Show the latest UI and a full status bar at 9:41 with full
  battery, not charging.
- **Global audience.** No region-specific idioms in captions; plan localized
  sets per language the app supports.

## Creative assets (advisory)

- **Product page header:** one clear idea for a first-time visitor; uncluttered.
- **Search results:** state the obvious; the app's purpose must be clear at a
  glance, and showing the firsthand experience (real UI) works best.
- Reuse one 16:9 universal master for both placements when the composition
  survives both crops.
- Keep text and the main subject inside the art safe area (`apple-specs.md`).
  The kit's default header places the devices outside it, as decoration that
  narrow displays crop (`render.py` prints a `note:`); that is advisory, not
  blocking, while the caption carries the message. If the user wants every
  device inside, set `creatives.layout: "safe"` (caption and one hero device).

## Header and search videos (blocking unless marked)

Rules C1–C9 and the overclaim traps apply to every beat of a video. Also:

| # | Rule | Check |
| --- | --- | --- |
| V1 | Works muted: every claim is on-screen text; no voice-over dependence, no "sound on" prompt | Read each beat's caption on the video sheet |
| V2 | Poster frame (frame 0) shows the headline complete, inside the safe area | First tile of the video sheet |
| V3 | Loops without a jump: the last frame flows into the first | Seam pair on the video sheet; `check_assets.py` seam row |
| V4 | No blank, clipped or half-faded frame on a hold | Every tile of the video sheet |
| V5 | Only grounded frames: a beat shows no screen the stills do not show | Compare beats with `config.js` frames |
| V6 | Not an app preview: no device-recorded footage, no simulated gameplay or flows the app lacks | Advisory: app previews are out of scope |

Each Custom Product Page can carry its own header; one variant per ad
creative keeps the ad's promise and the page's first image the same.

## Story and captions

Plan the frames as a sequence a first-time visitor reads left to right:

| Position | Job | Example headline (two lines) |
| --- | --- | --- |
| 1 | The core promise: what the app is, shown in use | "Every recipe you love. / In one place." |
| 2–3 | The two strongest differentiators | "Plan the week / in a tap." |
| 4–6 | Trust and depth: privacy, control, integrations | "Your data stays / on your iPhone." |
| Last | Retention: history, sync, widgets the app really has | "Pick up / where you left off." |

Caption formula: a plain benefit in line one, the accent phrase in line two
(the `<em>` span in config.js). Aim for 12–28 characters per line. Write from
the user's side ("Your keys stay on your iPhone"), not the system's ("Keychain
integration"). Supporting line: one sentence, at most about 70 characters,
adding a fact the screen cannot show.

Bad → good:
- "Settings screen with provider list" → "Your keys stay / on your iPhone." (the bad one describes the screen)
- "The #1 AI app for everyone" → "Many AI models. / One app." (the bad one is an unverifiable claim)
- "Works with CarPlay" (no CarPlay entitlement) → "Just ask Siri." with the listing's existing Siri wording in a callout
