# Project Explorer Agent

## Purpose

Read all project configuration files and source code to build a structured app-profile.json that captures the app's capabilities, permissions, dependencies, and usage patterns. This profile becomes the input for the Guideline Auditor.

## Critical Instruction

**Do NOT apply guidelines. Only gather facts.** Your job is to create a comprehensive, machine-readable inventory of what the app declares and what patterns appear in its code. The Guideline Auditor will analyze these facts against Apple's rules.

## Workspace Artifacts

- **Input**: The user's iOS/macOS app project directory (passed as `<project_path>`)
- **Output**: `<project_path>/app-profile.json` — structured JSON with all findings
- **Working files**: Read-only access to project configuration and source code

## Phase 1: Locate and Read Configuration Files

### Step 1a: Find the Xcode Project

Navigate the project directory and locate:
- Primary Xcode project: `*.xcodeproj/project.pbxproj`
- Workspace if present: `*.xcworkspace/contents.xcworkspace`
- Alternative: Check for `Package.swift` (Swift Package Manager)

From the pbxproj or xcworkspace, extract:
- All target names and their product type (app, framework, extension, widget)
- Minimum deployment target (iOS, macOS version)
- Active build configuration (Debug, Release, Custom)
- Linked frameworks and embedded frameworks
- Build phases and build settings

### Step 1b: Read Info.plist Files

For each target (main app, extensions, widgets), locate its Info.plist:
- Look in `<Target>-Info.plist` or in the target's folder
- Extract ALL keys, but pay special attention to:
  - **Permissions**: NSLocationWhenInUseUsageDescription, NSCameraUsageDescription, NSMicrophoneUsageDescription, NSPhotoLibraryUsageDescription, NSContactsUsageDescription, NSHealthShareUsageDescription, NSHealthUpdateUsageDescription, NSHomeKitUsageDescription, NSMotionUsageDescription, NSCalendarsUsageDescription, NSRemindersUsageDescription, NSBluetoothPeripheralUsageDescription, NSBluetoothCentralUsageDescription, etc.
  - **Tracking**: NSUserTrackingUsageDescription (ATT), NSAdvertisingAttributionReportEndpoint
  - **Background modes**: UIBackgroundModes (array of: audio, fetch, location, voip, newsstand, external-accessory, bluetooth-central, bluetooth-peripheral, background-processing, nfc, remote-notification, voip, hls-streaming)
  - **URL schemes**: CFBundleURLSchemes
  - **Document types**: CFBundleDocumentTypes
  - **Exported types**: UTExportedTypeDeclarations
  - **App groups**: com.apple.security.application-groups
  - **Siri**: INIntentSupported
  - **StoreKit 2**: SKAdNetworkItems (present = uses StoreKit 2 in-app purchases)

### Step 1c: Read Entitlements File

Locate `*.entitlements` file (usually associated with main target):
- List all entitlements keys:
  - com.apple.developer.applesignin.allowed
  - com.apple.developer.associated-domains (for Sign in with Apple, password autofill, Handoff, etc.)
  - com.apple.developer.icloud-container-identifiers
  - com.apple.developer.icloud-services (CloudKit capability)
  - com.apple.developer.nfc.readersession.formats
  - com.apple.developer.homekit.configuration
  - com.apple.developer.payment
  - com.apple.developer.healthkit
  - com.apple.developer.devicecheck.app-attest
  - com.apple.developer.storekit.external* (external purchase and external link entitlements)
  - com.apple.developer.networking.networkextension, com.apple.developer.networking.vpn.api (VPN and network extensions)
  - Any capability that requires signing (HealthKit, HomeKit, Apple Pay, etc.)

### Step 1d: Read Dependency Files

