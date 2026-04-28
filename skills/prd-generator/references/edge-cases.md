# Edge Cases

The skill must verify and handle these inputs explicitly:

- **Missing `idea.md`**: stop in Phase 1, ask user for the path; do NOT fabricate a product concept.
- **Missing `validate.md`**: warn the user; offer to proceed with idea.md only OR stop. Default: stop and ask.
- **Existing `prd.md`** (modification mode): always create `prd.backup.YYYYMMDD_HHMMSS.md` before overwrite. Assert the backup exists and is non-empty before writing the new file.
- **Conflicting requirements** between idea.md and validate.md (e.g., idea says "free tier" but validate flags it infeasible): record both in §9 Open Questions & Risks and ask the user to resolve before finalizing.
- **`validate.md` verdict = REJECT or NOT RECOMMENDED**: do not silently generate; surface the verdict and confirm the user still wants a PRD.
- **No technical context in idea.md**: leave §6 Technical Specifications as `TBD` placeholders; do NOT invent a stack.
- **Multiple candidate project folders** in auto-pick mode: list them and ask the user to choose; never pick silently.
- **Project folder outside an `ideas` repo**: skip Phase 6 (README maintenance) and Phase 7 (commit/push) silently; do not error.
- **Mermaid diagram render failure**: validate syntax (no tabs, balanced brackets) before writing. If invalid, fall back to a text bullet flow and flag the issue.
- **Compliance constraints unclear**: ask explicitly in Phase 3; do not assume GDPR/HIPAA/SOC2 applicability.
