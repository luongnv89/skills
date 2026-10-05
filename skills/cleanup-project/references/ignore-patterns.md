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

Before proposing a pattern, test it against every path the user chose to keep in Step 2. If a
pattern matches one, narrow it or drop it. Ignoring kept work hides it from the next `git status`.

## Secret-like files

For `.env*`, `*.pem`, `*.key`, `*.p12`, `id_rsa*`, or `credentials*`:

- If untracked: propose the pattern and point out that ignoring is the right move.
- If tracked: warn that adding the pattern does **not** remove the file from history. The secret
  should be rotated, and history rewriting is a separate decision. This skill does not rewrite
  history.

Name the file; never print its contents.

## Approve, apply, commit

1. Show the full proposed diff of `.gitignore` (or `.dockerignore`, etc.).
2. Apply only after approval. Re-run `git status --porcelain` to show the artifacts disappear.
3. Ask a second time before committing. Default: commit on `main` as
   `chore: ignore <what> artifacts`. The commit is local; offer `git push origin main` as a
   separate step that needs its own confirmation.
4. Alternative: a `chore/gitignore-cleanup` branch and a PR. Warn that until it merges, `main`
   has no such rule, so the artifacts stay visible in `git status` on `main` and the end state is
   PARTIAL.

If the user declines, apply nothing. Every artifact path that is not covered by an applied
pattern goes back to Step 2 for a keep or discard decision.
