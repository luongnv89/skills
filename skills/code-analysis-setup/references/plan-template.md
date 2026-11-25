# Plan, step reports and Final Report

## Plan (Step 3)

One plan covers every input. Item IDs are stable so the user can approve some: `S` sync, `C` config file, `H` hook entry, `J` CI job, `B` baseline, `I` install, `T` toplevel item for a subfolder input. Each item says whether it **creates** or **appends to** a file.

```text
◆ code-analysis-setup plan · 2 projects · hook budget 10 s per commit

P1 api  /work/api (toplevel) · Python 88% · pre-commit · 3 files per commit
  Sync (after approval):
    S1 git fetch origin && git pull --rebase origin main (stash a dirty tree first)
  Hook (append to .pre-commit-config.yaml; existing hooks unchanged):
    H1 bandit 1.8.x  -c pyproject.toml, staged *.py        ~0.6 s
    H2 gitleaks 8.x  hook id gitleaks (staged diff, --redact) ~0.3 s
       ruff: already configured (hook ruff) — skipped
  CI (create .github/workflows/code-analysis.yml):
    J1 semgrep scan --config p/python --metrics=off --error --baseline-commit <base sha>
       (fetch-depth: 0)                                          pull_request
       (registry rules: Semgrep Rules License, not OSI open source;
        not on push main: no base to compare with, see Baselines)
    J2 gitleaks git --redact (fetch-depth: 0)                   pull_request, push main
    J3 osv-scanner scan source -r . (v2 syntax)                 weekly + workflow_dispatch
  Baselines:
    B1 .gitleaksignore: tracked-file tree + history fingerprints, scanned after install (Step 4); you confirm each finding
    B2 bandit-baseline.json (-n 1, without B105-B107): written outside the repo after install,
       secret-scanned, copied in on your yes
  Installs (each its own item):
    I1 pre-commit install-hooks (builds hook environments in pre-commit's cache)
  Expected hook time: ~1.2 s per typical commit (budget 10 s)

P2 tools  /work/mono/tools (SUBFOLDER of /work/mono) · Shell 60%, Python 40% · no origin
  Sync: skipped (no origin)
  Config:
    C1 tools/.shellcheckrc (create)
  Toplevel (needs your explicit yes, affects all of /work/mono):
    T1 /work/mono/.pre-commit-config.yaml (create): shellcheck, ruff on tools/**
  Expected hook time: ~0.8 s per typical commit (budget 10 s)

Left out:
  - CodeQL: P1 is a private repo; needs paid GitHub Advanced Security
  - Bearer: no personal data handled (Elastic License 2.0, not open source; off by default)
  - semgrep in the hook: slow whole-repo scan, CI only
  - P2 hook inside tools/: hooks live at the repo toplevel, so only through T1

Real secrets to rotate: scanned in Step 4, after approval (nothing is scanned before it)

Verification (after install):
  warm-up: pre-commit install-hooks (reported as setup time)
  timing:  pre-commit run --files app/main.py app/db.py app/models.py
           snapshot git write-tree + git status --porcelain before and after
           gitleaks hook: not measured (staged-diff scanner)
  acceptance: gitleaks CI command and the hook-side tree scan (tracked files only, index export) re-run, each must exit 0

Nothing has been written. Reply: approve all · approve <IDs> · change … · stop
```

Rules for the plan:

- Every tool shows its licence when it is not plainly OSI open source.
- An item that writes or appends to a file in the pre-sync dirty list is marked `dirty (uncommitted changes)`. `approve all` skips it; only `approve <ID>` covers it. A skipped `dirty` item is reported in the Step 4 report and the Final Report.
- Every skipped tool says what already covers it (hook id, workflow, or `covered by security-setup (security/security-tools.json)`).
- The sync line per repo is exact: the commands, or `skipped (no origin)`, or `skipped (not a git repo)`.
- A subfolder input lists hook items under *Toplevel* as `T` items. A folder outside git says `hooks: left out (not a git repo)` and `history: left out (not a git repo)`.
- Expected hook time is an estimate from the cost class and the files per commit, and says so. Over budget: move tools to CI until it fits, and say which.
- Baselines in the plan name the mechanism only. Steps 1 to 3 run no scanner, so finding counts and the secrets to rotate come from Step 4, after approval.
- Interactive run: the approval prompt is the last line. Then stop and wait. Unattended run (no user to answer, such as a subagent or eval runner): print the plan, then the PARTIAL Final Report (*No user present* below) instead of waiting.

## Step reports

After each step, print:

```text
◆ Step 1 — Analyse (2 projects)
  √ P1 api: toplevel, pre-commit, Python 88%
  √ P2 tools: subfolder of /work/mono (flagged)
  × P3 /work/notes: not a git repo (hooks and history left out)
  Result: PARTIAL
```

Per-step checks:

| Step | Checks |
|---|---|
| 1 Analyse | toplevel resolved per input; dirty list saved; hook manager and CI found; security-setup footprint checked |
| 2 Plan | every category decided per project; duplicates skipped with reason; hook estimate within budget |
| 3 Gate | plan printed; reply recorded (approve all / some / stop / no user) |
| 4 Install | sync result per repo; each approved file written or appended; baselines hold no secret values |
| 5 Verify | warm-up time; sample size; per-commit time vs budget; snapshot unchanged; acceptance commands exit 0 |

## Final Report

Four lines, every run, stops included: `Result:`, `Evidence:`, `Uncertainty:`, `Decision:`.

Rejected plan:

```text
Result: BLOCKED. Plan rejected by the user; nothing written.
Evidence: HEAD 3f2a9c1 and git stash list unchanged; no fetch, pull, install or hook run.
Uncertainty: none.
Decision: Nothing to undo. Re-run with a changed scope when ready.
```

No user present:

```text
Result: PARTIAL. Plan printed for 1 project; no user to approve, nothing written.
Evidence: plan above (H1-H2, J1-J3, B1-B2); git status unchanged; no scanner run, so baseline counts are unknown.
Uncertainty: hook time is an estimate (~1.2 s), not measured.
Decision: A user must approve the plan before anything is installed.
```

Timing skipped:

```text
Evidence: ... timing: skipped (no clean tracked files) ...
```

Redaction: any secret match in Evidence, a baseline or timing output appears as `REDACTED`, never the value.
