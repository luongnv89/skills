---
name: excalidraw-generator
description: "Generate diagrams as valid Excalidraw JSON — flowcharts, architecture, ER diagrams, mind maps, sequence diagrams, wireframes, C4 models, and more. Don't use for draw.io/Mermaid output, slide decks, or pixel-perfect brand graphics."
license: MIT
effort: high
metadata:
  version: 1.5.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Excalidraw Diagram Generator

Generate professional diagrams as valid Excalidraw JSON. Every request flows through four phases — **Understand**, **Propose**, **Generate**, **Validate** — before the file is written. The body stays lean to respect the agent's context budget; depth lives in `references/`.

> Part of the **diagram-generator** suite. For precise, editable-in-draw.io output, use `drawio-generator` instead; the `diagram-generator` umbrella routes between the two.

## When to Use

The frontmatter `description` sets triggers and exclusions. Output: a `.excalidraw` file, plus a companion `.md` only on request.

## Environment Check

If the Agent tool is available, use subagents per *Subagent Architecture* for large diagrams; fresh-context validation avoids single-pass context overflow. Without it (e.g., Claude.ai), run every phase inline and self-review against the 10 checks.

## Repo Sync Before Edits (mandatory)

Run this once: before reading an existing `.excalidraw` file (*Iteration*), otherwise before the Phase 4 write. The sync target is the output file's directory.

1. Run `repo="$(git -C "<output dir>" rev-parse --show-toplevel)"`. If it fails, skip the sync and record `sync: skipped (not a git repo)`.
2. Run `git -C "$repo" remote get-url origin`. If it fails, skip steps 3–7 and record `sync: skipped (no origin)`.
3. Run `branch="$(git -C "$repo" rev-parse --abbrev-ref HEAD)"`. If it prints `HEAD`, skip steps 4–7 and record `sync: skipped (detached HEAD)`.
4. Run `git -C "$repo" status --porcelain`. If the output is empty, run `git -C "$repo" fetch origin && git -C "$repo" pull --rebase origin "$branch"`.
5. If the output is not empty, run `git -C "$repo" stash push -u -m "excalidraw-generator pre-sync"`, then the same fetch and pull, then `git -C "$repo" stash pop`.
6. If `fetch` or `pull` fails before a rebase starts (network, authentication, or a missing remote branch), do not retry. Run `git -C "$repo" stash pop` when step 5 stashed, record `sync: failed (<first error line>)`, and continue. The Final Report repeats it on the `Uncertainty:` line.
7. If the rebase conflicts, run `git -C "$repo" rebase --abort`, then `git -C "$repo" stash pop` when step 5 stashed. If the stash pop conflicts, leave the stash in place. In both cases do not write the file; stop and ask the user how to continue. With no answer, the status is `BLOCKED`.

This skill commits nothing.

## Core Workflow

### Phase 1: Understand

Confirm what to draw before generating anything.

- **Clear request** — restate it in one sentence and propose a visualization type.
- **Ambiguous input** — ask about entities, relationships, flow direction, style.
- **Code, data, schemas, or files** — extract structure (SQL → ER, steps → flowchart; full mapping in `references/diagram-types.md`).

### Phase 2: Propose

Present the numbered plan below.

- If the request names the diagram type and every element, or the user says "just do it", state the defaults you chose in one line and proceed to Phase 3. Defaults: hand-drawn, `roughness: 1`, Virgil font (`fontFamily: 1`), best-fit layout.
- Otherwise, wait for the user to confirm or change the plan. Do not generate JSON before the user answers.

1. **Diagram type** — catalogue in `references/diagram-types.md`; offer numbered alternatives if several fit.
2. **Key elements** — list the nodes and shapes.
3. **Layout** — e.g. `(A) Top-to-bottom`, `(B) Left-to-right`, `(C) Radial`.
4. **Style** — rendering style (hand-drawn, sketchy, clean) and a color scheme that fits the purpose; variants in `references/style-and-iteration.md`. No fixed palette.
5. **Estimated complexity** — small (<10 elements), medium (10–30), large (>30).

### Phase 3: Generate

Compose the `.excalidraw` document in memory (raw JSON, no wrapper). Phase 4 writes the file.

Output path: use the path the user gave. Otherwise use a descriptive kebab-case name ending in `.excalidraw` (`auth-flow.excalidraw`) in the current working directory. If that file exists and the user did not ask to update it, confirm with the user before you overwrite it; to update it, follow *Iteration*.

Start from the envelope in `references/excalidraw-format.md` → *Top-Level Structure* (`type`, `version`, `source`, `elements`, `appState`, `files`); set `theme` and `viewBackgroundColor` to suit the diagram. That file holds the full element schema and field defaults.

Critical rules every element must follow:
- Include every required field from `references/validation-checks.md` → *Check 2*.
- Use descriptive kebab-case IDs (`node-api-gateway`).
- Size each container to fit its bound text (*Check 10*); grow the shape, never shrink the text below `fontSize: 16`.
- Bind text and arrows in both directions (`containerId` ↔ `boundElements`, `startBinding`/`endBinding` ↔ `boundElements`).

