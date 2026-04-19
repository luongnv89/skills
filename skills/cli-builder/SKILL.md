---
name: cli-builder
description: "Build a production-quality CLI tool for any module or application. Auto-detects language, recommends CLI libraries, and follows a 5-step approval-gated workflow: Analyze, Design, Plan, Execute, Summarize."
effort: high
license: MIT
metadata:
  version: 1.0.2
  creator: Luong NGUYEN <luongnv89@gmail.com>
---

# CLI Builder

Build production-quality CLI tools for any module or application, in any language.

Reference files (read on demand, not upfront):
- `references/cli-libraries.md` — read during Step 2 (Design) to recommend libraries and during Step 4 (Execute) for starter scaffolds
- `references/testing-patterns.md` — read during Step 4 (Execute) when writing tests

## Repo Sync Before Edits (mandatory)

Before creating/updating/deleting files in an existing repository, sync the current branch with remote:

```bash
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin
git pull --rebase origin "$branch"
```

If the working tree is not clean, stash first, sync, then restore:

```bash
git stash push -u -m "pre-sync"
branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin && git pull --rebase origin "$branch"
git stash pop
```

If `origin` is missing, pull is unavailable, or rebase/stash conflicts occur, stop and ask the user before continuing.

## Branch-First Safety Rule

Before changing any file, check the current branch. Only create a new branch if on `main` or `master` — otherwise continue on the existing branch (the user likely set it up already or is resuming work):

```bash
current_branch="$(git rev-parse --abbrev-ref HEAD)"
if [ "$current_branch" = "main" ] || [ "$current_branch" = "master" ]; then
  slug="$(echo "${CLI_NAME:-cli}" | tr '[:upper:] ' '[:lower:]-' | tr -cd 'a-z0-9-')"
  ts="$(date +%Y%m%d-%H%M%S)"
  git checkout -b "feat/cli-${slug}-${ts}"
fi
```

## Mandatory 5-Step Workflow (approval-gated)

### Step 1: Analyze

Understand the project before proposing anything.

**Auto-detect language** by checking for manifest files:
- `package.json` / `tsconfig.json` -> JavaScript/TypeScript
- `pyproject.toml` / `setup.py` / `setup.cfg` / `requirements.txt` -> Python
- `go.mod` -> Go
- `Cargo.toml` -> Rust
- `pom.xml` / `build.gradle` / `build.gradle.kts` -> Java/Kotlin
- `Gemfile` / `*.gemspec` -> Ruby

**Identify existing CLI/entry points**: check for `bin` fields, `__main__.py`, `main.go`, `fn main()`, existing arg parsing code, or `scripts` in package.json.

**Understand module structure**: public API, core functions, data types, dependencies.

**Ask clarifying questions** (only what cannot be inferred):
- Primary use case (automation, developer tool, data processing, admin)
- Target audience (developers, ops, end users)
- Single command or multi-command (subcommand tree)
- Output formats needed (text, JSON, table, CSV)
- Distribution method (pip/npm/go install, standalone binary, source)

Present findings and wait for approval before proceeding.

---

### Step 2: Design

Present a structured CLI design document:

- **Tool name** and binary/entry point name
- **Command tree** (visual hierarchy for multi-command tools)
- **Arguments and options per command** (name, type, required/optional, default, help text)
- **Global options** (verbose, quiet, output format, config file, no-color)
- **I/O behavior** (stdin support, stdout/stderr separation, piping)
- **Config strategy** (CLI args > env vars > config file > defaults)
- **Example invocations** (at least 3 realistic examples showing common use cases)

Iterate until user approves:
- Ask for feedback
- Adjust design
- Repeat until explicit approval

**No implementation before design approval.**

---

### Step 3: Plan

Break implementation into three phases, each with granular tasks.

**Phase 1 — Foundation** (get a working CLI skeleton):
- Entry point and arg parsing setup
- One core command (the most important one)
- Help text and version flag
- Basic tests (help output, version, one command)

**Phase 2 — Complete** (full feature set):
- All remaining commands
- Input validation and error handling
- Output formatting (text, JSON, table as designed)
- Comprehensive tests

**Phase 3 — Polish** (optional, confirm with user):
- Config file support
- Environment variable overrides
- Shell completions (bash, zsh, fish)
- Distribution/packaging setup (setup.py, package.json bin, goreleaser, etc.)

Each task includes:
- **Goal**: one sentence
- **Files**: create or modify
- **Expected behavior**: what the user can do after this task
- **Test**: how to verify
- **Effort**: S / M / L

Iterate the plan with user until approved.

**No execution before plan approval.**

---

### Step 4: Execute

Implement the approved plan task by task:

1. Implement one task
2. Run tests after each task
3. Demo between phases (show example commands and output)
4. Commit per phase with descriptive message

If tests fail, fix before moving to the next task. If a design issue is discovered during implementation, pause and discuss with user.

---

### Step 5: Summarize

Deliver a final summary:

