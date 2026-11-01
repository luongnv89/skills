# GitHub Actions Workflow Templates

Philosophy: **lean, fast CI**. pre-commit already handles format, lint, type-check, unit tests, and E2E tests locally, so GitHub Actions carries only the four responsibilities the SKILL's Check Routing Table assigns it: a diff-scoped bypass guard, multi-version matrix testing (which doubles as the default-branch full-suite run), secrets-dependent work, and deployment. Each job is also tuned for feedback speed, with free techniques only: an agent that pushes, waits for CI, fixes, and pushes again spends most of its loop waiting on the slowest job.

## The one rule every template here follows

`pre-commit run` executes **commit-stage hooks only**. Hooks on `stages: [pre-push]` — the full test suite, coverage threshold, and CLI E2E — are silently skipped unless you also pass `--hook-stage pre-push`. `pre-commit/action@v3.0.1` shares this blind spot, which is why these templates call the CLI directly instead:

```yaml
  hooks:
    name: Verify hooks were not bypassed
    if: github.event_name == 'pull_request'   # avoids the all-zeros `github.event.before`
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0                      # `--from-ref` needs the base SHA locally
          filter: blob:none                   # full history, file contents fetched on demand
      # ... set up the project toolchain and Python here ...
      - name: Run both hook stages over the PR diff
        run: |
          pip install pre-commit
          base="${{ github.event.pull_request.base.sha }}"
          pre-commit run --from-ref "$base" --to-ref HEAD
          pre-commit run --hook-stage pre-push --from-ref "$base" --to-ref HEAD
```

Three details are load-bearing, and dropping any one of them makes the job fail on its first run:

- **`fetch-depth: 0`.** `actions/checkout` clones at depth 1, so the base SHA is not in the object store and `--from-ref` dies on a bad object.
- **`if: github.event_name == 'pull_request'`.** On a `push` event `github.event.before` is all zeros for a branch's first push, and stale after a force-push. Pull requests are where bypassed commits actually enter, so guard there.
- **The project's toolchain in the same job.** Hooks declared `language: system` shell out to `npm`, `mypy`, `go`, or `cargo`; a bare Python job cannot run them.

