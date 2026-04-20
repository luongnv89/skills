---
name: skill-creator
description: "Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, update or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy. Don't use for running skills themselves, generating prose/blog content, or scaffolding unrelated Python projects — this is only for authoring and evaluating skill-packaged capabilities."
effort: max
license: MIT
metadata:
  version: 1.3.0
  creator: Luong NGUYEN <luongnv89@gmail.com>
---

# Skill Creator

A skill for creating new skills and iteratively improving them.

At a high level, the process of creating a skill goes like this:

- Decide what you want the skill to do and roughly how it should do it
- Write a draft of the skill
- Create a few test prompts and run claude-with-access-to-the-skill on them
- Help the user evaluate the results both qualitatively and quantitatively
  - While the runs happen in the background, draft some quantitative evals if there aren't any (if there are some, you can either use as is or modify if you feel something needs to change about them). Then explain them to the user (or if they already existed, explain the ones that already exist)
  - Use the `eval-viewer/generate_review.py` script to show the user the results for them to look at, and also let them look at the quantitative metrics
- Rewrite the skill based on feedback from the user's evaluation of the results (and also if there are any glaring flaws that become apparent from the quantitative benchmarks)
- Repeat until you're satisfied
- Expand the test set and try again at larger scale

Your job when using this skill is to figure out where the user is in this process and then jump in and help them progress through these stages. So for instance, maybe they're like "I want to make a skill for X". You can help narrow down what they mean, write a draft, write the test cases, figure out how they want to evaluate, run all the prompts, and repeat.

On the other hand, maybe they already have a draft of the skill. In this case you can go straight to the eval/iterate part of the loop.

Of course, you should always be flexible and if the user is like "I don't need to run a bunch of evaluations, just vibe with me", you can do that instead.

Then after the skill is done (but again, the order is flexible), you can also run the skill description improver, which we have a whole separate script for, to optimize the triggering of the skill.

Cool? Cool.

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

**Intent Capture phase checks:** `Goal defined`, `Triggers identified`, `Output format agreed`

**Skill Writing phase checks:** `SKILL.md written`, `README generated`, `Subagents designed`

**Testing phase checks:** `Evals created`, `Runs completed`, `Viewer launched`

**Iteration phase checks:** `Feedback incorporated`, `Benchmarks improved`, `Description optimized`

## Communicating with the user

The skill creator is liable to be used by people across a wide range of familiarity with coding jargon. If you haven't heard (and how could you, it's only very recently that it started), there's a trend now where the power of Claude is inspiring plumbers to open up their terminals, parents and grandparents to google "how to install npm". On the other hand, the bulk of users are probably fairly computer-literate.

So please pay attention to context cues to understand how to phrase your communication! In the default case, just to give you some idea:

- "evaluation" and "benchmark" are borderline, but OK
- for "JSON" and "assertion" you want to see serious cues from the user that they know what those things are before using them without explaining them

It's OK to briefly explain terms if you're in doubt, and feel free to clarify terms with a short definition if you're unsure if the user will get it.

---

## Mandatory Rule for Repo-Mutating Skills

When creating or updating any skill that changes files in a git repository (code, docs, config, commits, publishing), include this rule in that skill's SKILL.md:

- Add a **"Repo Sync Before Edits (mandatory)"** section near the top.
- Require pulling latest remote branch before modifications:
  - `branch="$(git rev-parse --abbrev-ref HEAD)"`
  - `git fetch origin`
  - `git pull --rebase origin "$branch"`
- If working tree is dirty: stash, sync, then pop.
- If `origin` is missing or conflicts occur: stop and ask the user before continuing.

Do not ship repo-mutating skills without this pre-sync guardrail.

## Version Management (mandatory)

Every skill must have a `metadata.version` field in its YAML frontmatter using semantic versioning (`MAJOR.MINOR.PATCH`). This version tracks the evolution of the skill itself — it tells users and tooling which iteration they're running.

