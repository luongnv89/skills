---
name: auto-push
description: "Generate a commit message, stage all changes, and push to remote after scanning for secrets, large files, and protected-branch risks. Skip for opening PRs, code review, or cutting releases/tags."
license: MIT
effort: low
metadata:
  version: 1.1.0
  author: "Luong NGUYEN <luongnv89@gmail.com>"
---

# Commit and Push Everything

**CAUTION**: Stage ALL changes, commit, and push to remote. Use only when confident all changes belong together.

## When to Use

Trigger this skill when the user asks to "commit and push everything", "ship this", "auto-push", or otherwise wants a one-shot stage-commit-push for the current working tree. Skip when they want PRs, code review, releases, or tags.

## Prerequisites

- `git` is installed and the current directory is inside a git repository.
- An `origin` remote exists, and the user can push to it.
- `git config user.name` and `user.email` are set, so `git commit` can run.

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

## Instructions

### Step 1: Analyze Changes
Run in parallel:
- `git status` - Show modified/added/deleted/untracked files
- `git diff --stat` - Show change statistics
- `git log -1 --oneline` - Show recent commit for message style

### Step 2: Run Safety Checks

**❌ Record a finding if detected:**
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

**✅ Also check:**
1. `.gitignore`: no path from `git status --porcelain` matches a secret, build-artifact, or temp-file pattern above. If one does, record it as a finding and suggest the `.gitignore` entry.
2. Merge conflicts: `git diff --name-only --diff-filter=U` prints nothing. If it prints a path, record a finding.
3. Branch: if the current branch is `main` or `master`, record a finding.
4. API keys: every `*_API_KEY`, `*_SECRET`, or `*_TOKEN` value in the changed files is a placeholder. If one is a real value, record a finding.

Each match in the first list above is also a finding. A safety check fails when it records at least one finding.

### Step 3: Confirm and Execute

1. Print the dry-run preview below. If a safety check failed, end it with the findings instead of the `Proceeding now` line.
2. If every safety check passed, continue to Step 4. Do not ask a yes/no question.
3. If any safety check failed, list each finding and stop. Continue only after the user explicitly confirms every finding. Never bypass a failed safety check without that confirmation.
```
📊 Changes Summary:
- X files modified, Y added, Z deleted
- Total: +AAA insertions, -BBB deletions

🔒 Safety: ✅ No secrets | ✅ No large files | ⚠️ [warnings]
🌿 Branch: [name] → origin/[name]

Proceeding now: git add . → commit → push
```

### Step 4: Stage Files

Run sequentially:
```bash
git add .
git status --porcelain
```

Check that every path listed in Step 1 is now staged. If a path is missing, or a path appears that the safety checks did not cover, stop and report it.

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
git push
git log -1 --oneline --decorate
```

- If `git commit` fails (for example, a pre-commit hook), print the hook output and stop. Do not retry.
- If `git push` is rejected as non-fast-forward, run `git pull --rebase && git push` once. If the rebase conflicts or the second push fails, stop and report.
- If `git push` succeeds, check that `git log -1 --oneline --decorate` shows the new commit on `origin/[branch]`.

### Step 7: Report the Result

Print the report shown in Expected Output. It opens with the status, then:

- **Evidence:** the checks that ran and what they observed (safety scan, push exit code, `git log` verification).
- **Uncertainty:** what was not checked. CI and remote hooks never run locally. The placeholder test for API keys is a pattern match, not proof. List every finding the user confirmed in Step 3.
- **Decision:** "No approval needed." after a successful push. When blocked, name the user action needed.

## Expected Output

The final report is plain text in this fixed form. If the user asks for another format, keep the four parts in the same order.

On success:

```
✅ Successfully pushed to remote!

Commit: abc1234 feat: add login page with OAuth support
Branch: feature/auth → origin/feature/auth
Files changed: 4 (+112, -8)
Evidence: safety scan 0 findings · git push exit 0 · origin/feature/auth at abc1234
Uncertainty: CI and remote hooks not run; API-key check is pattern-based
Decision: No approval needed.
```

When a safety check fails:

```
❌ Push blocked — secrets detected

  .env: OPENAI_API_KEY=sk-proj-xxxxx (real key)

Evidence: safety scan 1 finding; nothing staged, committed, or pushed
Uncertainty: API-key check is pattern-based; other findings may be false positives
Decision: Remove or rotate the key, then re-run /auto-push, or confirm the finding to continue.
```

## Acceptance Criteria

The skill run is successful when all of the following hold:

- [ ] Working tree synced with origin (`git fetch` ran; rebase clean or stash/pop completed without conflicts)
- [ ] Safety scan reported no secrets, no real API keys, and no large binaries — or the user explicitly confirmed each finding
- [ ] Branch is correct (warned and confirmed if `main`/`master`)
- [ ] Commit message follows the conventional format from Step 5
- [ ] `git push` exited 0 and `git log -1` shows the new commit on the remote-tracking ref
- [ ] Final report printed with commit hash, branch, file counts, Evidence, Uncertainty, and Decision

When grading a run, also check that a reader can use the report:

- **Result is findable:** the first line says pushed or blocked.
- **Facts and assumptions are separate:** Evidence names only checks that ran; Uncertainty names what did not.
- **Claims are traceable:** each claim points to a command result (push exit code, `git log` output, a finding's file path). A clean safety scan does not mean the push succeeded.
- **Next decision is clear:** Decision says "No approval needed." or names the user action.

Agent inspection cannot confirm that a human understood the report. If no human feedback was given, report human understanding as unconfirmed.

## Handle Edge Cases and Errors

For the edge-case table, per-phase step-completion report format, error-handling guidance, and alternative workflows (selective staging, interactive `git add -p`, PR flow), see [`references/edge-cases-and-reports.md`](./references/edge-cases-and-reports.md). Print a step completion report from that file after each step.

Use individual git commands instead if you want more control over what gets committed.