Scoping to the diff with `--from-ref`/`--to-ref` is what keeps the guard cheap. Running `--all-files` in CI re-checks the entire repository on every push and is the cost blow-up this skill exists to avoid. `filter: blob:none` is a speed detail, not a load-bearing one; see [Blobless checkout](#blobless-checkout).

## Table of Contents

- [Fast CI at no extra cost](#fast-ci-at-no-extra-cost)
- [Minimal (pre-commit already covers everything)](#minimal-pre-commit-already-covers-everything)
- [JavaScript/TypeScript](#javascripttypescript)
- [Python](#python)
- [Go](#go)
- [Rust](#rust)
- [Java (Maven)](#java-maven)
- [Multi-language](#multi-language)
- [Common Additions](#common-additions)
- [CI speed audit](#ci-speed-audit)
- [Sources](#sources)

---

## Fast CI at no extra cost

A pull request takes as long as its slowest job, plus the time that job waited for a runner. Every technique below is free on a public repository and cost-neutral or cost-reducing on a private one. None of them buys a faster machine.

### Who pays

Run `gh repo view --json visibility --jq .visibility` and record the answer in Step 1; `INTERNAL` bills like private. Generate the workflow for that answer. Only the guard's leg split reads `github.event.repository.visibility` at run time: the guard runs on `pull_request`, whose payload always carries the repository, and anything but `public` gets the single leg. Everything else is written in or left out when the workflow is generated, because a `schedule` payload carries no repository:

| Generated piece | Public repository | Private repository |
|---|---|---|
| Guard legs (run-time split) | One per hook stage | One, commit stage first |
| Version matrix, and Minimal's `full` (only with affected-test selection) | Every merge | Every merge under 30 default-branch commits a month; nightly from 30 |
| Codecov upload | One matrix leg, no run-time visibility test | Left out; coverage summary in `$GITHUB_STEP_SUMMARY` |
| `seed-cache` (Minimal only) | Every merge | Left out |
| Rust macOS legs | In the matrix | Left out; a macOS job on release tags or nightly when needed |

| | Public repository | Private repository |
|---|---|---|
| Standard GitHub-hosted runners | Free and unlimited | Plan's included usage, then billed per minute |
| Linux runner (`ubuntu-latest`) | 4 vCPU, 16 GB RAM | 2 vCPU, 8 GB RAM |
| Billing granularity | None | Each job rounded up to a whole minute |
| One more parallel job or shard | Free, within the plan's concurrent-job limit | Adds its own setup time and minute rounding to the bill |

**Out of scope because they cost money:** third-party runner services (they sell faster machines, and they are paid), GitHub larger runners (not free even on public repositories), sharding a private repository's tests across extra jobs, and raising the Actions cache limit above the free 10 GB per repository.

### The techniques

| Technique | Public | Private | Where |
|---|---|---|---|
| Cancel superseded pull request runs | Yes | Yes | `concurrency:` |
| Seed dependency caches from the default branch | Every merge | Per merge, or nightly on a busy repository | `matrix-test`; Minimal: `seed-cache` |
| Blobless full-history checkout in the guard | Yes | Yes | `filter: blob:none` |
| `timeout-minutes` on every job | Yes | Yes | Each job |
| Affected-only tests once the suite is slow, full suite on the default branch | Yes | Yes | `scripts/affected-tests.sh`, `matrix-test` or `full` |
| Guard split into parallel jobs by hook stage | Yes | No: one job, commit stage first | `matrix.stages` |
| Slow suite sharded across standard runners | Yes, below the concurrency limit | No | `--shard` |
| Test workers matched to runner cores | 4 | 2 | Runner default |

The JavaScript/TypeScript, Python, and Minimal templates carry the full set; affected-test selection exists for Vitest (`scripts/affected-tests.sh`) and for monorepo tools, so other suites run whole in the guard, in parallel. Go, Rust, Java, and Multi-language carry the universal ones (concurrency, blobless guard, timeouts) and keep the matrix on every merge (Multi-language: every merge that touches that language); on a private repository, move it to `schedule:` the same way when the default branch gets 30 or more commits a month.

### Cancel superseded runs

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.run_id }}
  cancel-in-progress: true
```

The pull request number exists only on `pull_request` events, so an agent's new push cancels the run it supersedes. `push`, `schedule`, and `workflow_dispatch` runs fall back to their own run ID and are never cancelled: they seed caches, run the nightly suite, and deploy. GitHub's docs show the same fallback with `github.head_ref`, but a branch name is not unique: two fork pull requests from branches named `patch-1` would cancel each other.

### Seed caches from the default branch

A cache saved by a `pull_request` run belongs to `refs/pull/<n>/merge`: later runs of that pull request can restore it, and other pull requests cannot. Every run can restore caches from its own branch, its base branch, and the default branch. A workflow with no default-branch job therefore never writes a cache a new pull request can use, and every pull request's first run installs cold.

- `actions/setup-node` keys its cache on OS, architecture, package manager, and lockfile hash, not on the Node version, so any default-branch job with `cache: npm` seeds the key the guard restores. `actions/setup-python` adds the Python version to its key: seed with the version the guard uses.
- The templates seed from the default-branch `matrix-test`, which runs anyway: per merge, or nightly on a busy private repository. One leg also restores and saves the pre-commit cache. The Minimal template has no matrix, so on a public repository it gets a `seed-cache` job on every merge that installs only on a cache miss. On a private repository that job would cost a rounded minute per merge, so it is left out.
- Cache the pre-commit hook environments too: `~/.cache/pre-commit`, keyed on the Python interpreter (`env.pythonLocation`, set by `setup-python`) and the hash of `.pre-commit-config.yaml`, as `pre-commit/action` does. Without the interpreter in the key, a Python patch update leaves broken environments behind an exact key match that is never re-saved.
- Caches unused for 7 days are evicted, and the free allowance is 10 GB per repository. Never raise the limit: usage above 10 GB is billed.

**`node_modules`.** `setup-node`'s `cache:` restores the package manager's download cache, not `node_modules`, so `npm ci` still runs on every job. Caching `node_modules` itself can be faster, but GitHub's cache examples advise against it: it breaks across Node versions, and `npm ci` deletes it. Adopt it only when the audit shows install time dominating and a measured restore beats the install. Then key on OS, Node version, and lockfile hash, set no `restore-keys`, and install only on an exact miss:

```yaml
      - uses: actions/cache@v4
        id: node-modules
        with:
          path: node_modules
          key: node-modules-${{ runner.os }}-node24-${{ hashFiles('package-lock.json') }}
      - if: steps.node-modules.outputs.cache-hit != 'true'
        run: npm ci
```

### Blobless checkout

`actions/checkout` fetches one commit by default. The guard needs history (`--from-ref` dies on a missing base SHA), and so do `nx affected`, `turbo --affected`, and `vitest --changed`. `fetch-depth: 0` provides it, but it also downloads every past version of every file. Adding `filter: blob:none` keeps every commit and tree, fetches file contents only for the checked-out commit, and lets git download an older blob on demand. checkout applies the filter together with full history: with `fetch-depth: 0` it drops the depth argument and keeps the filter.

Keep `persist-credentials` at its default so on-demand fetches can authenticate on a private repository. Never speed up a history reader with a shallow clone: `--from-ref` fails, and Turborepo treats a too-shallow checkout as "every package changed". Jobs that read no history keep the default single-commit fetch.

### Parallel jobs on public repositories, one job on private ones

On a public repository, split the guard's two hook stages into parallel matrix legs: format, lint, and type-check report in one leg while the tests run in the other. On a private repository each leg pays its own checkout, install, and minute rounding, so keep one leg that runs the commit stage first. The fast checks then fail first and end the job early. The templates derive the split from the event payload, and anything not provably public gets the single leg:

```yaml
    strategy:
      fail-fast: false
      matrix:
        stages: ${{ fromJSON(github.event.repository.visibility == 'public' && '["pre-commit", "pre-push"]' || '["pre-commit pre-push"]') }}
```

The run step loops `for stage in ${{ matrix.stages || 'pre-commit pre-push' }}`, so every stage runs in some leg, and a copy of the step in a job without the matrix still runs both. A matrix renames the check (`Verify hooks were not bypassed (pre-commit)`): when merging this into an existing workflow, list the branch's required status checks that need updating in the diff summary. Keep side work, such as a build or a migration check, out of the slowest leg.

### Affected-only on pull requests, full suite on the default branch

- **The guard is already diff-scoped for file-based hooks.** A test hook with `pass_filenames: false` is not, so once the suite outgrows the 60-second push budget, make it affected-aware. pre-commit exports `PRE_COMMIT_FROM_REF` and `PRE_COMMIT_TO_REF` to hooks on `pre-push` and whenever `--from-ref`/`--to-ref` is passed, so `scripts/affected-tests.sh` (in [precommit-configs.md](precommit-configs.md#fast-test-runs)) runs only the affected tests in both places, and the full suite when no range exists.
- **Monorepos:** `nx affected -t test --base=<sha> --head=<sha>` (`nrwl/nx-set-shas` finds the last successful default-branch commit), `turbo run test --affected` (`TURBO_SCM_BASE`/`TURBO_SCM_HEAD`), or `dorny/paths-filter` outputs on job-level `if:` to skip a whole language.
- **Filters list what may be skipped, never what must run.** An unmatched path, such as a new top-level directory or a shared config, runs everything. Vitest's `forceRerunTriggers` defaults to `package.json` and the Vite/Vitest configs; a tsconfig-only change otherwise selects no test at all, so add tsconfig files, lockfiles, and test setup files.
- **Guard the skip logic.** `vitest run --changed` exits 0 when it selects nothing, so a broken selector reports green with zero tests. The affected script fails when source files changed and no test was selected.
- **Skip with job-level `if:`, never workflow-level `paths:`, on a required workflow.** A workflow skipped by a path filter leaves its required checks Pending and blocks the merge; a job skipped by `if:` reports Success.
- **Backstop:** the full suite runs on the default branch. In the JavaScript/TypeScript and Python templates the version matrix is that run; in Minimal it is the `full` job, added only once a hook selects affected tests.
- **Per merge or nightly.** Per merge on a public repository: it is free, it uploads coverage on every merge, and a public repository's schedules are disabled after 60 days without activity. On a private repository, count the default branch's commits over the last 30 days: `git rev-list --count --first-parent --since=30.days <default-branch>` (for example `origin/main`). Under 30, run it per merge (`if: github.event_name == 'push' || github.event_name == 'workflow_dispatch'`), since nightly would be more runs; from 30, nightly (`schedule:` plus `workflow_dispatch`). A private repository's schedules are never disabled.
- **Schedules** use the default branch's latest commit. Cron is UTC; the optional `timezone:` key (an IANA name such as `Europe/Paris`) puts "nightly" in the team's night. Pick an odd minute, because the top of the hour is delayed under load.

### Match parallelism to the runner

- Vitest's `maxWorkers` defaults to all available parallelism in run mode: 4 workers on a public Linux runner, 2 on a private one. Keep the default and benchmark half (`--maxWorkers=50%`), which can be as fast and less flaky. Never hard-code a count tuned on a laptop.
- pytest-xdist: `-n auto` starts one worker per available CPU (physical cores when psutil is installed), `-n logical` one per logical core (needs `psutil`). pytest-xdist must be a dev dependency; Step 2 adds it when missing.
- TypeScript 7's `tsc --checkers` defaults to 4; on a 2-vCPU runner, benchmark `--checkers 2`.

### Timeouts

`timeout-minutes` defaults to 360, so a hung job on a private repository bills up to six hours. Set each job to about three times its typical duration from the audit.

### Queue wait and sharding

The time between a job's creation and its start is time the agent waits, and the audit measures it. On GitHub-hosted standard runners it is usually seconds; long waits come from the plan's concurrent-job limit (20 on Free, 40 on Pro, 60 on Team, 500 on Enterprise). More parallel legs or shards than the limit queue behind each other, so keep them below it. On a public repository a slow suite can also be sharded across standard runners for free (`vitest run --shard=<i>/<n> --reporter=blob`, then `vitest run --merge-reports`). On a private repository never shard: each shard repeats setup and rounds up to a minute.

---

## Minimal (pre-commit already covers everything)

If your pre-commit setup runs format, lint, type-check, unit tests, and E2E tests, CI shrinks to the bypass guard, plus a cheap cache-seeding job on a public repository. Generate it for the visibility Step 1 recorded:

- **Public:** as shown.
- **Private:** drop the `push` trigger and the `seed-cache` job. The workflow then runs on pull requests only, with one guard leg.

```yaml
name: CI

on:
  pull_request:
    branches: [main, master]
  push:                        # public repos only: seed-cache below
    branches: [main, master]

# A new push to a PR cancels its superseded run. Other events have no PR number,
# fall back to their unique run ID, and are never cancelled.
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.run_id }}
  cancel-in-progress: true

jobs:
  # PRs are where bypassed commits enter. Gating the job on `pull_request` also
  # avoids `github.event.before`, which is all zeros on a branch's first push.
  hooks:
    name: Verify hooks were not bypassed
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    timeout-minutes: 15
    strategy:
      fail-fast: false
      matrix:
        # The one run-time visibility test: a pull_request payload always carries
        # the repository. Public repos run free: one parallel leg per stage.
        # Anything not provably public pays per job: one leg, commit stage first.
        stages: ${{ fromJSON(github.event.repository.visibility == 'public' && '["pre-commit", "pre-push"]' || '["pre-commit pre-push"]') }}
    steps:
      - uses: actions/checkout@v4
        with:
          # A diff-scoped run needs BOTH endpoints in the object store, and
          # checkout defaults to fetch-depth 1 — without this the base SHA is
          # missing and `--from-ref` dies on a bad object.
          fetch-depth: 0
          # Blobless: every commit and tree, file contents only for this commit.
          filter: blob:none

      # ... set up the project toolchain and install dependencies here:
      # `language: system` hooks shell out to them ...

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Cache pre-commit environments
        uses: actions/cache@v4
        with:
          path: ~/.cache/pre-commit
          key: pre-commit-${{ runner.os }}-${{ env.pythonLocation }}-${{ hashFiles('.pre-commit-config.yaml') }}

      # The ONLY overlap with pre-commit, and it costs seconds because the run is
      # scoped to the diff. Every stage must run in some leg — `pre-commit run`
      # alone executes commit-stage hooks and silently skips the pre-push suite and E2E.
      - name: Run the hook stage(s) over the PR diff
        run: |
          pip install pre-commit
          base="${{ github.event.pull_request.base.sha }}"
          for stage in ${{ matrix.stages || 'pre-commit pre-push' }}; do
            pre-commit run --hook-stage "$stage" --from-ref "$base" --to-ref HEAD
          done

  # Public repos only: leave it out on a private repo, where it would bill a
  # rounded minute per merge. PR caches are scoped to refs/pull/<n>/merge; only
  # default-branch caches reach every PR.
  seed-cache:
    if: github.event_name == 'push'
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - uses: actions/cache@v4
        with:
          path: ~/.cache/pre-commit
          key: pre-commit-${{ runner.os }}-${{ env.pythonLocation }}-${{ hashFiles('.pre-commit-config.yaml') }}
      - run: pip install pre-commit && pre-commit install-hooks
```

The guard proves the hooks actually ran on the incoming commits — the one thing local tooling cannot prove about itself, since `--no-verify` skips hooks entirely. File-based hooks check only the diff, so they stay fast as the repository grows; project-wide hooks (type-check, test suites) run whole unless they select affected work.

### Add a default-branch full run only with affected-test selection

Without affected-test selection, the guard already ran the whole suite, so the template above has no full run and no `schedule:`. Once a hook selects affected tests (`scripts/affected-tests.sh`, `nx affected`, or `turbo run --affected`), add the `full` job as its backstop, on the same rule as the version matrix:

- **Public repository, or private with under 30 default-branch commits a month:** per merge. Keep the `push` trigger (add it back on a private repository) and add `workflow_dispatch:`. On a public repository `full` saves the same caches as `seed-cache`, so drop `seed-cache`.
- **Private with 30 or more:** nightly. Add `schedule:` and `workflow_dispatch:`, and use the commented nightly `if:`.

```yaml
on:
  pull_request:
    branches: [main, master]
  push:
    branches: [main, master]
  workflow_dispatch:
  # Private repo with 30+ default-branch commits a month: nightly instead of
  # per merge (and drop `push` unless another job uses it).
  # schedule:
  #   - cron: '27 3 * * *'       # UTC unless `timezone:` is set; odd minute
  #     timezone: 'Europe/Paris' # optional IANA time zone
```

```yaml
  # The backstop for hooks that select affected tests: with no ref range,
  # scripts/affected-tests.sh runs the whole suite. Runs on the default branch,
  # so its cache save also seeds the caches every PR restores.
  full:
    name: Default-branch full run
    # Per merge. A private repo with 30+ default-branch commits a month runs
    # it nightly instead:
    #   if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
    if: github.event_name == 'push' || github.event_name == 'workflow_dispatch'
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      # ... the same project toolchain and install steps as the guard ...
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - uses: actions/cache@v4
        with:
          path: ~/.cache/pre-commit
          key: pre-commit-${{ runner.os }}-${{ env.pythonLocation }}-${{ hashFiles('.pre-commit-config.yaml') }}
      - name: Run both hook stages over every file
        run: |
          pip install pre-commit
          pre-commit run --all-files
          pre-commit run --all-files --hook-stage pre-push
```

---

## JavaScript/TypeScript

Add matrix version testing — the part pre-commit can't do locally — as the default-branch full-suite run, with the guard tuned for fast feedback. Generate it for the visibility Step 1 recorded:

- **Public:** as shown. The matrix runs on every merge (free), seeds the caches every pull request restores, and uploads coverage to Codecov from one leg.
- **Private, under 30 default-branch commits a month:** as shown, with the Codecov step replaced by the commented coverage summary.
- **Private, 30 or more:** also switch the matrix to its commented nightly `if:` and add the commented `schedule:` trigger; keep `push` only when another job, such as a deploy, runs on it.

```yaml
name: CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]
  workflow_dispatch:
  # Private repo with 30+ default-branch commits a month: the matrix runs
  # nightly instead of per merge. Cron is UTC unless `timezone:` is set.
  # schedule:
  #   - cron: '27 3 * * *'       # an odd minute avoids top-of-hour delays
  #     timezone: 'Europe/Paris' # optional IANA time zone

# A new push to a PR cancels its superseded run. Other events have no PR number,
# fall back to their unique run ID, and are never cancelled.
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.run_id }}
  cancel-in-progress: true

jobs:
  # PRs are where bypassed commits enter. Gating the job on `pull_request` also
  # avoids `github.event.before`, which is all zeros on a branch's first push.
  hooks:
    name: Verify hooks were not bypassed
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    timeout-minutes: 15
    strategy:
      fail-fast: false
      matrix:
        # The one run-time visibility test: a pull_request payload always carries
        # the repository. Public repos run free: one parallel leg per stage.
        # Anything not provably public pays per job: one leg, commit stage first.
        stages: ${{ fromJSON(github.event.repository.visibility == 'public' && '["pre-commit", "pre-push"]' || '["pre-commit pre-push"]') }}
    steps:
      - uses: actions/checkout@v4
        with:
          # A diff-scoped run needs BOTH endpoints in the object store, and
          # checkout defaults to fetch-depth 1 — without this the base SHA is
          # missing and `--from-ref` dies on a bad object.
          fetch-depth: 0
          # Blobless: every commit and tree, file contents only for this commit.
          filter: blob:none

      # The project toolchain: `language: system` hooks shell out to it.
      # The npm cache key ignores the Node version, so the default-branch
      # matrix below seeds the key this job restores.
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 24
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      # pre-commit is a Python tool; the runner's system Python can refuse
      # `pip install` under PEP 668.
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Cache pre-commit environments
        uses: actions/cache@v4
        with:
          path: ~/.cache/pre-commit
          key: pre-commit-${{ runner.os }}-${{ env.pythonLocation }}-${{ hashFiles('.pre-commit-config.yaml') }}

      # The ONLY overlap with pre-commit, and it costs seconds because the run is
      # scoped to the diff (a slow suite's test hook selects affected tests). Every
      # stage must run in some leg — `pre-commit run` alone executes commit-stage
      # hooks and silently skips the pre-push suite and E2E.
      - name: Run the hook stage(s) over the PR diff
        run: |
          pip install pre-commit
          base="${{ github.event.pull_request.base.sha }}"
          for stage in ${{ matrix.stages || 'pre-commit pre-push' }}; do
            pre-commit run --hook-stage "$stage" --from-ref "$base" --to-ref HEAD
          done

  # The full suite on the default branch: the backstop for affected-only PR
  # runs, and the job that seeds the caches every PR restores.
  matrix-test:
    # Per merge. A private repo with 30+ default-branch commits a month runs
    # it nightly instead:
    #   if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
    if: github.event_name == 'push' || github.event_name == 'workflow_dispatch'
    runs-on: ubuntu-latest
    timeout-minutes: 20

    strategy:
      matrix:
        node-version: [22, 24, 26]

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm test            # must write coverage for the step below

      - name: Build
        run: npm run build

      # One leg also seeds the guard's pre-commit cache from the default
      # branch (same interpreter, same key).
      - if: matrix.node-version == 24
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - if: matrix.node-version == 24
        uses: actions/cache@v4
        with:
          path: ~/.cache/pre-commit
          key: pre-commit-${{ runner.os }}-${{ env.pythonLocation }}-${{ hashFiles('.pre-commit-config.yaml') }}
      - if: matrix.node-version == 24
        run: pip install pre-commit && pre-commit install-hooks

      # Public repos only, written in from Step 1's visibility, not tested at
      # run time. Codecov's team use on private repos is paid, so a private
      # repo gets this step instead. It reads coverage/coverage-summary.json:
      # add 'json-summary' to Vitest's `coverage.reporter` in vitest.config.
      # - name: Coverage summary
      #   if: matrix.node-version == 24
      #   run: |
      #     jq -r '.total | "Lines \(.lines.pct)%, branches \(.branches.pct)%"' \
      #       coverage/coverage-summary.json >> "$GITHUB_STEP_SUMMARY"
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        if: matrix.node-version == 24
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
```

### With pnpm

```yaml
      - name: Setup pnpm
        uses: pnpm/action-setup@v2
        with:
          version: 8

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 24
          cache: 'pnpm'

      - name: Install dependencies
        run: pnpm install --frozen-lockfile
```

With a warm store, pnpm links packages from it instead of downloading them. Measure the install in the audit before reaching for a `node_modules` cache.

---

## Python

Generate the workflow for the visibility Step 1 recorded:

- **Public:** as shown. The matrix runs on every merge (free), seeds the caches every pull request restores, and uploads coverage to Codecov from one leg.
- **Private, under 30 default-branch commits a month:** as shown, with the Codecov step replaced by the commented coverage summary (`coverage report --format=markdown`).
- **Private, 30 or more:** also switch the matrix to its commented nightly `if:` and add the commented `schedule:` trigger; keep `push` only when another job, such as a deploy, runs on it.

```yaml
name: CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]
  workflow_dispatch:
  # Private repo with 30+ default-branch commits a month: the matrix runs
  # nightly instead of per merge. Cron is UTC unless `timezone:` is set.
  # schedule:
  #   - cron: '27 3 * * *'       # an odd minute avoids top-of-hour delays
  #     timezone: 'Europe/Paris' # optional IANA time zone

# A new push to a PR cancels its superseded run. Other events have no PR number,
# fall back to their unique run ID, and are never cancelled.
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.run_id }}
  cancel-in-progress: true

jobs:
  # PRs are where bypassed commits enter. Gating the job on `pull_request` also
  # avoids `github.event.before`, which is all zeros on a branch's first push.
  hooks:
    name: Verify hooks were not bypassed
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    timeout-minutes: 15
    strategy:
      fail-fast: false
      matrix:
        # The one run-time visibility test: a pull_request payload always carries
        # the repository. Public repos run free: one parallel leg per stage.
        # Anything not provably public pays per job: one leg, commit stage first.
        stages: ${{ fromJSON(github.event.repository.visibility == 'public' && '["pre-commit", "pre-push"]' || '["pre-commit pre-push"]') }}
    steps:
      - uses: actions/checkout@v4
        with:
          # A diff-scoped run needs BOTH endpoints in the object store, and
          # checkout defaults to fetch-depth 1 — without this the base SHA is
          # missing and `--from-ref` dies on a bad object.
          fetch-depth: 0
          # Blobless: every commit and tree, file contents only for this commit.
          filter: blob:none

      # The pip cache key includes the Python version: the default-branch
      # matrix's 3.12 leg seeds the key this job restores.
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      # The dev extras hold every hook tool, pytest-xdist included.
      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Cache pre-commit environments
        uses: actions/cache@v4
        with:
          path: ~/.cache/pre-commit
          key: pre-commit-${{ runner.os }}-${{ env.pythonLocation }}-${{ hashFiles('.pre-commit-config.yaml') }}

      # The ONLY overlap with pre-commit, and it costs seconds because the run is
      # scoped to the diff. Every stage must run in some leg — `pre-commit run`
      # alone executes commit-stage hooks and silently skips the pre-push suite and E2E.
      - name: Run the hook stage(s) over the PR diff
        run: |
          pip install pre-commit
          base="${{ github.event.pull_request.base.sha }}"
          for stage in ${{ matrix.stages || 'pre-commit pre-push' }}; do
            pre-commit run --hook-stage "$stage" --from-ref "$base" --to-ref HEAD
          done

  # The full suite on the default branch: the backstop for affected-only PR
  # runs, and the job that seeds the caches every PR restores.
  matrix-test:
    # Per merge. A private repo with 30+ default-branch commits a month runs
    # it nightly instead:
    #   if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
    if: github.event_name == 'push' || github.event_name == 'workflow_dispatch'
    runs-on: ubuntu-latest
    timeout-minutes: 20

    strategy:
      matrix:
        python-version: ['3.12', '3.13', '3.14']

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'

      - name: Install dependencies
        run: pip install -e ".[dev]"

      # `-n auto` comes from pytest-xdist, which Step 2 puts in the dev extras:
      # one worker per available CPU (physical cores when psutil is installed).
      - name: Run tests with coverage
        run: pytest -n auto --cov --cov-report=xml -q

      # The 3.12 leg also seeds the guard's pre-commit cache from the default
      # branch (same interpreter, same key).
      - if: matrix.python-version == '3.12'
        uses: actions/cache@v4
        with:
          path: ~/.cache/pre-commit
          key: pre-commit-${{ runner.os }}-${{ env.pythonLocation }}-${{ hashFiles('.pre-commit-config.yaml') }}
      - if: matrix.python-version == '3.12'
        run: pip install pre-commit && pre-commit install-hooks

      # Public repos only, written in from Step 1's visibility, not tested at
      # run time. Codecov's team use on private repos is paid, so a private
      # repo gets this step instead:
      # - name: Coverage summary
      #   if: matrix.python-version == '3.12'
      #   run: coverage report --format=markdown >> "$GITHUB_STEP_SUMMARY"
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        if: matrix.python-version == '3.12'
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
```

### With uv

`astral-sh/setup-uv` saves uv's package cache to the Actions cache (`enable-cache`; its default `auto` enables it on GitHub-hosted runners). The same seeding rule applies, so give the default-branch jobs the same step. setup-uv publishes no floating major tag from v10 on, so pin a release.

```yaml
      - name: Install uv
        uses: astral-sh/setup-uv@v10.3.3
        with:
          enable-cache: true

      - name: Install dependencies
        run: uv sync --locked
```

### With Poetry

```yaml
      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: 1.7.1
          virtualenvs-create: true
          virtualenvs-in-project: true

      - name: Load cached venv
        uses: actions/cache@v4
        with:
          path: .venv
          key: venv-${{ runner.os }}-${{ matrix.python-version }}-${{ hashFiles('**/poetry.lock') }}

      - name: Install dependencies
        run: poetry install --no-interaction
```

---

## Go

```yaml
name: CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

# A new push to a PR cancels its superseded run. Other events have no PR number,
# fall back to their unique run ID, and are never cancelled.
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.run_id }}
  cancel-in-progress: true

