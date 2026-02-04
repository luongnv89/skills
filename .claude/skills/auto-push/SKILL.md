---
name: auto-push
description: Safely commit and push changes with comprehensive verification. Use when the user asks to "push changes", "auto push", "commit and push", or wants to safely push code to remote. Performs full verification including sensitive data detection, pre-commit hooks, tests, builds, and security checks before committing. Requires user confirmation before pushing.
---

# Auto Push

Safely stage, commit, and push changes with comprehensive verification and user confirmation.

## Phase 1: Discover Changes

### 1.1 Gather Git Context

```bash
git branch --show-current           # Current branch
git status --short                  # File status
git diff --cached --stat            # Staged changes
git diff --stat                     # Unstaged changes
git diff HEAD                       # Full diff
git log --oneline -5                # Recent commits for style
git remote -v                       # Remote info
```

### 1.2 Detect Sensitive Data

Scan all changed files for secrets. **STOP if any detected:**

**File patterns to reject:**
- `.env*`, `*.key`, `*.pem`, `*.p12`, `*.pfx`, `*.cer`
- `credentials.json`, `secrets.yaml`, `id_rsa*`

**Content patterns to reject:**
```
OPENAI_API_KEY=sk-...              # Real API key
AWS_SECRET_ACCESS_KEY=AKIA...      # Real AWS key
STRIPE_API_KEY=sk_live_...         # Real Stripe key
password=<actual-password>          # Hardcoded password
```

**Acceptable placeholders:**
```
API_KEY=your-api-key-here
SECRET_KEY=placeholder
TOKEN=xxx
API_KEY=<your-key>
SECRET=${YOUR_SECRET}
```

### 1.3 Handle Sensitive Files

If sensitive files detected:

1. List the problematic files
2. Check if `.gitignore` covers them
3. If not, **ask user**: "Should I add these patterns to .gitignore?"
   - If yes: Update `.gitignore` and stage it
   - If no: **STOP** - do not proceed with commit

### 1.4 Check for Problematic Files

Warn about (but don't auto-reject):
- Large files >10MB (suggest Git LFS)
- Build artifacts: `node_modules/`, `dist/`, `build/`, `__pycache__/`, `.venv/`
- Temp files: `.DS_Store`, `thumbs.db`, `*.swp`, `*.tmp`

## Phase 2: Verification & Commit

### 2.1 Run Pre-commit Hooks (if applicable)

```bash
# Check if pre-commit exists
if [ -f .pre-commit-config.yaml ]; then
    pre-commit run --all-files
fi

# Or if husky is configured
if [ -d .husky ]; then
    # Hooks run automatically on commit
fi
```

If pre-commit fails: **STOP**, show errors, fix issues first.

### 2.2 Run Tests (if applicable)

Detect and run project tests:

| Project Type | Detection | Command |
|--------------|-----------|---------|
| Node.js | `package.json` with test script | `npm test` |
| Python | `pytest.ini`, `setup.py`, `pyproject.toml` | `pytest` or `python -m pytest` |
| Go | `*_test.go` files | `go test ./...` |
| Rust | `Cargo.toml` | `cargo test` |

If tests fail: **STOP**, show failures, do not commit.

### 2.3 Run Build (if applicable)

| Project Type | Detection | Command |
|--------------|-----------|---------|
| Node.js | `package.json` with build script | `npm run build` |
| TypeScript | `tsconfig.json` | `tsc --noEmit` |
| Go | `go.mod` | `go build ./...` |
| Rust | `Cargo.toml` | `cargo build` |

If build fails: **STOP**, show errors, do not commit.

### 2.4 Security Scan (if tools available)

```bash
# npm audit for Node.js
npm audit --audit-level=high 2>/dev/null

# pip-audit for Python
pip-audit 2>/dev/null

# cargo audit for Rust
cargo audit 2>/dev/null
```

Report high/critical vulnerabilities but don't block (warn user).

### 2.5 Stage Files

Stage specific files (never `git add .` or `git add -A`):

```bash
git add <file1> <file2> ...        # Stage specific files
git status                          # Verify staging
```

### 2.6 Create Commit

Generate message following Conventional Commits:

```
<type>(<scope>): <short description>

<optional body>
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`

```bash
git commit -m "$(cat <<'EOF'
type(scope): description

- Detail 1
- Detail 2
EOF
)"
```

If commit fails (pre-commit hook): Fix and retry, **do not use --no-verify**.

## Phase 3: Push Confirmation

### 3.1 Present Summary

Display to user:

```
📊 Changes Summary:
- X files modified, Y added, Z deleted
- +AAA insertions, -BBB deletions

✅ Verification Results:
- Sensitive data: None detected
- Pre-commit: Passed (or N/A)
- Tests: Passed (or N/A)
- Build: Passed (or N/A)
- Security: No critical issues (or warnings)

🌿 Branch: <branch> → origin/<branch>
📝 Commit: <hash> <message>

Ready to push. Type 'yes' to confirm or 'no' to cancel.
```

### 3.2 Wait for Confirmation

**WAIT for explicit "yes"** before pushing. Do not proceed on any other input.

### 3.3 Execute Push

```bash
git push
# If fails with non-fast-forward:
git pull --rebase && git push

# If no upstream:
git push -u origin <branch>
```

### 3.4 Confirm Success

```
✅ Successfully pushed!

Commit: <hash> <message>
Branch: <branch> → origin/<branch>
Files: X changed (+insertions, -deletions)
```

## Error Handling

| Error | Solution |
|-------|----------|
| Sensitive data found | Add to .gitignore (with user permission) |
| Pre-commit fails | Fix issues, do not bypass |
| Tests fail | Fix tests before committing |
| Build fails | Fix build errors |
| Push rejected | `git pull --rebase && git push` |
| No upstream | `git push -u origin <branch>` |
| Protected branch | Suggest PR workflow |

## Safety Rules

- **Never commit secrets** - Always scan and reject
- **Never use --no-verify** - Unless explicitly requested
- **Never force push** - Unless explicitly requested
- **Never push without confirmation** - Always wait for "yes"
- **Always update .gitignore** - With user permission for sensitive patterns