**When creating a new skill**, set `metadata.version: 1.0.0` in the frontmatter:
```yaml
---
name: my-skill
description: ...
metadata:
  version: 1.0.0
---
```

**When updating or modifying an existing skill**, always bump the version before saving. Read the current version from the frontmatter and increment it:
- **Patch** (`x.y.Z`): Bug fixes, typo corrections, minor wording tweaks that don't change behavior
- **Minor** (`x.Y.0`): New capabilities, added sections, new subagents, expanded trigger phrases
- **Major** (`X.0.0`): Breaking changes to the skill's workflow, output format changes, restructured architecture

If the frontmatter has no `metadata.version` field, add one starting at `1.0.0`.

This applies every time you write or edit a SKILL.md — whether creating from scratch, improving after eval feedback, optimizing the description, or any other modification. The version bump is part of the edit, not a separate step.

## YAML Frontmatter Safety (mandatory)

YAML is surprisingly easy to break. An unquoted value containing a colon (`:`) causes many parsers to treat the rest of the line as a new mapping, silently producing wrong output or a hard parse error. This has bitten real skills — `cli-builder` and `code-review` both shipped with broken frontmatter for this reason.

**Rule: quote every frontmatter string that contains any of these characters: `:`, `#`, `{`, `}`, `[`, `]`, `,`, `&`, `*`, `?`, `|`, `-`, `<`, `>`, `=`, `!`, `%`, `@`, `` ` ``.**

In practice, the safest approach is to quote all multi-word string values in frontmatter by default — it costs nothing and prevents the whole class of bugs.

**Examples of the problem and the fix:**

```yaml
# BROKEN — the : after "workflow" starts a new mapping in strict parsers
description: Follows a 5-step workflow: Analyze -> Design -> Plan -> Execute -> Summarize.

# FIXED
description: "Follows a 5-step workflow: Analyze -> Design -> Plan -> Execute -> Summarize."
```

```yaml
# BROKEN — the : after "B+C" breaks strict parsers
architecture: subagent (Pattern B+C: Parallel Workers + Review Loop)

# FIXED
architecture: "subagent (Pattern B+C: Parallel Workers + Review Loop)"
```

When writing or editing any SKILL.md frontmatter, scan every value for colons and other special characters and wrap the value in double quotes if any are present. If the value itself contains double quotes, escape them with `\"`.

## Creating a skill

### Capture Intent

Start by understanding the user's intent. The current conversation might already contain a workflow the user wants to capture (e.g., they say "turn this into a skill"). If so, extract answers from the conversation history first — the tools used, the sequence of steps, corrections the user made, input/output formats observed. The user may need to fill the gaps, and should confirm before proceeding to the next step.

1. What should this skill enable Claude to do?
2. When should this skill trigger? (what user phrases/contexts)
3. What's the expected output format?
4. Should we set up test cases to verify the skill works? Skills with objectively verifiable outputs (file transforms, data extraction, code generation, fixed workflow steps) benefit from test cases. Skills with subjective outputs (writing style, art) often don't need them. Suggest the appropriate default based on the skill type, but let the user decide.
5. **Should this skill use subagents?** Evaluate whether the skill would benefit from delegating work to subagents via the Agent tool. Read `references/subagent-patterns.md` for the full guide, but the key signals are:
   - Will the skill read many files or scan large codebases? → Explorer subagent
   - Can parts of the work run in parallel? → Parallel worker subagents
   - Does the skill need independent quality review? → Review loop with fresh subagents
   - Will the skill produce large artifacts that require focused reasoning? → Executor subagent
   If any of these apply, design the skill with a main-agent-as-orchestrator architecture where the main agent handles user communication and coordination, and subagents handle the heavy lifting. This keeps the main conversation context clean.

### Interview and Research

Proactively ask questions about edge cases, input/output formats, example files, success criteria, and dependencies. Wait to write test prompts until you've got this part ironed out.

