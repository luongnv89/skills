# Deleting comments (Gate C)

How Step 6 deletes approved comments, checks the result, and handles a project whose checks cannot run.

## Mechanics

- **Own lines:** delete every line of the comment unit.
- **Inline comment:** remove the comment and the whitespace before it, and keep the code on that line.
- **Mid-line block comment** (`a /* x */ + b`, `a/**/b`): remove the comment. Where removing it would join two tokens (`a/**/b` → `ab`), leave one space, and list the line as a forced change.
- **Blank lines:** when the deleted lines had a blank line above and below, also delete the blank lines below, so the gap matches what was there before the comment.
- **Line endings:** keep each file's line endings (CRLF stays CRLF) and its final newline exactly as they were. Edit in binary-safe mode or check `git diff --stat` shows no whole-file rewrite.
- **Emptied blocks:** a Python body left empty by a deleted docstring gets `...`. A block another language requires to be non-empty keeps the comment as machine-read instead. Find these before the plan: apply the planned deletion to a copy in the audit folder and parse every changed file (`python3 -m py_compile`, `bash -n`, `node --check`, `gofmt -l`). For Bats files, which `bash -n` cannot parse, first rewrite each `@test "…" {` line to `f() {`. A file that newly fails to parse names the comment that must stay.
- **Never touched:** machine-read entries, unsure entries, unapproved entries, and every path on the pre-sync list.

## Deletion check

Run it on `git diff -U0 <base> -- <changed source files>`, leaving out the pre-sync paths, the ADR files and the ratchet files:

1. Every removed line is an approved comment's own line or one of the blank lines above.
2. Every added line is a code line with its inline or mid-line comment removed, or a forced change the plan listed.
3. Nothing else differs. For a file that fails, put that file back to the base (`git checkout <base> -- <file>`), which is safe because pre-sync paths are never in this list and this run's only edits to the file are deletions. Then redo its approved deletions, and re-check it. If it fails again, leave the file at the base and list its comments as not deleted.

## Re-running the checks

Re-run each baseline check with the exact command from Gate 0. Each one that passed must pass again, and the number of tests passed must not drop. A drop or a new failure means a deleted comment was read by something: a doctest, a docstring a framework reads, a directive the inventory missed. Find it by restoring the file's comments one entry at a time (or by halves), move the culprit to machine-read, keep its comment, and re-run.

## Unverified

When no build or test check can run on this machine (the toolchain is missing, the project builds only on another OS, the checks need services that are down), say so in the Gate C plan, before approval. When only some checks run (a syntax check but not the tests), the plan names those that ran and those that could not, and the deletion counts as unverified for what only the missing checks cover:

```text
UNVERIFIED: no build or test check can run here (<reason>). Deleting these comments cannot be checked on this machine.
Run on a machine that can: <the project's check commands>
```

The user may still approve. After the deletion, the report is `PARTIAL`, and `Decision:` asks the user to run those commands and report the result before the branch is merged. Never treat a check that could not run as a check that passed.

## Commits

Commit only the paths this gate changed, by name: `git commit -m "<message>" -- <path> <path> …`. The `--` form commits those paths alone, so anything the user had staged stays staged and out of the commit. A new file must be added first (`git add -- <new path>`), because `git commit -- <path>` refuses an untracked path. Before committing, confirm that each named path is in the plan and that none is on the pre-sync list. Never commit on the default branch.
