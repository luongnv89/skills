# The 32 Viral Product Principles — Evaluation Rubric

Score every principle as **PASS**, **PARTIAL**, or **FAIL** using the criteria below. Each
entry lists: the principle, what to look at, the concrete check, and the three verdict bars.

**Confidence flag.** Principles marked `⚠ visual` or `⚠ judgment` cannot be fully decided from
markup/code alone. Still give a verdict, but tag it low-confidence in the report and tell the
user what a human needs to eyeball. Everything else is `objective` — decide it from evidence.

**Evidence source** tells you where to look: `LP` = landing page (rendered or markup), `CODE` =
codebase (pricing logic, billing integration, feature surface, routes), `BOTH` = cross-check.

When the evidence is genuinely absent (e.g. no pricing anywhere), that is a real FAIL, not an
"unknown" — a viral product would have shipped it. Only use low-confidence for things that exist
but need a human's taste to judge (design punch, emotional pull, novelty).

---

## A. Pricing & monetization (read CODE first, confirm on LP)

These are the most checkable. Look for billing integrations (Stripe, Paddle, LemonSqueezy,
RevenueCat), pricing config, plan/tier definitions, and the rendered pricing section.

### 1. No free plan — `objective` · `CODE`+`LP`
**Check:** Is there a free tier, free forever plan, or unlimited free usage?
- **PASS** — No free plan. Free trial is fine; "free forever" is not.
- **PARTIAL** — Time-boxed free trial only, or a tiny capped free tier clearly framed as a trial.
- **FAIL** — A standing "Free" plan in pricing, or core value usable indefinitely at no cost.

### 8. Hard paywall — `objective` · `BOTH`
**Check:** Does payment come before account/data collection, or can users get deep in for free?
- **PASS** — Credit card / payment required before the core result is delivered.
- **PARTIAL** — Signup required but no card; value gated later.
- **FAIL** — Full value delivered with no payment ask anywhere.

### 12. Popcorn Pricing (max 3 tiers) — `objective` · `LP`
**Check:** Count the pricing tiers. A single fixed price (one SKU, one-time or flat) is the
cleanest possible case — it is a **PASS**, not a miss; there is no decision to simplify.
- **PASS** — 1–3 tiers (Good / Better / Best), **or** a single fixed price / one SKU.
- **PARTIAL** — 4 tiers.
- **FAIL** — 5+ tiers, or a configurator/spreadsheet-style pricing matrix.

### 16. Pricing impossible to miss — `objective` · `LP`
**Check:** Is "Pricing" a top-nav/header link, and is the pricing section easy to reach?
- **PASS** — "Pricing" in the header nav AND a clear pricing section on the page.
- **PARTIAL** — Pricing section exists but not linked from the header.
- **FAIL** — No discoverable pricing, or "contact us" only.

### 27. No subscription — `objective` · `CODE`+`LP`
**Check:** Is billing one-time, or recurring monthly/annual?
- **PASS** — One-time / lifetime payment is the primary offer.
- **PARTIAL** — Subscription primary but a lifetime/one-time option is offered.
- **FAIL** — Subscription-only (monthly/annual) with no one-time path.

### 32. Priced above competitors — `judgment` · `BOTH`
**Check:** Compare the headline price to named competitors (research if not stated).
- **PASS** — Priced at or above the category's typical/premium price; not the cheapest.
- **PARTIAL** — Middle of the pack.
- **FAIL** — Positioned as "the cheap option" or visibly the lowest price.

---

## B. Hero & headline (read LP)

The hero is the top of the page before any scroll. Most virality lives here.

### 20. Sellable from the hero alone — `judgment` · `LP`
**Check:** From the hero (headline + sub + CTA + visual) alone, is it clear what this is, who
it's for, and why to want it?
- **PASS** — A stranger understands and wants it from the hero with zero scrolling.
- **PARTIAL** — Understandable but not compelling, or needs one scroll to "get it".
- **FAIL** — Hero is a logo + vague tagline, or a feature dump that explains nothing.

### 7. Headline a fifth-grader understands — `objective` · `LP`
**Check:** Reading level / jargon count in the main headline.
- **PASS** — Plain words, no jargon, ~fifth-grade reading level.
- **PARTIAL** — One piece of jargon or a slightly abstract phrase.
- **FAIL** — Buzzword soup ("AI-powered synergy platform"), unparseable by a layperson.

### 18. Emotional headline — `judgment` · `LP`
**Check:** Does the headline make you laugh, say "wow", or "what is this"?
- **PASS** — Clear emotional hook (humor, awe, intrigue, pain).
- **PARTIAL** — Mildly interesting but flat.
- **FAIL** — Pure description of the feature, zero feeling.

### 17. Memorable-next-day headline — `judgment` · `LP`
**Check:** Is the headline sticky — short, concrete, surprising enough to repeat tomorrow?
- **PASS** — Short, vivid, repeatable.
- **PARTIAL** — Fine but forgettable.
- **FAIL** — Long, generic, or a feature list masquerading as a headline.

