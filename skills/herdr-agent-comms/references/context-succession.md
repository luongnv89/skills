# Context succession (HANDOFF) — herdr-agent-comms

Read this when the main agent's own context gate fires, or before starting a fleet run expected to outlast one context window.

**HANDOFF** = the orchestrator role migrates from this pane to a fresh successor pane. Root is a **role, not a pane**: after a HANDOFF the successor is `root_pane` for every later operation, the outgoing pane is retired to read-only, and it is closed only under Rule 8 confirmation.

HANDOFF is not a worker restart. Workers are respawned through Phase 2; HANDOFF replaces the orchestrator itself, so exactly one agent keeps write access to the fleet.

## Gate points

Self-check at these checkpoints only — not on every tool call.

| Checkpoint | When |
|---|---|
| Before a spawn wave | Phase 2, before the first `herdr pane split` |
| Before a broadcast | Phase 6, before `broadcast.sh` |
| After a reply relay | Phase 5, once the delta has been relayed |

Never gate mid-cycle. If a send has dispatched and its wait has not resolved, finish Phase 5 first, then gate.

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
| Relayed reads (Phase 5 deltas) | 20 |
| Spawn waves (Phase 2 runs) | 4 |

Whichever count trips first. HANDOFF immediately, regardless of counters, on a harness compaction/summarization notice, on your own truncated output, or after losing tracked pane ids twice.

Anti-thrash: a generation may not HANDOFF until it has completed at least one full operation (spawn wave, send cycle, or broadcast). Log every UNKNOWN decision:

```text
⚠ Context UNKNOWN for main — fallback: {continue|handoff} ({reads}/20 reads · {waves}/4 waves)
```

## HANDOFF procedure

1. **Record the brief** from the template below. Compact state only — never transcripts, full diffs, or pasted worker output.
2. **Spawn the successor** with the canonical `spawn_sub` workflow in `herdr-recipes.md`: plan the rightmost split, split `--direction right --no-focus` in `project_dir`, parse the pane id, equalize as a hard gate. Name it `main-g<N>` for generation `N` (the original main is `g1`); on collision, suffix an epoch. Launch the **same agent CLI the outgoing main is running**, bare, unless the user named a different one — a successor on an unfamiliar CLI cannot honor the brief. If the grid already holds more than four panes, warn that columns are cramped and ask before adding the successor column.
3. **Ready-gate it** with `wait_for_idle.py --ready`. On non-zero, abort the HANDOFF: stay main, report the orphan pane id, and ask before closing it. A failed HANDOFF never leaves the fleet without an orchestrator.
4. **Send the brief** through the full Phase 4 cycle — baseline, fresh `HERDR_DONE_` marker, preflight, `herdr pane run`, delivery check. Multi-line payload: use the guarded multi-line recipe in `herdr-recipes.md`.
5. **Wait for the ack** `HANDOFF ACCEPTED gen=<N> fleet=<k>` via `wait_for_idle.py`. No ack (timeout or blocked) means the HANDOFF failed — stay main and report.
6. **Retire this pane.** After the ack, issue no further writes to any fleet pane: no sends, no splits, no closes. Remain available for read-only reporting so the human is not stranded.
7. **Announce the successor** to the human by pane id and name, with `herdr agent focus main-g<N>` so they can steer it directly.

## Handoff brief template

```text
You are now the MAIN AGENT (orchestrator) for this Herdr fleet. Load the
`herdr-agent-comms` skill and continue the run from the state below.

generation: {N}   (previous main: {old_pane} — retired, read-only)
handoff threshold: {T}%   — keep gating your own context at this number
workspace: {ws}   tab: {root_tab}   project_dir: {project_dir}
your pane: {new_pane}   — use it as root_pane for every later operation

objective: {one-paragraph restatement of the user's ask}

fleet roster:
  {name} = {pane_id} · role {role} · status {status} · last verified: {deliverable}

delivered (do NOT redo): {bullets}
outstanding (in order): {bullets}
constraints: {confirmations granted or withheld · destructive scope · layout limits}

Rules:
1. Mint fresh baselines and completion markers. Never inherit mine.
2. Never write to {old_pane}. Never close panes, tabs, or the server without
   explicit user confirmation.
3. Re-verify every worker's status before your first send.
4. Reply exactly `HANDOFF ACCEPTED gen={N} fleet={k}` before doing any work.

Do not read my transcript. Everything you need is above.
```

## Done when

The report records a parsed percentage or an explicit UNKNOWN fallback; any HANDOFF has a ready successor pane id, a delivered brief, a received ack, and an announced focus command; and the outgoing pane has made no write since the ack.
