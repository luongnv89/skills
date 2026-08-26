# Preflight — dependency detection and failure blocks

Everything Phase 0 needs: how to probe `gh` for real readiness, how to detect each dependency, and the exact block to print when one is
missing. Read this when a check fails — or when you are unsure how to check one.

**One report, not one stop per failure.** Run every check in all five groups — **env**, **gh**,
**skill**, **bundled**, **input** — collect the failures, then print every failure block together and
stop. A user with no `gh`, no `asm`, and no `issue-creator` should learn all three
in one pass instead of three re-runs.

## gh readiness

`command -v gh` proves a binary exists. It does not prove `gh` can file 50 issues into *this* repo as
the *intended* user. These six probes do. Every command below was verified against `gh` 2.87.3.

### The probes — G1–G6

```bash
gh --version                                              # G1 — recorded in the report
gh label list --limit 1 --json name >/dev/null            # G1 — capability probe for --json
gh auth status                                            # G2 — active account
                                                          # G3 — Token scopes line
gh repo view --json nameWithOwner,hasIssuesEnabled,isArchived,viewerPermission,isPrivate
                                                          # G4 — the repo's own verdict
git remote | wc -l                                        # G5 — >1 means the target is ambiguous
gh repo set-default --view                                # G5 — only when the above is >1
gh api rate_limit --jq '.resources.core.remaining'        # G6 — budget headroom
```

G1 is a **capability probe, not a version floor**: rather than asserting a minimum `gh` version,
run the `--json` form this skill depends on and read the error. `unknown flag: --json` means the
installed `gh` is too old; the fix is an upgrade regardless of which version introduced the flag.

G5 counts `git remote`, not `git remote -v` — the verbose form prints two lines per remote, so
a single-remote repo looks like two.

### Decision table

| Probe | Observation | Verdict |
|---|---|---|
| G1 | `gh` absent | **stop** — *Missing tool* block |
| G1 | `--json` rejected | **stop** — *gh too old* block |
| G2 | not logged in | **stop** — *Not authenticated* block |
| G2 | exactly one account | pass — record it |
| G2 | **more than one account** | **confirm** — name the `Active account: true` one and ask before filing |
| G3 | `Token scopes:` includes `repo` | pass |
| G3 | no `repo` scope | **stop** — *Insufficient token scope* block |
| G4 | command errors / repo not found | **stop** — *No GitHub remote* block |
| G4 | `hasIssuesEnabled: false` | **stop** — nothing to file into |
| G4 | `isArchived: true` | **stop** — the repo is read-only |
| G4 | `viewerPermission` `ADMIN`/`MAINTAIN`/`WRITE` | pass |
| G4 | `viewerPermission` `TRIAGE` | **degrade** — file and label with *existing* labels; label creation off |
| G4 | `viewerPermission` `READ`/`NONE` | **stop** — no labels, no epic edits; offer `--dry-run` |
| G5 | one remote | pass |
| G5 | >1 remote, default set | pass — record which repo is the target |
| G5 | >1 remote, no default | **stop** — *Ambiguous target repo* block |
| G6 | `remaining` ≥ `4 × tasks + 20` | pass |
| G6 | `remaining` < that | **stop** — *API budget* block, with the reset time |
| G6 | more than 80 tasks | **warn** — secondary content-creation limits; recommend `--phase` runs |

A **degrade** verdict continues the run and is repeated in the final report — a silently reduced run
that looks like a clean one is the failure this rule exists to prevent. A **confirm** verdict pauses
for the user and nothing else.

The `4 × tasks + 20` estimate: per task, one create, one label edit, one verification read, and a
share of the dependency pass; plus the epic, the label diff, and the dashboard write. The primary
limit is 5,000/hour, so this rarely binds. What does bind on large plans is GitHub's **secondary**
content-creation limit, which no endpoint reports — hence the warn at 80.

### gh failure blocks

#### gh too old

```text
✗ Your gh does not support `--json` ({version})

  This skill reads the tracker as structured JSON — parsed text output is not a
  supported fallback.

  To fix:  brew upgrade gh   ·   sudo apt update && sudo apt install --only-upgrade gh
  Check:   gh --version && gh label list --limit 1 --json name
```

#### Insufficient token scope

```text
✗ Your gh token is missing the `repo` scope

  Scopes found: {scopes}

  Creating issues and labels needs `repo`.

  To fix:  gh auth refresh -h github.com -s repo
  Check:   gh auth status
```

#### Multiple accounts (confirm, not a failure)

```text
⚠ Two gh accounts are logged in to github.com

  Active:  {active_account}  ← issues will be authored by this account
  Other:   {other_account}

  Switch with:  gh auth switch --user {other_account}

  File {n} issues as {active_account}? [Y/n]
```

#### Issues disabled / repo archived

```text
✗ {nameWithOwner} cannot accept issues ({reason})

  reason = "issues are disabled" → enable them: Settings → General → Features → Issues
  reason = "the repository is archived" → unarchive it: Settings → General → Danger Zone

  Nothing was created.
```

#### Insufficient repository permission

```text
✗ Your permission on {nameWithOwner} is {viewerPermission}

  Filing this plan needs WRITE (or TRIAGE, with label creation disabled): the run
  applies labels to every issue and rewrites the epic body.

  To fix:  ask for write access, or fork the repo and run there.

  What still works:  /plan-to-issues --dry-run
```

#### Ambiguous target repo

```text
✗ This repo has {n} remotes and no default is set

  gh would prompt for a target mid-run, which stalls a batch of {n_tasks} issues.

  To fix:  gh repo set-default
  Check:   gh repo set-default --view
```

