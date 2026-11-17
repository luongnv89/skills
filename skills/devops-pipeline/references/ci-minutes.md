# CI Minutes Optimization

Mode for an existing GitHub Actions pipeline whose minutes or cost the user wants cut. It extends the read-only [CI speed audit](github-actions.md#ci-speed-audit): audit billed minutes and the critical path, report named findings, apply only the findings the user approves, prove each with before/after runs, and end in a pull request the user merges. The skill never merges.

Practitioner source, a requirements hint rather than evidence: "How we cut CI from an hour to under 3 minutes", @0xZoZoZo, x.com/0xZoZoZo/status/2122477327003140194 (60m51s to 2m55s with no runner upgrade).

## Contents

1. [Billed minutes](#1-billed-minutes)
2. [Critical path](#2-critical-path)
3. [Duplicate runs and tiny jobs](#3-duplicate-runs-and-tiny-jobs)
4. [Test scope](#4-test-scope)
5. [Cache and parallelism](#5-cache-and-parallelism)
6. [Tool swaps](#6-tool-swaps)
7. [Apply and measure](#7-apply-and-measure)
8. [CI budget and experiment log](#8-ci-budget-and-experiment-log)
9. [Worked example](#worked-example)

## 1. Billed minutes

Run the audit script first; each `jobs.jsonl` line carries the job's runner `labels`, `total` seconds, and per-step seconds. Use the jobs API, not the per-run `timing` endpoint: GitHub marks "Get workflow run usage" as closing down, and it reports `total_ms: 0` on public repositories.

GitHub rounds each job up to a whole minute, then prices it per runner. Standard-runner rates in USD per minute, from [Actions runner pricing](https://docs.github.com/en/billing/reference/actions-runner-pricing), fetched 2026-11-17:

| Runner | SKU | USD/min |
|---|---|---|
| Linux 2-core x64 (`ubuntu-*`) | `actions_linux` | 0.006 |
| Linux 2-core arm64 (`ubuntu-*-arm`) | `actions_linux_arm` | 0.005 |
| Linux 1-core (`ubuntu-slim`) | `actions_linux_slim` | 0.002 |
| Windows 2-core x64 / arm64 | `actions_windows`, `actions_windows_arm` | 0.010 |
| macOS 3- or 4-core | `actions_macos` | 0.062 |
| macOS large (`macos-*-large`) | larger runner | 0.077 |
| macOS xlarge (`macos-*-xlarge`) | larger runner | 0.102 |

- **Public repositories:** standard runners are free, so the goal there is wall time, not minutes.
- **Self-hosted runners:** free; they do not draw from included usage.
- **Larger runners:** billed per minute at their own rates, even on public repositories. This mode never proposes them. The script prices the two macOS labels above and reports every other label (a custom, Linux or Windows larger runner, a third-party runner, or a job with several labels) as `unknown` with no price, so a bill containing them is flagged as understated, never silently priced at the standard rate. Labels match exactly, so `macos-15-xlarge` is never priced as `macos`.
- **Included usage** is a monthly dollar amount per plan (see [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)), not a minute quota. Report spend in USD and billed minutes per SKU.

Save as `billed-minutes.jq` next to `jobs.jsonl`:

```jq
# Billed minutes per run, priced per runner SKU, and a 30-day projection.
# Usage: jq -s --slurpfile counts counts.json -f billed-minutes.jq jobs.jsonl
def sku: (.labels // [] | map(ascii_downcase)) as $l |
  if any($l[]; . == "self-hosted") then "self-hosted"
  elif ($l | length) != 1 then "unknown"
  else $l[0] |
    if test("^ubuntu-slim$") then "linux_slim"
    elif test("^ubuntu-(latest|[0-9]{2}\\.[0-9]{2})-arm$") then "linux_arm"
    elif test("^ubuntu-(latest|[0-9]{2}\\.[0-9]{2})$") then "linux"
    elif test("^windows-11-arm$") then "windows_arm"
    elif test("^windows-(latest|[0-9]{4})$") then "windows"
    elif test("^macos-(latest|[0-9]{2})(-intel)?$") then "macos"
    elif test("^macos-(latest|[0-9]{2})-large$") then "macos_large"
    elif test("^macos-(latest|[0-9]{2})-xlarge$") then "macos_xlarge"
    else "unknown" end end;
def median: sort | if length == 0 then 0 else .[length / 2 | floor] end;
{linux: 0.006, linux_arm: 0.005, linux_slim: 0.002, windows: 0.010, windows_arm: 0.010,
 macos: 0.062, macos_large: 0.077, macos_xlarge: 0.102, "self-hosted": 0} as $rate |
map(. + {sku: sku, billed: ((.total / 60) | ceil)}) |
(group_by(.run) | map({event: .[0].event, secs: (map(.total) | add), min: (map(.billed) | add),
   usd: (map(.billed * ($rate[.sku] // 0)) | add), unpriced: (map(select(.sku == "unknown")) | length)})) as $runs |
{per_sku: (group_by(.sku) | map({sku: .[0].sku, jobs: length, secs: (map(.total) | add),
   billed_min: (map(.billed) | add), usd_per_min: $rate[.[0].sku]})),
 per_event: ($runs | group_by(.event) | map({event: .[0].event, runs: length,
   median_secs: (map(.secs) | median), median_billed_min: (map(.min) | median),
   median_usd: (map(.usd) | median * 1000 | round / 1000), unpriced_jobs: (map(.unpriced) | add)})
   | map(. + {runs_30d: ($counts[0][.event] // 0)}
     | . + {month_billed_min: (.median_billed_min * .runs_30d),
            month_usd: (.median_usd * .runs_30d * 100 | round / 100)}))}
| . + {month_total: {billed_min: (.per_event | map(.month_billed_min) | add // 0),
                     usd: (.per_event | map(.month_usd) | (add // 0) * 100 | round / 100)},
       unsampled_events: (($runs | map(.event)) as $seen | ($counts[0] // {}) | to_entries
         | map(select(.key | IN($seen[]) | not) | {event: .key, runs_30d: .value}))}
```

Count the last 30 days of runs per event, then project. Bind `repo` and `workflow` to the values the audit script measured:

```bash
repo=OWNER/REPO
workflow=ci.yml   # the workflow file the audit measured
since="$(jq -nr 'now - 30*86400 | strftime("%Y-%m-%d")')"
gh run list --repo "$repo" --workflow "$workflow" --created ">=$since" --limit 1000 --json event,conclusion \
  --jq 'map(select(.conclusion != "action_required" and .conclusion != "skipped"))
        | group_by(.event) | map({(.[0].event): length}) | add' > counts.json
if [ -s jobs.jsonl ]; then jq -s --slurpfile counts counts.json -f billed-minutes.jq jobs.jsonl
else echo 'no runs measured'; fi
```

Monthly estimate = median billed minutes (and USD) per run of each event × that event's 30-day run count, summed. State its limits in the report: it covers one workflow (repeat per workflow file), a run's billed minutes include its re-run attempts (a job carried over unchanged into a "Re-run failed jobs" attempt counts once), the audit's medians leave out cancelled runs and jobs, and `counts.json` counts cancelled runs at the full median. `unsampled_events` lists events with 30-day runs but none in the sample; they are left out of `month_total`, so report them as unpriced and re-run the audit with a sample that includes at least one run of each. It is an estimate, not the invoice.

Without `gh` auth or run history, review the workflow statically: report findings with no billed numbers, and say under `Uncertainty:` that no runs were measured.

## 2. Critical path

Wall time is the longest chain of `needs:`-linked jobs; inside a job, steps run in order. Find the slowest job and its slowest steps, plus the jobs that consume the most billed minutes:

```bash
jq -rs 'def median: sort | if length == 0 then 0 else .[length / 2 | floor] end;
  (group_by(.job) | max_by(map(.total) | median)) as $slow |
  "slowest job: \($slow[0].job), median \($slow | map(.total) | median)s",
  ($slow | map(.steps[]) | group_by(.name) | map({step: .[0].name, secs: (map(.secs) | median)})
   | sort_by(-.secs) | .[:6][] | "  \(.secs)s\t\(.step)"),
  "top consumers (billed min over the sample):",
  (group_by(.job) | map({job: .[0].job, min: (map((.total / 60) | ceil) | add)}) | sort_by(-.min) | .[:5][]
   | "  \(.min)\t\(.job)")' jobs.jsonl
```

Optimize the longest chain first. A step that is neither on the critical path nor in a top-consuming job gets no finding: cutting it changes neither wall time nor the bill.

## 3. Duplicate runs and tiny jobs

- **Duplicate runs per commit (private and internal repositories):** `push` on every branch plus `pull_request` runs the workflow twice for each pull request commit. The audit records each run's `headSha`; this prints the median runs per commit (used in §7) and the commits that ran on both events:

  ```bash
  jq -r 'map(select(.event == "push" or .event == "pull_request")) | group_by(.headSha) | map(length) | sort
    | if length == 0 then "no push or pull_request runs"
      else "runs per commit: \(.[length / 2 | floor]), duplicate commits: \(map(select(. > 1)) | length)" end' runs.json
  ```

  Finding: `push` on the default branch only. On a public repository the second run costs no billed minutes and no wall time: list it, do not trial it.
- **Tiny jobs (private repositories):** each job rounds up separately, so ten 15-second jobs bill 10 minutes for 2.5 minutes of work, each also repeating checkout and setup. Finding: merge them into one job's steps where they share a toolchain. On public repositories, keep them parallel if that shortens wall time.

## 4. Test scope

A large set of tests repeating one assertion (one template rendered for thousands of pages, one schema checked per fixture) can become representative cases plus a separate content validation (a schema or link check over all the data). This is a **named finding, proposed only**: it lists the tests affected, what keeps each behavior covered, and the measured time saved. It is applied only after the user approves that finding by name. "Delete the slow tests" or "just make it green" approves nothing. No test is deleted or skipped otherwise, no lint rule is relaxed except through an approved named finding (such as a tool swap's listed losses), and no coverage threshold is ever lowered.

## 5. Cache and parallelism

Measure, do not assume:

- **Cache:** compare restore + save seconds with the install or build seconds it avoids, on a warm run (key hit) and a cold run (key miss). A cache that costs more than it saves is a finding to remove it. Cache scope and seeding: [github-actions.md](github-actions.md#2-check-the-caches).
- **Parallelism:** time the suite at 1, 2 and the runner's core count of workers. More workers than cores can be slower (contention, per-worker setup). Keep the fastest measured value.

## 6. Tool swaps

Propose a faster tool only when its step is on the critical path or in a top-consuming job, with a measured trial on this repository and a list of what would be lost: unsupported lint rules, formatting diffs, files a fast type checker skips. Benchmarks and configs: [precommit-configs.md](precommit-configs.md).

- Oxfmt is pre-1.0 (0.79): a trial, never a silent default.
- Bun: for dependency install only; switching the lockfile needs the user's approval.
- Framework migrations (such as Next.js to Astro): reported as findings only, never performed.

"Swap every tool" is not a finding; each swap is its own named finding with its trial and losses.

## 7. Apply and measure

Terms used below:

- *Sample*: one attempt of a commit's measured run (its `pull_request` run, else its `push` run, else a dispatched run). *Per commit* = the sample's billed minutes × the commit's own `push` and `pull_request` runs of the workflow; a commit with none (dispatched samples) uses the runs per commit from the first audit (§3).
- *Baseline*: the last kept state on the branch: the baseline commit's 3 samples at first, then the samples of the latest kept change.
- *Beats noise*: all 3 samples of the change are below the baseline's minimum, the saving is at least 1 billed minute per commit (private, internal) or 10% of wall time (public), and every job passed in every sample. A change with no real effect passes this by chance about 1 time in 20.

Print a commit's samples from a fresh audit of the branch (`ci-speed-audit.sh OWNER/REPO <workflow> 10 ci/minutes-<yyyymmdd>`, in a new subdirectory), with `sha` bound to the full commit SHA:

```bash
jq -rs --slurpfile runs runs.json --arg sha "$sha" '
  ($runs[0] | map(select(.headSha == $sha))) as $r |
  ($r | map(select(.event == "push" or .event == "pull_request")) | length) as $pp |
  "commit \($sha[0:7]): \($pp) push/pull_request run(s)",
  (map(select(.run as $id | $r | any(.databaseId == $id))) | group_by([.run, .attempt]) | .[] |
   "run \(.[0].run) attempt \(.[0].attempt) \(.[0].event): billed \(map((.total / 60) | ceil) | add) min, " +
   "wall \((map(.end) | max) - (map(.start) | min)) s, all passed: \(all(.[]; .conclusion == "success"))")' jobs.jsonl
```

1. **Approval per finding:** list the findings by name; apply only those the user approves.
2. **One approval before anything is pushed**, on every repository: name the branch, the draft pull request, the runs the trials trigger, and the budget in billed minutes (free on a public repository's standard runners, but it still takes time). Budget = `(approved changes + 1) × (one push + 2 re-runs)`, plus the run that opening the pull request triggers, one push per change for a possible revert, and one for the final log commit. A push costs the billed minutes per commit of every workflow it triggers (doubled while duplicate runs exist); a re-run costs one attempt of the measured workflow. Declined → stop; nothing is pushed.
3. **Branch in a separate worktree**, never in the user's working tree: `git fetch origin && git worktree add -b ci/minutes-<yyyymmdd> <scratch path> origin/<default-branch>` (add `-2`, `-3` when the branch exists). The user's uncommitted work stays where it is. Before each push, check the workflow's `on:` events, `branches`, `paths`/`paths-ignore`, `types`, and job `if:` conditions on drafts.
4. **Baseline.** The first commit adds the budget file (§8). Push it and open the pull request: a draft, unless the workflow skips drafts, then ready and titled `Do not merge: measuring CI minutes`. Re-run the commit's measured run twice (`gh run rerun <run-id>`): 3 samples. If a path filter skips the commit and the workflow has `workflow_dispatch`, show the user that no job deploys, publishes or uses environment secrets under that event, get a yes naming the jobs that will run, then dispatch 3 times (`gh workflow run <workflow> --ref ci/minutes-<yyyymmdd>`); every later sample is dispatched the same way. Otherwise stop and report. If any job fails in the baseline, stop: no change can beat a red baseline.
5. **One atomic commit per approved change**, in finding order, its diff shown and confirmed first; git history replaces the `.bak` copy here, so never commit a `.bak` file. Push, re-run twice (or dispatch 3 times), then print its samples. For a cache change, compare warm attempts with warm ones, and drop a change that wins warm but loses more on its cold first run.
6. **Keep or revert.** Kept when it beats noise; its samples become the baseline. Otherwise `git revert --no-edit` it and push. Never force-push or rewrite the branch.
7. **Stop conditions.** No run completes within 3 times the audit's median wall time: stop and report. Billed minutes on the branch reach the approved budget: revert every change not yet measured and log it `not measured`.
8. **Log.** One row per change (kept, reverted, `not measured`) goes into `.github/CI-BUDGET.md` in one final commit, pushed and counted in the budget. Never mark it `[skip ci]`: a skipped head commit leaves the pull request's required checks Pending and blocks the merge.
9. **Pull request:** mark it ready (or retitle it) as `ci: cut Actions minutes (<kept> of <tried> changes kept)`, with the before/after table (median and min–max per change), each reverted or unmeasured change and why, every required status check whose name the branch changes (so branch protection can be updated first), and what the numbers cannot show: samples from one short period on one branch, cancelled runs left out, list prices. The user reviews and merges; the skill never merges, never changes a branch protection rule, and never configures a paid or larger runner.

## 8. CI budget and experiment log

Write `.github/CI-BUDGET.md` (a new file, shown as a diff first) so the next agent does not repeat an experiment:

```markdown
# CI budget

Measured on <date> over <N> runs of <workflow>. Billed: <min>/run, ~<min>/month (<USD> at private rates).

| Check | What it catches | What already covers it | Time added (median) |
|---|---|---|---|
| guard | hooks bypassed with --no-verify | nothing else | 48 s |

## Experiment log

| Date | Change | Before (median, min–max) | After (median, min–max) | Kept? | Why |
|---|---|---|---|---|---|
| 2026-11-17 | push on main only | 12 billed min/commit (12–13) | 6 (6–7) | kept | one run per commit instead of two |
```

## Worked example

Run on 2026-11-17 against two public repositories (free, so the dollar figures are at private-repo rates): `bash ci-speed-audit.sh <repo> ci.yml 30`, then the projection above. The `timing` endpoint returned `"total_ms": 0` for ripgrep run 44148873281.

**`BurntSushi/ripgrep`** (Linux, Windows x64 and arm64, macOS; sample 30 runs: 14 `pull_request`, 1 `push`, 15 `schedule`). Hand-check of run 44148873281 (`pull_request`): macOS job 64 s → ceil 2 min × $0.062 = $0.124; Windows jobs 110 s and 100 s → 2 + 2 = 4 min × $0.010 = $0.04; Windows arm job 110 s → 2 min × $0.010 = $0.02; 19 Linux jobs, 2455 s (40.9 min) of work, billed 50 min × $0.006 = $0.30. Run total 58 billed minutes, $0.484. Rounding alone added 9 Linux minutes (22%).

```text
per_event  runs  median_billed_min  median_usd  runs_30d  month_billed_min  month_usd
pull_request 14  56                 0.472       40        2240              18.88
push          1  54                 0.464       17         918               7.89
schedule     15  56                 0.466       31        1736              14.45
month_total: 4894 billed min, $41.22
```

**`luongnv89/asm`** (Linux only; sample 30 runs: 19 `pull_request`, 11 `push`). Run 44124847105 (`push`): 12 jobs, 1036 s; per-job ceil 1+1+2+2+2+1+1+3+3+1+3+1 = 21 min × $0.006 = $0.126, also the median for both events. 30-day counts: 141 `pull_request`, 55 `push` (8 `action_required` runs excluded) → 21 × 196 = 4116 billed min, $24.70 a month at private rates. Critical path: `build` (median 51 s) → `e2e-node (26)` (median 146 s, of which 89 s is `Run Node.js E2E tests` and 41 s `Install dependencies`). Top consumers: the three `e2e-node` legs (83-90 billed min each over 30 runs). Named findings: run the Node matrix off pull requests (one version there), and measure whether caching `node_modules` beats the 41 s install, warm and cold.
