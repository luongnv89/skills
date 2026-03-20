# Apple App Store Review Guidelines — Complete Checklist

This reference contains every checkable guideline organized by section. For each guideline, the checker should determine: PASS, FAIL, WARNING (potential issue), or N/A (not applicable to this app type).

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
| 1.1.1 | No defamatory, discriminatory, or mean-spirited content | Review app content, user-facing text, imagery for offensive material targeting race, religion, gender, sexual orientation, etc. |
| 1.1.2 | No realistic portrayals of people or animals being killed, maimed, tortured, or abused | Check for graphic violence in content, images, videos, or gameplay |
| 1.1.3 | No depictions encouraging illegal or irresponsible weapon use | Look for content promoting illegal firearm purchases or dangerous weapon modifications |
| 1.1.4 | No overtly sexual or pornographic material | Check for explicit sexual content in images, text, or user-generated content |
| 1.1.5 | No inflammatory religious commentary or inaccurate religious text | Review any religious content for inflammatory or misleading material |
| 1.1.6 | No false information or trick/joke functionality that could cause harm | Check for misleading claims, fake device capabilities, prank features that could cause distress |
| 1.1.7 | No content capitalizing on recent traumatic events | Check for exploitation of disasters, conflicts, pandemics, or tragedies |

### 1.2 User-Generated Content

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 1.2 | UGC apps must have: content filtering, reporting mechanism, user blocking, published contact info for concerns | If app allows user posts/comments/media: verify moderation system, report button, block functionality, visible support contact |
| 1.2.1 | Creator content apps need moderation and age identification | If app features creator-generated content: verify age gating and content moderation system |

### 1.3 Kids Category

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 1.3-a | No links outside parental-gated areas | If Kids Category: verify no external links, purchasing prompts, or distractions outside parental gates |
| 1.3-b | No third-party analytics or advertising | If Kids Category: verify no third-party SDKs for analytics or ads (limited exceptions require human review) |
| 1.3-c | No IDFA collection or identifiable info transmission | If Kids Category: verify no device identifier collection or personal data transmission |
| 1.3-d | Comply with COPPA and applicable children's privacy laws | If Kids Category: verify compliance with children's privacy regulations |

### 1.4 Physical Harm

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 1.4.1 | Medical apps must provide validated accuracy info | If medical/health app: verify accuracy claims have supporting evidence, proper disclaimers |
| 1.4.2 | Drug dosage calculators need FDA/approved entity backing | If drug dosage calculator: verify regulatory approval documentation |
| 1.4.3 | No encouragement of tobacco, drugs, or excessive alcohol use | Check content for substance use glorification or encouragement |
| 1.4.4 | DUI checkpoint apps limited to law enforcement published info | If DUI-related: verify data sources are public law enforcement info |
| 1.4.5 | No encouragement of dangerous physical activities | Check for content encouraging risky stunts or dangerous behavior |

### 1.5 Developer Information

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 1.5-a | Easy contact method in app AND support URL | Verify in-app contact mechanism AND working support URL in metadata |
| 1.5-b | Valid contact info for Wallet passes | If using Wallet: verify passes include valid contact information |

### 1.6 Data Security

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 1.6 | Appropriate security measures for user data | Verify encryption for sensitive data, secure API communication (HTTPS), secure data storage practices |

### 1.7 Reporting Criminal Activity

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 1.7 | Crime reporting must involve local law enforcement | If crime reporting features: verify law enforcement partnership and geo-restrictions |

---

## 2. PERFORMANCE

### 2.1 App Completeness

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 2.1-a | App must be final version, all metadata complete, URLs working, tested for bugs | Verify: no placeholder text, all links work, no crashes on launch, all features functional |
| 2.1-a-demo | Demo account or built-in demo mode for login features | If app requires login: verify demo credentials exist and are documented in review notes |
| 2.1-b | In-app purchases complete, up-to-date, visible, and functional | Verify all IAPs are configured, working, and properly described |

### 2.2 Beta Testing

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 2.2-a | Beta testing only through TestFlight | Verify no third-party beta distribution; no "beta" label in App Store version |
| 2.2-b | App intended for public distribution | Verify app isn't limited to internal use only |

