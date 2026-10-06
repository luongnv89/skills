---
name: drawio-generator
description: "Generate professional diagrams as valid draw.io XML — flowcharts, architecture, C4 models, ER diagrams, sequence diagrams, mind maps, and swimlanes. Don't use for Excalidraw or Mermaid output, hand-drawn sketch styles, or slide decks/presentations."
license: MIT
effort: high
metadata:
  version: 1.4.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Draw.io Diagram Generator

Generate professional diagrams as valid draw.io XML. Every request flows through four phases — **Understand**, **Propose**, **Generate**, **Validate** — before the file is written. Body content is intentionally lean to respect the agent's context budget; depth lives in `references/`.

> Part of the **diagram-generator** suite. For a hand-drawn / sketch look, use `excalidraw-generator` instead; the `diagram-generator` umbrella routes between the two.

## Environment Check

If the Agent tool is available, use subagents per *Subagent Architecture* for large diagrams; fresh-context validation avoids single-pass context overflow. Without it (e.g., Claude.ai), run every phase inline and self-review against the 9 checks.

## Repo Sync Before Edits (mandatory)

Run this once: before reading an existing `.drawio` file (*Iteration*), otherwise before the Phase 4 write. The sync target is the output file's directory.

1. Run `repo="$(git -C "<output dir>" rev-parse --show-toplevel)"`. If it fails, skip the sync and record `sync: skipped (not a git repo)`.
2. Run `git -C "$repo" remote get-url origin`. If it fails, skip steps 3–6 and record `sync: skipped (no origin)`.
3. Run `branch="$(git -C "$repo" rev-parse --abbrev-ref HEAD)"`. If it prints `HEAD`, skip steps 4–6 and record `sync: skipped (detached HEAD)`.
4. Run `git -C "$repo" status --porcelain`. If the output is empty, run `git -C "$repo" fetch origin && git -C "$repo" pull --rebase origin "$branch"`.
5. If the output is not empty, run `git -C "$repo" stash push -u -m "drawio-generator pre-sync"`, then the same fetch and pull, then `git -C "$repo" stash pop`.
6. If the rebase conflicts, run `git -C "$repo" rebase --abort`, then `git -C "$repo" stash pop` when step 5 stashed. If the stash pop conflicts, leave the stash in place. In both cases do not write the file; stop and ask the user how to continue. With no answer, the status is `BLOCKED`.

This skill writes one file and commits nothing.

## Core Workflow

### Phase 1: Understand

Confirm what to draw before generating anything.

- **Clear request** — restate briefly and propose a visualization type:
  > "I'll create a C4 container diagram with a layered layout: API gateway on top, services in the middle, databases at the bottom. Sound good?"
- **Ambiguous input** — ask targeted questions: main entities, relationships, flow direction, multi-page need.
- **Code, schema, or config provided** — extract structure:
  - Code → class/dependency/architecture
  - SQL/schema → ER diagram
  - JSON/YAML config → architecture, deployment
  - Steps/process → flowchart, sequence

### Phase 2: Propose

Present the numbered plan below.

- If the request names the diagram type and every element, state the defaults you chose in one line and proceed to Phase 3.
- Otherwise, wait for the user to confirm or change the plan. Do not generate XML before the user answers.

1. **Diagram type** (offer alternatives if multiple fit)
2. **Key elements** — list nodes/shapes
3. **Layout** — e.g. `(A) Top-to-bottom`, `(B) Left-to-right`, `(C) Layered`
4. **Style** — `(1) Professional`, `(2) C4 official`, `(3) Monochrome`
5. **Multi-page?** — for C4, offer one page per level
6. **Estimated complexity** — small (<10), medium (10–30), large (30+)

### Phase 3: Generate

Generate the draw.io XML in memory. Phase 4 writes the file.

Output path: use the path the user gave. Otherwise use a descriptive kebab-case name ending in `.drawio` (`auth-flow.drawio`) in the current working directory. If that file exists and the user did not ask to update it, confirm with the user before you overwrite it; to update it, follow *Iteration*.

Read `references/xml-authoring.md` for shape/edge/container syntax, sizing rules, multi-page structure, and file naming. Read `references/drawio-format.md` for the full XML schema and color palettes.

Critical rules every shape must follow:
- Always include `html=1;whiteSpace=wrap;` in the style string
- Use descriptive kebab-case IDs (`node-api-gateway`)
- Provide `<mxGeometry x y width height as="geometry"/>` sized to fit the label
- Edges need `source`, `target`, and `<mxGeometry relative="1" as="geometry"/>`

### Phase 4: Validate

Run all 9 checks before writing the file. See `references/validation-checks.md` for the full check list and fix patterns.

