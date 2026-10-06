# Report and improvement-plan contract (version 1)

Always produce a human Markdown report and JSON companion. All supported findings must
be scoped to evidence; structural validation does not validate their truth.

## Markdown sections (exact H2 headings)

1. `Executive Summary`: outcome PASS/PARTIAL (rule: `final-report.md`), main strengths and
   top three priorities.
2. `Scope and Evidence`: mode, audience/goal, sample, exclusions, tool limits, E records.
3. `Human UX`: all six human coverage entries with status/rationale and relevant E/F ids.
4. `AI/Search AX`: all six AX entries, applicability/policy and optional-format caveats.
5. `Prioritized Findings`: F ids, type, severity/confidence, evidence and recommendations.
6. `Improvement Plan`: T ids, phases, priority, finding links, owner, effort, dependencies,
   expected qualitative impact and concrete acceptance checks.
7. `Limitations and Next Step`: evidence gaps, no unsupported certification/outcome, exact
   artifact paths and explicit choice-of-IDs implementation offer. Stop for approval.

No arbitrary aggregate score. Do not hide not-tested or not-applicable entries. If fewer
than three actionable priorities exist, list only the supported ones, not padding.

## JSON fields

Top-level keys: `schema_version` (integer 1), `scope`, `evidence`, `coverage`, `findings`, `plan`.
Arrays can be empty except coverage, which has exactly 12 entries with the canonical ids.
Required shapes; additional fields are allowed but do not replace these:

```json
{
  "schema_version": 1,
  "scope": {
    "target": "provided saved HTML", "mode": "evidence-only",
    "audience": "unknown", "primary_goal": "unknown",
    "sampled_surfaces": ["pricing"], "limitations": ["No rendered view or analytics"]
  },
  "evidence": [
    {"id": "E1", "source": "pricing.html:12-13", "method": "saved HTML inspection",
     "observation": "Two purchase links have identical primary labels", "limitations": "No visual or click test"}
  ],
  "coverage": [
    {"aspect": "clarity", "status": "issues", "rationale": "Ambiguous purchase links in saved HTML",
     "evidence_ids": ["E1"], "finding_ids": ["F1"]}
  ],
  "findings": [
    {"id": "F1", "aspect": "clarity", "kind": "observed", "severity": "medium",
     "confidence": "medium", "title": "Purchase labels do not distinguish options",
     "evidence_ids": ["E1"], "recommendation": "Give each action a specific label"}
  ],
  "plan": [
    {"id": "T1", "phase": 1, "priority": "P2", "finding_ids": ["F1"],
     "title": "Clarify purchase links", "owner": "content/design", "effort": "S",
     "dependencies": [], "expected_impact": "Reduce ambiguous choices; validate with users",
     "acceptance_checks": ["Each action names its destination/option and passes a keyboard/user test"]}
  ]
}
```

This excerpt omits the other 11 coverage entries; a deliverable must include them.
`scope.mode`: live-web | repo | evidence-only | native-app.
Coverage statuses: pass | issues | not-tested | not-applicable.
Finding kind: observed | hypothesis. Severity: critical | high | medium | low.
Confidence: high | medium | low. Effort: XS (bounded copy/config), S (one component/route),
M (cross-surface), L (architectural/research); these are estimates, not guaranteed hours.

`pass` requires evidence. `issues` requires evidence and at least one observed finding for
that aspect. Finding/coverage references must exist; a finding must support the linked
coverage aspect through its primary or related aspects. Optional `related_aspects` is an array of canonical aspect ids. A coverage link may match
primary `aspect` or a `related_aspects` member, so one defect can support multiple audiences
without duplicating findings. The same rule applies to the observed finding required by
`issues`. Observed findings require evidence; hypotheses require explicit uncertainty in
title/recommendation. Every finding must be referenced by at least one plan task. Plan
measurement tasks may have empty finding_ids. Dependencies name T ids, form an acyclic
graph and precede dependent tasks in the array. Strings nonempty except evidence
limitations, which may be empty; scope limitations can be empty.

## Triage

Severity uses verified user/task harm: critical = blocks the primary task for the relevant
audience or exposes sensitive data; high = major repeated friction/exclusion; medium =
meaningful but recoverable friction; low = polish/optional opportunity. Severity is a
judgment, not a score. Insufficient evidence to demonstrate harm stays a hypothesis.

Priority: P0 critical blocker/privacy or urgent evidence collection; P1 high impact;
P2 medium/supported discoverability improvement; P3 low/optional polish. Findings about
missing optional Markdown/llms/AI buttons default to low hypotheses/opportunities unless
explicit requirements establish harm. Do not treat an intentional policy restriction as
a defect. Task grouping may share ids across aspects, but never duplicate one defect.

Phases: 0 unblock/measure; 1 human/accessibility/performance fundamentals; 2 public
content/discovery; 3 polish/experiments. Order tasks by phase then priority then id, except
move a prerequisite ahead of its dependents and explain any phase exception in Markdown.

## Validator

`python3 <skill-dir>/scripts/validate_report.py <json-path> --markdown <md-path>`
Stdlib-only. Exit 0 = structural PASS; exit 1 = validation/read/parse errors with field
paths on stderr. Checks 12-aspect coverage, shape/types/enums, E/F/T references, observed
finding evidence, all findings planned, acyclic/ordered dependencies and Markdown headings.
It cannot check evidence truth, severity wisdom, hypothesis wording, privacy decisions or
Markdown/JSON semantic agreement; parent must review those explicitly.
