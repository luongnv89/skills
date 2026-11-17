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
surfaces and any supplied guidelines. Without guidelines label strategic fit as a
hypothesis, not a breach. Source design tokens can show consistency but not rendered
appearance. Suggest a coherent system rather than a gratuitous trend-driven redesign.
Validation: approved brand tokens/copy rules and visual review of named states.

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
