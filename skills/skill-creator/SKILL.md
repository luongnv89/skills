---
name: skill-creator
version: 2.0.0
description: Interactive guide for creating new skills (or updating existing skills) that extend Claude's capabilities. Walks the user through use case definition, frontmatter generation, instruction writing, and validation. Use when users want to create a new skill, build a skill, update an existing skill, or ask "help me make a skill for X". Always clarifies requirements before generating.
---

# Skill Creator

Interactive, guided skill creation following Anthropic's best practices.

## Important

- NEVER generate a skill without first completing the Discovery phase
- ALWAYS present the full understanding summary and get explicit user approval before writing any skill files
- ALWAYS include test and validation steps in every created skill where applicable
- Quality is more important than speed -- take your time to do this thoroughly

## Workflow Overview

Skill creation follows four phases in strict order:

1. **Discovery** -- Ask questions, clarify requirements, gather examples
2. **Approval** -- Present understanding summary, get user sign-off
3. **Build** -- Initialize, write SKILL.md and resources, run validation
4. **Test & Deliver** -- Generate test suite, run validation, package

Do NOT skip or merge phases. Complete each phase before proceeding.

---

## Phase 1: Discovery

Goal: Understand exactly what the user needs before writing anything.

### Step 1.1: Identify the Core Purpose

Ask the user:
- "What task or workflow should this skill handle?"
- "Can you give 2-3 concrete examples of how you would use this skill?"

If the user's answer is vague or only covers one scenario, ask follow-up:
- "What would a user say to trigger this skill?"
- "Are there related tasks this skill should also handle, or should those be separate?"

### Step 1.2: Clarify Technical Requirements

Based on the user's answers, determine:
- **Category:** Document & Asset Creation, Workflow Automation, or MCP Enhancement
- **Approach:** Problem-first (user describes outcomes) or Tool-first (user has tools, needs guidance)
- **Tools needed:** Built-in Claude tools, MCP servers, or external scripts
- **Dependencies:** Required packages, APIs, services

Ask about anything unclear:
- "Does this skill need to interact with any external services or MCP servers?"
- "Are there specific output formats or quality standards required?"
- "Should this skill work with specific file types?"

### Step 1.3: Identify Edge Cases and Error Scenarios

Ask:
- "What could go wrong during this workflow?"
- "How should the skill handle errors (e.g., missing data, API failures)?"
- "Are there tasks that look similar but should NOT trigger this skill?"

### Step 1.4: Gather Domain Knowledge

If the skill embeds specialized knowledge:
- "Do you have any reference documentation, templates, or examples to include?"
- "Are there company-specific conventions or standards to follow?"

### Discovery Completion Gate

Do NOT proceed to Phase 2 until you can clearly answer ALL of these:
- What does the skill do? (purpose)
- When should it trigger? (2-3 trigger phrases)
- When should it NOT trigger? (negative triggers)
- What are the workflow steps? (sequence)
- What tools/resources are needed? (dependencies)
- What can go wrong? (error cases)

If any answer is unclear, ask the user before proceeding.

---

## Phase 2: Approval

Goal: Present a complete understanding summary and get explicit user approval.

### Step 2.1: Present the Understanding Summary

Display the following structured summary to the user:

```
## Skill Summary for Approval

**Name:** [kebab-case-name]
**Category:** [Document & Asset Creation / Workflow Automation / MCP Enhancement]
**Approach:** [Problem-first / Tool-first]

### What It Does
[1-2 sentence description]

### When It Triggers (description field)
[Draft description including WHAT + WHEN + trigger phrases]

### When It Should NOT Trigger
[Negative triggers / out-of-scope tasks]

### Workflow Steps
1. [Step 1]
2. [Step 2]
3. [Step N]

### Error Handling
- [Error scenario 1] → [How to handle]
- [Error scenario 2] → [How to handle]

### Resources to Include
- scripts/: [list or "none"]
- references/: [list or "none"]
- assets/: [list or "none"]

### Test Cases
**Should trigger:**
- "[example phrase 1]"
- "[example phrase 2]"
- "[example phrase 3]"

**Should NOT trigger:**
- "[unrelated phrase 1]"
- "[unrelated phrase 2]"

### Success Criteria
- [Criterion 1]
- [Criterion 2]
```

### Step 2.2: Get Explicit Approval

Ask the user:
- "Does this summary accurately capture what you need? Please confirm or tell me what to change."

If the user requests changes, update the summary and re-present it. Do NOT proceed until the user explicitly approves.

---

## Phase 3: Build

Goal: Create the skill folder, SKILL.md, and all resources.

### Step 3.1: Initialize the Skill

Run the initialization script:

```bash
python scripts/init_skill.py <skill-name> --path <output-directory>
```

Skip if updating an existing skill.

### Step 3.2: Write the YAML Frontmatter

Use the approved summary to write the frontmatter:

```yaml
---
name: [kebab-case-name]
version: 1.0.0
description: [approved description -- must include WHAT it does + WHEN to use it with trigger phrases. Under 1024 chars. No XML tags.]
---
```

**Frontmatter rules:**
- `name`: kebab-case only, no spaces or capitals, must match folder name
- `version`: semver format (MAJOR.MINOR.PATCH)
- `description`: MUST include both WHAT the skill does and WHEN to use it
  - Structure: `[What it does] + [When to use it] + [Key capabilities]`
  - Include specific trigger phrases users might say
  - Mention file types if relevant
  - Under 1024 characters
  - No XML angle brackets
- Do not use "claude" or "anthropic" in the name (reserved)

**Description quality check -- verify it is NOT:**
- Too vague (e.g., "Helps with projects")
- Missing triggers (e.g., "Creates documentation systems")
- Too technical without user triggers (e.g., "Implements entity model with relationships")

