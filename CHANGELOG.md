# Changelog

## v1.5.0 — 2026-03-17

### Features
- Add **excalidraw-generator** skill — generate diagrams, charts, and visualizations as valid Excalidraw JSON with a 4-phase workflow (Understand → Propose → Generate → Validate) @luongnv89
  - Supports **25+ diagram types** across 8 categories: flowcharts, architecture, ER diagrams, mind maps, sequence diagrams, Gantt charts, Kanban boards, SWOT analysis, wireframes, and more
  - **9 automated quality checks** with auto-fix: JSON validation, required fields, unique IDs, two-way text/arrow bindings, overlap detection, semantic completeness, readable text
  - Selectable **color palettes** (Professional, Pastel, Monochrome) and **rendering styles** (Hand-drawn, Clean, Sketchy)
  - Outputs `.excalidraw.md` (Markdown with code block) by default, or raw `.excalidraw` files
  - Comprehensive reference docs for Excalidraw JSON schema and all diagram type layouts

### New Skills
| Skill | Version |
|-------|---------|
| excalidraw-generator | 1.0.0 |

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.4.0...v1.5.0

## v1.4.0 — 2026-03-17

### Features
- Add **store policy compliance checking** to aso-marketing skill — validates all proposed metadata against Apple App Store Review Guidelines (2.3.7, 2.3.8, 5.2.1) and Google Play metadata policies before submission @luongnv89
  - New **Phase 3: Policy Compliance Check** — scans for prohibited keywords, trademark/competitor brand violations, formatting issues, and content accuracy
  - Comprehensive **prohibited keyword lists** for both stores (e.g., "free", "best", "#1", "top", "download now")
  - **Trademark protection** — prevents competitor brand names from leaking into proposed metadata
  - Policy compliance integrated into Review (Phase 5), Verify (Phase 6), and Summary Report (Phase 7)
  - New **Store Policy Compliance** section in best practices reference with universal comparison table
  - Updated evals with policy compliance assertions

### Skills Updated
| Skill | Version Change |
|-------|---------------|
| aso-marketing | 1.0.0 → 1.1.0 |

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.3.0...v1.4.0

## v1.3.0 — 2026-03-17

### Features
- Add **aso-marketing** skill — full-lifecycle App Store Optimization for mobile apps covering both Apple App Store and Google Play with keyword strategy, metadata optimization, conversion improvement, and localization @luongnv89
- Add **Skill Management** section to README referencing [agent-skill-manager](https://github.com/luongnv89/agent-skill-manager) (`asm`) for managing skills across all AI coding agents @luongnv89
- Add Marketing phase to the workflow diagram and skill tables @luongnv89

### New Skills
| Skill | Version |
|-------|---------|
| aso-marketing | 1.0.0 |

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.2.0...v1.3.0

## v1.2.0 — 2026-03-13

### Features
- Add "Install All" tools option to install.sh and remote-install.sh with shared `.agents/skills/` + symlinks @luongnv89
- Add remote installer and update README with all installation methods @luongnv89
- Add Step 6 (Update Documentation) and Step 10 (Publish to PyPI/npm) to release-manager skill @luongnv89

### Skills Updated
| Skill | Version Change |
|-------|---------------|
| release-manager | 2.1.0 → 2.2.0 |

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.1.3...v1.2.0

## v1.1.3 — 2026-03-11

### Bug Fixes
- Update release-manager to use CHANGELOG.md instead of RELEASE_NOTES.md @luongnv89

### Skills Updated
| Skill | Version Change |
|-------|---------------|
| release-manager | 2.0.0 → 2.1.0 |

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.1.2...v1.1.3

## v1.1.2 — 2026-03-11

### Bug Fixes
- Audit and fix frontmatter, repo-sync, and hardcoded paths across 15 skills (38a74c4) @luongnv89

### Skills Updated
| Skill | Change |
|-------|--------|
| cli-builder | Added `version: 1.0.0`, fixed multi-line description |
| install-script-generator | Fixed multi-line description |
| release-manager | Fixed multi-line description |
| auto-push | Added `version: 1.0.0` |
| context-hub | Added `version: 1.0.0` |
| theme-transformer | Added `version: 1.0.0`, removed unnecessary YAML quoting |
| oss-ready | Added missing H1 title |
| seo-ai-optimizer | Added missing Repo Sync Before Edits section |
| skill-inventory-auditor | Added missing Repo Sync Before Edits section |
| idea-validator | Replaced hardcoded paths/URLs with dynamic resolution |
| prd-generator | Replaced hardcoded paths/URLs with dynamic resolution |
| tasks-generator | Replaced hardcoded paths/URLs with dynamic resolution |
| system-design | Replaced hardcoded GitHub URL with dynamic resolution |
| ollama-optimizer | Removed stale generated output file |
| skill-creator | Standardized README.md to match catalog template |

### README
- Updated version table to match actual SKILL.md versions
- Added missing cli-builder and vscode-extension-publisher entries

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.1.1...v1.1.2

## v1.1.1 — 2026-03-11

### Bug Fixes
- Require single-line description in skill-creator for correct external parsing (3fde564) @luongnv89

### Skills Updated
| Skill | Change |
|-------|--------|
| skill-creator | Added single-line description validation in SKILL.md guide and quick_validate.py |

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.1.0...v1.1.1

## v1.1.0 — 2026-03-11

### Features
- Rename release-notes to **release-manager** with full release automation (2cf22aa) @luongnv89
- Add **skill-inventory-auditor** for finding and removing duplicate skills (d7cb4dd) @luongnv89

### Bug Fixes
- Enforce standard compliance across 6 skills — added repo sync and reference sections (1376208) @luongnv89

### Skills Updated
| Skill | Version Change |
|-------|---------------|
| release-manager | 1.0.0 → 2.0.0 (renamed from release-notes) |
| skill-inventory-auditor | New — 1.0.0 |
| code-review | 1.0.0 → 1.0.1 |
| name-checker | 1.0.0 → 1.0.1 |
| ollama-optimizer | 1.0.0 → 1.0.1 |
| seo-ai-optimizer | 1.0.0 → 1.0.1 |
| skill-creator | 1.0.0 → 1.0.1 |

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.0.0...v1.1.0

## v1.0.0 — Initial Release

First stable release with 20+ skills for AI agents.
