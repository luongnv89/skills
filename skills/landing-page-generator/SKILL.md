---
name: landing-page-generator
description: "Write landing pages (PAS, AIDA, StoryBrand) from a brief or README, as HTML with privacy, terms, changelog, setup pages. Use for sales copy, hero sections, CTAs, README rewrites. Don't use for blogs, release notes, project docs, or coding mockups."
license: MIT
effort: high
dependencies:
  - frontend-design
metadata:
  version: 1.7.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Landing Page Generator

Generate landing pages using proven copywriting frameworks (PAS, AIDA, StoryBrand). One skill,
two modes: write conversion-focused marketing copy from a product brief, or transform an existing
project README into a scannable, visual landing page. A full landing page ships with the companion
pages its footer links to: Privacy Policy, Terms of Use, Changelog, and Docs, each where it applies.
The last step builds the landing page and those pages as HTML with `frontend-design`.

## Two Modes

Pick the mode that matches the input and deliverable:

| Mode | Use when | Input | Output | Where |
|---|---|---|---|---|
| **A — Landing copy** | You need marketing copy for a sales/landing page | Product/service brief | Conversion-focused copy (hero → CTA) + A/B notes + companion page copy, in chat; the built pages in `landing-page/` | This file, below |
| **B — README landing page** | You have an existing project `README.md` to make persuasive and scannable | Repo `README.md` + project files | Rewritten `README.md` (mermaid, tables, collapsed details) + `README.backup.md` + companion page files + the built pages in `landing-page/` | `references/readme-mode.md` |

If the user asks to "turn my README into a landing page", "make my GitHub page sell the project",
or similar, follow **Mode B** in `references/readme-mode.md`. Otherwise use **Mode A** below. When
unsure which applies, ask.

## Companion Pages

Decide each companion page from facts the brief or the project states, never from a guess. Record
each decision with its reason:

| Page | Applies when |
|---|---|
| Privacy Policy | Always |
| Terms of Use | The product has user accounts, a paid plan, a free trial, or a subscription. An open-source tool with none of these gets no Terms page: its license governs use |
| Changelog | Always. Mode B links an existing history file instead of writing one |
| Docs | The product is a CLI, library/SDK, self-hosted service, plugin/extension, or API, or the brief or project names a setup step the product's users perform outside its UI (install command, API key, environment variable, config file, DNS record). Contributor setup does not count |

- If the user asks for a single section or says "landing page only", skip every companion page and record the skip.
- If the user names extra pages, add them to the pages the table applies. If the user says "only" those pages, write only them and record the rest as `skipped — not requested`.
- If the user asks for one companion page alone, write only that page and name the footer link it needs. Mode A runs Step 6 for it and asks only for a missing product name; a repo file follows `references/readme-mode.md` → *Edge Cases*.

Mode A delivers each page as a copy block in chat. Mode B writes `PRIVACY.md`, `TERMS.md`,
`CHANGELOG.md`, and `docs/getting-started.md`, and never overwrites an existing file. Sources,
templates, and checks: `references/companion-pages.md`.

## Anti-Slop Rules

AI-generated marketing copy has predictable tells that kill credibility. See `references/anti-slop-rules.md` for banned phrases and structural patterns to avoid.

**Quick test:** read each sentence and ask "does this give the reader information they didn't already have?" If not, cut it.

## Default Quality Bar

In both modes, the final deliverable (Mode A copy and its structure; Mode B README layout; the companion pages; the built pages) must be professional, production-ready, elegant, and premium, even when the user never asks. The brief or project voice decides the tone; this bar decides the finish:
- **Professional**: precise and credible; no hype
- **Production-ready**: ship-ready, every section complete; the only allowed gaps are labeled `[proof needed]` (Mode A) or `[placeholder]` (Mode B) markers
- **Elegant**: concise, one consistent voice, clean scannable hierarchy
- **Premium**: confident restraint, specific claims, polished formatting

These are qualities of the output, never words to put in it: do not write "premium", "elegant", or "world-class" into the copy.

## Prerequisites

Before writing, confirm the user supplied enough detail to make specific claims:

- Product/service name and target audience
- Problem solved and primary desired action
- Proof points, metrics, testimonials, or named differentiators
- Pricing/trial/guarantee details if a pricing section is requested

If proof is missing, write placeholders clearly labeled `[proof needed]`; never invent customers,
metrics, guarantees, scarcity, compliance claims, or commands.

## Dependency Preflight (mandatory)

This skill optionally invokes `frontend-design`, declared in frontmatter `dependencies`, for
the page build only (Mode A Step 7, Mode B Step 8). Before the first write:

