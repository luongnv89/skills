# Don't Make Me Think — Core Principles Reference

This is a deep reference for the usability principles from Steve Krug's "Don't Make Me Think." Consult this when you need detailed guidance on a specific principle during a review.

## Table of Contents
1. [The First Law: Don't Make Me Think](#1-the-first-law)
2. [How We Really Use the Web: Scanning](#2-scanning)
3. [Billboard Design 101: Visual Hierarchy](#3-visual-hierarchy)
4. [Omit Needless Words](#4-omit-needless-words)
5. [Navigation and Wayfinding](#5-navigation)
6. [The Trunk Test](#6-trunk-test)
7. [The Home Page](#7-home-page)
8. [Usability and Accessibility](#8-accessibility)
9. [Mobile Usability](#9-mobile)
10. [Goodwill and the Reservoir](#10-goodwill)

---

## 1. The First Law: Don't Make Me Think {#1-the-first-law}

The fundamental principle: every page or screen should be self-evident. When a user looks at it, they should "get it" — what it is and how to use it — without having to spend effort figuring it out.

**What "thinking" looks like in practice:**
- "Where am I?"
- "Where should I start?"
- "Where did they put ___?"
- "What are the most important things on this page?"
- "Why did they call it that?"
- "Is that a button or just decoration?"
- "Can I click on that?"

**The test:** If something requires the user to stop and puzzle over it — even for a fraction of a second — it violates this principle.

**Common violations:**
- Clever or cute names instead of clear ones (e.g., "Explore the Universe" instead of "Browse Products")
- Non-standard link/button styling that leaves users unsure what's clickable
- Layout that doesn't communicate structure or priority
- Instructions that need to be read to understand the interface (if you need instructions, the design has failed)

---

## 2. How We Really Use the Web: Scanning {#2-scanning}

Users don't read pages. They scan them. They're on a mission, moving fast, and they'll latch onto whatever seems closest to what they're looking for.

**Three facts about real-world web use:**
1. **We don't read, we scan.** Users pick out words, phrases, and images that catch their eye. They skip over everything else.
2. **We don't make optimal choices, we satisfice.** Users don't pick the best option — they pick the first reasonable one. "Good enough" wins over "best."
3. **We don't figure out how things work, we muddle through.** Users rarely read instructions. They just try things and see what happens.

**Design implications:**
- Make the scan path obvious — the eye should flow naturally to what matters
- The first plausible option should be the right one (or close to it)
- Don't rely on users reading explanatory text — they won't
- Use the words users are already looking for (match their mental model)

---

## 3. Billboard Design 101: Visual Hierarchy {#3-visual-hierarchy}

Since users scan, the visual hierarchy is everything. It tells users what's important, what's related, and what's nested inside what — all at a glance.

**Three principles of visual hierarchy:**
1. **The more important something is, the more prominent it is.** Bigger, bolder, distinctive color, more whitespace, nearer the top.
2. **Things that are related are grouped visually.** Proximity, shared backgrounds, borders, similar styling — these signal "these go together."
3. **Things that are nested are visually contained.** Indentation, enclosure, and typographic hierarchy show parent-child relationships.

**Making pages scannable:**
- Create clear visual regions (header, nav, content, sidebar, footer)
- Use headings generously — they act as signposts during scanning
- Keep paragraphs short (nobody reads long blocks online)
- Use bulleted lists whenever you have a list of items
- Highlight key terms so scanners can find them
- Eliminate visual noise — busy backgrounds, too many colors, gratuitous decoration

---

## 4. Omit Needless Words {#4-omit-needless-words}

Krug's Third Law of Usability: Get rid of half the words on each page, then get rid of half of what's left.

**Two types of words to kill:**
1. **Happy talk** — Introductory text that says nothing useful. "Welcome to our award-winning platform where we strive to deliver the best possible experience..." Nobody reads this. Kill it.
2. **Instructions** — If the design requires instructions, the design is broken. But if you must include them, make them ruthlessly brief.

**Why fewer words is more:**
- Reduces noise on the page, making useful content more visible
- Shortens pages, reducing the need to scroll
- Gives every remaining word more power and visibility

**The test:** For every word on the page, ask: "Does removing this hurt?" If the answer is no, remove it.

---

## 5. Navigation and Wayfinding {#5-navigation}

Navigation serves two purposes: it helps users find what they're looking for, and it tells them where they are.

**Navigation conventions that work:**
- **Persistent navigation** — Site ID (logo), main sections, utilities (search, help, login), and a "you are here" indicator. These should be on every page in the same place.
- **Breadcrumbs** — Show the path. Use > as separator. Bold the current page. Put them at the top. Don't make them too big (they're secondary navigation).
- **Page names** — Every page needs one. It should match what the user clicked to get there. It should be prominent and frame the content.

**Navigation tab design (Krug's favorite):**
- Active tab is clearly connected to the content (different color, no bottom border)
- Inactive tabs are visually distinct from the active one
- The tabs look like physical tabs

**Search:**
- Simple box, no fancy options by default
- A button labeled "Search" (not "Go" or "Find" or "Quick Search")
- Keep it visible on every page

---

## 6. The Trunk Test {#6-trunk-test}

Imagine being blindfolded, driven around, and dropped on a random page of a website. Can you answer these questions?

1. **What site is this?** (Site ID / logo)
2. **What page am I on?** (Page name)
3. **What are the major sections?** (Primary navigation)
4. **What are my options at this level?** (Local navigation)
5. **Where am I in the scheme of things?** ("You are here" indicators)
6. **How can I search?** (Search box)

If a page can't answer all six, it has navigation problems.

---

## 7. The Home Page {#7-home-page}

The home page has special responsibilities that no other page has. It must simultaneously:

1. **Site identity and mission** — What is this site? What does it do? Why should I be here and not somewhere else?
2. **Site hierarchy** — What can I find here? (Content and features)
3. **Teasers** — Content highlights to entice deeper exploration
4. **Timely content** — Signs of life, freshness
5. **Deals and promotions** — If relevant
6. **Shortcuts** — Frequently requested content
7. **Registration/login** — If needed

**The tagline test:** Can a new visitor describe what your site does in one sentence after seeing the home page for 5 seconds? If not, the home page isn't doing its job.

A good tagline is:
- Clear and informative (not clever or cute)
- 6-8 words
- Conveys differentiation
- Not a mission statement or motto

---

## 8. Usability and Accessibility {#8-accessibility}

Accessibility is not separate from usability — it's the same thing applied more broadly. Making a site accessible almost always makes it more usable for everyone.

**Key overlap:**
- Clear headings help screen readers AND scanning users
- Good contrast helps low-vision users AND everyone in bright sunlight
- Keyboard navigation helps motor-impaired users AND power users
- Simple language helps cognitive disabilities AND ESL users AND busy people

**Minimum bar:**
- Add alt text to every meaningful image
- Use real headings (h1-h6), not just big bold text
- Ensure sufficient color contrast
- Make all functionality keyboard-accessible
- Don't rely on color alone to convey meaning

---

## 9. Mobile Usability {#9-mobile}

Mobile isn't just "smaller" — it changes how people use interfaces. But the core principle is the same: don't make them think.

**Mobile-specific concerns:**
- **Affordances** — Touch targets must be big enough (44px minimum). It must be clear what's tappable.
- **Memorability** — Users often can't see the full page, so they must remember what's above/below the fold. Reduce memory load.
- **Tradeoffs** — Mobile forces prioritization. You can't show everything, so you must decide what matters most. This is actually a useful exercise for desktop too.
- **Gestures** — Swipe, pinch, long-press are invisible. If a gesture is the only way to do something, users may never discover it. Always provide a visible alternative.

---

## 10. Goodwill and the Reservoir {#10-goodwill}

Every user arrives with a reservoir of goodwill. Good experiences fill it; bad experiences drain it. When the reservoir empties, the user leaves — possibly forever.

**Things that drain goodwill:**
- Hiding information users want (phone number, pricing, shipping costs)
- Punishing users for not doing things your way (rigid form validation, error messages that blame them)
- Asking for unnecessary information
- Fake "friendly" polish over a frustrating experience
- Cluttering the interface with ads and cross-promotions
- An unprofessional look that undermines trust

**Things that fill goodwill:**
- Tell users what they want to know up front — be transparent
- Save users steps whenever possible
- Know what questions users are likely to have, and answer them
- Provide graceful error recovery (pre-fill forms, don't lose data)
- When in doubt, apologize (sincerely, not corporate-speak)

---

## Krug's Usability Testing Approach

You don't need expensive labs or large user groups. Krug advocates:

- **Test early and often** — One user in the first week is worth 50 users near launch
- **Three users is enough** — You'll find most of the important problems
- **Watch, don't ask** — Have people try to use it. Don't ask them what they think of it.
- **Focus on the big issues** — Fix the things that affect everyone, not edge cases

**The morning of usability testing:**
1. Give users a realistic task
2. Watch them try to do it
3. Note where they get confused, make wrong choices, or fail
4. Fix the worst problems you see
5. Test again
