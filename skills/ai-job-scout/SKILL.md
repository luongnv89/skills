---
name: ai-job-scout
description: "Find open AI engineering jobs that fit a candidate, verify location and apply links, and assess each employer's product. Use for one-off shortlists or a job alert's research step. Don't use for résumé writing, job applications, or company news."
license: MIT
effort: high
metadata:
  version: 1.1.0
  author: "Luong NGUYEN"
---

# AI Job Scout

Find the requested number of open roles (three by default) that match the candidate, then examine the *company and project*, not just the job ad. Research-only: never apply, contact recruiters, or change a job tracker without a separate request.

## When to Use

Use when a candidate asks for an AI job shortlist, the research step of an already configured job alert, or whether the projects behind open roles are worth pursuing. The skill produces a report, not a schedule: use a scheduler only when the user asks, and never claim a schedule exists without verifying it.

## Instructions

Run steps 1–4 in order. Research a company (step 3) only for roles that passed step 2. After each step, print its Step Completion Report.

Terms used throughout:

- **Verified listing:** the role's page on the employer's careers site or its ATS (Greenhouse, Lever, Ashby, Workable, and similar), opened and read on the run date. Aggregators (LinkedIn, Welcome to the Jungle, remote boards) and search snippets only help discovery; they are never a verified listing.
- **AI-central:** the listing's responsibilities make building, evaluating, securing, or operating AI/ML systems a primary duty.
- **Prior report:** an earlier report or list of listing URLs that the user supplied or that this run can open.
- **Near-miss:** a shortlisted role that failed the step 3 gate; report it with its evidence, and never rank it.

## Inputs and branches

- **Candidate:** Public GitHub/profile URL and any résumé or constraints the user has supplied. If none is available, ask for the profile before claiming a personal fit. If the user gives none, label the search unpersonalized. Re-read the public profile on each run; do not store a biography in this skill.
- **Geography:** Build the **location rule**, the candidate's accepted work arrangements as testable conditions, from the user's work arrangement and home location. Hybrid in a city: admit a role only when its verified listing names that city and states an office-attendance policy. Fully remote: admit a role only when its verified listing says applicants in the user's country are eligible. Example: "Paris hybrid or fully remote from France" admits Paris hybrid roles with a stated attendance policy and remote roles open to France-based applicants. "Remote" with no eligible country or region is *unknown*, not worldwide. If hybrid is only inferred (for example, from where the candidate lives), label the fit conditional and ask the candidate to confirm.
- **Cadence:** If a recurring alert has a prior report, compare against it and skip repeats unless the listing materially changed. If no prior report is available, state that deduplication was not verified; do not claim every pick is new. Check dates and open status on the run date.
- **Count:** Default to three roles; use the user's count when given. Fewer qualifying roles is a valid result.
- **Format:** Write the text report by default. If the count is above five, or the user asks to filter roles (for example by salary or remote policy), read `references/interactive-report.md` and build the HTML report instead, unless the user asks for text. If HTML cannot be produced here, say so and write the text report.

## 1. Derive a candidate-fit brief

Read the profile and note supported seniority, projects, languages, AI specialties, adjacent domain experience, and geographic constraints with links. Distinguish observed repository code/activity from a README's self-description and from independently unverified career claims. Do not infer work authorization outside the candidate's home country, education, spoken languages, relocation willingness, or production deployment from project descriptions alone.

**Gate:** The brief records at least one source for each positive fit claim and the location rule. Missing essential constraints are listed, not guessed.

## 2. Discover and verify live listings

1. Search employer career pages and ATS boards for several role families that match the brief.
2. Open the verified listing for each candidate role. If the page is blocked, retry with another retrieval method or the employer's ATS endpoint, then with an interactive browser. If every method fails, reject the role.
3. Open the application form when one exists. A reachable application tab on the listing URL counts as a working apply path.
4. Record from the verified listing: title, employer, responsibilities, required seniority, location/remote eligibility (quoted), posting date or "unknown", and salary and equity or "not listed". Do not turn an old posting date into a new one.
5. Apply the hard rejects. Record each rejected role with the check it failed.