### 2.3 Accurate Metadata

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 2.3.1 | No hidden or dormant features | Check for undocumented features, remote feature flags that could activate undisclosed functionality |
| 2.3.1-a | All new features described with specificity | Verify What's New text describes all changes in the update |
| 2.3.2 | In-app purchases disclosed in description, screenshots, previews | Verify IAP pricing and content is mentioned in description; screenshots don't show paid content without disclosure |
| 2.3.3 | Screenshots show app in actual use | Verify screenshots are real app UI, not just splash screens, login pages, or marketing graphics |
| 2.3.4 | Preview videos use actual app screen captures | If app preview exists: verify it shows real in-app footage, not cinematic trailers |
| 2.3.5 | Correct category selected | Verify primary and secondary categories match app functionality |
| 2.3.6 | Age rating answered honestly | Verify content questionnaire answers match actual app content |
| 2.3.7-name | App name ≤ 30 characters, unique, accurate | Verify character count and that name isn't confusingly similar to existing apps |
| 2.3.7-keywords | No trademark terms, pricing words, or irrelevant phrases in keywords | Check keywords for: competitor names, "free"/"best"/"#1", unrelated terms |
| 2.3.8 | Metadata appropriate for all audiences (4+ standard) | Verify title, subtitle, description, screenshots don't contain mature content |
| 2.3.8-kids | "For Kids"/"For Children" reserved for Kids Category | If not Kids Category: verify these phrases aren't used anywhere in metadata |
| 2.3.9 | Rights secured for all materials in icons, screenshots, previews | Verify no unlicensed stock photos, third-party logos, or copyrighted material |
| 2.3.10 | No references to other platforms | Check metadata for mentions of "Android", "Google Play", "Windows", etc. |
| 2.3.11 | Pre-order apps must be complete and deliverable | If pre-order: verify app is feature-complete for scheduled release |
| 2.3.12 | Describe new features/changes in What's New | Verify What's New text exists and accurately describes changes |
| 2.3.13 | In-app events must be accurate, timely, and compliant | If in-app events configured: verify accuracy and timing |

### 2.4 Hardware Compatibility

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 2.4.1 | iPhone apps should run on iPad when possible | If iPhone-only: verify there's a good reason not to support iPad |
| 2.4.2 | Use power efficiently; no excessive battery drain or crypto mining | Check for background processes, excessive CPU/GPU usage, cryptocurrency mining code |
| 2.4.3 | Apple TV apps usable with Siri remote or game controllers | If tvOS: verify Siri remote compatibility |
| 2.4.4 | Don't suggest device restart or unrelated system setting changes | Check for prompts asking users to restart device or change unrelated settings |
| 2.4.5 | Mac App Store requirements (sandboxing, Xcode packaging, etc.) | If Mac app: verify sandboxing, no third-party installers, no auto-launch without consent |

### 2.5 Software Requirements

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 2.5.1 | Public APIs only; run on currently shipping OS | Check for private API usage; verify compatibility with current OS |
| 2.5.2 | Self-contained bundles; no external code loading | Check for dynamic code downloading, external frameworks loaded at runtime |
| 2.5.3 | No malware, viruses, or harmful code | Scan for malicious patterns, obfuscated payloads, unauthorized data collection |
| 2.5.4 | Background services for intended purposes only | Verify background modes match declared usage (audio, location, VoIP, etc.) |
| 2.5.5 | Fully functional on IPv6-only networks | Verify no hardcoded IPv4 addresses; test IPv6 compatibility |
| 2.5.6 | Use appropriate WebKit framework for web content | If displaying web content: verify using WKWebView (not deprecated UIWebView) |
| 2.5.8 | No alternate desktop/home screen environments | Verify app doesn't attempt to replace or replicate the home screen |
| 2.5.9 | Don't alter standard switches or native UI elements | Check for re-skinned standard iOS controls that change expected behavior |
| 2.5.11 | SiriKit/Shortcuts: handle only supported intents, accurate vocabulary | If Siri integration: verify intent handling matches capabilities; no ads between request and fulfillment |
| 2.5.12 | CallKit/SMS blocking: block confirmed spam only | If call/SMS blocking: verify blocking criteria are reasonable; no data use for profiling |
| 2.5.13 | Facial recognition uses LocalAuthentication; alternate auth for under-13 | If using Face ID: verify proper framework usage; alternate auth available for minors |
| 2.5.14 | Explicit user consent for recording/logging | If recording audio/video/screen: verify consent prompt before recording starts |
| 2.5.15 | File viewing apps support Files app and iCloud documents | If file viewer: verify Files app integration |
| 2.5.16 | Widgets, extensions, notifications related to app content | Verify widgets/extensions serve content from the main app; App Clips in main binary with no ads |
| 2.5.17 | Matter support uses Apple's Matter framework | If smart home: verify using Apple's Matter SDK |
| 2.5.18 | Display advertising limited to main binary; age-appropriate; clear close buttons | Verify ads only in main app (not extensions); interstitial ads have visible close button; no ads targeting kids/health data |

