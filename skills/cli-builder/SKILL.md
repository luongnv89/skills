---
name: cli-builder
description: |
  Guide users through building a CLI tool for any module or application. Use when users ask to "build a CLI", "create a command-line tool", "add CLI interface", "make this scriptable", "wrap this in a CLI", "add a terminal interface", or mention specific CLI frameworks like argparse, click, typer, commander, yargs, cobra, clap, picocli, or thor. Follows a strict 5-step approval-gated workflow: Analyze -> Design -> Plan -> Execute -> Summarize. Language-agnostic — auto-detects the project's language and recommends appropriate CLI libraries.
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

Before changing any file, create a dedicated branch (repo sync above must have run first):

```bash
slug="$(echo "${CLI_NAME:-cli}" | tr '[:upper:] ' '[:lower:]-' | tr -cd 'a-z0-9-')"
ts="$(date +%Y%m%d-%H%M%S)"
git checkout -b "feat/cli-${slug}-${ts}"
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