Check available MCPs - if useful for research (searching docs, finding similar skills, looking up best practices), research in parallel via subagents if available, otherwise inline. Come prepared with context to reduce burden on the user.

### Write the SKILL.md

Based on the user interview, fill in these components:

- **name**: Skill identifier. Must be **1-64 characters**, **lowercase letters, digits, and hyphens only**, **no consecutive hyphens**, and must **exactly match the parent directory name**. Example: a skill at `skills/my-skill/SKILL.md` must have `name: my-skill`. These rules are enforced by `scripts/quick_validate.py` — mismatches will fail validation.
- **description**: When to trigger, what it does. This is the primary triggering mechanism — include both what the skill does AND specific contexts for when to use it. All "when to use" info goes here, not in the body. **The description MUST be a single line (no newlines or line breaks)** — this is required for correct parsing by external tools and automation that process skill metadata. Claude currently tends to *undertrigger* skills — to skip them when they'd be useful — so make descriptions a little bit "pushy." But pushy has a complement: **negative triggers** (see below).
- **effort** (optional): How much reasoning effort the skill requires. Valid values: `low`, `medium`, `high`, `max`. Defaults to `high` when omitted. Use `low` for simple lookups or template fills, `medium` for moderate multi-step tasks, `high` for complex workflows requiring deep reasoning, and `max` for tasks demanding exhaustive analysis. This is an optional attribute — not all tools support it yet.
- **metadata.version**: Semantic version string (e.g., `1.0.0`). See "Version Management" above — this must be set on creation and bumped on every update.
- **compatibility**: Required tools, dependencies (optional, rarely needed)
- **the rest of the skill :)**

#### Writing a good description: pushy + negative triggers

A description has two jobs: pull in the queries that *should* trigger the skill, and push away the queries from adjacent domains that *shouldn't*. Most skill authors do the first part well (the "pushy" half) and forget the second. The result is false-positive triggers — a Tailwind skill running on a Vue project, a Python skill firing on a shell script question.

**The fix is a "Don't use for ..." clause.** Name the adjacent domains that share keywords or intent but are the wrong fit. This is especially important when your skill sits near other skills in the marketplace or covers a narrow slice of a broad topic.

**Example 1 — positive triggers only (insufficient):**
> Creates React components using Tailwind CSS.

**Example 1 — with negative triggers (much better):**
> Creates React components using Tailwind CSS. Make sure to use whenever the user asks for a new React component, UI element, or styled layout. **Don't use for** Vue, Svelte, vanilla CSS, or plain HTML projects.

**Example 2 — positive triggers only:**
> Generates SQL migrations for Postgres schemas.

**Example 2 — with negative triggers:**
> Generates SQL migrations for Postgres schemas. Trigger whenever the user needs a schema change, new table, or index. **Don't use for** MySQL, SQLite, MongoDB, or one-off ad-hoc queries.

Write the positive and negative halves as one continuous sentence or two back-to-back sentences — not a structured list. The description field is prose the model reads at trigger-time; the goal is for it to naturally rule out near-misses without feeling like a contract.

`scripts/quick_validate.py` emits a non-fatal warning if a description appears to lack a negative-trigger clause. It's a nudge, not a blocker — sometimes the skill's domain genuinely has no close neighbors, and that's fine.

### Skill Writing Guide

#### Anatomy of a Skill

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description required)
│   └── Markdown instructions
├── README.md (required — human-readable docs for catalog browsing)
├── agents/ (optional — subagent prompt files)
│   ├── explorer.md   - Codebase analysis subagent
│   ├── executor.md   - Implementation subagent
│   └── reviewer.md   - Quality review subagent
└── Bundled Resources (optional)
    ├── scripts/    - Executable code for deterministic/repetitive tasks
    ├── references/ - Docs loaded into context as needed
    └── assets/     - Files used in output (templates, icons, fonts)
