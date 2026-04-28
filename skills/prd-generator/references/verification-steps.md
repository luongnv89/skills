# Verification Steps

Run these checks after generation; each should pass before declaring the run complete:

1. `test -f "$PROJECT_DIR/prd.md"` — file exists.
2. `grep -c '^## ' "$PROJECT_DIR/prd.md"` — returns >= 10.
3. `grep -E 'Given .* When .* Then' "$PROJECT_DIR/prd.md" | wc -l` — returns >= 1.
4. `grep -c 'mermaid' "$PROJECT_DIR/prd.md"` — returns >= 1.
5. `grep -Ec '(Must|Should|Could|Won.t)' "$PROJECT_DIR/prd.md"` — returns >= 4.
6. `grep -c 'idea.md' "$PROJECT_DIR/prd.md"` — returns >= 1 (source attribution).
7. If a prior prd.md existed: `ls "$PROJECT_DIR"/prd.backup.*.md` — at least one backup file present.
