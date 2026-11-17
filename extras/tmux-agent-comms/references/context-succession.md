# Context succession (HANDOFF) — tmux-agent-comms

Read this when the main agent's own context gate fires, or before starting a fleet run expected to outlast one context window.

**HANDOFF** = the orchestrator role migrates from this agent to a fresh successor session. Orchestrator is a **role, not a session**: after a HANDOFF the successor drives every later operation, the outgoing agent is retired to read-only, and its session is killed only under Critical Rule 1 confirmation.

HANDOFF is not a worker restart. Workers are respawned through Phase 1; HANDOFF replaces the orchestrator itself, so exactly one agent keeps write access to the fleet.

## Gate points

Self-check at these checkpoints only — not on every tool call.

| Checkpoint | When |
|---|---|
| Before a spawn wave | Phase 1, before the first `new-session` |
| Before a broadcast | Phase 6, before `broadcast.sh` |
| After a reply relay | Phase 5, once the capture has been relayed |

Never gate mid-cycle. If a message has been sent and its wait has not resolved, finish Phase 4 first, then gate.

## Probe and decision

Read your own usage the way this harness surfaces it — status line, a context command, or a remaining-context warning — and resolve it to an integer percentage of the window consumed, or to UNKNOWN. Do not read transcripts or session files to derive it.

| Result | Action |
|---|---|
| Integer `P >= threshold` | HANDOFF |
| Integer `P < threshold` | Continue as main |
| UNKNOWN or unavailable | Apply the fallback below |

Threshold defaults to **50** and is overridable in conversation ("handoff at 65"). Values outside 1–99 use 50 and print one warning.

## UNKNOWN fallback

Count from the moment this generation became main:

| Counter | HANDOFF at |
|---|---|
| Relayed reads (Phase 5 captures) | 20 |
| Spawn waves (Phase 1 runs) | 4 |

Whichever count trips first. HANDOFF immediately, regardless of counters, on a harness compaction/summarization notice, on your own truncated output, or after losing tracked session names twice.

Anti-thrash: a generation may not HANDOFF until it has completed at least one full operation (spawn wave, send cycle, or broadcast). Log every UNKNOWN decision:

```text
⚠ Context UNKNOWN for main — fallback: {continue|handoff} ({reads}/20 reads · {waves}/4 waves)
```

## HANDOFF procedure

1. **Record the brief** from the template below. Compact state only — never transcripts, full diffs, or pasted worker output.
2. **Spawn the successor** through Phase 1: name it `<folder>-main-g<N>` for generation `N` (the original main is `g1`), collision-check with `tmux has-session`, open it in an app terminal tab when available, and otherwise create it detached and print the attach command. Launch the **same agent CLI the outgoing main is running** unless the user named a different one — a successor on an unfamiliar CLI cannot honor the brief.
3. **Ready-gate it** with `wait_for_idle.py --ready --timeout 60`. On non-zero, abort the HANDOFF: stay main, report the unused session, and ask before killing it. A failed HANDOFF never leaves the fleet without an orchestrator.
4. **Send the brief** through the full Phase 3 cycle — baseline, fresh `TAC_DONE_` marker, preflight, text then a separate `Enter`, delivery check. The brief is multi-line, so load it with paste-buffer per Critical Rule 4 rather than shell escaping.
5. **Wait for the ack** `HANDOFF ACCEPTED gen=<N> fleet=<k>` with `wait_for_idle.py`. No ack (timeout or blocked) means the HANDOFF failed — stay main and report.
6. **Retire this agent.** After the ack, issue no further writes to any fleet session: no `send-keys`, no new sessions, no kills. Remain available for read-only reporting so the human is not stranded.
7. **Announce the successor** to the human by exact session name, and print — do not run — `tmux attach-session -t <folder>-main-g<N>` so they can steer it directly.

## Handoff brief template

```text
You are now the MAIN AGENT (orchestrator) for this tmux fleet. Load the
`tmux-agent-comms` skill and continue the run from the state below.

generation: {N}   (previous main: {old_target} — retired, read-only)
handoff threshold: {T}%   — keep gating your own context at this number
workdir: {project_dir}   your session: {new_session}

objective: {one-paragraph restatement of the user's ask}

fleet roster:
  {session} · role {role} · state {in-progress|done|blocked|unknown} · last verified: {deliverable}

delivered (do NOT redo): {bullets}
outstanding (in order): {bullets}
constraints: {confirmations granted or withheld · destructive scope}

Rules:
1. Mint fresh baselines and completion markers. Never inherit mine.
2. Never write to {old_target}. Never kill a session or the server without
   explicit user confirmation.
3. Re-verify every session with `has-session` and a bounded capture before
   your first send.
4. Reply exactly `HANDOFF ACCEPTED gen={N} fleet={k}` before doing any work.

Do not read my transcript. Everything you need is above.
```

## Done when

The report records a parsed percentage or an explicit UNKNOWN fallback; any HANDOFF has a ready successor session, a delivered brief, a received ack, and an announced attach command; and the outgoing agent has made no write since the ack.
