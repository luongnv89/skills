# Report Templates

Read this file at Phase 3, before writing the guide, and again before printing the final summary.

## Step Completion Report examples

One example per phase. Adapt the check names to what the step actually validated, and replace every value with the observed one.

### Detection (step 1 of 4)

```
◆ Detection (step 1 of 4 — hardware profiling)
··································································
  Hardware detected:      √ pass — macOS 14, Apple M2
  GPU identified:         √ pass — Apple Metal (unified memory)
  RAM measured:           √ pass — 16GB unified memory
  [Criteria]:             √ 3/3 met
  ____________________________
  Result:                 PASS
```

### Analysis (step 2 of 4)

```
◆ Analysis (step 2 of 4 — profile selection)
··································································
  Tier classified:        √ pass — Prosumer (16GB unified)
  Profile selected:       √ pass — Flash attention, full offload
  Bottlenecks identified: √ pass — memory bandwidth primary constraint
  [Criteria]:             √ 3/3 met
  ____________________________
  Result:                 PASS
```

### Plan (step 3 of 4)

```
◆ Plan (step 3 of 4 — optimization guide)
··································································
  Guide generated:        √ pass — ollama-optimization-guide.md written
  Parameters tuned:       √ pass — OLLAMA_FLASH_ATTENTION=1 (KV cache unquantized: 16GB)
  Model recommendations ready: √ pass — llama3.1:8b-instruct-q4_K_M suggested
  [Criteria]:             √ 3/3 met
  ____________________________
  Result:                 PASS
```

### Verification (step 4 of 4)

```
◆ Verification (step 4 of 4 — config validation)
··································································
  Benchmark commands listed: √ pass — python3 scripts/benchmark_ollama.py
  Config verified:        √ pass — ollama run --verbose output checked
  [Criteria]:             √ 2/2 met
  ____________________________
  Result:                 PASS
```

When Phase 4 is skipped (Ollama not installed, no model installed), print the Verification block with `Result: PARTIAL` and the reason on the skipped check.

## Optimization guide template

Save the guide as `ollama-optimization-guide.md` at the path the user chose. If the user declines a file, print the same content in the reply.

```markdown
# Ollama Optimization Guide

**Generated:** <timestamp>
**System:** <OS> | <CPU> | <RAM>GB RAM | <GPU>

## System Overview
<hardware summary and constraints>

## Current Configuration
<existing Ollama setup and env vars>

## Recommendations

### Environment Variables
<shell commands to set vars>

### Model Selection
<recommended models with rationale>

### Performance Tuning
<Modelfile adjustments if needed>

## Execution Checklist
- [ ] <step 1>
- [ ] <step 2>
...

## Verification
<benchmark commands and expected results>

## Rollback
<commands to revert changes if needed>
```

## Final summary fill rules

The final summary format and the status rules live in SKILL.md (*Final Report*). Fill each line as follows:

| Line | Fill with |
|------|-----------|
| `Result:` | The status, the `hardware_tier.category` (`no tier` when BLOCKED), and one clause on what changed (for example "2 env vars applied, 1 model pulled") or "no changes applied". |
| `Evidence:` | Only checks that ran, with the observed value: `detect_system.py` exit code and tier, `ollama --version`, the backup file path, the `benchmark_ollama.py` `avg_tokens_per_second`. Never cite a check that did not run. |
| `Uncertainty:` | Each untested or assumed item, labeled: a tier based on unknown VRAM, a benchmark taken before the changes were applied, a restart the user still has to perform, a change not verified. Write `none` only when every recommended change was applied and verified. |
| `Decision:` | The next change that needs the user's approval, with its exact command, or `No approval needed.` |
| `Remaining action:` | One line per action the user must still take (install Ollama, quit and reopen Ollama.app, pull a model). Omit the line when there is none. |
| `Guide:` | The saved path, or `printed inline`. |

## Reader checks

Use these four checks to review a final summary. They test whether a person can use the report, not only whether the tuning is correct:

1. **Main result is findable** — the first line states the status and the tier without reading the guide.
2. **Facts and assumptions are separated** — every `Evidence:` item names a check that ran; every assumption or untested item is under `Uncertainty:`.
3. **Claims are traceable** — "applied" means the write command succeeded and the backup exists; "verified" means `benchmark_ollama.py` or `ollama run --verbose` ran after the change. A guide that was only written is not an applied change.
4. **Next decision is clear** — `Decision:` names the approval needed or says `No approval needed.`, and every user action is on its own `Remaining action:` line.

Ask a human reviewer the same four questions and record the answers in the eval feedback. Missing or blank feedback leaves human understanding unconfirmed; an agent's own reading cannot confirm it.
