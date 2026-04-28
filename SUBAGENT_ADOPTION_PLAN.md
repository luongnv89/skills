# Subagent Architecture Adoption Plan

> Review of all 35 skills in `skills/` against the subagent patterns guide (`references/subagent-patterns.md`), with prioritized recommendations for adoption.

**Date**: 2026-03-24 (Adoption Plan created)
**Reviewed by**: 5 parallel reviewer agents analyzing batches of 7 skills each

**Status Update (2026-03-25)**:
- ✅ **Documentation phase complete**: All 11 HIGH-priority skills now have complete SKILL.md documentation with subagent architecture, Environment Check sections, and README Resources tables listing all agent files
- ✅ **Agent files identified**: 47 total agent files referenced across 11 HIGH-priority skills
- ✅ **Placeholders ready**: All agent file paths created as stubs in respective skill directories
- 🔄 **Next phase**: Implement agent file content (starting with appstore-review-checker, excalidraw-generator, drawio-generator)

---

## Executive Summary

- **35 skills reviewed**
- **11 HIGH priority** candidates for subagent adoption
- **10 MEDIUM priority** candidates (beneficial but not urgent)
- **14 LOW priority** (no meaningful benefit or already well-architected)
- **2 skills already use subagents** (skill-creator, release-manager)
- **Most common pattern**: Review Loop (Pattern C) — 9 skills would benefit from fresh-context reviewers

---

## Subagent Patterns Reference

| Pattern | Description | Best For |
|---|---|---|
| **A: Explorer+Executor** | One subagent researches, main agent decides, another executes | Codebase analysis → action workflows |
| **B: Parallel Workers** | Multiple subagents handle independent chunks simultaneously | Batch processing, multi-file transforms |
| **C: Review Loop** | Creator + independent reviewer alternate until quality is met | Output quality assurance, validation |
| **D: Research+Synthesis** | Multiple researchers gather info, synthesizer combines findings | Multi-source information gathering |
| **E: Staged Pipeline** | Each stage produces intermediate artifact for the next | Document processing, data transforms |

---

## HIGH Priority — Should Adopt Subagents

### 1. appstore-review-checker (Score: 5/5)

**Pattern**: A (Explorer+Executor) + C (Review Loop)

**Why**: Reads 5-10 large project files (project.pbxproj, Info.plist, entitlements, source code) and applies 150+ guidelines. Single-context approach regularly hits compression issues on real iOS projects.

**Subagents to create**:
| Agent File | Role |
|---|---|
| `agents/project-explorer.md` | Read all project config and source files, build structured app profile JSON |
| `agents/guideline-auditor.md` | Apply 150+ guidelines against the app profile, return per-guideline verdicts |
| `agents/report-writer.md` | Format audit JSON into the exact report template (`APPSTORE_AUDIT.md`) |
| `agents/fixer.md` | Apply code-level fixes for user-approved FAIL items |

**SKILL.md changes**: Phase 1 → explorer subagent. Phase 2 → guideline-auditor subagent. Phase 3 → report-writer subagent. Phase 4 → fixer subagent. Main agent never reads source files or guidelines directly.

**Risk**: Explorer must be exhaustive — missed files cause false-negatives in the auditor. Fixer should be capped to code-level fixes only; metadata fixes stay as human checklists.

---

### 2. seo-ai-optimizer (Score: 5/5)

**Pattern**: D (Research+Synthesis) + E (Staged Pipeline)

**Why**: 7 explicit steps mixing file scan, web search, code generation, and validation — all accumulating in one context. Highest stated effort level ("high").

**Subagents to create**:
| Agent File | Role |
|---|---|
| `agents/auditor.md` | Run audit script + manual review checklist, return structured JSON of issues |
| `agents/researcher.md` | Perform 4 web searches for latest SEO/AI-bot best practices, synthesize against references |
| `agents/implementer.md` | Apply approved changes per category (meta tags, robots.txt, llms.txt, JSON-LD, sitemap) |
| `agents/validator.md` | Re-run audit on modified files, return pass/fail delta report |

