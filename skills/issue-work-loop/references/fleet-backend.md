# Fleet Backend — /issue-work-loop

The loop runs in the **Herdr TUI** through `herdr-agent` or in the **Herdr desktop app** through `hc-agent`. This file covers both: how the runtime is detected, and which TUI step each app step replaces. TUI wording in the other references remains authoritative for the TUI. For every `hc`, `herdr-app`, and `agent.py` behavior quoted here, the acquired `hc-agent` skill is the source of truth.

## Runtime detection

The rule mirrors `hc-agent`'s root resolver (`HERDR_ENV=1` is refused as a TUI pane, then `HC_TERMINAL_ID` names the root terminal) and `herdr-agent`'s Phase 1 guard:

| Environment | `runtime` | `fleet` skill |
|---|---|---|
| `HERDR_ENV=1`, even when `HC_TERMINAL_ID` is also set (a TUI running inside an app terminal) | `tui` | `herdr-agent` |
| `HERDR_ENV` is not `1` and `HC_TERMINAL_ID` is non-empty | `app` | `hc-agent` |
| Neither | — | stop with *No Herdr runtime detected* |

In the app, `herdr` is on PATH, but it reaches a separate TUI server: from an app terminal, `herdr pane current --current` returned another project's pane. The loop never calls `herdr` in the app, not even `herdr status`.

In the app, Prerequisite 4 checks only that `hc` and `herdr-app` are on PATH, with one `command -v` per binary, because bash's `command -v hc herdr-app` exits 0 when only one of them exists. `agent.py check` needs the acquired `hc-agent` scripts, so it runs after Dependency Preflight, as Phase 1 root context.

## Preflight backend selection

The Dependency Preflight block sets `runtime` and `fleet` by the rule above. It acquires `$fleet issue-pr-review`, plus `issue-resolver` in ISSUE mode, under one `iwl_session`, and never the other runtime's fleet skill. Then:

- `fleet_dir` is the `path` field of `$lease_dir/$fleet.json`, never a repository path. In the TUI the same value is also `herdr_agent_dir`, the name `loop-protocol.md` uses.
- `here` is the absolute `$fleet_dir/scripts`. It must hold `launch_profile.py`, and in the app also `agent.py`. If either is missing, stop before the repo sync.

## Operations: TUI vs app

| Step | TUI (`herdr-agent`) | App (`hc-agent`) |
|---|---|---|
| Root context | `$HERDR_PANE_ID`, `$HERDR_TAB_ID`, `$HERDR_WORKSPACE_ID` after `herdr status` | `python3 "$here/agent.py" check` prints `terminal` (the root terminal), `pane` (record as `root_pane`), `space`, `tab`, and `cwd` (record as `project_dir`) |
| Helper capability gate | `loop-protocol.md` → *Installed-helper capability gate* | *App launch-profile gate* below: the same `--without` / `bypass` check against hc-agent's `launch_profile.py` |
| Profile probe | `launch_profile.py --root-pane "$root_pane" …` | `launch_profile.py --root "$HC_TERMINAL_ID" …`; hc-agent has no root-pane option |
| Root evidence | `herdr agent get "$root_pane"` and `herdr pane process-info --pane "$root_pane"` | `hc get "$HC_TERMINAL_ID" --json`: `.status.app` names the kind, `.foreground.argv` is the root argv |
| Spawn | `herdr pane split`, then `launch_profile.py … --start NAME --pane "$worker_pane" --timeout 60000` (milliseconds) | One fused call, `launch_profile.py … --start NAME --cwd "$project_dir" --timeout 60` (seconds) |
| Boot-gate keys | `herdr pane send-keys` | `hc keys "$t" shift+tab` (claude) or `hc keys "$t" tab` (opencode) |
| Send and wait | `preflight_send.py`, then `herdr agent prompt … --wait --timeout 180000` | `agent.py prompt "$t" - --timeout 180`, task on stdin |
| Read reply | `herdr agent read … --source recent-unwrapped --lines 80` | `agent.py read "$t" --turn "$turn"` |
| No-agent fallback | The installed skill's verified pane-surface fallback after preflight exit 5 | None: exit 5 is BLOCKED |
| Fleet status | `herdr agent list` | `agent.py fleet --json` (polled one terminal at a time) |
| Close | `herdr pane close "$worker_pane"` | `agent.py close <names…> --confirmed`, under the *Close-confirmation policy* |
| Timeout unit | Milliseconds | Seconds |

