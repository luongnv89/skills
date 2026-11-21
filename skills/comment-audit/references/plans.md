# Gate plans

Every approval gate prints one plan for its action group alone, then asks one question and waits. Keep each plan short enough to read on one screen. With more than 30 items, print the summary and the first 30 items, put the full list in `plan-<gate>.md` in the audit folder, and give that path. An item that absorbs many comments shows its count and its first five IDs; the full list goes in the file.

## Shape

```text
Gate <0|A|B|C|D> — <action group> (<N> items)
Scope: <scope> · base <7-char SHA> · branch <branch>
Changes: <files created or changed, or issues filed>, nothing else
Commit: "<message>" with only <paths>, on <branch> (or: no commit)
Items:
  <ID>  <one line per item>
  ...
Not in this plan: <unsure entries, skipped kinds, pre-sync paths, linter-required doc comments, with counts>
Reply: approve all · approve <IDs> · skip · stop
```

A gate with no items prints `Gate <X> — <action group>: nothing to do (<reason>)` and moves on without asking.

## Per gate

**Gate 0, prepare.** Three items:
- `P1 sync`: the commands from *Repo Sync Before Edits*, whether a stash is needed (the user has uncommitted changes), and any local commits `pull --rebase` would rewrite (`git log origin/<branch>..HEAD`).
- `P2 branch`: its name.
- `P3 checks`: each check command, what it may write (build folders, caches, files outside the repo), and anything it installs or downloads on first run (a test runner it clones, a tool from a registry). Mark each check that cannot run here and why.

Replies: approve all, approve some (for example `approve P2 P3`, so no sync), skip (no sync, no branch, no checks), stop.

**Gate A, ADRs.** One item per ADR: `ADR-<number> <path> "<title>" ← 12 comments (C012, C044, …): <two-line summary>`. Decision Records already recorded in a repo doc get one item each: `R<n> already recorded at <path>:<line> ← C031`. Name the format (the repo's existing template, or the default in `references/adr-and-issues.md`) and say whether an index file changes. If the user skipped Gate 0's branch, the plan stops here and asks for one: nothing is committed on the default branch.

**Gate B, issues.** One item per hack: `I<n> "<title>" ← C031 (src/sync.py:88), labels: <existing labels or none>`. If the duplicate search found an issue, the item reads `link to #<number> (open|closed): <title>` instead of filing. Name the tracker and repository (`gh`, `owner/repo`), or say the issues become drafts in the audit folder because no tracker can be written to.

**Gate C, deletion.** Start with the counts:
- per kind, with how many of the Tautologies are descriptive doc comments;
- the comment lines removed, and the blank lines and inline edits apart;
- the verification line: the checks that will be re-run, or the `UNVERIFIED` block from `references/deletion.md`.

Then one item per comment, `C007 Tautology src/load.py:13 "# open the file and parse it"`, grouped by file. List every forced code change separately (`src/base.py:40 empty body → ...`). Leave out Excuse entries without an issue number and Decision Record entries without an ADR, and say why. If a linter requires doc comments, ask here whether to keep them or also change the lint config.

**Gate D, ratchet.** One item per file, with an ID: `D1 scripts/check_comments.py (new)`, `D2 comment-baseline.json (new, 214 lines in 31 files)`, `D3 package.json: "lint" script runs the check`. Then the mechanism and why it fits the stack, the command that runs the check, and the known gaps from `references/lint-ratchet.md`.

## Replies

| Reply | Do |
|---|---|
| approve all, yes, go ahead | Apply every item in this plan |
| approve C3, C7-C12 | Apply only those items; the rest stay and are listed as unapproved |
| skip | Change nothing in this group; go to the next gate |
| stop | Change nothing more; go to Step 8 |
| a question, or a change request | Answer it or revise the plan, then ask again; nothing is applied yet |

A reply that changes an item's kind (an unsure entry, or "C9 is a decision, not a tautology") updates the audit and the affected plans before anything is applied.
