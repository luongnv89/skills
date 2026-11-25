# Merge, baselines and timing (Steps 2, 4 and 5)

## Dedup: is the tool already there?

A planned tool is **already configured** when any of these match, in the hook manager, in any CI workflow, or in security-setup's footprint:

1. The same hook id (`ruff`, `ruff-check`, `eslint`, `gitleaks`, `bandit`).
2. The same tool name in an `entry:`, `run:`, lint-staged command or husky line (`gitleaks`, `semgrep`, `osv-scanner`).
3. The same action in a `uses:` line (`gitleaks/gitleaks-action`, `github/codeql-action`).
4. security-setup's footprint (`security-check` hook, `scripts/security_check.py`, `security/security-tools.json`): every tool in that JSON's `checks[]` is configured for its `category`, in the hook through `security-check` and in CI through `.github/workflows/security.yml` when it exists. Do not add a second secret scanner, SAST tool or dependency scanner for a category it covers. The plan lists each skipped tool as `covered by security-setup (security/security-tools.json)`.

A match is skipped, never edited. A configured tool with an outdated version is reported, not upgraded.

## pre-commit (`.pre-commit-config.yaml`)

- Append new entries under `repos:`. Keep every existing repo, hook, `rev:`, `args:`, `exclude:`, `default_stages` and comment, in their order.
- When the repo URL is already listed, add the new hook id under that repo entry instead of a second entry for the same URL.
- Pin `rev:` to a released tag, as the existing entries do.
- Tools that pre-commit cannot fetch run as `repo: local` hooks with `language: system`, which need the tool installed (a plan item).
- Install: when `core.hooksPath` is unset and `.git/hooks/pre-commit` is missing or already pre-commit's, run `pre-commit install`. When `core.hooksPath` points elsewhere (husky), do not run it: pre-commit refuses there (checked with pre-commit 4.7.0: "Cowardly refusing to install hooks with `core.hooksPath` set"), and a second manager is not installed (*SKILL.md → Edge Cases*).

## husky (`.husky/pre-commit`)

- Append the new commands after the existing lines. Never remove or reorder a line, and never rewrite the file.
- When the repo uses lint-staged, add the new tool to the lint-staged config for the matching glob: append to the existing command array for that glob, or add a new glob key. Never replace a key's commands.
- Without lint-staged, a husky line filters staged files by the tool's globs and skips the tool when none match, so an empty list never lints the whole repo: `git diff --cached --name-only --diff-filter=ACMR -z -- '*.js' '*.ts' | xargs -0 -r ./node_modules/.bin/eslint`. `-z` with `xargs -0` keeps paths with spaces intact; `-r` skips the run on empty input in GNU `xargs` (the macOS `xargs` checked here accepted `-r` and ran nothing on empty input; verify on install). Where `-r` is unavailable, check for an empty list explicitly. Adding lint-staged is its own plan item, default No (a new dependency).
- Call tools through the repo's own binaries (`./node_modules/.bin/eslint`, `npm exec --no -- eslint`), never an undeclared `npx` package.

## lefthook (`lefthook.yml`)

- Add each file-list tool under `pre-commit: commands: <name>:` with `glob:` and `run: <tool> {staged_files}`. A staged-diff scanner takes no file list: gitleaks runs as `run: gitleaks git --pre-commit --staged --redact`, without `glob:` or `{staged_files}`. Keep every existing command and option.
- A command name already present means a conflict: use a new name (`<tool>-analysis`) only when its `run:` differs and calls a different tool; otherwise it is a duplicate and is skipped.
- Tools added here run in check mode, so no re-staging of fixed files is needed. If the user approves fix mode, check how the installed lefthook version handles re-staging before relying on it.
- Run `lefthook install` only when lefthook's hook is not already installed.

## GitHub Actions

- Add a new workflow, `.github/workflows/code-analysis.yml`, rather than editing existing jobs. Add a job to an existing workflow only if the user asks.
- Each job: `permissions: contents: read` (plus `security-events: write` only for a SARIF upload the plan lists), `timeout-minutes`, and actions pinned the way the repo already pins them (tag or SHA, never a branch).
- Pull-request workflows get `concurrency: { group: code-analysis-${{ github.ref }}, cancel-in-progress: true }`.
- Install tools at a fixed version (`pip install semgrep==<version>`, a release binary with a checksum), never `latest` and never `curl | sh`.
- Dependency scans also get `schedule:` (weekly) and `workflow_dispatch:`.
- A job that compares against history or a base ref checks out with `fetch-depth: 0`, or fetches the base ref before the scan: a history secret scan, `semgrep scan --baseline-commit`, `golangci-lint --new-from-rev`, or any ref diff. The default shallow checkout has no base commit to compare with.
- No `continue-on-error` and no `|| true` on a gating step. A check meant to be informational is placed in a job that is not required, and the plan says so.
- No other CI system is edited; the plan reports it as left out.