**Hard reject:** unreachable verified listing; closed or missing application; the location rule fails or remote eligibility stays ambiguous; the role is not AI-central; a junior or intern role outside the requested level; a prior report's listing with no material change.

**Gate:** Every shortlisted role has a verified listing URL and a quoted location policy that passes the location rule. Never weaken a hard reject to reach the count.

## 3. Research each company's product and the role's project

For *each* shortlisted role, read the employer's product/about pages, docs or engineering blog; consult independent coverage only where it adds substantiated context. Explain:

1. The product, its users or problem, and the role's documented responsibilities. Name the specific assigned project only when the listing or another employer source identifies it; otherwise label the assignment unknown.
2. Where AI actually fits in the product and what is technically distinctive versus generic AI marketing.
3. A candid **interestingness verdict** for this candidate, supported by concrete engineering problems, not prestige or funding alone.
4. Unknowns or risks (e.g. unclear product maturity, vague AI remit, domain mismatch). Include funding, customer counts, revenue, and stage only when sourced and relevant; never infer traction from a polished site.

**Gate:** At least one directly read company/project source beyond the job ad supports the product description for every ranked role. If none can be read, report the role as a near-miss instead of ranking it.

## 4. Rank and report

Rank by (in order) hard-gate certainty, relevant demonstrated skills, centrality of AI work, strength of the actual project, and posting recency. Do not assign numerical scores. State why #1 beats #2, including tradeoffs.

Read `references/report-format.md` and draft the report in its order: **Result** (first line: `Complete`, `Partial`, or `None`, with K of N roles), **Search evidence**, **Ranked roles**, **Uncertainty**, and **Decision** ("No approval needed" plus the candidate's next actions). Check the draft against the Acceptance Criteria, print step 4's report block, then deliver.

## Step Completion Reports

After each step, print one block. Its `Gate` line restates that step's **Gate**:

```text
◆ Step N of 4 — <step name>
  <check>:  √ pass | × fail — <reason>
  Gate:     √ met | × not met — <what is missing>
  Status:   PASS | PARTIAL | FAIL
```

| Step | Checks |
|---|---|
| 1 | `Profile read`, `Fit claims sourced`, `Location rule`, `Missing constraints` |
| 2 | `Listings opened`, `Hard rejects`, `Shortlisted` (count) |
| 3 | `Product sources read`, `Near-misses` |
| 4 | `Ranked`, `Acceptance criteria`, `Format` (HTML: delivery check) |

Status is PASS when the gate holds (from step 2, for every requested role), PARTIAL when it holds for fewer, and FAIL when it holds for none. Step 4's gate is the Acceptance Criteria. A FAIL still continues to step 4.

## Expected output

See `references/report-format.md` for each section's fields and a full example.

## Edge Cases

- **An aggregator shows a role as active, but its verified listing is closed or unreachable:** Reject the role.
- **No qualifying roles, or only a prior report's unchanged listings:** Report `None — 0 of N roles` with the filters applied; never pad the list or fabricate roles.

## Acceptance Criteria

Check every item before delivery. Remove from the ranking any role with a hard-reject or gate failure; label a missing soft detail "unknown".

**Correctness**

- The ranking has no more than the requested count.
- Each ranked role has a verified listing and a separately read company/project source, both linked.
- Every location statement quotes the employer's policy and shows it passes the location rule.
- Every product assessment covers what the company builds, the role's documented duties, the interestingness verdict, and what remains unknown.
- Every fit claim points to candidate evidence; salary, dates, traction, and language claims without a source are omitted or marked unknown.
- No application, outreach, or tracker change was made.

**Understanding**

- The report's first line is the Result line, giving the status and count without expanding anything.
- Verified facts name their source; inferences, conditional fit, and unverified items are labeled.
- Each material claim's evidence matches its scope; a reachable apply form is never reported as eligibility.
- The Decision line says "No approval needed" and names the candidate's remaining actions.

These checks verify the report against its instructions. Only reviewer feedback confirms that a human understood it; without that feedback, report understanding as unconfirmed.

## Testing

Use `evals/evals.json` for positive, boundary, and negative-trigger tests. Grade every non-negative eval against both lists above.