**Embedding in Markdown:** only when asked, write the `.excalidraw` file first, then a companion `.md` holding the same JSON in a fenced block tagged `excalidraw`.

### Phase 4: Validate

Run all 10 checks on the in-memory JSON before writing the file. See `references/validation-checks.md` for checks, the Check 10 formula, and fixes.

1. Run the 10 checks. If all pass, run *Repo Sync*, write the file, and give the *Final Report* with status `COMPLETE`.
2. If a check fails, fix it and re-run all 10 checks. A failure of check 1 or 8 needs a Phase 3 regeneration, not a patch. Stop after 3 fix cycles.
3. If checks 1–6 pass but a check from 7–10 still fails after cycle 3, run *Repo Sync*, write the file, and report `PARTIAL` with the failed check numbers.
4. If a check from 1–6 still fails after cycle 3, do not write the file. Report `BLOCKED` with the failed checks.

The 10 checks: (1) JSON envelope, (2) required fields, (3) unique IDs, (4) text bindings, (5) arrow bindings, (6) arrow points, (7) overlaps, (8) semantic completeness, (9) readable text, (10) shape-to-text fit — the most common failure.

---

## Expected Output

For "draw a flowchart of the user login process": a `login-flow.excalidraw` file written to disk (raw JSON), then the *Final Report*. A bound shape-and-label pair is in `references/excalidraw-format.md` → *Minimal bound-text example*.

## Final Report

End every run, stops included, with this compact text block. A Phase 1–2 question that awaits the user's answer does not end the run; if the user ends the run without answering, report `BLOCKED`. Status is `COMPLETE` (file written, 10/10 checks pass), `PARTIAL` (file written, a check from 7–10 failed), or `BLOCKED` (no file written). Fill rules, `PARTIAL` and `BLOCKED` examples, and reader checks: `references/final-report.md`. Example:

```
Result: COMPLETE. Wrote login-flow.excalidraw (6 shapes, 6 text labels, 5 arrows).
Evidence: /abs/path/login-flow.excalidraw. Validation 10/10 checks passed (inline, 1 cycle). sync: skipped (not a git repo)
Uncertainty: Rendering in Excalidraw untested. Assumed top-to-bottom flow; the request gave no direction.
Decision: No approval needed.
```

## Acceptance Criteria

Verify these for every run:

- [ ] A `.excalidraw` file is written to disk and its JSON parses with top-level `type`, `version`, `elements`, `appState`, `files`, unless the status is `BLOCKED`.
- [ ] Checks 1–7, 9 and 10 in `references/validation-checks.md` pass, or the Final Report lists each failed check.
- [ ] Every entity and relationship in the user's request is represented in the output (check 8).
- [ ] The Final Report opens with `Result:` and its status, and has `Evidence:`, `Uncertainty:` and `Decision:` lines. `Evidence:` cites only checks that ran; `10/10` appears only when all 10 passed.
- [ ] The Final Report passes the four reader checks in `references/final-report.md` (result findable, facts and assumptions separated, claims traceable, next decision clear). Without a human reviewer's answer, human understanding is unconfirmed.

## Edge Cases

- **Empty or vague input** ("make a diagram"): ask targeted clarifying questions before generating — never produce a placeholder.
- **Large diagram (>30 elements)**: run the *Subagent Architecture* loop; cap at 3 fix cycles.
- **Very large diagram (>50 elements)**: warn that one canvas will be crowded; offer frames, several files, or an overview first, and wait for the choice.
- **Ambiguous relationships**: ask for direction and cardinality before generating.
- **Unsupported diagram type** (e.g., a chart that needs real axis scales): explain the limitation and propose the closest supported type from `references/diagram-types.md`.
- **User supplies an existing `.excalidraw` file**: follow *Iteration* — never regenerate it from scratch.

More edge cases: `references/style-and-iteration.md`.

---

## Step Completion Reports

After each phase, print a short status report with that phase's checks; the template and per-phase checks are in `references/step-reports.md`. The Validate report precedes the *Final Report*; it does not replace it.

## Iteration

When iterating on an existing diagram, read the file and modify the JSON in memory. Preserve element IDs that haven't changed (request patterns: `references/style-and-iteration.md` → *Iteration*). Run Phase 4 on the result before rewriting the file; a `BLOCKED` result leaves the original file untouched.

---

## Subagent Architecture

Large diagrams (>30 elements) run this loop; others run inline. Detail: `references/style-and-iteration.md` → *Subagent Architecture*.

1. **Generate** — spawn `agents/json-generator.md` with the confirmed plan.
2. **Validate** — spawn `agents/json-validator.md`; it reports PASS/FAIL for all 10 checks.
3. **Fix** — on NEEDS_FIX, spawn `agents/json-fixer.md`, which patches and never regenerates. If it returns `ready_for_validation: false` (check 1 or 8), re-spawn the generator instead. Each fix or regeneration is one cycle; stop at 3.
4. The main agent applies Phase 4 steps 1–4 to the returned JSON and last validator report.

