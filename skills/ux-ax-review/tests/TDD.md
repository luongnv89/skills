# Validator vertical TDD record

Command run from the repository root for each RED and GREEN:

```sh
python3 -B -m unittest discover -s skills/ux-ax-review/tests -v
```

Each slice added one test method, ran the command and observed assertion failures
(exit 1), then implemented only that behavior and reran the whole suite.
No pytest or network access was used.

| Slice | RED | GREEN suite |
|---|---|---|
| Valid empty evidence report | exit 1, validator missing | exit 0, 1 test |
| Root object and exact integer schema version | exit 1 | exit 0, 2 tests |
| Top-level arrays and object rows | exit 1 | exit 0, 3 tests |
| Required scope fields and types | exit 1 | exit 0, 4 tests |
| Required record fields and types | exit 1 | exit 0, 5 tests |
| Enums and bounded integer phases | exit 1 | exit 0, 6 tests |
| Exactly one of each canonical aspect | exit 1 | exit 0, 7 tests |
| Duplicate and malformed record IDs | exit 1 | exit 0, 8 tests |
| Evidence/finding/task references | exit 1 | exit 0, 9 tests |
| Observed findings require evidence | exit 1 | exit 0, 10 tests |
| Conclusive coverage requires evidence | exit 1 | exit 0, 11 tests |
| Linked finding aspects match coverage | exit 1 | exit 0, 12 tests |
| Issues requires a linked observed finding for same aspect | exit 1 | New test passed; full suite found 2 older hypothesis fixtures incorrectly retaining issues status |

The parent resumed the corrected 13-test suite and verified exit 0. It then used
one additional failing-test-first slice at a time, with whole-suite GREEN after each:

| Slice | RED | GREEN suite |
|---|---|---|
| Related aspects support deduplicated cross-audience findings | exit 1 | exit 0, 14 tests |
| Every observed/hypothesis finding must have a plan task | exit 1 | exit 0, 15 tests |
| Tasks require at least one acceptance check | exit 1 | exit 0, 16 tests |
| Dependencies ordered, no self/cyclic/forward links | exit 1 | exit 0, 17 tests |
| All seven Markdown H2 headings outside fences | exit 1 | exit 0, 18 tests |
| CLI valid PASS and structural field errors | exit 1 | exit 0, 19 tests |
| CLI parse/read/nonfinite/Markdown errors without traceback | exit 1 | exit 0, 20 tests |
| Programmatic nested nonfinite values rejected | exit 1 | exit 0, 21 tests |

The original 21-test suite passed; validator CLI behavior is exercised by real subprocesses.
These tests establish structural validation only, never evidence truth or site compliance.

## Markdown fence reviewer fix

Baseline: the same command above passed all 21 tests (exit 0). Each regression
below was added and executed before its corresponding production change; every
RED failure was an assertion failure, not an import or execution error.

| Slice | RED whole suite | GREEN whole suite |
|---|---|---|
| Closing fence matches opening character and minimum run length | exit 1, 22 tests, 2 failing subtests: shorter backtick/tilde runs falsely exposed all seven headings | exit 0, 22 tests |
| Closing fence has no trailing non-whitespace text | exit 1, 23 tests, 6 failing subtests: backtick/tilde fences with attached, space-separated or tab-separated text falsely exposed headings | exit 0, 23 tests |
| Fence indentation limited to 0–3 spaces, not indented code | exit 1, 24 tests, 6 failing subtests: four-space/tab-indented code incorrectly opened fences | exit 0, 24 tests |

Both exact reviewer reproducers now return all seven missing-H2 errors.
Regression coverage also includes mismatched fence characters, equal/longer valid
closing runs, trailing spaces/tabs, opening and closing indentation from 0 to 3
spaces, four-space/tab-indented non-fences, and four-space-indented non-headings.
Headings inside an active fence never satisfy the report heading requirement.
The optional ATX heading syntax suggestion was not included in this narrow fix;
all other validator checks and the existing canonical heading contract are unchanged.

Final executed result: `Ran 24 tests in 1.597s`, `OK` (exit 0).
`git diff --check` also passed. No refactor, staging, commit or publication was performed.
