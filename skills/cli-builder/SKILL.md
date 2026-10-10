---
name: cli-builder
description: "Build production-quality CLIs with language detection and a five-step approval-gated workflow. Use when wrapping an existing module or app. Don't use for GUI/TUI apps, web APIs, or one-off shell scripts."
license: MIT
effort: high
metadata:
  version: 1.3.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# CLI Builder

Build production-quality CLI tools for any module or application, in any language.

Reference files (read each one on demand, not upfront, to keep the agent's context budget small):
- `references/cli-libraries.md` — read during Step 2 (Design) to recommend libraries and during Step 4 (Execute) for starter scaffolds
- `references/btop-style.md` — read during Step 2 (Design) to write the Visual style section and during Step 4 (Execute) to build the style module and its tests
- `references/testing-patterns.md` — read during Step 4 (Execute) when writing tests
- `references/final-report.md` — read during Step 5 (Summarize) to write the final report

## Repo Sync Before Edits (mandatory)

Run this section once, before Step 1, so the analysis reads the current code. If `git rev-parse --git-dir` fails, the directory is not a git repository: skip this section, the Branch-First Safety Rule, and the Step 4 commits, and list `no git repository: no branch or commits` under `Uncertainty:` in the final report.

In a git repository, sync the current branch with remote:

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

Run this rule at the start of Step 4, before the first file write, with `CLI_NAME` set to the tool name approved in Step 2. Only create a new branch if on `main` or `master` — otherwise continue on the existing branch (the user likely set it up already or is resuming work):

```bash
current_branch="$(git rev-parse --abbrev-ref HEAD)"
if [ "$current_branch" = "main" ] || [ "$current_branch" = "master" ]; then
  slug="$(echo "${CLI_NAME:-cli}" | tr '[:upper:] ' '[:lower:]-' | tr -cd 'a-z0-9-')"
  ts="$(date +%Y%m%d-%H%M%S)"
  git checkout -b "feat/cli-${slug}-${ts}"
fi
```

## Mandatory 5-Step Workflow (approval-gated)

**Explicit approval** is a user reply that accepts the presented item as it stands, such as "approved" or "looks good, go ahead". A question, a change request, or no reply is not approval. Steps 1-3 write no files.

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

**Record the module structure**: list the public functions or classes the CLI will expose, their inputs and outputs, the core data types, and runtime dependencies.

**Ask clarifying questions** (only what cannot be inferred):
- Primary use case (automation, developer tool, data processing, admin)
- Target audience (developers, ops, end users)
- Single command or multi-command (subcommand tree)
- Output formats needed (text, JSON, table, CSV)
- Distribution method (pip/npm/go install, standalone binary, source)

Present the findings: detected language, entry points, the list of exposed functions, and the open questions. Wait for explicit approval before Step 2.

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
- **Visual style** (in every design) — the btop-inspired look from `references/btop-style.md`: components per command, theme roles, fallbacks, the styling library or zero-dependency module, and a mockup of one command's styled output. Use another style only when the user explicitly declines this one.

Approval loop:
1. Present the design document.
2. Ask for feedback.
3. If the reply is not explicit approval, revise the design and return to 1.

**No implementation before design approval.** If the user ends the run without approving the design, stop; the final status is `BLOCKED`.

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
- Output formatting (text, JSON, table as designed) through one style module that follows the approved Visual style
- Comprehensive tests

**Phase 3 — Polish** (optional; include it only when the user confirms it):
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

Use the same approval loop as Step 2 for the plan.

**No execution before plan approval.** If the user ends the run without approving the plan, stop; the final status is `BLOCKED`.

---

### Step 4: Execute

Before the first file write, apply the Branch-First Safety Rule. Then, for each task in the approved plan:

1. Implement the task.
2. Run the project's test command, taken from the manifest (for example `pytest`, `npm test`, `go test ./...`, `cargo test`).
3. If a test fails, fix the code and re-run the test command. After 3 failed fix attempts on the same task, stop Step 4, show the failing output, and ask the user how to proceed. Do not start the next task while a test fails.
4. If the test command cannot run (missing toolchain or test runner), tell the user. Continue only after explicit approval, and record that task's tests as `not run`.

At the end of each phase:

5. Run the demo (`--help` plus at least one approved example invocation) and show the output. From Phase 2 on, also run one example with `FORCE_COLOR=1` (`references/btop-style.md` → Verify). A demo that exits non-zero is a failing test (item 3).
6. In a git repository, stage only the files this phase created or modified, then commit them with a descriptive message.

If a task needs a change to the approved design (a command, option, or output format differs), stop Step 4. Present the proposed change and wait for explicit approval before you continue.

---

### Step 5: Summarize

Print the final report once, after the last Step Completion Report, as plain text in the chat. Do not write a report file unless the user asks for one. Read `references/final-report.md` for each part's contents, the status rules, and two examples. The four parts, in this order:

1. `Result:` — the status first (`COMPLETE`, `PARTIAL — <reason>`, or `BLOCKED — <reason>`), then the tool name.
2. `Evidence:` — only checks that ran: files, test counts, demo exit codes.
3. `Uncertainty:` — untested behavior and assumptions, labeled apart from verified facts.
4. `Decision:` — the approval needed, or `No approval needed.`, then each remaining user action.

After the four parts, print the usage quick-start (install command and 3-5 example invocations) and the next steps (suggested improvements, missing features, distribution TODO).

**Status rules** — apply the first rule that matches:

1. `BLOCKED` — the run stopped before the first file write, for example because the design or plan was not approved, there was no module to wrap and the user gave no answer, or Repo Sync hit a conflict or a missing `origin` the user did not approve working around.
2. `PARTIAL` — at least one file was written, and then any of these happened: a test or demo still fails, a test command could not run, the user stopped Step 4 early, an approved task is not done, or a design change awaits approval.
3. `COMPLETE` — every task in the approved plan is done, and every test command and demo ran and passed. A Phase 3 the user declined does not make the run partial.

## Expected Output

After running this skill on a Python module called `mylib`, the final report looks like this (full example: `references/final-report.md`):

```
Result: COMPLETE — mylib CLI (Python, click) with subcommands run and info
Evidence:
  Branch: feat/cli-mylib-20260419-143200
  Created: cli/main.py, cli/commands/run.py, cli/commands/info.py, tests/test_cli.py
  Modified: pyproject.toml ([project.scripts] entry point)
  pytest: 8 passed, 0 failed
  Visual style: btop, rich
  Demo: mylib --help, mylib --version, mylib info, env -u NO_COLOR FORCE_COLOR=1 mylib info (all exit 0)
Uncertainty:
  Tested on macOS only. Styled output not viewed in a real terminal; light-background terminal not tried.
  Shell completions not built (Phase 3 declined).
Decision: No approval needed.
  Remaining action: review the branch and push it.

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
  Implementation:         √ pass (2 subcommands, 4 files created)
  Test coverage:          √ pass (8/8 tests passing)
  Phase demos completed:  √ pass (help, version, run verified)
  Final report delivered: √ pass
  Criteria:               √ 4/4 met
  ____________________________
  Result:                 PASS
```

## Edge Cases

- **No clear module to wrap**: Ask the user what functions/features the CLI should expose before proceeding with analysis.
- **Multiple languages detected**: Present a choice; recommend the language with the most existing CLI-related code.
- **Existing CLI found**: Offer to extend or refactor rather than rebuild; audit what already exists first.
- **Existing CLI has its own visual style**: Present the btop style in the design anyway, list where it differs from the current output, and let the user choose at design approval.
- **Live, refreshing btop-like view requested**: In Step 1, say a full-screen live view is a TUI, which this skill does not build, and offer append-only output (`references/btop-style.md`).
- **Monorepo with many packages**: Ask which package/service should get the CLI; scope the analysis to that subtree.
- **No test framework present**: Add a minimal test setup (pytest, jest, go test) as part of Phase 1 foundation tasks.
- **Binary output required (standalone .exe / compiled)**: Note distribution method during Design phase and add build step (PyInstaller, pkg, goreleaser) to Phase 3 polish.
- **User approves design but rejects implementation**: Return to Design phase; do not silently proceed with the rejected approach.

## Acceptance Criteria

- [ ] Language is auto-detected from manifest files before asking clarifying questions
- [ ] CLI design document is presented and explicitly approved before any implementation begins
- [ ] Implementation plan is presented and explicitly approved before execution starts
- [ ] `--help` works at every command level and `--version` is implemented
- [ ] Exit codes follow the canonical table in `references/testing-patterns.md`
- [ ] Error messages go to stderr; clean output goes to stdout (pipeable)
- [ ] `NO_COLOR` env var or `--no-color` flag is respected
- [ ] Terminal output follows the approved Visual style, and `--format json`, piped, and `NO_COLOR` output contain no ESC (`0x1b`) byte
- [ ] Tests are written and pass before moving to the next phase
- [ ] Final report includes install command and at least 3 usage examples
- [ ] The final report opens with `Result:` and a status chosen by the Step 5 status rules, then `Evidence:`, `Uncertainty:`, and `Decision:`
- [ ] A reader can find the result, separate verified checks from assumptions, trace each claim to a file or command, and see the next decision (reader checks in `references/final-report.md`). Human understanding stays unconfirmed until a user answers those checks

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

**Phase: Design (Step 2)** — checks: `Design approval`, `Command tree defined`, `I/O behavior specified`, `Example invocations provided`, `Visual style defined`

**Phase: Plan (Step 3)** — checks: `Plan approval`, `Phases broken down`, `Tasks have goals and tests`, `Effort estimated`

**Phase: Execute + Summarize (Steps 4–5)** — checks: `Implementation`, `Test coverage`, `Phase demos completed`, `Final report delivered`

## Error Handling

| Situation | Action |
|-----------|--------|
| No clear module to wrap | Ask user what functionality the CLI should expose |
| Multiple languages detected | Ask user which language to use, recommend the one with more CLI code |
| Existing CLI found | Offer to extend/refactor rather than rebuild; audit existing CLI first |
| Unknown framework requested | Read the framework's official documentation; if none is reachable, ask the user for a docs link |
| Tests fail after implementation | Fix and re-run; never skip broken tests. After 3 failed attempts on one task, stop and ask the user (Step 4) |
| Test command cannot run | Tell the user; continue only after explicit approval, and record the tests as `not run` (status `PARTIAL`) |
| Not a git repository | Skip Repo Sync, the branch rule, and commits; list it under `Uncertainty:` |

## Quality Guardrails

Every CLI built with this skill must include:

- **Help text**: every command and option has a description (`--help` works at every level)
- **Error messages**: written to stderr, include what went wrong and how to fix it
- **Exit codes**: follow the canonical table in `references/testing-patterns.md` (0 = success, non-zero = failure)
- **POSIX conventions**: `--long-flag`, `-s` short flag, `--` to end options
- **Pipeable I/O**: support stdin when it makes sense, clean stdout for piping
- **No-color support**: respect `NO_COLOR` env var or `--no-color` flag
- **Version flag**: `--version` prints version and exits
