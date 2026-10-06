# Expected output & step-completion examples

Visual reference for what a successful opencode-runner invocation produces. SKILL.md links here instead of inlining these blocks.

## Phase 2 — Free model picker

```
Found 4 free cloud models. Pick one or accept the default.

1. opencode/deepseek-v4-flash-free  (default — priority 1)
2. opencode/minimax-m2.5-free
3. opencode/nemotron-3-super-free
4. opencode/big-pickle

Note: Free models on OpenCode Zen may use collected data for model improvement.
```

## Phase 3 — Confirmation summary

```
Ready to delegate to opencode

- Model:    opencode/deepseek-v4-flash-free (free tier)
- Cwd:      /Users/.../current-project
- Files:    none
- Prompt:   "Add a retry decorator to utils/http.py and update tests"

Confirm to proceed, or tell me what to change.
```

## Phase 5 — Low-token progress polls

```
opencode started: run=/tmp/opencode-run-1234567890 pid=48211
Poll 1 (t+30s):  running, 1.1 KB,  last: "Reading utils/http.py …"
Poll 2 (t+60s):  running, 4.2 KB,  last: "Editing utils/http.py …"
Poll 3 (t+150s): done, exit 0, 7.8 KB,  last: "Done. 3 files changed, 147 lines added."
```

## Phase 6 — Cleanup confirmation

```
cleanup=complete
Cleanup complete — no opencode run process remains.
```

If the task fails or times out, the output instead shows which model was tried, the exit code and error message from opencode, a recommendation to retry with the next free model, and the cleanup confirmation. Every run then ends with the final report (`references/final-report.md`).

---

## Per-phase Step Completion Report examples

### Installation (phase 1 of 6)

```
◆ Installation (phase 1 of 6 — opencode readiness)
··································································
  opencode found:         √ pass — /usr/local/bin/opencode
  Version current:        √ pass — already at latest
  [Criteria]:             √ 2/2 met
  ____________________________
  Result:                 PASS
```

### Model Discovery (phase 2 of 6)

```
◆ Model Discovery (phase 2 of 6 — free model picker)
··································································
  Models queried:         √ pass — 4 free cloud models available
  List presented to user: √ pass — priority 1 marked default
  User choice captured:   √ pass — user picked deepseek-v4-flash-free
  [Criteria]:             √ 3/3 met
  ____________________________
  Result:                 PASS
```

### Confirmation (phase 3 of 6)

```
◆ Confirmation (phase 3 of 6 — pre-run review)
··································································
  Summary shown:          √ pass — model, cwd, files, prompt
  User confirmed:         √ pass — "proceed"
  [Criteria]:             √ 2/2 met
  ____________________________
  Result:                 PASS
```

### Execution (phase 4 of 6)

```
◆ Execution (phase 4 of 6 — task delegation)
··································································
  Backgrounded with log:  √ pass — opencode started: run=/tmp/opencode-run-1234567890 pid=48211
  Foreground avoided:     √ pass
  [Criteria]:             √ 2/2 met
  ____________________________
  Result:                 PASS
```

### Monitor (phase 5 of 6)

```
◆ Monitor (phase 5 of 6 — low-token polling)
··································································
  Polls within cap:       √ pass — 3 polls (max 6)
  Cadence respected:      √ pass — ≥30s between polls
  Stall detected:         × n/a  — output grew every poll
  Tail-only summary:      √ pass — last 40 lines read on done
  Exit code read:         √ pass — exit=0
  [Criteria]:             √ 4/4 met
  ____________________________
  Result:                 PASS
```

### Cleanup (phase 6 of 6)

```
◆ Cleanup (phase 6 of 6 — process termination)
··································································
  Processes killed:       √ pass — pidfile-owned wrapper and its opencode child terminated
  Temp files cleaned:     √ pass — "$RUN.log", "$RUN.pid" and "$RUN.exit" removed
  No run process left:    √ pass — cleanup=complete
  [Criteria]:             √ 3/3 met
  ____________________________
  Result:                 PASS
```
