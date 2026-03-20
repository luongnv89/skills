---
name: github-issue-creator
description: Create or update GitHub issues from screenshots, bug report emails, messages, or any visual/text input. Extracts structured issue data from images or pasted text, detects the repo's issue templates, proposes issues for user approval, then creates or updates them via gh CLI. Use this skill whenever the user shares a screenshot of a bug, pastes an error report, forwards a bug email, wants to file issues from a conversation, says "create an issue from this", "turn this into a GitHub issue", "file a bug for this", "update the issue with this info", or has any visual or textual bug/feature report they want tracked as GitHub issues — even if they just drop an image and say "handle this".
---

# GitHub Issue Creator

Create and update GitHub issues from screenshots, emails, messages, and other unstructured input sources.

## Repo Sync Before Edits (mandatory)

This skill creates issues on a remote GitHub repo, so always verify connectivity first:

```bash
gh auth status
gh repo view --json name,owner,url
```

If `gh` is not authenticated or the current directory is not a GitHub repo, stop and tell the user what's missing before continuing.

## Workflow

Follow these three phases strictly. Do not skip the approval step — the user must confirm before any issue is created or updated.

### Phase 1: Extract Information

Read the user's input carefully. Input can be:

- **Screenshots / images**: Read the image file to extract text, error messages, UI state, stack traces, and any visible context. Pay attention to browser URLs, error codes, timestamps, and user-visible symptoms.
- **Pasted text**: Bug report emails, Slack messages, support tickets, error logs, user complaints.
- **Verbal descriptions**: The user describing a bug or feature request conversationally.
- **Multiple sources**: The user may provide several screenshots plus some context text. Combine all of them.

For each distinct issue you identify, extract:
- **Title**: A clear, concise summary (imperative or descriptive — e.g., "Login button unresponsive on mobile Safari")
- **Description**: What's happening, including any error messages, stack traces, or reproduction context from the source material
- **Steps to reproduce**: If inferable from the input
- **Expected vs actual behavior**: If inferable
- **Environment details**: OS, browser, app version — anything visible in the input
- **Severity/priority signal**: If the source indicates urgency ("critical", "blocking", "P0", etc.)
- **Labels**: Suggest appropriate labels based on content (e.g., `bug`, `enhancement`, `critical`, `ui`, `backend`)

It's fine if not all fields are available — extract what you can. Don't fabricate details that aren't in the input.

### Phase 1.5: Sanitize Sensitive Information

GitHub issues are typically public (or at least visible to the whole team). Bug reports from emails, screenshots, and support tickets often contain personal or confidential data that should never end up in a GitHub issue. Before composing any issue content, scan everything you extracted and redact the following:

**Personal Identifiable Information (PII):**
- **Names of end users or reporters** — replace with generic references like "a user", "the reporter". Keep names only if the person is a team member the user explicitly wants tagged.
- **Email addresses** — redact entirely (e.g., `j***@example.com` or just remove)
- **Phone numbers** — remove
- **Physical addresses** — remove
- **User IDs / account names** of end users — replace with `[user_id]` or `[redacted]`

**Credentials and secrets:**
- **API keys, tokens, passwords** — if visible in screenshots or logs, replace with `[REDACTED_API_KEY]`, `[REDACTED_TOKEN]`, etc. Flag these to the user as a heads-up ("I noticed an API key in the screenshot — I've removed it from the issue.")
- **Session IDs, cookies, auth headers** — redact
- **Database connection strings** — redact

**Infrastructure details (redact unless clearly needed for the bug):**
- **Internal IP addresses** — replace with `[internal_ip]`
- **Internal hostnames / URLs** that expose infrastructure — replace with `[internal_host]`
- **Database names, table names** — keep only if directly relevant to the bug

**Other sensitive content:**
- **Customer data** visible in screenshots (financial info, health info, private messages) — describe the data type without reproducing the actual values (e.g., "the user's transaction history was visible" instead of listing actual transactions)
- **Proprietary business logic** visible in error details — summarize rather than quote verbatim if it reveals trade secrets

