# Subagent evaluation rubric

The pass/fail checklist for the **Evaluate** branch and the self-check at the end of **Create**. This is a *design audit* — no test runs, no benchmarks. Grade each item `√ pass` / `× fail` / `~ partial` with a one-line reason, then give an overall `PASS | FAIL | PARTIAL`.

Read the target file once (frontmatter + body), state its claimed responsibility in your own words, then walk all six categories.

## 1. Frontmatter validity

- [ ] `name` and `description` both present (the two required fields).
- [ ] `name` is lowercase letters/digits/hyphens, no consecutive hyphens, and **matches the filename stem** (`code-reviewer` ⇒ `code-reviewer.md`).
- [ ] YAML parses — string values containing `:` `#` `-` `,` `<` `>` `|` `[` `]` `{` `}` `*` `&` `?` `!` are quoted. (`description` almost always needs quotes.)
- [ ] No unknown/misspelled fields. Advanced fields (`isolation`, `context`, `memory`, `hooks`, `permissionMode`, …) are present only with a clear reason.
- [ ] If plugin-bundled: no `hooks`, `mcpServers`, or `permissionMode` (forbidden for plugin agents).

## 2. Single responsibility

- [ ] The agent's job fits in one sentence with no "and" joining unrelated work.
- [ ] It doesn't duplicate an existing sibling agent's purpose.
- [ ] If it does two jobs, flag it for a split.

## 3. Tools — least privilege

- [ ] `tools` lists only what the job needs (or is deliberately omitted for a genuine general-purpose agent — flag omission if the agent is narrow).
- [ ] Read-only agents (review/audit/analysis) have **no** `Edit`/`Write`.
- [ ] `Bash` is scoped to patterns where feasible (`Bash(npm:*)`) rather than unrestricted.
- [ ] Tools in frontmatter agree with what the body claims to do (no "read-only" body holding `Write`).

## 4. Description quality (the trigger)

- [ ] States **when** to invoke (the situation/trigger).
- [ ] States **what** the agent does.
- [ ] Has `Use PROACTIVELY` / `MUST BE USED` **iff** the agent should auto-delegate (present when it should, absent when it should only run on request).
- [ ] Names what it's **not** for when a sibling agent could grab the same task.
- [ ] Single line, no newlines.

## 5. System-prompt body structure

- [ ] Opens with a one-line **role** statement (`You are an expert … specializing in …`).
- [ ] Has an ordered **When invoked** action list.
- [ ] Has a **Process** section with concrete sub-steps (real commands/files, not vague advice).
- [ ] Has a fixed **Output Format** so the main agent can consume results.
- [ ] Has verifiable **completion criteria** (a checklist or equivalent).
- [ ] Is example-rich and concrete — names commands, files, labels.

## 6. Anti-patterns (each present = a `× fail`)

- [ ] **Multi-concern agent** — bundles unrelated jobs.
- [ ] **Over-provisioned tools** — broad/unrestricted access a narrow job doesn't need; `bypassPermissions` without strong justification.
- [ ] **Vague trigger** — description that won't reliably fire or that overlaps a sibling.
- [ ] **No output contract** — output shape left unspecified.
- [ ] **No-op prose** — lines like "be thorough", "use good judgment", "think carefully" that change nothing the agent does. Each should be a concrete step or deleted.
- [ ] **Read-write mismatch** — body and `tools` disagree on whether the agent mutates anything.
- [ ] **Stale version pinning** — hardcoded version numbers / dated "Last Updated" lines that will rot. (Minor; note, don't fail the whole agent.)

## Reporting

**Evaluate branch:** present findings as before/after suggestions. Do **not** silently edit — let the user decide or switch to Improve. Emit a Step Completion Report with one check per category:

```
◆ Evaluate subagent (<name>.md)
··································································
  Frontmatter valid:     √ pass
  Single responsibility: × fail — reviews code AND writes tests
  Tools least-privilege: ~ partial — has Write but is a reviewer
  Description quality:   √ pass
  Body structure:        √ pass (missing Output Format)
  Anti-patterns:         × fail — multi-concern + read-write mismatch
  ____________________________
  Result:                FAIL — split into two agents
```

**Create self-check / Improve re-check:** the same checklist, used to confirm a draft is clean (Create) or that prior `× fail`s are now `√ pass` (Improve).