### Step 3.3: Write the SKILL.md Body

Follow this structure (adapt sections as needed):

```markdown
# [Skill Name]

## Instructions

### Step 1: [First Major Step]
Clear, actionable explanation.
[Include specific commands, parameters, expected output]

### Step 2: [Next Step]
...

## Examples

### Example 1: [Common Scenario]
User says: "[trigger phrase]"
Actions:
1. [action]
2. [action]
Result: [expected outcome]

## Error Handling

### [Error Scenario]
**Cause:** [why it happens]
**Solution:** [specific fix steps]

## Validation

[If applicable, include validation steps or checklist for the skill's output]
```

**Writing rules:**
- Be specific and actionable -- avoid vague instructions like "validate the data"
- Use imperative/infinitive form
- Include concrete commands with parameters
- Reference bundled resources clearly: `See references/api-guide.md for rate limiting`
- Keep SKILL.md under 500 lines; move details to `references/`
- Put critical instructions at the top
- Use bullet points and numbered lists over prose
- Include error handling for every workflow step that can fail

### Step 3.4: Create Supporting Resources

**Scripts (`scripts/`):**
- Write executable code for deterministic/repetitive tasks
- Test every script by actually running it
- Include proper error handling and usage instructions

**References (`references/`):**
- Move detailed documentation out of SKILL.md
- Structure files with table of contents if over 100 lines
- Keep references one level deep from SKILL.md

**Assets (`assets/`):**
- Include templates, images, fonts used in output
- Not intended to be loaded into context

Delete any example files from `init_skill.py` that are not needed.

### Step 3.5: Add Test and Validation Section

Every skill MUST include testing guidance. Add to the SKILL.md or as a separate `references/testing.md`:

**Triggering test suite:**
```
Should trigger:
- "[obvious task phrase]"
- "[paraphrased request]"
- "[alternative wording]"

Should NOT trigger:
- "[unrelated topic]"
- "[similar but out-of-scope task]"
```

**Functional test cases** (where applicable):
```
Test: [test name]
Given: [preconditions]
When: [action]
Then:
  - [expected result 1]
  - [expected result 2]
  - [no errors]
```

---

## Phase 4: Test & Deliver

Goal: Validate the skill and deliver to the user.

### Step 4.1: Run Structural Validation

Run the validation script:

```bash
python scripts/quick_validate.py <path/to/skill-folder>
```

Fix any reported errors before proceeding.

### Step 4.2: Manual Validation Checklist

Verify each item:

**Structure:**
- [ ] Folder named in kebab-case
- [ ] SKILL.md exists (exact spelling, case-sensitive)
- [ ] YAML frontmatter has `---` delimiters
- [ ] `name` is kebab-case, no spaces, no capitals
- [ ] `description` includes WHAT and WHEN
- [ ] No XML tags anywhere
- [ ] No README.md inside skill folder

**Content:**
- [ ] Instructions are clear and actionable (no vague language)
- [ ] Error handling included for failure scenarios
- [ ] Examples provided with realistic user requests
- [ ] References clearly linked from SKILL.md
- [ ] No TODO placeholders remaining
- [ ] SKILL.md under 500 lines

**Testing:**
- [ ] Triggering test suite included (should/should-not trigger)
- [ ] Functional test cases included where applicable
- [ ] Scripts tested by running them

### Step 4.3: Package the Skill

```bash
python scripts/package_skill.py <path/to/skill-folder> [output-directory]
```

The packaging script validates automatically and creates a versioned `.skill` file.

### Step 4.4: Present to User

Deliver the completed skill with:
1. The `.skill` file location
2. Summary of what was created (files, structure)
3. The test suite for the user to run
4. Installation instructions:
   - Claude.ai: Settings > Capabilities > Skills > Upload
   - Claude Code: Place in skills directory
5. Iteration guidance: "After using the skill, bring back any edge cases or failures to improve it"

---

## Core Principles Reference

### Concise is Key

The context window is a shared resource. Only add context Claude doesn't already have. Challenge each piece of information: "Does Claude really need this?" Prefer concise examples over verbose explanations.

### Progressive Disclosure

Skills use three loading levels:
1. **Metadata** (name + description) -- always in context (~100 words)
2. **SKILL.md body** -- loaded when skill triggers (keep under 5k words)
3. **Bundled resources** -- loaded as needed by Claude

Keep SKILL.md focused. Move detailed docs to `references/` and link to them.

### Degrees of Freedom

Match specificity to the task:
- **High freedom** (text instructions): Multiple valid approaches, context-dependent
- **Medium freedom** (pseudocode/parameterized scripts): Preferred pattern exists, some variation OK
- **Low freedom** (specific scripts): Fragile operations, consistency critical

### What NOT to Include

Do not create these files inside a skill:
- README.md, CHANGELOG.md, INSTALLATION_GUIDE.md
- User-facing documentation (skill is for AI agent, not humans)
- Auxiliary context about the creation process

### Design Patterns

For detailed patterns, consult these references:
- **Multi-step workflows**: See `references/workflows.md` for sequential and conditional patterns
- **Output quality**: See `references/output-patterns.md` for template and example patterns

---

## Updating Existing Skills

When asked to update an existing skill:

1. **Read the current skill** -- Understand what exists before changing anything
2. **Run Discovery** -- Ask what needs to change and why
3. **Present changes for Approval** -- Show a diff-style summary of proposed changes
4. **Apply changes** -- Edit files, update version (PATCH for fixes, MINOR for features, MAJOR for breaking changes)
5. **Re-validate** -- Run validation script and checklist
6. **Re-package** -- Create new versioned `.skill` file