## App launch-profile gate

Run this gate before **every** app worker start, the same set of launches as `loop-protocol.md` → *Selective worker launch-profile gate*:

```bash
here=""
if [ -n "${fleet_dir:-}" ] && [ -d "$fleet_dir/scripts" ]; then
  here="$(cd -- "$fleet_dir/scripts" 2>/dev/null && pwd -P)"
fi
if [ -z "$here" ] || [ ! -f "$here/launch_profile.py" ] || [ ! -f "$here/agent.py" ]; then
  echo "Error: installed hc-agent scripts are unavailable; refusing to launch a worker" >&2
  exit 1
fi
helper="$here/launch_profile.py"
helper_usage="$(python3 "$helper" --help 2>&1)" || {
  echo "Error: installed hc-agent launch_profile.py --help failed; refusing to launch a worker" >&2
  exit 1
}
if ! grep -Fq -- "--without" <<<"$helper_usage" ||
   ! grep -Fq -- "bypass" <<<"$helper_usage"; then
  echo "Error: installed launch_profile.py does not support --without bypass; refusing to launch a worker" >&2
  exit 1
fi
```

Probe with the exact worker inputs, keeping `--without bypass`:

```bash
profile_args=(
  --root "$HC_TERMINAL_ID"
  --main-model "$main_model" --main-thinking "$main_thinking"
  "${worker_profile_args[@]}" --without bypass
)
profile_json="$(python3 "$helper" \
  "${profile_args[@]}" -- "${worker_native_args[@]}")" || {
  echo "Error: worker launch profile failed; refusing to launch" >&2
  exit 1
}
```

Validate `profile_json` with the unchanged parser in `loop-protocol.md` → *Probe and target evidence*. hc-agent prints the same required keys and adds `main_kind` and `launch`, which the parser ignores. Every other rule there still applies, except the destination readback, which the app replaces as described next: inspect the root argv from `hc get "$HC_TERMINAL_ID" --json` and every local file a worker argument names; redact values; refuse explicit native, configuration, or environment bypass; fail closed on unknown or unverifiable input; and re-probe immediately before every start.

Split and start are one call in the app, so no destination pane exists before the start. Right after the start, `hc get "$t" --json` is the supported destination evidence: `.foreground.argv` must carry no bypass token, and `.foreground.cwd` must equal `$project_dir`. On a mismatch, close that worker under *Close-confirmation policy* and stop BLOCKED before any task. The start passes no environment (`pane.split` takes none), so the worker inherits the app terminal's environment, and no supported command reads it back. The loop sets no bypass variable itself. An environment-carried bypass inherited from the app is therefore not ruled out: record it under `Uncertainty:` in the final report.

## App spawn

```bash
python3 "$helper" "${profile_args[@]}" \
  --start "$worker_name" --cwd "$project_dir" --timeout 60 \
  -- "${worker_native_args[@]}"
```

`--timeout` is in **seconds** here; never pass the TUI's `60000`. The start prints one JSON line with `name`, `terminal`, `pane`, `outcome`, `cwd`, and `focus_restored`. Use the printed `name`, which gets an epoch suffix when the name is taken. Record `{role, name, terminal, pane}` in the run's spawn ledger, and use the `t…` terminal address for every later `hc` and `agent.py` call.

| Exit | Meaning | Loop response |
|---|---|---|
| 0 | `outcome: ready` | Continue to the boot gate. If `focus_restored` is false, tell the user before they type |
| 3 | Booted into a dialog | BLOCKED, needs a human: `agent.py focus <name>`; never answer the dialog |
| 1 | Did not start; the message names any orphan terminal | Record the orphan in the ledger, read it with `hc read <t> --lines 40`, stop BLOCKED; never retry blindly |
| 2 | Usage | Fix the call; nothing started |

The loop does not choose placement: hc-agent splits its newest worker pane, or root's, to the right. It passes no environment, because `pane.split` takes none.

## App boot gate

The boot-gate matrix in `loop-protocol.md` is unchanged. Only the keystroke transport differs:

- **claude:** send `hc keys "$t" shift+tab` as a keystroke, never as text. Then run a bounded read, `hc read "$t" --lines 40` (or `agent.py read "$t" --tail 40`), which must show the auto-accept-edits indicator. Allow at most three presses, reading after each one. If the indicator still does not show, close that loop-owned worker and stop BLOCKED with *App boot mode unverifiable*.
- **opencode:** send `hc keys "$t" tab`, then run the same bounded read for the Build agent.
- **pi:** autonomous by default. `outcome: ready` from the start is its readiness wait.

