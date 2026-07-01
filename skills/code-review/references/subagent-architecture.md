# Subagent Architecture

Full detail on the Pattern B+C (Parallel Workers + Review Loop) architecture used for medium/large audits: the orchestration diagram, per-agent responsibilities, graceful degradation when the Agent tool is unavailable, and known risk mitigations.

## Diagram

```
┌─────────────────────────────────┐
│  Main SKILL (Orchestrator)      │
│  - Parse scope (PR/audit)       │
│  - Batch files into groups      │
│  - Check Agent availability     │
└──────────────┬──────────────────┘
               │
       ┌───────┴───────┬───────────┬─────────────┐
       │               │           │             │
       v               v           v             v
   ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
   │ Reviewer 1 │ │ Reviewer 2 │ │ Reviewer 3 │ │ Reviewer N │
   │   Batch 1  │ │   Batch 2  │ │   Batch 3  │ │  Batch N   │
   │   5-10     │ │   5-10     │ │   5-10     │ │   5-10     │
   │   files    │ │   files    │ │   files    │ │   files    │
   │ (parallel) │ │ (parallel) │ │ (parallel) │ │ (parallel) │
   └─────┬──────┘ └─────┬──────┘ └─────┬──────┘ └─────┬──────┘
         │              │              │              │
         │              └──────────────┴──────────────┘
         │                             │
         └─────────────────────────────┘
                     │
        ┌────────────v────────────────┐
        │  Report Assembler           │
        │  - Merge all findings       │
        │  - Deduplicate issues       │
        │  - Rank by severity         │
        │  - Generate CODE_REVIEW.md  │
        └────────────┬────────────────┘
                     │
             ┌───────v────────┐
             │  Reviewer      │
             │  Validator     │
             │  - Fresh eyes  │
             │  - Verify      │
             │  - Completeness│
             └────────────────┘
```

## Agent Files

- **agents/file-reviewer.md** — Review a batch of 5-10 files against the full checklist
  - Returns structured JSON with findings, severity levels, and fix suggestions
  - Run in parallel on multiple batches
  - Input: file list, checklist config, language context
  - Output: JSON with findings array

- **agents/report-assembler.md** — Merge all batch results into one report
  - Deduplicates findings by (file, line, smell)
  - Ranks by severity (critical → major → minor → info)
  - Identifies cross-file patterns (duplicate code, shotgun surgery)
  - Generates final CODE_REVIEW.md
  - Input: array of JSON outputs from file-reviewer
  - Output: Markdown report + validation JSON

- **agents/reviewer.md** — Fresh-context validation pass
  - Verifies accuracy of all findings
  - Catches false positives and severity miscategorizations
  - Identifies missed issues
  - Returns validation report with corrections
  - Input: CODE_REVIEW.md + original source files
  - Output: Validation JSON + updated CODE_REVIEW.md if corrections needed

## Graceful Degradation

If the Agent tool is unavailable:
- Fall back to inline execution in main SKILL.md
- Use sequential file processing instead of parallel batches
- Return CODE_REVIEW.md without a validation pass
- Log message: "Subagent architecture unavailable; running inline review"

## Risk Mitigation

**Missed cross-file smells**: Report-assembler cross-file analysis partially mitigates by identifying:
- Duplicate code patterns
- Shotgun surgery risks
- Architectural coupling

**Context overflow**: Batching 5-10 files per agent keeps context manageable while maintaining review quality.

**False positives**: Reviewer agent catches most false positives through fresh-context validation before final report.
