---
name: code-review
description: "Review or improve code — one skill, four modes: bug/security review (default), performance, clean-code audit, slop cleanup. Pass mode:review|perf|clean|cleanup or infer. Don't use for writing features or generating tests (use test-coverage)."
license: MIT
effort: high
metadata:
  version: 2.0.1
  author: "Luong NGUYEN <luongnv89@gmail.com>"
  architecture: "router (4 modes, each a self-contained workflow in references/)"
---

# Code Review

One skill for reviewing and improving code quality. Pick a **mode** by intent (or pass an explicit
`mode:` parameter); each mode is a full, self-contained workflow in `references/`. Load only the
mode you need — this protects the agent's context budget.

## Modes

| Mode | Use when the user wants to... | Reads / writes | Output | Workflow |
|---|---|---|---|---|
| **review** (default) | find bugs, security holes, quality issues in a diff/PR | read-only | prioritized findings report | `references/review-mode.md` |
| **perf** | make code faster — bottlenecks, leaks, algorithmic waste | read-only | performance findings report | `references/perf-mode.md` |
| **clean** | audit readability/standards vs the bbv Clean Code cheat sheet | read-only | `CLEAN_CODE_AUDIT.md` | `references/clean-mode.md` |
| **cleanup** | actually refactor out AI slop, dead code, duplication, cruft | **WRITES CODE** | modified source files | `references/cleanup-mode.md` |

## Selecting the mode

1. **Explicit wins.** If the request carries `mode:review|perf|clean|cleanup` (or `--mode <name>`), use it.
2. **Otherwise infer** from the request:
   - "review", "find bugs", "security", "is this correct", "look for vulnerabilities" → **review**
   - "slow", "faster", "optimize", "bottleneck", "memory leak", "performance" → **perf**
   - "clean code", "readability", "audit against standards", "clean-code audit" → **clean**
   - "remove slop", "clean up the codebase", "refactor out cruft / dead code / duplication" → **cleanup**
3. **Ambiguous?** Ask which mode, naming the options. Fall back to **review** only when the intent is
   clearly "review this" with no other signal.

## Safety: cleanup writes code — the other three do not

`review`, `perf`, and `clean` are strictly **read-only**: they analyze and report, never touching
source. `cleanup` **modifies files**. Therefore:

- **Never enter `cleanup` by weak inference.** Run it only when the user explicitly asks to
  refactor / clean up the codebase (or passes `mode:cleanup`). A plain "review my code" must never
  rewrite files — stay in a read-only mode.
- **Confirm before the first write** in `cleanup`, and follow that mode's own gating.

## Repo Sync Before Edits

The router itself is read-only. The two modes that touch a git repo carry the mandatory
sync-before-edits step in their own workflow: `cleanup` (writes source) in `references/cleanup-mode.md`
and `clean` (writes `CLEAN_CODE_AUDIT.md`) in `references/clean-mode.md`. Before either mode edits,
follow that reference's Repo Sync step — sync with remote (stash-first if the tree is dirty) so writes
land on top of the latest base.

## Run the mode's workflow

Read the selected mode's reference file and execute its steps exactly. Supporting files each mode
uses (already colocated under this skill):

- **review** → `references/review-mode.md` — agents `agents/reviewer.md`, `agents/file-reviewer.md`, `agents/report-assembler.md`; refs `references/subagent-architecture.md`, `references/code-smells.md`
- **perf** → `references/perf-mode.md` — ref `references/language-checks.md`
- **clean** → `references/clean-mode.md` — refs `references/clean-code-checklist.md`, `references/tdd-checklist.md`, `references/html-report-guide.md`, `references/report-template.html`
- **cleanup** → `references/cleanup-mode.md` — the 8 cleaner agents in `agents/` (`deduplicator.md`, `type-consolidator.md`, `unused-code-killer.md`, `circular-dep-untangler.md`, `weak-type-strengthener.md`, `defensive-programming-remover.md`, `legacy-code-remover.md`, `slop-comment-cleaner.md`)

## Environment Check

If the Agent tool is available, modes that use subagents (**review**, **cleanup**) spawn them per
their workflow — fresh-context validation and parallel work. If it is unavailable (e.g., Claude.ai),
execute each mode's phases inline (less rigorous, but functional).

## Chaining modes

Modes compose: a common flow is **clean** (audit → `CLEAN_CODE_AUDIT.md`) then **cleanup** (apply the
refactors), or **review**/**perf** to find issues before fixing. Run one mode at a time; confirm with
the user before switching into the code-writing `cleanup` mode.
