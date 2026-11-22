# Plan, Step Reports and Final Report

## Plan

Step 3 prints one plan per run and waits for the user's reply. It is a dry run: nothing has been written, installed or started.

```text
◆ verify-setup plan for <repo> at <base SHA>
App: web app (Next.js) · root: . · verify skill: verify
Sync (after approval):
  S1 stash the dirty tree, git pull --rebase origin main, pop the stash
Write:
  W1 .claude/skills/verify/SKILL.md (new)
  W2 .claude/skills/verify/feature-map.md (new, 9 features)
  W3 .agents/skills/verify/SKILL.md and feature-map.md (identical copies)
  W4 .verify/.gitignore (holds *)
Run (3 times in Step 5):
  R1 npm run build               package.json:8         writes .next/
  R2 npm run dev                 package.json:7         port 3000
  R3 curl -fsS localhost:3000/api/health  src/app/api/health/route.ts:3
  Harness (covered by this approval): mkdir, setsid or set -m, curl, kill, lsof/ss, git rev-parse/git status
Mutating rows (run against the test database from compose.test.yaml:3):
  F6 POST /api/todos creates a todo
Install (each default No):
  I1 npm ci into node_modules/ (cache in .verify/cache) — needed for R2
  I2 npx playwright install chromium — no browser tool found; without it F3, F5 stay UNVERIFIED
Pointer:
  P1 AGENTS.md +1 line: "- Before committing, follow `.agents/skills/verify/SKILL.md`"
Ask: F8 "Export CSV" has no expected result in the repo. What should it produce?
Reply: approve all · approve <IDs> · change … · stop
```

An update to an existing verify skill shows the diff for each changed file instead of `(new)`.

## Step reports

After each step, print a compact block: one `√` or `×` line per check, then `Result: PASS | FAIL | PARTIAL`.

```text
◆ Detect (step 1 of steps 0–7)
··································································
  App classified:        √ web app (next in package.json:14)
  Boot command sourced:  √ npm run dev (package.json:7)
  Ready signal sourced:  √ GET /api/health (src/app/api/health/route.ts:3)
  Drivers listed:        × no browser tool; curl only
  ____________________________
  Result:        PARTIAL
```

| Step | Checks |
|---|---|
| 0 Prepare | `Git repository`, `Pre-sync list saved`, `Base recorded`, `Existing verify skill checked` |
| 1 Detect | `App classified`, `Install, build, boot sourced` (or `unknown` listed), `Ready signal sourced`, `Drivers listed` |
| 2 Map | `Boot and main path first`, `Every row has a source`, `Expected results observable`, `Rows needing input listed` |
| 3 Plan | `Plan shown`, `Approval received` (or no user, with the reason), `Installs separate and default No` |
| 4 Write | `Sync done or skipped with reason`, `Only approved files written`, `Copies identical`, `No <…> placeholder left`, `Nothing outside the repo` |
| 5 Stress test | `3 runs completed`, `Per-step comparison done`, `Flaky steps reported`, `Teardown after every run` |
| 6 Pointer | `AGENTS.md exists`, `Approved`, `At most one line added` (or skipped, with the reason) |
| 7 Report | `Files and statuses listed`, `Final Report printed` |

A skipped optional step reports `— skipped` with the reason and `Result: PASS`.

## Final Report

The four-line block that ends every run, stops included. It follows the Step 7 summary and never replaces it.

### Status

| Status | When |
|---|---|
| `COMPLETE` | The approved files were written and the three runs agree on every step. A step that fails in all three runs is still reported. `COMPLETE (no app)` when the repo has nothing to boot or run |
| `PARTIAL` | No user was present to approve, so nothing was written; the user approved only part; a step was flaky; or rows stayed `UNVERIFIED` |
| `BLOCKED` | Nothing was written: not a git repository, the sync stopped, or the request is out of scope |

### Fill rules

- `Result:` the status, the verify skill's path, the app type, the feature count, and the statuses across the runs.
- `Evidence:` the sourced boot and ready commands, each run's duration, the log folder, and the sync line. Cite only commands that ran.
- `Uncertainty:` `UNVERIFIED` rows and why, flaky steps with their three results, stable failures, assumptions the user approved (a ready timeout, a missing lockfile), and paths outside the repo the app writes to.
- `Decision:` what waits on the user (expected results to give, variables to set, fixes to approve, installs declined), or "No approval needed". Then the remaining action, such as reviewing and committing the new files.

### PARTIAL example (no user present)

```text
Result: PARTIAL. Detected a CLI (pyproject.toml:7-8, [project.scripts]) and drafted .claude/skills/verify/ with 5 features; nothing was written or run because no user is present to approve the plan.
Evidence: commands sourced: python3 -m wordcount count tests/fixtures/sample.txt (README.md:10), python3 -m wordcount --version (wordcount/cli.py:13); install: none needed (no dependencies declared); draft and plan printed above.
Uncertainty: the stress test has not run; F5 (unknown command) expects argparse's exit 2 and "invalid choice" (wordcount/cli.py:14), framework behaviour rather than a repo test.
Decision: Approve the plan (W1-W4, R1-R2) to write the files and run the stress test.
```

### BLOCKED example

```text
Result: BLOCKED. Nothing was written: /work/site is not a git repository.
Evidence: `git rev-parse --show-toplevel` failed with "not a git repository".
Uncertainty: None beyond the checks listed.
Decision: Run verify-setup inside a git repository.
```

### Reader checks

Before printing the block, confirm:

1. **Result findable:** the first line states the status and what was written.
2. **Facts and assumptions separated:** each verified item names its command or file; each assumption is labeled.
3. **Claims traceable:** each count cites the feature map or a run log.
4. **Next decision clear:** `Decision:` names what waits on the user, or says nothing does.
