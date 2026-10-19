# Apple App Store Review Guidelines — Complete Checklist

Source: https://developer.apple.com/app-store/review/guidelines/, synced to the revision marked **Last Updated: October 16, 2026**. When Apple publishes a newer revision, diff the live page against this file before relying on it.

This reference contains every checkable guideline organized by section. For each guideline, the checker should determine: PASS, FAIL, WARNING (potential issue), or N/A (not applicable to this app type).

**IDs.** IDs follow Apple's numbering. A lettered or roman sub-clause becomes a suffix (Apple's 5.1.1(v) is `5.1.1-v`, 3.1.1(a) is `3.1.1a`), and a word suffix splits one guideline into separate checks (`5.1.1-v-delete`). Apple marks these numbers "Intentionally omitted", so they have no row: 2.5.7, 2.5.10 (the empty-ad-banner rule, deleted in November 2025), 3.2.2(ii), 3.2.2(vi), 4.2.4, 4.2.5, 4.4.3, 4.6.

**SDKs count.** The developer is responsible for everything in the app, including ad networks, analytics services, and third-party SDKs, so an SDK's violation is the app's violation.

## Table of Contents

1. [Safety](#1-safety)
2. [Performance](#2-performance)
3. [Business](#3-business)
4. [Design](#4-design)
5. [Legal](#5-legal)

---

## 1. SAFETY

### 1.1 Objectionable Content

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 1.1.1 | No defamatory, discriminatory, or mean-spirited content | Review text and imagery for content targeting religion, race, sexual orientation, gender, national/ethnic origin, or other groups, especially content likely to humiliate, intimidate, or harm; professional political satire and humor is generally exempt |
| 1.1.2 | No realistic portrayals of people or animals being killed, maimed, tortured, or abused, and nothing that encourages violence | Check content, images, videos, and gameplay; game "enemies" must not solely target a specific race, culture, real government, corporation, or other real entity |
| 1.1.3 | No depictions encouraging illegal or reckless use of weapons and dangerous objects; no facilitating firearm or ammunition purchases | Look for reckless-weapon content and any flow that sells, links to, or helps buy firearms or ammunition |
| 1.1.4 | No overtly sexual or pornographic material | Check images, text, and UGC for explicit content, including AI-generated nudity and "nudification" of real people; "hookup" apps and apps that may facilitate prostitution, human trafficking, or exploitation are rejected |
| 1.1.5 | No inflammatory religious commentary or inaccurate or misleading quotations of religious texts | Review religious content for inflammatory or misquoted material |
| 1.1.6 | No false information or features, including inaccurate device data or trick/joke functionality | Check for fake capabilities (such as fake location trackers) and prank features; an "for entertainment purposes" disclaimer doesn't cure it; apps enabling anonymous or prank calls or SMS/MMS are rejected |
| 1.1.7 | No harmful concepts that capitalize or seek to profit on recent or current events | Check for exploitation of violent conflicts, terrorist attacks, epidemics, or other tragedies |

### 1.2 User-Generated Content

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 1.2 | UGC apps, including social media and AI content-creation apps, need filtering, reporting, blocking, and published contact info | If users can post, share, or generate content (including with AI): verify a content filter, a report control with timely responses, a block control, and visible contact info; Apple may treat missing safeguards, or violations left unfixed after notice, as a Developer Code of Conduct violation |
| 1.2-ncii | Moderation covers nonconsensual intimate imagery, including imagery generated with AI tools | If the app generates, edits, or hosts images or video of people: verify filtering and takedown cover nonconsensual intimate imagery, including AI output, and no feature sexualizes a real person's photo |
| 1.2-prohibited | No UGC app used primarily for pornography, Chatroulette-style or random/anonymous chat, objectifying real people ("hot-or-not"), physical threats, or bullying | Check the core feature set for these uses; incidental NSFW content from a web-based service must be hidden by default and enabled only on the website |
| 1.2.1 | Creator content is moderated as UGC, sold through 3.1.1, and labeled when it costs extra | If the app features creator content (video, articles, audio, casual games): verify 1.2 moderation applies to it, purchases follow 3.1.1, and users can tell which content needs a purchase |
| 1.2.1-a | Creator apps let users identify content above the app's age rating and restrict underage access using verified or declared age | Verify labels on over-rating creator content and an age gate based on verified or declared age |

### 1.3 Kids Category

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 1.3-a | No links out, purchasing opportunities, or other distractions except behind a parental gate | If Kids Category: verify external links, purchase prompts, and distractions sit behind a parental gate; the obligations continue in later updates even if the category is deselected |
| 1.3-b | No third-party analytics or third-party advertising | If Kids Category: verify no third-party ad or analytics SDKs; limited exceptions are analytics that collect no IDFA or identifiable info about children, their location, or devices, and contextual ads from services with published Kids Category practices that include human review of ad creatives |
| 1.3-c | No personally identifiable or device information sent to third parties | If Kids Category: verify no IDFA collection and nothing sent to third parties that identifies a child or device (names, birthdates, emails, location, device or network identifiers) |
| 1.3-d | Comply with children's privacy laws worldwide | If Kids Category: verify COPPA, GDPR, and local children's-privacy compliance (see 5.1.4) |

### 1.4 Physical Harm

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 1.4.1 | Medical apps that could give inaccurate data or be used to diagnose or treat patients get greater scrutiny | If medical/health app: verify disclosed data and methodology behind accuracy claims; no claims to take x-rays or measure blood pressure, body temperature, blood glucose, or blood oxygen with device sensors alone; a reminder to consult a doctor; any regulatory clearance linked in the review notes |
| 1.4.2 | Drug dosage calculators come from the drug manufacturer, a hospital, university, health insurer, pharmacy, or other approved entity, or have FDA (or international counterpart) approval | If dosage calculator: verify the submitting entity or the approval |
| 1.4.3 | No encouraging tobacco, vape products, illegal drugs, or excessive alcohol, and nothing encouraging minors to use them | Check content for substance-use encouragement; verify no sale of controlled substances (licensed pharmacies and licensed or legal cannabis dispensaries excepted) or tobacco |
| 1.4.4 | DUI checkpoints only as published by law enforcement; never encourage drunk driving or reckless behavior such as speeding | If driving-related: verify checkpoint sources are law-enforcement publications |
| 1.4.5 | No urging users into activities (bets, challenges) or device use that risks physical harm | Check for dares, challenges, or stunts that risk harm to users or others |

### 1.5 Developer Information

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 1.5-a | Easy contact method in the app AND in the Support URL | Verify an in-app contact path and a working support URL with current contact info (especially for classroom apps) |
| 1.5-b | Wallet passes carry valid issuer contact info and are signed with a dedicated certificate assigned to the pass's brand or trademark owner | If using Wallet: verify pass contact info and the signing certificate's owner |

### 1.6 Data Security

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 1.6 | Appropriate security measures prevent unauthorized use, disclosure, or access to user data | Verify HTTPS for API traffic, Keychain or encrypted storage for credentials and sensitive data, and no secrets in logs |

### 1.7 Reporting Criminal Activity

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 1.7 | Crime-reporting apps involve local law enforcement and ship only where that involvement is active | If crime-reporting features: verify law-enforcement involvement and storefronts limited to those regions |

---

## 2. PERFORMANCE

### 2.1 App Completeness

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 2.1-a | Final version with complete metadata and working URLs, tested on-device for bugs and stability | Verify no placeholder text or empty websites, all links resolve, no obvious crash paths, and backend services live during review; pre-order submissions count too |
| 2.1-a-demo | Demo account for login-gated features; a demo mode only when legal or security obligations rule out a demo account, and with Apple's prior approval | If the app requires login: verify demo credentials (plus any QR code or hardware needed) are in the review notes; a built-in demo mode needs that reason and prior approval and must show full functionality, else WARNING |
| 2.1-b | In-app purchases are complete, up to date, visible to the reviewer, and functional | Verify every configured IAP is reachable in the build; any IAP the reviewer can't find is explained in the review notes |

### 2.2 Beta Testing

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 2.2-a | Demos, betas, and trial versions go through TestFlight, not the App Store | Verify no "beta" or "demo" labeling in the App Store build and no third-party beta distribution |
| 2.2-b | TestFlight builds are meant for public distribution, follow these guidelines, and are never given out for compensation | Verify the app isn't internal-only and testers get no rewards or crowdfunding perks for access; significant beta updates go through TestFlight App Review |

### 2.3 Accurate Metadata

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 2.3 | All metadata (privacy information, description, screenshots, previews) reflects the app's core experience and stays current | Compare the description and screenshots with features found in code; flag promised features that don't exist and stale privacy answers |
| 2.3.1-a | Notes for Review describe every new feature and product change specifically; no misleading marketing | Verify the App Review notes are specific (generic notes are rejected) and new features are reachable for review; flag promotion of content or services the app lacks (such as iOS virus scanners) or a false price, inside or outside the App Store; egregious or repeated cases (2.3.1(b)) mean removal from the Developer Program |
| 2.3.2 | IAP disclosed in the description, screenshots, and previews | Verify they say which featured items, levels, or subscriptions cost extra; promoted IAPs have public-audience display names, screenshots, and descriptions, and the app completes a promoted purchase at launch (Apple names SKPaymentTransactionObserver; StoreKit 2 apps use PurchaseIntent) |
| 2.3.3 | Screenshots show the app in use, not only title art, a login page, or a splash screen | Verify screenshots are real app UI; text and image overlays (touch points, Apple Pencil) are allowed |
| 2.3.4 | Previews use only video screen captures of the app | If previews exist: verify in-app footage, not cinematic trailers; narration and overlays are allowed; sticker and iMessage apps may show Messages |
| 2.3.5 | Most appropriate category selected | Verify primary and secondary categories match functionality |
| 2.3.6 | Age-rating questions answered honestly so parental controls work | Verify answers match content, including the social-media questions App Store Connect requires since September 2026 (a feed that redistributes, amplifies, or lets users interact with UGC); media needing local content ratings or warnings complies in each storefront |
| 2.3.7-name | Unique app name, 30 characters max | Verify the character count and no confusing similarity to existing apps |
| 2.3.7-keywords | No trademarked terms, popular app names, pricing information, or irrelevant phrases packed into keywords or other metadata | Check for competitor or popular app names, "free"/"best"/"#1"/sale wording, and unrelated terms |
| 2.3.7-fields | Each metadata field holds only what fits it; subtitles follow standard metadata rules | Verify names, subtitles, screenshots, and previews carry no prices, terms, or text not specific to that field; subtitles have no inappropriate content, references to other apps, or unverifiable claims |
| 2.3.8 | Metadata suits all audiences (4+), even when the app is rated higher | Verify app and IAP icons (including Apple Watch and alternate icons), screenshots, and previews are 4+, and icons look consistent across sizes and variants |
| 2.3.8-kids | "For Kids" and "For Children" are reserved for the Kids Category | If not Kids Category: verify these phrases appear nowhere in metadata |
| 2.3.9 | Rights secured for all materials in icons, screenshots, and previews; fictional account data only | Verify no unlicensed stock photos, third-party logos, or copyrighted material, and screenshots show fictional account info, not a real person's data |
| 2.3.10 | Focus on the Apple platforms the app supports; no names, icons, or imagery of other mobile platforms or alternative app marketplaces | Check the app UI and metadata for "Android", "Google Play", other mobile platforms, or alternative marketplaces (unless specific, approved interactive functionality); no irrelevant information |
| 2.3.11 | Pre-order apps are complete and deliverable as submitted, and the release matches what was advertised | If pre-order: verify feature-completeness; a material change (such as a new business model) means restarting pre-orders |
| 2.3.12 | "What's New" text describes new features and product changes | Verify significant changes are listed specifically; bug fixes, security updates, and performance work may use a generic note |
| 2.3.13 | In-app events are accurate, timely, and use an App Store Connect event type | If in-app events exist: verify metadata is about the event, timing matches the schedule in every storefront, monetization follows Section 3, and the deep link opens the right screen |
| 2.3.14 | Creative assets (product page header and search-result images and video) pertain to the app's content, functionality, or brand, follow standard metadata rules, and suit all audiences | If creative assets exist: verify no inappropriate content, references to other apps meant to mislead, unverifiable product claims, or specific or discounted prices |

### 2.4 Hardware Compatibility

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 2.4.1 | iPhone apps should run on iPad whenever possible | If iPhone-only: verify there's a reason not to support iPad |
| 2.4.2 | Use power efficiently and don't risk device damage | Check for rapid battery drain, excess heat or resource strain, advice to charge the device under a pillow, excessive SSD write cycles, and unrelated background processes such as cryptocurrency mining, including inside third-party ads |
| 2.4.3 | Apple TV apps work with the Siri Remote or third-party game controllers alone | If tvOS: verify Siri Remote support; a required game controller is stated in the metadata |
| 2.4.4 | Never suggest or require a restart or system-setting changes unrelated to core functionality | Check for prompts to restart, turn off Wi-Fi, or disable security features |
| 2.4.5 | Mac App Store requirements | If Mac app: verify (i) App Sandbox and macOS file-system rules; (ii) Xcode packaging, no third-party installers, one self-contained bundle; (iii) no auto-launch, login items, or lingering processes without consent, no auto-added Dock icons or desktop shortcuts; (iv) no downloading apps, kexts, or functionality-changing code; (v) no root escalation or setuid; (vi) no launch license screen, license keys, or own copy protection; (vii) updates only through the Mac App Store; (viii) no deprecated or optional tech such as Java; (ix) all localizations in one bundle |

### 2.5 Software Requirements

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 2.5.1 | Public APIs only, running on the currently shipping OS, with frameworks used for their intended purpose | Check for private API usage and deprecated frameworks slated for removal; HealthKit, HomeKit, and similar frameworks serve their stated purpose (HealthKit apps integrate with Health) and the description mentions the integration |
| 2.5.2 | Self-contained bundle; no reading or writing outside the container; no downloading or executing code that adds or changes features | Check for runtime code loading that alters features; educational coding apps may run downloaded code only when the user can view and edit all of it |
| 2.5.3 | No viruses, files, or code that harms or disrupts the OS or hardware features, including Push Notifications and Game Center | Scan for malicious patterns and abuse of system services |
| 2.5.4 | Background services only for their intended purposes (VoIP, audio playback, location, task completion, local notifications) | Verify each UIBackgroundModes entry matches real usage |
| 2.5.5 | Fully functional on IPv6-only networks | Verify no hardcoded IPv4 addresses or IPv4-only APIs |
| 2.5.6 | Apps that browse the web use the appropriate WebKit framework and WebKit JavaScript | If displaying web content: verify WKWebView or SFSafariViewController, not UIWebView; an alternative browser engine needs Apple's entitlement (EU and Japan only) |
| 2.5.8 | No alternate desktop/home screen environments | Verify the app doesn't replace or replicate the home screen |
| 2.5.9 | Don't alter or disable standard switches, native UI elements, or expected behaviors | Check for overridden Volume or Ring/Silent switch behavior, re-skinned controls that behave differently, and blocked links out to other apps |
| 2.5.11 | SiriKit and Shortcuts: only intents the app handles itself, app-specific vocabulary, direct resolution | If Siri or Shortcuts: verify intents match the stated function without another app; plist phrases and aliases relate to the app (no generic terms or third-party names); no ads between request and fulfillment; disambiguation only when needed |
| 2.5.12 | CallKit and SMS Fraud Extension apps block only confirmed spam | If call or SMS blocking: verify the marketing text names the blocking features and explains the list criteria, and blocking data isn't used for tracking, profiles, or sale |
| 2.5.13 | Facial-recognition account authentication uses LocalAuthentication, with an alternate method for users under 13 | If face-based login: verify LocalAuthentication (not ARKit or custom face recognition) and an alternative for under-13 users |
| 2.5.14 | Explicit consent plus a clear visual or audible indicator when recording or logging user activity | If recording camera, microphone, screen, or other input: verify a consent prompt and a recording indicator |
| 2.5.15 | File-picking apps include items from the Files app and iCloud documents | If the app lets users view and select files: verify Files and iCloud document support |
| 2.5.16 | Widgets, extensions, and notifications relate to the app's content and functionality | Verify each widget, extension, and notification serves the main app's purpose |
| 2.5.16-a | All App Clip features ship in the main app binary; App Clips contain no advertising | If an App Clip exists: verify its features are in the main app and it shows no ads |
| 2.5.17 | Matter support uses Apple's Matter framework to start pairing | If smart home: verify pairing starts through Apple's Matter support framework; any other Matter component is certified by the Connectivity Standards Alliance |
| 2.5.18 | Display ads only in the main app binary; age-appropriate, transparent, dismissible, and reportable | Verify no ads in extensions, App Clips, widgets, notifications, keyboards, or watchOS apps; users can see in the app what data targeted an ad; no targeting on health, ClassKit, or kids' data; interstitials are labeled as ads, don't trick taps, and have visible close/skip buttons large enough to use; users can report inappropriate ads |
| 2.5.19 | No hidden, dormant, or undocumented features; functionality is clear to users and App Review | Check for remote-config or feature-flag gates on functionality absent from the review notes and description, server switches that change the app's purpose after approval (bait-and-switch), and obfuscation that hides features; these are grounds for removal and account termination |

---

## 3. BUSINESS

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 3 | The business model is clear, prices aren't rip-offs, and ratings aren't manipulated | Verify the business model is explained in metadata and review notes, no irrationally high prices, and no paid, incentivized, filtered, or fake reviews or chart manipulation (including through third-party services) |

### 3.1 Payments

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 3.1.1-iap | Unlocking features or functionality (subscriptions, in-game currency, levels, premium content, full version) uses in-app purchase | Verify digital unlocks use StoreKit, with no license keys, AR markers, QR codes, cryptocurrencies, or crypto wallets as unlock mechanisms; Mac App Store apps may enable hosted plug-ins or extensions by other means |
| 3.1.1-restore | Restorable purchases can be restored | If the app sells non-consumables or subscriptions: verify an accessible, working "Restore Purchases" control (consumables-only apps need none) |
| 3.1.1-noexpire | Credits or in-game currencies bought with IAP never expire | If virtual currency: verify no expiration on purchased items |
| 3.1.1-tip-gift | Tips use IAP currencies; gifts of IAP-eligible items refund only to the original purchaser and can't be exchanged | If tipping or gifting: verify both run through IAP and follow the refund rule |
| 3.1.1-lootbox | Loot boxes disclose odds before purchase | If randomized paid items: verify the odds of each item type show before the user pays |
| 3.1.1-giftcards | Digital gift cards, certificates, vouchers, and coupons for digital goods sell only through IAP | If the app sells gift cards: verify digital ones use IAP (physical cards mailed to customers may use other payment) |
| 3.1.1-trial | Non-subscription free trials use a Non-Consumable IAP at Price Tier 0 named "XX-day Trial" | If a non-subscription trial: verify the IAP setup and that the duration, content lost at trial end, and later charges show before the trial starts |
| 3.1.1-nft | NFT services may sell through IAP; owning an NFT can't unlock features | If NFT support: verify NFTs are viewable only, not feature keys; outside the US storefront, no buttons, links, or calls to action to non-IAP NFT purchases |
| 3.1.1a | Links to other purchase methods (Apple's 3.1.1(a)) | If the app has buttons, links, or calls to action to non-IAP purchasing: the US storefront needs no entitlement; any other storefront needs a StoreKit External Purchase Link Entitlement (or, where permitted, a Music Streaming Services Entitlement) for that storefront and platform, linking to a permitted destination, else FAIL; storefronts unknown means WARNING; misleading marketing or fraud around the entitlement means removal |
| 3.1.2-sub | Auto-renewable subscriptions (3.1.2(a)) give ongoing value, last at least 7 days, and work on all the user's devices | If subscription: verify continuing value (new content, SaaS, cloud), a period of 7+ days, and access on every device where the app is available |
| 3.1.2-notask | Subscribers get what they paid for without extra tasks | Verify no required social posts, contact uploads, or check-ins to unlock paid access |
| 3.1.2-switch | Moving to a subscription model doesn't take away functionality users already paid for | If the app moved from a paid unlock to a subscription: verify earlier purchasers keep what they bought |
| 3.1.2-scam | No subscription bait-and-switch or false pretenses | Verify offers aren't misleading (hidden trial conversions, disguised purchase buttons); scam apps are removed |
| 3.1.2-upgrade | Seamless upgrade and downgrade (3.1.2(b)); no accidental duplicate subscriptions | If multiple tiers: verify they share one subscription group |
| 3.1.2-disclosure | Before asking a user to subscribe, the app states what they get for the price (3.1.2(c)) | Verify the sign-up screen shows the subscription name and duration, what it provides, the full renewal price (the billed amount is the most prominent price), and a sign-in or restore option; the app and its metadata link to the Terms of Use (EULA) and Privacy Policy (Apple's subscriptions page; DPLA Schedule 2) |
| 3.1.3 | Apps using another purchase method under 3.1.3(a)–(g) may not encourage non-IAP purchasing in the app, except on the US storefront or under 3.1.1(a) and 3.1.3(a) | If the app relies on a 3.1.3 exception: verify no in-app steering outside those exceptions; messages sent outside the app are fine |
| 3.1.3-reader | Reader apps (3.1.3(a)) for magazines, newspapers, books, audio, music, or video may give access to content bought elsewhere | If reader app: verify no in-app non-IAP digital purchasing; free-tier sign-up and account management are allowed; an account link needs the External Link Account Entitlement, except on the US storefront |
| 3.1.3-multiplatform | Multiplatform services (3.1.3(b)) may unlock content bought on other platforms or the web | Verify those items, consumables included, are also offered as IAP in the app |
| 3.1.3-enterprise | Enterprise services (3.1.3(c)) sold only to organizations may skip IAP | If sold to organizations for employees or students: verify consumer, single-user, or family sales use IAP |
| 3.1.3-p2p | Real-time person-to-person services between two individuals (3.1.3(d)) may skip IAP | If 1:1 services (tutoring, medical consultations, real estate tours, fitness training): verify they're one-to-one; one-to-few and one-to-many real-time services use IAP |
| 3.1.3-physical | Physical goods and services consumed outside the app (3.1.3(e)) must use a non-IAP payment method | If selling physical goods or real-world services: verify Apple Pay, card entry, or similar, never IAP |
| 3.1.3-standalone | Free stand-alone companions to paid web tools for VoIP, cloud storage, email, or web hosting (3.1.3(f)) may skip IAP | Verify no purchasing inside the app and no calls to action to buy outside it |
| 3.1.3-admanagement | Apps only for buying and managing ad campaigns (3.1.3(g)) may skip IAP | Verify the app doesn't display the ads itself; buying "boosts" or ads shown in the same app uses IAP |
| 3.1.4 | Hardware-specific content may unlock without IAP | If features depend on specific hardware (a telescope) or an approved optional product (a toy): verify an IAP path also exists for the optional case; no requiring unrelated purchases or marketing activities to unlock |
| 3.1.5 | Cryptocurrency apps follow the wallet, mining, exchange, ICO, and rewards rules | If crypto: verify (i) wallets come from an organization account; (ii) no on-device mining; (iii) exchanges run only where licensed; (iv) ICOs, crypto futures, and crypto-securities trading come from established banks, securities firms, FCMs, or approved institutions; (v) no crypto rewards for tasks such as downloading apps or posting to social networks |

### 3.2 Other Business Model Issues

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 3.2.1-i | Promoting your own apps is acceptable when the app isn't merely a catalog of them | If the app lists your other apps: verify it has its own functionality |
| 3.2.1-ii | Collections of third-party apps serve a specific approved need (health management, aviation, accessibility) with robust editorial content | If recommending third-party apps: verify editorial content beyond a storefront |
| 3.2.1-iii | Only approved rental content (films, TV, music, books) may expire after the rental period | Verify nothing else the user paid for expires |
| 3.2.1-iv | Wallet passes are used for payments, offers, or identification | If Wallet passes: verify one of those uses (tickets, coupons, VIP credentials) |
| 3.2.1-v | Insurance apps are free, legally compliant where distributed, and don't use IAP | If insurance: verify a free app with no IAP |
| 3.2.1-nonprofit | Only approved nonprofits fundraise in apps (3.2.1(vi)), with Apple Pay, disclosed fund use, and tax receipts | If charity: verify approved nonprofit status, Apple Pay support, and fund-use disclosure; platforms connecting donors to nonprofits list only approved nonprofits |
| 3.2.1-vii | Individual users may give each other monetary gifts without IAP when optional and 100% goes to the recipient | If peer gifting: verify both conditions, and that gifts tied to digital content or services use IAP |
| 3.2.1-viii | Financial trading, investing, or money-management apps come from the licensed institution providing the service | If finance: verify the submitting institution and licensing in each storefront |
| 3.2.2-i | No App Store-like interface or general-interest collection of third-party apps, extensions, or plug-ins | Verify no store or marketplace UI for other apps |
| 3.2.2-iii | No artificial ad impressions or click-throughs, and no apps built mainly to show ads | Verify no ad-fraud patterns and that ads aren't the app's main content |
| 3.2.2-iv | No in-app collection for charities or fundraisers unless an approved nonprofit | If fundraising without approval: verify a free app that collects funds outside the app (Safari or SMS) |
| 3.2.2-v | No arbitrary restriction of who may use the app, such as by location or carrier | Verify no unjustified geo-fencing or carrier restrictions |
| 3.2.2-vii | No artificial boosting of a user's visibility, status, or rank on other services unless their terms allow it | Check for follower or ranking boosts on third-party platforms |
| 3.2.2-viii | No binary options trading; CFDs and other derivatives (FOREX) are licensed everywhere offered | If trading: verify no binary options and licensing for derivatives |
| 3.2.2-ix | Personal loans disclose all terms, cap APR at 36% including costs and fees, and never require full repayment within 60 days | If lending: verify conspicuous disclosure of the equivalent maximum APR and the payment due date, and terms within both limits |
| 3.2.2-x | Don't force rating, reviewing, downloading other apps, or other store actions to use the app | Verify no functionality gated on store actions; rewarding in-app actions (finishing a level, watching an ad) is fine |

---

## 4. DESIGN

### 4.1 Copycats

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 4.1-a | Don't copy popular apps or make minor changes to another app's name or UI | Check UI, functionality, and concept originality |
| 4.1-b | No impersonation of other apps or services | Verify the app's identity doesn't mislead; impersonation breaches the Developer Code of Conduct |
| 4.1-c | No other developer's icon, brand, or product name in your app's icon or name without that developer's approval | Check the icon and name for other developers' brands or product names |

### 4.2 Minimum Functionality

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 4.2 | Features, content, and UI beyond a repackaged website | Verify native functionality, not just a web wrapper |
| 4.2-utility | Lasting entertainment value or adequate utility | Verify a real purpose; a song or movie belongs in the iTunes Store, a book or game guide in Apple Books |
| 4.2.1 | ARKit experiences are rich and integrated | If AR: verify more than dropping a model into a view or replaying an animation |
| 4.2.2 | Not primarily marketing, ads, web clippings, content aggregators, or link collections (catalogs excepted) | Verify the app isn't a promotional vehicle or link aggregator |
| 4.2.3-i | Works on its own without installing another app | Verify no companion app is required to function |
| 4.2.3-ii | Discloses the download size and asks before downloading resources needed at first launch | If the app downloads additional resources on first launch: verify a size disclosure and a prompt |
| 4.2.6 | No commercialized template or app-generation-service apps unless submitted by the content provider | Verify the submitter provides the content; template providers use one aggregated "picker" app instead |
| 4.2.7 | Remote desktop clients that mirror specific software follow strict rules | If remote desktop: verify (a) only a user-owned PC or game console on the local LAN; (b) software runs and renders on the host, with no extra APIs; (c) account creation and management start on the host; (d) no iOS- or store-like UI and no browsing or buying unowned software; (e) not a thin client for cloud apps |

### 4.3 Spam

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 4.3-a | No multiple Bundle IDs of the same app | Verify no near-duplicate submissions (one app per city, team, or school); variations belong in one app, possibly through IAP |
| 4.3-b | Nothing indistinguishable from what's already widely available | If in a saturated category (dating, flashlight, sound effects, wallpaper, simple timers, fortune telling): verify a meaningfully different or improved experience; drinking games, Kama Sutra, fart, and burp apps are rejected as low-effort |

### 4.4 Extensions

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 4.4 | Extensions follow Apple's extension documentation, include functionality, and are disclosed in marketing text | If extensions: verify help screens and settings where possible and an accurate mention in the marketing text |
| 4.4-nopurchase | Extensions can't include marketing, advertising, or IAP | Verify no monetization inside extensions |
| 4.4.1 | Keyboard extensions provide input, work offline, and stay in their lane | If custom keyboard: verify typed input, Sticker-guideline compliance for images or emoji, a next-keyboard control, function without full network access or full access, activity collection only to improve the keyboard, no launching apps other than Settings, and no repurposed keys |
| 4.4.2 | Safari extensions run on the current Safari and request only the site access they need | If Safari extension: verify current-Safari compatibility, no interference with System or Safari UI, no malicious or misleading code, and website access limited to what it needs |

### 4.5 Apple Sites and Services

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 4.5.1 | Approved Apple RSS feeds only; no scraping Apple sites or building rankings from them | If using Apple data: verify approved feeds |
| 4.5.2 | Apple Music through MusicKit: user-initiated playback, no monetized access | If MusicKit: verify the user starts playback with standard controls; no IAP, ads, or user-info requests to access Apple Music; no downloading, uploading, or sharing MusicKit files; cover art only with playback; Apple Music user data disclosed in the purpose string, shared with third parties only to support or improve the app experience, and never used to identify users or target ads |
| 4.5.3 | No spam, phishing, or unsolicited messages through Apple services (Game Center, Push Notifications, Live Activities); no mining Game Center data | Verify no promotional blasts through push or Live Activities and no reverse lookup or harvesting of Player IDs or aliases |
| 4.5.4 | Push notifications are optional, carry no sensitive data, and need opt-in for marketing | Verify the app works without push, no personal or confidential data in notifications, and marketing pushes only after explicit in-app consent with an in-app opt-out |
| 4.5.5 | Game Center Player IDs used only as the Game Center terms allow | If Game Center: verify Player IDs aren't shown in the app or shared with third parties |
| 4.5.6 | Apple emoji only through Unicode characters | Verify Apple emoji images aren't embedded in the binary or used on other platforms |

### 4.7 Mini Apps, Mini Games, Streaming Games, Chatbots, Plug-ins, and Game Emulators

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 4.7 | Software not embedded in the binary (HTML5/JavaScript mini apps and mini games, streaming games, chatbots, plug-ins, emulator game downloads) must comply with all guidelines | If the app offers such software: verify the developer controls what's offered; any non-compliant item leads to rejection |
| 4.7.1 | Offered software follows the privacy rules (5.1), has filtering, reporting, and blocking, and sells digital goods through 3.1 | Verify moderation, privacy compliance, and IAP for digital goods in hosted software |
| 4.7.2 | No extending or exposing native platform APIs or technologies to the software without Apple's prior permission | Check JavaScript bridges and plug-in APIs that expose native capabilities |
| 4.7.3 | No sharing data or privacy permissions with individual software without explicit consent each time | Verify per-item consent before a mini app gets data or permissions |
| 4.7.4 | An index of offered software and metadata, with universal links to each item | If hosting software: verify the catalog and its universal links |
| 4.7.5 | Users can identify software above the app's age rating, and underage access is restricted with verified or declared age | Verify age labels and an age gate based on verified or declared age |

### 4.8 Login Services

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 4.8 | Third-party or social login for the primary account needs an equivalent privacy-focused login option | If Facebook, Google, X, LinkedIn, Amazon, WeChat, or a similar login sets up or authenticates the primary account: verify an option that limits data to name and email, lets users keep their email private, and doesn't collect app interactions for ads without consent (Sign in with Apple qualifies). Exempt: apps using only their own account system; an alternative marketplace's own login; required existing education or enterprise accounts; government or industry-backed citizen ID; a client for a specific third-party service users sign in to directly |

### 4.9 Apple Pay

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 4.9 | Apple Pay: material purchase info before the sale, correct branding and UI | If Apple Pay: verify purchase info before the sale and branding per the Apple Pay marketing guidelines and HIG; recurring payments disclose the renewal term and that it continues until canceled, what each period provides, the actual charges, and how to cancel |

### 4.10 Monetizing Built-In Capabilities

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 4.10 | Don't monetize built-in hardware or OS capabilities or Apple services | Verify no paywall on push notifications, the camera, the gyroscope, Apple Music access, iCloud storage, or Screen Time APIs |

---

## 5. LEGAL

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 5 | Comply with the law everywhere the app is offered; no soliciting, promoting, or encouraging criminal or clearly reckless behavior | Check for features that enable illegal activity; apps found to facilitate human trafficking or child exploitation are reported to authorities, removed, and blocked from alternative distribution |

### 5.1 Privacy

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 5.1.1-i | Privacy policy linked in App Store Connect AND inside the app | Verify the policy URL exists in metadata and is easy to reach in the app |
| 5.1.1-i-content | The policy covers data, uses, third-party protection, retention, deletion, and consent revocation | Verify the policy names the data collected, how, and every use; confirms third parties (analytics, ad networks, SDKs, related entities) give equal protection; and explains retention, deletion, and how to revoke consent or request deletion |
| 5.1.1-ii | User consent before collecting user or usage data, even anonymous data; clear purpose strings | Verify consent before collection, purpose strings that fully describe each use, and no paid functionality that depends on granting data access; collection under GDPR legitimate interest complies with that law |
| 5.1.1-ii-withdraw | An easy, understandable way to withdraw consent | Verify users can revoke consent in the app |
| 5.1.1-iii | Data minimization: request only data relevant to core functionality | Check for excess permissions; prefer the out-of-process picker or share sheet over full Photos or Contacts access |
| 5.1.1-iv | Respect permission settings; no manipulating, tricking, or forcing consent | Verify the app works with declined permissions, offers alternatives (manual address entry when Location is declined), and doesn't demand unrelated permissions (microphone to post photos) |
| 5.1.1-v-login | No login required unless the app has significant account-based features | If login is required: verify it's essential and no personal information is required unless core to the app or required by law |
| 5.1.1-v-delete | Apps that support account creation offer account deletion in the app | If the app supports account creation (sign-up through a third-party login included): verify an in-app deletion flow that deletes the account, not only a sign-out |
| 5.1.1-v-social | Apps not centered on a social network work without a social login; social credentials are revocable in the app | If social login: verify access without it (or through another mechanism), an in-app way to revoke credentials and disconnect data access, and no social tokens stored off the device |
| 5.1.1-vi | No surreptitious discovery of passwords or private data | Verify no hidden keylogging, clipboard harvesting, or credential capture |
| 5.1.1-vii | SafariViewController visibly presents information and isn't used to track users | If SFSafariViewController: verify it isn't hidden or obscured and doesn't track users without consent |
| 5.1.1-viii | No compiling personal information from any source other than the user, or without explicit consent, even from public databases | Verify no scraping or aggregation of people's data |
| 5.1.1-ix | Highly regulated services (banking and financial services, healthcare, gambling, legal cannabis, air travel, crypto exchanges) and apps needing sensitive data come from a legal entity that provides the service | If regulated: verify the submitter is that legal entity, not an individual developer; cannabis sales are geo-restricted to legal jurisdictions |
| 5.1.1-x | Requests for basic contact info (name, email) are optional | Verify no feature depends on providing contact information |
| 5.1.2-i | No using, transmitting, or sharing personal data without permission; App Tracking Transparency for tracking; no feature gated on system permissions | Verify ATT before tracking, clear disclosure of how and where data is used, third-party sharing limited to improving the app or serving ads, and no feature, content, or reward (gift cards, codes) gated on enabling push, location, or tracking |
| 5.1.2-i-ai | Sharing personal data with a third-party AI requires clear disclosure and explicit permission first | If user content or personal data reaches an external AI service (OpenAI, Anthropic, Google Gemini, or similar SDKs or endpoints): verify an in-app disclosure that the data goes to a third-party AI service and an explicit opt-in before the first transmission |
| 5.1.2-ii | Data collected for one purpose isn't repurposed without further consent | Verify data use matches its stated purpose |
| 5.1.2-iii | No surreptitious profiling or re-identification of anonymous users | Verify no fingerprinting or profile reconstruction from "anonymized" or Apple-API data |
| 5.1.2-iv | No contact databases built from Contacts, Photos, or similar APIs; no installed-app analytics | Verify these APIs serve user-facing features only and the app doesn't record which other apps are installed for analytics or ads |
| 5.1.2-v | Contact people only at the user's explicit, individual initiative | If invite or share features: verify no Select All option or all-selected default, and a preview of the message and its apparent sender before sending |
| 5.1.2-vi | HomeKit, HealthKit, Clinical Health Records, MovementDisorder, ClassKit, and depth or facial-mapping data (ARKit, Camera, Photo APIs) aren't used for marketing, ads, or data mining | If using these: verify the data never reaches ad or marketing pipelines, including third parties' |
| 5.1.2-vii | Apple Pay data shared only to deliver goods and services | If Apple Pay: verify payment data isn't shared for marketing |
| 5.1.3-i | Health, fitness, and medical data isn't used or disclosed for ads, marketing, or data mining | If health app: verify the data is used only to improve health management or for health research with permission, with no ad or marketing use (a direct user benefit such as an insurance discount is allowed when the provider submits the app and shares nothing) and disclosure of the specific health data collected |
| 5.1.3-ii | No false data written to HealthKit; no personal health information in iCloud | If writing health data: verify accuracy and no iCloud storage of personal health info |
| 5.1.3-iii | Health research needs informed consent covering nature, purpose, duration, procedures, risks, benefits, confidentiality, contact, and withdrawal | If human-subject research: verify a consent flow (parent or guardian for minors) |
| 5.1.3-iv | Health research has independent ethics review board approval | If health research: verify the approval is available on request |
| 5.1.4-a | Kids' data: comply with COPPA, GDPR, and similar laws; birthdate and parental contact collected only for compliance | If the app targets children: verify compliance, useful functionality regardless of age, and no third-party analytics or ads in apps primarily for kids beyond 1.3's limited exceptions |
| 5.1.4-b | Kids Category apps, and apps collecting personal info from minors, need a privacy policy; third-party analytics or ads only under 1.3's terms | Verify the policy and children's-privacy compliance (a parental gate isn't parental consent); apps outside the Kids Category don't imply children are the main audience in name, subtitle, icon, screenshots, or description |
| 5.1.5 | Location Services only when directly relevant, with notice and consent and the purpose explained | If location: verify relevance, consent, and an in-app explanation; no location-based emergency services or autonomous control of vehicles or aircraft (small drones and toys excepted) |

### 5.2 Intellectual Property

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 5.2.1 | No unauthorized third-party IP and no misleading or copycat names or metadata; submitted by the rights owner | Verify content is original or licensed and the submitter owns or licensed the IP |
| 5.2.2 | Using or monetizing third-party services requires permission under their terms | If integrating third-party content or services: verify terms-of-use permission (authorization on request) |
| 5.2.3 | No illegal file sharing; no saving, converting, or downloading media from third-party sources without authorization | Verify no downloading from Apple Music, YouTube, SoundCloud, Vimeo, or similar without explicit authorization |
| 5.2.4-a | No suggestion that Apple is a source or endorser | Verify no "Apple recommended" or "Featured by Apple" claims |
| 5.2.4-b | Apple applies the "Editor's Choice" badge itself | Verify no self-applied "Editor's Choice" label |
| 5.2.5 | Nothing confusingly similar to Apple products, interfaces, apps, or advertising themes | Verify UI, icon, and name don't mimic Apple's apps (App Store, Messages, Finder); no Apple emoji in keyboards or sticker packs; iTunes or Apple Music previews aren't used as entertainment (background music) and link to the music; Activity rings don't mimic the Activity control; Apple Weather data carries WeatherKit attribution |

### 5.3 Gaming, Gambling, and Lotteries

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 5.3.1 | Sweepstakes and contests are sponsored by the app's developer | If sweepstakes or contests: verify developer sponsorship |
| 5.3.2 | Official rules appear in the app and state that Apple isn't a sponsor or involved | Verify in-app official rules with the Apple disclaimer |
| 5.3.3 | No IAP for credit or currency used in real-money gaming | Verify real-money gaming isn't funded through IAP |
| 5.3.4 | Real-money gaming and lotteries are licensed, geo-restricted, and free on the App Store | If real-money gaming (sports betting, poker, casino, horse racing) or a lottery: verify licensing where used, geo-restriction, and a free app; no card counters or other illegal gambling aids; lotteries have consideration, chance, and a prize |

### 5.4 VPN Apps

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 5.4 | VPN apps use NEVPNManager, come from organization accounts, and never sell or share user data | If VPN: verify NEVPNManager, an organization account, a screen before purchase or use declaring the data collected and its use, a privacy-policy promise not to sell, use, or disclose data, and license info in the review notes where a territory requires one |

### 5.5 Mobile Device Management

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 5.5 | MDM capability is requested from Apple and offered only by enterprises, schools, or government (limited parental-control and security cases) | If MDM or configuration profiles: verify an eligible entity, a data declaration before purchase or use, a privacy-policy no-sale promise, and analytics limited to the MDM app's own performance |

### 5.6 Developer Code of Conduct

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 5.6 | Treat users and Apple with respect; no manipulative or deceptive practices | Check for dark patterns: tricking users into purchases, forcing unnecessary data sharing, sneaky price increases, charging for undelivered features |
| 5.6.1 | Review prompts use Apple's API; responses to reviews stay respectful | Verify rating requests use the system API (SKStoreReviewController, AppStore.requestReview, or SwiftUI requestReview), not a custom rating dialog; a user-tapped "Write a review" link to the App Store page is fine |
| 5.6.2 | Accurate, truthful, current developer identity | Verify the seller name and the developer details shown in the app and metadata agree |
| 5.6.3 | No manipulation of charts, search, reviews, or referrals | Check for incentivized-review flows or rank manipulation |
| 5.6.4 | Sustained quality: no excessive customer reports or refund requests | Usually not verifiable statically; mark WARNING only when the user reports complaint or refund spikes |

---

## Quick Reference: Top 20 Rejection Triggers

These are the guidelines most commonly causing rejection — audit these first:

1. **5.1.1-i** — Missing or inaccessible privacy policy
2. **2.1-a** — App crashes, broken features, placeholder text
3. **2.3** — Misleading metadata (description doesn't match app)
4. **4.2** — Insufficient functionality / web wrapper
5. **2.1-a-demo** — Missing demo account for review
6. **3.1.1-iap** — Digital goods not using Apple IAP
7. **3.1.1-restore** — Missing "Restore Purchases" button
8. **5.1.1-v-delete** — No in-app account deletion
9. **2.3.7-keywords** — Prohibited words in metadata ("free", "best", "#1")
10. **2.3.3** — Screenshots don't show actual app usage
11. **5.1.2-i** — Missing App Tracking Transparency
12. **4.8** — Third-party login without an equivalent privacy-focused option such as Sign in with Apple
13. **2.3.6** — Incorrect age rating
14. **1.2** — UGC app missing moderation/reporting/blocking
15. **2.5.5** — App doesn't work on IPv6-only networks
16. **3.1.2-disclosure** — Unclear subscription terms
17. **2.3.10** — References to other platforms in metadata
18. **5.2.1** — Unauthorized third-party IP usage
19. **4.1-a, 4.1-b, 4.1-c** — Copycat, impersonation, or another developer's brand
20. **2.5.1** — Private API usage
