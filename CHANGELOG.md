# Changelog

## v1.9.0 — 2026-03-20

### New Skills
| Skill | Version |
|-------|---------|
| opencode-runner | 1.2.0 |
| appstore-review-checker | 1.0.0 |

### Features
- **opencode-runner**: Delegate coding tasks to opencode using free cloud models with automatic model selection (minimax > kimi > glm > MiMo > Big Pickle), mandatory process cleanup, and progress monitoring
- **appstore-review-checker**: Audit apps against Apple's App Store Review Guidelines
- **name-checker**: Add package registry checks (npm, PyPI, Homebrew, apt) for comprehensive name availability

### Skills Updated
| Skill | Version Change |
|-------|---------------|
| name-checker | 1.0.1 → 1.1.0 |

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.8.0...v1.9.0

## v1.8.0 — 2026-03-20

### Features
- **excalidraw-generator**: adopt dark neon theme and Helvetica font for all diagrams

### New Skills
| Skill | Version |
|-------|---------|
| github-issue-creator | 1.0.0 |

### Documentation
- Add installation instructions (npx + asm) to all 32 skill READMEs
- Fix asm install command format to `github:luongnv89/skills:skills/<name>`

### Skills Updated
| Skill | Version Change |
|-------|---------------|
| excalidraw-generator | 1.1.1 → 1.2.0 |

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.7.0...v1.8.0

## v1.7.0 — 2026-03-18

### Features
- Add **readme-to-landing-page** skill — transform any project README into a persuasive, landing-page-structured markdown using proven copywriting frameworks (PAS, AIDA, StoryBrand) @luongnv89

