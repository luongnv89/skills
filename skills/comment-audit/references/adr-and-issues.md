# ADRs and issues

## ADRs (Gate A)

**Find the folder and format.** Look, in this order, for:

1. an `.adr-dir` file at the repo root (adr-tools), which names the folder;
2. an existing folder of numbered decision files: `doc/adr/`, `docs/adr/`, `docs/adrs/`, `docs/decisions/`, `doc/architecture/decisions/`, `adr/`, or `architecture/decisions/`, holding files like `0001-*.md`.

If found, copy its template (the headings of its most recent ADR), its numbering (next free number, same zero padding) and its file naming. Update its index file (`README.md` or `index.md` listing the ADRs) if it has one.

If none exists, create `docs/adr/` and use Michael Nygard's format ("Documenting Architecture Decisions", 2011), numbered from `0001`:

```markdown
# <number>. <decision as a short phrase>

Date: <YYYY-MM-DD>

## Status

Accepted

## Context

<the forces and constraints, from the comment and the code around it>

## Decision

<what the code does and the rule it follows>

## Consequences

<what this makes easier or harder; what would change it>

## Source

Moved from code comments at <base SHA>: <path>:<lines> (<symbol>).
```

**Content rules:**

- One ADR per decision. Comments that record the same decision go into one ADR.
- Status is `Accepted`, because the code already follows the decision.
- Write the Context and Decision from the comment and the code it sits on. Do not add reasons the comment and code do not support. A missing reason is written as unknown.
- The Source section names every absorbed comment's path, line range at the base commit, and the function or class, so readers can find where the rule applies after the comment is gone.
- Keep the comment's references (ticket links, contract clauses, bug URLs) verbatim.

## Issues (Gate B)

**Tracker.** Use GitHub through `gh` when `gh auth status` succeeds and `origin` is a GitHub repository. Any other case (no `gh`, no remote, another tracker, no write access) is the no-tracker path below.

**Duplicate search, before the plan.** For each hack, run `gh issue list --state all --search "<file name> <key words of the hack>" --limit 10`. An open issue that describes the same hack is linked, not re-filed. A closed one is linked and noted, because the hack may have come back.

**One issue per hack.** Excuse comments about the same shortcut, even in several files, become one issue.

**Issue body:**

```markdown
## What the code does now

<the hack, from reading the code: what it does and why it is a shortcut>

## Where

- `<path>:<line>` at <base SHA> (<permalink when the repo is on GitHub>)

## The comment that was removed

> <the comment text, verbatim>

## What a fix needs

<the proper behaviour, when the code and comment make it clear; otherwise "Needs investigation">

Found by a comment audit of <scope>.
```

**Title:** an imperative phrase naming the hack and where it is, such as "Stop clamping negative stock to zero in needs_reorder".

**Labels:** only labels that already exist in the repository (`gh label list`), such as `tech-debt` or `bug`. Never create a label. With no fitting label, file it without one.

**No-tracker path.** Write each issue as `issue-<n>.md` in the audit folder, list them in the report, and keep those Excuse comments in the code. They become deletable on a later run, or later in this run once the user gives the issue numbers.
