# Label set — derivation, colours, creation

Every issue this skill files carries a deterministic **label set**. "Proper label" means the label is
derived from the plan by rule, identical on every run, and machine-filterable — not a per-issue
judgement call. Read this in Phase 2.

## The four axes

One label per axis, except `dim:` which may repeat when a task closes findings from several
dimensions.

| Axis | Label | Derived from | Mandatory |
|---|---|---|---|
| Phase | `phase:pre`, `phase:p0` … `phase:p4` | the task's `## Phase` heading, lowercased | yes |
| Type | `bug`, `improvement`, `feature` | dimension mapping below | yes |
| Dimension | `dim:dep`, `dim:bug`, `dim:sec`, `dim:test`, `dim:ci`, `dim:docs`, `dim:perf`, `dim:ux`, `dim:clean`, `dim:dead`, `dim:env` | `<DIM>` of each `Closes:` finding id | when `Closes:` is non-empty |
| Priority | `priority:critical`, `priority:high`, `priority:medium`, `priority:low` | highest severity among closed findings, else the phase default | yes |

The epic carries exactly one label: `epic`.

Effort stays in the issue body's Metadata section — it is not a label. Four axes across ~50 issues is
already 4–6 labels per issue; a fifth buys filtering nobody uses and doubles the labels to create.

**No `blocked` label.** Dependencies live in the issue body (`Depends on #N`, written by the bridge)
and in the plan map's `depends on #N` note. A `blocked` label would need re-synchronising on every
child close — exactly the churn this skill removed from the epic body, and it would put derived
status back into the tracker by another route.

## Dimension → type mapping

| Dimensions in `Closes:` | Type label | Why |
|---|---|---|
| `BUG`, `SEC` | `bug` | defect or vulnerability — something is wrong today |
| `DEP`, `PERF`, `CLEAN`, `DEAD`, `TEST`, `CI`, `DOCS`, `UX` | `improvement` | the code works; this makes it better, safer, or faster |
| none (**milestone-enabling**) | `improvement` | scaffolding for a milestone, unless it adds a capability the repo does not have |
| a task that introduces a capability absent from the repo (first CI pipeline, first test suite) | `feature` | new capability, matching `/issue-creator`'s classification |

Mixed dimensions: `bug` wins over `improvement` — the defect is the reason the task exists.

## Priority from severity

| Highest severity closed | Priority label |
|---|---|
| `Critical` | `priority:critical` |
| `High` | `priority:high` |
| `Medium` | `priority:medium` |
| `Low` | `priority:low` |

When severity is unavailable (no `MODERNIZATION_REPORT.md` beside the plan, or a
`tasks-generator` plan with no findings), use the phase default from
`references/plan-parsing.md` → *Dimension and severity*, and say so once in the report:
`Priority source: phase-default (no MODERNIZATION_REPORT.md found)`.

## Colours

Fixed hex per label so a repo relabelled by this skill looks the same everywhere. Colours are passed
without the leading `#`.

| Label | Hex | | Label | Hex |
|---|---|---|---|---|
| `epic` | `5319E7` | | `dim:dep` | `0E8A16` |
| `phase:pre` | `6E7781` | | `dim:bug` | `B60205` |
| `phase:p0` | `B60205` | | `dim:sec` | `D93F0B` |
| `phase:p1` | `D93F0B` | | `dim:test` | `1D76DB` |
| `phase:p2` | `FBCA04` | | `dim:ci` | `0052CC` |
| `phase:p3` | `0E8A16` | | `dim:docs` | `C5DEF5` |
| `phase:p4` | `1D76DB` | | `dim:perf` | `FEF2C0` |
| `priority:critical` | `B60205` | | `dim:ux` | `D4C5F9` |
| `priority:high` | `D93F0B` | | `dim:clean` | `BFD4F2` |
| `priority:medium` | `FBCA04` | | `dim:dead` | `E4E669` |
| `priority:low` | `C2E0C6` | | `dim:env` | `5319E7` |
| `bug` / `improvement` / `feature` | GitHub defaults — never recolour an existing label | | | |

## Creation procedure

```bash
gh label list --limit 200 --json name --jq '.[].name'      # existing set, one call
gh label create "phase:p0" --color B60205 --description "Modernization phase P0 — Stabilize"
```

Rules:

- **Diff first, ask once.** Print every missing label with its colour, then a single `[Y/n]`. Never
  create labels one prompt at a time, and never create them silently.
- **Never modify an existing label.** A repo that already has `bug` in another colour keeps it. Only
  missing labels are created.
- **Fail-soft.** `gh label create` failing (permissions, org policy, race) is a `⚠`: record the label
  as **dropped**, continue, and file issues with the labels that do exist.
- **Dropped labels are reported.** The final report names every dropped label and the issues that
  therefore carry a reduced set. An issue reduced below its two mandatory labels (`phase:` + type) is
  a `PARTIAL` result, not a pass.

## Applying labels

`/issue-creator` applies its own suggested labels at creation time. This skill adds the label set
afterwards, additively:

```bash
gh issue edit <n> --add-label "phase:p0,improvement,dim:dep,priority:high"
gh issue view <n> --json labels --jq '[.labels[].name]'     # verify-by-re-read
```

Never `--remove-label` a label `/issue-creator` chose. Two labelling systems coexisting is noise;
deleting another skill's output is data loss.