**SKILL.md changes**: Steps 1-2 → auditor subagent. Step 3 → researcher subagent (parallel with auditor review). Steps 4-5 → main agent synthesizes and presents. Step 6 → implementer subagent. Step 7 → validator subagent.

**Risk**: Auditor runs both a script and manual review (two different tasks). Researcher depends on web search availability — needs fallback to reference files.

---

### 3. code-review (Score: 5/5)

**Pattern**: B (Parallel Workers) + C (Review Loop)

**Why**: Full codebase audits (Mode 2) scan entry points, business logic, and frequently-modified files in one pass. Context grows fast with many file reads.

**Subagents to create**:
| Agent File | Role |
|---|---|
| `agents/file-reviewer.md` | Review a batch of files against the full checklist, return structured JSON findings |
| `agents/report-assembler.md` | Merge all batch results, de-duplicate, rank by severity, write `CODE_REVIEW.md` |
| `agents/reviewer.md` | Fresh-context agent validates findings are accurate and well-evidenced |

**SKILL.md changes**: Phase 1 → explorer subagent enumerates and classifies files into batches. Phase 2 → parallel file-reviewer workers (one per batch). Phase 3 → report-assembler. Phase 4 → independent reviewer. Mode 1 (small PR/diff) should stay inline as a fast path.

**Risk**: Parallel workers reviewing different batches may miss cross-file smells (duplicate code, shotgun surgery). Report-assembler partially mitigates but cannot fully reconstruct cross-cutting context.

---

### 4. brand-name-checker (Score: 5/5)

**Pattern**: B (Parallel Workers) + D (Research+Synthesis)

**Why**: 13+ sequential web fetches across social platforms, package registries, domains, and trademark databases. These are structurally independent — parallelization yields ~4x speedup.

**Subagents to create**:
| Agent File | Role |
|---|---|
| `agents/social-checker.md` | Search 6 social platforms in parallel, return availability per platform |
| `agents/registry-checker.md` | Check npm, PyPI, Homebrew, apt availability and owner info |
| `agents/domain-checker.md` | Check .com, .io, .app, .co, regional TLDs |
| `agents/trademark-checker.md` | Search WIPO, EUIPO, INPI trademark databases |
| `agents/synthesizer.md` | Apply risk matrix, produce final recommendation |

**SKILL.md changes**: Spawn social-checker first (for early-exit logic). If clear, spawn registry + domain + trademark in parallel. Synthesizer aggregates all results. All 13+ web fetches move out of main context.

**Risk**: Early-exit logic means social-checker must complete before other workers spawn. Wasted fetches if social is already a blocker but workers launched prematurely.

---

### 5. excalidraw-generator (Score: 5/5)

**Pattern**: C (Review Loop)

**Why**: Large JSON output with ~20 fields per element. 10 validation checks (two-way bindings, size-fit, arrow points) benefit from fresh-context reviewer that doesn't "know" what the generator intended.

**Subagents to create**:
| Agent File | Role |
|---|---|
| `agents/json-generator.md` | Generate complete Excalidraw JSON from confirmed plan, write to file |
| `agents/json-validator.md` | Run all 10 validation checks independently, return structured pass/fail |
| `agents/json-fixer.md` | Apply targeted fixes from validator report (not regenerate from scratch) |

**SKILL.md changes**: Phases 1-2 (Understand + Propose) stay in main agent. Phase 3 → json-generator subagent. Phase 4 → review loop: validator → if NEEDS_FIX → fixer → fresh validator → max 3 cycles.

**Risk**: For simple diagrams (< 10 elements), three subagents add unjustified overhead. Consider: only spawn review loop for complexity > 30 elements.

---

### 6. openspec-task-loop (Score: 5/5)

**Pattern**: E (Staged Pipeline) + C (Review Loop)

