# Stress-Testing the Harness

The verify skill is the smoke test for every change, so a step that passes on one run and fails on the next teaches agents to re-run instead of fix. Step 5 runs the harness three times and reports every step whose result changed.

## Running it

1. Run only commands the approved plan listed. A command that is not in it needs a new approval.
2. Follow the generated verify skill exactly as written, start to finish, three times: run 1, run 2, run 3. Do not edit it between runs. Do not reuse a running app: each run boots its own, and tears it down, even after a failure.
3. Fresh state per run where the verify skill creates any: a new `$RUN_DIR` folder (set in the verify skill's step 1), and the same seed data. Do not reset anything the verify skill does not reset; a step that depends on state left by the previous run is a finding, not something to hide.
4. Before each run, check that the app's port is free (`lsof -i :<port>` or `ss -ltn`); a port still held by a process this run started is a teardown failure, and one held by anything else stops the stress test with the conflict reported. Start the app in its own process group (`setsid`, or `set -m` in bash) and tear it down by stopping that whole group, so a child process (the `node` that `npm run` starts) cannot keep the port.
5. Readiness is one bounded poll of the ready signal (for example `curl -fsS` every second up to the stated timeout). That waits for a signal and is not a retry: a feature step itself runs once, and its first result is the result.
6. Record per step and per run: the status (`PASS`, `FAIL`, `UNVERIFIED`), the exit code where there is one, the observation compared with the expected result, and the seconds it took. Boot, ready and teardown are steps too.
7. Keep every run's log folder. They are the evidence for the report.

## Comparing the runs

| Pattern across runs 1-3 | Verdict | What to do |
|---|---|---|
| Same status and same observation | **Stable** | Nothing |
| Same status, observation differs only in values the map does not check (a timestamp, an ID) | **Stable** | Nothing; note the varying field if the map's expected result might depend on it |
| Status differs (for example `PASS, FAIL, PASS`) | **Flaky** | Report all three results; propose a fix |
| Same status, observation differs in a value the map checks | **Flaky** | Report all three observations; propose a fix |
| `FAIL` in all three | **Stable failure** | Report it as a bug or a wrong row; never edit the row to pass |
| `UNVERIFIED` in all three | **Not run** | Report the reason (missing variable, driver or answer) |

`dirty` is expected to be `yes` on every run until the user commits the new files. Compare runs on per-step results, not on `dirty`.

A step that takes more than twice as long in one run as in the others, and over 1 second in its slowest run, is flagged as **slow variance**, with its three durations.

## Proposing a fix

Name the likely cause from the logs, and propose the smallest change to the verify skill or feature map that removes it:

| Cause seen in the logs | Fix to propose |
|---|---|
| A step ran before the app was ready | A real ready signal (a health URL, a log line) instead of a fixed wait |
| Port already in use from the previous run | Teardown that waits for the process to exit; or a free port through the variable the app reads |
| State left by the previous run (a record already exists, a file is in the way) | The repo's own reset or seed command, or a unique value per run where the app allows it |
| An expected result depends on time, order or randomness | A check on the stable part (status, a field's presence) with the user's approval |
| Network calls to an external service | Mark the row `UNVERIFIED` offline, or use the repo's own mock or test mode if it has one |

Never propose a retry, a fixed sleep, a longer timeout on its own, or dropping the step: they hide the flake instead of removing it. Each fix is a plan item the user approves; after it is applied, run the harness three times again and compare.

## Speed

Report each run's total seconds and the three slowest steps. When one run takes over five minutes, say so and suggest what to move out (an exhaustive check the test suite already covers, a second boot, a build that the dev server does not need), as a proposal.

## Report table

```text
Stress test: 3 runs of .claude/skills/verify/SKILL.md at 3f2a9c1 (logs: .verify/runs/20261122T101500Z-4121, …T101544Z-4388, …T101630Z-4602)
Step          Run 1        Run 2        Run 3        Verdict
Boot          PASS 6.1s    PASS 5.8s    PASS 6.0s    stable
Ready         PASS 1.2s    PASS 1.1s    PASS 9.7s    stable, slow variance
F2 Sign-in    PASS         FAIL         PASS         flaky: run 2 saw an empty page (app.log: request before ready)
F7 Export     FAIL         FAIL         FAIL         stable failure: 500 on /export (all runs)
Totals        41s          39s          48s
```
