# Final Report

The closing output of every diagram-generator run, stops included. `SKILL.md` (*Final Report*) holds
the status rule; this file holds the umbrella's own templates, the fill rules, and the reader checks.

## When an engine ran

The routed engine's Final Report is the closing output. Relay its four lines verbatim. The engine
owns the status (`COMPLETE`, `PARTIAL` or `BLOCKED`), the validation count, and the file path; the
umbrella never re-grades them. The engine's `BLOCKED` (for example, a failed structural check or a
declined overwrite) stays `BLOCKED`.

Add at most one line after the relayed report, and only when the lease release failed:

```text
Router note: asm deps release failed for session diagram-generator-1791323441-4242; run asm deps release --session diagram-generator-1791323441-4242 --json.
```

With **Both formats**, relay each engine's Final Report in the order the engines ran.

## When the umbrella stopped before any engine ran

The status is always `BLOCKED`, because no file was written. Use one of these three templates.

### Out of scope

```text
Result: BLOCKED. Not routed: Mermaid is out of scope for diagram-generator.
Evidence: Routing rule 1 matched ("as a Mermaid diagram"). No engine ran and no file was written.
Uncertainty: None. No preflight or sync ran.
Decision: No approval needed. Write Mermaid directly in Markdown, or ask for a draw.io or Excalidraw diagram instead.
```

### Unanswered routing question

```text
Result: BLOCKED. No diagram written: the engine choice was not answered.
Evidence: No format signal matched rules 1-5. Asked "Precise and editable (draw.io) or hand-drawn sketch (Excalidraw)?" twice with no answer.
Uncertainty: No engine ran, so no file was generated or validated.
Decision: Choose draw.io or Excalidraw, or say "just pick", then re-run.
```

### Missing engine

```text
Result: BLOCKED. No diagram written: excalidraw-generator is not installed.
Evidence: Routed to excalidraw-generator (rule 5, "sketchy wireframe"). Preflight dg_mode=installed; neither ~/.claude/skills/excalidraw-generator/SKILL.md nor ~/.agents/skills/excalidraw-generator/SKILL.md exists.
Uncertainty: No engine ran, so no file was generated or validated.
Decision: Install excalidraw-generator with the printed command, then re-run. draw.io output is available only if you ask for it.
```

## Fill rules

- `Result:` comes first, and its first word after `Result:` is the status.
- `Evidence:` names the routing rule that matched, the user's words that matched it, and the
  preflight mode and outcome when the preflight ran. Cite only checks that ran.
- `Uncertainty:` states that no file was generated or validated. Add a failed release here.
- `Decision:` names the one action that unblocks the run. Name the other engine only as an option
  the user may request; never as a switch already made.

## Reader checks

Grade every closing report against these four checks. Negative-trigger cases, where the skill was
not applied, are excluded.

| Check | Observable evidence |
|---|---|
| Main result is findable | The first line gives the status and whether a file was written. |
| Facts and assumptions are separated | `Evidence:` names checks that ran; `Uncertainty:` holds what did not run and any assumption. |
| Claims are traceable | Each claim points to a routing rule, a preflight outcome, or the engine's file path and check count. |
| Next decision is clear | `Decision:` names the required action, or says `No approval needed.` |

Agent inspection cannot confirm human understanding. Ask a reviewer whether they could find the
result, separate facts from assumptions, trace claims, and identify the next decision. Without an
answer, record human understanding as unconfirmed.