**Why**: Multi-task loop where each iteration accumulates context. Without subagents, 5-10 task iterations degrade reasoning quality significantly.

**Subagents to create**:
| Agent File | Role |
|---|---|
| `agents/spec-scaffolder.md` | Create all OpenSpec artifacts (proposal.md, design.md, tasks.md, specs/) |
| `agents/implementer.md` | Implement scoped task, update checkboxes, run validation |
| `agents/verifier.md` | Independently check quality gate: scope atomicity, acceptance criteria, spec-to-test alignment |
| `agents/archiver.md` | Merge spec deltas, move to archive, update parent tasks.md |

**SKILL.md changes**: Each of the 6 core loop steps maps to a subagent spawn. Main agent becomes pure orchestrator. Manual fallback path stays for environments without Agent tool.

**Risk**: Strictly sequential (step N depends on step N-1) — no parallelism benefit. Each subagent needs substantial context about the task being processed.

---

### 7. tad-generator (Score: 4/5)

**Pattern**: D (Research+Synthesis) + E (Staged Pipeline)

**Why**: 5 independent research rounds can run in parallel. PRD content (potentially large) stays out of main context.

**Subagents to create**:
| Agent File | Role |
|---|---|
| `agents/prd-reader.md` | Read PRD + supporting docs, return structured extraction |
| `agents/tech-researcher.md` | Handle one research round (spawned 5x in parallel) |
| `agents/tad-writer.md` | Generate complete tad.md from all inputs |

**SKILL.md changes**: Phase 1-2 → prd-reader subagent. Phase 3 (Clarify Architecture) stays in main agent. Phase 4 → 5 parallel tech-researcher spawns. Phase 5 → tad-writer subagent.

**Risk**: Research rounds are conceptual reasoning, not data fetching — parallel subagents won't produce fundamentally different info, but they keep each round's reasoning isolated.

---

### 8. tasks-generator (Score: 4/5)

**Pattern**: E (Staged Pipeline) + B (Parallel Workers)

**Why**: Per-sprint task generation is parallelizable. Large PRDs produce 30-80 tasks across 4+ sprints.

**Subagents to create**:
| Agent File | Role |
|---|---|
| `agents/requirements-extractor.md` | Read PRD + docs, return structured feature list and constraints |
| `agents/sprint-planner.md` | Define sprint structure (POC, MVP, full feature scopes) |
| `agents/sprint-worker.md` | Generate all tasks for one sprint (spawned per sprint in parallel) |
| `agents/dependency-resolver.md` | Wire cross-sprint dependencies, validate no circular deps, produce critical path |

**SKILL.md changes**: Phase 1 → requirements-extractor. Phases 2-3 → sprint-planner. Phase 4-5 → parallel sprint-workers + dependency-resolver as final assembler.

**Risk**: Sprint tasks are not fully independent — Sprint 2 often depends on Sprint 1. Dependency-resolver must do a second pass to wire cross-sprint deps.

---

### 9. drawio-generator (Score: 4/5)

**Pattern**: C (Review Loop)

**Why**: Same structure as excalidraw-generator. Large XML output + 9 validation checks benefit from independent reviewer.

**Subagents to create**:
| Agent File | Role |
|---|---|
| `agents/xml-generator.md` | Generate complete draw.io XML from confirmed plan, write to file |
| `agents/xml-validator.md` | Run all 9 validation checks independently |
| `agents/xml-fixer.md` | Apply targeted corrections from validator report |

**SKILL.md changes**: Same pattern as excalidraw-generator. Phases 1-2 stay in main agent. Phase 3 → generator. Phase 4 → review loop (max 3 cycles).

**Risk**: Same as excalidraw — overhead unjustified for simple diagrams. Consider complexity threshold.

---

### 10. aso-marketing (Score: 4/5)

**Pattern**: E (Staged Pipeline) + C (Review Loop)

