# Context succession (HANDOFF) — rex-agent

Read this when the main agent's own context gate fires, or before starting a fleet run expected to outlast one context window.

**HANDOFF** = the orchestrator role migrates from this block to a fresh successor block. Root is a **role, not a block**: after a HANDOFF the successor is the root for every later operation, the outgoing block is retired to read-only, and it is closed only under Rule 8 confirmation.

HANDOFF is not a worker restart. Workers are respawned through Phase 2; HANDOFF replaces the orchestrator itself, so exactly one agent keeps write access to the fleet.

## Gate points

Self-check at these checkpoints only — not on every tool call.

| Checkpoint | When |
|---|---|
| Before a spawn wave | Phase 2, before the first `launch_profile.py --start` |
| Before a broadcast | Phase 7, before `agent.py broadcast` |
| After a reply relay | Phase 5, once the delta has been relayed |

Never gate mid-cycle. If a prompt has dispatched and its wait has not resolved, finish Phase 5 first, then gate.

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

Whichever count trips first. HANDOFF immediately, regardless of counters, on a harness compaction or summarization notice, on your own truncated output, or after losing tracked block IDs twice.

Anti-thrash: a generation may not HANDOFF until it has completed at least one full operation (spawn wave, prompt cycle, or broadcast). Log every UNKNOWN decision:

```text
⚠ Context UNKNOWN for main — fallback: {continue|handoff} ({reads}/20 reads · {waves}/4 waves)
```

## HANDOFF procedure

1. **Record the brief** from the template below. Compact state only — never transcripts, full diffs, or pasted worker output.
2. **Start the successor** with the Phase 2 call: `launch_profile.py --main-model … --main-thinking … --start main-g<N> --cwd "$project_dir"` for generation `N` (the original main is `g1`). That places it as the rightmost column, equalizes, and returns only when it reports `idle`, on the **inherited launch profile**: the outgoing main's kind, model, thinking level, and setup flags, unless the user named a different one for the successor itself. A successor on an unfamiliar CLI or a weaker model cannot honor the brief. Overrides the user set for workers (for example "no bypass for workers") do not apply to the successor, which replaces the main agent; record them in the brief so the successor keeps applying them. If the window already holds more than four columns, warn that they are cramped and ask before adding the successor.
3. **On a failed start, abort.** Any non-zero exit means the HANDOFF failed: stay main, report the orphan block ID from the error, and ask before closing it. A failed HANDOFF never leaves the fleet without an orchestrator.
4. **Send the brief** through the full Phase 4 cycle: `agent.py prompt <successor block> - --timeout 120` with the brief on stdin, using the `block_id` the start printed. Do not add the worker preamble, because the successor is not a worker. The brief asks for the ack and nothing else, so the turn settles quickly.
5. **Read the ack** `HANDOFF ACCEPTED gen=<N> fleet=<k>` with `agent.py read <successor block> --turn <turn>`. On `timeout` or `stalled`, run `agent.py get` and read the screen before deciding: a successor still writing its ack has not failed, so wait once more with `agent.py wait`. No ack after that means the HANDOFF failed — stay main and report.
6. **Hand over control** with `agent.py prompt <successor block> "GO gen=<N>" --activity-timeout 15 --timeout 20`. Outcome `settled`, or `timeout` with `"observed_working": true`, means the successor took over. This is the outgoing block's last fleet write.
7. **Retire this block.** Issue no further writes to any fleet block: no prompts, starts, or closes. Remain available for read-only reporting so the human is not stranded.
8. **Announce the successor** to the human by name and block ID, with `rex focus -s "$session" <successor block>` so they can steer it directly.

The two-step ack and `GO` keep exactly one orchestrator at every moment: the successor does no work before `GO`, and the outgoing block writes nothing after it.

## Handoff brief template

```text
You are now the MAIN AGENT (orchestrator) for this Rex fleet. Load the
`rex-agent` skill and continue the run from the state below.

generation: {N}   (previous main: {old_block} — retired, read-only)
handoff threshold: {T}%   — keep gating your own context at this number
session: {session}   window: {root_window}   project_dir: {project_dir}
your block: {new_block}   — your $REX_BLOCK; the scripts use it as root
launch profile: {kind · model · thinking · user-named overrides, e.g. without bypass}
                — start every new worker on it

objective: {one-paragraph restatement of the user's ask}

fleet roster:
  {name} = {block_id} · role {role} · status {status} · last verified: {deliverable}

delivered (do NOT redo): {bullets}
outstanding (in order): {bullets}
constraints: {confirmations granted or withheld · destructive scope · layout limits}

Rules:
1. Prompt only through your own `agent.py prompt` cycles. Never inherit
   my in-flight waits.
2. Never write to {old_block}. Never close blocks, windows, or the session
   without explicit user confirmation.
3. Re-verify every worker with `agent.py fleet` before your first prompt.
4. Reply with only `HANDOFF ACCEPTED gen={N} fleet={k}`, then stop: run no
   command and touch no block until a message says `GO gen={N}`.

Do not read my transcript. Everything you need is above.
```

## Done when

The report records a parsed percentage or an explicit UNKNOWN fallback; any HANDOFF has a ready successor block ID, a delivered brief, a received ack, a sent `GO`, and an announced focus command; and the outgoing block has made no write since the `GO`.
