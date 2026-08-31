# Input Resolution

How `/plan-to-issues` decides what it is converting. Read in Phase 0 (input check) and Phase 1.

The skill accepts **two input kinds**. Both produce the same worklist schema
(`references/plan-parsing.md`) and the same output: one epic plus one issue per task.

| Kind | `source.kind` | `source.value` | Where the worklist comes from |
|---|---|---|---|
| Plan file | `file` | repo-root-relative path, normalized | parsed from the file |
| Conversational intent | `conversation` | a confirmed slug (see below) | drafted from the conversation, then **confirmed by the user** |

No filename is special. `MODERNIZATION_PLAN.md` is one accepted plan file among many; so is a
`/tasks-generator` `tasks.md`, a hand-written `ROADMAP.md`, or a plan at an arbitrary path.

## Resolution order (Phase 0)

Apply in order; the first that resolves wins.

1. **Explicit path argument** — `/plan-to-issues <path>`. Wins over everything, including a
   conversation. A path that does not exist is a **stop**, never a silent fall-through to the
   conversation.
2. **Explicit conversation flag** — `/plan-to-issues --from-conversation`. Wins over discovery.
3. **Both present, neither forced** — a plan file is discoverable *and* the conversation carries
   actionable intent: **ask once**, never guess.

   ```text
   Two possible inputs:
     1. Plan file      docs/ROADMAP.md (4 phases, 18 tasks)
     2. This conversation  (~6 tasks drafted from the discussion above)
   Which should I convert? [1/2]
   ```
4. **Plan discovery** — the candidate sweep below.
5. **Conversation fallback** — no plan file resolves, but the conversation carries actionable
   intent: use it (announce the choice, do not ask).
6. **Neither** — stop with the *no input* failure block in `references/preflight.md`.

### Plan discovery candidates

First hit wins: `MODERNIZATION_PLAN.md` at repo root → `docs/MODERNIZATION_PLAN.md` → a single
`*PLAN*.md` at root → `tasks.md` → a `tasks/` directory. Two or more candidates → list them and ask
which. Never guess between candidates.

**Discovery always resolves to one file** — including when the hit is a directory: `tasks/` means
`tasks/tasks.md` when it exists, otherwise the single `*.md` inside it, otherwise list them and ask
which. Phase 3 binds the epic to that path, so a directory is never the bound value, and the choice
is made in Phase 0 — before Phase 2 creates a label — not after the first mutation.

A file with no task heading at either supported depth is **not a plan** — stop. Do not fall back to
the conversation: an unparseable file is an error to report, not a reason to invent work.

## What counts as actionable conversational intent

All three must hold, or the conversation is **not** an input:

- The user has described work to be done in *this* repo — not asked a question, not requested an
  explanation, not discussed a plan they intend to write later.
- At least **two** distinct units of work are identifiable, or one unit the user explicitly asks to
  file. A single vague sentence is not a backlog.
- The intent is in the user's own turns. Text the agent proposed and the user never endorsed is not
  intent; neither is a file quoted into the conversation (that is a plan file — ask for its path).

Ambiguous → ask rather than draft. Filing issues is a mutation.

## Phase 1 on the conversation path — draft, then confirm (gate)

The file path is **plan-faithful**: fields are copied, never improved. The conversation path cannot
be, because a discussion is not a structured plan. It gets an explicit **confirmation gate** in
place of faithfulness, and the same worklist schema out.

1. **Draft the worklist** from the user's turns only. Assign task ids in the plan grammar
   (`<phase>.<n>`, e.g. `1.1`). With no phases discussed, emit a single phase `P1` with the goal
   set to the user's stated objective.
2. **Copy, do not enrich.** Same contract as the file path: never open source files, never predict
   affected files, never add analysis the conversation did not contain. Acceptance criteria are
   drawn from what the user said "done" means; where they said nothing, emit one criterion
   restating the task and mark it `(needs review)`.
3. **Print the draft and ask once.** Task id, title, phase, effort, and dependencies per row, plus
   the epic title:

   ```text
   Drafted 6 tasks from this conversation, under epic "Harden the ingest path":
     1.1  Add retry/backoff to the S3 client            effort M   deps: none
     1.2  Surface partial-batch failures in the CLI     effort S   deps: 1.1
     ...
   File these? [Y]es / [e]dit / [n]o
   ```
   `edit` re-drafts from the user's corrections and asks again. `no` stops — nothing is created.
   **This gate is mandatory and has no auto-accept**: the file path has a reviewable artifact, the
   conversation path has only this.
4. **Record the confirmed draft** in the run report and, verbatim, in the epic body under a
   `## Source` heading. That block is the conversation path's substitute for a plan file — the only
   durable record of what was converted.

**Completion criteria (conversation path):** every drafted task has an id, a title, ≥ 1 acceptance
criterion, a `Dependencies` value (`None` allowed), and an effort; the user confirmed the draft
verbatim; the confirmed draft is recorded in the epic body. No confirmation, no filing.

## Epic identity and re-run on the conversation path

Phase 3 binds an epic with a marker naming its source
(`references/epic-identity.md`). Both kinds use one marker shape:

```text
<!-- plan-to-issues:plan=docs/ROADMAP.md -->
<!-- plan-to-issues:conversation=harden-the-ingest-path -->
```

The `conversation` value is a **slug of the epic title the user confirmed in step 3**: lowercased,
non-alphanumerics collapsed to `-`, trimmed, truncated to 60 characters.

**A conversation slug is not a stable identity, and this skill does not pretend it is.** Two runs
from two different discussions of the same subject can slug identically, and the same intent
rephrased slugs differently. So on the conversation path, idempotent re-run is
**operator-supplied, not automatic**:

- Phase 3 searches for an epic carrying this exact `plan-to-issues:conversation=<slug>` marker. **A hit is never
  silently reused** — print the epic and ask: reuse it (idempotent re-run, file only what it does
  not list), or create a new epic. Default is reuse.
- The final report always prints the epic number with the re-run invocation:
  `Re-run this backlog with: /plan-to-issues --from-conversation --epic <n>`. That number is the
  stable handle; the slug is only a hint that finds it. `sync <epic#>` only re-renders the map.
- `/plan-to-issues --from-conversation --epic <n>` binds directly to a known epic and **skips the
  search entirely**. This is the supported way to resume a conversation-sourced run.

The `file` path keeps its existing exact-match reuse: a normalized path *is* stable, so a hit there
is reused without asking (`references/epic-identity.md` step 1).

**Never materialize a plan file to obtain an identity.** This skill writes to the tracker only; its
acceptance criteria require `git status --porcelain` to match the pre-run snapshot.

## Mode interactions

- `--dry-run` — works on both kinds. On the conversation path it prints the draft and the
  plan-to-issue table and stops **before** the confirmation gate, creating nothing.
- `--phase P0,P1` — works on both. On the conversation path, phases exist only if the conversation
  discussed them.
- `sync <epic#>` — source-agnostic. It re-renders the map of an existing epic and never resolves an
  input; a conversation-sourced epic syncs exactly like a file-sourced one, except the unmapped-task
  comparison is against the `## Source` block instead of a plan file.