---

## 3. BUSINESS

### 3.1 Payments

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 3.1.1-iap | Digital content/features unlocked via in-app purchase | Verify digital goods (subscriptions, premium features, virtual currencies) use Apple IAP |
| 3.1.1-restore | Restore Purchases mechanism exists | Verify a "Restore Purchases" button is accessible and functional |
| 3.1.1-noexpire | Purchased credits/currencies don't expire | If virtual currency: verify no expiration on purchased items |
| 3.1.1-lootbox | Loot boxes disclose odds before purchase | If randomized purchases: verify probability disclosure before user pays |
| 3.1.1-nft | NFT ownership doesn't unlock features or functionality | If NFT support: verify NFTs are viewable but don't gate app features |
| 3.1.1-trial | Free trials use Non-Consumable IAP at Price Tier 0 with "XX-day Trial" naming | If free trial: verify proper IAP configuration, duration disclosure, post-trial charges |
| 3.1.1a | External purchase links only with proper entitlement in allowed regions | If linking to external purchases: verify StoreKit External Purchase Link Entitlement |
| 3.1.2-sub | Subscriptions provide ongoing value, minimum 7 days, cross-device | If subscription: verify continuous value delivery, proper duration, universal access |
| 3.1.2-disclosure | Clear subscription terms before purchase | Verify subscription screen shows: price, billing period, renewal terms, cancellation method |
| 3.1.2-notask | No extra tasks required for subscription access (social posts, check-ins) | Verify subscriptions don't require non-app actions |
| 3.1.2-upgrade | Seamless upgrade/downgrade between subscription tiers | If multiple tiers: verify smooth tier switching without multiple subscriptions |
| 3.1.3-reader | Reader apps: access previously purchased content only | If reader app: verify proper entitlement, no in-app digital purchasing |
| 3.1.3-physical | Physical goods/services can use alternative payment | If selling physical goods: verify correct payment categorization |
| 3.1.3-p2p | Person-to-person real-time services can use alternative payment | If 1:1 services (tutoring, medical): verify correct categorization |
| 3.1.4 | Hardware-specific content unlocking | If hardware-dependent features: verify optional hardware with IAP alternative |
| 3.1.5 | Cryptocurrency apps: proper licensing and entity requirements | If crypto wallet/exchange/mining: verify organization status, proper licensing, no on-device mining |

### 3.2 Business Model Issues

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 3.2.1-nonprofit | Nonprofit fundraising requires Apple approval and proper disclosure | If charity: verify approved nonprofit status, fund usage disclosure |
| 3.2.2-i | No App Store-like interface for displaying third-party apps | Verify no store/marketplace UI for other apps |
| 3.2.2-iii | No artificial ad impression/click inflation | Verify no ad fraud patterns |
| 3.2.2-v | No arbitrary user restriction by location or carrier | Verify no unjustified geo-fencing or carrier restrictions |
| 3.2.2-viii | No binary options trading; CFD/FOREX requires licensing | If financial trading: verify licensing and prohibited instrument avoidance |
| 3.2.2-ix | Personal loans: clear terms, max 36% APR | If lending: verify rate disclosure, legal APR limits |
| 3.2.2-x | Don't force rating/reviewing/downloading other apps | Verify no forced actions; can incentivize in-app actions only |

---

## 4. DESIGN

### 4.1 Copycats

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 4.1-a | Don't copy popular apps or create minor variants | Check UI, functionality, and concept originality |
| 4.1-b | No impersonation of other apps or developers | Verify app identity is genuine and doesn't mislead |
| 4.1-c | Don't use another developer's icon, brand, or product name | Check icons, names, and branding for similarity to existing apps |

### 4.2 Minimum Functionality

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 4.2 | App includes features/content/UI beyond a repackaged website | Verify app provides native functionality, not just a web wrapper |
| 4.2-utility | App provides lasting entertainment or adequate utility | Verify app has real purpose and value beyond a one-time use |
| 4.2.1 | ARKit experiences must be rich and integrated | If AR features: verify they're substantial, not just model dropping |
| 4.2.2 | Not primarily marketing, ads, web clippings, or link collections | Verify app isn't just a promotional vehicle or link aggregator |
| 4.2.6 | No template/generation service apps unless provider-submitted | Verify app isn't a clone from a template service submitted by the end-user |
| 4.2.7 | Remote desktop: local LAN only, host-executed, no iOS-mimicking UI | If remote desktop: verify LAN restriction, proper execution model, distinct UI |