jobs:
  # PRs are where bypassed commits enter. Gating the job on `pull_request` also
  # avoids `github.event.before`, which is all zeros on a branch's first push.
  hooks:
    name: Verify hooks were not bypassed
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
        with:
          # A diff-scoped run needs BOTH endpoints in the object store, and
          # checkout defaults to fetch-depth 1 — without this the base SHA is
          # missing and `--from-ref` dies on a bad object.
          fetch-depth: 0
          filter: blob:none

      # The project toolchain: `language: system` hooks shell out to it.
      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version: '1.22'
          cache: true

      # pre-commit is a Python tool; the runner's system Python can refuse
      # `pip install` under PEP 668.
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      # The ONLY overlap with pre-commit, and it costs seconds because the run is
      # scoped to the diff. Both invocations are required — `pre-commit run` alone
      # executes commit-stage hooks and silently skips the pre-push suite and E2E.
      - name: Run both hook stages over the PR diff
        run: |
          pip install pre-commit
          base="${{ github.event.pull_request.base.sha }}"
          pre-commit run --from-ref "$base" --to-ref HEAD
          pre-commit run --hook-stage pre-push --from-ref "$base" --to-ref HEAD

  matrix-test:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    if: github.event_name == 'push'

    strategy:
      matrix:
        go-version: ['1.21', '1.22']

    steps:
      - uses: actions/checkout@v4

      - name: Set up Go ${{ matrix.go-version }}
        uses: actions/setup-go@v5
        with:
          go-version: ${{ matrix.go-version }}
          cache: true

      - name: Run tests with coverage
        run: go test -race -coverprofile=coverage.out ./...

      - name: Build
        run: go build ./...

      # Public repos only, written in from Step 1's visibility: Codecov's team
      # use on private repos is paid. A private repo writes
      # `go tool cover -func=coverage.out | tail -n 1` to $GITHUB_STEP_SUMMARY instead.
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        if: matrix.go-version == '1.22'
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: coverage.out
```

---

## Rust

```yaml
name: CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