- **Design summary**: tool name, command tree, key options
- **Implementation summary**: files created/modified, libraries used, patterns applied
- **Test results**: pass/fail counts, coverage if available
- **Usage quick-start**: install command, 3-5 example invocations
- **Next steps**: suggested improvements, missing features, distribution TODO

## Expected Output

After running this skill on a Python module called `mylib`, the final deliverable looks like:

```
feat/cli-mylib-20260419-143200 branch created

Files created:
  cli/main.py          — entry point with argparse/click/typer wiring
  cli/commands/run.py  — "mylib run" subcommand
  cli/commands/info.py — "mylib info" subcommand
  tests/test_cli.py    — CLI smoke tests (help, version, run)
  pyproject.toml       — updated with [project.scripts] entry point

Usage quick-start:
  pip install -e .
  mylib --help
  mylib run --input data.csv --output results.json
  mylib info --format json
```

Step Completion Report (Steps 4-5):
```
◆ Execute + Summarize (step 4-5 of 5 — mylib CLI)
··································································
  Implementation:        √ pass (3 commands, 2 files)
  Test coverage:         √ pass (8/8 tests passing)
  Phase demos completed: √ pass (help, version, run verified)
  Summary delivered:     √ pass
  Criteria:              √ 4/4 met
  ____________________________
  Result:                PASS
```

## Edge Cases

- **No clear module to wrap**: Ask the user what functions/features the CLI should expose before proceeding with analysis.
- **Multiple languages detected**: Present a choice; recommend the language with the most existing CLI-related code.
- **Existing CLI found**: Offer to extend or refactor rather than rebuild; audit what already exists first.
- **Monorepo with many packages**: Ask which package/service should get the CLI; scope the analysis to that subtree.
- **No test framework present**: Add a minimal test setup (pytest, jest, go test) as part of Phase 1 foundation tasks.
- **Binary output required (standalone .exe / compiled)**: Note distribution method during Design phase and add build step (PyInstaller, pkg, goreleaser) to Phase 3 polish.
- **User approves design but rejects implementation**: Return to Design phase; do not silently proceed with the rejected approach.

## Acceptance Criteria

- [ ] Language is auto-detected from manifest files before asking clarifying questions
- [ ] CLI design document is presented and explicitly approved before any implementation begins
- [ ] Implementation plan is presented and explicitly approved before execution starts
- [ ] `--help` works at every command level and `--version` is implemented
- [ ] Exit codes follow POSIX convention (0 = success, 1 = runtime error, 2 = usage error)
- [ ] Error messages go to stderr; clean output goes to stdout (pipeable)
- [ ] `NO_COLOR` env var or `--no-color` flag is respected
- [ ] Tests are written and pass before moving to the next phase
- [ ] Final summary includes install command and at least 3 usage examples

## Step Completion Reports

After completing each major step, output a status report in this format:

```
◆ [Step Name] ([step N of M] — [context])
··································································
  [Check 1]:          √ pass
  [Check 2]:          √ pass (note if relevant)
  [Check 3]:          × fail — [reason]
  [Check 4]:          √ pass
  [Criteria]:         √ N/M met
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

Adapt the check names to match what the step actually validates. Use `√` for pass, `×` for fail, and `—` to add brief context. The "Criteria" line summarizes how many acceptance criteria were met. The "Result" line gives the overall verdict.

### Skill-specific checks per phase

**Phase: Analyze (Step 1)** — checks: `Project analysis`, `Language detected`, `Entry points identified`, `Clarifying questions asked`

**Phase: Design (Step 2)** — checks: `Design approval`, `Command tree defined`, `I/O behavior specified`, `Example invocations provided`

**Phase: Plan (Step 3)** — checks: `Plan approval`, `Phases broken down`, `Tasks have goals and tests`, `Effort estimated`

**Phase: Execute + Summarize (Steps 4–5)** — checks: `Implementation`, `Test coverage`, `Phase demos completed`, `Summary delivered`

## Error Handling

| Situation | Action |
|-----------|--------|
| No clear module to wrap | Ask user what functionality the CLI should expose |
| Multiple languages detected | Ask user which language to use, recommend the one with more CLI code |
| Existing CLI found | Offer to extend/refactor rather than rebuild; audit existing CLI first |
| Unknown framework requested | Research the framework, ask user for docs link if needed |
| Tests fail after implementation | Fix before proceeding; never skip broken tests |

## Quality Guardrails

Every CLI built with this skill must include:

- **Help text**: every command and option has a description (`--help` works at every level)
- **Error messages**: written to stderr, include what went wrong and how to fix it
- **Exit codes**: 0 = success, 1 = runtime error, 2 = usage error (follow POSIX convention)
- **POSIX conventions**: `--long-flag`, `-s` short flag, `--` to end options
- **Pipeable I/O**: support stdin when it makes sense, clean stdout for piping
- **No-color support**: respect `NO_COLOR` env var or `--no-color` flag
- **Version flag**: `--version` prints version and exits