```bash
command -v asm >/dev/null || echo "asm not installed: npm install -g agent-skill-manager"
asm deps discover "<this skill's directory>" --json
printf 'lp_session=%s\n' "landing-page-generator-$(date +%s)-$$"   # record it; reuse it verbatim
```

When the page build is reached, run `asm deps acquire frontend-design --session <lp_session> --json`
and read the returned `skillMdPath`. If `asm` is missing or the acquire fails, read
`~/.claude/skills/frontend-design/SKILL.md` or `~/.agents/skills/frontend-design/SKILL.md`. Do not
acquire it when the build is skipped (`references/page-build.md` → *Build decision*). If an acquire
ran, run `asm deps release --session <lp_session> --json` at the end, including an early stop.
Without `frontend-design`, the run falls back to copy only and records `page: not built — <reason>`;
it never skips the page silently.

## Repo Sync Before Edits (mandatory)

Mode B rewrites `README.md` and writes companion page files inside the repo; the page build writes `landing-page/`. Sync before those writes to avoid clobbering remote work. If the working tree is not clean, stash first, sync, then restore:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
dirty=0
if [ -n "$(git status --porcelain)" ]; then
  git stash push -u -m "pre-sync"
  dirty=1
fi
git fetch origin
git pull --rebase origin "$branch"
if [ "$dirty" -eq 1 ]; then
  git stash pop
fi
```

If `origin` is missing, pull is unavailable, or rebase/stash conflicts occur, stop and ask the user before continuing. If a command after `git stash push` fails, run `git rebase --abort` (when a rebase is in progress), then `git stash pop`, then stop. Skip the sync and record `sync: skipped (<reason>)` when the user says to skip it, or when `git rev-parse --show-toplevel` is not the project directory (ask before syncing a parent repo). Mode A runs this section only before its page build writes into an existing folder (`references/page-build.md` → *Output folder*).

## Workflow (Mode A — Landing copy)

> Mode B (README landing page) has its own self-contained workflow in `references/readme-mode.md`.

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
| Data collected, analytics, processors | Privacy Policy |
| Accounts, plans, trial, billing | Terms of Use |
| Release history: versions, dates, changes | Changelog |
| Install and setup steps | Docs |

If any **core** input is missing—product/service name, target audience, problem solved, or primary
CTA—ask before proceeding. For missing proof, pricing, guarantee, or companion-page details, proceed
with `[proof needed]` placeholders per Prerequisites and guardrails.

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
only the reference needed for the requested output. End the landing copy with optimization notes: A/B
test ideas and conversion tips.

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

### Step 6: Generate Companion Pages

If *Companion Pages* skips every page, write no COMPANION PAGES block: record the skip in this step's report and the Final Report, then go to Step 7.

1. Decide each page with the *Companion Pages* table. Record it as `delivered` or `skipped — <reason>`.
2. After the OPTIMIZATION NOTES, write the COMPANION PAGES block from `references/companion-pages.md`.
3. Write each delivered page from its template in `references/companion-pages.md`.
4. Run the companion checks in `references/companion-pages.md`. Fix each failure before delivery.

### Step 7: Build the Final Page

Follow `references/page-build.md`:

1. Decide the build with its *Build decision* table and record the `page:` entry.
2. Acquire `frontend-design` (*Dependency Preflight*) and give it the *Brief for frontend-design* with the copy of each page.
3. Run the *Page checks*. Fix each failure, then re-run the check.

The pages carry the copy's sections, CTAs, and `[proof needed]` markers verbatim. Without
`frontend-design`, follow *Fallback: copy only*: the copy stands and the run is `PARTIAL`.

## Example Triggers

- "Write landing page copy for a B2B SaaS tool"
- "Create sales page content using PAS framework"
- "Generate hero section copy for my product"
- "Write conversion-optimized CTAs"
- "Help me with landing page headlines"
- "Write the landing page, privacy policy, and changelog for my CLI tool"
- "Write and build a landing page for my app"

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

COMPANION PAGES
Footer links: Privacy Policy · Terms of Use · Changelog
Skipped: Docs — hosted app; the brief names no setup step outside the app

PRIVACY POLICY
Product/Service: AcmeDesk
Effective date: [proof needed — publication date]
...

page: built (landing-page/: index.html, privacy.html, terms.html, changelog.html)
```

## Safety & Guardrails

- Confirm missing inputs before generating a full page; if the user wants speed, proceed with clearly
  marked assumptions.
- Treat unsupported claims as an error: add `[proof needed]` instead of fabricating metrics, logos,
  testimonials, awards, guarantees, medical/legal/financial outcomes, or fake urgency.