# A new push to a PR cancels its superseded run. Other events have no PR number,
# fall back to their unique run ID, and are never cancelled.
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.run_id }}
  cancel-in-progress: true

jobs:
  # PRs are where bypassed commits enter. Gating the job on `pull_request` also
  # avoids `github.event.before`, which is all zeros on a branch's first push.
  hooks:
    name: Verify hooks were not bypassed
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
        with:
          # A diff-scoped run needs BOTH endpoints in the object store, and
          # checkout defaults to fetch-depth 1 — without this the base SHA is
          # missing and `--from-ref` dies on a bad object.
          fetch-depth: 0
          filter: blob:none

      # The project toolchain: `language: system` hooks shell out to it.
      - name: Setup Rust
        uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt, clippy

      - name: Cache cargo
        uses: Swatinem/rust-cache@v2

      # pre-commit is a Python tool; the runner's system Python can refuse
      # `pip install` under PEP 668.
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      # The ONLY overlap with pre-commit, and it costs seconds because the run is
      # scoped to the diff. Both invocations are required — `pre-commit run` alone
      # executes commit-stage hooks and silently skips the pre-push suite and E2E.
      - name: Run both hook stages over the PR diff
        run: |
          pip install pre-commit
          base="${{ github.event.pull_request.base.sha }}"
          pre-commit run --from-ref "$base" --to-ref HEAD
          pre-commit run --hook-stage pre-push --from-ref "$base" --to-ref HEAD

  matrix-test:
    if: github.event_name == 'push'

    strategy:
      matrix:
        # Public repos: both OSes, free. Private repos: macOS minutes bill at
        # about 10x Linux, so generate `os: [ubuntu-latest]`, and when macOS
        # matters, a separate macOS job on release tags or a nightly schedule.
        os: [ubuntu-latest, macos-latest]
        rust: [stable, beta]

    runs-on: ${{ matrix.os }}
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4

      - name: Setup Rust ${{ matrix.rust }}
        uses: dtolnay/rust-toolchain@master
        with:
          toolchain: ${{ matrix.rust }}

      - name: Cache cargo
        uses: Swatinem/rust-cache@v2

      - name: Run tests
        run: cargo test --all-features

      - name: Build release
        run: cargo build --release