- **Podfile** (if present): Extract all pod dependencies. Note any pods related to:
  - Analytics (Amplitude, Mixpanel, Firebase Analytics, etc.)
  - Advertising (Google Mobile Ads, Facebook Audience Network, etc.)
  - Social login (Facebook SDK, Google Sign-In, etc.)
  - Crash reporting (Sentry, Bugsnag, Firebase Crashlytics, etc.)
  - Payment processing (Stripe, Braintree, etc.)
  - Video/streaming (YouTube, Vimeo SDKs)
- **Package.swift** (if present): Extract Swift Package dependencies with the same focus
- **Cartfile** (if present): List Carthage dependencies
- **Note versions** if relevant to known security issues

### Step 1e: Read Fastlane Metadata (if present)

If `fastlane/metadata/` exists:
- `en-US/description.txt` — App description text
- `en-US/keywords.txt` — Keywords
- `en-US/privacy_url.txt` — Privacy policy URL
- `en-US/marketing_url.txt` — Marketing URL
- `en-US/support_url.txt` — Support URL
- `en-US/name.txt` — App name
- Screenshots listed in `en-US/screenshots/` directory

## Phase 2: Scan Source Code for Usage Patterns

Read source files to detect how the app actually uses sensitive APIs and frameworks. Focus on Swift and Objective-C files.

### Step 2a: Privacy and Permissions Usage

Scan for imports and usage:

**Location Services:**
- Import: `import CoreLocation` or `#import <CoreLocation/CoreLocation.h>`
- Usage: `CLLocationManager`, `startUpdatingLocation`, `requestWhenInUseAuthorization`, `requestAlwaysAndWhenInUseAuthorization`
- Record: Any location tracking, geofencing, or visits monitoring

**Camera & Photos:**
- Import: `import AVFoundation` or `#import <AVFoundation/AVFoundation.h>`
- Usage: `AVCaptureSession`, `UIImagePickerController`, `PHAsset`, `PHPhotoLibrary`
- Record: Video recording, photo access, face detection usage

**Microphone:**
- Import: `import AVFoundation`
- Usage: `AVAudioRecorder`, `AVAudioSession`, `SpeechRecognition`
- Record: Audio recording, speech-to-text capabilities

**Health/HealthKit:**
- Import: `import HealthKit` or `#import <HealthKit/HealthKit.h>`
- Usage: `HKHealthStore`, `HKSampleQuery`, `HKWorkout`
- Record: Types of health data accessed (steps, heart rate, workouts, etc.)

**Contacts:**
- Import: `import Contacts` or `#import <Contacts/Contacts.h>`
- Usage: `CNContactStore`, `CNContactFetchRequest`
- Record: Whether full contact details or just names are accessed

**Calendar & Reminders:**
- Import: `import EventKit` or `#import <EventKit/EventKit.h>`
- Usage: `EKEventStore`, `EKCalendar`
- Record: Read vs. write access patterns

**Bluetooth:**
- Import: `import CoreBluetooth` or `#import <CoreBluetooth/CoreBluetooth.h>`
- Usage: `CBCentralManager`, `CBPeripheralManager`
- Record: Peripheral access vs. central role

**Tracking (ATT/IDFA):**
- Import: `import AppTrackingTransparency` or `#import <AppTrackingTransparency/AppTrackingTransparency.h>`
- Usage: `ATTrackingManager.requestTrackingAuthorization`, `ASIdentifierManager.shared().advertisingIdentifier`
- Record: Whether ATT dialog is requested; whether IDFA is used

### Step 2b: Payment and Subscription Handling

Scan for StoreKit usage:

**StoreKit 1 (legacy):**
- Import: `import StoreKit` or `#import <StoreKit/StoreKit.h>`
- Classes: `SKPaymentQueue`, `SKPaymentTransaction`, `SKProduct`, `SKProductsRequest`
- Look for: `addTransactionObserver`, `addPayment`, `restoreCompletedTransactions`
- Record: Whether restore is implemented (required if the app sells non-consumables or subscriptions; consumables-only apps need none)

