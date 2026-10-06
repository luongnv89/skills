# Scopes, Results and Report Format

Detail for the SKILL.md Inputs scope table, the Results definitions, the Step Completion Reports
and the final report.

## Scope details

Infer the scope from the request and confirm it once (`Scope: <name> (Steps …). OK?`). If the user
corrects it, use the correction and do not ask again.

| Scope | Runs | Skipped, reported `— skipped by user` |
|---|---|---|
| full | Prerequisites, 1–7 | none |
| review | Prerequisites, 1, 2, 3, 7 | 4, 5, 6 |
| ignore | Prerequisites, 1, 3, 4, 7 | 2, 5, 6 |
| sweep | Prerequisites, 1, 3, 5, 6, 7 | 2, 4 |
| report-only | Prerequisites, 1, Step 5 up to the table, Step 6 list | 2, 3, 4, Step 5 deletes, 7 |
| drill-down | Prerequisites, 1, Step 6 for the named branch | 2, 3, 4, 5, 7 |

- **Skipped-phase residue.** In a sweep run on a dirty tree, Step 7 still runs `git status
  --porcelain`. Report the entries as `Working tree: 3 entries — skipped by user`. They do not
  make the run PARTIAL. If the dirty tree blocks `git switch main`, SKILL.md Step 3 item 3
  applies.
- **report-only.** Read-only apart from `git fetch --prune`, which only refreshes remote-tracking
  refs. Never switch, pull, discard, commit, push, or delete, and never run a plan from
  `action-plans.md` D; offer only the read-only drill-down overview. Local rows are tested
  against local `main` as it is, unpulled: list that under `Unverified:`. Because nothing
  switches, the current branch may itself be merged: list it in the table as
  `current, not deletable` rather than leaving it out.
- **drill-down.** The named branch only. If it is protected (for example the current branch), say
  which rule applies and stop with `BLOCKED — <branch> is protected`. If it is merged, show its
  signal and offer the Step 5 delete for that one row.

## Results per scope

| Scope | PASS | PARTIAL | BLOCKED |
|---|---|---|---|
| full, review, ignore, sweep | on `main`, status clean (in-scope entries), no unprotected merged ref left (sweep and full) | residue inside the scope, each item with its reason | prerequisite, Step 3, or an error |
| report-only | table and unmerged list produced; no ref or file changed | none (a check that could not run, such as a failed `gh pr list`, goes under `Unverified:`) | prerequisite or fetch failure |
| drill-down | the chosen plan ran and its last check printed the expected result, or Keep | the plan stopped part-way (e.g. archive pushed, delete rejected as `stale info`) | prerequisite, protected branch, or an error |

PARTIAL triggers and their report wording:

| Trigger | Wording |
|---|---|
| change left as is | `PARTIAL — 2 changes left as is (user choice)` |
| named stash | `PARTIAL — stash "cleanup: notes" kept (user choice)` |
| declined discard or declined table row | `PARTIAL — feat/x declined in the table` |
| ignore rule in an open PR | `PARTIAL — ignore rule pending in PR #58` (deferred paths listed under it) |
| ignore commit declined | `PARTIAL — .gitignore change not committed (user choice)` |
| skipped or `stale info` delete | `PARTIAL — origin/feat/y skipped: remote tip moved since the table` |
| user declined everything | `PARTIAL — no change approved` |

Several triggers join with `; `: `PARTIAL — 1 change left as is (user choice); feat/x declined in
the table`. `main` ahead of `origin/main` with the push declined is still PASS; name the push
under `Next:`. A failed `gh pr list` (no auth, non-GitHub remote) is not PARTIAL by itself: signal
3 is unavailable for the run and goes under `Unverified:`, in every scope. A Step 7 leftover from
a phase outside the scope is `— skipped by user` and does not affect the result.

## Step completion block

```
◆ Cleanup (step 5 of 7 — merged-branch sweep)
··································································
  Candidates listed:  √ pass (4 local, 3 remote)
  User confirmation:  √ pass (one confirmation for the table)
  Deleted:            √ pass (7 refs, 0 failures)
  Protected skipped:  √ pass (main, release/2.1, worktree feat/wip)
  ____________________________
  Result:             PASS
```

Check names per step:

| Step | Checks |
|---|---|
| 1 | Fetched, Snapshot recorded, merged-PR check (gh), Detached commits |
| 2 | Entries listed, Decisions recorded, Plan confirmed, Discards run, Keep commit, Stash |
| 3 | Worktree check, Switched, Pulled, Ahead count |
| 4 | Patterns proposed, Kept paths tested, Diff applied, Commit, Push |
| 5 | Candidates listed, User confirmation, Deleted, Protected skipped |
| 6 | Unmerged listed, Drill-down |
| 7 | On main, Status clean, No merged local, No merged remote, Re-check |

A check with nothing to do reads `√ pass (none needed)`.

## Final report fields

```
◆ Cleanup Report
Result:      PASS | PARTIAL — <reason> | BLOCKED — <stop point>
Verified:    <each check that ran> → <observed output>
Unverified:  <each check that did not run, and why> | none
Next:        <remaining user action> | No approval needed
··································································
  Scope:              <scope>
  Branch:             <branch> (<N> ahead of origin/main)
  Changes reviewed:   <n> (<k> kept → <branch>, <d> discarded, <i> ignored/deferred, <l> left as is)
  Ignore file:        <+N patterns, where committed, pushed or not>
  Merged deleted:     <ref> (<signal>, <sha or PR #>); ...
  Skipped deletes:    <ref> (<signal>, <sha>; <reason>) | none
  Unmerged kept:      <branches>
  Protected skipped:  <branches>
```

- **Skipped deletes** lists every merged ref that was not deleted, with its signal, its sha and
  one reason: `declined in the table`, `stale info: remote tip moved since the table`, or the
  git error (permissions, branch protection, already gone).
- **Result** is the first line under the header. The reason names the residue or the stop point.
- **Verified** lists only checks that ran, with what they printed (Step 7 commands, the Step 3
  ahead count, the Step 7 re-check).
- **Unverified** lists checks that did not run: `merged-PR check unavailable — squash merges
  detected by patch equivalence only`, a skipped delete, a local-only run, local `main` not
  pulled (report-only), a re-check not run.
- **Next** comes only from approvals the skill already asks for: `push N commits to
  origin/main`, `merge ignore PR #N`, `remove worktree <path>`, `run /cleanup-project in
  <path>`, `abandon or branch N detached commits`. Otherwise `No approval needed`. Invent no new
  gates.
- Omit a field line whose phase was outside the scope, or mark it `— skipped by user`.
