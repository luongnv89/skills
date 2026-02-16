# Guide to Building, Testing, and Validating Agent Skills for Claude

> Based on "The Complete Guide to Building Skills for Claude" by Anthropic

---

## Table of Contents

1. [Overview](#1-overview)
2. [Step 1: Understand What a Skill Is](#2-step-1-understand-what-a-skill-is)
3. [Step 2: Plan Your Skill](#3-step-2-plan-your-skill)
4. [Step 3: Set Up the File Structure](#4-step-3-set-up-the-file-structure)
5. [Step 4: Write the YAML Frontmatter](#5-step-4-write-the-yaml-frontmatter)
6. [Step 5: Write the Instructions (SKILL.md Body)](#6-step-5-write-the-instructions-skillmd-body)
7. [Step 6: Add Supporting Files](#7-step-6-add-supporting-files)
8. [Step 7: Test Your Skill](#8-step-7-test-your-skill)
9. [Step 8: Validate Your Skill](#9-step-8-validate-your-skill)
10. [Step 9: Iterate Based on Feedback](#10-step-9-iterate-based-on-feedback)
11. [Step 10: Distribute and Share](#11-step-10-distribute-and-share)
12. [Skill Patterns Reference](#12-skill-patterns-reference)
13. [Troubleshooting Guide](#13-troubleshooting-guide)
14. [Quick Checklist](#14-quick-checklist)
15. [Resources](#15-resources)

---

## 1. Overview

A **skill** is a set of instructions -- packaged as a simple folder -- that teaches Claude how to handle specific tasks or workflows. Instead of re-explaining your preferences, processes, and domain expertise in every conversation, skills let you teach Claude once and benefit every time.

Skills work identically across **Claude.ai**, **Claude Code**, and the **API**. Build once, use everywhere.

**Time to build your first skill:** ~15-30 minutes using the skill-creator.

---

## 2. Step 1: Understand What a Skill Is

### Core Concepts

A skill is a folder containing:

| File/Folder | Required? | Purpose |
|---|---|---|
| `SKILL.md` | **Required** | Main instruction file with YAML frontmatter |
| `scripts/` | Optional | Executable code (Python, Bash, etc.) |
| `references/` | Optional | Documentation loaded as needed |
| `assets/` | Optional | Templates, fonts, icons used in output |

### Progressive Disclosure (Three Levels)

Skills use a three-level system to minimize token usage:

1. **First level (YAML frontmatter):** Always loaded in Claude's system prompt. Provides just enough info for Claude to know *when* to use the skill.
2. **Second level (SKILL.md body):** Loaded when Claude thinks the skill is relevant. Contains full instructions.
3. **Third level (Linked files):** Additional files in the skill directory that Claude navigates and loads only as needed.

### Key Principles

- **Composability:** Claude can load multiple skills simultaneously. Your skill should work well alongside others.
- **Portability:** Skills work across Claude.ai, Claude Code, and the API without modification.

---

## 3. Step 2: Plan Your Skill

### 3.1 Define Use Cases

Before writing any code, identify **2-3 concrete use cases** your skill should enable.

**Good use case definition:**

```
Use Case: Project Sprint Planning
Trigger: User says "help me plan this sprint" or "create sprint tasks"
Steps:
  1. Fetch current project status from Linear (via MCP)
  2. Analyze team velocity and capacity
  3. Suggest task prioritization
  4. Create tasks in Linear with proper labels and estimates
Result: Fully planned sprint with tasks created
```

**Ask yourself:**
- What does a user want to accomplish?
- What multi-step workflows does this require?
- Which tools are needed (built-in or MCP)?
- What domain knowledge or best practices should be embedded?

### 3.2 Choose a Category

| Category | Used For | Key Techniques |
|---|---|---|
| **Document & Asset Creation** | Creating consistent, high-quality output (documents, apps, designs, code) | Embedded style guides, template structures, quality checklists |
| **Workflow Automation** | Multi-step processes benefiting from consistent methodology | Step-by-step validation gates, templates, review/refinement loops |
| **MCP Enhancement** | Workflow guidance to enhance tool access an MCP server provides | Coordinating multiple MCP calls, embedding domain expertise, error handling |

### 3.3 Choose Your Approach

- **Problem-first:** "I need to set up a project workspace" -- Your skill orchestrates the right tools in the right sequence. Users describe outcomes; the skill handles the tools.
- **Tool-first:** "I have Notion MCP connected" -- Your skill teaches Claude the optimal workflows and best practices. Users have access; the skill provides expertise.

### 3.4 Define Success Criteria

**Quantitative metrics:**
- Skill triggers on 90% of relevant queries
- Completes workflow in X tool calls
- 0 failed API calls per workflow

**Qualitative metrics:**
- Users don't need to prompt Claude about next steps
- Workflows complete without user correction
- Consistent results across sessions

---

## 4. Step 3: Set Up the File Structure

### Create the Folder

```
your-skill-name/
├── SKILL.md                    # Required - main skill file
├── scripts/                    # Optional - executable code
│   ├── process_data.py
│   └── validate.sh
├── references/                 # Optional - documentation
│   ├── api-guide.md
│   └── examples/
└── assets/                     # Optional - templates, etc.
    └── report-template.md
```

### Critical Naming Rules

**SKILL.md naming:**
- Must be exactly `SKILL.md` (case-sensitive)
- No variations accepted (SKILL.MD, skill.md, etc.)

**Skill folder naming:**
- Use kebab-case: `notion-project-setup`
- No spaces: ~~`Notion Project Setup`~~
- No underscores: ~~`notion_project_setup`~~
- No capitals: ~~`NotionProjectSetup`~~

**No README.md inside the skill folder.** All documentation goes in SKILL.md or `references/`.

---

## 5. Step 4: Write the YAML Frontmatter

The YAML frontmatter is the **most important part** -- it determines whether Claude loads your skill.

### Minimal Required Format

```yaml
---
name: your-skill-name
description: What it does. Use when user asks to [specific phrases].
---
```

### Required Fields

**`name` (required):**
- kebab-case only
- No spaces or capitals
- Should match folder name

**`description` (required):**
- MUST include BOTH: what the skill does AND when to use it (trigger conditions)
- Under 1024 characters
- No XML tags (`<` or `>`)
- Include specific tasks users might say
- Mention file types if relevant

**Description structure:** `[What it does] + [When to use it] + [Key capabilities]`

### Good Description Examples

```yaml
# Good - specific and actionable
description: Analyzes Figma design files and generates developer handoff
  documentation. Use when user uploads .fig files, asks for "design specs",
  "component documentation", or "design-to-code handoff".

# Good - includes trigger phrases
description: Manages Linear project workflows including sprint planning,
  task creation, and status tracking. Use when user mentions "sprint",
  "Linear tasks", "project planning", or asks to "create tickets".

# Good - clear value proposition
description: End-to-end customer onboarding workflow for PayFlow. Handles
  account creation, payment setup, and subscription management. Use when
  user says "onboard new customer", "set up subscription", or "create
  PayFlow account".
```

### Bad Description Examples

```yaml
# Too vague
description: Helps with projects.

# Missing triggers
description: Creates sophisticated multi-page documentation systems.

# Too technical, no user triggers
description: Implements the Project entity model with hierarchical relationships.
```

### Optional Fields

```yaml
---
name: skill-name
description: [required description]
license: MIT                    # Optional: for open-source skills
compatibility: "Requires Node.js 18+, works on macOS/Linux"  # Optional: 1-500 chars
allowed-tools: "Bash(python:*) Bash(npm:*) WebFetch"         # Optional: restrict tool access
metadata:                       # Optional: custom key-value pairs
  author: Company Name
  version: 1.0.0
  mcp-server: server-name
  category: productivity
  tags: [project-management, automation]
---
```

### Security Restrictions

**Forbidden in frontmatter:**
- XML angle brackets (`<` `>`)
- Skills with "claude" or "anthropic" in name (reserved)
- Code execution in YAML

---

## 6. Step 5: Write the Instructions (SKILL.md Body)

After the frontmatter, write the actual instructions in Markdown.

### Recommended Template

```markdown
---
name: your-skill
description: [...]
---

# Your Skill Name

## Instructions

### Step 1: [First Major Step]
Clear explanation of what happens.

Example:
```bash
python scripts/fetch_data.py --project-id PROJECT_ID
Expected output: [describe what success looks like]
```

(Add more steps as needed)

## Examples

### Example 1: [Common Scenario]
User says: "Set up a new marketing campaign"

Actions:
1. Fetch existing campaigns via MCP
2. Create new campaign with provided parameters

Result: Campaign created with confirmation link

## Troubleshooting

### Error: [Common error message]
**Cause:** [Why it happens]
**Solution:** [How to fix]
```

### Best Practices for Instructions

**Be specific and actionable:**

```markdown
# Good
Run `python scripts/validate.py --input {filename}` to check data format.
If validation fails, common issues include:
- Missing required fields (add them to the CSV)
- Invalid date formats (use YYYY-MM-DD)

# Bad
Validate the data before proceeding.
```

**Include error handling:**

```markdown
## Common Issues

### MCP Connection Failed
If you see "Connection refused":
1. Verify MCP server is running: Check Settings > Extensions
2. Confirm API key is valid
3. Try reconnecting: Settings > Extensions > [Your Service] > Reconnect
```

**Reference bundled resources clearly:**

```markdown
Before writing queries, consult `references/api-patterns.md` for:
- Rate limiting guidance
- Pagination patterns
- Error codes and handling
```

**Use progressive disclosure:** Keep SKILL.md focused on core instructions. Move detailed documentation to `references/` and link to it.

---

## 7. Step 6: Add Supporting Files

### Scripts (`scripts/`)

Executable code that Claude can run during workflows:
- Validation scripts
- Data processing utilities
- Build/compilation helpers

### References (`references/`)

Documentation that Claude loads on demand:
- API guides
- Code examples
- Pattern libraries
- Style guides

### Assets (`assets/`)

Templates and resources used in output:
- Report templates
- Email templates
- Configuration files

---

## 8. Step 7: Test Your Skill

Skills can be tested at three levels of rigor:

| Method | Best For | Setup Required |
|---|---|---|
| **Manual testing in Claude.ai** | Fast iteration, no setup | None |
| **Scripted testing in Claude Code** | Repeatable validation | Minimal |
| **Programmatic testing via Skills API** | Systematic evaluation suites | API setup |

> **Pro Tip:** Iterate on a single task before expanding. Get one challenging task working perfectly, then extract the winning approach into a skill.

### 8.1 Triggering Tests

**Goal:** Ensure your skill loads at the right times.

**Test cases:**
- Triggers on obvious tasks
- Triggers on paraphrased requests
- Does NOT trigger on unrelated topics

**Example test suite:**

```
Should trigger:
- "Help me set up a new ProjectHub workspace"
- "I need to create a project in ProjectHub"
- "Initialize a ProjectHub project for Q4 planning"

Should NOT trigger:
- "What's the weather in San Francisco?"
- "Help me write Python code"
- "Create a spreadsheet" (unless your skill handles sheets)
```

### 8.2 Functional Tests

**Goal:** Verify the skill produces correct outputs.

**Test cases:**
- Valid outputs generated
- API calls succeed
- Error handling works
- Edge cases covered

**Example:**

```
Test: Create project with 5 tasks
Given: Project name "Q4 Planning", 5 task descriptions
When: Skill executes workflow
Then:
  - Project created in ProjectHub
  - 5 tasks created with correct properties
  - All tasks linked to project
  - No API errors
```

### 8.3 Performance Comparison

**Goal:** Prove the skill improves results vs. baseline.

**Baseline comparison:**

```
Without skill:                    With skill:
- User provides instructions      - Automatic workflow execution
  each time                       - 2 clarifying questions only
- 15 back-and-forth messages      - 0 failed API calls
- 3 failed API calls              - 6,000 tokens consumed
  requiring retry
- 12,000 tokens consumed
```

---

## 9. Step 8: Validate Your Skill

### Use the skill-creator Tool

The `skill-creator` skill (available in Claude.ai and Claude Code) can help you build and validate skills.

**To use it:**
```
"Use the skill-creator skill to help me build a skill for [your use case]"
```

**Creating skills:** Generates from natural language descriptions, produces properly formatted SKILL.md, suggests trigger phrases.

**Reviewing skills:** Flags common issues (vague descriptions, missing triggers, structural problems), identifies over/under-triggering risks, suggests test cases.

**Validating skills:**
```
"Review this skill and suggest improvements"
```

> Note: skill-creator helps you design and refine skills but does not execute automated test suites or produce quantitative evaluation results.

### Validation Checklist

Run through this checklist before considering your skill complete:

**Structure validation:**
- [ ] Folder named in kebab-case
- [ ] SKILL.md file exists (exact spelling)
- [ ] YAML frontmatter has `---` delimiters
- [ ] `name` field: kebab-case, no spaces, no capitals
- [ ] `description` includes WHAT and WHEN
- [ ] No XML tags (`<` `>`) anywhere

**Content validation:**
- [ ] Instructions are clear and actionable
- [ ] Error handling included
- [ ] Examples provided
- [ ] References clearly linked

**Trigger validation:**
- [ ] Tested triggering on obvious tasks
- [ ] Tested triggering on paraphrased requests
- [ ] Verified doesn't trigger on unrelated topics

**Functional validation:**
- [ ] Functional tests pass
- [ ] Tool integration works (if applicable)

---

## 10. Step 9: Iterate Based on Feedback

Skills are living documents. Plan to iterate based on:

### Undertriggering Signals

**Symptoms:**
- Skill doesn't load when it should
- Users manually enabling it
- Support questions about when to use it

**Solution:** Add more detail and nuance to the description -- include keywords, especially for technical terms.

### Overtriggering Signals

**Symptoms:**
- Skill loads for irrelevant queries
- Users disabling it
- Confusion about purpose

**Solution:** Add negative triggers, be more specific.

```yaml
# Example: adding negative triggers
description: Advanced data analysis for CSV files. Use for statistical
  modeling, regression, clustering. Do NOT use for simple data exploration
  (use data-viz skill instead).
```

### Execution Issues

**Symptoms:**
- Inconsistent results
- API call failures
- User corrections needed

**Solution:** Improve instructions, add error handling. Address:
1. **Instructions too verbose** -- Keep concise, use bullet points
2. **Instructions buried** -- Put critical instructions at the top, use `## Important` headers
3. **Ambiguous language** -- Be explicit and specific
4. **Model "laziness"** -- Add explicit encouragement:
   ```markdown
   ## Performance Notes
   - Take your time to do this thoroughly
   - Quality is more important than speed
   - Do not skip validation steps
   ```

---

## 11. Step 10: Distribute and Share

### For Individual Users

1. Download the skill folder
2. Zip the folder (if needed)
3. Upload to Claude.ai via **Settings > Capabilities > Skills**
4. Or place in Claude Code skills directory

### For Organizations

- Admins can deploy skills workspace-wide
- Automatic updates
- Centralized management

### Via GitHub (Recommended)

1. **Host on GitHub** with a public repo
   - Clear README with installation instructions
   - Example usage and screenshots

2. **Create an installation guide:**
   ```markdown
   ## Installing the [Your Service] Skill

   1. Download the skill:
      - Clone repo: `git clone https://github.com/yourcompany/skills`
      - Or download ZIP from Releases

   2. Install in Claude:
      - Open Claude.ai > Settings > Skills
      - Click "Upload skill"
      - Select the skill folder (zipped)

   3. Enable the skill:
      - Toggle on the [Your Service] skill
      - Ensure your MCP server is connected

   4. Test:
      - Ask Claude: "Set up a new project in [Your Service]"
   ```

### Via API

For programmatic use cases:
- `/v1/skills` endpoint for listing and managing skills
- Add skills to Messages API requests via the `container.skills` parameter
- Works with the Claude Agent SDK for building custom agents

### Positioning Your Skill

**Focus on outcomes, not features:**

```
# Good
"The ProjectHub skill enables teams to set up complete project
workspaces in seconds -- including pages, databases, and templates
-- instead of spending 30 minutes on manual setup."

# Bad
"The ProjectHub skill is a folder containing YAML frontmatter
and Markdown instructions that calls our MCP server tools."
```

---

## 12. Skill Patterns Reference

### Pattern 1: Sequential Workflow Orchestration

**Use when:** Multi-step processes in a specific order.

```markdown
## Workflow: Onboard New Customer

### Step 1: Create Account
Call MCP tool: `create_customer`
Parameters: name, email, company

### Step 2: Setup Payment
Call MCP tool: `setup_payment_method`
Wait for: payment method verification

### Step 3: Create Subscription
Call MCP tool: `create_subscription`
Parameters: plan_id, customer_id (from Step 1)

### Step 4: Send Welcome Email
Call MCP tool: `send_email`
Template: welcome_email_template
```

**Key techniques:** Explicit step ordering, dependencies between steps, validation at each stage, rollback instructions for failures.

### Pattern 2: Multi-MCP Coordination

**Use when:** Workflows span multiple services.

```markdown
### Phase 1: Design Export (Figma MCP)
1. Export design assets from Figma
2. Generate design specifications
3. Create asset manifest

### Phase 2: Asset Storage (Drive MCP)
1. Create project folder in Drive
2. Upload all assets
3. Generate shareable links

### Phase 3: Task Creation (Linear MCP)
1. Create development tasks
2. Attach asset links to tasks
3. Assign to engineering team

### Phase 4: Notification (Slack MCP)
1. Post handoff summary to #engineering
2. Include asset links and task references
```

**Key techniques:** Clear phase separation, data passing between MCPs, validation before moving to next phase.

### Pattern 3: Iterative Refinement

**Use when:** Output quality improves with iteration.

```markdown
### Initial Draft
1. Fetch data via MCP
2. Generate first draft report
3. Save to temporary file

### Quality Check
1. Run validation script: `scripts/check_report.py`
2. Identify issues:
   - Missing sections
   - Inconsistent formatting
   - Data validation errors

### Refinement Loop
1. Address each identified issue
2. Regenerate affected sections
3. Re-validate
4. Repeat until quality threshold met

### Finalization
1. Apply final formatting
2. Generate summary
3. Save final version
```

**Key techniques:** Explicit quality criteria, iterative improvement, validation scripts, know when to stop iterating.

### Pattern 4: Context-Aware Tool Selection

**Use when:** Same outcome, different tools depending on context.

```markdown
### Decision Tree
1. Check file type and size
2. Determine best storage location:
   - Large files (>10MB): Use cloud storage MCP
   - Collaborative docs: Use Notion/Docs MCP
   - Code files: Use GitHub MCP
   - Temporary files: Use local storage

### Execute Storage
Based on decision:
- Call appropriate MCP tool
- Apply service-specific metadata
- Generate access link

### Provide Context to User
Explain why that storage was chosen
```

**Key techniques:** Clear decision criteria, fallback options, transparency about choices.

### Pattern 5: Domain-Specific Intelligence

**Use when:** Your skill adds specialized knowledge beyond tool access.

```markdown
### Before Processing (Compliance Check)
1. Fetch transaction details via MCP
2. Apply compliance rules:
   - Check sanctions lists
   - Verify jurisdiction allowances
   - Assess risk level
3. Document compliance decision

### Processing
IF compliance passed:
  - Call payment processing MCP tool
  - Apply appropriate fraud checks
  - Process transaction
ELSE:
  - Flag for review
  - Create compliance case

### Audit Trail
- Log all compliance checks
- Record processing decisions
- Generate audit report
```

**Key techniques:** Domain expertise embedded in logic, compliance before action, comprehensive documentation, clear governance.

---

## 13. Troubleshooting Guide

### Skill Won't Upload

| Error | Cause | Solution |
|---|---|---|
| "Could not find SKILL.md" | File not named exactly `SKILL.md` | Rename to `SKILL.md` (case-sensitive). Verify with `ls -la` |
| "Invalid frontmatter" | YAML formatting issue | Ensure `---` delimiters, no unclosed quotes, correct syntax |
| "Invalid skill name" | Name has spaces or capitals | Use kebab-case: `my-cool-skill` |

### Skill Doesn't Trigger

**Symptom:** Skill never loads automatically.

**Fix:** Revise your description field.

**Quick checklist:**
- Is it too generic? ("Helps with projects" won't work)
- Does it include trigger phrases users would actually say?
- Does it mention relevant file types if applicable?

**Debugging approach:** Ask Claude: "When would you use the [skill name] skill?" Claude will quote the description back. Adjust based on what's missing.

### Skill Triggers Too Often

**Solutions:**
1. **Add negative triggers:** `"Do NOT use for simple data exploration (use data-viz skill instead)."`
2. **Be more specific:** Change `"Processes documents"` to `"Processes PDF legal documents for contract review"`
3. **Clarify scope:** `"Use specifically for online payment workflows, not for general financial queries."`

### Instructions Not Followed

**Common causes:**
1. **Instructions too verbose** -- Keep concise, use bullet points, move detail to separate files
2. **Instructions buried** -- Put critical instructions at the top, use `## Important` headers
3. **Ambiguous language** -- Replace `"Make sure to validate things properly"` with `"CRITICAL: Before calling create_project, verify: Project name is non-empty, At least one team member assigned, Start date is not in the past"`

### MCP Connection Issues

**Symptom:** Skill loads but MCP calls fail.

**Checklist:**
1. Verify MCP server is connected (Settings > Extensions)
2. Check authentication (API keys valid, proper permissions/scopes)
3. Test MCP independently (ask Claude to call MCP directly without skill)
4. Verify tool names (case-sensitive, check MCP server documentation)

### Large Context Issues

**Symptom:** Skill seems slow or responses degraded.

**Solutions:**
1. **Optimize SKILL.md size** -- Move detailed docs to `references/`, keep SKILL.md under 5,000 words
2. **Reduce enabled skills** -- Evaluate if you have more than 20-50 skills enabled simultaneously

---

## 14. Quick Checklist

### Before You Start
- [ ] Identified 2-3 concrete use cases
- [ ] Tools identified (built-in or MCP)
- [ ] Reviewed this guide and example skills
- [ ] Planned folder structure

### During Development
- [ ] Folder named in kebab-case
- [ ] SKILL.md file exists (exact spelling)
- [ ] YAML frontmatter has `---` delimiters
- [ ] `name` field: kebab-case, no spaces, no capitals
- [ ] `description` includes WHAT and WHEN
- [ ] No XML tags (`<` `>`) anywhere
- [ ] Instructions are clear and actionable
- [ ] Error handling included
- [ ] Examples provided
- [ ] References clearly linked

### Before Upload
- [ ] Tested triggering on obvious tasks
- [ ] Tested triggering on paraphrased requests
- [ ] Verified doesn't trigger on unrelated topics
- [ ] Functional tests pass
- [ ] Tool integration works (if applicable)
- [ ] Compressed as .zip file

### After Upload
- [ ] Test in real conversations
- [ ] Monitor for under/over-triggering
- [ ] Collect user feedback
- [ ] Iterate on description and instructions
- [ ] Update version in metadata

---

## 15. Resources

### Official Documentation
- [Best Practices Guide](https://docs.anthropic.com)
- [Skills Documentation](https://docs.anthropic.com)
- [API Reference](https://docs.anthropic.com)
- [MCP Documentation](https://docs.anthropic.com)

### Tools
- **skill-creator skill** -- Built into Claude.ai and available for Claude Code. Use: `"Help me build a skill using skill-creator"`
- **Public skills repository** -- GitHub: `anthropics/skills` -- Contains Anthropic-created skills you can customize

### Example Skills
- Document Skills (PDF, DOCX, PPTX, XLSX)
- Example Skills (various workflow patterns)
- Partner Skills Directory (Asana, Atlassian, Canva, Figma, Sentry, Zapier, and more)

### Getting Support
- **General questions:** Claude Developers Discord
- **Bug reports:** GitHub Issues at `anthropics/skills/issues` (include skill name, error message, steps to reproduce)
