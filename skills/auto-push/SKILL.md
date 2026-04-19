---
name: auto-push
description: Stage all changes, commit with a generated message, and push to remote — with safety checks for secrets, large files, and protected branches. Executes immediately after checks pass; no extra confirmation needed.
effort: low
license: MIT
metadata:
  version: 1.0.1
  creator: Luong NGUYEN <luongnv89@gmail.com>
---

# Commit and Push Everything

⚠️ **CAUTION**: Stage ALL changes, commit, and push to remote. Use only when confident all changes belong together.

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

## Workflow

### 1. Analyze Changes
Run in parallel:
- `git status` - Show modified/added/deleted/untracked files
- `git diff --stat` - Show change statistics
- `git log -1 --oneline` - Show recent commit for message style

### 2. Safety Checks

**❌ STOP and WARN if detected:**
- Secrets: `.env*`, `*.key`, `*.pem`, `credentials.json`, `secrets.yaml`, `id_rsa`, `*.p12`, `*.pfx`, `*.cer`
- API Keys: Any `*_API_KEY`, `*_SECRET`, `*_TOKEN` variables with real values (not placeholders like `your-api-key`, `xxx`, `placeholder`)
- Large files: `>10MB` without Git LFS
- Build artifacts: `node_modules/`, `dist/`, `build/`, `__pycache__/`, `*.pyc`, `.venv/`
- Temp files: `.DS_Store`, `thumbs.db`, `*.swp`, `*.tmp`

**API Key Validation:**
Check modified files for patterns like:
```bash
OPENAI_API_KEY=sk-proj-xxxxx  # ❌ Real key detected!
AWS_SECRET_KEY=AKIA...         # ❌ Real key detected!
STRIPE_API_KEY=sk_live_...    # ❌ Real key detected!

# ✅ Acceptable placeholders:
API_KEY=your-api-key-here
SECRET_KEY=placeholder
TOKEN=xxx
API_KEY=<your-key>
SECRET=${YOUR_SECRET}
```

**✅ Verify:**
- `.gitignore` properly configured
- No merge conflicts
- Correct branch (warn if main/master)
- API keys are placeholders only

### 3. Execute Immediately (No Extra Confirmation)

Present a short summary, then proceed directly when safety checks pass:
```
📊 Changes Summary:
- X files modified, Y added, Z deleted
- Total: +AAA insertions, -BBB deletions

🔒 Safety: ✅ No secrets | ✅ No large files | ⚠️ [warnings]
🌿 Branch: [name] → origin/[name]

Proceeding now: git add . → commit → push
```

Do not ask for additional yes/no confirmation after this skill is invoked.

### 4. Execute

Run sequentially:
```bash
git add .
git status  # Verify staging
```

### 5. Generate Commit Message

Analyze changes and create conventional commit:

**Format:**
```
[type]: Brief summary (max 72 characters)

- Key change 1
- Key change 2
- Key change 3
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `build`, `ci`

**Example:**
```
docs: Update concept README files with comprehensive documentation

- Add architecture diagrams and tables
- Include practical examples
- Expand best practices sections
```

### 6. Commit and Push

```bash
git commit -m "$(cat <<'EOF'
[Generated commit message]
EOF
)"
git push  # If fails: git pull --rebase && git push
git log -1 --oneline --decorate  # Verify
```

### 7. Confirm Success

```
✅ Successfully pushed to remote!

Commit: [hash] [message]
Branch: [branch] → origin/[branch]
Files changed: X (+insertions, -deletions)
```

## Expected Output

On success, the skill outputs a confirmation block:

```
✅ Successfully pushed to remote!

Commit: abc1234 feat: add login page with OAuth support
Branch: feature/auth → origin/feature/auth
Files changed: 4 (+112, -8)
```

If safety checks block the push, the skill outputs:

```
❌ Push blocked — secrets detected

  .env: OPENAI_API_KEY=sk-proj-xxxxx (real key)

Action required: remove or rotate the key, then re-run /auto-push.
```

## Edge Cases

| Scenario | Handling |
|---|---|
| Merge conflict detected | Stop; show conflicting files; tell user to resolve conflicts then re-run |
| Protected branch (main/master) | Warn with a 🔴 banner; recommend creating a branch and using a PR instead |
| Empty commit (nothing staged) | Detect with `git status`; report "nothing to commit" and exit cleanly |
| No remote configured | Report "no remote origin"; suggest `git remote add origin <url>` |
| Push rejected (non-fast-forward) | Run `git pull --rebase && git push`; if rebase fails, stop and report |
| Pre-commit hook fails | Surface hook output; do not retry; ask user to fix the hook issue |
| Binary or large file (>10 MB) | Block and suggest Git LFS; do not stage the file |

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

**Phase: Analyze Changes** — checks: `Modified files listed`, `Change statistics available`, `Recent commit style identified`

**Phase: Safety Checks** — checks: `Safety scan`, `Secret detection`, `Large file check`, `Branch warning (main/master)`

**Phase: Commit** — checks: `Staging complete`, `Commit message conventional`, `No merge conflicts`

**Phase: Push** — checks: `Push success`, `Remote branch exists`, `Final log verified`

## Error Handling

- **git add fails**: Check permissions, locked files, verify repo initialized
- **git commit fails**: Fix pre-commit hooks, check git config (user.name/email)
- **git push fails**:
  - Non-fast-forward: `git pull --rebase && git push`
  - No remote branch: `git push -u origin [branch]`
  - Protected branch: Use PR workflow instead

## Alternatives

If user wants control, suggest:
1. **Selective staging**: Review/stage specific files
2. **Interactive staging**: `git add -p` for patch selection
3. **PR workflow**: Create branch → push → PR (use `/pr` command)

**⚠️ Remember**: Always review changes before pushing. When in doubt, use individual git commands for more control.
