# Vocabulary and Configuration — /issue-work-loop

Lookup material for the loop. The body links here rather than inlining it, so it stays out of the context window until a term or key is actually needed.

## Leading words

- **ISSUE** — implementer resolves an open issue, then reviewer/fix rounds
- **PR** — reviewer-first loop on an existing open PR; linked issue is optional
- **ROUND** — one review plus its optional fix
- **FINDING** — any reviewer item, including notes and partials
- **CLEAN** — explicit clean verdict with zero FINDINGS
- **FIXER** — PR-mode writer, created only after the first FINDINGS verdict and push-safety gate
- **FRESHEN** — restart one worker with a compact handoff at the context gate
- **SWEEP** — close spawned panes, remove loop worktrees, return main repo to default branch
- **USER-MERGE** — final open-PR handoff; the human decides whether to merge

## Configuration keys

Optional `.gitissue.yml` keys (defaults when absent):

| Key | Default | Role |
|---|---|---|
| `work_loop.max_rounds` | `5` | Maximum completed review ROUNDs |
| `work_loop.agent_cli` | `"claude"` | Interactive worker launcher; autonomy follows the per-harness boot-gate matrix |
| `work_loop.context_threshold` | `50` | FRESHEN at or above this percentage |
| `work_loop.implementer_name` | `"impl-{N}"` | ISSUE implementer pane |
| `work_loop.reviewer_name` | `"rev-{N}"` in ISSUE; `"rev-pr-{M}"` in PR | Reviewer pane |
| `work_loop.fixer_name` | `"fix-{M}"` | PR FIXER pane, lazily spawned |
| `work_loop.auto_cleanup` | `true` | Run SWEEP before handoff |

CLI flags override config. `--no-cleanup` sets `auto_cleanup: false` for debugging and leaves panes/worktrees. Print `○ First run — using default config` when `.gitissue.yml` is absent; do not modify the file.

