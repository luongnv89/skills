# Usability Guide — "Don't Make Me Think" by Steve Krug

Rules for reviewing or creating designs based on Krug's principles. Good design doesn't make users think unnecessarily — everything should be self-evident.

The six Quick rules below apply to every design, regardless of aesthetic direction. This is the same source the `dont-make-me-think` skill audits against, condensed for inline use during generation; keep the two in sync if Krug-principle guidance changes.

## Table of Contents

- [Quick rules](#quick-rules)
- [Quick Reference Checklist](#quick-reference-checklist)

---

## Quick rules

### 1. Design for Scanning, Not Reading
- Users scan pages — they do not read them. Use clear headings, short paragraphs, bullet points, and visual hierarchy (bigger/bolder = more important).
- Highlight keywords. Apply the **billboard rule**: if a user can't grasp the page purpose in 5 seconds, simplify.

### 2. Follow Conventions
- Place navigation at the top, logo upper-left, search top-right. Use familiar icons (magnifying glass for search, hamburger for mobile menu).
- Use straightforward labels: "Books" not "Library Vault". Clicks are fine if each is unambiguous.

### 3. Make Interactions Self-Evident
- Buttons must look clickable (shaded, bordered, with hover states). Links must be visually distinct from body text.
- CTAs name the action and its outcome ("Shop Now", "Start My Free Trial") and are prominently placed. Forms have no unnecessary fields.

### 4. Eliminate Cognitive Load
- Edit ruthlessly — cut half the words, then half again. Use plain language, no jargon.
- Ensure consistency across pages: same button styles, same spacing patterns, same color semantics.
- Design error states gracefully: clear messages with recovery suggestions (e.g., "No results found. Try a broader search.").

### 5. Self-Test Every Design
- Before delivering, simulate user paths: role-play 3-5 task scenarios (e.g., "Find and buy a product"). Record each point of hesitation and fix it before delivery.
- Verify mobile responsiveness — the design must adapt without losing core functionality.

### 6. Accessibility Is Mandatory
- Alt text on all images, WCAG AA contrast (4.5:1 minimum), keyboard navigable.
- Site identity (logo, tagline) visible on every page.

---

## Quick Reference Checklist

Use this during implementation to verify Krug compliance:

- [ ] Page purpose is obvious within 5 seconds
- [ ] Navigation is persistent, conventional, and clearly labeled
- [ ] Site identity (logo, tagline) is visible on every page
- [ ] CTAs are prominent and use action verbs ("Shop Now", not "Click Here")
- [ ] Content is scannable: headings, bullets, highlighted keywords
- [ ] Buttons look clickable; links are distinguishable from text
- [ ] No jargon — plain language throughout
- [ ] Error states are graceful with helpful recovery suggestions
- [ ] Consistent styling across all pages (buttons, colors, spacing)
- [ ] Mobile-responsive with no loss of core functionality
- [ ] Accessibility: alt text, sufficient contrast (WCAG AA), keyboard navigable