## Baselines

Existing findings must not block day one, and a baseline must never hold a secret.

| Tool | Baseline | What it stores |
|---|---|---|
| gitleaks | `.gitleaksignore` (preferred) | one fingerprint per line |
| detect-secrets | `.secrets.baseline` | hashed secrets, file and line |
| Bandit | `-b bandit-baseline.json`, generated without B105, B106, B107 (below) | finding metadata and quoted source lines (`code`); hardcoded-password findings never go in it |
| Semgrep | none in the repo; on pull requests CI passes `--baseline-commit <base sha>` with `fetch-depth: 0` | nothing |
| SwiftLint | `--write-baseline <temp file>`, run from the repo root, copied in, then `--baseline <file>` | finding metadata, the flagged source line (`text`) and file paths relative to the directory lint ran in (seen with SwiftLint 0.65.1; verify on install) |
| ESLint | bulk suppressions in recent versions (`--suppress-all`); verify on install | rule counts per file |
| golangci-lint | `--new-from-rev <base>` | nothing |
| Linters without a baseline | the hook checks staged files only; CI lints changed files on PRs | nothing |

A push to the default branch has no base commit to compare with, so a Semgrep job on push would report every existing finding. On day one, Semgrep runs on pull requests only; when the user also wants it on push, it goes in a separate job that is not required, and the plan says so.

### Bandit

A Bandit baseline report quotes the flagged source lines (`code`), so a hardcoded-password finding (B105, B106, B107) would copy a secret value into it. Those findings are handled as secret findings: never written to the baseline, reported to rotate, or, when the user confirms a false positive, marked with an inline `# nosec B105` (or the matching id), a source edit shown to the user in Step 4 and made only on their yes.

Generate the baseline from the repo root into the temporary folder, with one context line per finding and without those tests: `bandit -r <paths> -n 1 --skip B105,B106,B107 -f json -o "$tmp/bandit-baseline.json"` (checked with Bandit 1.9.4; verify on install). Then follow *Baselines that quote source* below. The configured hook and CI commands keep B105 to B107 on; never add the `--skip` there. Each such finding therefore still fails the Bandit acceptance run until it is rotated or marked `# nosec`, and until then the report says that check fails (Bandit 1.9.4: a command without the skip, reading a baseline made with it, exited 1 on the remaining B105 finding).

### Baselines that quote source

A Bandit or SwiftLint baseline can still quote a secret on a line no secret rule flagged. Such a baseline is never written into the repo before it is checked:

1. Write it to the temporary folder outside the repo: Bandit as above; SwiftLint with `swiftlint lint --write-baseline "$tmp/swiftlint-baseline.json"` (SwiftLint 0.65.1 exited 2 on error-level violations and still wrote the file, so judge the file, not the exit code).
2. Scan the temporary file with the repo's secret scanner, redacted: `gitleaks dir --redact "$tmp/<baseline file>"`. Show each hit to the user (file, rule, line; the value is `REDACTED`).
3. Drop every finding whose hit the user does not confirm as a false positive or already rotated, and report that secret to rotate.
4. Copy the file into the repo only after the user confirms, then delete the temporary file.

### gitleaks

Fingerprints must come from the same kind of scan each configured command runs, over the same files. A tree scan (`gitleaks dir`) and a history scan (`gitleaks git`) can report the same secret at different lines (a line added above it in a later commit), and a secret deleted from the tree is found only in history. A `gitleaks dir` run in the working copy also reads gitignored and untracked files (a local `.env`) that no commit and no CI checkout holds, so the tree scan covers tracked files only.

1. Run each scan the configured commands run, with redaction, into temporary reports **outside the repo**:
   - tree (tracked files only): export the index outside the repo and scan it from inside the export, so the paths stay repo-relative: `git checkout-index -a --prefix="$tmp/tree/"`, then `(cd "$tmp/tree" && gitleaks dir --redact --report-format json --report-path "$tmp/tree.json" .)`.
   - history (when CI scans history): `gitleaks git --redact --report-format json --report-path "$tmp/history.json" .`
   - local files: `gitleaks dir --redact --report-format json --report-path "$tmp/local.json" .` in the working copy. A finding whose `File` is not listed by `git ls-files` is local-only.
