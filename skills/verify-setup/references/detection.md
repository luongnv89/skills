# Detecting the App and Its Commands

Step 1 reads the repo; it runs nothing. Every command found here is recorded with its source as `path:line`. A value found only in prose that does not name the command (a README that says "start the server") is not a source.

## App type

Check every signal; a repo can hold several apps (a monorepo, or a server with its own frontend). Record each app with its root folder.

| Type | Signals |
|---|---|
| **Web app** | A frontend framework or bundler in the manifest (`next`, `vite`, `react-scripts`, `nuxt`, `@sveltejs/kit`, `astro`, `@angular/core`, Rails or Django templates), an `index.html` served by the app, a `dev` or `start` script that serves pages |
| **API or service** | A server framework (`express`, `fastify`, `hono`, `@nestjs/core`, `flask`, `fastapi`, `django` without templates, `gin`, `echo`, `axum`, `actix-web`, `spring-boot`), an OpenAPI or GraphQL schema, a Dockerfile `EXPOSE`, a compose service with `ports:`, a `Procfile` `web:` line, a worker with a health endpoint, a plain server in code (Node `http.createServer` or `node:http`, Python `http.server`, Go `net/http` `ListenAndServe`) |
| **CLI** | `bin` in `package.json`, `[project.scripts]` or `console_scripts` in Python packaging, `[[bin]]` or `src/main.rs` in Cargo, a Go `main` package with `cobra`, `urfave/cli` or `flag`, a `cmd/` folder |
| **Mobile or desktop** | `ios/`, `android/`, Xcode or Gradle projects, Flutter, React Native, Electron or Tauri config |
| **Library** | Only packaging metadata and modules, no entry point, server or `bin` |

A server that also serves pages is a web app and an API: one verify skill can cover both, with features from each.

## Where commands come from

Look in this order and stop at the first source that gives the command. Cite it.

1. The manifest's scripts: `package.json` `scripts`, `pyproject.toml` (`[project.scripts]`, `[tool.poetry.scripts]`, task runner sections such as `[tool.poe.tasks]`), `Cargo.toml`, `composer.json` `scripts`, `deno.json` `tasks`.
2. Task runners: `Makefile`, `justfile`, `Taskfile.yml`, `mise.toml`, `.tool-versions` for runtime versions.
3. Containers: `docker-compose.yml` or `compose.yaml` services, `Dockerfile` `CMD`, `ENTRYPOINT` and `EXPOSE`, `Procfile`, `devcontainer.json` `postCreateCommand`.
4. CI: the steps in `.github/workflows/*.yml` (or other CI config) that install, build, start or smoke-test the app.
5. Docs: a fenced command block in `README*`, `CONTRIBUTING*` or `docs/` under a run, start or usage heading, or a command in `AGENTS.md` or `CLAUDE.md`.

The package manager comes from the lockfile: `package-lock.json` → `npm ci`, `pnpm-lock.yaml` → `pnpm install --frozen-lockfile`, `yarn.lock` → `yarn install --frozen-lockfile` (Yarn 1) or `yarn install --immutable` (Yarn 2+), `bun.lock` or `bun.lockb` → `bun install --frozen-lockfile`, `uv.lock` → `uv sync --frozen`, `poetry.lock` → `poetry install`, `Pipfile.lock` → `pipenv sync`, `Cargo.lock` → `cargo build --locked`, `go.sum` → `go build ./...`. With no lockfile, say so: the install is not reproducible, and it is an assumption in the plan. A manifest that declares no dependencies needs no install ("none needed").

## What to record per app

| Field | What it holds | Examples |
|---|---|---|
| Install | The lockfile command, or "none needed" | `npm ci` (package-lock.json) |
| Build | The build command, or "none" | `npm run build` (package.json:8) |
| Boot | The command that starts the app, with the port or entry point | `npm run dev` (package.json:7), port 5173 (vite.config.ts:6) |
| Ready signal | How to know it is up: a health URL, a log line the code prints, a port that opens; for a CLI, the process exit | `GET /health` → 200 (src/server.ts:41) |
| Teardown | How to stop it: the PID this run started, `docker compose down` for a compose stack it started | stop PID; `docker compose down` (compose.yaml) |
| Environment | Variable names the app reads, from `.env.example`, config or code; never values | `DATABASE_URL` (.env.example:2) |
| Writes | Paths outside the repo the config shows the app writes to | `~/.myapp/cache` (src/config.py:12) |