- Validate every CTA against the CTA Button Rules before delivery.
- Warn when the requested copy depends on regulated claims, competitor comparisons, or scarcity that
  requires legal or factual review.
- Treat each Privacy Policy and Terms of Use as a draft for legal review. Name that review as a
  remaining user action on the Final Report's `Decision:` line.

## Edge Cases

- If the user asks for only one section, generate that section and a short note on how it fits the page.
- If the product is vague, ask 2–4 targeted questions rather than writing generic copy.
- If the user requests HTML or a design for the page, Step 7 builds it from the copy. If they want
  copy only, skip the build and record why. If they bring a finished design and want only its code,
  or ask for wireframes, SEO strategy, or UX critique, explain that this skill does not do it.
- If social proof is unavailable, write a proof slot rather than a fake testimonial.

## Final Report

End every run, stops included, with this compact text block. Status is `COMPLETE` (the deliverable is produced and every applicable check passes — Mode A: the full-page copy follows the chosen framework's template, or the requested single section plus its fit note is delivered; Mode B: `README.md` is rewritten, `README.backup.md` exists, and the Step 6 Self-Review Checklist passes; both modes: each applicable companion page is delivered, written, or linked and passes the companion checks, and the pages are built and pass the page checks or skipped at the user's request; companion pages only: each requested page passes the companion checks), `PARTIAL` (a deliverable was produced but a check still fails, or the page was not built), or `BLOCKED` (no deliverable: a required question went unanswered and the user ended the run, Mode B found no `README.md` and the user declined creating one, or Repo Sync stopped on a conflict). A question that awaits the user's answer does not end the run. Fill rules, `PARTIAL` and `BLOCKED` examples, and reader checks: `references/final-report.md`. Example:

```text
Result: COMPLETE. Delivered full PAS landing copy for AcmeDesk (hero through final CTA), A/B test ideas, and Privacy Policy, Terms of Use, and Changelog pages, built as HTML in landing-page/; Docs skipped (hosted app, no setup outside the app).
Evidence: Framework PAS named and applied via references/section-templates.md; hero headline 8 words; every CTA starts with an action verb; pages: Privacy Policy, Terms of Use, Changelog delivered, Docs skipped (hosted app); companion checks Pages decided, Facts traced, No compliance claims, Footer links, Changelog style, Anti-slop passed; [proof needed] markers: 2 on the landing page, 18 on the companion pages; anti-slop check passed; page: built (landing-page/: index.html, privacy.html, terms.html, changelog.html) by frontend-design; page checks Pages built, Sections carried, CTAs carried, Markers carried (24/24), Nothing added, Notes excluded, Links resolve, Design checks passed; sync: skipped (new folder).
Uncertainty: Assumed a setup-time objection belongs in the FAQ; no data practices, legal entity, or release date were supplied, so those facts are markers; responsive rendering untested (no browser), breakpoints inspected in CSS.
Decision: No approval needed. Before publishing: replace the [proof needed] markers with real facts, and have a lawyer review the Privacy Policy and Terms of Use.
```

## Acceptance Criteria

Verify before delivering. When the run delivers companion pages only, only the companion and Final Report items apply:

- Output follows the framework-specific template in `references/section-templates.md` or a user-specified
  subset.
- Chosen framework is named and consistently applied.
- Hero headline is 10 words or fewer, specific, and value-led.
- Every CTA starts with an action verb and states the outcome.
- Unsupported proof is labeled `[proof needed]`; no fake claims are present.
- Copy passes `references/anti-slop-rules.md`.
- Output meets the Default Quality Bar (professional, production-ready, elegant, premium) without the user asking.
- Final response includes A/B test ideas and conversion tips unless the user asked for a single section.
- Each companion page is recorded as delivered, linked, or skipped with its reason, and each delivered
  page passes the companion checks in `references/companion-pages.md`.
- The run records a `page:` entry: built pages pass the page checks in `references/page-build.md`
  (sections, CTAs, and gap markers carried verbatim; nothing added), or the skip or fallback reason is stated.
- The run closes with a Final Report: `Result:` and its status first, then `Evidence:`, `Uncertainty:`, and `Decision:` lines; `Evidence:` cites only checks that ran.
- The Final Report passes the four reader checks in `references/final-report.md` (result findable, facts and assumptions separated, claims traceable, next decision clear). Without a human reviewer's answer, human understanding is unconfirmed.

## Step Completion Reports

After each major step, emit a compact status block — per-check `√`/`×` lines and a closing `Result: PASS | FAIL | PARTIAL` line. Mode A uses the format and per-step checks in `references/step-reports.md`; Mode B uses `references/readme-step-reports.md`.