```

The `agents/` directory is for skills that use the Agent tool to delegate work to subagents. Each file contains a complete prompt template for a specific subagent role (what it does, what it receives, what it returns). The SKILL.md references these files — e.g., "Read `agents/explorer.md` for the full explorer prompt" — so the main skill stays lean while subagents get detailed instructions. See `references/subagent-patterns.md` for when and how to use this pattern.

#### Progressive Disclosure

Skills use a three-level loading system:
1. **Metadata** (name + description) — Always in context (~100 words)
2. **SKILL.md body** — In context whenever skill triggers (keep under 500 lines)
3. **Bundled resources** — As needed (unlimited, scripts can execute without loading)

**Key patterns:**
- Keep SKILL.md under 500 lines. This is a hard rule for the skills authored here, not just a preference — longer SKILL.md files waste tokens on every invocation and tend to bury important guidance. If you're approaching the limit, add another layer of hierarchy (pull dense sections out to `references/`) and replace them with a one-line pointer like "Read `references/foo.md` when you need X."
- Reference files clearly from SKILL.md with guidance on when to read them
- For large reference files (>300 lines), include a table of contents

**Domain organization**: When a skill supports multiple domains/frameworks, organize by variant:
```
cloud-deploy/
├── SKILL.md (workflow + selection)
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```
Claude reads only the relevant reference file.

#### Principle of Lack of Surprise

This goes without saying, but skills must not contain malware, exploit code, or any content that could compromise system security. A skill's contents should not surprise the user in their intent if described. Don't go along with requests to create misleading skills or skills designed to facilitate unauthorized access, data exfiltration, or other malicious activities. Things like a "roleplay as an XYZ" are OK though.

#### Writing Patterns

Prefer using the imperative form in instructions.

**Defining output formats** — You can do it like this:
```markdown
## Report structure
ALWAYS use this exact template:
# [Title]
## Executive summary
## Key findings
## Recommendations
```

**Examples pattern** — It's useful to include examples. You can format them like this (but if "Input" and "Output" are in the examples you might want to deviate a little):
```markdown
## Commit message format
**Example 1:**
Input: Added user authentication with JWT tokens
Output: feat(auth): implement JWT-based authentication
```

#### Bundled scripts and error messages

When a skill includes scripts under `scripts/`, the scripts become part of the agent's execution surface — an agent runs them and reacts to what they print. That means a terse, unexplained `exit 1` is effectively a dead end: the agent sees a non-zero exit and has no idea what went wrong or how to recover.

**Rule: scripts must print descriptive, human-readable error messages on stderr (or stdout) before exiting.** The agent that just ran the script should be able to self-correct without the user intervening.

**Bad:**
```bash
if [ -z "$FIELD" ]; then
  exit 1
fi
```

```python
if not frontmatter.get('name'):
    sys.exit(1)
```

**Good:**
```bash
if [ -z "$FIELD" ]; then
  echo "Error: missing required field 'name' in SKILL.md frontmatter." >&2
  echo "Expected format: name: my-skill-name" >&2
  exit 1
fi
```

```python
if not frontmatter.get('name'):
    print(
        "Error: missing required field 'name' in SKILL.md frontmatter. "
        "Expected format: name: my-skill-name",
        file=sys.stderr,
    )
    sys.exit(1)
