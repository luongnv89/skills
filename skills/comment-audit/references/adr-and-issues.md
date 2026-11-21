# ADRs and issues

## ADRs (Gate A)

**Find the folder and format.** Look, in this order, for:

1. an `.adr-dir` file at the repo root (adr-tools), which names the folder;
2. an existing folder of numbered decision files: `doc/adr/` (adr-tools' default), `docs/adr/`, `docs/adrs/`, `docs/decisions/`, `doc/architecture/decisions/`, `adr/`, or `architecture/decisions/`, holding files like `0001-*.md`.

If found, copy its template (the headings of its most recent ADR), its numbering (next free number, same zero padding) and its file naming. Update its index file (`README.md` or `index.md` listing the ADRs) if it has one.

**Decisions already written down.** Before planning, check whether the repo already records a decision elsewhere: a design doc, `CONTRIBUTING.md`, `docs/`, or a doc the comment itself points to. A Decision Record whose reason is already there with the same rule gets no new ADR entry. The Gate A plan lists it as `already recorded at <path>:<line>`, and the comment becomes deletable like one with an ADR. When the doc says less than the comment, the ADR entry holds the difference and cites the doc.

If none exists, create `docs/adr/` and use Michael Nygard's format ("Documenting Architecture Decisions", 2011), numbered from `0001`:

```markdown
# <number>. <decision or subsystem, as a short phrase>

Date: <YYYY-MM-DD>

## Status

Accepted

## Context

<the forces and constraints, from the comments and the code around them>

## Decision

<what the code does and the rule it follows; for a subsystem ADR, one numbered entry per decision>

## Consequences

<what this makes easier or harder; what would change it>

## Source

Moved from code comments at <base SHA>: <path>:<lines> (<symbol>), one line per comment.
```

**Grouping.** A decision that stands alone gets its own ADR. Decisions that belong to one subsystem (a module, a service, a feature area) go into one ADR for that subsystem, each as its own numbered entry under Decision, with its own reason. Never make one ADR per comment when many comments share a subsystem, and never put unrelated subsystems in one ADR.

- **Repeated comments are one decision.** The same comment, word for word or nearly, in many files becomes one entry, and its Source line lists every copy.
- **Size.** Keep an ADR to about 30 decision entries. Split a larger subsystem by topic. Reasons for test fixture values go into ADRs per test area (one per feature under test), not one ADR for the whole suite.

**Content rules:**

- Status is `Accepted`, because the code already follows the decision.
- Write the Context and Decision from the comment and the code it sits on. Do not add reasons the comment and code do not support. A missing reason is written as unknown.
- The Source section names every absorbed comment's path, line range at the base commit, and the function or class, so readers can find where the rule applies after the comment is gone.
- Keep the comment's references (ticket links, contract clauses, bug URLs) verbatim. Never copy a secret: write `[redacted]`.

## Issues (Gate B)

**Tracker.** Use GitHub through `gh` when `gh auth status` succeeds and `origin` is a GitHub repository. Any other case (no `gh`, no remote, another tracker, no write access) is the no-tracker path below.

**Duplicate search, before the plan.** GitHub's search requires every word to match, so search twice for each hack and merge the results: once by its key phrase alone (`gh issue list --state all --search '"per-test timeout"' --limit 10`) and once by the file name alone. Read each result. An open issue that describes the same hack is linked, not re-filed. A closed one is linked and noted, because the hack may have come back or the fix may have missed it.

**One issue per hack.** Excuse comments about the same shortcut, even in several files, become one issue.

**Issue body:**

```markdown
## What the code does now

<the hack, from reading the code: what it does and why it is a shortcut>

## Where

- `<path>:<line>` at <base SHA> (<permalink when the repo is on GitHub>)

## The comment

> <the comment text, verbatim, with any secret replaced by [redacted]>

It is deleted from the code once this issue exists.

## What a fix needs

<the proper behaviour, when the code and comment make it clear; otherwise "Needs investigation">

Found by a comment audit of <scope>.
```

**Title:** an imperative phrase naming the hack and where it is, such as "Stop clamping negative stock to zero in needs_reorder".

**Labels:** only labels that already exist in the repository (`gh label list`), such as `tech-debt` or `bug`. Never create a label. With no fitting label, file it without one.

**No-tracker path.** The Gate B plan says the issues become drafts. After approval, write each as `issue-<n>.md` in the audit folder, list them in the report, and keep those Excuse comments in the code. When the user files them and gives the numbers, record the numbers and offer those comments in a new Gate C plan.