### 3. Numbers instead of adjectives — `objective` · `LP`
**Check:** Does the hero/value copy use specific numbers vs vague adjectives?
- **PASS** — Concrete numbers ("Save 4 hours every week", "Ship in 30 seconds").
- **PARTIAL** — Mix of one number and several adjectives.
- **FAIL** — Adjective-only ("fast", "powerful", "seamless"), no numbers.

### 24. Sells a human desire, not a feature — `judgment` · `LP`
**Check:** Does the top copy sell an outcome (money, time, health, status, less pain) or a feature?
- **PASS** — Leads with the outcome; features are vehicles.
- **PARTIAL** — Outcome present but buried under feature talk.
- **FAIL** — Feature/spec list with no human payoff.

---

## C. Message clarity & focus (read BOTH)

### 11. Does one thing — `judgment` · `BOTH`
**Check:** Does the product (per LP claims and CODE surface area) do one clear thing?
- **PASS** — One job, stated once, reflected in a focused feature set.
- **PARTIAL** — One primary thing plus a couple of bolt-ons that blur the message.
- **FAIL** — Swiss-army-knife positioning; many unrelated features competing for attention.

### 30. Describable in under 10 words — `objective` · `LP`
**Check:** Is there a ≤10-word description of what it is? (Often the meta description, tagline, or
the first sentence.) Count the words of the clearest one-liner.
- **PASS** — A crisp ≤10-word description exists and is prominent.
- **PARTIAL** — Exists but is 11–15 words or buried.
- **FAIL** — No single-sentence description; takes a paragraph to explain.

### 6. One idea per screen — `judgment` · `LP`
**Check:** Does each section/screen communicate exactly one idea?
- **PASS** — Each section = one message, clean rhythm.
- **PARTIAL** — Mostly, but 1–2 sections cram multiple ideas.
- **FAIL** — Walls of mixed messaging; no one-idea-per-screen structure.

### 22. One call to action — `objective` · `LP`
**Check:** Count distinct CTA *types*. Repeating the SAME CTA down the page is good; competing
CTAs ("Buy" vs "Book a demo" vs "Join Discord" vs "Read docs") is the failure.
- **PASS** — One primary CTA, repeated. No competing primary actions.
- **PARTIAL** — One primary plus one secondary (e.g. a quiet "docs" link).
- **FAIL** — Multiple competing primary CTAs of equal weight.

### 28. CTA says what happens next — `objective` · `LP`
**Check:** Does the primary CTA describe the action, not "Get Started"/"Sign up"?
- **PASS** — Action-specific ("Analyze My Website", "Generate My Logo").
- **PARTIAL** — Slightly specific ("Start free trial").
- **FAIL** — Generic ("Get Started", "Sign up", "Learn more", "Submit").

---

## D. Proof & differentiation (read BOTH)

### 21. Empathy before selling — `judgment` · `LP`
**Check:** Is there a problem/empathy section before the pitch that names the pain precisely?
- **PASS** — Clear problem framing that nails the reader's pain before the solution.
- **PARTIAL** — A token problem line, then straight to features.
- **FAIL** — Jumps to selling with no problem framing.

### 9. Copy only you could write — `judgment` · `LP`
**Check:** Could a competitor paste this copy onto their site unchanged? Look for specific,
experience-based detail vs interchangeable boilerplate.
- **PASS** — Copy is specific, opinionated, clearly from lived experience.
- **PARTIAL** — Some specific lines amid generic ones.
- **FAIL** — Entirely interchangeable SaaS boilerplate.

### 14. Steals copy from customers — `judgment` · `LP`
**Check:** Does the copy use real customer language (verbatim phrases, quotes feeding the copy)?
- **PASS** — Copy mirrors how customers actually talk; voice-of-customer present.
- **PARTIAL** — Some customer phrasing, mostly founder/marketer voice.
- **FAIL** — Pure corporate-speak, no customer voice.

### 26. No weak words — `objective` · `LP`
**Check:** Scan for hedges: "most", "many", "rarely", "often", "some", "usually", "can help",
"may", "up to".
- **PASS** — Strong, falsifiable claims; no hedging.
- **PARTIAL** — One or two hedge words.
- **FAIL** — Pervasive weak/hedge language.

### 29. Has testimonials — `objective` · `LP`
**Check:** Are there testimonials / social proof (named quotes, logos, ratings, user counts)?
- **PASS** — Real testimonials with names/handles/photos, or strong proof (counts, logos).
- **PARTIAL** — Generic or anonymous quotes, or thin proof.
- **FAIL** — No testimonials or social proof at all.

### 31. Compares to competitors — `objective` · `LP`
**Check:** Is there a comparison table / "vs" section making the switch obvious?
- **PASS** — Clear comparison table against named alternatives.
- **PARTIAL** — Mentions alternatives in prose without a table.
- **FAIL** — No comparison; reader can't see why to switch.