```

Good error messages say three things: **what went wrong, which input caused it, and how to fix it.** If the fix involves a filename, config key, or command, mention it explicitly — the agent will copy it verbatim.

#### Step Completion Reports (mandatory)

Every skill must produce a structured status report after each major phase — compact monospace block with checkmark rows and a summary result line, so pass/fail is immediately scannable. Mirror the format shown above in the "Step Completion Reports" section near the top of this file. Tailor the check names to what each step actually validates (e.g., a code review skill might use `Correctness`, `Test coverage`, `Security`, `Edge cases`; a deploy skill might use `Build`, `Tests`, `Lint`, `CI status`).

### Writing Style

Try to explain to the model why things are important in lieu of heavy-handed musty MUSTs. Use theory of mind and try to make the skill general and not super-narrow to specific examples. Start by writing a draft and then look at it with fresh eyes and improve it.

### Generate README.md

Every skill must include a README.md. **README.md is for human catalog browsing. It ships inside the `.skill` package but is never auto-loaded into agent context.** The runtime loader only pulls in `name` + `description` from frontmatter (always), `SKILL.md` body (on trigger), and files under `scripts/` / `references/` / `assets/` (only when SKILL.md tells the agent to read them). README.md sits outside all three, so keeping it focused on what humans need when deciding whether to install a skill — capabilities, triggers, workflow diagram, usage — costs zero runtime tokens.

This also means the rule "don't dump human prose that wastes tokens" applies to `SKILL.md` and `references/` (which *do* get loaded), not to README.md itself.

Use the following template:

```markdown
# [Skill Display Name]

> [One-line description of what the skill does]

## Highlights

- [Key capability 1]
- [Key capability 2]
- [Key capability 3]
- [Key capability 4]

## When to Use

| Say this... | Skill will... |
|---|---|
| "[trigger phrase 1]" | [What happens] |
| "[trigger phrase 2]" | [What happens] |
| "[trigger phrase 3]" | [What happens] |

## How It Works

` ` `mermaid
graph TD
    A["[First Step]"] --> B["[Second Step]"]
    B --> C["[Third Step]"]
    C --> D["[Final Step]"]
    style A fill:#4CAF50,color:#fff
    style D fill:#2196F3,color:#fff
` ` `

## Usage

` ` `
/[skill-name]
` ` `

## Resources

| Path | Description |
|---|---|
| `references/` | [What the references contain] |
| `scripts/` | [What the scripts do] |

## Output

[Description of what the skill produces — files, reports, etc.]
```

**README rules:**
- Title: Use the human-readable display name (e.g., "Code Optimizer", not "code-optimizer")
- Tagline: One sentence in blockquote format (> prefix)
- Highlights: 3-5 bullet points of key capabilities
- When to Use: Table with 3-4 trigger phrases mapping to actions
- How It Works: Mermaid `graph TD` diagram showing the main workflow steps. First node green (#4CAF50), last node blue (#2196F3)
- Usage: Code block with the slash command invocation
- Output: Brief description of what the skill produces
- Optional **Resources** section: Table with `| Path | Description |` columns if the skill has `scripts/`, `references/`, or `assets/` directories

### Test Cases

After writing the skill draft, come up with 2-3 realistic test prompts — the kind of thing a real user would actually say. Share them with the user: [you don't have to use this exact language] "Here are a few test cases I'd like to try. Do these look right, or do you want to add more?" Then run them.

Save test cases to `evals/evals.json`. Don't write assertions yet — just the prompts. You'll draft assertions in the next step while the runs are in progress.

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's task prompt",
      "expected_output": "Description of expected result",
      "files": []
    }
  ]
}
```

