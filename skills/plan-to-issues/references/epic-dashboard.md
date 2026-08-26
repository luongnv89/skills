# The epic dashboard

The epic body is the deliverable people read. It answers "how far along is the plan, and what can be
started now?" without opening the plan. Read this in Phase 5 and in Sync mode.

## Sentinels

The dashboard lives between two markers, and **only the region between them is ever rewritten**:

```text
<!-- plan-dashboard:start -->
… rendered block …
<!-- plan-dashboard:end -->
```

Immediately above the sentinels sits the **plan-binding marker**, written when the epic is created
(SKILL.md Phase 3, step 4) — before the first child issue is filed:

```text
<!-- plan-to-issues:plan=MODERNIZATION_PLAN.md -->
```

It is what makes an epic discoverable on a re-run. The sentinels alone cannot do that job: they carry
no plan path, and a run interrupted during Phase 4 would have written neither if they were deferred
to Phase 5. Both are therefore written up front — the sentinel pair starts out empty and Phase 5
fills it.

Everything outside the sentinels — the binding marker, `/issue-creator`'s
`<!-- gitissue:normalized v1 -->` marker, the epic's Description, Reporter Context, Acceptance
Criteria, Metadata — is preserved byte-for-byte. Absent sentinels mean: in Phase 5, append the block
at the end of the body; in Sync mode, **stop** (the issue is not this skill's epic).

Remove any flat `## Children` checklist `/issue-creator` appended when binding the batch. The
dashboard supersedes it; two checklists of the same children drift within a week.

## Layout

```markdown
<!-- plan-dashboard:start -->
## Implementation Dashboard

**Plan:** `MODERNIZATION_PLAN.md` · **Baseline at audit:** AMBER — builds; 41/58 tests pass
**Progress:** 12/50 closed ██░░░░░░░░ 24% · **Last synced:** 2026-08-26

| Phase | Progress | Milestone | Status |
|---|---|---|---|
| Pre Agent environment | 3/3 ██████████ 100% | ME — CLAUDE.md and AGENTS.md exist | ✅ met |
| P0 Stabilize | 4/6 ███████░░░ 67% | M0 — baseline-green reproducible in CI | ◐ in progress |
| P1 Secure & Patch | 0/11 ░░░░░░░░░░ 0% | M1 — zero High/Critical advisories | ○ not started |
| P2 Modernize | 0/14 ░░░░░░░░░░ 0% | M2 — every major current or deferred | ○ not started |
| P3 Clean & Harden | 0/12 ░░░░░░░░░░ 0% | M3 — coverage ≥ 62% | ○ not started |
| P4 Polish | 0/8 ░░░░░░░░░░ 0% | M4 — UX closed; bundle ≤ 480 KB | ○ not started |

### Pre — Agent environment · 3/3 ██████████ 100%

**Goal:** project env an AI agent can use autonomously · **Milestone ME:** ✅ met

- [x] #101 — Pre.1 Make the project environment agent-runnable
- [x] #102 — Pre.2 Create or improve CLAUDE.md
- [x] #103 — Pre.3 Create or improve AGENTS.md

### P0 — Stabilize · 4/6 ███████░░░ 67%

**Goal:** build green, tests runnable, CI running · **Milestone M0:** ◐ in progress

- [x] #104 — 0.1 Commit the lockfile and restore the build
- [ ] #108 — 0.5 Add the CI workflow  ·  depends on #104, #107
- [ ] #109 — 0.6 Pin the Node runtime  ·  ⚠ unknown dep 0.9

**Critical path:** #101 ✅ → #102 ✅ → #104 ✅ → #118 ○

**Next actionable** — open, every dependency closed: #105, #106, #107

### Deferred and out of scope

| Finding | Severity | Why deferred | Revisit when |
|---|---|---|---|
| F-DEP-009 | Medium | upstream v4 unreleased | when v4 ships |

<sub>Rendered by `/plan-to-issues` — refresh with `/plan-to-issues sync 100`</sub>
<!-- plan-dashboard:end -->
```

### Rules the layout must hold

- **Checklist grammar is fixed:** `- [x] #<n> — <task-id> <title>`, em-dash `—` between number and
  task id (IDD SPEC §2.1 checklist form). Sync parses it back; a hyphen there breaks the parse.
- **Checkbox state mirrors the issue state**, never a guess: `[x]` closed, `[ ]` open,
  `- [ ] #N — <id> <title>  ·  ⚠ missing` when the number no longer resolves.
- **Phase order is plan order** — `Pre`, `P0` … `P4`. An empty phase renders as
  `— no tasks in plan`; a phase excluded by `--phase` renders as `— not filed`. Never drop a phase:
  a missing row reads as "done".
- **Milestone status** is derived, not stored: ✅ met (every task closed), ◐ in progress (≥ 1 closed),
  ○ not started (none closed).
- **Progress bars are 10 cells**, `█` filled, `░` empty, rounded down so 99% never shows full.
- Sections with no rows (Deferred, Next actionable) are omitted rather than rendered empty.

## Render input schema

`scripts/render_dashboard.py` reads this on stdin and writes the block (sentinels included) to
stdout. It is deterministic: same input, same bytes.

```json
{
  "plan_path": "MODERNIZATION_PLAN.md",
  "baseline": "AMBER — builds; 41/58 tests pass",
  "synced": "2026-08-26",
  "epic": 100,
  "critical_path": ["Pre.1", "Pre.2", "0.1", "2.4"],
  "phases": [
    {
      "id": "Pre",
      "title": "Agent environment",
      "goal": "project env an AI agent can use autonomously",
      "filed": true,
      "milestone": { "id": "ME", "exit": "CLAUDE.md and AGENTS.md exist" },
      "tasks": [
        { "task_id": "Pre.1", "title": "Make the project environment agent-runnable",
          "issue": 101, "state": "closed", "depends_on": [], "unknown_deps": [] }
      ]
    }
  ],
  "deferred": [
    { "id": "F-DEP-009", "severity": "Medium", "why": "upstream v4 unreleased", "revisit": "when v4 ships" }
  ]
}
```

`state` is one of `open`, `closed`, `missing`. `issue` is `null` for a task that was not filed.
`synced` is supplied by the caller (`date -u +%Y-%m-%d`) — the renderer never reads the clock, so its
output stays reproducible.

## Sync algorithm

```bash
gh issue view <epic> --json body --jq '.body' > epic-body.md          # 1. fetch
grep -c 'plan-dashboard:start' epic-body.md                           # 2. gate: must be 1
grep -oE '#[0-9]+ — [A-Za-z0-9.]+' epic-body.md                       # 3. children + task ids
gh issue list --state all --limit 500 --json number,state,title       # 4. live states, one call
python3 scripts/render_dashboard.py < dashboard-input.json            # 5. re-render
gh issue edit <epic> --body-file epic-body-updated.md                 # 6. write back
gh issue view <epic> --json body --jq '.body' | grep -c 'plan-dashboard'  # 7. verify: must be 2
```

Between 4 and 5: a dashboard number absent from the live list becomes `state: "missing"`; a plan
task with no dashboard entry becomes an **unmapped** task, listed under `Not filed` and reported with
the hint to re-run Create mode. Sync files nothing itself — one mode, one mutation class.

Step 6 uses `--body-file`, not `--body`: a 50-issue dashboard passed as an argument can exceed
`ARG_MAX`, and the failure is a truncated epic body.
