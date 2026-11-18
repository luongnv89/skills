# Companion Pages

The pages a full landing page links to from its footer: Privacy Policy, Terms of Use,
Changelog, and Docs. `SKILL.md` → *Companion Pages* decides which pages apply. This file
holds the sources, the delivery rules, one template per page, and the companion checks.
Read only the sections for the pages that apply, to save context budget.

Contents: [Sources and gap markers](#sources-and-gap-markers) · [Delivery](#delivery) ·
[Privacy Policy](#privacy-policy) · [Terms of Use](#terms-of-use) ·
[Changelog](#changelog) · [Docs](#docs) · [Companion checks](#companion-checks)

## Sources and gap markers

Take every fact on a companion page from a source: the brief, the user's answers, or, when
the brief is a project README, a project file. For each fact without a source, write the gap
marker `[proof needed — <missing fact>]`. Never fill a gap with a typical value, such as a
30-day retention period, a refund window, a release date, or an install command. A product
category is not a data practice: "self-hosted", "open-source", or "local-first" never supports
"collects no data" or "your data stays on your servers". Write such a claim only when the user
states it.

| Page | Facts it needs | Project sources (README brief) |
|---|---|---|
| Privacy Policy | Data collected, purpose, processors and third parties, cookies or analytics, retention, user requests, contact, effective date | Manifests and lockfiles, outbound network calls in source, existing privacy text |
| Terms of Use | Legal entity, plans and billing, trial and cancellation terms, refunds, acceptable use, governing law, contact | Existing terms, pricing in the README or site |
| Changelog | Versions, release dates, user-visible changes | The history file, git tags and their dates, the manifest version |
| Docs | Requirements, install commands, configuration keys, commands and flags, documented failures | README install and usage sections, `docs/`, manifest `bin`/`scripts`/`engines`, argument definitions and config readers in source, `.env.example` |

Privacy evidence, when the brief is a project README:

1. Search the manifests and lockfiles for analytics, telemetry, and crash-reporting packages (for example Sentry, PostHog, Segment, Mixpanel, Amplitude, Google Analytics).
2. Search the source for outbound network calls (`fetch(`, `https.request`, `axios`, `requests.`, `http.Client`) and for environment variables that turn telemetry off.
3. Record each hit as `path:line` with what it sends.
4. If the searches find nothing, put "no data collection found in the source" on the Final Report's `Uncertainty:` line. Write a gap marker on the page, not "collects no data": finding nothing is not proof. Write the claim only after the user confirms it.

## Delivery

Each delivered page goes to a copy block in chat after the landing copy's OPTIMIZATION NOTES,
opened by the COMPANION PAGES block below. No page copy is written to a project file; Step 7
builds the HTML pages from these copy blocks. When the brief is a project README and the project
already has such a page (for example `CHANGELOG.md`), read it as a source and leave it unchanged.

When at least one page is delivered, open the companion pages with this block. When every page is skipped, write no block:

```
COMPANION PAGES
Footer links: [each delivered page, in this order: Privacy Policy · Terms of Use · Changelog · Docs]
Skipped: [page] — [reason from the Companion Pages table]
```

## Privacy Policy

Write plain language a customer can read in five minutes. State each practice a source
supports, and name each processor. Do not claim compliance with GDPR, CCPA, HIPAA, or
another regulation, a security guarantee, or a no-sale promise unless the user supplied
the claim. Add a section for EU, UK, or California residents only when the user names
those users or regions.

```
PRIVACY POLICY
Product/Service: [Name]
Effective date: [date]

Summary: [2–3 sentences: what is collected, why, and who receives it]

1. Information we collect: [each category, and whether the user provides it, the product collects it automatically, or a third party supplies it]
2. How we use it: [each purpose, tied to a category]
3. Cookies and analytics: [each tool by name]
4. Sharing and processors: [each processor and the reason]
5. Retention: [period per category]
6. Your choices: [access, correction, deletion, export, opt-out, and how to make a request]
7. Children: [minimum age]
8. Changes to this policy: [how users are notified]
9. Contact: [contact channel]
```

## Terms of Use

Write only the terms a source supports. Take prices, billing cycles, trial conversion,
and refunds from the pricing facts alone. Write a standard warranty disclaimer and
liability limit, and use a gap marker for every amount, period, and jurisdiction the
user did not supply.

```
TERMS OF USE
Product/Service: [Name]
Effective date: [date]

1. Agreement: [legal entity that offers the product]
2. Accounts: [eligibility and account responsibilities]
3. Plans, billing, and trials: [plans, prices, billing cycle, trial conversion]
4. Cancellation and refunds: [how to cancel; refund terms]
5. Acceptable use: [prohibited uses]
6. Your content: [ownership, and the license the product needs to run; only when the product stores user content]
7. Termination: [when either party can end the agreement]
8. Disclaimers and liability: [warranty disclaimer and liability limit]
9. Governing law: [jurisdiction]
10. Changes and contact: [how changes are announced; contact channel]
```

## Changelog

Write for the people who use the product, newest release first. Group each release under
**New**, **Improved**, **Fixed**, and **Action needed**, and omit empty groups. Write one
plain-language sentence per item, benefit first. Leave out commit hashes, PR or issue
numbers, author handles, conventional-commit prefixes, and file paths. These groups match
the end-user notes of the `ship` skill, so a later release can be added at the top.

```
CHANGELOG
Product/Service: [Name]

[Version] — [Date]
New
• [What the user can now do]
Improved
• [What works better]
Fixed
• [What now works]
Action needed
• [The step the user must take]
```

- Release history supplied: write one entry per release, at most the five most recent. Link older releases when a releases or tags URL is known.
- No release history: write one entry. Use the version and date from the brief, or gap markers. List the brief's features under **New** only when the brief says this is the first release; otherwise the entry's items are one gap marker.

## Docs

The Docs page takes a new user from nothing to a first working result. Omit a section
only when the product has nothing for it.

```
DOCS: GETTING STARTED
Product/Service: [Name]

Requirements: [OS, runtime and version, accounts or keys]
Install: [one install command per line]
Configure: [each setting: name, effect, default, where it is set]
First run: [the shortest command or action sequence to a working result, with the expected output]
Commands: [command or flag — what it does] (CLI only)
Troubleshooting: [symptom — fix] (documented failures only)
Uninstall: [command or steps]
```

- Take every command (install, run, upgrade, uninstall) from the README, existing docs, or the user. Never derive one from a package name or another command: the package may be unpublished.
- Take each flag and configuration key from the brief, or, when the brief is a project README, from the argument definitions and config readers in source. A flag the source defines but the README omits belongs on the page.
- Write Troubleshooting entries only for failures the project documents or the user supplies.

## Companion checks

Run these checks on every page the run delivers. Fix each failure before delivery. A failure
that cannot be fixed makes the run `PARTIAL` (`references/final-report.md`).

| Check | Pass when |
|---|---|
| Pages decided | Each of the four pages is recorded as delivered or skipped with its reason |
| Facts traced | Each data practice, legal term, version, date, command, flag, and setting traces to the brief, the user's answers, or a project file; every other fact is a gap marker |
| No compliance claims | No page claims regulatory compliance, a security guarantee, or a no-sale promise the user did not supply |
| Footer links | The COMPANION PAGES block lists every delivered page. A companion page delivered alone: the run names the footer link it needs |
| Changelog style | Newest release first; each release has a version and a date or a gap marker; no hashes, PR or issue numbers, or author handles |
| Docs commands | Each command comes from a source |
| Nothing overwritten | No existing project file was modified, `README.md` included |
| Anti-slop | The page passes `references/anti-slop-rules.md` |