```

---

## Java (Maven)

```yaml
name: CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

# A new push to a PR cancels its superseded run. Other events have no PR number,
# fall back to their unique run ID, and are never cancelled.
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.run_id }}
  cancel-in-progress: true

jobs:
  # PRs are where bypassed commits enter. Gating the job on `pull_request` also
  # avoids `github.event.before`, which is all zeros on a branch's first push.
  hooks:
    name: Verify hooks were not bypassed
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
        with:
          # A diff-scoped run needs BOTH endpoints in the object store, and
          # checkout defaults to fetch-depth 1 — without this the base SHA is
          # missing and `--from-ref` dies on a bad object.
          fetch-depth: 0
          filter: blob:none

      # The project toolchain: `language: system` hooks shell out to it.
      - name: Set up JDK 21
        uses: actions/setup-java@v4
        with:
          java-version: '21'
          distribution: 'temurin'
          cache: 'maven'

      # pre-commit is a Python tool; the runner's system Python can refuse
      # `pip install` under PEP 668.
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      # The ONLY overlap with pre-commit, and it costs seconds because the run is
      # scoped to the diff. Both invocations are required — `pre-commit run` alone
      # executes commit-stage hooks and silently skips the pre-push suite and E2E.
      - name: Run both hook stages over the PR diff
        run: |
          pip install pre-commit
          base="${{ github.event.pull_request.base.sha }}"
          pre-commit run --from-ref "$base" --to-ref HEAD
          pre-commit run --hook-stage pre-push --from-ref "$base" --to-ref HEAD

  matrix-test:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    if: github.event_name == 'push'

    strategy:
      matrix:
        java-version: ['17', '21']

    steps:
      - uses: actions/checkout@v4

      - name: Set up JDK ${{ matrix.java-version }}
        uses: actions/setup-java@v4
        with:
          java-version: ${{ matrix.java-version }}
          distribution: 'temurin'
          cache: 'maven'

      - name: Run tests
        run: mvn test -q

      - name: Build
        run: mvn package -DskipTests -q