**CLI entry points.** A `[project.scripts]`, `bin` or `[[bin]]` entry is a command only once the package is installed or built. Use, in order: an invocation the repo documents without an install (`python -m <pkg>` with a `__main__.py`, `node bin/cli.js`, `cargo run --`, `go run ./cmd/<name>`), each with its source; else the entry point after the approved install into the repo (a repo-local `.venv/`, `node_modules/.bin/`, `target/`). With neither, the CLI rows are `UNVERIFIED`; never compose an invocation such as `python -c 'from pkg import main'`.

A field with no source is `unknown`. The plan lists each `unknown` and asks the user for it, or proposes an assumption for approval: for a missing ready signal, polling the boot URL or port with a stated timeout. Take the timeout from the repo when it has one (a compose `healthcheck`, a CI wait step), else propose one (for example 30 seconds) in the plan as an assumption. A fixed sleep is never a ready signal.

**Port.** Use the port the config names. When it is configurable by an environment variable the code reads (`PORT`), the verify skill may set a free port that way. When the port is fixed and busy, report the conflict; never kill the process holding it.

## Keeping writes in the repo

Package managers and runtimes write caches, logs and temp files to the home directory by default (`~/.npm/_logs` on every `npm` call, `~/.cache/pip`). From Step 4 on (after approval; creating `.verify/` is itself a write), every command the skill runs, and every command the generated verify skill runs, starts with this environment, using absolute paths under the repo (`$ROOT` is `git rev-parse --show-toplevel`):

```bash
V="$ROOT/.verify"; mkdir -p "$V/tmp" "$V/cache" "$V/logs"
export TMPDIR="$V/tmp" XDG_CACHE_HOME="$V/cache" \
  npm_config_cache="$V/cache/npm" npm_config_logs_dir="$V/logs/npm" npm_config_update_notifier=false \
  XDG_DATA_HOME="$V/data" PIP_CACHE_DIR="$V/cache/pip" PIP_REQUIRE_VIRTUALENV=1 UV_CACHE_DIR="$V/cache/uv" \
  PYTHONPYCACHEPREFIX="$V/cache/pycache" PIPENV_VENV_IN_PROJECT=1 \
  YARN_CACHE_FOLDER="$V/cache/yarn" YARN_ENABLE_GLOBAL_CACHE=false PNPM_HOME="$V/cache/pnpm" \
  GOCACHE="$V/cache/go-build" GOMODCACHE="$V/cache/go-mod" CARGO_HOME="$V/cache/cargo" \
  NEXT_TELEMETRY_DISABLED=1 DO_NOT_TRACK=1
```

Keep only the lines for the tools the app uses. A Python install goes into a repo-local `.venv/` (`python3 -m venv .venv`, then `.venv/bin/pip install --no-cache-dir …`); `PIP_REQUIRE_VIRTUALENV` makes a pip call outside it fail instead of writing to user site-packages. A redirected cache starts empty, so the first install downloads more: say so in the plan.

A tool or app path that no variable redirects (a config path the code hard-codes under `~`, a system service) is a write outside the repo: the commands that cause it are not run, their rows are `UNVERIFIED`, and the plan names the path.

## Drivers

| App | Driver, in order of preference | Without it |
|---|---|---|
| Web app | A browser tool the agent already has (a browser MCP such as Chrome DevTools or Playwright MCP); Playwright already in the repo with its browsers installed (`node_modules/playwright/package.json` present and a browser in its cache folder) | `curl` the page: status code and text in the served HTML. Clicks, forms and shortcuts are `UNVERIFIED` |
| API or service | `curl` (or the repo's HTTP client in its existing e2e tests) | Nothing needed beyond `curl` |
| CLI | The built binary or the manifest's entry point | Nothing needed |
| Mobile or desktop | An installed simulator, emulator or driver the repo's tooling names | Features `UNVERIFIED` |

Before approval, check what is installed only by reading: `command -v <tool>` and files on disk (`node_modules/.bin/`, `.venv/bin/`, a browser cache folder). Never call `npx`, `npm`, `pip` or another package manager to probe: they write logs or caches to the home directory and may download the package. Installing a missing driver, browser, simulator or test framework is a separate plan item, default No.

## CLI smoke script reuse

devops-pipeline generates `scripts/e2e_test.sh` (or `scripts/e2e_test.py`) for CLI projects: it builds the CLI, runs each command with representative input and error paths, and asserts exit codes and output. When the repo has that script:

- The verify skill runs it as one step, with its source cited, and grades it by its exit code.
- The feature map still lists each CLI feature; rows the script already covers say `covered by scripts/e2e_test.sh`, and the verify skill adds steps only for the rest.

Without that script, the CLI verify skill follows the same shape: `--help` for each subcommand, each feature with input from the repo's fixtures or README examples, the exit code and an output pattern, and one error path (an unknown command or invalid flag), each with its source.
