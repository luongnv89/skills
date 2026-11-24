# Human UX checklist

Review in the stated audience/task context. Name sampled states and untested subchecks.
Use evidence rules; aesthetic opinions and predicted outcomes are hypotheses, not defects.

## Clarity

Check who the product serves, what it does, why it matters, and the next action without
assuming product familiarity. Inspect heading hierarchy, scanning, labels, information
scent, navigation, error/recovery messaging and task completion. Copy fixes must preserve
actual product claims. Validation: a representative user can identify the offering and
complete the primary task; record task, sample and success criteria, not a fictitious test.

## Brand

Compare tone, logo, typography, color, illustration and trust signals across sampled
surfaces and any supplied guidelines, including a design-rules or tokens file recorded in
repo mode. Without guidelines label strategic fit as a
hypothesis, not a breach. Source design tokens can show consistency but not rendered
appearance. Suggest a coherent system rather than a gratuitous trend-driven redesign.
Validation: approved brand tokens/copy rules and visual review of named states.

### Visual-system check

Part of `brand`, never a 13th aspect. Inspect the sampled surfaces and the style sources
in the bundle (stylesheets, tokens or theme files, animation config) for:

- **AI-default tells**: gradients on backgrounds, text, buttons or tiles; colored glow
  (`box-shadow`/`text-shadow` halos); grain or noise overlays; decorative shadows on static
  cards; cards inside cards; icon-in-tinted-circle feature grids; sparkle or emoji icons;
  eyebrow labels above headings; numbered "01 / 02" section labels; Title Case UI text;
  overused fonts (Inter, Roboto, Arial, system stacks, Space Grotesk); cream or off-white
  page backgrounds; italic accent words in headlines; pill-shaped buttons. These are one
  practitioner's defaults, not platform rules.
- **Colour literals outside token files**: hex, `rgb()`, `hsl()` or named colours in
  component rules when the project declares tokens. Cite file:line per distinct value.
- **Type-scale sprawl**: the distinct font sizes, weights and families in use, listed
  against the declared scale.
- **Motion timing read from source**: durations, delays, easing curves and what animates
  on load or scroll, with file:line. Reduced motion stays an accessibility check.
- **Redundant elements**: anything that is not content, a control or a state cue, such as
  icons beside headings, dividers, badges, background shapes, decorative borders, or a
  subtitle restating its heading. Name each one.
- **Competing effects**: two or more emphasis effects on one element or region (gradient
  plus glow plus shadow, several accent colours, badges beside the primary action).

Classify each item. Name the element and the rule, never "looks AI-generated":

| Situation | Finding |
|---|---|
| Breaks a rule in supplied guidelines | `observed` under `brand`, citing the E record of the rule's file:line and the E record of the breach |
| Supplied guidelines or the user's brief ask for the element | No finding |
| No rule covers it and no harm is shown | `hypothesis`, confidence `low`, severity `low`; it never makes `brand` `issues` |
| It causes real harm: contrast below the WCAG minimum, clipped or overlapping text, content hidden by an effect | `observed` under the harmed aspect (`accessibility`, `responsive`) with `related_aspects: ["brand"]`; harm read from source stays source-scoped until rendered |

**Colour schemes.** When the product offers a dark scheme (a `prefers-color-scheme` query,
a `color-scheme` declaration, a theme toggle) or forced-colours styles (`forced-colors:
active`), check each offered scheme: tokens defined for it, literals that bypass it, and
contrast in a render with that scheme emulated. No render leaves that subcheck
not-tested. A scheme the product does not offer is not a finding.

## Responsive

With graphical tools inspect a narrow viewport (e.g. 320/375 CSS px), intermediate and
wide viewport, plus zoom/reflow, text expansion, orientation, touch controls, overflow,
menus and dialogs. Record exact viewports actually tested. Do not claim device testing
from viewport resizing. CSS media queries alone cannot prove layout correctness.
Validation: primary task works without unintended horizontal scrolling at chosen widths;
exceptions such as legitimate data tables are explained.

## Accessibility

Use [WCAG 2.2](https://www.w3.org/TR/WCAG22/) as reference, usually AA unless specified.
Inspect semantic landmarks/headings, labels/names, alt text, keyboard reachability/order,
visible/unobscured focus, error identification, contrast, reduced motion, captions, target
size and status announcements. Cite relevant success criteria for supported findings;
explain exceptions rather than treating every guideline as a blanket pixel rule.
Automated scans cover only a subset; screenshots cannot prove semantics. Do not infer
compliance from a clean scan. Plan manual keyboard + screen-reader checks in key flows.
Validation: reproduce the reported issue and check the exact remediation with appropriate
assistive technology; never certify the whole app from the sample.

## Performance

Record actual timings and test environment. For web use field Core Web Vitals at the 75th
percentile when available: LCP ≤2.5s, INP ≤200ms, CLS ≤0.1 are good thresholds ([source](https://web.dev/articles/vitals)).
A Lighthouse score/lab simulation is not field INP or an actual-user outcome. Investigate
network payload, images/fonts, rendering/hydration, caching and interaction work only with
supporting evidence. Code smells are hypotheses until measured. No measurement means
not-tested plus an instrumentation task. Native metrics use platform-appropriate traces.
Validation: repeat the same lab test/settings; assess field trends with a stated window
and enough traffic. Do not convert a byte saving into invented milliseconds.

## Conversion

Map entry → value → action → completion, including onboarding, forms, checkout and trust.
Check CTA hierarchy, pricing clarity, objection handling, unnecessary data collection,
form errors and recovery, consent, and post-action expectations. Do not submit live forms
or create/purchase anything just to finish an audit. Reject dark patterns and unsupported
urgency/testimonials. Distinguish observed friction, user-test results, analytics, and
hypothesized lift. Validation: measurable funnel event definition or scoped experiment,
baseline, guardrail metrics and success criterion; never promise a percentage uplift.
