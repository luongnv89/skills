# Context succession (HANDOFF) — hc-agent

Read this when the main agent's own context gate fires, or before starting a fleet run expected to outlast one context window.

**HANDOFF** = the orchestrator role migrates from this terminal to a fresh successor pane. Root is a **role, not a pane**: after a HANDOFF the successor is the root for every later operation (its own `HC_TERMINAL_ID`), the outgoing pane is retired to read-only, and it is closed only under Rule 8 confirmation.

HANDOFF is not a worker restart. Workers are respawned through Phase 2; HANDOFF replaces the orchestrator itself, so exactly one agent keeps write access to the fleet. The successor is a `pane.split` terminal with no parent (`die_with_parent: false`), so it keeps running when the old root ends. Never start it with `hc run`, whose terminals end with their parent.

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

Whichever count trips first. HANDOFF immediately, regardless of counters, on a harness compaction or summarization notice, on your own truncated output, or after losing tracked terminal addresses twice.

Anti-thrash: a generation may not HANDOFF until it has completed at least one full operation (spawn wave, prompt cycle, or broadcast). Log every UNKNOWN decision:

```text
⚠ Context UNKNOWN for main — fallback: {continue|handoff} ({reads}/20 reads · {waves}/4 waves)
```

## HANDOFF procedure

1. **Record the brief** from the template below. Compact state only — never transcripts, full diffs, or pasted worker output.
2. **Start the successor** with the Phase 2 call plus `--role main`: `launch_profile.py --main-model … --main-thinking … --start main-g<N> --role main --cwd "$project_dir"` for generation `N` (the original main is `g1`). It splits to the right in the root's tab, restores focus, and returns only when the successor reports `idle`, on the **inherited launch profile** (kind, model, thinking level, setup flags, wrapper), unless the user named a different one for the successor itself. Overrides the user set for workers (for example "no bypass for workers") do not apply to the successor; record them in the brief so it keeps applying them. The `main` role keeps teardown from ever closing it.
3. **On a failed start, abort.** Any non-zero exit means the HANDOFF failed: stay main, report the orphan terminal and pane from the error, and ask before closing it.
4. **Send the brief** through the full Phase 4 cycle: `agent.py prompt main-g<N> - --timeout 120` with the brief on stdin. Do not add the worker preamble, because the successor is not a worker. The brief asks for the ack and nothing else, so the turn settles quickly.
5. **Read the ack** `HANDOFF ACCEPTED gen=<N> fleet=<k>` with `agent.py read main-g<N> --turn <turn>`. On `timeout` or `stalled`, run `agent.py get` and read the screen before deciding: a successor still writing its ack has not failed, so wait once more with `agent.py wait`. No ack after that means the HANDOFF failed — stay main and report.
6. **Hand over control** with `agent.py prompt main-g<N> "GO gen=<N>" --activity-timeout 15 --timeout 20`. Outcome `settled`, or `timeout` after the successor reported `working`, means it took over. This is the outgoing terminal's last fleet write.
7. **Retire this terminal.** Issue no further writes to any fleet terminal: no prompts, starts, focus changes, or closes. Remain available for read-only reporting so the human is not stranded.
8. **Announce the successor** to the human by name, terminal address, and pane, and tell them `agent.py focus main-g<N>` (or the app's agent list) shows it. Run that focus yourself only before `GO`.

The two-step ack and `GO` keep exactly one orchestrator at every moment: the successor does no work before `GO`, and the outgoing terminal writes nothing after it.

## Handoff brief template

```text
You are now the MAIN AGENT (orchestrator) for this hc-agent fleet in the
Herdr desktop app. Load the `hc-agent` skill and continue the run from the
state below.

generation: {N}   (previous main: {old_terminal} — retired, read-only)
handoff threshold: {T}%   — keep gating your own context at this number
space: {space}   tab: {tab}   project_dir: {project_dir}
your terminal: {new_terminal}   — your $HC_TERMINAL_ID; the scripts use it as root
launch profile: {kind · wrapper · model · thinking · user-named overrides, e.g. without bypass}
                — start every new worker on it

objective: {one-paragraph restatement of the user's ask}

fleet roster:
  {name} = {terminal} · pane {pane} · role {role} · status {status} · last verified: {deliverable}

delivered (do NOT redo): {bullets}
outstanding (in order): {bullets}
constraints: {confirmations granted or withheld · destructive scope · layout limits}

Rules:
1. Prompt only through your own `agent.py prompt` cycles. Never inherit
   my in-flight waits. Never call the `herdr` CLI.
2. Never write to {old_terminal}. Never close panes, tabs, or spaces
   without explicit user confirmation.
3. Re-verify every worker with `agent.py fleet` before your first prompt.
4. Reply with only `HANDOFF ACCEPTED gen={N} fleet={k}`, then stop: run no
   command and touch no terminal until a message says `GO gen={N}`.

Do not read my transcript. Everything you need is above.
```

## Done when

The report records a parsed percentage or an explicit UNKNOWN fallback; any HANDOFF has a ready successor terminal, a delivered brief, a received ack, a sent `GO`, and an announced successor; and the outgoing terminal has made no write since the `GO`.