### Bug Fixes
- **logo-designer**: update default brand palette to dark theme with neon green accent (#0A0A0A, #111111, #262626, #A1A1A1, #FAFAFA, #00FF41) and Inter font
- **README**: add missing readme-to-landing-page skill entry

### Documentation
- Rewrite README as a landing page with PAS copywriting framework

### Other Changes
- Add GitHub issue template for new skill proposals
- Add `.gstack/` and `*-workspace/` to .gitignore

### New Skills
| Skill | Version |
|-------|---------|
| readme-to-landing-page | 1.0.0 |

### Skills Updated
| Skill | Version Change |
|-------|---------------|
| logo-designer | 1.1.0 → 1.2.0 |

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.6.2...v1.7.0

## v1.6.2 — 2026-03-18

### Bug Fixes
- **skill audit**: comprehensive quality audit and fix across all 30 skills @luongnv89
  - Remove embedded test/validation sections from seo-ai-optimizer and vscode-extension-publisher SKILL.md (91 lines of non-runtime content)
  - Remove dangling script references in idea-validator and note-taker
  - Remove committed `__pycache__/*.pyc` files from skill-creator
  - Fix auto-push README diagram contradicting no-confirmation behavior
  - Trim overly long descriptions on 8 skills (release-manager, excalidraw-generator, drawio-generator, aso-marketing, theme-transformer, note-taker, idea-validator, prd-generator)
  - Extract `references/publishing.md` from release-manager to get body under 500 lines
  - Add missing Go, Rust, and Java language-specific checks to code-optimizer
  - Standardize repo sync block to canonical full form across 6 skills (aso-marketing, release-manager, ollama-optimizer, name-checker, context-hub, code-review)
  - Add explicit read-on-demand cues for reference files (code-review, openspec-task-loop, prd-generator)
  - Fix README resource tables to list specific files (system-design, tasks-generator, code-review, devops-pipeline)
  - Fix name-checker "CRITICAL: STOP" wording to actionable skip instruction
  - Remove decorative padding sections (agent-config Notes, system-design Design Principles)
  - Fix logo-designer conflicting design principles (no gradients vs shadows)
  - Remove motivational non-instructional line from frontend-design
  - Clarify docs-generator commit behavior and branch detection
  - Move drawio-generator "Advantages Over Excalidraw" to README
  - Collapse excalidraw-generator redundant JSON section to pointer
  - Clarify ollama-optimizer output path and benchmark expectations
  - Add missing branch creation step to oss-ready README diagram
  - Add read-on-demand cues for unreferenced files in skill-creator

### Skills Updated (30 files changed, -227 lines net)
| Skill | Change |
|-------|--------|
| agent-config | Remove filler Notes section |
| aso-marketing | Trim description, standardize repo sync |
| auto-push | Fix README diagram |
| cli-builder | (no content change — reviewed, passed) |
| code-optimizer | Add Go/Rust/Java checks, rename Step 0 |
| code-review | Standardize repo sync, read-on-demand cue, fix README |
| context-hub | Standardize repo sync |
| devops-pipeline | Fix README resource table |
| docs-generator | Clarify branch detection and commit behavior |
| drawio-generator | Trim description, remove Advantages section |
| excalidraw-generator | Trim description, collapse redundant section |
| frontend-design | Remove motivational line |
| idea-validator | Trim description, remove missing script ref |
| logo-designer | Fix conflicting design principles |
| name-checker | Standardize repo sync, fix STOP wording |
| note-taker | Trim description, remove missing script ref |
| ollama-optimizer | Standardize repo sync, clarify output/benchmark |
| openspec-task-loop | Add read-on-demand cue |
| oss-ready | Fix README diagram |
| prd-generator | Trim description, add read-on-demand cue |
| release-manager | Trim description, standardize repo sync, extract publishing to references/ |
| seo-ai-optimizer | Remove embedded test cases |
| skill-creator | Remove __pycache__, add reference cues |
| system-design | Remove Design Principles padding, fix README |
| tasks-generator | Fix README resource table |
| theme-transformer | Trim description |
| vscode-extension-publisher | Remove embedded test cases |

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.6.1...v1.6.2

## v1.6.1 — 2026-03-18

### Bug Fixes
- **skill consistency**: audit and fix skill consistency issues across 4 skills @luongnv89
  - excalidraw-generator: add missing metadata.version, fix README mermaid check count (9 → 10)
  - drawio-generator: add missing metadata.version
  - cli-builder: replace non-standard README sections with standard Output
- **SKILL.md frontmatter**: migrate from unsupported `version:` attribute to valid `metadata.version` across all 30 skills @luongnv89
  - Add `license: MIT` and `metadata.creator` to every skill
  - Valid frontmatter attributes now: argument-hint, compatibility, description, disable-model-invocation, license, metadata, name, user-invocable

### Skills Updated
| Skill | Version Change |
|-------|---------------|
| excalidraw-generator | 1.1.0 → 1.1.1 |
| drawio-generator | 1.0.0 → 1.0.1 |

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.6.0...v1.6.1

## v1.6.0 — 2026-03-18

### Features
- Add **drawio-generator** skill — generate diagrams and visualizations as draw.io (diagrams.net) XML files with a 4-phase workflow (Understand → Propose → Generate → Validate) @luongnv89
  - Supports **25+ diagram types**: flowcharts, C4 models, ER diagrams, swimlanes, architecture, and more
  - **Multi-page support** — multiple C4 levels or related diagrams in a single `.drawio` file
  - **9 automated quality checks**: XML validation, required attributes, unique IDs, edge bindings, overlap detection, container hierarchy, semantic completeness, text readability
  - Native `.drawio` output compatible with diagrams.net, VS Code, Confluence, and Jira
  - Comprehensive reference docs for draw.io XML schema, shapes, styles, and color palettes

### Bug Fixes
- **excalidraw-generator**: fix text rendering — add Check 10 (shape-to-text size fit), require `autoResize: true` and `lineHeight: 1.25`, boundary labels must be standalone text
- **excalidraw-generator**: default output changed to `.excalidraw` (raw JSON) instead of `.excalidraw.md`

### New Skills
| Skill | Version |
|-------|---------|
| drawio-generator | 1.0.0 |

### Skills Updated
| Skill | Version Change |
|-------|---------------|
| excalidraw-generator | 1.0.0 → 1.1.0 |

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.5.0...v1.6.0

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
