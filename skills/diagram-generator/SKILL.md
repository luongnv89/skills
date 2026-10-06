---
name: diagram-generator
description: "Generate a diagram and route to the right engine — draw.io XML (precise, editable, C4, swimlanes) or Excalidraw JSON (hand-drawn, sketch, wireframes). One entry for flowcharts, architecture, ER, sequence, mind maps. Don't use for Mermaid or slides."
license: MIT
effort: high
dependencies:
  - drawio-generator
  - excalidraw-generator
metadata:
  version: 1.4.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Diagram Generator

Single entry point for "make me a diagram". This umbrella picks one engine and hands the request to
it. Both engines cover the same diagram types (flowchart, architecture, C4, ER, sequence, mind map)
through the same four phases (**Understand → Propose → Generate → Validate**); they differ only in
**output format and aesthetic**. The umbrella writes no file itself. Its body stays short to protect
the agent's context window; report templates live in `references/`.

## Which engine?

| Engine | When the user wants... | Output |
|---|---|---|
| `drawio-generator` | Precise, professional diagrams to edit later in draw.io / diagrams.net / Confluence; official C4 styling; swimlanes; multi-page | kebab-case `.drawio` file (XML) |
| `excalidraw-generator` | A hand-drawn, sketchy, whiteboard feel; wireframes; quick collaborative sketches | kebab-case `.excalidraw` file (JSON) |

Apply the routing rules in order and stop at the first rule that matches:

1. The request asks for **Mermaid**, a slide deck, or brand/marketing graphics → do not route. Write
   the out-of-scope Final Report (Mermaid is native Markdown; use a presentation or design tool for
   the others).
2. The request updates an existing file → route by its extension: `.drawio` → `drawio-generator`,
   `.excalidraw` → `excalidraw-generator`.
3. The request names exactly one tool or editing target ("draw.io", "diagrams.net", "Confluence",
   "Excalidraw") → route to that engine, even when the aesthetic words point to the other one.
4. The request names both tools → if it asks for both files, follow *Edge Cases → Both formats*;
   otherwise ask the routing question in rule 6.
5. The request asks for a hand-drawn, sketch, whiteboard, or wireframe look → `excalidraw-generator`.
6. No format signal → ask one question: "Precise and editable (draw.io) or hand-drawn sketch
   (Excalidraw)?" Wait for the answer. If the user explicitly delegates ("just pick", "choose for
   me", "use the default"), route architecture, C4, ER, sequence, and swimlane diagrams to
   `drawio-generator`, and wireframes, brainstorms, and mind maps to `excalidraw-generator`.
   Anything else that is delegated goes to `drawio-generator`.

Silence is not delegation. Ask content questions (entities, relationships, direction) only inside
the engine's Phase 1, never in the umbrella.

## Dependency Preflight (mandatory)

This skill invokes the two engines declared in frontmatter `dependencies`, but each run needs only
the one that routing selects. Run this once, after routing and before the engine starts:

```bash
if command -v asm >/dev/null && asm deps --help >/dev/null 2>&1; then
  asm deps discover diagram-generator --json || echo "discover failed; acquire still runs" >&2
  echo "dg_mode=lease"
else
  echo "asm deps unavailable: npm install -g agent-skill-manager@latest" >&2
  echo "dg_mode=installed"
fi
printf 'dg_session=%s\n' "diagram-generator-$(date +%s)-$$"   # record it; reuse it verbatim
```

1. With `dg_mode=lease`, run `asm deps acquire <engine> --session <dg_session> --json` for the
   routed engine only. Record the returned `skillMdPath`.
2. With `dg_mode=installed`, run
   `test -f "$HOME/.claude/skills/<engine>/SKILL.md" || test -f "$HOME/.agents/skills/<engine>/SKILL.md"`
   and record the path that exists.
3. If step 1 or 2 fails, print
   `Missing skill: <engine> — install: asm install github:luongnv89/skills:skills/diagram-generator/<engine> -p claude --yes`,
   then stop with the missing-engine Final Report. Never substitute the other engine. Never
   imitate the engine inline.
4. **Release in `finally`.** If any acquire ran, run `asm deps release --session <dg_session> --json`
   once at every terminal outcome, stops included, after the closing Final Report.