**How to handle it in practice:**
- After extracting information in Phase 1, do a sweep for all of the above before composing the issue body.
- When you redact something, note it briefly in the proposal so the user can see what was removed and override if needed (e.g., "Note: removed reporter's email address and an exposed API key from the issue body").
- If the input is heavily loaded with sensitive data and redacting it would make the bug report meaningless, flag this to the user: "This report contains a lot of sensitive details. Want me to create a more generic description, or would you prefer a private/internal issue?"
- When in doubt, redact. It's easy for the user to add information back; it's hard to un-leak something posted publicly.

### Phase 2: Detect Templates and Propose Issues

#### Template Detection

Check the repo for issue templates:

```bash
# Check for issue templates in common locations
ls .github/ISSUE_TEMPLATE/ 2>/dev/null
cat .github/ISSUE_TEMPLATE/*.md 2>/dev/null
cat .github/ISSUE_TEMPLATE/*.yml 2>/dev/null
# Also check for a simple issue template
cat .github/ISSUE_TEMPLATE.md 2>/dev/null
```

If templates exist, read them and use their structure for the proposed issues. Match each issue to the most appropriate template (e.g., bug report template for bugs, feature request template for enhancements).

If no templates exist, use this default structure:

```markdown
## Description
[Clear description of the issue]

## Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Environment
- OS: [if known]
- Browser/Version: [if known]
- App Version: [if known]

## Additional Context
[Screenshots, logs, related issues]
```

#### Check for Existing Issues

Before proposing new issues, search for potentially related open issues:

```bash
gh issue list --state open --limit 30
```

If any existing issues look related to the extracted information, propose updating them instead of creating duplicates. Use keyword matching on titles and bodies — err on the side of flagging potential duplicates for the user to decide.

#### Present the Proposal

Show the user a clear, numbered list of proposed actions. For each:

```
### Issue [N]: [Create new | Update #existing-number]

**Title**: [issue title]
**Labels**: `bug`, `ui` (etc.)
**Template**: [template name if using repo template, or "default"]

**Body preview**:
> [Show the full issue body as it will appear on GitHub]

---
```

If proposing updates to existing issues, show what will be added (as a comment or body edit) and link to the existing issue.

End with a clear prompt:

> **Does this look right?** You can:
> - Say **"go"** or **"approve"** to create/update all issues as shown
> - Say **"skip 2"** to exclude a specific issue
> - Ask me to modify any issue before creating it
> - Say **"cancel"** to abort

**Do not proceed until the user explicitly approves.** This is critical — creating issues is a visible action that others will see.

### Phase 3: Create / Update Issues

Once approved, execute the actions using `gh`:

**Creating a new issue:**
```bash
gh issue create --title "TITLE" --body "$(cat <<'ISSUE_BODY'
... issue body ...
ISSUE_BODY
)" --label "bug,ui"
```

**Updating an existing issue (add a comment):**
```bash
gh issue comment ISSUE_NUMBER --body "$(cat <<'COMMENT_BODY'
... update content ...
COMMENT_BODY
)"
```

**Adding labels to an existing issue:**
```bash
gh issue edit ISSUE_NUMBER --add-label "label1,label2"
```

After each action, confirm success and report the issue URL back to the user. At the end, provide a summary:

> **Done!** Created/updated the following issues:
> - #42: Login button unresponsive on mobile Safari
> - #38: (updated) Add dark mode support — added reproduction details

## Important Guidelines

- **Never create issues without approval.** The proposal step is not optional.
- **Preserve original context.** When the input is a screenshot or email, mention the source in the issue body (e.g., "Reported via email on 2026-03-17" or "From screenshot of error dialog"). Don't attach the screenshot itself to the issue unless the user asks — just describe what's visible.
- **One input can yield multiple issues.** A single screenshot might show several problems. A forwarded email might contain a list of bugs. Extract them all as separate issues.
- **Be conservative with labels.** Only suggest labels that clearly apply. If the repo has existing labels, prefer those over inventing new ones. Check with: `gh label list --limit 50`
- **Handle ambiguity by asking.** If you're not sure whether something is a bug or a feature request, or whether two things should be one issue or two, ask the user.
- **YAML template parsing.** Some repos use `.yml` templates with structured fields (type: input, type: textarea, etc.). When you encounter these, map your extracted data to the template's field IDs and format the issue body accordingly, respecting required fields and field types.
