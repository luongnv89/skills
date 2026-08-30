---
name: doc-manager
description: "Generate or update docs to match the code, citing each claim to path:line and asking on ambiguity; runbook docs also get a check-only validation script. Don't use for API-reference autogen (JSDoc/Sphinx), landing pages, or CLAUDE.md/AGENTS.md."
license: MIT
effort: medium
metadata:
  version: 2.0.3
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Doc Manager

Keep a project's Markdown documentation **true to the code**. Every run ends with each doc `updated`, `verified-current`, or `flagged` — and every non-obvious claim traced to a source. Scope is Markdown only (`README.md`, `docs/*.md`, per-component READMEs); docstrings and comments are read as source-of-truth but not rewritten.

**Prime directive — never invent.** If the code does not show it and the user has not stated it, do not write it. When a fact is unclear or docs conflict with code, **ask the user**, then record the resolution in `docs/DECISIONS.md`. A guess is a defect here, not a convenience.

## Repo Sync Before Edits (mandatory)

Before creating/updating/deleting any file in the repo, sync the current branch:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin && git pull --rebase origin "$branch"
```

If the tree is dirty: `git stash push -u -m "pre-sync"` → sync → `git stash pop`. If `origin` is missing, or rebase/stash conflicts occur, **stop and ask** before continuing.

## Prerequisites

Validate before starting; if any fails, stop and surface it:

- **Git**: `git --version` ≥ 2.30. Working tree clean or stashable.
- **Remote**: `git remote get-url origin` resolves (needed for sync). If absent, ask before any pull/rebase.
- **Write access**: analysis needs read only. Writing files needs the tree to be writable; if read-only, emit a diff/summary instead of writing.
- **Mermaid** (optional): only if diagrams must be exported — `command -v mmdc`.

## Branch selector

Work one doc at a time. For each doc in the inventory, pick the path:

| Situation | Path |
|---|---|
| A needed doc does not exist | **A. Generate** |
| A doc exists but may not match the code | **B. Reconcile** |
| A doc **or a section of one** covers deploy / release / setup / operational process | also run **C. Runbook add-on** |

A single run usually mixes A and B across the inventory. C is additive — it layers onto whichever of A/B produced runbook content. Classify **at the section level**: a doc that mixes a runbook section with reference content gets C applied to the runbook section only, not the whole file.

## Workflow

### 0. Feature branch

1. If already on a task feature branch, skip.
2. Detect convention: `git branch -r | head -20` (`feat/`, `feature/`, …).
3. Create `feat/doc-manager` (or the repo's convention).

### 1. Inventory + scope

Read the codebase to establish ground truth, then build the doc inventory.

- **Project facts**: type (library/API/web/CLI/service), entry points, config, scripts, env vars, endpoints — each with its source location. This is your citation pool.
- **Existing docs**: every `README.md`, `docs/*.md`, per-component README.
- **Inventory table** — for each doc: `path | purpose | status(unknown) | is-runbook?`. Also list **needed-but-missing** docs implied by the code (e.g. code has a `deploy/` dir but no `docs/deployment.md`).

Present the inventory to the user and confirm scope before editing. **Do not silently expand** beyond confirmed scope.

### 2. Per-doc pass

For each doc, run its path. Cite as you write — do not defer citation to a review pass.

**A. Generate** — create from code analysis. Include only what the code (or a user answer) supports. Structure by relevance to project type; skip categories that don't apply.

**B. Reconcile** — diff doc against code:
- Claim matches code → keep; add a citation if missing, and **re-verify any existing `path:line` still resolves to the claimed fact** (line numbers rot when code above them shifts — repoint or FLAG stale cites).
- Claim contradicts code → fix to match code, cite the code.
- Claim unverifiable from code and not user-stated → **flag** inline (`<!-- FLAG: unverified — {what} -->`) and ask the user; never silently keep or delete.
- Doc fully current (every cite re-verified) → mark `verified-current`, touch nothing.

**Citation rule (checkable).** Every non-obvious factual claim carries an inline source. Forms, in order of preference:

- Single line — `src/server.ts:12` (a specific value: port, default, flag).
- Range / multi-source — `src/retry.ts:8-24` or `config.ts:4, env.ts:11` for an emergent fact that spans lines/files (e.g. "retries 3× with backoff", "config merges env > file > defaults"). This is a real citation, **not** a FLAG — FLAG is only for facts the code cannot confirm.
- Whole file — `src/router.ts` when the fact is the file's overall behavior and no line is more authoritative.

> The server listens on port 8080 (`src/server.ts:12`).

**Cite unless trivially obvious.** Default to citing; the burden is on treating a claim as obvious, not on citing it. Section intros and definitions of common terms are obvious. Anything a reader could get wrong — ports, commands, paths, env vars, versions, endpoints, defaults, behavior — is not. This coverage check is a **judgment pass** (grep can't verify it), so err toward over-citing: an uncited factual claim is the exception you must be able to justify.

**Decisions log.** Every ambiguity you ask about gets appended to `docs/DECISIONS.md`:

```markdown
## YYYY-MM-DD
- Q: {the ambiguity}
- A ({who}): {resolution}
- Source: `path:line` (if code-derived)
```

Use the run date; never fabricate one. Get it from the environment context, not a guess.

### 3. Runbook add-on (path C)

For any deploy/release/setup/operational doc, produce a **check-only** validation script and keep a troubleshooting log. Read `references/runbook-validation.md` for the script contract, template, and the fix→document loop. In short:

- **The validation script (`scripts/validate-<name>.sh`) is check/dry-run by default.** It verifies preconditions and asserts expected state idempotently. Every destructive or outward-facing step is gated behind `--run-destructive` or a `MANUAL:` marker — never auto-run.
- Script lives in the documented repo's `scripts/`, and the runbook section links to it. On a read-only tree, emit the script inline **and run it once** so you can report its `--check` outcome.
- Run it (`--check`). Classify each failure: if the doc/check is wrong, fix it; if it is an operator env/tool/network prerequisite the agent cannot satisfy here, document it as a runbook prereq or `MANUAL:` step (do **not** weaken or drop the check just to force green). Append only real fix findings to `docs/troubleshooting.md`, cited.

### 4. Validate the run

1. **Citations**: no non-obvious claim is unsourced or unresolved-`FLAG`. Grep for stray `FLAG:` markers — none may remain unaddressed.
2. **Links**: every internal `[text](path)` resolves.
3. **Orphans**: every `docs/*.md` is reachable from `README.md` or another doc within one hop.
4. **Inventory closed**: every doc is `updated`, `verified-current`, or `flagged` (with the flag surfaced to the user). None left `unknown`.
5. **Runbook**: each runbook section links a well-formed check-only `validate-<name>.sh` (run `--check` to confirm — on a writable tree it's committed; on a read-only tree it's emitted inline and run once). Agent-satisfiable local/static checks must pass; env/tool/network gaps that only an operator can close are documented as prereqs/`MANUAL:` rather than forced to exit 0. `docs/troubleshooting.md` reflects any real fix applied.
6. **Diagrams** (if any): Mermaid renders without error (`mmdc` if available).

Present a change summary. **Do not commit unless the user explicitly asks.**

## Expected output

- Root `README.md` and `docs/*.md` reconciled to the code, each non-obvious claim cited to `path:line`.
- `docs/DECISIONS.md` — append-only log of every ambiguity resolved with the user.
- For runbook sections: `scripts/validate-<name>.sh` (check-only) linked from the section, plus `docs/troubleshooting.md` updated with fixes found during validation.
- A change summary listing per-doc status and any open `FLAG`s.

## Acceptance criteria

A run passes when **all** hold:

- [ ] **No invented facts.** Every non-obvious claim in every touched doc is either cited to `path:line` or marked `FLAG` and raised with the user. Zero unresolved `FLAG` markers at close.
- [ ] **Inventory closed.** Every doc in scope ends `updated`, `verified-current`, or `flagged`; none left `unknown` or known-stale-and-untouched.
- [ ] **Decisions logged.** Every user-resolved ambiguity is appended to `docs/DECISIONS.md` with the resolution and (where applicable) source.
- [ ] **Runbook validated.** Each deploy/process/setup section has a check-only `validate-<name>.sh` that is linked, well-formed, and gates every destructive step (run `--check` to confirm). Acceptance is **not** "exit 0 at all costs": agent-satisfiable local/static checks must pass; genuine operator prerequisites (missing env vars, tools, remote health outside this environment) may leave `--check` non-zero when documented as prereqs or `MANUAL:` steps — never invent a green path by dropping real checks. On a read-only tree the script is emitted inline and its `--check` outcome reported instead of committed. `docs/troubleshooting.md` records any real fix applied.
- [ ] **Links + orphans.** Every internal link resolves; no `docs/*.md` is orphaned.
- [ ] **Branch discipline.** No commits on `main`/`master`; all changes on a feature branch. No commit without an explicit user request.

## Edge cases

- **No docs exist**: all-Generate run. Start from `README.md`, add `docs/` files the code justifies. Still cite everything.
- **Docs conflict with code**: code wins. Fix the doc to match, cite the code, and log the conflict in `DECISIONS.md`. Do not delete the user's prose without asking.
- **Ambiguity with no code answer**: ask the user; never guess. If unreachable, leave the claim as a `FLAG` and report it — do not fill the gap.
- **Monorepo**: limit per-component READMEs to packages with public APIs or user-facing behavior; skip build output and generated packages.
- **Secrets**: never document credentials, tokens, or internal-only endpoints beyond what code comments already expose.
- **Read-only repo**: emit docs and the validation script as a diff/inline summary instead of writing files; still run the script once to report its `--check` outcome (including documented prereq failures).

## Step Completion Reports

After each major step, emit:

```
◆ [Step Name] ([step N of M] — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          × fail — [reason]
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Use `√` pass, `×` fail, `—` for context. Per-phase checks:

- **Inventory + scope** — `Ground-truth read`, `Inventory built`, `Scope confirmed`
- **Per-doc pass** — `Claims cited`, `Conflicts flagged`, `Decisions logged`
- **Runbook add-on** — `Validate script check-only`, `Destructive steps gated`, `Troubleshooting updated`
- **Validate the run** — `No unresolved FLAGs`, `Links resolve`, `Inventory closed`, `Runbook script well-formed`

## Guidelines

- **Protect the context budget.** State the fact, cite it, move on. No filler, no restating the obvious, no marketing tone.
- Adapt structure to project type — not every `docs/` category applies.
- Prefer code-derived facts over stale prose; keep existing accurate docs untouched (`verified-current`).
- Maintain cross-references; remove content only when it's wrong or orphaned, and say so in the summary.
