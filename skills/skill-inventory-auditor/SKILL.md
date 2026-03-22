---
name: skill-inventory-auditor
description: Audit all installed agent skills across global and project scopes to find and remove duplicate skills. Use when asked to "audit my skills", "check for duplicate skills", "clean up skills", "deduplicate skills", "find duplicate skills", or when the user wants to find and remove duplicated skill installations.
effort: low
license: MIT
metadata:
  version: 1.0.0
  creator: Luong NGUYEN <luongnv89@gmail.com>
---

# Skill Inventory Auditor

Find and remove duplicate skills across installed skill directories.

## Repo Sync Before Edits (mandatory)

Before removing skills from git-tracked directories, sync the current branch with remote:

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

### Phase 1: Scan

Run the duplicate scanner with scope `both` (default) unless the user specifies otherwise:

```bash
python3 {SKILL_DIR}/scripts/scan_inventory.py --scope both --project-dir {cwd}
```

Scopes: `global` (`~/.claude/skills/`, `~/.agents/skills/`), `project` (`.claude/skills/`), or `both`.

Parse the JSON output. If the script fails, report the error and stop.

### Phase 2: Report Duplicates

If no duplicates are found, say so and stop.

For each duplicate group:

1. Present a table with skill name, location, version, and description excerpt
2. Show the similarity score between descriptions
3. Explain why they were flagged (same name or similar description)
4. Recommend which to keep based on:
   - Higher version number
   - More descriptive name
   - Richer feature set (more scripts/files)
   - Location preference (project-local skills may override global)

Ask the user which skills to keep/remove for each group. Wait for confirmation.

### Phase 3: Remove Duplicates

Present a summary of planned removals, then ask for confirmation.

**Symlink removal** (preserves the source):
```bash
rm {symlink_path}
```

**Directory removal**:
```bash
rm -rf {directory_path}
```

**Safety rules**:
- Always confirm before executing removals
- Print exactly what will be deleted
- Never remove skills from the project source repository (e.g., `skills/` in a git repo)
- When removing a symlink, only the link is deleted — the source remains intact

After removals, rerun the scanner to verify no duplicates remain.

## Important Notes

- This skill only removes installed copies (in `~/.claude/skills/`, `~/.agents/skills/`, or `.claude/skills/`). It never touches source repositories.
- Symlinks between `~/.claude/skills/` and `~/.agents/skills/` pointing to the same target are shared installations, NOT duplicates. The scanner excludes these automatically.