```

---

## Multi-language

For monorepos, path filters decide what runs, at no extra job: a step in the guard picks the toolchains a pull request needs, and each language's version matrix lives in its own push-only workflow that GitHub starts only when that language changed. `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  pull_request:
    branches: [main, master]

# A new push to a PR cancels its superseded run. Other events have no PR number,
# fall back to their unique run ID, and are never cancelled.
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.run_id }}
  cancel-in-progress: true

jobs:
  # ONE guard job, not one per language. A hook set is a single config: splitting
  # the guard across per-language jobs makes each one run every hook, so the
  # backend job would try to execute the eslint hook with no Node toolchain.
  # Per-language `files:` filters in .pre-commit-config.yaml already do the
  # scoping; the paths-filter step below decides which toolchains this job sets
  # up, not which hooks run. `files:` does not change cwd: Node entries must
  # `--prefix frontend`.
  hooks:
    name: Verify hooks were not bypassed
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          filter: blob:none

      # A step, not a separate `changes` job: that job would bill its own
      # rounded minute on every private run. On pull requests the filter reads
      # the changed files from the REST API.
      - uses: dorny/paths-filter@v3
        id: changes
        with:
          filters: |
            frontend:
              - 'frontend/**'
            backend:
              - 'backend/**'

      # Toolchains `language: system` hooks shell out to. Gate Node on the
      # frontend filter: `cache: npm` requires a lockfile, and this template's
      # lives at `frontend/package-lock.json`, not the repo root — a backend-only
      # PR would otherwise fail the guard with "Dependencies lock file is not found".
      - name: Setup Node.js
        if: steps.changes.outputs.frontend == 'true'
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      - if: steps.changes.outputs.frontend == 'true'
        working-directory: frontend
        run: npm ci

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - if: steps.changes.outputs.backend == 'true'
        run: pip install -e "backend/[dev]"

      - name: Run both hook stages over the PR diff
        run: |
          pip install pre-commit
          base="${{ github.event.pull_request.base.sha }}"
          pre-commit run --from-ref "$base" --to-ref HEAD
          pre-commit run --hook-stage pre-push --from-ref "$base" --to-ref HEAD
```

The per-language workflows carry CI-lane work only — a version matrix. They must not re-run the test suite at a single version: the pre-push hook already did that, and duplicating it is exactly what the routing table forbids. `.github/workflows/frontend-matrix.yml`:

```yaml
name: Frontend matrix

# Push-only and path-filtered: a merge that touches only backend/ starts no
# frontend run, so a private repo pays for no idle legs and needs no separate
# `changes` job. A push-only workflow is never a required pull request check,
# so its path filter cannot leave a check Pending. On a private repo with 30+
# default-branch commits a month, replace `push` with a nightly `schedule:`
# (which ignores `paths:` and runs every night).
on:
  push:
    branches: [main, master]
    paths: ['frontend/**']
  workflow_dispatch:

jobs:
  frontend:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    strategy:
      matrix:
        node-version: [18, 20, 22]
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      - working-directory: frontend
        run: npm ci
      - working-directory: frontend
        run: npm test
      - working-directory: frontend
        run: npm run build
```

`.github/workflows/backend-matrix.yml`, on the same rule:

```yaml
name: Backend matrix

on:
  push:
    branches: [main, master]
    paths: ['backend/**']
  workflow_dispatch:

jobs:
  backend:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e "backend/[dev]"
      - run: pytest -q
```

A filter lists what may trigger a run, so add shared paths a language depends on (a root lockfile, shared config) to its `paths:`. Deploy jobs that run on every merge go in a workflow without `paths:`.

---

## Common Additions

### Upload coverage to Codecov

Codecov's team use on private repositories is paid, so write the upload in only for a public repository, from Step 1's visibility. Never gate it at run time: a scheduled run's payload carries no repository, so a runtime visibility test would skip every nightly upload. On a private repository, write the coverage summary to `$GITHUB_STEP_SUMMARY` instead (`coverage report --format=markdown` for coverage.py; for Vitest, add `json-summary` to `coverage.reporter` and read `coverage/coverage-summary.json` with `jq`).

```yaml
      - name: Upload coverage to Codecov   # public repositories only
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
```

### PR status comment

```yaml
      - name: Comment PR
        uses: actions/github-script@v7
        if: github.event_name == 'pull_request'
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '✅ All checks passed!'
            })