**Why**: 7-phase pipeline with heavy file reads, policy rule scanning, compliance checks, and metadata writes. One of the most context-heavy skills.

**Subagents to create**:
| Agent File | Role |
|---|---|
| `agents/analyzer.md` | Read all codebase/metadata files, produce Phase 1 analysis report |
| `agents/plan-writer.md` | Generate ASO plan (keywords, metadata, visuals, localization) |
| `agents/compliance-checker.md` | Verify all metadata against prohibited keywords/trademark rules |
| `agents/executor.md` | Implement approved metadata changes |
| `agents/reviewer.md` | Run Phase 5 review checklist + Phase 6 best-practices verification |

**SKILL.md changes**: Each of 7 phases maps to a subagent. Main agent orchestrates phase transitions and manages the user approval gate after Phase 3.

**Risk**: Heavy data flow between stages — each subagent needs all context the previous one produced. Use workspace staging pattern.

---

### 11. logo-designer (Score: 4/5)

**Pattern**: A (Explorer+Executor) + C (Review Loop)

**Why**: 7 SVG files generated inline is the single biggest context cost. Brand research across multiple project files adds to the burden.

**Subagents to create**:
| Agent File | Role |
|---|---|
| `agents/brand-researcher.md` | Read project files, produce structured brand brief |
| `agents/svg-generator.md` | Generate all 7 SVG files to `/assets/logo/` |
| `agents/svg-reviewer.md` | Validate SVG structure (viewBox, no rasters, all 7 files, correct names) |

**SKILL.md changes**: Phase 1 → brand-researcher. Phase 3 → svg-generator. New validation step → svg-reviewer. Main agent handles style selection interactively.

**Risk**: SVG generator needs exact hex codes and product name — any ambiguity produces off-brand logos. Reviewer can check structure but not visual aesthetics.

---

## MEDIUM Priority — Would Benefit, Not Urgent

| Skill | Score | Pattern | Key Change |
|---|---|---|---|
| **usability-review** | 4/5 | C: Review Loop | Add `agents/ui-analyst.md` + `agents/report-writer.md` + `agents/fixer.md` |
| **readme-to-landing-page** | 4/5 | C: Review Loop | Add `agents/researcher.md` + `agents/writer.md` + `agents/reviewer.md` |
| **cli-builder** | 4/5 | A: Explorer+Executor | Add `agents/analyzer.md` + `agents/implementer.md` + `agents/reviewer.md` |
| **theme-transformer** | 4/5 | A: Explorer+Executor | Add `agents/style-auditor.md` + `agents/theme-executor.md` + `agents/accessibility-checker.md` |
| **code-optimizer** | 3/5 | A: Explorer+Executor | Add `agents/analyzer.md` + `agents/fixer.md` |
| **test-coverage** | 3/5 | A+B: Explorer+Parallel | Add `agents/coverage-analyzer.md` + `agents/test-writer.md` (per-module parallel) |
| **prd-generator** | 3/5 | E+C: Pipeline+Review | Add `agents/context-extractor.md` + `agents/prd-writer.md` + `agents/prd-reviewer.md` |
| **install-script-generator** | 3/5 | E: Pipeline | Add `agents/env-analyzer.md` + `agents/script-writer.md` + `agents/script-validator.md` |
| **ollama-optimizer** | 3/5 | A: Explorer+Executor | Add `agents/system-analyzer.md` + `agents/guide-generator.md` |
| **skill-creator** | 5 (already) | Refactor | Extract `agents/executor.md` to bring SKILL.md from 596 to <500 lines |

---

## LOW Priority — No Meaningful Benefit