### 4.3 Spam

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 4.3-a | No multiple Bundle IDs for the same app | Verify no duplicate submissions with minor variations |
| 4.3-b | Avoid oversaturated categories; must be unique/high-quality | If in a crowded category: verify app offers genuine differentiation |

### 4.4 Extensions

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 4.4 | Extensions include functionality and are disclosed in marketing | If extensions: verify they have help/settings and are described in metadata |
| 4.4-nopurchase | Extensions can't include marketing, advertising, or IAP | Verify no monetization inside extensions |
| 4.4.1 | Keyboard extensions: provide input, work offline, don't track user activity beyond enhancement | If custom keyboard: verify core input works, offline capability, minimal data collection |
| 4.4.2 | Safari extensions: run on current Safari, don't interfere with system UI | If Safari extension: verify compatibility and non-interference |

### 4.5 Apple Sites and Services

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 4.5.1 | Use approved Apple RSS feeds only; no scraping or custom rankings | If using Apple data: verify approved feed usage |
| 4.5.2 | Apple Music: proper MusicKit usage, no monetization of access | If music features: verify MusicKit compliance, no payment for Apple Music access |
| 4.5.3 | No spam via Game Center or Push Notifications | Verify no misuse of Apple messaging/notification systems |
| 4.5.4 | Push notifications: not required, no sensitive data, opt-in for marketing | Verify push is optional, marketing pushes require consent, no confidential data |
| 4.5.5 | Game Center Player IDs: use per terms | If Game Center: verify proper player ID handling |
| 4.5.6 | Unicode emoji rendering: Apple emoji OK, not for other platforms | Verify no custom rendering of Apple emoji on non-Apple platforms |

### 4.7 Mini Apps, Streaming, Chatbots, Emulators

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 4.7.1 | Hosted software follows privacy guidelines, has filtering/reporting/blocking | If hosting mini-apps/games: verify moderation, privacy compliance, reporting |
| 4.7.2 | No native API exposure without Apple permission | Verify hosted content doesn't access native APIs |
| 4.7.3 | Data/privacy permissions require per-instance user consent | Verify each hosted app requests its own permissions |
| 4.7.4 | Provide index of software with universal links | If hosting content: verify software catalog with deep links |
| 4.7.5 | Age identification and restriction for inappropriate content | If hosting varied content: verify age gating system |

### 4.8 Login Services

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 4.8 | Sign in with Apple required when third-party login offered | If using Facebook/Google/other login: verify Sign in with Apple is also offered (with exceptions for enterprise/education/specific services) |

### 4.9 Apple Pay

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 4.9 | Apple Pay: provide material info before sale, correct branding | If Apple Pay: verify purchase info display, proper branding, recurring payment disclosures |

### 4.10 Monetizing Built-In Capabilities

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 4.10 | Don't monetize hardware/OS built-ins or Apple services | Verify no paywall on camera, push notifications, iCloud storage, Screen Time, etc. |

---

## 5. LEGAL

