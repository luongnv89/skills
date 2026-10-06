# File Specs — oss-ready

Per-file content rules for Steps 2-6 of SKILL.md. Two terms from SKILL.md apply throughout:

- **Additive edit**: on a file that already exists, add only missing sections or lines. Never replace, reword, translate or delete the user's content.
- **Placeholder**: any match of `\[(YEAR|COPYRIGHT HOLDER|INSERT [A-Z ]+)\]|TODO|TBD|FIXME` in a created file, or in a line the run added to an existing file.

## Analysis values (Step 1)

Record each value. Steps 2-6 use them.

| Value | How to find it |
|-------|----------------|
| Stack | The manifests at the repo root: `package.json` is Node.js, `pyproject.toml` or `setup.py` is Python, `Cargo.toml` is Rust, `go.mod` is Go. More than one manifest, or manifests in subdirectories, is a monorepo |
| Purpose | The first paragraph of the existing README, else the manifest `description`. If neither exists, ask the user |
| Existing files | `ls -a` and `ls .github docs` for `LICENSE*`, `README*`, `CONTRIBUTING*`, `CODE_OF_CONDUCT*`, `SECURITY*`, `.github/`, `docs/`, `CHANGELOG*`, `.gitignore`. Each one found gets an additive edit only |
| License | The first line of an existing `LICENSE` |
| Repo URL | `git remote get-url origin`, rewritten to an `https://` URL |
| Default branch | From Step 0 |
| README language | The language of the existing README prose |
| Visibility | `gh repo view --json visibility -q .visibility`. If `gh` cannot run, record `visibility unknown` and continue |
| Fill values | The table below |

## Placeholder fill values (Step 1 collects them)

| Token | Asset | Fill with | If the value is unknown |
|-------|-------|-----------|-------------------------|
| `[YEAR]` | `LICENSE-MIT` | Output of `date +%Y` | Not possible; `date` always answers |
| `[COPYRIGHT HOLDER]` | `LICENSE-MIT` | The manifest author (`author` in `package.json`, `authors` in `pyproject.toml` or `Cargo.toml`). If none, the output of `git config user.name` | Ask the user. With no answer, leave the token; the run ends `PARTIAL` |
| `[INSERT CONTACT METHOD]` | `CODE_OF_CONDUCT.md` | The conduct contact the user gives | Leave the token; the run ends `PARTIAL` |
| `[INSERT SECURITY EMAIL]` | `SECURITY.md` | The security contact the user gives (email or form URL) | Leave the token; the run ends `PARTIAL` |

Never invent a contact address. Ask for both contacts in one question during Step 1.

## README.md (Step 2)

Write each section from the Step 1 analysis. When the README exists, apply an additive edit in the README's own language.

- Project overview and motivation: from the existing README or the manifest `description`
- Key features list: from the code's entry points, commands or exported modules
- Quick start: the shortest install-then-run command sequence found in the manifest scripts, `Makefile` or CLI help
- Prerequisites and installation: runtime and version from the manifest (`engines`, `requires-python`, `rust-version`, the `go` directive)
- Usage examples with code: copied from existing code, tests, scripts or `--help` output. Never invent a command
- Project structure: the top-level directories with one line each
- Technology stack: the stack and main dependencies from the manifest
- Contributing link: `[CONTRIBUTING.md](CONTRIBUTING.md)`
- License badge and a License section naming the license in `LICENSE`

If the code gives no source for a section, leave the section out. Do not write a placeholder. List the missing section under `Manual review` in the final report.

## CONTRIBUTING.md (Step 2)

Include each item. Take commands from the manifest; take the default branch from Step 0.

- How to contribute overview, with a link to the issue tracker (`<repo-url>/issues`)
- Development setup: clone, install, and run the tests with the project's real commands
- Branching strategy: feature branches from the default branch
- Commit conventions: Conventional Commits, unless the git log already follows another convention
- Pull request process and review expectations
- Coding standards: the linters and formatters configured in the repo, if any
- Testing requirements: the project's test command

## LICENSE, CODE_OF_CONDUCT.md, SECURITY.md (Step 2)

| File | Source | Rule when the file exists |
|------|--------|---------------------------|
| `LICENSE` | `assets/LICENSE-MIT`, unless the user names another license | Never overwrite. Record its first line as the detected license and skip the file |
| `CODE_OF_CONDUCT.md` | `assets/CODE_OF_CONDUCT.md` (Contributor Covenant 2.0) | Additive edit: append only template sections whose heading is missing |
| `SECURITY.md` | `assets/SECURITY.md` | Additive edit: append only template sections whose heading is missing |

When the user names a license other than MIT, write that license's standard SPDX text and use its title in the Acceptance Criteria check. Fill placeholders using the table above.

## GitHub templates (Step 3)

Copy each missing file from `assets/.github/` to the same path under `.github/`. Keep every existing file and workflow under `.github/` unchanged.

## docs/ (Step 4)

Create each missing file. Start each file with a `#` heading.

| File | Content | Skip when |
|------|---------|-----------|
| `docs/ARCHITECTURE.md` | Components and how data moves between them, from the source tree | Never |
| `docs/DEVELOPMENT.md` | Local setup, test, lint and debug commands from the manifest | Never |
| `docs/DEPLOYMENT.md` | Deploy steps from CI files, `Dockerfile` or deploy scripts. For a library, the release and publish steps from the manifest | No deploy or publish step exists in the repo. List the skip under `Manual review` |
| `docs/CHANGELOG.md` | An `## Unreleased` section, and one section per existing git tag | A root `CHANGELOG.md` exists. Keep it and record the skip as not applicable |

## Project metadata (Step 5)

Add each missing field. Never overwrite a field that has a value. Take `repository` from `git remote get-url origin`, rewritten to an `https://` URL.

| Stack | File | Fields |
|-------|------|--------|
| Node.js | `package.json` | `license`, `description`, `repository`, `keywords` |
| Python | `pyproject.toml` (`[project]` table) or `setup.py` | `license`, `description`, the repository URL under `[project.urls]` or `url=` |
| Rust | `Cargo.toml` (`[package]` table) | `license`, `description`, `repository` |
| Go | `go.mod` | None: the format has no such fields. Add the license badge to README.md instead. The metadata check is not applicable |
| No manifest | — | None. The metadata check is not applicable |

In a monorepo, edit only the root manifest unless the user names a sub-package. After the edit, parse the file to confirm it is still valid: `python3 -m json.tool package.json` or `python3 -c "import tomllib; tomllib.load(open('pyproject.toml','rb'))"` (use `Cargo.toml` for Rust). A parse failure makes Step 5 `FAIL`: write back the content the file had before the edit. Do not use `git checkout`, which also discards the user's uncommitted changes to that file. If `python3` is missing, or older than 3.11 and so without `tomllib`, the parse check did not run: list it under `Uncertainty:`, and the run ends `PARTIAL`.

## .gitignore (Step 6)

Append each pattern that is missing. Check one pattern with `grep -qxF '<pattern>' .gitignore`. Never remove a line.

| Stack | Patterns |
|-------|----------|
| Every stack | `.env`, `.DS_Store` |
| Node.js | `node_modules/`, `dist/`, `coverage/` |
| Python | `__pycache__/`, `*.pyc`, `.venv/`, `dist/`, `*.egg-info/` |
| Rust | `target/` |
| Go | `*.exe`, `*.test`, `*.out` |