| Skill | Score | Reason |
|---|---|---|
| **release-manager** | 5 (already) | Already well-architected with 4 agent files; minor polish only |
| **frontend-design** | 3/5 | Only usability-reviewer wins; generation must stay inline for coherence |
| **oss-ready** | 3/5 | Mostly template-based file creation; modest context savings |
| **devops-pipeline** | 2/5 | Generates 2 config files; only detection phase benefits marginally |
| **github-issue-creator** | 2/5 | Batch extractor only useful for 3+ inputs; PII handling must stay inline |
| **context-hub** | 2/5 | Parallel doc fetcher only for 3+ libraries; typical case is 1-2 |
| **vscode-extension-publisher** | 2/5 | Mostly interactive user guidance; preflight-only benefit |
| **skill-inventory-auditor** | 2/5 | Scanner script does the heavy lifting; small file set |
| **agent-config** | 2/5 | Reads 3-4 files, writes 1; inherently simple |
| **idea-validator** | 2/5 | Interactive Q&A dependency makes subagents the wrong tool |
| **docs-generator** | 2/5 | Marked "effort: low"; mandatory mid-flow user gate |
| **auto-push** | 1/5 | Designed to be fast/immediate; subagents add latency |
| **note-taker** | 1/5 | `disable-model-invocation: true`; quick capture action |
| **opencode-runner** | 1/5 | Thin CLI wrapper; every step depends on previous |

---

## Recommended Implementation Order

The order prioritizes skills where subagents provide the clearest, most testable benefit:

```
Phase 1 — Quick wins with shared patterns
  1. excalidraw-generator  ←→  drawio-generator  (identical Review Loop pattern)
  2. code-review                                   (Parallel Workers + Review)
  3. brand-name-checker                                  (Parallel Workers — ~4x speed)

Phase 2 — High-impact complex skills
  4. appstore-review-checker                       (Explorer + Guideline Auditor)
  5. seo-ai-optimizer                              (Research + Staged Pipeline)
  6. openspec-task-loop                            (Staged Pipeline per task)

Phase 3 — Workflow chain (compounding benefit)
  7. tad-generator + tasks-generator               (same PRD→TAD→Tasks chain)
  8. aso-marketing + logo-designer                 (brand/marketing pipeline)

Phase 4 — Refactoring existing
  9. skill-creator                                 (extract agents/executor.md)
```

---

## Pattern Distribution Summary

```
Review Loop (C)        ████████████████████  9 skills
Explorer+Executor (A)  ██████████████        7 skills
Parallel Workers (B)   ██████████            5 skills
Staged Pipeline (E)    ██████████            5 skills
Research+Synthesis (D) ██████                3 skills
None                   ████████████████████████████  14 skills
```

---

## Graceful Degradation Requirement

Every skill that adopts subagents **must** include a fallback section:

```markdown
## Environment Check
If the Agent tool is available, use subagents as described below.
If not (e.g., Claude.ai), execute each phase inline instead:
- Phase 1 (explore): Read the files directly in the main conversation
- Phase 2 (execute): Make changes directly
- Phase 3 (review): Self-review the output (less rigorous, but functional)
```

This ensures skills work everywhere, with varying levels of context efficiency.

---

## New Agent Files to Create (Total: ~50 files across 11 HIGH + 10 MEDIUM skills)

| Skill | Agent Files |
|---|---|
| appstore-review-checker | project-explorer, guideline-auditor, report-writer, fixer |
| seo-ai-optimizer | auditor, researcher, implementer, validator |
| code-review | file-reviewer, report-assembler, reviewer |
| brand-name-checker | social-checker, registry-checker, domain-checker, trademark-checker, synthesizer |
| excalidraw-generator | json-generator, json-validator, json-fixer |
| openspec-task-loop | spec-scaffolder, implementer, verifier, archiver |
| tad-generator | prd-reader, tech-researcher, tad-writer |
| tasks-generator | requirements-extractor, sprint-planner, sprint-worker, dependency-resolver |
| drawio-generator | xml-generator, xml-validator, xml-fixer |
| aso-marketing | analyzer, plan-writer, compliance-checker, executor, reviewer |
| logo-designer | brand-researcher, svg-generator, svg-reviewer |
