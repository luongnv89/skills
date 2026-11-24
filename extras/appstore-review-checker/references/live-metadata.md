# Live App Store Connect Metadata (optional)

Store copy is often edited directly in App Store Connect, so `fastlane/metadata` or an `AppStoreConnect` folder in the repo can be stale. A pre-submission audit should check the listing App Review will actually see.

## When to offer

Only when `command -v asc` succeeds. Ask once:

> The `asc` CLI is installed. Read the pending version's listing from App Store Connect (read-only) instead of, or in addition to, the repo metadata? If yes, give me the app's App Store Connect ID and the platform (`IOS` or `MAC_OS`), plus the version you are submitting if more than one is in preparation.

Without `asc`, or when the user declines, audit the repo metadata or pasted text as before.

Who asks depends on the mode. In single-conversation mode, the conversation runs the check and asks directly. In subagent mode, the Project Explorer cannot ask the user, so the main conversation runs `command -v asc` and asks **before** spawning it, then passes the answer (approved or declined), the app ID, the platform, and the version being submitted (if the user named one) in the explorer's prompt. The explorer runs the commands below only when that approval was passed in; it never offers or asks on its own.

## Rules

- Prefix every call with `ASC_READ_ONLY=1`. Only the four read commands below; never create, update, or submit anything.
- Never read, print, or pass API key files (`*.p8`), key IDs, or issuer IDs. `asc` uses the auth it already holds.
- If a call fails (not authenticated, unknown app ID), say so in one line, fall back to the repo metadata or pasted text, and continue. Never retry with other credentials.
- `asc validate --strict` is no substitute: it does not check third-party brands.

## Commands

1. `ASC_READ_ONLY=1 asc apps info list --app <app-id>` — while a version is pending, two app infos exist; pick the one whose state is not `READY_FOR_SALE`.
2. `ASC_READ_ONLY=1 asc apps info view --app <app-id> --info-id <info-id> --include appInfoLocalizations` — name and subtitle per locale. Pass `--info-id`: without it the call errors when two app infos exist.
3. `ASC_READ_ONLY=1 asc versions list --app <app-id> --platform <IOS|MAC_OS>` — pick the version being prepared for submission; if more than one is not live, ask which (single-conversation mode). The Project Explorer cannot ask: it takes the version named in its prompt, else the newest one that is not live, and names that version in `metadata.source`.
4. `ASC_READ_ONLY=1 asc localizations list --version <version-id>` — keywords, description, promotionalText, and whatsNew per locale.

## Reporting the source

Fill `metadata.locales` from these results and state the source on the report's `**Metadata source:**` line, for example `App Store Connect (asc, pending version 2.4.0)`. When both the repo and App Store Connect were read, audit the App Store Connect copy and list any field that differs between them as a WARNING under 2.3 (sync the repo copy).
