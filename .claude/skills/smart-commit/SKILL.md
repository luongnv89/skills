---
name: smart-commit
description: Create intelligent git commits with conventional commits format. Use when the user asks to commit changes, make a commit, create a git commit, or says "commit". Analyzes staged/unstaged changes, generates meaningful commit messages following conventional commits spec (feat, fix, docs, style, refactor, test, chore, perf), and ensures safe commit practices.
---

# Smart Commit

Create well-structured git commits with meaningful messages following the Conventional Commits specification.

## Workflow

### 1. Gather Context

Collect git state before committing:

```bash
git branch --show-current      # Current branch
git status --short             # File status overview
git diff --cached --stat       # Staged changes summary
git diff --stat                # Unstaged changes summary
git diff HEAD                  # Full diff of all changes
git log --oneline -5           # Recent commits for style reference
```

### 2. Analyze Changes

Review the diff to understand:
- What files changed and why
- Whether changes are related or should be separate commits
- The type of change (feature, fix, refactor, etc.)

### 3. Stage Files

If unstaged changes should be committed:

```bash
git add <specific-files>       # Stage specific files
```

**Never use `git add -A` or `git add .`** - always stage specific files to avoid accidentally committing secrets or unwanted files.

### 4. Create Commit

Use the provided message if given via arguments: `$ARGUMENTS`

Otherwise, generate a message following Conventional Commits:

```
<type>(<scope>): <short description>

<optional body with more details>
```

**Types:**
- `feat:` - New feature or functionality
- `fix:` - Bug fix
- `docs:` - Documentation only
- `style:` - Formatting, whitespace (no code change)
- `refactor:` - Code restructuring without behavior change
- `test:` - Adding or updating tests
- `chore:` - Maintenance, dependencies, build
- `perf:` - Performance improvements

**Message Guidelines:**
- First line under 72 characters
- Imperative mood ("Add feature" not "Added feature")
- Be specific about what changed and why
- Reference issue numbers if applicable

**Commit command format:**
```bash
git commit -m "$(cat <<'EOF'
type(scope): description

Optional body with details
EOF
)"
```

### 5. Verify

```bash
git status                     # Confirm commit succeeded
```

## Safety Rules

- **Never commit secrets** - Skip .env, credentials, API keys
- **Never use --no-verify** - Unless explicitly requested
- **Never amend commits** - Unless explicitly requested
- **Always verify success** - Check git status after commit