See `references/schemas.md` for the full schema (including the `assertions` field, which you'll add later).

Read `references/output-patterns.md` when designing output formats or file-writing behavior for a skill.
Read `references/workflows.md` when structuring multi-phase workflows or iteration loops in a skill.
Read `references/subagent-patterns.md` when the skill involves heavy exploration, parallel tasks, review loops, or large artifact generation — to design a subagent architecture that keeps the main agent's context clean.

### Optional: pre-eval LLM validation

Before spending tokens on full eval runs, you can run a cheaper 4-phase LLM validation pass to catch triggering failures, ambiguous logic, edge-case blind spots, and architectural bloat. Read `references/validation-prompts.md` for the copy-pasteable prompts for:

1. **Discovery validation** — does the frontmatter trigger correctly in isolation?
2. **Logic validation** — simulated step-by-step execution to find ambiguous instructions
3. **Edge case testing** — adversarial prompts to find failure states
4. **Architecture refinement** — enforces progressive disclosure and token discipline

This is optional — it's useful right after drafting a skill, after a large rewrite, or when an eval fails in a way you can't explain.

## Running and evaluating test cases

Read `references/eval-loop.md` for the full 5-step sequence (spawn runs, draft assertions, capture timing, grade/aggregate/view, read feedback). That file covers: the with-skill + baseline subagent pattern, the `eval_metadata.json` format, the `timing.json` capture, the `generate_review.py` invocation, and reading `feedback.json` when the user is done.

Do NOT use `/skill-test` or any other testing skill — the flow in `references/eval-loop.md` is the one this skill expects.

## Improving the skill

Read `references/iteration.md` for the improvement loop. That file covers five principles for revising a skill based on feedback (generalize, stay lean, explain the why, spot repeated work, consider subagents) plus the iteration loop itself and the optional blind comparison system.

## Description Optimization

The description field in SKILL.md frontmatter is the primary mechanism that determines whether Claude invokes a skill. After creating or improving a skill, offer to optimize the description for better triggering accuracy.

Read `references/description-optimization.md` for the full 4-step flow: generate trigger eval queries, review with the user via the HTML template, run the optimization loop with `run_loop.py`, and apply the best description. That file also explains the triggering mechanism itself and why substantive queries are better eval material than trivial ones.

### Package and Present (only if `present_files` tool is available)

Check whether you have access to the `present_files` tool. If you don't, skip this step. If you do, package the skill and present the `.skill` file to the user:

```bash
python -m scripts.package_skill <path/to/skill-folder>
```

After packaging, direct the user to the resulting `.skill` file path so they can install it.

## Environment-specific notes

If you're on Claude.ai (no subagents) or in Cowork (subagents but no browser), some mechanics change. Read `references/environment-modes.md` for the adapted flow in each environment. The core loop (draft → test → review → improve) is the same everywhere — only execution mechanics shift.

---

## Reference files

The `agents/` directory contains instructions for specialized subagents. Read them when you need to spawn the relevant subagent.

- `agents/grader.md` — How to evaluate assertions against outputs
- `agents/comparator.md` — How to do blind A/B comparison between two outputs
- `agents/analyzer.md` — How to analyze why one version beat another

The `references/` directory has additional documentation:
- `references/schemas.md` — JSON structures for evals.json, grading.json, etc.
- `references/subagent-patterns.md` — When and how to design skills that use the Agent tool to delegate work to subagents.
- `references/workflows.md` — Workflow patterns for structuring skill instructions, including the Subagent Orchestration pattern (Pattern 8).
- `references/output-patterns.md` — Output format and file-writing patterns.
- `references/validation-prompts.md` — Optional 4-phase LLM validation pass for a draft skill.
- `references/eval-loop.md` — Full 5-step eval run / grade / viewer flow.
- `references/iteration.md` — Principles for improving a skill based on feedback; blind comparison.
- `references/description-optimization.md` — 4-step description-tuning workflow.
- `references/environment-modes.md` — Claude.ai and Cowork-specific adaptations.

---

Repeating one more time the core loop here for emphasis:

- Figure out what the skill is about
- Draft or edit the skill
- Run claude-with-access-to-the-skill on test prompts
- With the user, evaluate the outputs:
  - Create benchmark.json and run `eval-viewer/generate_review.py` to help the user review them
  - Run quantitative evals
- Repeat until you and the user are satisfied
- Package the final skill and return it to the user.

Please add steps to your TodoList, if you have such a thing, to make sure you don't forget. If you're in Cowork, please specifically put "Create evals JSON and run `eval-viewer/generate_review.py` so human can review test cases" in your TodoList to make sure it happens.

Good luck!