1. Run the 9 checks. If all pass, run *Repo Sync*, write the file, and give the *Final Report* with status `COMPLETE`.
2. If a check fails, fix it and re-run all 9 checks. A failure of check 1 or 8 needs a Phase 3 regeneration, not a patch. Stop after 3 fix cycles.
3. If checks 1–5 pass but a check from 6–9 still fails after cycle 3, run *Repo Sync*, write the file, and report `PARTIAL` with the failed check numbers.
4. If check 1–5 still fails after cycle 3, do not write the file. Report `BLOCKED` with the failed checks.

The 9 checks: (1) XML structure and system cells, (2) required shape attributes, (3) unique IDs per page, (4) edge bindings, (5) edge geometry, (6) no overlaps >10px, (7) container hierarchy, (8) semantic completeness, (9) readable text and fitted shapes.

---

## Expected Output

A valid `.drawio` file written to disk (raw XML), then the *Final Report*. A minimal complete file is in `references/xml-authoring.md` → *Minimal complete file*.

## Final Report

End every run, stops included, with this compact text block. A Phase 1–2 question that awaits the user's answer does not end the run; if the user ends the run without answering, report `BLOCKED`. Status is `COMPLETE` (file written, 9/9 checks pass), `PARTIAL` (file written, a check from 6–9 failed), or `BLOCKED` (no file written). Fill rules, `PARTIAL` and `BLOCKED` examples, and reader checks: `references/final-report.md`. Example:

```
Result: COMPLETE. Wrote flow.drawio (1 page, 2 shapes, 1 edge, 0 containers).
Evidence: /abs/path/flow.drawio. Validation 9/9 checks passed (inline, 1 cycle). sync: skipped (not a git repo)
Uncertainty: Rendering in draw.io untested. Assumed top-to-bottom flow; the request gave no direction.
Decision: No approval needed.
```

## Acceptance Criteria

Verify these for every run:

- [ ] A `.drawio` file is written to disk and its XML parses, unless the status is `BLOCKED`.
- [ ] Checks 1–7 and 9 in `references/validation-checks.md` pass on every page, or the Final Report lists each failed check.
- [ ] Every entity and relationship in the user's request is represented in the output (check 8).
- [ ] The Final Report opens with `Result:` and its status, and has `Evidence:`, `Uncertainty:` and `Decision:` lines. `Evidence:` cites only checks that ran; `9/9` appears only when all 9 passed.
- [ ] The Final Report passes the four reader checks in `references/final-report.md` (result findable, facts and assumptions separated, claims traceable, next decision clear). Without a human reviewer's answer, human understanding is unconfirmed.

## Edge Cases

- **Empty or vague input** ("make a diagram"): ask targeted clarifying questions before generating — never produce a placeholder.
- **Very large diagram (>50 elements)**: warn that one page will be crowded; offer multi-page or hierarchical C4.
- **Unsupported diagram type** (e.g., Gantt with real date-axis ticks): explain the limitation and propose the closest supported alternative (e.g., swimlane timeline).
- **User supplies an existing `.drawio` file**: read it first, preserve existing cell IDs, append new elements — never regenerate from scratch.
- **Conflicting layout constraints**: surface the conflict and ask which takes priority.
- **Cross-page ID collision**: each `<diagram>` has its own ID namespace; system cells `id="0"` and `id="1"` must be present on every page independently.
- **Text exceeds shape capacity**: auto-grow shape height ~20px per extra line rather than letting text overflow silently.

---

## Step Completion Reports

After each phase, print a short status report with that phase's checks; the template and per-phase checks are in `references/step-reports.md`. The Validate report precedes the *Final Report*; it does not replace it.

## Styles and Diagram Types

Default style is Professional; C4 requests use the official C4 palette. Color rules and the supported diagram types: `references/xml-authoring.md` → *Style guidelines* and *Supported diagram types*.

## Iteration

When iterating on an existing diagram, read the file and modify the XML in memory. Preserve element IDs that haven't changed. Run Phase 4 on the result before rewriting the file; a `BLOCKED` result leaves the original file untouched.

---

## Subagent Architecture

Use the Phase 2 complexity estimate: large (30+ elements) runs this subagent loop; small and medium run inline.

**Phase 3 — `agents/xml-generator.md`**
- Receives: diagram type, elements, edges, style, complexity
- Outputs: complete draw.io XML with all required attributes
- Constraint: shapes sized to fit text labels

**Phase 4 — review loop (max 3 cycles)**

1. **Validate** — spawn `agents/xml-validator.md`. Outputs PASS/FAIL for all 9 checks.
2. **Fix** — if NEEDS_FIX, spawn `agents/xml-fixer.md` with the report. Patches XML; never regenerates. Skips semantic/structure issues (those require generator revision).
3. **Re-validate** with cycle++ until PASS or cycle == 3. If the fixer returns `ready_for_validation: false` (check 1 or 8), re-spawn `agents/xml-generator.md` with the validator report; that counts as a cycle.
4. Return the XML and the last validator report to the main agent, which applies Phase 4 steps 1–4 (write, `PARTIAL`, or `BLOCKED`).
