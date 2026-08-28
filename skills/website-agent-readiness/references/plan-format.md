# The plan grammar `/plan-to-issues` parses

`agent-ready-plan.md` is not free-form markdown. It is the `MODERNIZATION_PLAN.md` shape,
and `/plan-to-issues` parses it with line-anchored patterns. `scripts/render_plan.py`
emits it correctly — read this before changing that script or hand-editing the plan.

## Required structure

```markdown
# Agent Readiness Plan — <targetUrl>

**Baseline:** <level>/5 (<levelName>) — N pass, M fail, K neutral

## Phase P0 — <title>

**Goal:** <goal> · **Milestone M0:** <exit condition>

### Sprint P0 — <title>

#### Task 0.1: <title>

**Description**: <fix prompt> Implementation guide: <url>
**Closes**: — (milestone-enabling: M0)
**Dependencies**: None
**Effort**: XS
**Verify**: re-scan <url>; `checks.<category>.<check>.status` is `pass`
**Acceptance Criteria**:
- [ ] Implementation follows the guide at <url>
- [ ] Re-scanning <url> reports `checks.<category>.<check>.status` as `pass`
- [ ] The change is live on <url>, not only in a preview or staging environment
```

| Element | Pattern | Breaks if |
|---|---|---|
| Phase | `^## Phase <id> — <title>` | the dash is a hyphen, not an em dash |
| Phase goal | `**Goal:** … · **Milestone <MID>:** …` | on separate lines |
| Sprint | `^### Sprint <id> — <name>` | missing — tasks then have no sprint |
| Task | `^#{3,4} Task <id>: <title>` | heading level drifts outside H3/H4 |
| Field | `^\*\*<Field>\*\*: <value>` | the colon moves inside the bold |
| Criterion | `^- \[ \] <text>` | pre-checked as `- [x]` |

## The two traps

**Effort must be one band letter** — `XS`, `S`, `M`, `L`, or `XL`. A pipe-separated range
(`S | M | L (1–3 days)`) is read as an unfilled template leftover and nulls the field.

**Every task needs at least one `- [ ]` criterion.** A task with none fails
`/plan-to-issues`'s Phase 1 completion check, and a one-line fix like "add a
Content-Signal directive" is exactly where the criterion gets dropped as obvious.

Verify both before handing the plan over:

```bash
grep -cE '^#{3,4} Task ' agent-ready-plan.md
grep -cE '^\*\*Effort\*\*: (XS|S|M|L|XL)$' agent-ready-plan.md
```

Both must equal the triage task count.

## Why `Closes:` is a dash

`/plan-to-issues` derives `dim:` labels from `Closes:` finding IDs shaped
`F-<DIM>-<NNN>`, where `<DIM>` is a **closed enum**: `dep bug sec test ci docs perf ux
clean dead env`. Agent-readiness gaps are not codebase audit findings and do not belong
to any of them.

So every task uses the documented milestone-enabling form:

```
**Closes**: — (milestone-enabling: M<n>)
```

This records `closes: []`. What follows, per `plan-to-issues/references/labels.md`:

- **No `dim:` label.** `labels.md` makes the dimension axis conditional — "when `Closes:`
  is non-empty". `plan-parsing.md`'s "otherwise the phase's dominant dimension" describes
  the *worklist*, not the label set; with every task milestone-enabling there is no
  dominant dimension to inherit anyway.
- **Priority from the phase default** — `P0`/`P1` → `high`, `P2` → `medium`, `P3`/`P4` →
  `low`. This is the only lever, which is why the phase mapping is the priority decision.
- **Type is `improvement` or `feature`, decided per task.** `labels.md` types a
  milestone-enabling task `improvement` *"unless it adds a capability the repo does not
  have"*, and a task introducing an absent capability `feature`. Publishing a first-ever
  llms.txt, MCP Server Card, or API catalog is the second case, so expect `feature` on
  most tasks. Either is correct; do not try to force one.

Inventing `F-AGENT-001` would fabricate a dimension the tracker cannot filter on — the
dash is correct, not a workaround.

## Invoke with the explicit path

```
/plan-to-issues agent-ready-plan.md
```

Bare `/plan-to-issues` runs discovery: `MODERNIZATION_PLAN.md` → `docs/MODERNIZATION_PLAN.md`
→ a single `*PLAN*.md` at root → `tasks.md` → `tasks/`. In a repo that has been through
`/codebase-modernizer`, that resolves to the **wrong plan** and files its tasks instead.
Whether lowercase `agent-ready-plan.md` matches the `*PLAN*` glob is not worth finding
out — always pass the path.

`--dry-run` combined with an explicit path is not a documented invocation. The preview
this skill offers is Gate G3: the user reads the rendered plan before any issue exists.

## Sanitisation

`render_plan.py` passes every scanner-derived string through `clean()`: whitespace
collapsed to one line, leading `#` stripped, and `|` escaped in table cells. The scan
response quotes the target site verbatim, so an unsanitised `message` could forge a
heading or break a table column. Keep new fields going through `clean()`.
