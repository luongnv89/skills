---
name: ai-job-scout
description: "Find open AI engineering jobs, verify candidate/location fit, and assess each company's product. Use for one-off reports or configured alerts; not for scheduling, applying, CV writing, or generic company news."
license: MIT
effort: high
metadata:
  version: 1.0.0
  author: "Luong NGUYEN"
---

# AI Job Scout

Find up to three open roles that match the candidate, then examine the *company and project*, not just the job ad. Do not fill a daily quota with stale or geographically ineligible roles. Research-only: never apply, contact recruiters, or change a job tracker without a separate request.

## When to Use

Use when a candidate asks for an AI job shortlist, the research portion of an already configured recurring job alert, or whether the projects behind matching open roles are worth pursuing. This skill produces a report, not a scheduled alert; use an available scheduler separately only when requested, and never claim a schedule was created without verifying it. Do not run this workflow for résumé editing, automatic applications, or generic company news.

## Instructions

Follow the four gates below in order. Every role must pass the employer-listing and location gate before spending time on product research; evaluate company interest only for eligible open roles.

## Inputs and branches

- **Candidate:** Public GitHub/profile URL and any résumé or constraints the user has supplied. If none is available, ask for the profile before claiming a personal fit; an unpersonalized search must be labeled as such. A GitHub README is self-reported, not proof of employment, degrees, language level, or production experience. Refresh the public profile on each run rather than preserving a fixed biography in this skill.
- **Geography:** Use the user's stated work arrangement and home location. If the user wants Paris hybrid or fully remote from France, admit only Paris hybrid with a stated office-attendance policy or fully remote roles explicitly open to France-based applicants. Paris residence alone does not prove willingness to attend an office: if hybrid is merely an inferred preference, label fit conditional and confirm with the candidate before claiming it meets their work-arrangement constraint. “Remote” without an eligible country/region is *unknown*, not worldwide. An office in Paris alone does not establish a hybrid policy.
- **Cadence:** In a recurring alert, compare prior reports/URLs only when supplied or actually accessible; avoid repeats unless the listing materially changes. If history is unavailable, say deduplication against earlier reports could not be verified; do not claim every pick is new. On a one-shot request, do not assume a previous report exists. Dates and open status are checked on the day of each search.
- **Count:** Default top three; obey another user-specified count. Fewer qualifying roles is a valid result.

## 1. Derive a candidate-fit brief

Read the profile and note supported seniority, projects, languages, AI specialties, adjacent domain experience, and geographic constraints with links. Distinguish observed repository code/activity from a README's self-description and from independently unverified career claims. Do not infer work authorization outside the candidate's home country, education, spoken languages, relocation willingness, or production deployment from project descriptions alone.

**Gate:** The brief records at least one source for each positive fit claim and an explicit location rule. Missing essential constraints are identified rather than guessed.

## 2. Discover and verify live listings

Search current employer career pages and ATS listings; aggregators (LinkedIn, Welcome to the Jungle, remote boards, search snippets) are discovery aids, not the final evidence. Try multiple role families aligned to the brief. Open each employer-hosted listing and, when available, its application form. Confirm title, employer, role responsibilities, required seniority, location/remote eligibility, posting date (if given), salary (if given), and a working direct apply URL (a reachable application tab on the listing URL counts). Prefer recent listings, but do not turn an old date into a fictitious new one. If a page is blocked, retry another retrieval method or official ATS endpoint, including an interactive browser if the text extractor fails; do not present a search snippet as a verified open job.

**Hard reject:** closed or missing application; location excludes the candidate or remote eligibility remains ambiguous; AI is incidental; junior/intern role outside the requested level; duplicate of a previously reported opening without a material change. Say *why* a near-miss failed. Never infer “worldwide remote” from the word “remote.”

**Gate:** Every shortlisted role has a live employer/ATS URL and source-backed location eligibility. If fewer than requested pass, continue with fewer rather than weakening the gate.

## 3. Research each company's product and the role's project

For *each* shortlisted role, read the employer's product/about pages, docs or engineering blog; consult independent coverage only where it adds substantiated context. Explain:

