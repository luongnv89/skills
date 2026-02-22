---
name: prd-generator
version: 1.2.2
description: Generate comprehensive Product Requirements Documents (PRD) from idea validation files. Use when users ask to "create a PRD", "generate product requirements", "write a PRD", or want to turn validated ideas into actionable product specs. Works with idea.md and validate.md files and always reports GitHub links to changed files.
---

# PRD Generator

Generate comprehensive Product Requirements Documents from validated idea files.

## Input

Preferred: project folder path in `$ARGUMENTS` containing:
- `idea.md` - Product concept and technical context (required)
- `validate.md` - Evaluation and recommendations (required)

If path is not provided (auto-pick mode):
1. Reuse the most recent project folder path from this chat/session (typically from idea-validator output).
2. If unavailable, use env var `IDEAS_ROOT` when present.
3. Else check shared marker file `~/.config/ideas-root.txt`.
4. Backward compatibility fallback: `~/.openclaw/ideas-root.txt`.
5. If still unavailable, auto-discover the newest folder containing both `idea.md` + `validate.md` under:
   - `/home/luongnv/workspace/ideas` (default)
   - `/home/luongnv/workspace/idea-2-prd` (legacy fallback)
6. If multiple candidates are plausible, ask user to choose.

## Workflow

### Phase 1: Validate Input

1. Resolve `PROJECT_DIR` (from `$ARGUMENTS` or auto-pick mode above)
2. Check `PROJECT_DIR/idea.md` exists
3. Check `PROJECT_DIR/validate.md` exists
4. If `PROJECT_DIR/prd.md` exists, create backup: `prd.backup.YYYYMMDD_HHMMSS.md`

### Phase 2: Extract Context

From `idea.md`:
- Product name/concept
- Target audience
- Goals & objectives
- Technical context (stack, constraints)

From `validate.md`:
- Verdict and ratings
- Strengths/weaknesses
- Competitors
- Enhanced version suggestions
- Implementation roadmap

### Phase 3: Clarify Requirements

Ask user (if not clear from input files):
- Official product name?
- Business model? (SaaS, marketplace, freemium)
- Target MVP timeframe?
- Team size/composition?
- Compliance requirements? (GDPR, HIPAA, SOC2)

### Phase 4: Generate PRD

Create `prd.md` with these sections:

1. **Product Overview** - Vision, users, objectives, success metrics
2. **User Personas** - 2-3 detailed personas from target audience
3. **Feature Requirements** - Matrix with MoSCoW prioritization, user stories, acceptance criteria
4. **User Flows** - Primary flows with mermaid diagrams
5. **Non-Functional Requirements** - Performance, security, compatibility, accessibility
6. **Technical Specifications** - Architecture diagram, frontend/backend/infrastructure specs
7. **Analytics & Monitoring** - Key metrics, events, dashboards, alerts
8. **Release Planning** - MVP and version roadmap with checklists
9. **Open Questions & Risks** - Questions, assumptions, risk mitigation
10. **Appendix** - Competitive analysis, glossary, revision history

See [references/prd-template.md](references/prd-template.md) for full template structure.

### Phase 5: Output

1. Write `prd.md` to project folder
2. Summarize sections created
3. Highlight areas needing user review
4. Suggest next steps

### Phase 6: README Maintenance (ideas repo)

After writing `prd.md`, if the project folder is inside an `ideas` repo, update the repo README ideas table:
- Preferred: `cd` to the repo root and run `python3 scripts/update_readme_ideas_index.py` (if it exists)
- Fallback: update `README.md` manually (ensure PRD status becomes ✅ for that idea)

### Phase 7: Commit and push (mandatory)

- Commit immediately after updates.
- Push immediately to remote.
- If push is rejected: `git fetch origin && git rebase origin/main && git push`.

Do not ask for additional push permission once this skill is invoked.

## Reporting with GitHub links (mandatory)
When reporting completion, include:
- GitHub link to `prd.md`
- GitHub link to `README.md` when it was updated
- Commit hash

Link format:
- `https://github.com/luongnv89/ideas/blob/main/<relative-path>`

## Modification Mode

If user wants to modify existing PRD:
1. Create timestamped backup
2. Ask what to modify (features, priorities, timeline, specs, personas)
3. Apply changes preserving structure
4. Update revision history

## Guidelines

- **Thorough**: Cover all sections comprehensively
- **Realistic**: Base on validate.md feasibility ratings
- **Specific**: Include concrete metrics and criteria
- **Actionable**: Every section guides implementation
- **Visual**: Include mermaid diagrams for architecture and flows
