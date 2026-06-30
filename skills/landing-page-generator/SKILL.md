---
name: landing-page-generator
description: "Generate conversion-focused landing page copy with PAS, AIDA, or StoryBrand. Use when creating sales pages, hero sections, CTAs, or full marketing website copy. Don't use for README rewrites, blog posts, or UX audits."
license: MIT
effort: high
metadata:
  version: 1.1.3
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Landing Page Generator

Generate conversion-focused landing page copy using proven copywriting frameworks.

## Anti-Slop Rules

AI-generated marketing copy has predictable tells that kill credibility. See `references/anti-slop-rules.md` for banned phrases and structural patterns to avoid.

**Quick test:** read each sentence and ask "does this give the reader information they didn't already have?" If not, cut it.

## Prerequisites

Before writing, confirm the user supplied enough detail to make specific claims:

- Product/service name and target audience
- Problem solved and primary desired action
- Proof points, metrics, testimonials, or named differentiators
- Pricing/trial/guarantee details if a pricing section is requested

If proof is missing, write placeholders clearly labeled `[proof needed]`; never invent customers,
metrics, guarantees, scarcity, or compliance claims.

## Workflow

### Step 1: Gather Product/Service Information

Collect before writing:

| Input | Purpose |
|---|---|
| Product/service name | Anchor all copy |
| Target audience | Tone, pain points, vocabulary |
| Problem solved | Core value prop |
| Competitive advantage | Differentiation |
| Desired visitor action | Primary CTA |
| Social proof | Testimonials, metrics, logos |

If any **core** input is missing—product/service name, target audience, problem solved, or primary
CTA—ask before proceeding. For missing proof, pricing, or guarantee details, proceed with `[proof needed]`
placeholders per Prerequisites and guardrails.

### Step 2: Choose Copywriting Framework

| Framework | Best for | Structure |
|---|---|---|
| **PAS** | Pain-driven B2B, productivity tools | Problem → Agitate → Solution |
| **AIDA** | Consumer apps, broad audiences | Attention → Interest → Desire → Action |
| **StoryBrand** | Narrative brands, coaching, services | Hero → Guide → Plan → CTA → Success/Failure |

Tell the user which framework you picked. Let them override.

### Step 3: Generate Landing Page Sections

Populate **every section** in the framework-specific template from `references/section-templates.md`
that matches the framework chosen in Step 2. Use that template's section names and order exactly—do not
substitute a generic Hero/Problem/Solution layout when another framework applies.

**Content quality (all frameworks):**
- Headlines: 10 words or fewer, value-led, specific to the audience
- Subheadlines: 1–2 sentences that expand the headline without repeating it
- Body copy: active voice, benefit-led; address pain points with concrete scenarios where the template calls for them
- Features: 3–5 items described as outcomes, not feature lists
- How It Works: 3–4 simple steps; icon concept + description per step; CTA at the end
- Social proof: quote + name + role + company, or `[proof needed]` when proof is unavailable
- Pricing (if applicable): feature comparison, recommended plan callout, guarantee copy or `[proof needed]`
- FAQ: 5–7 common objections with clear, confident answers
- CTAs: follow CTA Button Rules; place primary and secondary CTAs where the template specifies
- Final CTA: risk reversal (guarantee, trial); urgency or scarcity only when genuine; button text reinforces value

### Step 4: Format Output

Use the template matching the chosen framework in `references/section-templates.md` (PAS, AIDA, or
StoryBrand). Keep large reusable structures in references to protect the agent's context budget; read
only the reference needed for the requested output. End with optimization notes: A/B test ideas and
conversion tips.

### Step 5: Copywriting Best Practices

- Active voice, present tense
- Benefits over features
- Specific numbers and data where available
- Address objections directly
- Urgency without pressure tactics
- Short, scannable sentences
- "You" language (customer-focused)
- Multiple CTAs throughout the page

### CTA Button Rules

- Start with an action verb
- Be specific about the outcome
- First person when appropriate ("Start My Free Trial")
- Genuine urgency ("Get Instant Access")
- Never generic ("Submit", "Click Here")

## Example Triggers

- "Write landing page copy for a B2B SaaS tool"
- "Create sales page content using PAS framework"
- "Generate hero section copy for my product"
- "Write conversion-optimized CTAs"
- "Help me with landing page headlines"

## Expected Output Example

Example input:

```text
Generate a landing page for AcmeDesk, a helpdesk for solo founders. Audience: indie SaaS founders.
Primary CTA: Start free trial. Differentiator: setup in 10 minutes, shared inbox + AI drafts.
```

Expected output:

```text
LANDING PAGE COPY
Product/Service: AcmeDesk
Framework: PAS

HERO SECTION
Headline: Answer Every Customer Without Hiring Support
Subheadline: AcmeDesk gives solo founders a shared inbox and AI draft replies that are ready in 10 minutes, not weeks.
CTA Button: "Start My Free Trial"
Trust Bar: [proof needed — add user count, testimonial, or response-time metric]
...
OPTIMIZATION NOTES
A/B Test Ideas: test speed-focused vs founder-control headlines.
```

## Safety & Guardrails

- Confirm missing inputs before generating a full page; if the user wants speed, proceed with clearly
  marked assumptions.
- Treat unsupported claims as an error: add `[proof needed]` instead of fabricating metrics, logos,
  testimonials, awards, guarantees, medical/legal/financial outcomes, or fake urgency.
- Validate every CTA against the CTA Button Rules before delivery.
- Warn when the requested copy depends on regulated claims, competitor comparisons, or scarcity that
  requires legal or factual review.

## Edge Cases

- If the user asks for only one section, generate that section and a short note on how it fits the page.
- If the product is vague, ask 2–4 targeted questions rather than writing generic copy.
- If the user requests HTML, design, wireframes, SEO strategy, or UX critique, explain that this skill
  only generates landing-page copy and offer a copy-only structure.
- If social proof is unavailable, write a proof slot rather than a fake testimonial.

## Acceptance Criteria

Verify before delivering:

- Output follows the framework-specific template in `references/section-templates.md` or a user-specified
  subset.
- Chosen framework is named and consistently applied.
- Hero headline is 10 words or fewer, specific, and value-led.
- Every CTA starts with an action verb and states the outcome.
- Unsupported proof is labeled `[proof needed]`; no fake claims are present.
- Copy passes `references/anti-slop-rules.md`.
- Final response includes A/B test ideas and conversion tips unless the user asked for a single section.

## Output Quality Checklist

Before delivering, confirm all copy:

- Leads with value, not features
- Addresses target audience pain points
- Uses emotional and logical appeals
- Has clear, compelling CTAs
- Includes social proof elements
- Handles objections proactively
- Creates urgency only when justified
- Is scannable and easy to read
- Follows the chosen framework consistently
- Passes the anti-slop rules
