# Ignore-File Update

Step 4 procedure. Patterns are proposed from evidence in this repo, never from a generic
template dump.

## Evidence sources

1. Untracked paths from Step 2 (`git status --porcelain=v1 -z`, `??` entries) that look like
   artifacts.
2. Tracked files that already match an ignore rule:

   ```bash
   git ls-files -ci --exclude-standard
   ```

   These stay tracked despite the rule. Fixing them means `git rm --cached -- <p>`, which removes
   the file from the index (not from disk) and shows up as a deletion for everyone who pulls. Ask
   before proposing it.
3. The project's stack (a `package.json`, `pyproject.toml`, `Cargo.toml`, ...) only to name a
   pattern for an artifact you actually saw.

## Candidate patterns

| Seen | Pattern |
|---|---|
| `node_modules/` | `node_modules/` |
| `dist/`, `build/`, `out/` | the matching directory, anchored with `/` if it is top-level only |
| `__pycache__/`, `*.pyc` | `__pycache__/`, `*.py[cod]` |
| `.venv/`, `venv/` | the matching directory |
| `.DS_Store`, `Thumbs.db` | the file name |
| `*.swp`, `*~` | the editor pattern |
| `.env`, `.env.local` | `.env*` plus `!.env.example` when an example file is tracked |
| coverage output | `coverage/`, `.coverage`, `htmlcov/` |

Only add a pattern that matches something present. Do not duplicate a pattern already in the
file; check with `git check-ignore -v -- <p>`.

## Never ignore a kept path

Before proposing a pattern, test it against every kept path. Kept = committed, stashed, or left
as is. Write the proposed patterns to a temp file and test them without touching `.gitignore`:

```bash
tmp="$(mktemp)"; printf '%s\n' 'node_modules/' '.env*' > "$tmp"
git -c core.excludesFile="$tmp" check-ignore --no-index -v -- <kept paths>
```

Any output line names a pattern that matches a kept path: narrow it or drop it. No output means
no kept path is hidden. Ignoring kept work hides it from the next `git status`.

Exception: paths kept on disk + ignored are exempt; they are meant to be ignored, so a pattern
may match them.

## Secret-like files

For `.env*`, `*.pem`, `*.key`, `*.p12`, `id_rsa*`, or `credentials*`, print one line per file
above the diff:

```
⚠ secret-like: .env (untracked) — will be ignored, stays on disk
⚠ secret-like: config/prod.key (tracked) — ignoring does not remove it from history; rotate it
```

- If untracked: propose the pattern; ignoring is the right move.
- If tracked: adding the pattern does **not** remove the file from history. The secret should be
  rotated, and history rewriting is a separate decision. This skill does not rewrite history.

Name the file; never print its contents.

## Approve, apply, commit

1. Show the full proposed diff of `.gitignore` (or `.dockerignore`, etc.).
2. Apply only after approval. Re-run `git status --porcelain` to show the artifacts disappear.
3. Ask a second time before committing. Default: commit on `main` as
   `chore: ignore <what> artifacts`. The commit is local; offer `git push origin main` as a
   separate step that needs its own confirmation.
4. Alternative: a `chore/gitignore-cleanup` branch and a PR, ending with `git switch main`
   (`action-plans.md` C). Warn that until it merges, `main` has no such rule, so the artifacts
   stay visible in `git status` on `main` and the result is PARTIAL with the PR ref.

## Paths left uncovered

If the user declines the diff, apply nothing. For each deferred path not covered by a pattern
applied on `main`, ask here, inline: `commit to wip / stash / leave as is / discard` (a secret-like path
defaults to `leave as is` and is never committed by default).

- Commit: `git switch wip/cleanup-<date>` (or `git switch -c wip/cleanup-<date>` if Step 2 made
  none), `git add -- <p>`, `git commit -m "<msg>" -- <p>`, then `git switch main`.
- Stash: `git stash push -u -m "cleanup: <name>" -- <p>`.
- Discard: `git clean -n -- <p>`, then `git clean -f -- <p>` after a yes.

After the branch+PR option, do not ask: list the deferred paths under `PARTIAL — ignore rule
pending in PR #N`. Steps 2 and 3 do not repeat.