Shift+Tab delivery through `hc keys` is **not yet verified live**: hc-agent documents `hc keys` from its help text only. That is why the gate fails closed. Permission bypass is never the fallback. Keep `--without bypass` on every start, and never pass `--dangerously-skip-permissions`, `--allow-dangerously-skip-permissions`, or `--permission-mode bypassPermissions`.

## App send, wait, and read

```bash
python3 "$here/agent.py" prompt "$t" - --timeout 180 <<'EOF'
<task text>
EOF
```

Give the shell call a timeout of at least 250000 ms, because `hc send` can wait 60 s for a person's draft before the 180 s turn wait. Record the `turn` from the prompt's JSON for every prompt. Read only that turn's delta:

```bash
python3 "$here/agent.py" read "$t" --turn "$turn"
```

`read` exit 4 means the tag was not in the lines read. Raise `--lines` once, then use hc-agent's file fallback.

| `agent.py prompt` exit | Outcome | Loop response |
|---|---|---|
| 0 | settled | Read with `--turn`, then parse |
| 1 | error (missing or ambiguous target, own terminal, bad text) | Stop BLOCKED and report the message; nothing more is sent |
| 2 | usage | Fix the call; nothing was sent |
| 3 | blocked | BLOCKED, needs human input: surface it, `agent.py focus`; never answer it, never `--force` |
| 4 | unverifiable | BLOCKED, *App terminal has no agent status*; read the screen, never type |
| 5 | no agent | BLOCKED, *App terminal has no agent status*; the app has no no-agent fallback |
| 6 | working | The loop's existing rule for a working target: dispatch stops |
| 7 | stalled | The loop's existing STALLED rule: inspect, report, never blindly resend |
| 8 | timeout | The loop's existing TIMEOUT rule: inspect, report, never blindly resend |
| 9 | exited | The worker's program finished. Read why with `hc read`, report that role FAILED, and stop BLOCKED |

## Close-confirmation policy

hc-agent Rule 8: "**Confirm destruction.** Closing panes, tabs, or spaces can lose work. Obtain explicit approval and preserve the orchestrator pane unless the user says otherwise." The loop obtains that approval this way:

- **FRESHEN and failed boot gates:** invoking the loop approves closing and respawning a worker the loop itself spawned this run.
- **SWEEP:** an explicit `work_loop.auto_cleanup: true` in `.gitissue.yml` approves closing this run's workers. In the app, the documented default (`true` when the key is absent) is **not** approval, unlike the TUI.
- **Otherwise**, with `auto_cleanup` absent or false: when a user is present, list the run's workers with `agent.py fleet` and ask before closing. A yes closes them. A no, or no answer, leaves them open. An unattended run leaves them open. Either way the report shows `Cleanup: ⚠ pending` with the names. `--no-cleanup` leaves them open without asking, as in the TUI.
- Pass only names from this run's spawn ledger to `agent.py close <names…> --confirmed`. Never pass root, a `main` successor, an unlabelled terminal, or a terminal outside the root's tab. hc-agent refuses root and `main` too, but that refusal is a backstop, not the policy.
- Verify with `agent.py fleet --json` that no closed ledger name remains.

## Steps that differ in the app

1. Prerequisite 4 checks `hc` and `herdr-app`, never `herdr`, and Dependency Preflight acquires `hc-agent`, not `herdr-agent`.
2. Phase 1 root context comes from `agent.py check`.
3. No no-agent fallback: a terminal without agent status is BLOCKED, never typed into.
4. Split and start are one call. The loop does not choose placement and passes no `--env`.
5. Timeouts are seconds (`--timeout 60` start, `--timeout 180` prompt), not milliseconds.
6. Replies are read by turn ID (`agent.py read --turn`). The loop records one turn per prompt.
7. Closes reach only labelled workers this loop spawned, under the *Close-confirmation policy*. SWEEP needs an explicit `auto_cleanup: true` or the user's answer.
8. Shift+Tab via `hc keys` is not verified live, so the claude boot gate fails closed with *App boot mode unverifiable*.
9. Worker status is polled (`agent.py fleet`), not an atomic snapshot.
10. The app has no sidebar badges or notifications. The loop uses neither in either runtime, so nothing is lost: blocked workers are surfaced in chat, with `agent.py focus`.