### 5.1 Privacy

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 5.1.1-i | Privacy policy linked in App Store Connect AND in-app | Verify privacy policy URL exists in metadata AND is accessible within the app |
| 5.1.1-i-content | Privacy policy identifies data collected, usage, and sharing | Verify policy is specific about what data, why, and who it's shared with |
| 5.1.1-ii | User consent for data collection (even anonymous) | Verify consent mechanism before any data collection; clear purpose strings |
| 5.1.1-ii-withdraw | Easy consent withdrawal method | Verify users can revoke data permissions easily |
| 5.1.1-iii | Data minimization: only collect relevant data | Check for excessive permissions or data collection beyond core functionality |
| 5.1.1-iv | Respect permission settings; no manipulation or forced consent | Verify app works with declined permissions; no repeated permission prompts |
| 5.1.1-v-login | Account sign-in not required for non-account-based apps | If login required: verify it's essential to core functionality |
| 5.1.1-v-delete | Account creation must allow deletion within app | If accounts exist: verify in-app account deletion mechanism |
| 5.1.1-v-social | Non-social apps provide non-login option; revoke social credentials in-app | If social login: verify guest mode and credential revocation |
| 5.1.1-vi | No surreptitious password/private data discovery | Verify no hidden keylogging, clipboard monitoring, or credential harvesting |
| 5.1.1-vii | SafariViewController for visible information only; no hidden tracking | If using SFSafariViewController: verify it's visible and not used for fingerprinting |
| 5.1.1-viii | No data compilation from non-user sources without consent | Verify no scraping or aggregating personal data from external sources |
| 5.1.1-ix | Regulated apps (banking, health, gambling, cannabis, crypto, air travel) submitted by legal entity | If regulated category: verify legal entity submission |
| 5.1.2-i | Permission required before data use/sharing; ATT for tracking | Verify App Tracking Transparency implementation; clear third-party sharing disclosure |
| 5.1.2-ii | One-purpose data not repurposed without consent | Verify data collected for one reason isn't used for another |
| 5.1.2-iii | No surreptitious user profiling or anonymous identification | Verify no fingerprinting or hidden analytics building user profiles |
| 5.1.2-iv | No Contacts/Photos API misuse for contact databases or install analytics | Verify these APIs are used for user-facing features only |
| 5.1.2-v | Contact people only at explicit user initiative (no Select All default) | If sharing/invite features: verify user explicitly selects recipients |
| 5.1.2-vi | HealthKit/HomeKit/ClassKit data not used for marketing or data mining | If using these frameworks: verify data usage is limited to intended purpose |
| 5.1.2-vii | Apple Pay user data only for goods/service delivery | If Apple Pay: verify payment data not shared for marketing |
| 5.1.3-i | Health/fitness data not shared for ads/marketing/data mining | If health app: verify no data monetization; disclose specific data collected |
| 5.1.3-ii | No false/inaccurate health data; no personal health info in iCloud | If health data: verify accuracy standards and storage security |
| 5.1.3-iii | Health research requires informed consent with specific disclosures | If health research: verify comprehensive consent flow |
| 5.1.3-iv | Health research requires ethics board approval | If health research: verify IRB/ethics board documentation |
| 5.1.4-a | Kids apps: review COPPA/GDPR; no third-party analytics/ads | If targets children: verify strict compliance with children's privacy laws |
| 5.1.4-b | Kids Category apps need privacy policy; "For Kids" reserved | If Kids Category: verify privacy policy; if not Kids Category: don't use "For Kids" |
| 5.1.5 | Location Services: relevant to features, consent obtained, purpose explained | If using location: verify relevance, consent prompt, in-app explanation |

### 5.2 Intellectual Property

| ID | Guideline | What to Check |
|----|-----------|---------------|
| 5.2.1 | No unauthorized third-party IP; submit via rights owner | Verify all content is original or properly licensed; app submitted by IP owner |
| 5.2.2 | Third-party service integration has explicit permission | If integrating third-party services: verify Terms of Use compliance |
| 5.2.3 | No illegal file sharing or unauthorized downloading from third-party sources | Verify no piracy features; no saving from YouTube/SoundCloud/etc. without authorization |
| 5.2.4-a | No suggestion of Apple endorsement or source | Verify no "Apple recommended", "Featured by Apple" claims in marketing |
| 5.2.4-b | "Editor's Choice" applied only by Apple | Verify no self-applied "Editor's Choice" label |
| 5.2.5 | Don't appear confusingly similar to Apple products | Verify UI, icon, name don't mimic Apple's own apps |

---

## Quick Reference: Top 20 Rejection Triggers

These are the guidelines most commonly causing rejection — audit these first:

1. **5.1.1-i** — Missing or inaccessible privacy policy
2. **2.1-a** — App crashes, broken features, placeholder text
3. **2.3** — Misleading metadata (description doesn't match app)
4. **4.2** — Insufficient functionality / web wrapper
5. **2.1-a** — Missing demo account for review
6. **3.1.1-iap** — Digital goods not using Apple IAP
7. **3.1.1-restore** — Missing "Restore Purchases" button
8. **5.1.1-v-delete** — No in-app account deletion
9. **2.3.7-keywords** — Prohibited words in metadata ("free", "best", "#1")
10. **2.3.3** — Screenshots don't show actual app usage
11. **5.1.2-i** — Missing App Tracking Transparency
12. **4.8** — Missing Sign in with Apple when third-party login exists
13. **2.3.6** — Incorrect age rating
14. **1.2** — UGC app missing moderation/reporting/blocking
15. **2.5.5** — App doesn't work on IPv6-only networks
16. **3.1.2-disclosure** — Unclear subscription terms
17. **2.3.10** — References to other platforms in metadata
18. **5.2.1** — Unauthorized third-party IP usage
19. **4.1** — Copycat or impersonation
20. **2.5.1** — Private API usage
