# Gate plans

Every approval gate prints one plan for its action group alone, then asks one question and waits. Keep each plan short enough to read on one screen. When it has more than 30 items, print the summary and the first 30 items, and put the full list in `plan-<gate>.md` in the audit folder. Give that path in the plan.

## Shape

```text
Gate <A|B|C|D> — <action group> (<N> items)
Scope: <scope> · base <7-char SHA> · branch <branch>
Changes: <files created or changed, or issues filed>, nothing else
Items:
  <ID>  <one line per item>
  ...
Not in this plan: <unsure entries, skipped kinds, pre-sync paths, with counts>
Reply: approve all · approve <IDs> · skip · stop
```

## Per gate

**Gate A, ADRs.** One item per ADR: `ADR-<number> <path> "<title>" ← C012, C044: <two-line summary>`. Name the format (the repo's existing template, or the default in `references/adr-and-issues.md`) and say whether an index file changes.

**Gate B, issues.** One item per hack: `I<n> "<title>" ← C031 (src/sync.py:88), labels: <existing labels or none>`. If the duplicate search found an issue, the item reads `link to #<number> (open|closed): <title>` instead of filing. Name the tracker and repository (`gh`, `owner/repo`).

**Gate C, deletion.** Start with the counts: per kind, and the own lines removed. Then one item per comment, `C007 Tautology src/load.py:13 "# open the file and parse it"`, grouped by file. Then list every forced code change separately (`src/base.py:40 empty body → ...`). Leave out Excuse entries without an issue number and Decision Record entries without an ADR, and say why.

**Gate D, ratchet.** The mechanism and why it fits the stack, every file added or changed with the change in one line, the command that runs the check and where it is wired, the baseline total (comment lines in how many files), and the known gaps from `references/lint-ratchet.md`.

## Replies

| Reply | Do |
|---|---|
| approve all, yes, go ahead | Apply every item in this plan |
| approve C3, C7-C12 | Apply only those items; the rest stay and are listed as unapproved |
| skip | Change nothing in this group; go to the next gate |
| stop | Change nothing more; go to Step 8 |
| a question, or a change request | Answer it or revise the plan, then ask again; nothing is applied yet |

A reply that changes an item's kind (an unsure entry, or "C9 is a decision, not a tautology") updates the audit and the affected plans before anything is applied.