1. The product, its users or problem, and the role's documented responsibilities. Name the specific assigned project only when the listing or another employer source identifies it; otherwise label the assignment unknown.
2. Where AI actually fits in the product and what is technically distinctive versus generic AI marketing.
3. A candid **interestingness verdict** for this candidate, supported by concrete engineering problems, not prestige or funding alone.
4. Unknowns or risks (e.g. unclear product maturity, vague AI remit, domain mismatch). Funding, customer counts, revenue, and stage are included only when sourced and relevant; never infer traction from a polished site.

**Gate:** At least one directly read company/project source beyond the job ad supports the product description for every ranked role. If none is available, exclude the role from the ranked shortlist and mention it only as an unverified near-miss. Link sources near the claims they support.

## 4. Rank and report

Rank by (in order) hard-gate certainty, relevant demonstrated skills, centrality of AI work, strength of the actual project, and posting recency. Do not assign fake numerical scores. State why #1 beats #2, including tradeoffs. Do not repeat yesterday's unchanged positions to fill the quota.

For each rank, provide these labeled sections (adapt detail to evidence, not a rigid word count):

- **Role & apply:** employer, title, direct employer/ATS link, checked date, posting date or “unknown.”
- **Location & compensation:** exact hybrid/remote rule and applicant-country eligibility, with quote; salary/currency if published, otherwise “not listed.”
- **Company & project:** what it builds, users/problem, documented role responsibilities (specific assignment if sourced, otherwise “unknown”), AI mechanism, product/source link, and *interestingness verdict* with evidence and caveats.
- **Fit:** requirements, matching candidate projects with URLs; distinguish observed repository work from self-reported experience and unproved professional claims; gaps/uncertainties and rank rationale.

Cite the listing and company sources directly; distinguish facts from inference. An application form being reachable does not prove the applicant qualifies or that a hiring team is responding. Close with unverified items and near-miss exclusions when relevant. If no role passes, report the search surfaces and why none qualified; never fabricate three.

## Pre-delivery check

For each selected job, verify: employer-hosted listing and apply path reachable; AI role central; candidate eligible under the exact location rule; company/project source actually read; fit versus gaps and interestingness both explained; dates and salary not invented; no outreach or application performed. A missing hard gate means remove the role. A missing soft detail must be labeled unknown.

## Expected output example

Illustrative format only — placeholders are **not** real listings or evidence:

```text
1. [Company] — Senior AI Engineer | [live employer ATS link]
   Location: Paris hybrid, two office days [job quote/link]. Posted: unknown. Salary: not listed.
   Project: [specific product, users and AI mechanism] [company product link].
   Interestingness: High/Medium/Low — [concrete engineering challenge and caveat].
   Fit: [candidate project link and relevant experience]; gap: [unproved skill].
   Why #1: [comparison against next role]. Checked: [date].
```

## Edge Cases

- **Blocked official listing or closed apply form:** Try another official endpoint; otherwise reject, regardless of the aggregator's “active” badge.
- **Remote policy says only “remote”:** Do not assume global hiring or France eligibility. Reject until employer evidence resolves it.
- **No candidate profile:** Ask for one or explicitly label fit unpersonalized; never invent background.
- **No worthwhile matches or only yesterday's unchanged jobs:** Report the shortage and filters applied; do not recycle or pad.

## Acceptance Criteria

- The output contains no more than the requested count and no hard-gate failures.
- Each selected role has distinct verified employer/ATS and company/project sources with direct URLs.
- Every location statement quotes the employer's policy and explicitly establishes candidate eligibility.
- Every product assessment says what the company builds, what the role is documented to do, why it may be interesting, and what project assignment remains unknown.
- Every claimed fit points to candidate evidence; all unsupported salary, dates, traction, and language claims are omitted or marked unknown.

## Testing

Use `evals/evals.json` for positive, boundary, and negative-trigger tests. Given a listing that says only “remote,” expect the report to exclude it until the employer confirms the candidate's country; given a closed apply form, expect rejection even if an aggregator lists it as open. Verify each completed report against the acceptance criteria above before delivery.
