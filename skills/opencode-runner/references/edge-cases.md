# Edge cases and command reference — opencode-runner

Read this when an edge case below fires, or when you need an opencode command that a phase does not spell out. Each case points back to the SKILL.md phase that owns its handling, and names the final report status it ends with.

## Edge cases

- **opencode not installed** — see Phase 1, Step 1: print the install instructions, then stop with `BLOCKED`.
- **`opencode upgrade` fails** — see Phase 1, Step 2: report the error and continue if `opencode --version` still exits 0. If it does not, stop with `BLOCKED`; never continue on a broken binary.
- **No free cloud models available** — see Phase 2, Selection logic item 6: stop with `BLOCKED`. Never fall back to local or paid models.
- **All priority free models tried and all fail** — see Phase 5, *On error, stall, or timeout*: suggest `opencode auth list`, run Phase 6, and end with `PARTIAL`.
- **Task stalls or times out (no output growth)** — see Phase 5, *Cadence*: ask the user, kill only on approval, suggest a retry, run Phase 6, and end with `PARTIAL`.
- **User rejects or changes the Phase 3 confirmation** — see Phase 3, final paragraph: loop back and re-confirm. A cancel stops with `BLOCKED`. Never invoke `opencode run` unconfirmed.
- **User has an interactive opencode TUI session open** — see Phase 6, Step 2: kill only `opencode run` processes and leave the TUI alone.
- **Task prompt contains multi-line content or file references** — see Phase 4, *Handling multi-line or complex prompts*: use `--file`.
- **opencode produces output but exits non-zero** — the last poll shows a non-zero `exit=`. Report the exit code and the last lines of output, run Phase 6, and end with `PARTIAL`. The final report's `Decision:` asks the user to check the changed files before relying on them.
- **The wrapper was killed before opencode finished** — the last poll shows `exit=none`. Treat it as a failure: run Phase 6 and end with `PARTIAL`.

## Command reference

| Command | Purpose |
|---------|---------|
| `opencode --version` | Check installed version |
| `opencode upgrade` | Update to latest |
| `opencode models` | List available models |
| `opencode run -m MODEL "prompt"` | Run task with specific model |
| `opencode stats` | View usage statistics |
| `opencode auth list` | Check authenticated providers |
| `pgrep -fl "opencode run"` | Find running `opencode run` processes |
| `pkill -f "opencode run"` | Kill orphaned run processes |