```

### Deployment (on merge to main)

`hooks` is deliberately **not** in `needs:`. It only runs on `pull_request`, and a `needs:`
on a job that was skipped skips the dependent too — listing it here would mean main never
deploys. The guard already gated the pull request that produced this merge.

The same rule applies to `matrix-test`. It runs on every merge, so `needs: [matrix-test]` is
safe, except on a private repository with 30 or more default-branch commits a month, where it
runs nightly: there, drop the `needs:` line, or deploy from a release tag after a green nightly
run, or move the matrix back to `push` when every merge deploys.

```yaml
  deploy:
    # needs: [matrix-test]   # only when the matrix runs per merge, not nightly
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      # Add deployment steps
```

### Skipping specific pre-commit hooks in CI

Some hooks (like interactive formatters) may not make sense in CI. Skip them with the `SKIP` env var, on the guard job's run step:

```yaml
      - name: Run the hook stage(s) over the PR diff
        env:
          SKIP: "no-commit-to-branch"  # comma-separated hook IDs to skip
        run: |
          # ... the guard's pre-commit run lines, unchanged ...
```

Skip sparingly. Every skipped hook is a check that now runs nowhere, since the guard is the only place CI re-verifies hook output.

---

### Keeping the matrix off the hot path

Every template here keeps `matrix-test` off pull requests: it runs on merges to the default branch, or nightly (`schedule:` and `workflow_dispatch`) on a private repository with 30 or more default-branch commits a month. Keep it there. A three-version matrix on every pull request commit triples the bill on a private repository, and on any repository it takes three of the plan's concurrent-job slots from the agents' pull request runs, to re-confirm a signal the hooks already gave locally. On a public repository, if the audit shows queue waits at the concurrent-job limit, move it to nightly too; the generated Codecov upload then runs nightly. For a library where version skew is the main risk, widen it to `pull_request` only on the release branch, never on every push to a feature branch.

---

## CI speed audit

Audit mode for an existing pipeline. The audit is read-only: it needs an authenticated `gh` and `jq`, writes two scratch files (`runs.json`, `jobs.jsonl`) to the current directory, and changes nothing on GitHub or in the repository. Run it from a fresh scratch directory (`cd "$(mktemp -d)"`), never inside the audited repository, and run no hooks: an audit only reads.

### 1. Split every job into queue, setup, and work

Save as `ci-speed-audit.sh` in the scratch directory and run `bash ci-speed-audit.sh OWNER/REPO ci.yml 150`. Each run costs one API call; 50 runs take about a minute. Only runs and jobs that ended in success or failure count: a run cancelled by a newer push would drag the medians down.

```bash
#!/usr/bin/env bash
# CI speed audit (read-only): split every job of the last N runs into queue wait,
# setup (job setup, checkout, toolchain, cache, install, post steps) and work.
# Usage: ci-speed-audit.sh OWNER/REPO WORKFLOW [N]     Needs: gh (authenticated), jq.
set -euo pipefail
repo="$1"; workflow="$2"; limit="${3:-150}"
gh run list --repo "$repo" --workflow "$workflow" --status completed --limit "$limit" \
  --json databaseId,event,conclusion,createdAt,updatedAt |
  jq '[.[] | select(.conclusion == "success" or .conclusion == "failure")]' > runs.json
