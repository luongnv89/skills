# Report format (step 4)

Read this before writing the report. It is the content contract for both formats: the text report below, and the HTML report in `interactive-report.md`, which adds filters and evidence panels to the same content and moves rejected roles and near-misses into their own group.

## Order

1. **Result** (first line): `Complete — N of N roles`, `Partial — K of N roles`, or `None — 0 of N roles`, with the run date.
2. **Search evidence:** surfaces searched, the number of verified listings opened, and each rejected role with the hard reject it failed.
3. **Ranked roles**, each with the four sections below. Detail follows the evidence, not a word count.
4. **Uncertainty:** unverified items, inferences, conditional fit, deduplication status, and near-misses with their missing product evidence.
5. **Decision:** "No approval needed." Then the candidate's next actions, such as confirming an office-attendance policy or applying through the listed link. Do not invent approval steps: the skill itself never applies.

## Sections for each ranked role

- **Role & apply:** employer, title, verified listing link, checked date, posting date or "unknown".
- **Location & compensation:** the quoted hybrid/remote policy and applicant-country eligibility; salary and currency if published, otherwise "not listed".
- **Company & project:** what it builds, its users or problem, documented responsibilities (the specific assignment if a source names it, otherwise "unknown"), the AI mechanism, a product source link, and the *interestingness verdict* with evidence and caveats.
- **Fit:** requirements, matching candidate projects with URLs, observed repository work versus self-reported claims, gaps, and why this role ranks above the next one.

## Rules

- Check each role's posting date and open status on the run date; that run date is the role's checked date.
- Put each source link next to the claim it supports.
- Label each inference as an inference.
- A reachable application form does not prove that the applicant qualifies or that a hiring team is responding.
- If no role passes, write `None — 0 of N roles` and let the search evidence explain why. Never fabricate roles.

## Example

Illustrative format only. Placeholders are **not** real listings or evidence.

```text
Partial — 2 of 3 roles (checked 2026-10-06)
Search: 4 ATS boards, 3 career sites; 9 verified listings opened; 7 rejected
(3 location rule, 2 closed, 1 not AI-central, 1 prior-report repeat).

1. [Company] — Senior AI Engineer | [verified listing link]
   Location: Paris hybrid, two office days [quote/link]. Posted: unknown. Salary: not listed.
   Project: [specific product, users and AI mechanism] [company product link].
   Interestingness: High/Medium/Low — [concrete engineering challenge and caveat].
   Fit: [candidate project link and relevant experience]; gap: [unproved skill].
   Why #1: [comparison against #2].
2. [Company] — ...

Uncertainty: hybrid willingness inferred, not confirmed; deduplication not verified (no prior report).
Near-miss: [Company] — product pages unreadable (step 3 gate).
Decision: No approval needed. Next: confirm two office days in Paris; apply via the links yourself.
```
