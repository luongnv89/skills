---
name: auto-push
description: "Generate a commit message, stage all changes, and push to remote after scanning for secrets, large files, and protected-branch risks. Skip for opening PRs, code review, or cutting releases/tags."
license: MIT
effort: low
metadata:
  version: 1.0.2
  author: Luong NGUYEN <luongnv89@gmail.com>
---

# Commit and Push Everything

**CAUTION**: Stage ALL changes, commit, and push to remote. Use only when confident all changes belong together.

## When to Use

Trigger this skill when the user asks to "commit and push everything", "ship this", "auto-push", or otherwise wants a one-shot stage-commit-push for the current working tree. Skip when they want PRs, code review, releases, or tags.

## Sync Repo Before Edits
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

## Instructions

### Step 1: Analyze Changes
Run in parallel:
- `git status` - Show modified/added/deleted/untracked files
- `git diff --stat` - Show change statistics
- `git log -1 --oneline` - Show recent commit for message style

### Step 2: Run Safety Checks

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

### Step 3: Confirm and Execute

Present a short summary as a dry-run preview, then proceed directly when safety checks pass. If any safety check fails, STOP and ask for explicit user confirmation before continuing — never bypass a failed safety check without a confirmation prompt.
```
📊 Changes Summary:
- X files modified, Y added, Z deleted
- Total: +AAA insertions, -BBB deletions

🔒 Safety: ✅ No secrets | ✅ No large files | ⚠️ [warnings]
🌿 Branch: [name] → origin/[name]

Proceeding now: git add . → commit → push
```

When all safety checks pass, proceed directly without an additional yes/no confirmation prompt.

### Step 4: Stage Files

Run sequentially:
```bash
git add .
git status  # Verify staging
```

### Step 5: Generate Commit Message

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

### Step 6: Commit and Push

```bash
git commit -m "$(cat <<'EOF'
[Generated commit message]
EOF
)"
git push  # If fails: git pull --rebase && git push
git log -1 --oneline --decorate  # Verify
```

### Step 7: Report Success

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

## Acceptance Criteria

The skill run is successful when all of the following hold:

- [ ] Working tree synced with origin (`git fetch` ran; rebase clean or stash/pop completed without conflicts)
- [ ] Safety scan reported no secrets, no real API keys, and no large binaries — or the user explicitly confirmed each warning
- [ ] Branch is correct (warned and confirmed if `main`/`master`)
- [ ] Commit message follows the conventional format from Step 5
- [ ] `git push` exited 0 and `git log -1` shows the new commit on the remote-tracking ref
- [ ] Final success report printed (commit hash, branch, file counts)

## Handle Edge Cases and Errors

For the edge-case table, per-phase step-completion report format, error-handling guidance, and alternative workflows (selective staging, interactive `git add -p`, PR flow), see [`references/edge-cases-and-reports.md`](./references/edge-cases-and-reports.md).

**Remember**: Always review changes before pushing. When in doubt, use individual git commands for more control.