jq -r '.[] | "\(.databaseId) \(.event)"' runs.json | while read -r run_id event; do
  gh api "repos/$repo/actions/runs/$run_id/jobs?per_page=100" --paginate |
  jq -c --arg ev "$event" '
    def secs: if . == null then 0 else fromdateiso8601 end;
    def dur: (.completed_at | secs) - (.started_at | secs);
    .jobs[] | select((.conclusion == "success" or .conclusion == "failure") and .started_at != null) |
    ([.steps[]? | select(.name | test("^(Post |Complete job)|set ?up|checkout|cache|restore|install|npm ci|pnpm i|yarn|pip |uv sync"; "i")) | dur] | add // 0) as $setup |
    {run: .run_id, event: $ev, job: .name, conclusion,
     queue: ((.started_at | secs) - (.created_at | secs)),
     setup: $setup, work: (dur - $setup), total: dur}'
done > jobs.jsonl
echo "== Per job (medians, seconds; slowest first)"
jq -rs 'def median: sort | if length == 0 then 0 else .[length / 2 | floor] end;
  group_by(.job) | map({job: .[0].job, runs: length, queue: (map(.queue) | median),
    setup: (map(.setup) | median), work: (map(.work) | median), total: (map(.total) | median)})
  | sort_by(-.total) | (["job", "runs", "queue", "setup", "work", "total"] | @tsv),
    (.[] | [.job, .runs, .queue, .setup, .work, .total] | @tsv)' jobs.jsonl | column -t -s $'\t'
echo "== Per event: median run wall time (created -> last update) and the job most often slowest"
jq -rs --slurpfile runs runs.json '
  def median: sort | if length == 0 then 0 else .[length / 2 | floor] end;
  ($runs[0] | map({key: (.databaseId | tostring),
     value: ((.updatedAt | fromdateiso8601) - (.createdAt | fromdateiso8601))}) | from_entries) as $wall |
  group_by(.run) | map({event: .[0].event, wall: $wall[.[0].run | tostring],
     slowest: (max_by(.queue + .total) | .job)}) | group_by(.event) | .[] |
  "\(.[0].event): \(length) runs, median wall \(map(.wall) | median)s, slowest job: \(map(.slowest) | group_by(.) | max_by(length) | .[0])"' jobs.jsonl
```

- `queue` — job created to job started: waiting for a runner. It is part of what the agent waits for.
- `setup` — job setup, checkout, toolchain, cache restore and save, dependency install, and post steps.
- `work` — everything else: the lint, type-check, test, or build the job exists for.

The setup/work split matches step names, so it is a heuristic. Before trusting it, read the step list of one slow job: `gh api repos/OWNER/REPO/actions/runs/RUN_ID/jobs --jq '.jobs[] | .name, (.steps[] | "  \(.name)")'`.

### 2. Check the caches

```bash
repo=OWNER/REPO
workflow=ci.yml   # the workflow file the audit measured
# Which refs own the caches? No refs/heads/<default> entry means nothing seeds them.
gh cache list --repo "$repo" --limit 100 --json key,ref,sizeInBytes |
  jq -r 'group_by(.ref) | .[] | "\(.[0].ref)\t\(length) entries\t\((map(.sizeInBytes) | add) / 1e6 | floor) MB"'
gh api "repos/$repo/actions/cache/usage" --jq '"\(.active_caches_count) caches, \(.active_caches_size_in_bytes / 1e9) GB of the free 10 GB"'
# Restores and misses in the latest pull request runs (setup-* and actions/cache log lines).
for id in $(gh run list --repo "$repo" --workflow "$workflow" --event pull_request --status completed \
    --limit 10 --json databaseId --jq '.[].databaseId'); do
  log="$(gh run view --repo "$repo" "$id" --log 2>/dev/null)"
  echo "run $id: restored=$(grep -c 'Cache restored from key' <<<"$log") missed=$(grep -ci -E 'cache not found|cache is not found' <<<"$log")"
done
```

### 3. Read the numbers

| Signal | Likely cause | Free fix |
|---|---|---|
| `queue` above about 30 s | The plan's concurrent-job limit, hit by matrices, shards, or superseded runs | `concurrency` cancel; matrix off pull requests; fewer legs |
| `setup` larger than `work` | Cold caches, full-history checkout, slow install | Seed caches from the default branch; blobless checkout; pre-commit environment cache; measure a `node_modules` cache |
| No cache under `refs/heads/<default>` | No job runs on the default branch | A default-branch matrix or full run (Minimal on a public repository: `seed-cache`) |
| Pull request runs miss while the lockfile matches the default branch | Key mismatch: OS, tool version, or lockfile path | Identical setup step and version in the seeding job and the guard |
| One job is always the slowest | It is the critical path | Split by stage (public); move side work out; affected-only tests; shard (public only) |
| The same step in several jobs | Duplicated work | Run it once; hook checks belong to the guard |
| Matrix legs on `pull_request` | Version matrix on the hot path | Default branch only: per merge, or nightly on a busy private repository |
| No `timeout-minutes` | 360-minute default | About three times the typical duration |

Measure before cutting. Deleting tests is rarely the fix: in the report that prompted this section, the time was never in the tests, and in the example below the time *is* in the slowest job's work. The split says which case you are in. Never propose a paid runner, a larger runner, sharding on a private repository, a cache limit above 10 GB, or deleting or skipping tests.

### 4. Report

Report one row per finding, each tied to the audit output, then the proposed diff through the Safety Rails merge procedure. Example from a real run against the public `luongnv89/asm` repository (50 runs of `ci.yml`, 2026-11-01):

```text
== Per job (medians, seconds; slowest first)
job                   runs  queue  setup  work  total
e2e-node (26)         50    2      17     76    96
e2e-node (24)         50    2      14     76    90
unit-tests (22)       50    2      14     49    63
lint                  50    2      14     10    24
== Per event: median run wall time (created -> last update) and the job most often slowest
pull_request: 31 runs, median wall 131s, slowest job: e2e-node (26)
push: 19 runs, median wall 117s, slowest job: e2e-node (26)
caches: refs/heads/main 4 entries; last 5 pull request runs restored=12 missed=0
```

| Finding | Evidence | Free fix |
|---|---|---|
| The critical path is end-to-end test work, not setup | `e2e-node (26)`: 76 s of 96 s is work | Affected-only selection for e2e, or shard e2e across standard runners (public repository, so free) |
| Caches are already seeded and restored | 4 caches under `refs/heads/main`; 0 misses in 5 pull request runs | None needed |
| Version matrix runs on every pull request | 3 legs each of `unit-tests` and `e2e-node` per pull request run | Matrix on merges to the default branch; one version on pull requests. Queue is 2 s today, so this frees concurrent-job slots rather than time |

---

## Sources

Fetched 2026-11-01. Re-check them when a template changes; runner specs and prices change.

- GitHub-hosted runners reference (standard runner specs for public and private repositories; free and unlimited on public repositories): https://docs.github.com/en/actions/reference/runners/github-hosted-runners
- Actions runner pricing (each job rounded up to a whole minute; larger runners not free for public repositories): https://docs.github.com/en/billing/reference/actions-runner-pricing
- GitHub Actions billing (included usage; cache is a separate 10 GB allowance per repository, overage billed): https://docs.github.com/en/billing/concepts/product-billing/github-actions
- Actions limits (concurrent jobs per plan; 6-hour job limit): https://docs.github.com/en/actions/reference/limits
- Dependency caching reference (restore scope: current branch, base branch, default branch; pull request caches scoped to `refs/pull/.../merge`; 7-day eviction; 10 GB default): https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching
- `actions/cache` examples (caching `node_modules` not recommended: breaks across Node versions, incompatible with `npm ci`): https://github.com/actions/cache/blob/main/examples.md
- `actions/setup-node` README (`cache` does not cache `node_modules`) and `src/cache-restore.ts` (key `node-cache-<platform>-<arch>-<pm>-<hash>`, `cache-hit` output): https://github.com/actions/setup-node
- `actions/setup-python` `src/cache-distributions/pip-cache.ts` (key includes the Python version; `cache-hit` means an exact key match): https://github.com/actions/setup-python
- `actions/checkout` README (`filter`, `fetch-depth`, `persist-credentials`) and `src/git-source-provider.ts` (with `fetch-depth: 0` the filter is passed and the depth omitted): https://github.com/actions/checkout
- Control workflow concurrency (the `github.head_ref || github.run_id` fallback cancels on pull requests only; the templates key on the pull request number instead, which is unique across forks): https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency
- Workflow syntax (`timeout-minutes` default 360; `cancel-in-progress` accepts expressions): https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- Events that trigger workflows (`schedule`: default branch's latest commit, cron in UTC unless `timezone:` is set, delays at the top of the hour, disabled after 60 days without activity in public repositories; the `schedule` payload carries no repository): https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- Troubleshooting required status checks (a workflow skipped by path filtering stays Pending; a job skipped by a conditional reports Success): https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks
- Nx affected (`nx affected -t`, `--base`/`--head`, `nrwl/nx-set-shas`, lockfile changes affect every task by default): https://nx.dev/docs/features/ci-features/affected
- Turborepo run reference (`--affected`, `TURBO_SCM_BASE`/`TURBO_SCM_HEAD`, too-shallow checkouts mark every package changed, `--filter` git ranges): https://turborepo.dev/docs/reference/run
- `dorny/paths-filter` README (v4 is current and needs the Node 24 runtime; the Multi-language template still pins v3; pull requests use the REST API, so no checkout is needed; MIT): https://github.com/dorny/paths-filter
- `pre-commit/action` `action.yml` (cache key `pre-commit-3|${{ env.pythonLocation }}|<config hash>`): https://github.com/pre-commit/action
- pre-commit (CI cache of `~/.cache/pre-commit`; `default_stages` defaults to all stages; `PRE_COMMIT_FROM_REF`/`PRE_COMMIT_TO_REF`, also set by `--from-ref`/`--to-ref` in `pre_commit/commands/run.py`): https://pre-commit.com/
- `astral-sh/setup-uv` README (`enable-cache`, default `auto`): https://github.com/astral-sh/setup-uv
- Vitest sharding and test isolation: https://vitest.dev/guide/improving-performance
- The X post that prompted this section, treated as a requirements hint, not as evidence: @owengretzinger, "CI went from 40 min to 2 min", 2026-10-30
