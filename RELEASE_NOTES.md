# Release Notes

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
