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

- **Public repositories:** standard runners are free, so the goal there is wall time, not minutes.
- **Self-hosted runners:** free; they do not draw from included usage.
- **Larger runners:** billed per minute at their own rates, even on public repositories. This mode never proposes them; the script reports them as `unknown` with no price, so a bill containing them is flagged as understated, never silently priced at the standard rate.
- **Included usage** is a monthly dollar amount per plan (see [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)), not a minute quota. Report spend in USD and billed minutes per SKU.

Save as `billed-minutes.jq` next to `jobs.jsonl`:

```jq
# Billed minutes per run, priced per runner SKU, and a 30-day projection.
# Usage: jq -s --slurpfile counts counts.json -f billed-minutes.jq jobs.jsonl
def sku: (.labels // [] | map(ascii_downcase) | join(" ")) as $l |
  if ($l | test("self-hosted")) then "self-hosted"
  elif ($l | test("large|core|gpu")) then "unknown"
  elif ($l | test("macos")) then "macos"
  elif ($l | test("windows")) then (if ($l | test("arm")) then "windows_arm" else "windows" end)
  elif ($l | test("ubuntu")) then (if ($l | test("arm")) then "linux_arm" elif ($l | test("slim")) then "linux_slim" else "linux" end)
  else "unknown" end;
def median: sort | if length == 0 then 0 else .[length / 2 | floor] end;
{linux: 0.006, linux_arm: 0.005, linux_slim: 0.002, windows: 0.010, windows_arm: 0.010,
 macos: 0.062, "self-hosted": 0} as $rate |
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

Monthly estimate = median billed minutes (and USD) per run of each event × that event's 30-day run count, summed. State its limits in the report: it covers one workflow (repeat per workflow file), it reads only the latest attempt of each run, the audit's medians leave out cancelled runs and jobs, and `counts.json` counts cancelled runs at the full median. `unsampled_events` lists events with 30-day runs but none in the sample; they are left out of `month_total`, so report them as unpriced and re-run the audit with a sample that includes at least one run of each. It is an estimate, not the invoice.

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

- **Duplicate runs per commit:** `push` on every branch plus `pull_request` runs the workflow twice for each pull request commit. Finding: `push` on the default branch only.
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

1. **Budget first (private repositories):** estimate the minutes the measurement runs will bill (runs per change × billed minutes per run) and get the user's approval before triggering any.
2. **Approval per finding:** list the findings by name; apply only those the user approves.
3. **Branch:** create a branch; one atomic commit per approved change. Commit and push only with the user's approval.
4. **Measure:** at least three runs before and three after each change, same workflow and event. Keep a change only when its median beats the before median by more than the run-to-run spread and all jobs pass.
5. **Revert and log:** otherwise revert the commit and record the experiment in `.github/CI-BUDGET.md`.
6. **Pull request:** open one PR with the before/after table and the budget file. The user reviews and merges; the skill never merges and never configures a paid or larger runner.

## 8. CI budget and experiment log

Write `.github/CI-BUDGET.md` (a new file, shown as a diff first) so the next agent does not repeat an experiment:

```markdown
# CI budget

Measured on <date> over <N> runs of <workflow>. Billed: <min>/run, ~<min>/month (<USD> at private rates).

| Check | What it catches | What already covers it | Time added (median) |
|---|---|---|---|
| guard | hooks bypassed with --no-verify | nothing else | 48 s |

## Experiment log

| Date | Change | Before (median) | After (median) | Spread | Kept? | Why |
|---|---|---|---|---|---|---|
| 2026-11-17 | push on main only | 2 runs/commit | 1 run/commit | n/a | kept | halves pull request minutes |
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
