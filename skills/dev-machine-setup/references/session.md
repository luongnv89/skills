# Session file — pause and resume

`~/.dev-machine-setup/session.json` is the durable running log. It exists so a run interrupted anywhere —
the user walks away, the terminal closes, the machine reboots — can be picked up by triggering the skill
again, with nothing re-asked and nothing re-run.

Created at the end of phase 1, rewritten whole at every **Record** step. Never patch it in place: rewriting
the whole document is one command and cannot leave half-valid JSON behind.

## Schema

```json
{
  "schema": 1,
  "status": "in-progress",
  "mode": "setup",
  "started": "2026-08-20T09:41:00Z",
  "updated": "2026-08-20T10:12:33Z",
  "machine": { "os": "darwin", "arch": "arm64", "host": "mbp-luong", "manager": "brew" },
  "phases": { "1": "done", "2": "skipped", "3": "done", "4": "partial", "5": "in-progress", "6": "pending" },
  "items": [
    { "id": "uv", "kind": "baseline", "state": "done", "evidence": "uv 0.11.0" },
    { "id": "opencode", "kind": "agent", "state": "declined", "note": "user wanted claude only" },
    { "id": "npm-global-bin-not-on-path", "kind": "finding", "severity": "high",
      "state": "needs-new-shell", "evidence": "export line appended to ~/.zshrc" },
    { "id": "oh-my-zsh-missing", "kind": "finding", "severity": "low", "state": "approved",
      "command": "sh -c \"$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)\"" }
  ],
  "backups": ["/Users/me/.zshrc.bak.20260820094533"],
  "next": "run oh-my-zsh-missing, then re-run detect_env.py"
}
```

| Field | Rule |
|-------|------|
| `status` | `in-progress` until phase 6 sets `complete`. Only a `complete` session is skipped silently at phase 0. |
| `mode` | `setup` or `tune`, fixed in phase 1. A resume keeps it — do not re-derive it from the new prompt. |
| `machine` | Identity check for staleness. A different `host` or `os` means a different machine: start fresh. |
| `phases` | `pending` · `in-progress` · `done` · `skipped` · `partial`. |
| `items[].kind` | `baseline` · `agent` · `finding` · `debloat`. |
| `items[].state` | `pending` · `approved` · `done` · `needs-new-shell` · `failed` · `declined` · `deferred`. |
| `items[].command` | Only on items still owing a command (`approved`, `failed`). This is what rebuilds the paste-once block at a pause — drop it once the item is `done`. |
| `backups` | Absolute path of every rc file copy made, so a bad edit is recoverable without guessing. |
| `next` | One sentence, written for a *cold* reader: the resume screen is built from it. |

## Writing it

Timestamps: run `date -u +%Y-%m-%dT%H:%M:%SZ` first and paste the literal value. The heredoc below is quoted,
so `$(...)` inside the JSON is stored verbatim — which is what item commands need.

```bash
mkdir -p ~/.dev-machine-setup
cat > ~/.dev-machine-setup/session.json <<'JSON'
{ ...the whole document... }
JSON
```

PowerShell:

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\.dev-machine-setup" | Out-Null
@'
{ ...the whole document... }
'@ | Set-Content -Encoding utf8 "$HOME\.dev-machine-setup\session.json"
```

## Reconciling on resume (phase 0)

The machine moved on while you were away — the user may have pasted the remaining blocks by hand, or
installed something else entirely. So re-run `detect_env.py` **before** trusting any recorded state, and
treat the fresh probe as the authority:

| Recorded state | Fresh probe says | Becomes |
|----------------|------------------|---------|
| `approved` / `pending` / `failed` | already satisfied | `done` — evidence `"verified on resume"` |
| `approved` / `pending` | still missing / still a finding | stays — re-present its run-block |
| `done` / `needs-new-shell` | still missing / still a finding | `pending` — say it regressed, then re-present |
| `declined` / `deferred` | still a finding | unchanged — **do not re-propose** unless the user asks |
| anything | `machine` block mismatches this host | session is stale — start fresh, keep the old file |

**Never replay a stored `command` that names a file line number.** Line numbers move — a phase-3 install
that appended to the same rc file invalidates them, and a stale `sed -i '12d'` deletes the wrong line. On
resume, re-run the finding's inspect block and re-derive the fix from fresh output. Currently only
`path-duplicates` produces such commands; store its `command` as the *inspect* block, never the edit.

Never report an item as done on the strength of `evidence` alone. A finding that only clears in a new login
shell is `needs-new-shell`, not `done`, until a fresh shell confirms it.

## Pausing

On "pause", "stop here", or "I'll finish later", output exactly three things:

1. The session file path.
2. What is left: counts by state, and the `next` sentence.
3. A paste-once block of the `command` of every item still in state `approved`, in approval order — so the
   user can finish by hand without the agent.

Leave nothing half-applied: if an rc file was opened for edit, either complete that one edit or restore its
backup before pausing.