2. Show each finding to the user (file, rule, line, commit; the value is `REDACTED`). Each one is either a false positive or already rotated (baseline it), or a real secret (report it to rotate; do not baseline). Local-only findings are listed separately as `local-only, not committed` and are never baselined; the user decides what to do with them.
3. Write the confirmed findings' `Fingerprint` values to `.gitleaksignore` in the commit-less `file:rule:line` form: tree fingerprints already have it; strip the leading `<commit>:` from history fingerprints. A commit-less entry suppresses that rule at that file and line in every commit, so each entry is shown to the user before it is written.
4. Delete the temporary reports and the export.

With gitleaks 8.30.1 this was checked on scratch repos: tree fingerprints alone did not cover a history finding whose line had moved, and the union of tree and stripped history fingerprints made both `gitleaks dir` and `gitleaks git` exit 0. A tracked file got the same `file:rule:line` fingerprint from the index export as from `gitleaks dir` in the working copy; with it in `.gitleaksignore`, `gitleaks dir` and `gitleaks git` in a fresh clone both exited 0, while `gitleaks dir` in the working copy still failed on a gitignored `.env`. Confirm on the installed version with the acceptance check below.

If a `--baseline-path <report.json>` file is used instead, that report must have been written with `--redact`, and every gitleaks command that reads it (hook and CI) also passes `--redact`. The plan then shows both commands.

**Acceptance check:** re-run the exact gitleaks command configured in CI on the baselined repo; it must exit 0. A CI `gitleaks dir` command is re-run on a fresh index export, as below, since a CI checkout holds no gitignored files. The hook's staged-diff command (`gitleaks git --pre-commit --staged`, or the `gitleaks` pre-commit hook id) passes trivially with nothing staged (checked with gitleaks 8.30.1: ~0 bytes scanned, exit 0), so running it proves nothing. The hook-side proof is the same tracked-files tree scan on a fresh export. Step 4 leaves `.gitleaksignore` uncommitted, so it is not in the export and is passed explicitly: `(cd "$tmp/tree" && gitleaks dir --redact -i "<repo toplevel>/.gitleaksignore" .)`; it must exit 0. `gitleaks dir .` in the working copy is not the check: a local-only file makes it fail. A `.gitleaksignore` file that exists is not proof. If one still fails, re-scan with that command's report, show the remaining findings (redacted), and repeat steps 2 to 4 for them; a finding the user does not confirm stays a finding, and the report says the check fails. Delete the export afterwards.

## Timing (Step 5)

### Warm-up

Build environments and caches before timing, and report this as setup time:

- pre-commit: `pre-commit install-hooks`
- Node: none beyond the approved dependency install
- Others: one `--version` call per tool, to confirm it runs

### Invariant

```bash
tree_before="$(git write-tree)"
status_before="$(git status --porcelain)"
# ... timing run ...
[ "$(git write-tree)" = "$tree_before" ] && [ "$(git status --porcelain)" = "$status_before" ]
```

If either differs, restore and report it: `git read-tree "$tree_before"`, then `git checkout -- <sample files>`. The sample files were clean before the run, so checking them out only undoes what the timing run changed. When the invariant cannot be guaranteed (an unmerged index, a tool that writes outside its cache, a cache path inside the repo that is not ignored), print `timing: skipped (<reason>)` and do not time.

### Sample

Tracked files that are not in the pre-sync dirty list, not written in Step 4, and not dirty now, matching the globs the hook covers, up to the median files per commit. An empty sample prints `timing: skipped (no clean tracked files)`.

### Timed run

- pre-commit: `time pre-commit run --files <sample>`. Tools added by this skill are in check mode. An existing fixer hook may still try to rewrite a file; the invariant catches and restores that.
- husky or lefthook: time each underlying tool command on the sample, in check mode (`ruff check <files>`, `./node_modules/.bin/eslint --cache --cache-location "$tmp/eslintcache" <files>`, `swiftlint lint --quiet <files>`), and add the times. A cache that would land in the repo unignored is pointed at a temp folder outside the repo, which is deleted afterwards. Never time through lint-staged or another wrapper that stages files, and never `git add`.
- A staged-diff scanner (the gitleaks hook) has nothing staged during the timing run, so its time means nothing. Under `pre-commit run --files`, the total includes that hook's near no-op pass, which is not a measurement of it; report it as `not measured (staged-diff scanner)` in the timing line and the Final Report's `Uncertainty:`.
- Report each tool's time, the total, the budget, and the setup time separately. Redact any secret match in the output.
