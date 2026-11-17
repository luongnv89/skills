# CI minutes optimization

Mode for an existing GitHub Actions pipeline. Enter it only when the user asks about Actions minutes or cost, or explicitly asks for measured changes on a branch or pull request; "CI is slow, make it faster" gets the read-only [CI speed audit](github-actions.md#ci-speed-audit) and Step 3 instead. It runs in four phases: **measure**, **find**, **apply and prove**, **open a pull request**. The first two are read-only. The last two are the only part of this skill that commits and pushes: after one explicit approval, only to a new branch in a separate worktree, only for findings the user approved, and it never merges.

Several rules below come from a practitioner write-up that took a content site's CI from a peak of 60m51s to 2m55s without a runner upgrade ("How we cut CI from an hour to under 3 minutes", @0xZoZoZo, 2026-11-16). They are labelled *(practitioner)*: one team's measured experience, not GitHub rules.

**Leading words.**

- *Billed minutes*: each job's duration rounded up to a whole minute, summed per run attempt.
- *Goal*: billed minutes per commit on a private or internal repository; wall time per run attempt (first job created to last job done) on a public one, where standard runners are free. A removed job bills 0 minutes; it shortens the wall time only when it was on the critical path. Work moved to merges or a nightly schedule adds its own cost back into the monthly figure.
- *Baseline*: the last kept state on the branch: the baseline commit's samples at first, then the samples of the latest kept change.
- *Sample*: a row marked `yes` in the `sample` column of `ci-minutes.sh <visibility> <sha>`: an attempt of the commit's `pull_request` run (else its `push` run). `per_commit` is its billed minutes times the commit's `push` and `pull_request` runs of the workflow. On the dispatch path (Phase 3, step 4) the dispatched runs are the samples, and Phase 1's runs per commit, given as the third argument for every commit, is the multiplier.
- *Beats noise*: every one of the change's 3 samples is below the baseline's minimum, the saving is at least 1 billed minute per commit (private) or 10% of the wall time (public), and every job passed in every sample. With 3 samples a side, a change with no real effect passes this by chance 1 time in 20.

## Contents

- [1. Measure](#1-measure)
- [2. Find](#2-find)
- [3. Apply and prove](#3-apply-and-prove)
- [4. Open the pull request](#4-open-the-pull-request)
- [CI budget file](#ci-budget-file)
- [Sources](#sources)

## 1. Measure

Work in a scratch directory outside the repository (`cd "$(mktemp -d)"`), one subdirectory per workflow: every audit writes `runs.json` and `jobs.jsonl` into its own directory, and the scripts below read them from there.

1. **List the workflows by run count** (one API call):

```bash
set -euo pipefail
repo=OWNER/REPO
gh run list --repo "$repo" --limit 500 --json workflowName,event,createdAt |
  jq -r '(map(.createdAt | fromdateiso8601) | (max - min) / 86400) as $days | group_by(.workflowName) |
    map({w: .[0].workflowName, runs: length, events: (map(.event) | unique | join(","))}) | sort_by(-.runs) | .[] |
    "\(.runs) runs in \($days * 10 | floor / 10) days (\(.events)): \(.w)"'
```

2. **Billed minutes per run for each workflow that runs on `push`, `pull_request` or `schedule`**: in its subdirectory, run the [CI speed audit](github-actions.md#ci-speed-audit) with N=20, then `ci-minutes.sh` with the visibility from Step 1. Multiply each workflow's runs by its billed minutes per run, and give the full 150-run audit to the workflows that make up most of the total.
3. **The steps of the jobs that matter**: `ci-steps.sh "<job name>"` for the job the audit names as most often slowest and for the job with the most billed minutes.

```bash
#!/usr/bin/env bash
# CI minutes (read-only): billed minutes and wall time per run attempt, per commit, per job
# and per 30 days, from the CI speed audit's runs.json and jobs.jsonl (same directory).
# Usage: ci-minutes.sh PRIVATE|PUBLIC|INTERNAL [SHA [RUNS_PER_COMMIT]]     Needs: jq, column.
# With SHA (a commit or its prefix), it also prints one row per run attempt of that commit: a trial's
# samples, marked in the `sample` column. per_commit = billed × the commit's push and pull_request runs
# of this workflow. On the dispatch path, give RUNS_PER_COMMIT (Phase 1's "per commit" run count): it
# then applies to every row, and the dispatched runs are the samples.
# Billing: each job rounded up to a whole minute at the list rate of its standard GitHub-hosted
# runner label (rates below, from GitHub's "Actions runner pricing" page; re-check them).
# Self-hosted jobs are not billed by GitHub (0). Any other label (larger, custom or third-party
# runner) is not priced: it is listed and left out of the totals. Cancelled runs and cancelled
# jobs are not in the audit's files, though they bill: the real figure is higher.
set -euo pipefail
vis="$(printf '%s' "${1:-}" | tr '[:lower:]' '[:upper:]')"
case "$vis" in PUBLIC | PRIVATE | INTERNAL) ;; *) echo "usage: ci-minutes.sh PRIVATE|PUBLIC|INTERNAL [SHA [RUNS_PER_COMMIT]]" >&2; exit 1 ;; esac
sha="$(printf '%s' "${2:-}" | tr '[:upper:]' '[:lower:]')"; rpc_arg="${3:-}"
case "$rpc_arg" in "" | [1-9] | [1-9][0-9]) ;; *) echo "error: RUNS_PER_COMMIT must be a whole number from 1 to 99" >&2; exit 1 ;; esac
[ -z "$rpc_arg" ] || [ -n "$sha" ] || { echo "error: RUNS_PER_COMMIT needs a SHA" >&2; exit 1; }
for f in runs.json jobs.jsonl; do
  [ -e "$f" ] || { echo "error: $f missing; run ci-speed-audit.sh in this directory first" >&2; exit 1; }
done
[ -s jobs.jsonl ] || { echo "no runs: the audit found no completed jobs to measure; review the workflow statically" >&2; exit 2; }
if [ -n "$sha" ] && ! jq -e --arg w "$sha" 'any(.[]; (.headSha // "") | startswith($w))' runs.json > /dev/null; then
  echo "error: no run of commit $sha in runs.json (widen N or check the SHA)" >&2; exit 1
fi
jq -rs --slurpfile runs runs.json --arg vis "$vis" --arg want "$sha" --arg rpcarg "$rpc_arg" '
  def median: sort | if length == 0 then 0 else .[length / 2 | floor] end;
  def class: (.labels // [] | map(ascii_downcase)) as $l |
    if any($l[]; . == "self-hosted") then "self-hosted"
    elif ($l | length) != 1 then "other"
    else $l[0] |
      if test("^ubuntu-slim$") then "linux-slim"
      elif test("^ubuntu-(latest|[0-9]{2}\\.[0-9]{2})-arm$") then "linux-arm"
      elif test("^ubuntu-(latest|[0-9]{2}\\.[0-9]{2})$") then "linux"
      elif test("^windows-(latest|[0-9]{4}|11-arm)$") then "windows"
      elif test("^macos-(latest|[0-9]{2})(-intel)?$") then "macos"
      elif test("^macos-(latest|[0-9]{2})-large$") then "macos-large"
      elif test("^macos-(latest|[0-9]{2})-xlarge$") then "macos-xlarge"
      else "other" end end;
  def rate: {"linux-slim": 0.002, "linux-arm": 0.005, "linux": 0.006, "windows": 0.010,
    "macos": 0.062, "macos-large": 0.077, "macos-xlarge": 0.102, "self-hosted": 0}[.] // 0;
  map(. + {class: class, attempt: (.attempt // 1)}) |
  map(. + {billed: (if .class == "other" or .class == "self-hosted" or .total <= 0 then 0
                    else (.total + 59) / 60 | floor end)}) as $jobs |
  ($jobs | map(select(.class != "other" and .class != "self-hosted"))) as $hosted |
  ($runs[0] | map({key: (.databaseId | tostring), value: .headSha}) | from_entries) as $sha |
  ($runs[0] | map(.createdAt | fromdateiso8601) | sort) as $t |
  (if ($t | length) > 1 then ($t[-1] - $t[0]) / 86400 else 0 end) as $days |
  (if $days >= 1 then 30 * (($t | length) - 1) / $days else null end) as $per30 |
  ($runs[0] | map({key: (.databaseId | tostring), value: .event}) | from_entries) as $ev |
  ($jobs | group_by([.run, .attempt]) | map({run: .[0].run, attempt: .[0].attempt, sha: $sha[.[0].run | tostring],
     event: $ev[.[0].run | tostring], billed: (map(.billed) | add), usd: (map(.billed * (.class | rate)) | add),
     wall: ((map(.end) | max) - (map(.start) | min)), passed: all(.[]; .conclusion == "success")})) as $att |
  ($att | map(.run) | unique | length) as $nrun |
  def pp: .event == "push" or .event == "pull_request";
  ($att | map(select(.attempt == 1))) as $first |
  ($first | map(select(pp)) | group_by(.sha) | map({runs: length, billed: (map(.billed) | add)})) as $commits |
  ($commits | map(.runs) | median) as $rpc |
  "== Billed minutes (\($vis); each job rounded up to a whole minute, standard-runner list rates)",
  (if $nrun < ($runs[0] | length) then "warning: job data for \($nrun) of \($runs[0] | length) runs; the figures use those \($nrun)" else empty end),
  "runs: \($runs[0] | length) over \($days * 10 | floor / 10) days" +
    (if $per30 then ", about \($per30 | floor) per 30 days" else " (span under a day: no monthly rate)" end) +
    "; \($att | length) run attempts with job data",
  "per run (first attempts, median): \($first | map(.billed) | median) billed min, wall \($first | map(.wall) | median) s",
  (if ($commits | length) > 0 then
    "per commit (push and pull_request first attempts summed, median over \($commits | length) commits): \($commits | map(.billed) | median) billed min in \($rpc) run(s)" +
    (if $per30 then "; about \(($commits | length) / $nrun * $per30 | floor) commits per 30 days" else "" end)
   else "per commit: no push or pull_request runs in the sample" end),
  ($first | map(select(pp | not)) | group_by(.event) | .[] |
    "\(.[0].event) runs (not per commit): \(length)" + (if $per30 then ", about \(length / $nrun * $per30 | floor) per 30 days" else "" end) +
    ", median \(map(.billed) | median) billed min per run"),
  (if $per30 then "monthly estimate: \(($att | map(.billed) | add) / $nrun * $per30 | floor) billed min, \(($att | map(.usd) | add) / $nrun * $per30 * 100 | floor / 100) USD at list rates before the plan included usage" +
     (if $vis == "PUBLIC" then "; standard runners are free on a public repo, so optimize wall time" else "" end) else empty end),
  "rounding overhead: \((($hosted | map(.billed) | add // 0) - ($hosted | map(.total) | add // 0) / 60) * 10 | floor / 10) of \($hosted | map(.billed) | add // 0) billed min",
  (if any($jobs[]; .class == "other") then
    "not priced (larger, custom or third-party runner; left out of the totals): " +
    ([$jobs[] | select(.class == "other") | (.labels // [] | join("+") | if . == "" then "(no label)" else . end)] | group_by(.) | map("\(.[0]) ×\(length)") | join(", "))
   else empty end),
  "== Per job: billed minutes per 30 days (largest first)",
  (["job", "class", "jobs", "median_s", "max_s", "billed/run", "billed/30d"] | @tsv),
  ($jobs | group_by(.job) | map({job: .[0].job, class: .[0].class, n: length,
      med: (map(.total) | median), max: (map(.total) | max),
      b: (if .[0].class == "other" then "n/a" else map(.billed) | median end),
      m: (if .[0].class == "other" or ($per30 | not) then "n/a" else (map(.billed) | add) / $nrun * $per30 | floor end)})
    | sort_by(if (.m | type) == "number" then -.m else 0 end) | .[]
    | [.job, .class, .n, .med, .max, .b, .m] | @tsv),
  "== Duplicate runs: commits that ran this workflow on both push and pull_request",
  ($runs[0] | map(select(.headSha != null)) | group_by(.headSha)
    | map(select((map(.event) | unique) as $e | ($e | index("push")) and ($e | index("pull_request"))))
    | "\(length) commits" + (if length > 0 then " (e.g. \(.[0][0].headSha[0:7]))" else "" end) +
      (if $per30 and length > 0 then "; about \(length / $nrun * $per30 | floor) per 30 days" else "" end)),
  "== Jobs under a minute (each still bills a whole minute on a private repo)",
  ($hosted | group_by(.job) | map(select((map(.total) | median) < 60)) | map(.[0].job) | if length == 0 then "none" else join(", ") end),
  (if $want == "" then empty else
    ($att | map(select(.sha != null and (.sha | startswith($want))))) as $s |
    ($s | map(select(pp) | .run) | unique | length) as $pp |
    (if $rpcarg != "" then ($rpcarg | tonumber) elif $pp > 0 then $pp else null end) as $n |
    (if $rpcarg != "" then [$s[] | select(.event == "workflow_dispatch") | .run]
     else [($s | map(select(.event == "pull_request")) | min_by(.run) // empty | .run)] as $pr |
       if ($pr | length) > 0 then $pr else [($s | map(select(.event == "push")) | min_by(.run) // empty | .run)] end
     end) as $sampled |
    "== Samples of commit \($want): \($pp) push/pull_request run(s)" +
      (if $n == null then "; per_commit n/a: pass Phase 1 runs per commit as the third argument (dispatch path)"
       elif $rpcarg != "" then "; per_commit = billed × \($n) (RUNS_PER_COMMIT; dispatched runs are the samples)"
       else "; per_commit = billed × \($n)" end),
    (["run", "attempt", "event", "sample", "billed", "per_commit", "wall_s", "all_passed"] | @tsv),
    ($s | sort_by(.run, .attempt) | .[] | [.run, .attempt, .event, (.run as $r | if any($sampled[]; . == $r) then "yes" else "-" end),
      .billed, (if $n == null then "n/a" else .billed * $n end), .wall, .passed] | @tsv)
  end)
' jobs.jsonl |
  awk -F'\t' -v cmd="column -t -s '$(printf '\t')'" '   # align only the table lines
    NF > 1 { if (!t) { fflush(); t = 1 } print | cmd; next }
    { if (t) { close(cmd); t = 0 } print; fflush() } END { if (t) close(cmd) }'
```

```bash
#!/usr/bin/env bash
# CI steps (read-only, offline): median and max seconds per step of one job, slowest first,
# from the CI speed audit's jobs.jsonl. Usage: ci-steps.sh "JOB NAME"     Needs: jq, column.
set -euo pipefail
[ "$#" -eq 1 ] || { echo 'usage: ci-steps.sh "JOB NAME"' >&2; exit 1; }
[ -s jobs.jsonl ] || { echo "error: jobs.jsonl missing or empty; run ci-speed-audit.sh first" >&2; exit 1; }
jq -rs --arg job "$1" '
  def median: sort | if length == 0 then 0 else .[length / 2 | floor] end;
  map(select(.job == $job)) as $j |
  if ($j | length) == 0 then "error: no job named \($job) in jobs.jsonl\n" | halt_error(1) else . end |
  "== \($job): \($j | length) runs, median total \($j | map(.total) | median)s"' jobs.jsonl
jq -rs --arg job "$1" '
  def median: sort | if length == 0 then 0 else .[length / 2 | floor] end;
  map(select(.job == $job)) as $j | ($j | map(.total) | median) as $tot |
  (["step", "median_s", "max_s", "share"] | @tsv),
  ([$j[].steps[]] | group_by(.name) | map({name: .[0].name, m: (map(.s) | median), x: (map(.s) | max)})
    | sort_by(-.m) | .[] | [.name, .m, .x, (if $tot > 0 then "\(.m * 100 / $tot | floor)%" else "-" end)] | @tsv)
' jobs.jsonl | column -t -s $'\t'
```

How to read them:

- **Say which goal the run uses.** On a private or internal repository, rank by `billed/30d`. On a public one, rank by the critical path: the chain of jobs (`needs:`) and steps a pull request waits on.
- **The monthly figure is an estimate**: billed minutes per run times the run rate over the sample's date span (it needs at least a day). It is a list price before the plan's included usage, and cancelled runs and jobs are not counted, so the real usage is higher. `billed/run` is a median and `billed/30d` a sum: a large `max_s` next to a small median is an outlier run (and a `timeout-minutes` finding). `per commit` sums each commit's first `push` and `pull_request` attempts, so both runs of one commit count together; `schedule`, dispatch and other runs get their own line and are not commits.
- **Rates** are GitHub's list prices per minute for standard runners (fetched 2026-11-16): `ubuntu-slim` 0.002, Linux arm64 0.005, Linux 0.006, Windows 0.010, macOS 0.062, `macos-*-large` 0.077, `macos-*-xlarge` 0.102 USD. Any other label is a larger, custom or third-party runner: the script lists it as `not priced`, shows `n/a` for its job, and leaves it out of the totals, so name it in the report. Larger runners bill even on public repositories. This skill never adds one.
- GitHub's per-run `timing` endpoint is closed for accounts on the new billing platform, so the script computes minutes from job durations. A run's `updatedAt` is not its finish time (it moves later), so wall time comes from the jobs' own timestamps. A job carried over unchanged into a "Re-run failed jobs" attempt is counted once, in the attempt that ran it.

Done when each audited workflow has a billed-minutes block and a per-job table from real runs, plus the step tables; or the report states why no runs could be read (no `gh` auth, the audit's "0 completed runs" exit 2, no history) and the review is static.

## 2. Find

Walk the findings in this order: earlier ones remove work, later ones only make work faster. Each finding names its evidence line from Phase 1 and its expected saving against the goal.

| Signal (Phase 1) | Finding | Free fix |
|---|---|---|
| A CI step runs a check that a hook already runs, outside the deliberate overlaps | Duplicate of the Check Routing Table | Remove it, through Step 3's merge procedure; the bypass guard already re-runs the hooks |
| A step that is not on the critical path and not a top minute consumer | Not worth changing *(practitioner: "if the build takes ten minutes and lint takes one, making lint instant still leaves you waiting ten minutes")* | None. List it as out of scope |
| A lint, format or type-check step in CI that no hook runs | A check in the wrong lane (Check Routing Table) | Propose the hook first (Step 2 and the merge procedure); the bypass guard then covers it in CI. A swap is proposed only for what stays in CI |
| `Duplicate runs` above 0, private or internal repository | Each pull request commit runs the workflow twice: `push` on every branch plus `pull_request` | `push:` limited to the default branch, `pull_request` unchanged. On a public repository it saves no billed minutes and no wall time: list it, do not trial it |
| Several `Jobs under a minute` on a private repository | Rounding: ten 30-second jobs bill ten minutes for five | Merge them into one job, commit-stage checks first. Keep them separate on a public repository when that shortens the critical path |
| One test job dominates and its tests repeat one assertion over many generated inputs (pages, fixtures, locales) | Test scope wider than what it proves *(practitioner)* | Test the shared template or code path with representative cases, and validate the content itself with a fast script instead of a browser. Browser tests stay for navigation, interaction and integration |
| Cache restore plus save steps take about as long as the work they avoid | A cache that costs more than it saves *(practitioner: "a cache hit isn't automatically a faster pipeline")* | A trial that drops or rescopes it |
| A test step dominates while its independent tests run one after another, or workers fight for the runner's cores | Wrong parallelism | Run independent tests concurrently, or trial two or three worker counts; split into groups of equal duration on public repositories only. More workers can be slower *(practitioner)* |
| Independent setup steps run one after another, or a job waits on `needs:` for work it repeats | Serial setup | Overlap them (a service container starting while dependencies install), or drop the `needs:` |
| A tool step is on the critical path or a top minute consumer | Slow tool | A tool swap, under the rules below |
| Matrix legs on `pull_request`, no `timeout-minutes`, cold caches | Already covered by the [audit table](github-actions.md#3-read-the-numbers) | That table's fix |

**Test-scope findings change what is tested, so they need their own approval.** The proposal names each test file or group, the assertion it repeats, the representative cases that replace it, and the content check that keeps the rest covered. Nothing is deleted or skipped until the user approves that named finding; a blanket "make CI faster" is not approval.

### Tool swaps

Propose a swap only when Phase 1 puts its step on the critical path or among the top minute consumers. Every proposal carries a trial on the branch and a list of what the swap loses; the user approves both before it is kept. A tool that a hook runs is swapped in `.pre-commit-config.yaml` too, through the merge procedure, so the hook and the guard stay the same tool.

| Swap | What the trial must show | What it can lose |
|---|---|---|
| ESLint → Oxlint, with ESLint kept for the rules Oxlint lacks | The lint step (Oxlint plus the remaining ESLint run) before and after; the same findings on the current tree | Nothing: ESLint keeps every rule Oxlint lacks, and no rule is dropped to save its run *(practitioner: 107 s → 3 s, after trimming some rules, which this mode does not do)* |
| Prettier → Oxfmt | Format-check time before and after; the number of files Oxfmt would reformat on the current tree | Oxfmt is pre-1.0 (0.79.0, 2026-11-16): pin the exact version. Its defaults differ (`printWidth` 100) and Prettier plugins are not supported; the reformat diff is part of the approval *(practitioner: 37 s → 1 s)* |
| `tsc` 6 → TypeScript 7's native `tsc` | Type-check time before and after; the same error count and the same project files checked (`tsc --listFilesOnly`, ignoring `node_modules` and the bundled `lib.*.d.ts`) | Framework checkers that embed TypeScript (Astro, Vue, Svelte templates) still need their own checker. A fast check that silently skips files is no win *(practitioner: 67 s → 17 s)* |
| `npm ci` → `bun ci` for the install step only | Install step time before and after; the same dependency tree (`npm ls --all` after each) | Under `--frozen-lockfile` and `bun ci`, Bun migrates `package-lock.json` in memory and writes nothing, so the lockfile stays npm's. Build and tests keep running on Node *(practitioner: installs in 3–6 s)* |
| A framework migration (for example Next.js → Astro for a mostly static site) | Not a CI change | Report it as a finding with the build step's share of the critical path. Never perform it in this mode |

Never propose a paid or larger runner, sharding on a private repository, a cache above the free 10 GB, or relaxing a lint rule or threshold to save time.

Done when every finding has an evidence line, an expected saving and a free fix, and the list is ranked by expected saving. Ask the user which findings to apply, one answer per finding. Stop here when the user asked for an audit only, or approved none.

## 3. Apply and prove

1. **One approval before anything is pushed**, on every repository: name the branch, the draft pull request, the number of runs the trials trigger, and the measurement budget in billed minutes (free on a public repository's standard runners, but it still takes time). Budget it from Phase 1: a push costs the billed minutes per commit of every workflow that runs on the branch's pushes and pull request (doubled while `Duplicate runs` is above 0), a re-run costs one run attempt of the measured workflow, and the budget is `(approved changes + 1) × (one push + 2 re-runs)`, plus the run that opening the pull request triggers, one push per change for a possible revert (including one at the budget stop), and one for the final log commit. On the dispatch path (step 4), each measurement is 3 dispatches instead of a push and 2 re-runs, plus whatever `push` and `pull_request` runs the commit triggers itself. Declined → stop; nothing is pushed.
2. **Branch in a separate worktree**, never in the user's working tree: `git fetch origin && git worktree add -b ci/minutes-<yyyymmdd> <scratch path> origin/<default-branch>` (add `-2`, `-3` when the branch exists). Fetching the default branch fresh satisfies Repo Sync Before Edits, and the user's uncommitted work stays where it is.
3. **Check the triggers before each push**: the workflow's `on:` events, `branches`, `paths`/`paths-ignore`, `types`, and job `if:` conditions on drafts.
4. **Baseline.** The first commit adds the [CI budget file](#ci-budget-file). Push it, then open the pull request: a draft unless the workflow skips drafts, otherwise ready and titled `Do not merge: measuring CI minutes`. Re-run the commit's `pull_request` run of the measured workflow twice (its `push` run when there is none) with `gh run rerun <run-id>`: 3 samples. If a path filter skips that commit, there is no baseline from pushes: either stop and report, or, if the workflow has `workflow_dispatch`, show the user that no job in it deploys, publishes or uses environment secrets under that event, get their yes naming the jobs that will run, and use `gh workflow run <workflow> --ref ci/minutes-<yyyymmdd>` three times instead; every later commit is then sampled the same way, with the same third argument, so the samples stay comparable. If any job fails in the baseline, stop: no change can beat a red baseline.
5. **One atomic commit per approved change**, in the Phase 2 order. Show its diff and get the user's confirmation, as the merge procedure requires; on this branch git history replaces the `.bak` copy, so never commit a `.bak` file.
6. **Measure each commit**: push, re-run twice (or dispatch three times, as in step 4), then run the audit with the branch as its fourth argument (`ci-speed-audit.sh OWNER/REPO <workflow> 10 ci/minutes-<yyyymmdd>`) in a fresh subdirectory, and `ci-minutes.sh <visibility> <sha>` for this commit's 3 samples (add Phase 1's runs per commit as a third argument on the dispatch path). For a cache change, compare warm attempts with warm ones, and do not keep a change that wins warm but loses more on its first, cold run.
7. **Keep or revert.** Kept when it beats noise against the baseline; its samples become the next baseline. Otherwise `git revert --no-edit` it and push; never force-push or rewrite the branch.
8. **Stop conditions.** No run completes within 3 times the Phase 1 median wall time: stop and report. The billed minutes on the branch reach the approved budget: revert any change not yet measured and log it as `not measured`. The approved list is done: go to Phase 4.
9. **Experiment log.** Keep one row per change, kept, reverted or not measured, in the scratch directory, and append them to the budget file in one final commit, pushed normally and counted in the budget. Never mark it `[skip ci]`: a skipped head commit leaves the pull request's required checks Pending and blocks the merge. Its run is the last check that the branch is green.

Done when every approved change has a kept, reverted or `not measured` row with its numbers.

## 4. Open the pull request

Mark the draft ready (or retitle it), as `ci: cut Actions minutes (<kept> of <tried> changes kept)`. Its body has:

- the goal (billed minutes per commit, or wall time) and why;
- one row per change: job, baseline median (min–max), after median (min–max), billed minutes per commit before and after, and the monthly estimate before and after. Before is Phase 1's `monthly estimate`; after is before minus the per-commit saving times the commits per 30 days it applies to, plus the billed minutes of work moved to merges or a nightly schedule times its runs per 30 days. The saving applies to Phase 1's commits per 30 days, except for duplicate-run removal: that saves the removed `push` run on each duplicate commit (Phase 1's duplicate commits per 30 days times its billed minutes per run), and default-branch pushes keep their run. An unchanged workflow therefore keeps its figure. Scheduled runs are not commits, and the branch does not measure them: name a change's likely effect on them under the limits, not in the figure; the branch's own runs span too little time for a rate;
- each reverted or unmeasured change with the reason, so nobody retries it blind;
- each required status check whose name the branch changes (a merged job, a new matrix leg), so the branch protection can be updated before merge;
- what the numbers cannot show: samples from one short period on one branch, the cancelled runs left out, and list prices.

Never merge it, and never change a branch protection rule. Done when `gh pr view --json url` returns the URL.

## CI budget file

`.github/CI-BUDGET.md`, created on the branch as Phase 3's first commit (merge procedure when it already exists):

```markdown
# CI budget

Goal: <billed minutes per commit | wall time per pull request run>, measured <date> from <N> runs.

| Job | What failure it catches | Already covered by | Median time | Budget |
|---|---|---|---|---|

## Experiments

| Date | Change | Before (median, min–max) | After (median, min–max) | Kept? | Why |
|---|---|---|---|---|---|
```

`Budget` is the job's median time plus a margin the user agrees (20% unless they say otherwise). A check added to CI later gets a row first: what failure it catches, what already covers it, and the time it adds *(practitioner: "We spent too long treating every extra check as free")*. Every trial gets an experiment row, so the next agent does not repeat a failed one. If the repository has an `AGENTS.md`, propose one line pointing at this file.

## Sources

Fetched 2026-11-16. Re-check them when a figure here changes.

- "How we cut CI from an hour to under 3 minutes", @0xZoZoZo on X, 2026-11-16 (the *(practitioner)* rules): https://x.com/0xZoZoZo/status/2122477327003140194
- Actions runner pricing (each job rounded up to a whole minute; per-minute rates for standard and larger runners; larger runners not free on public repositories): https://docs.github.com/en/billing/reference/actions-runner-pricing
- "Actions Get workflow usage and Get workflow run usage endpoints closing down" (GitHub changelog, 2025-02-02): https://github.blog/changelog/2025-02-02-actions-get-workflow-usage-and-get-workflow-run-usage-endpoints-closing-down/
- REST "List jobs for a workflow run" (`filter=latest` is the default; `filter=all` returns every attempt): https://docs.github.com/en/rest/actions/workflow-jobs
- Skipping workflow runs (`[skip ci]` skips `push` and `pull_request` runs, and a skipped head commit leaves required checks Pending): https://docs.github.com/en/actions/how-tos/manage-workflow-runs/skip-workflow-runs
- Oxfmt (Prettier-compatible, pre-1.0; `oxfmt` 0.79.0 on npm, 2026-11-16) and its Prettier migration guide (`printWidth` 100, no Prettier plugins): https://oxc.rs/docs/guide/usage/formatter.html and https://oxc.rs/docs/guide/usage/formatter/migrate-from-prettier.html
- Bun lockfile docs (automatic migration of `package-lock.json`; under `--frozen-lockfile` and `bun ci` the migrated lockfile stays in memory and nothing is written): https://bun.com/docs/pm/lockfile