### 19. Does something never seen before — `judgment` · `BOTH`
**Check:** Is there a genuinely novel mechanic/experience, or is it another clone?
- **PASS** — A clear "I haven't seen this" element.
- **PARTIAL** — Familiar category with one fresh twist.
- **FAIL** — Indistinguishable clone of existing products.

---

## E. Show, don't tell (read BOTH)

### 10. Shows product before explaining — `objective` · `LP`
**Check:** Does a demo/screenshot/video appear at or near the top, before paragraphs of text?
- **PASS** — Visual demo (screenshot, GIF, video, live widget) high on the page.
- **PARTIAL** — A demo exists but appears below lots of text.
- **FAIL** — No product visual; text-only explanation.

### 25. Try before buying — `objective` · `BOTH`
**Check:** Can the visitor experience real value on the page (interactive demo, sample output,
playground) without paying?
- **PASS** — A working interactive demo or real sample output on the landing page.
- **PARTIAL** — A static preview or canned screenshots only.
- **FAIL** — Everything hidden behind signup/paywall; nothing to try.

### 15. Founder you can see and hear — `judgment` · `LP`
**Check:** Is there a founder video / Loom / face / personal voice (not a corporate promo)?
- **PASS** — Founder video or clearly personal founder presence.
- **PARTIAL** — A founder name/photo but no video or voice.
- **FAIL** — Faceless corporate page.

---

## F. Visual & shareability (read LP — often `⚠ visual`)

### 2. Three colors — `objective` · `LP`
**Check:** Count the dominant brand colors used for emphasis. Ideal: neutral text, neutral
background, one accent for the primary action.
- **PASS** — ~3 colors: text, background, one accent (CTA).
- **PARTIAL** — 4 colors, or an accent used in too many places.
- **FAIL** — Rainbow palette; many competing accent colors.

### 4. Shareable footer — `judgment` · `LP`
**Check:** Does the page end on something memorable/shareable (strong line, bold CTA, identity),
not just legal links?
- **PASS** — A strong closing moment that invites sharing.
- **PARTIAL** — A normal footer with a CTA but nothing memorable.
- **FAIL** — Bare legal/links footer; weak ending.

### 5. OG image like a YouTube thumbnail — `⚠ visual` · `LP`
**Check:** Is there an `og:image` / `twitter:image`, correct size (~1200×630), and does it read
like a punchy thumbnail (big text, one idea) rather than a bland logo?
- **PASS** — OG image present, correctly sized, thumbnail-grade punch.
- **PARTIAL** — Present but bland/logo-only, or wrong size. *(Markup confirms presence; punch needs eyes.)*
- **FAIL** — No `og:image` at all.

### 23. Memorable name — `judgment` · `BOTH`
**Check:** Is the product name made of known words, easy to say/spell, no explanation needed?
- **PASS** — Simple, pronounceable, memorable name.
- **PARTIAL** — Slightly awkward spelling or mild wordplay.
- **FAIL** — Invented/unpronounceable name that needs explaining.

---

## G. Distribution context (read BOTH — `judgment`)

### 13. Rides a wave — `judgment` · `BOTH`
**Check:** Is it built around a current trend/technology/problem people already discuss (per
positioning and the actual stack/feature set)?
- **PASS** — Clearly riding a live wave (a hot technology, a trending problem).
- **PARTIAL** — Adjacent to a trend but not leaning into it.
- **FAIL** — No connection to any current momentum; swimming alone.

---

## Scoring

Map verdicts to points, then sum and normalize to 100:

- **PASS = 1.0**, **PARTIAL = 0.5**, **FAIL = 0.0**
- `Virality Score = round( (sum of points / 32) × 100 )`

**Count mechanically — do not tally by hand.** Hand-counting 32 items is error-prone. After
assigning all verdicts, list the principle numbers under each bucket (PASS / PARTIAL / FAIL),
assert the three lists cover all 32 with no overlap, then compute the score from the bucket
sizes. If you have a code tool available, count with it; otherwise write the three explicit
lists and verify `len(PASS)+len(PARTIAL)+len(FAIL) == 32` before computing. State the final
`PASS:n / PARTIAL:n / FAIL:n` and the arithmetic once, and don't show scratch recounts in the
report.

Tiers:
- **85–100 — Viral-ready.** Sharp positioning; tune the long tail.
- **65–84 — Promising.** Strong bones, a few high-impact gaps.
- **40–64 — Needs work.** Core virality levers (hero, paywall, proof) are leaking.
- **0–39 — Not viral yet.** Rework positioning and monetization before traffic.

When the user gives extra instructions (e.g. "we intend to stay subscription", "free tier is
strategic"), still score the principle as written, but note the deliberate deviation in the
report so the score isn't read as an accusation.