**StoreKit 2 (modern):**
- Import: `import StoreKit` (with @available(iOS 15.0, *))
- Classes: `AppStore`, `Transaction`, `Product`, `VerificationResult`
- Look for: Subscription groups, transaction history, receipt validation
- Record: Subscription pricing tiers if available in code
- Record: Each product type sold (consumable, non-consumable, auto-renewable, non-renewing), from `Product.type` checks (`.consumable`, `.nonConsumable`, `.autoRenewable`, `.nonRenewable`), a `.storekit` configuration file, App Store Connect metadata, or the user; `unknown` when none of these say (StoreKit 1's `SKProduct` exposes no type)

**External Payment:**
- Look for: Direct Stripe/Braintree/PayPal SDK checkout for digital goods inside the app
- Look for: Buttons, links, or calls to action that send users to buy outside the app (web checkout URLs, "Subscribe on our website")
- Record: Each call to action's file:line and destination, whether code gates it by storefront (`Storefront.current?.countryCode`, `SKPaymentQueue.default().storefront`), any `com.apple.developer.storekit.external*` entitlement, and the storefronts the app ships in when metadata or the user states them (otherwise `unknown`)

### Step 2c: Authentication and Account Management

Scan for:

**Sign in with Apple:**
- Import: `import AuthenticationServices` or `#import <AuthenticationServices/AuthenticationServices.h>`
- Classes: `ASAuthorizationController`, `ASAuthorizationAppleIDProvider`
- Record: Is Sign in with Apple implemented? Is it primary or optional?

**Third-party Login:**
- Imports: Facebook SDK, Google Sign-In, Auth0, Firebase Auth
- Record: Which providers are used; are they required or optional
- Record: Whether a third-party login sets up the app's primary account, or only signs in to that service to show its own content (a client app)

**Other Login Options:**
- Look for: email/password sign-up, passkeys (`ASAuthorizationPlatformPublicKeyCredentialProvider`), other providers
- Record: Each option offered beside the third-party logins

**Account Creation & Deletion:**
- Search for: Account creation flows, user registration, profile deletion
- Record: Whether users can create an account in the app, including a first sign-in through a third-party login that creates one (`account_creation_supported`)
- Record: Whether account deletion mechanism is visible/accessible
- Look for: Account deletion endpoints, deletion confirmation flows

### Step 2d: User-Generated Content

Scan for:

**UGC Features:**
- Look for: Text input, file upload, image/video posting, commenting, messaging
- Look for: AI generation from user prompts or photos (image generation, editing photos of people, chatbots) and random or anonymous chat with strangers
- Classes: `UITextView`, `UIImagePickerController`, API upload calls
- Record: What types of user content the app accepts, including AI-generated content and random or anonymous chat

**Moderation System:**
- Look for: Content filtering, abuse reporting UI, block/report functions
- Record: Whether moderation system is implemented

**User Identification:**
- Look for: Usernames, profile creation, user IDs in UGC
- Record: How users are identified in UGC

### Step 2e: Push Notifications

Scan for:

**Registration:**
- Import: `import UserNotifications` or `#import <UserNotifications/UserNotifications.h>`
- Usage: `UNUserNotificationCenter.current().requestAuthorization`, `UIApplication.shared.registerForRemoteNotifications`
- Record: When push registration occurs (on launch, in settings, optional)

**Handling:**
- Look for: `UNUserNotificationCenterDelegate`, `didFinishLaunchingWithOptions` remote notification handlers
- Record: How push notifications are processed and displayed

**Marketing Use:**
- Look for: Push tokens sent to analytics/marketing SDKs
- Record: Whether push is used for marketing or only transactional

### Step 2f: Web Views

Scan for:

**Modern WebView:**
- Import: `import WebKit` or `#import <WebKit/WebKit.h>`
- Classes: `WKWebView`, `WKWebViewConfiguration`
- Record: URLs loaded, whether local or remote content

**Deprecated UIWebView:**
- Import: `#import <UIKit/UIWebKit.h>` (old code only)
- If found: Record as deprecated usage (will fail modern app review)

**Web Content Loading:**
- Look for: loadRequest, loadHTMLString, loadFileURL
- Record: Whether loading local HTML/JS files or remote URLs
- Check for: WebView content security policies

### Step 2g: Background Modes and Extensions

Scan for:

**Background Modes** (in Info.plist UIBackgroundModes):
- audio — playing audio in background
- fetch — periodic background fetch
- location — continuous location tracking
- voip — VoIP/calling app
- remote-notification — silent push notifications
- bluetooth-central/peripheral — BLE accessory connection
- nfc — NFC tag reading
- background-processing — iOS 13+ background processing tasks

**App Extensions:**
- Search for extension targets (Today Widget, Share Extension, Watch App, etc.)
- Record: Type and purpose of each extension

### Step 2h: Third-Party SDKs

From Podfile/Package.swift and code imports, catalog all third-party SDKs:

**Analytics SDKs** (check if present):
- Firebase Analytics, Amplitude, Mixpanel, AppsFlyer, Segment, etc.
- Record: Which ones are used

**Ad Networks** (especially important for Kids Category):
- Google Mobile Ads, Facebook Audience Network, AdMob, AppLovin, Unity Ads, etc.
- Record: Which ones and their versions

**Crash Reporting:**
- Sentry, Bugsnag, Firebase Crashlytics, Instabug, etc.
- Record: Which service is used

**Social Login SDKs:**
- Facebook SDK, Google Sign-In, Twitter, LinkedIn, etc.
- Record: Versions and scope of permissions requested

**Payment SDKs:**
- Stripe, PayPal, Square, Braintree, etc. (for non-IAP payments)
- Record: Which payment methods are supported

**AI Services:**
- SDKs or endpoints for OpenAI, Anthropic, Google Gemini or Vertex AI, and other hosted models (hosts such as `api.openai.com`, `api.anthropic.com`, `generativelanguage.googleapis.com`)
- Record: Provider, file:line, what user data is sent, and the file:line of any disclosure and opt-in shown before the first request

**Remote Config and Feature Flags:**
- Firebase Remote Config, LaunchDarkly, Statsig, Optimizely, ConfigCat, or a homegrown flag endpoint
- Record: Each flag that turns a user-facing feature on or off, with file:line and the feature it gates

**Other Popular SDKs:**
- Video streaming (YouTube, Vimeo, Twitch), mapping (Google Maps, Mapbox), chat/messaging libraries, etc.

### Step 2i: Network and Data Handling

Scan for:

**Network Calls:**
- Look for: Hardcoded IPv4 addresses, HTTP (non-HTTPS) URLs
- Record: Whether HTTP is used anywhere (should be HTTPS only)
- Check for: API endpoints in code, authentication headers

**Data Transmission:**
- Look for: Personal data being sent in logs, crash reports, or analytics
- Check for: Encryption of sensitive data in transit and at rest

**Keychain Usage:**
- Import: `import Security` or `#import <Security/Security.h>`
- Classes: `SecItem`, keychain queries
- Record: Whether sensitive data is stored securely

### Step 2j: Review Prompts

- Look for: `SKStoreReviewController`, `AppStore.requestReview`, SwiftUI `requestReview`
- Look for: Custom rating dialogs ("Rate us", star pickers, "Enjoying the app?" alerts)
- Record: file:line for each

## Phase 3: Build the app-profile.json

Create a JSON file with this structure:

```json
{
  "app_name": "string — extracted from Info.plist or Xcode project",
  "bundle_identifier": "string — from Info.plist CFBundleIdentifier",
  "min_deployment_target": "string — e.g. 'iOS 13.0'",
  "platforms": ["iOS", "macOS", "tvOS", "visionOS"],
  "targets": [
    {
      "name": "string",
      "type": "app|framework|extension|widget",
      "minimum_os": "string"
    }
  ],

  "app_classification": {
    "category": "game|media|social|productivity|utility|business|education|health|finance|other",
    "has_iap": boolean,
    "has_subscriptions": boolean,
    "has_external_payment": boolean,
    "has_user_accounts": boolean,
    "has_user_generated_content": boolean,
    "has_social_features": boolean,
    "is_kids_category": boolean,
    "is_medical_app": boolean,
    "is_regulated_category": "finance|gambling|health|cannabis|air_travel|crypto|vpn|mdm|none"
  },

  "permissions_declared": {
    "location": {
      "when_in_use": boolean,
      "always": boolean,
      "background_needed": boolean
    },
    "camera": boolean,
    "microphone": boolean,
    "photos": boolean,
    "contacts": boolean,
    "calendar": boolean,
    "reminders": boolean,
    "health": {
      "read": boolean,
      "write": boolean,
      "data_types": ["string"]
    },
    "homekit": boolean,
    "bluetooth": {
      "central": boolean,
      "peripheral": boolean
    },
    "nfc": boolean,
    "siri": boolean,
    "tracking": {
      "idfa_requested": boolean,
      "att_implemented": boolean
    }
  },

  "permissions_used_in_code": {
    "location": {
      "found": boolean,
      "usage_description": "string — what the app actually does with location"
    },
    "camera": {
      "found": boolean,
      "usage": "string — photo capture, video, face detection, etc."
    },
    "microphone": {
      "found": boolean,
      "usage": "string"
    },
    "photos": {
      "found": boolean,
      "usage": "string"
    },
    "contacts": {
      "found": boolean,
      "usage": "string"
    },
    "calendar": {
      "found": boolean,
      "usage": "string — read or write"
    },
    "reminders": {
      "found": boolean,
      "usage": "string"
    },
    "health": {
      "found": boolean,
      "data_types": ["string"]
    },
    "homekit": {
      "found": boolean,
      "usage": "string"
    },
    "bluetooth": {
      "found": boolean,
      "usage": "string"
    },
    "nfc": {
      "found": boolean,
      "usage": "string"
    },
    "tracking": {
      "idfa_used": boolean,
      "att_dialog_shown": boolean
    }
  },

  "entitlements": [
    "string — list of all entitlement keys found"
  ],

  "background_modes": [
    "string — list of UIBackgroundModes"
  ],

  "in_app_purchase": {
    "implemented": boolean,
    "storekit_version": "1|2|both|none",
    "product_types": ["consumable|non_consumable|auto_renewable|non_renewing|unknown"],
    "restore_purchases_implemented": boolean,
    "subscription_groups_found": ["string"],
    "external_payment_links_found": boolean,
    "external_purchase_ctas": [
      {
        "location": "string — file:line",
        "destination": "string — URL or screen",
        "gating": "us_storefront_check|entitlement|none"
      }
    ],
    "storefronts": "us_only|includes_non_us|unknown"
  },

  "account_system": {
    "has_login": boolean,
    "account_creation_supported": boolean,
    "sign_in_with_apple": boolean,
    "third_party_login": ["string"],
    "third_party_login_scope": "primary_account|service_client|none",
    "other_login_options": ["string — email/password, passkey, other providers"],
    "account_deletion_implemented": boolean,
    "account_deletion_visible": boolean,
    "demo_mode_available": boolean
  },

  "user_generated_content": {
    "accepts_ugc": boolean,
    "ugc_types": ["string — text, images, videos, files, etc."],
    "ai_generated_content": boolean,
    "random_or_anonymous_chat": boolean,
    "moderation_system": boolean,
    "reporting_system": boolean,
    "blocking_system": boolean
  },

  "third_party_ai": {
    "providers": ["string — SDK or endpoint host, with file:line"],
    "user_data_sent": "string — e.g. journal text, photos of people",
    "disclosure_and_opt_in": "string — file:line shown before the first request, or null"
  },

  "feature_flags": ["string — flag name, file:line, and the feature it gates"],

  "review_prompt": {
    "system_api": "string — file:line, or null",
    "custom_prompt": "string — file:line, or null"
  },

  "push_notifications": {
    "implemented": boolean,
    "registration_required": boolean,
    "used_for_marketing": boolean,
    "used_for_transactional": boolean
  },

  "web_views": [
    {
      "type": "WKWebView|UIWebView",
      "location": "string — filename or feature name",
      "content_type": "local|remote",
      "deprecated": boolean
    }
  ],

  "extensions_and_widgets": [
    {
      "type": "widget|share|notification-content|intent|iMessage|keyboard|watch|etc.",
      "name": "string"
    }
  ],

  "third_party_sdks": {
    "analytics": ["string"],
    "advertising": ["string"],
    "crash_reporting": ["string"],
    "social_login": ["string"],
    "payment_processors": ["string"],
    "video_streaming": ["string"],
    "other": ["string"]
  },

  "network_and_security": {
    "uses_https_only": boolean,
    "hardcoded_ipv4_found": boolean,
    "uses_keychain": boolean,
    "certificate_pinning": boolean
  },

  "metadata": {
    "description_text": "string — truncated app description from Fastlane or metadata",
    "privacy_policy_url": "string or null",
    "support_url": "string or null",
    "marketing_url": "string or null",
    "age_rating_available": boolean,
    "screenshots_present": boolean,
    "preview_video_present": boolean
  },

  "findings": {
    "missing_privacy_descriptions": ["string"],
    "declared_but_unused_permissions": ["string"],
    "used_but_not_declared_permissions": ["string"],
    "deprecated_apis": ["string"],
    "suspicious_patterns": ["string"]
  }
}
```

## Phase 4: Document Findings and Caveats

As you build the profile, if you find anything unexpected or suspicious, add notes to `findings.suspicious_patterns` such as:

- "Location permission declared but no usage found in code"
- "UIWebView deprecated API usage detected in ViewController.swift"
- "External payment SDK (Stripe) found but no IAP implementation"
- "Third-party analytics SDK imported but ATT not requested"
- "Account deletion UI not found in code, but app has user accounts"
- "User journal text sent to api.openai.com in SummaryService.swift:31; no disclosure or opt-in screen found"
- "Remote flag `enable_live_bets` in FeatureFlags.swift:12 gates a betting tab the description doesn't mention"

These will be important for the Guideline Auditor to investigate.

## Important Notes

1. **Be precise**: Use exact file paths and class names. Don't approximate.
2. **Don't judge**: If a permission is declared but the code is unclear, record both — let the auditor decide.
3. **Handle missing files gracefully**: If Podfile doesn't exist, record "N/A — no package manager found". If no entitlements file exists, record empty array.
4. **Search broadly for source code**: Include .swift, .m, .h files, and check inside targets/extensions. Don't assume all code is in the main app target.
5. **Metadata parsing**: If Fastlane metadata doesn't exist, check the Xcode project for embedded metadata like App Store description.
6. **SDK versions matter**: Record SDK versions when detectable (from Podfile.lock or package version declarations) for security checks later.

## Output Checklist

Before writing app-profile.json, verify:
- [ ] Project structure identified (Xcode, pbxproj, targets)
- [ ] All Info.plist files read
- [ ] Entitlements file parsed (if exists)
- [ ] Dependencies catalog complete (Podfile, Package.swift, Cartfile)
- [ ] Source code scanned for usage patterns
- [ ] Fastlane metadata read (if exists)
- [ ] app-profile.json written to workspace with all required fields
- [ ] Suspicious patterns documented in findings section
- [ ] No guidelines applied — purely factual inventory
