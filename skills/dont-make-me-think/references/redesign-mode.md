# Redesign Mode

Step 5 of `SKILL.md` → *Instructions*, run only when the user asks for fixes to be applied. Steps 1-4 are read-only; this is the only step that writes to the user's files. `SKILL.md` (*Redesign Mode*, *Repo Sync Before Edits*) holds the binding rules; this file holds the full procedure, the sync steps, and the Redesign summary.

## Procedure

1. Produce the review first (`report-format.md`).
2. If the fixes go into code files, run the Repo Sync below. For screenshot or wireframe input, write no file and run no sync: give specs an AI agent or developer can implement without guessing, then print the Redesign summary with `Applied 0 fixes; specs only`.
3. **Dry-run first.** Show the planned diff for each fix: file path, selector, before and after. List 🔴 issues first, then 🟡. Leave 🟢 issues out unless the user names them.
4. Wait for explicit confirmation. The user may confirm all fixes or name a subset. If the user does not confirm, write nothing and print the `BLOCKED` Redesign summary. An orchestrator never confirms on the user's behalf.
5. Before each edit, record the file's current content.
6. Apply each confirmed fix. Change the minimum necessary: surgical, not a rewrite. Preserve the brand and aesthetic. On a CSS framework (Tailwind, Bootstrap), keep the framework classes and change only values.
7. If a write fails, restore that file's recorded content and name the fix as not written. Never roll back with `git checkout` or `git restore`: they would discard the user's other uncommitted edits.
8. If a file is not writable, write nothing to it, name the permission issue in the Redesign summary, and give the fix as a spec.
9. Show the before/after for each fix written, then print the Redesign summary.

## Repo Sync steps

Run these once, before the first edit. The sync target is the directory holding the files to edit.

1. Run `repo="$(git -C "<target dir>" rev-parse --show-toplevel)"`. If it fails, skip the sync and record `sync: skipped (not a git repo)`.
2. Run `git -C "$repo" remote get-url origin`. If it fails, skip steps 3-7 and record `sync: skipped (no origin)`.
3. Run `branch="$(git -C "$repo" rev-parse --abbrev-ref HEAD)"`. If it prints `HEAD`, skip steps 4-7 and record `sync: skipped (detached HEAD)`.
4. Run `git -C "$repo" status --porcelain`. If the output is empty, run `git -C "$repo" fetch origin && git -C "$repo" pull --rebase origin "$branch"`.
5. If the output is not empty, run `git -C "$repo" stash push -u -m "dont-make-me-think pre-sync"`, then the same fetch and pull, then `git -C "$repo" stash pop`.
6. If `fetch` or `pull` fails before a rebase starts (network, authentication, or a missing remote branch), do not retry. Run `git -C "$repo" stash pop` when step 5 stashed, record `sync: failed (<first error line>)`, and continue.
7. If the rebase conflicts, run `git -C "$repo" rebase --abort`, then `git -C "$repo" stash pop` when step 5 stashed. If the stash pop conflicts, leave the stash in place. In both cases write no file; stop and ask the user how to continue. With no answer, the Redesign summary status is `BLOCKED`.

This skill commits nothing.

## Redesign summary

Print this four-line block below the report at the end of Redesign Mode:

```text
Result: COMPLETE. Applied 2 of 2 confirmed fixes in src/pages/Pricing.tsx.
Evidence: 🔴 "Disabled buttons, no explanation" — Pricing.tsx:42, the disabled Download button now shows the reason "Select a plan first" beside it. 🟡 "No pricing shown" — Pricing.tsx:18, the price now renders next to the CTA. sync: pulled origin/main, no conflicts.
Uncertainty: The rendered page was not re-checked in a browser; the fixes were verified in the source only.
Decision: No approval needed. Run your test suite before you commit.
```

| Status | When |
|---|---|
| `COMPLETE` | Every confirmed fix was written, or specs were given for screenshot or wireframe input. |
| `PARTIAL` | At least one confirmed fix was written and at least one was not; name each one not written and why. |
| `BLOCKED` | No file was written: the user did not confirm the dry-run diff, no file was writable, or Repo Sync stopped on a conflict. |

- `Evidence:` names each fix written with its `file:line` and what changed, plus the `sync:` record.
- `Uncertainty:` says how the fixes were verified (source only, or re-rendered) and lists each assumption.
- `Decision:` names the one action the user must take, or says `No approval needed.`