Do not acquire the engine that routing did not select.

## Repo Sync Before Edits (mandatory)

The umbrella runs no git command and writes no file. The routed engine runs its own *Repo Sync
Before Edits* (scoped to the output file's repository, with its conflict and network-failure rules)
before it writes. Do not run a second sync here, and do not skip the engine's sync.

## Workflow

1. Apply the routing rules. If rule 1 matches, write the out-of-scope Final Report and stop.
2. If rule 4 or 6 asks the routing question, wait for the answer. If the user has not answered
   after the question was asked twice (*Edge Cases*), write the unanswered-routing Final Report
   and stop.
3. Print one line: `Routing to <engine>: <the rule that matched, in the user's words>.`
4. Run the *Dependency Preflight*.
5. Read the recorded `SKILL.md` path and follow that engine's workflow with the user's request
   unchanged. The engine owns its questions, file naming, Repo Sync, validation, and fix cycles.
   It also asks for confirmation before it overwrites an existing file; never skip or pre-answer
   that confirmation.
6. Relay the engine's Final Report as the run's closing output (*Final Report* below).
7. Run the release step of the *Dependency Preflight*.

## Final Report

Both engines end every run, stops included, with a four-line Final Report (`Result:` COMPLETE |
PARTIAL | BLOCKED, `Evidence:`, `Uncertainty:`, `Decision:`). When an engine ran, its Final Report
is this skill's closing output. Relay it verbatim: do not restate it, re-grade it, or change its
status. If the release step fails, add one line after the closing report, whichever skill wrote it:
`Router note: asm deps release failed for session <dg_session>; run asm deps release --session <dg_session> --json.`

When the umbrella stops before any engine runs (out of scope, unanswered routing question, missing
engine), it writes its own four-line report with status `BLOCKED`. Templates and fill rules:
`references/final-report.md`. Expected output when the routed engine is missing:

```text
Result: BLOCKED. No diagram written: drawio-generator is not installed.
Evidence: Routed to drawio-generator (rule 3, "in draw.io"). Preflight dg_mode=lease; asm deps acquire drawio-generator failed.
Uncertainty: No engine ran, so no file was generated or validated.
Decision: Install drawio-generator with the printed command, then re-run. Excalidraw output is available only if you ask for it.
```

## Example

```text
Input:   "Draw a sketchy onboarding wireframe for mobile."
Route:   Routing to excalidraw-generator: rule 5, "sketchy wireframe".
Closing: excalidraw-generator's Final Report, relayed unchanged, e.g.
         Result: COMPLETE. Wrote mobile-onboarding-wireframe.excalidraw (...)
```

## Acceptance Criteria

Verify these for every run:

- [ ] Routing follows the first matching rule. Exactly one engine runs, unless the user asked for
      both files.
- [ ] The routed engine matches the requested tool, existing file extension, or aesthetic, and the
      `Routing to` line names the matching rule.
- [ ] The preflight acquires or checks only the routed engine. A missing engine stops the run with
      no file written and no substitution.
- [ ] When an engine ran, the closing output is that engine's Final Report, unchanged.
- [ ] When the umbrella stopped, its report opens with `Result: BLOCKED` and has `Evidence:`,
      `Uncertainty:` and `Decision:` lines.
- [ ] The closing report passes the four reader checks in `references/final-report.md` (result
      findable, facts and assumptions separated, claims traceable, next decision clear). Without a
      human reviewer's answer, human understanding is unconfirmed.

## Edge Cases

- **Both formats** — run the engine the user named first, or `drawio-generator` when no order was
  given. After its Final Report, run the other engine on the same content without asking again,
  because the user already asked for both: acquire it under the same `dg_session`. If the first
  engine ended `BLOCKED`, ask before running the second. Relay each engine's Final Report in turn.
- **Unanswered routing question** — ask it once more. Silence or a timeout is not delegation. If the
  user still does not answer, write the unanswered-routing Final Report.
- **Routed engine unavailable** — the preflight stops the run. Name the other engine as an option
  the user may request explicitly, and never switch to it on your own.
- **Request for an image file** (PNG, SVG) — say that both engines write an editable file that its
  editor can export to PNG or SVG. If the user accepts that, continue with the routing rules.
  Otherwise write the out-of-scope Final Report.
