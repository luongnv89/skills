# Verification Steps

Run these checks in Phase 5, after writing `prd.md`. Record each observed count for the Final Report's `Evidence:` line. A check that fails gets one regeneration of its section; a second failure makes the run `PARTIAL`.

1. `test -f "$PROJECT_DIR/prd.md"` — exits 0 (file exists).
2. `grep -c '^## ' "$PROJECT_DIR/prd.md"` — returns >= 10 (top-level sections).
3. `grep -Ec 'Given .*When .*Then' "$PROJECT_DIR/prd.md"` — returns >= 1 (acceptance criteria).
4. `grep -c '^```mermaid' "$PROJECT_DIR/prd.md"` — returns >= 1 (diagram blocks).
5. `grep -Ec '\b(Must|Should|Could|Won.t)\b' "$PROJECT_DIR/prd.md"` — returns >= 5 (MoSCoW-labeled lines).
6. `grep -c 'idea.md' "$PROJECT_DIR/prd.md"` — returns >= 1 (source attribution).
7. Only when a prior `prd.md` existed: `test -s "$PROJECT_DIR"/prd.backup.<timestamp>.md` for the backup this run wrote — exits 0 (backup present and non-empty). Otherwise record this check as `n/a`.

These checks establish only the counts they measure. They do not prove that the personas are realistic or that the metrics are achievable; leave those judgments to the user's review.