#### API budget

```text
✗ Not enough GitHub API budget for this run

  Needed:    ~{estimate} requests ({n_tasks} tasks)
  Remaining: {remaining} of {limit}, resets at {reset_time}

  To fix:  wait for the reset, or file one phase at a time:
           /plan-to-issues --phase P0
```

## Detecting an installed skill

A skill is available when its `SKILL.md` resolves under any skill root, or when it appears in this
session's available-skills listing. Check the listing first — it is what actually decides whether the
Skill tool can invoke it — then fall back to the filesystem:

```bash
ls ~/.claude/skills/issue-creator/SKILL.md 2>/dev/null \
  || ls .claude/skills/issue-creator/SKILL.md 2>/dev/null \
  || ls ~/.claude/plugins/*/skills/issue-creator/SKILL.md 2>/dev/null \
  || echo "MISSING: issue-creator"
```

Present in the listing but absent from disk (or the reverse) is still **installed** — one of the two
roots simply is not the one in use. Only both failing counts as missing.

`asm list` also enumerates what `asm` manages, and is the friendliest verification command to hand
back to the user after they install something.

## Skill dependency table

| Skill | Required | Source repo | Install |
|---|---|---|---|
| `issue-creator` | **yes** | `luongnv89/idd` | `asm install https://github.com/luongnv89/idd --skill issue-creator` |
| `codebase-modernizer` | only when no plan exists yet | `luongnv89/skills` | `asm install github:luongnv89/skills:skills/codebase-modernizer` |

## Failure blocks

Print these verbatim, substituting the bracketed values. Every skill block leads with the `asm`
install line **and** the line that installs `asm` itself — assume the user has neither.

### Missing required skill — `issue-creator`

```text
✗ Missing required skill: issue-creator

  /plan-to-issues delegates every issue body to /issue-creator. Filing issues without it
  would produce a backlog that /issue-triage and /issue-resolver cannot read.

  1. Install asm (the skill manager), if you don't have it:

       npm install -g agent-skill-manager

  2. Install the skill:

       asm install https://github.com/luongnv89/idd --skill issue-creator

     No asm, one-off:  npx skills add https://github.com/luongnv89/idd --skill issue-creator

  3. Verify:  asm list | grep issue-creator

  Then restart the agent session and re-run /plan-to-issues.
```

### No plan file found

```text
✗ No plan file found

  Looked for: MODERNIZATION_PLAN.md · docs/MODERNIZATION_PLAN.md · *PLAN*.md · tasks.md · tasks/

  If you have a plan elsewhere:

       /plan-to-issues path/to/plan.md

  If you have no plan yet, generate one with /codebase-modernizer. Not installed?

       npm install -g agent-skill-manager                                    # asm itself
       asm install github:luongnv89/skills:skills/codebase-modernizer        # the skill

     No asm, one-off:  npx skills add https://github.com/luongnv89/skills --skill codebase-modernizer
```

Name the second half only when `codebase-modernizer` is also missing. When it is installed, the
message is the first half plus `run /codebase-modernizer first`.

### Missing bundled file

```text
✗ Missing bundled dependency: {missing_file}

  To fix:  asm install github:luongnv89/skills:skills/plan-to-issues
           (or reinstall the full distribution)

  Then restart the agent session and re-run /plan-to-issues.
```

Check all of these relative to this SKILL.md's directory before running anything:
`references/preflight.md`, `references/plan-parsing.md`, `references/labels.md`,
`references/issue-creator-bridge.md`, `references/epic-dashboard.md`, `references/sync-mode.md`,
`references/edge-cases.md`, `agents/plan-parser.md`, `scripts/render_dashboard.py`.

This list is the authoritative guard — it must name **every** bundled file the skill loads at
runtime, including the ones only one mode reaches (`sync-mode.md` for `sync`, `edge-cases.md` for
the degraded paths). A truncated install that passes preflight and then fails mid-run is the exact
failure this gate exists to prevent.

### Missing tool

```text
✗ {tool} is not installed

  To fix:  {fix}
```

| Tool | `{fix}` |
|---|---|
| `gh` | `brew install gh` · `sudo apt install gh` · https://cli.github.com |
| `python3` | `brew install python3` · `sudo apt install python3` |

### Not authenticated

```text
✗ GitHub CLI is not authenticated

  To fix:  gh auth login
  Check:   gh auth status
```

### Not a git repository / no GitHub remote

```text
✗ No GitHub remote found

  To fix:  git remote add origin git@github.com:<owner>/<repo>.git
  Check:   git remote -v

  gh is the only tracker driver this skill supports — a GitLab or Bitbucket
  remote is out of scope.
```

## Preflight report

On success, one line per check, then continue:

```text
◆ Preflight (phase 0 of 7 — dependencies)
··································································
  Tools present:      √ pass (git, gh 2.87.3, python3)
  gh ready:           √ pass (luongnv89 · scopes include repo · --json ok)
  Repo writable:      √ pass (luongnv89/skills · issues on · ADMIN)
  API budget:         √ pass (4905 remaining, ~220 needed)
  Skills installed:   √ pass (issue-creator 0.8.0)
  Bundled files:      √ pass (9/9)
  Plan located:       √ pass (MODERNIZATION_PLAN.md — 50 tasks, 6 phases)
  ____________________________
  Result:             PASS
```

A degraded check shows `⚠` with what was reduced (`⚠ TRIAGE — label creation disabled`) and is
repeated in the final report. On failure the same report shows `×` rows, the failure blocks follow, and the run stops. Never print
`Result: PASS` with a `×` row above it, and never continue to Phase 1 on `PARTIAL`.
