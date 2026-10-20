#!/usr/bin/env python3
"""Helper for the user-test skill.

Subcommands: init, doctor, detect, app (start|wait|status|stop), check-features,
collect, update, build-check, checkpoint (save|restore|diff), report.

Every subcommand prints JSON on stdout. Exit codes: 0 ok, 1 a check failed,
2 bad input or a missing tool, 3 a conflict that needs the user. Failures
print `error:` and `fix:` lines on stderr. Standard library only.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import difflib
import hashlib
import importlib.util
import json
import os
import re
import shutil
import signal
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

RUN_ROOT = ".user-test"
EXIT_FAIL, EXIT_INPUT, EXIT_CONFLICT = 1, 2, 3

SEVERITIES = ["critical", "high", "medium", "low"]
CATEGORIES = ["functional", "crash", "performance", "ux", "accessibility",
              "content", "error-handling", "security"]
KINDS = ["defect", "improvement"]
COMPLEXITIES = ["simple", "medium", "complex"]
STATUSES = ["open", "fixed-verified", "fix-failed", "duplicate"]
COVERAGE = ["pass", "fail", "blocked", "skipped"]
EFFORTS = ["S", "M", "L"]
RISKS = ["low", "medium", "high"]
APP_TYPES = ["web", "api", "cli", "tui", "desktop", "mobile", "other"]
ID_RE = re.compile(r"^[a-z0-9_][a-z0-9-]*$")
URL_RE = re.compile(r"https?://(?:localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\])(?::\d+)?[^\s'\"<>\x1b]*")
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".gif", ".webp")


class Fail(Exception):
    def __init__(self, code: int, errors, fix: str):
        super().__init__(errors)
        self.code = code
        self.errors = [errors] if isinstance(errors, str) else list(errors)
        self.fix = fix


def fail(code: int, errors, fix: str):
    raise Fail(code, errors, fix)


def emit(obj) -> None:
    print(json.dumps(obj, indent=2))


def utc_now() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


def iso(t: _dt.datetime | None = None) -> str:
    return (t or utc_now()).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path: Path, what: str):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(EXIT_INPUT, f"{what} not found: {path}", f"Create {path.name} first (see the step that writes it).")
    except json.JSONDecodeError as exc:
        fail(EXIT_INPUT, f"{what} is not valid JSON: {path}: line {exc.lineno} col {exc.colno}: {exc.msg}",
             f"Fix the JSON syntax in {path}, then re-run.")


def save_json(path: Path, data) -> None:
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def deep_merge(dst: dict, patch: dict) -> dict:
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(dst.get(key), dict):
            deep_merge(dst[key], value)
        else:
            dst[key] = value
    return dst


def open_run(value: str) -> tuple[Path, dict]:
    run_dir = Path(value).expanduser().resolve()
    if not (run_dir / "run.json").is_file():
        fail(EXIT_INPUT, f"{run_dir} is not a user-test run dir (no run.json)",
             "Pass the run_dir printed by `init`, or run `init` first.")
    return run_dir, load_json(run_dir / "run.json", "run.json")


def tail(path: Path, lines: int = 30) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return "\n".join(ANSI_RE.sub("", text).splitlines()[-lines:])


def git(root: Path, *args: str) -> subprocess.CompletedProcess | None:
    if not shutil.which("git"):
        return None
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)


# ---------------------------------------------------------------- init

def cmd_init(a) -> None:
    root = Path(a.root).expanduser().resolve()
    if not root.is_dir():
        fail(EXIT_INPUT, f"--root {root} is not a directory",
             "Pass the project directory (any working directory for a Remote run).")
    if a.branch == "remote" and not a.url:
        fail(EXIT_INPUT, "--branch remote needs --url", "Pass the deployed app's URL with --url.")
    notes = []
    fix_mode = a.fix
    if a.branch == "remote" and fix_mode == "on":
        fix_mode = "off"
        notes.append("Fix mode forced off: the Remote branch has no source to fix.")
    stamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    run_dir = root / RUN_ROOT / stamp
    n = 2
    while run_dir.exists():
        run_dir = root / RUN_ROOT / f"{stamp}-{n}"
        n += 1
    for sub in ("evidence", "areas", "logs", "checkpoints", "work"):
        (run_dir / sub).mkdir(parents=True, exist_ok=True)
    excluded, in_git = False, False
    probe = git(root, "rev-parse", "--git-path", "info/exclude")
    if probe is not None and probe.returncode == 0:
        in_git = True
        exclude = Path(probe.stdout.strip())
        exclude = exclude if exclude.is_absolute() else root / exclude
        exclude.parent.mkdir(parents=True, exist_ok=True)
        current = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
        if not any(line.strip() in (".user-test/", "/.user-test/", ".user-test") for line in current.splitlines()):
            sep = "" if current.endswith("\n") or not current else "\n"
            exclude.write_text(current + sep + "# user-test runs: screenshots, logs, reports\n.user-test/\n",
                               encoding="utf-8")
        excluded = True
    else:
        notes.append("Not a git repo: .user-test/ is not excluded from version control.")
    scope = "all" if a.scope.strip().lower() in ("", "all") else \
        [s.strip() for s in a.scope.split(",") if s.strip()]
    run = {"version": 1, "run_id": run_dir.name, "root": str(root), "url": a.url, "branch": a.branch,
           "scope": scope, "fix_mode": fix_mode, "started_at": iso(), "driver": None,
           "app": {}, "checks": {}, "notes": notes}
    save_json(run_dir / "run.json", run)
    emit({"run_dir": str(run_dir), "branch": a.branch, "scope": scope, "fix_mode": fix_mode,
          "git": in_git, "excluded": excluded, "notes": notes})


# ---------------------------------------------------------------- doctor

def cmd_doctor(a) -> None:
    names = ["git", "node", "npm", "npx", "pnpm", "yarn", "bun", "python3", "docker", "tmux", "curl",
             "lighthouse", "hyperfine", "google-chrome", "chromium", "chromium-browser", "firefox",
             "adb", "xcrun"]
    tools = {name: shutil.which(name) for name in names}
    compose = None
    if tools["docker"]:
        try:
            r = subprocess.run(["docker", "compose", "version"], capture_output=True, text=True, timeout=15)
            compose = r.stdout.strip() or None if r.returncode == 0 else None
        except (OSError, subprocess.TimeoutExpired):
            compose = None
    caches = [os.environ.get("PLAYWRIGHT_BROWSERS_PATH", ""),
              str(Path.home() / ".cache" / "ms-playwright"),
              str(Path.home() / "Library" / "Caches" / "ms-playwright"),
              str(Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "ms-playwright")]
    found, browsers = [], []
    for cache in caches:
        if cache and Path(cache).is_dir():
            found.append(cache)
            browsers += sorted(p.name for p in Path(cache).iterdir() if p.is_dir() and not p.name.startswith("."))
    hints = []
    if browsers and tools["npx"]:
        hints.append("Playwright browser builds are cached; a Node Playwright script can drive a web UI "
                     "(references/testing.md, section 3).")
    if not browsers and not any(tools[b] for b in ("google-chrome", "chromium", "chromium-browser", "firefox")):
        hints.append("No browser found. Use browser tools from this session, or install Playwright into "
                     "<run_dir>/work (downloads a browser); otherwise web UI checks are untested.")
    if not tools["tmux"]:
        hints.append("tmux is missing: full-screen TUI apps cannot be driven; line-based CLIs still work.")
    emit({"python": sys.version.split()[0], "platform": sys.platform, "tools": tools,
          "docker_compose": compose,
          "playwright": {"python_module": importlib.util.find_spec("playwright") is not None,
                         "browser_caches": found, "browsers": sorted(set(browsers))},
          "hints": hints})


# ---------------------------------------------------------------- detect

FRONTEND_PORTS = [("next", 3000), ("vite", 5173), ("react-scripts", 3000), ("@angular/core", 4200),
                  ("nuxt", 3000), ("@sveltejs/kit", 5173), ("astro", 4321), ("gatsby", 8000),
                  ("@remix-run/dev", 3000)]
BACKEND_JS = ("express", "fastify", "koa", "@nestjs/core", "@hapi/hapi", "hono")
README_CMD = re.compile(r"^(?:\$\s*)?((?:npm|pnpm|yarn|bun|npx|python3?|pip3?|uv|poetry|flask|uvicorn|gunicorn|"
                        r"go|cargo|make|just|task|docker|docker-compose|bin/rails|rails|php|dotnet|mvn|\./mvnw|"
                        r"gradle|\./gradlew|mix|streamlit|node|deno)\b.*)$")


def read_text(path: Path, limit: int = 400_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def find_py(root: Path, pattern: str) -> tuple[Path, re.Match] | None:
    candidates = [root / n for n in ("main.py", "app.py", "server.py", "wsgi.py", "asgi.py")]
    candidates += sorted(root.glob("*/main.py")) + sorted(root.glob("*/app.py")) + sorted(root.glob("src/*/main.py"))
    rx = re.compile(pattern)
    for path in candidates:
        if path.is_file() and ".venv" not in path.parts and "node_modules" not in path.parts:
            match = rx.search(read_text(path))
            if match:
                return path, match
    return None


def cmd_detect(a) -> None:
    root = Path(a.root).expanduser().resolve()
    if not root.is_dir():
        fail(EXIT_INPUT, f"--root {root} is not a directory", "Pass the project directory.")
    out = {"root": str(root), "types": [], "install": [], "setup": [], "start": [], "build": [], "test": [],
           "services": None, "deps_missing": False, "readme_commands": [], "env": {}, "notes": []}

    def add(kind: str, cmd: str, source: str, confidence: str = "medium", port: int | None = None) -> None:
        if any(item["cmd"] == cmd for item in out[kind]):
            return
        item = {"cmd": cmd, "source": source, "confidence": confidence}
        if port:
            item["port"] = port
        out[kind].append(item)

    def typ(name: str) -> None:
        if name not in out["types"]:
            out["types"].append(name)

    pkg = root / "package.json"
    if pkg.is_file():
        try:
            data = json.loads(read_text(pkg))
        except json.JSONDecodeError:
            data = {}
            out["notes"].append("package.json is not valid JSON.")
        scripts = data.get("scripts") or {}
        deps = {**(data.get("dependencies") or {}), **(data.get("devDependencies") or {})}
        if (root / "pnpm-lock.yaml").exists():
            pm, install = "pnpm", "pnpm install --frozen-lockfile"
        elif (root / "yarn.lock").exists():
            pm, install = "yarn", "yarn install --frozen-lockfile"
        elif (root / "bun.lockb").exists() or (root / "bun.lock").exists():
            pm, install = "bun", "bun install --frozen-lockfile"
        else:
            pm, install = "npm", "npm ci" if (root / "package-lock.json").exists() else None
        if install:
            add("install", install, "lockfile", "high")
        else:
            out["notes"].append("No lockfile: installing would write one. Ask before installing dependencies.")
        if not (root / "node_modules").is_dir():
            out["deps_missing"] = True
            out["notes"].append("node_modules is missing: run the install command before starting.")

        def run(script: str) -> str:
            return f"npm {script}" if pm == "npm" and script in ("start", "test") else f"{pm} run {script}"

        port = next((p for name, p in FRONTEND_PORTS if name in deps), None)
        if "electron" in deps:
            typ("desktop")
        if "expo" in deps or "react-native" in deps:
            typ("mobile")
        if port or any(d in deps for d in ("react", "vue", "svelte", "solid-js", "preact")):
            typ("web")
        elif any(d in deps for d in BACKEND_JS):
            typ("api")
        if data.get("bin"):
            typ("cli")
        for script, conf in (("dev", "high"), ("start", "medium"), ("serve", "medium"), ("preview", "low")):
            if script in scripts:
                add("start", run(script), f"package.json scripts.{script}", conf, port)
        if "preview" in scripts:
            out["notes"].append("`preview` serves a production build: run the build first.")
        for script in ("build", "typecheck", "type-check", "tsc", "check"):
            if script in scripts:
                add("build", run(script), f"package.json scripts.{script}", "high")
        test = scripts.get("test", "")
        if test and "no test specified" not in test:
            add("test", run("test"), "package.json scripts.test", "high")

    if (root / "manage.py").is_file():
        typ("web")
        add("start", "python3 manage.py runserver 127.0.0.1:8000", "manage.py (Django)", "high", 8000)
        add("setup", "python3 manage.py migrate", "manage.py (Django)", "medium")
        add("test", "python3 manage.py test", "manage.py (Django)", "high")
    py_meta = "".join(read_text(p) for p in [root / "pyproject.toml", root / "Pipfile", root / "setup.py",
                                            root / "setup.cfg", *sorted(root.glob("requirements*.txt"))])
    if py_meta:
        if (root / "uv.lock").exists():
            add("install", "uv sync", "uv.lock", "high")
        elif (root / "poetry.lock").exists():
            add("install", "poetry install", "poetry.lock", "high")
        elif (root / "Pipfile.lock").exists():
            add("install", "pipenv install --dev", "Pipfile.lock", "high")
        elif (root / "requirements.txt").exists():
            add("install", "python3 -m venv .venv && .venv/bin/pip install -r requirements.txt",
                "requirements.txt", "medium")
        low = py_meta.lower()
        if "fastapi" in low:
            hit = find_py(root, r"(\w+)\s*=\s*FastAPI\(")
            if hit:
                mod = ".".join(hit[0].relative_to(root).with_suffix("").parts)
                typ("api")
                add("start", f"uvicorn {mod}:{hit[1].group(1)} --host 127.0.0.1 --port 8000",
                    f"{hit[0].relative_to(root)} (FastAPI)", "medium", 8000)
        if "flask" in low:
            hit = find_py(root, r"(\w+)\s*=\s*Flask\(")
            if hit:
                typ("web")
                add("start", f"flask --app {hit[0].relative_to(root)} run --port 5000",
                    f"{hit[0].relative_to(root)} (Flask)", "medium", 5000)
        if "streamlit" in low:
            hit = find_py(root, r"import streamlit")
            if hit:
                typ("web")
                add("start", f"streamlit run {hit[0].relative_to(root)} --server.port 8501",
                    f"{hit[0].relative_to(root)} (Streamlit)", "medium", 8501)
        if "[project.scripts]" in py_meta or "console_scripts" in py_meta:
            typ("cli")
        if "pytest" in low or any((root / d).is_dir() for d in ("tests", "test")):
            add("test", "python3 -m pytest -q", "pytest / tests dir", "medium")
    if not out["test"] and list(root.glob("tests/test_*.py")):
        add("test", "python3 -m unittest discover -s tests -q", "tests/test_*.py", "medium")
    if not out["start"]:
        hit = find_py(root, r"if __name__ == ['\"]__main__['\"]")
        if hit:
            add("start", f"python3 {hit[0].relative_to(root)}", f"{hit[0].relative_to(root)} __main__", "low")
    if any(p.suffix == ".py" for p in root.glob("*.py")) or py_meta:
        out["notes"].append("Python has no build step: compile-check changed files with "
                            "`python3 -m py_compile <file>`.")

    if (root / "go.mod").is_file():
        if (root / "main.go").is_file():
            add("start", "go run .", "go.mod + main.go", "medium")
        for cmd_dir in sorted((root / "cmd").glob("*")) if (root / "cmd").is_dir() else []:
            add("start", f"go run ./cmd/{cmd_dir.name}", "go.mod + cmd/", "low")
        add("build", "go build ./...", "go.mod", "high")
        add("test", "go test ./...", "go.mod", "high")
    if (root / "Cargo.toml").is_file():
        add("start", "cargo run", "Cargo.toml", "medium")
        add("build", "cargo build", "Cargo.toml", "high")
        add("test", "cargo test", "Cargo.toml", "high")
    if (root / "Gemfile").is_file() and (root / "bin" / "rails").exists():
        typ("web")
        add("start", "bin/rails server -p 3000", "bin/rails", "high", 3000)
        add("setup", "bin/rails db:prepare", "bin/rails", "medium")
        add("test", "bin/rails test", "bin/rails", "medium")
    if (root / "artisan").is_file():
        typ("web")
        add("start", "php artisan serve --port 8000", "artisan (Laravel)", "high", 8000)
        add("setup", "php artisan migrate", "artisan (Laravel)", "medium")
        add("test", "php artisan test", "artisan (Laravel)", "medium")
    if (root / "pom.xml").is_file():
        mvn = "./mvnw" if (root / "mvnw").exists() else "mvn"
        if "spring-boot" in read_text(root / "pom.xml"):
            add("start", f"{mvn} spring-boot:run", "pom.xml (Spring Boot)", "high", 8080)
        add("build", f"{mvn} -q -DskipTests package", "pom.xml", "high")
        add("test", f"{mvn} -q test", "pom.xml", "high")
    gradle = next((p for p in (root / "build.gradle", root / "build.gradle.kts") if p.is_file()), None)
    if gradle:
        gw = "./gradlew" if (root / "gradlew").exists() else "gradle"
        if "spring" in read_text(gradle):
            add("start", f"{gw} bootRun", gradle.name, "high", 8080)
        add("build", f"{gw} build -x test", gradle.name, "high")
        add("test", f"{gw} test", gradle.name, "high")
    if list(root.glob("*.csproj")) or list(root.glob("*.sln")):
        add("start", "dotnet run", ".csproj/.sln", "medium")
        add("build", "dotnet build", ".csproj/.sln", "high")
        add("test", "dotnet test", ".csproj/.sln", "high")
    if (root / "mix.exs").is_file():
        if "phoenix" in read_text(root / "mix.exs"):
            typ("web")
            add("start", "mix phx.server", "mix.exs (Phoenix)", "high", 4000)
        add("test", "mix test", "mix.exs", "high")

    for name in ("compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml"):
        if (root / name).is_file():
            out["services"] = {"file": name, "check": "docker compose ps --services --status running",
                               "start": "docker compose up -d <service>", "stop": "docker compose stop <service>"}
            out["notes"].append(f"{name} defines backing services. Start only the ones not already running, "
                                "outside `app start`; stop only those; never `docker compose down`.")
            break
    for name in ("Procfile.dev", "Procfile"):
        for line in read_text(root / name).splitlines():
            if line.startswith("web:"):
                add("start", line[4:].strip(), name, "medium")
    makefile = read_text(root / "Makefile")
    targets = set(re.findall(r"^([A-Za-z0-9_.-]+)\s*:(?!=)", makefile, re.M))
    for target in ("dev", "run", "start", "serve", "up"):
        if target in targets:
            add("start", f"make {target}", "Makefile", "medium")
    if "build" in targets:
        add("build", "make build", "Makefile", "medium")
    if "test" in targets:
        add("test", "make test", "Makefile", "medium")
    if (root / "index.html").is_file() and not pkg.is_file():
        typ("web")
        add("start", "python3 -m http.server 8000 --bind 127.0.0.1", "index.html (static)", "low", 8000)

    readme = next((p for p in sorted(root.glob("README*")) if p.is_file()), None)
    if readme:
        for number, line in enumerate(read_text(readme).splitlines(), 1):
            match = README_CMD.match(line.strip())
            if match and len(out["readme_commands"]) < 40:
                out["readme_commands"].append({"line": number, "cmd": match.group(1)[:200]})
    example = next((n for n in (".env.example", ".env.sample", ".env.template") if (root / n).is_file()), None)
    ignored = None
    if example:
        probe = git(root, "check-ignore", "-q", ".env")
        ignored = None if probe is None else probe.returncode == 0
    out["env"] = {"example": example, "env_exists": (root / ".env").is_file(), "env_ignored": ignored}
    if not out["start"]:
        out["notes"].append("No start command detected: read the README or ask the user.")
    emit(out)


# ---------------------------------------------------------------- app

def pid_alive(pid: int) -> bool:
    if os.name == "nt":
        r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True)
        return str(pid) in r.stdout
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    try:  # A zombie still answers kill(0); treat it as dead.
        status = Path(f"/proc/{pid}/stat").read_text().split(") ")[-1][:1]
        return status != "Z"
    except OSError:
        return True


def port_in_use(port: int) -> bool:
    for host in ("127.0.0.1", "::1"):
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            continue
    return False


def load_procs(run_dir: Path) -> dict:
    path = run_dir / "processes.json"
    return load_json(path, "processes.json") if path.exists() else {}


def cmd_app_start(a) -> None:
    run_dir, run = open_run(a.run_dir)
    procs = load_procs(run_dir)
    current = procs.get(a.name)
    if current and not current.get("stopped_at") and pid_alive(current["pid"]):
        fail(EXIT_CONFLICT, f"process '{a.name}' is already running (pid {current['pid']})",
             f"Stop it with `app stop --name {a.name}`, or start the new process with another --name.")
    if a.port and port_in_use(a.port):
        fail(EXIT_CONFLICT, f"port {a.port} is already in use",
             "If the app already runs there, use the Local-reuse branch (`app wait --url`); "
             "otherwise free the port or start the app on another one.")
    cwd = Path(a.cwd).expanduser().resolve() if a.cwd else Path(run["root"])
    env = dict(os.environ)
    for pair in a.env or []:
        if "=" not in pair:
            fail(EXIT_INPUT, f"--env {pair!r} is not KEY=VALUE", "Pass environment overrides as KEY=VALUE.")
        key, value = pair.split("=", 1)
        env[key] = value
    log = run_dir / "logs" / f"{a.name}.log"
    handle = open(log, "ab")
    kwargs = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    started = time.time()
    try:
        proc = subprocess.Popen(a.cmd, shell=True, cwd=str(cwd), env=env, stdin=subprocess.DEVNULL,
                                stdout=handle, stderr=subprocess.STDOUT, **kwargs)
    except OSError as exc:
        fail(EXIT_INPUT, f"could not start {a.cmd!r}: {exc}", "Check the command and --cwd.")
    finally:
        handle.close()
    time.sleep(1.0)
    code = proc.poll()
    procs[a.name] = {"pid": proc.pid, "pgid": proc.pid, "cmd": a.cmd, "cwd": str(cwd), "port": a.port,
                     "log": str(log), "started_at": iso(), "started_epoch": started}
    save_json(run_dir / "processes.json", procs)
    if code is not None:
        procs[a.name]["stopped_at"] = iso()
        procs[a.name]["exit_code"] = code
        save_json(run_dir / "processes.json", procs)
        deep_merge(run, {"app": {"ready": False, "start_cmd": a.cmd, "exit_code": code}})
        save_json(run_dir / "run.json", run)
        fail(EXIT_FAIL, [f"'{a.cmd}' exited with code {code} within 1s", "log tail:\n" + tail(log)],
             "Read the log tail. A detaching command (docker compose up -d) is a service, not the app: "
             "start it outside `app start`. Otherwise record the launch finding (SKILL.md Step 2.5).")
    emit({"name": a.name, "pid": proc.pid, "log": str(log), "port": a.port, "cwd": str(cwd)})


def http_status(url: str) -> int | None:
    context = ssl._create_unverified_context() if url.startswith("https://") else None
    request = urllib.request.Request(url, headers={"User-Agent": "user-test/1"})
    try:
        with urllib.request.urlopen(request, timeout=5, context=context) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except (urllib.error.URLError, OSError, ValueError):
        return None


def cmd_app_wait(a) -> None:
    run_dir, run = open_run(a.run_dir)
    proc = load_procs(run_dir).get(a.name)
    url = a.url
    if not url and not proc:
        fail(EXIT_INPUT, f"no --url given and no process named '{a.name}' was started by this run",
             "Pass --url for an app that is already running, or `app start` it first.")
    if not url and proc.get("port"):
        url = f"http://localhost:{proc['port']}/"
    started = time.time()
    deadline = started + a.timeout
    last = None
    while True:
        if not url and proc:
            match = URL_RE.search(ANSI_RE.sub("", read_text(Path(proc["log"]))))
            if match:
                url = match.group(0).replace("0.0.0.0", "127.0.0.1").rstrip(".,;)")
        if proc and (proc.get("stopped_at") or not pid_alive(proc["pid"])):
            deep_merge(run, {"app": {"ready": False, "url": url}})
            save_json(run_dir / "run.json", run)
            fail(EXIT_FAIL, [f"process '{a.name}' exited before the app became ready",
                             "log tail:\n" + tail(Path(proc["log"]))],
                 "Read the log tail; fix the start problem, then `app start` again.")
        if url:
            last = http_status(url)
            if last is not None and last < 500:
                break
        if time.time() >= deadline:
            deep_merge(run, {"app": {"ready": False, "url": url, "last_status": last}})
            save_json(run_dir / "run.json", run)
            detail = "no URL found in the log" if not url else \
                f"{url} answered {last}" if last else f"{url} did not answer"
            errors = [f"app not ready after {a.timeout}s: {detail}"]
            if proc:
                errors.append("log tail:\n" + tail(Path(proc["log"])))
            fail(EXIT_FAIL, errors, "Pass --url if the app listens elsewhere, raise --timeout for slow "
                 "starts, or fix the startup error shown in the log.")
        time.sleep(a.interval)
    origin = proc["started_epoch"] if proc and proc.get("started_epoch") and not proc.get("stopped_at") else started
    seconds = round(time.time() - origin, 2)
    deep_merge(run, {"app": {"ready": True, "url": url, "status": last, "ready_seconds": seconds,
                             "reused": proc is None}})
    if proc:
        run["app"]["start_cmd"] = proc["cmd"]
    save_json(run_dir / "run.json", run)
    emit({"ready": True, "url": url, "status": last, "seconds": seconds, "reused": proc is None})


def cmd_app_status(a) -> None:
    run_dir, _ = open_run(a.run_dir)
    out = {}
    for name, proc in load_procs(run_dir).items():
        out[name] = {"pid": proc["pid"], "cmd": proc["cmd"], "alive": False if proc.get("stopped_at") else pid_alive(proc["pid"]),
                     "stopped_at": proc.get("stopped_at"), "log": proc["log"]}
    emit({"processes": out, "running": sorted(n for n, p in out.items() if p["alive"])})


def stop_one(proc: dict) -> str:
    pid, pgid = proc["pid"], proc.get("pgid", proc["pid"])
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
        return "stopped"
    if pid_alive(pid):
        try:
            if os.getpgid(pid) != pgid:
                return "skipped: pid reused by another process"
        except ProcessLookupError:
            pass
    try:
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        return "already exited"
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            os.killpg(pgid, 0)
        except ProcessLookupError:
            return "stopped"
        if not pid_alive(pid):
            # Leader gone; give the rest of the group a moment.
            time.sleep(0.2)
            try:
                os.killpg(pgid, 0)
            except ProcessLookupError:
                return "stopped"
        time.sleep(0.2)
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    return "killed"


def cmd_app_stop(a) -> None:
    run_dir, _ = open_run(a.run_dir)
    procs = load_procs(run_dir)
    if a.name and a.name not in procs:
        fail(EXIT_INPUT, f"no process named '{a.name}' was started by this run",
             f"Known names: {', '.join(procs) or 'none'}. Only processes started with `app start` can be stopped.")
    result = {}
    for name in [a.name] if a.name else list(procs):
        proc = procs[name]
        if proc.get("stopped_at"):
            result[name] = "already stopped"
            continue
        result[name] = stop_one(proc)
        if not result[name].startswith("skipped"):
            proc["stopped_at"] = iso()
    save_json(run_dir / "processes.json", procs)
    emit({"stopped": result})


# ---------------------------------------------------------------- features, findings, coverage

def validate_features(data) -> tuple[list[str], dict]:
    errors, summary = [], {"areas": 0, "in_scope_areas": 0, "journeys": 0, "by_area": {}}
    if not isinstance(data, dict) or not isinstance(data.get("areas"), list) or not data["areas"]:
        return ["features.json needs a non-empty \"areas\" list"], summary
    app = data.get("app") or {}
    if app.get("type") and app["type"] not in APP_TYPES:
        errors.append(f"app.type {app['type']!r} must be one of {APP_TYPES}")
    area_ids, journey_ids = set(), set()
    for i, area in enumerate(data["areas"]):
        where = f"areas[{i}]"
        if not isinstance(area, dict):
            errors.append(f"{where} must be an object")
            continue
        aid = area.get("id", "")
        if not isinstance(aid, str) or not ID_RE.match(aid):
            errors.append(f"{where}.id {aid!r} must be lowercase kebab-case")
        elif aid in area_ids:
            errors.append(f"{where}.id {aid!r} is duplicated")
        area_ids.add(aid)
        if not area.get("name"):
            errors.append(f"{where} ({aid}) needs a name")
        in_scope = area.get("in_scope", True)
        journeys = area.get("journeys") or []
        if in_scope and not journeys:
            errors.append(f"area {aid!r} is in scope but has no journeys")
        for j, journey in enumerate(journeys):
            jwhere = f"area {aid!r} journeys[{j}]"
            jid = journey.get("id", "") if isinstance(journey, dict) else ""
            if not isinstance(jid, str) or not ID_RE.match(jid):
                errors.append(f"{jwhere}.id {jid!r} must be lowercase kebab-case")
                continue
            if jid in journey_ids:
                errors.append(f"journey id {jid!r} is duplicated")
            journey_ids.add(jid)
            for field in ("goal", "entry", "source"):
                if not journey.get(field):
                    errors.append(f"journey {jid!r} needs a non-empty {field!r}")
            for field in ("preconditions", "side_effects"):
                if field in journey and not isinstance(journey[field], list):
                    errors.append(f"journey {jid!r}: {field!r} must be a list")
        summary["areas"] += 1
        if in_scope:
            summary["in_scope_areas"] += 1
            summary["journeys"] += len(journeys)
            summary["by_area"][aid] = len(journeys)
    return errors, summary


def in_scope_journeys(features: dict) -> dict:
    out = {}
    for area in features.get("areas", []):
        if area.get("in_scope", True):
            for journey in area.get("journeys") or []:
                out[journey["id"]] = area["id"]
    return out


def cmd_check_features(a) -> None:
    run_dir, run = open_run(a.run_dir)
    features = load_json(run_dir / "features.json", "features.json")
    errors, summary = validate_features(features)
    if isinstance(run.get("scope"), list) and not errors:
        names = [f"{x.get('id', '')} {x.get('name', '')}".lower() for x in features["areas"] if x.get("in_scope", True)]
        for focus in run["scope"]:
            words = [w for w in re.split(r"[^a-z0-9]+", focus.lower()) if w]
            if not any(all(w in n for w in words) or focus.lower() in n for n in names):
                errors.append(f"focus feature {focus!r} matches no in-scope area id or name")
    if errors:
        fail(EXIT_FAIL, errors, "Fix each listed problem in features.json, then re-run `check-features`.")
    emit(summary)


def evidence_errors(run_dir: Path, paths, label: str) -> list[str]:
    errors = []
    if not isinstance(paths, list) or not paths:
        return [f"{label} needs at least one evidence path"]
    for raw in paths:
        if not isinstance(raw, str) or not raw:
            errors.append(f"{label} has an empty evidence entry")
            continue
        if os.path.isabs(raw):
            errors.append(f"{label} evidence {raw!r} must be relative to the run dir")
            continue
        path = (run_dir / raw).resolve()
        if run_dir not in path.parents:
            errors.append(f"{label} evidence {raw!r} points outside the run dir")
        elif not path.is_file():
            errors.append(f"{label} evidence {raw!r} does not exist")
    return errors


def finding_errors(run_dir: Path, f: dict, journeys: set[str] | None) -> list[str]:
    fid = f.get("id") or "?"
    label = f"finding {fid!r}"
    errors = []
    if not isinstance(f.get("id"), str) or not ID_RE.match(f.get("id", "")):
        errors.append(f"{label}: id must be lowercase kebab-case, e.g. checkout-1")
    for field in ("title", "impact", "where", "expected", "actual", "complexity_reason"):
        if not isinstance(f.get(field), str) or not f.get(field).strip():
            errors.append(f"{label}: {field!r} must be a non-empty string")
    for field, allowed in (("kind", KINDS), ("category", CATEGORIES), ("severity", SEVERITIES),
                           ("complexity", COMPLEXITIES), ("status", STATUSES)):
        if f.get(field, "open" if field == "status" else None) not in allowed:
            errors.append(f"{label}: {field} {f.get(field)!r} must be one of {allowed}")
    if not isinstance(f.get("steps"), list) or not f.get("steps"):
        errors.append(f"{label}: 'steps' must be a non-empty list of user actions")
    if journeys is not None and f.get("journey") is not None and f.get("journey") not in journeys:
        errors.append(f"{label}: journey {f.get('journey')!r} is not in features.json or the coverage rows")
    if f.get("category") == "performance":
        metric = f.get("metric") or {}
        if not all(k in metric for k in ("name", "value", "unit", "threshold")):
            errors.append(f"{label}: performance findings need metric {{name, value, unit, threshold}}")
    errors += evidence_errors(run_dir, f.get("evidence"), label)
    return errors


def coverage_errors(row: dict, idx: str) -> list[str]:
    errors = []
    jid = row.get("journey")
    label = f"coverage row {idx} ({jid!r})"
    if not isinstance(jid, str) or not jid:
        errors.append(f"{label}: needs a journey id")
    if row.get("status") not in COVERAGE:
        errors.append(f"{label}: status {row.get('status')!r} must be one of {COVERAGE}")
    if row.get("status") in ("blocked", "skipped") and not (row.get("reason") or "").strip():
        errors.append(f"{label}: a {row.get('status')} journey needs a reason")
    if row.get("status") == "fail" and not row.get("findings"):
        errors.append(f"{label}: a failed journey must list the finding ids that explain it")
    return errors


def cmd_collect(a) -> None:
    run_dir, run = open_run(a.run_dir)
    features_path = run_dir / "features.json"
    blocked = run.get("app", {}).get("ready") is False
    features = None
    if features_path.exists():
        features = load_json(features_path, "features.json")
        ferrors, _ = validate_features(features)
        if ferrors:
            fail(EXIT_FAIL, ferrors, "Fix features.json (`check-features`) before collecting.")
    elif not blocked:
        fail(EXIT_INPUT, "features.json is missing", "Run Step 3 (map the features) before `collect`.")
    expected = in_scope_journeys(features) if features else {}
    files = sorted((run_dir / "areas").glob("*.json"))
    if a.area:
        files = [p for p in files if p.stem == a.area]
        if not files:
            fail(EXIT_INPUT, f"areas/{a.area}.json does not exist", "Write the area file first (testing.md §9).")
        expected = {j: area for j, area in expected.items() if area == a.area}
    previous = {}
    if (run_dir / "findings.json").exists():
        previous = {f["id"]: f for f in load_json(run_dir / "findings.json", "findings.json").get("findings", [])
                    if isinstance(f, dict) and "id" in f}
    errors, coverage, findings, perf, notes = [], [], [], [], []
    seen_findings, seen_journeys = {}, {}
    for path in files:
        data = load_json(path, path.name)
        if not isinstance(data, dict):
            errors.append(f"{path.name} must hold a JSON object (testing.md section 9)")
            continue
        area = data.get("area") or path.stem
        bad = [k for k in ("coverage", "findings", "perf") if any(not isinstance(x, dict) for x in data.get(k) or [])]
        if bad:
            errors.append(f"{path.name}: every entry in {', '.join(bad)} must be a JSON object")
            continue
        for i, row in enumerate(data.get("coverage") or []):
            errors += coverage_errors(row, f"{path.name}[{i}]")
            jid = row.get("journey")
            if jid in seen_journeys:
                errors.append(f"journey {jid!r} has coverage rows in both {seen_journeys[jid]} and {path.name}")
            seen_journeys[jid] = path.name
            coverage.append({**row, "area": area, "discovered": jid not in expected})
        for f in data.get("findings") or []:
            if f.get("id") in seen_findings:
                errors.append(f"finding id {f.get('id')!r} is used in {seen_findings[f['id']]} and {path.name}")
                continue
            seen_findings[f.get("id")] = path.name
            merged = dict(f)
            merged.setdefault("status", "open")
            merged["area"] = area
            old = previous.get(f.get("id"))
            if old:
                for key in ("status", "fix", "plan", "duplicate_of", "complexity", "complexity_reason"):
                    if key in old:
                        merged[key] = old[key]
            findings.append(merged)
        perf += [{**p, "area": area} for p in data.get("perf") or []]
        notes += [f"{area}: {n}" for n in data.get("notes") or []]
    known = set(expected) | set(seen_journeys)
    for f in findings:
        errors += finding_errors(run_dir, f, known)
    for row in coverage:
        for fid in row.get("findings") or []:
            if fid not in seen_findings:
                errors.append(f"coverage row for {row.get('journey')!r} cites unknown finding {fid!r}")
    missing = sorted(j for j in expected if j not in seen_journeys)
    if missing:
        errors.append("journeys with no coverage row: " + ", ".join(missing))
    if errors:
        fail(EXIT_FAIL, errors, "Fix the area files under areas/ (or re-test the listed journeys), "
             "then run `collect` again.")
    titles = {}
    duplicates = []
    for f in findings:
        key = re.sub(r"[^a-z0-9]+", " ", f["title"].lower()).strip()
        if key in titles:
            duplicates.append([titles[key], f["id"]])
        titles[key] = f["id"]
    if not a.check_only and not a.area:
        save_json(run_dir / "findings.json", {"findings": findings, "coverage": coverage, "perf": perf,
                                              "notes": notes})

    def count(items, key):
        out = {}
        for item in items:
            out[item.get(key)] = out.get(item.get(key), 0) + 1
        return out

    emit({"written": not a.check_only and not a.area, "findings": len(findings),
          "by_severity": count(findings, "severity"), "by_category": count(findings, "category"),
          "by_kind": count(findings, "kind"), "coverage": count(coverage, "status"),
          "discovered_journeys": [r["journey"] for r in coverage if r["discovered"]],
          "possible_duplicates": duplicates, "areas_collected": [p.name for p in files]})


def cmd_update(a) -> None:
    run_dir, run = open_run(a.run_dir)
    if a.note:
        run.setdefault("notes", []).append(a.note)
        save_json(run_dir / "run.json", run)
        emit({"noted": a.note, "notes": len(run["notes"])})
        return
    if a.json_file and not Path(a.json_file).is_file():
        fail(EXIT_INPUT, f"--json-file {a.json_file} does not exist", "Write the JSON patch to that path first.")
    raw = Path(a.json_file).read_text(encoding="utf-8") if a.json_file else a.json
    if raw is None:
        fail(EXIT_INPUT, "update needs --json or --json-file", "Pass the patch as a JSON object.")
    try:
        patch = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(EXIT_INPUT, f"--json is not valid JSON: {exc.msg} at col {exc.colno}",
             "Quote the JSON for the shell, or write it to a file and pass --json-file.")
    if not isinstance(patch, dict):
        fail(EXIT_INPUT, "the patch must be a JSON object", "Pass an object such as '{\"status\": \"open\"}'.")
    if a.add_finding:
        patch.setdefault("status", "open")
        problems = [e for e in finding_errors(run_dir, patch, None)]
        if problems:
            fail(EXIT_INPUT, problems, "Add the missing fields; the full shape is in SKILL.md Step 2.5.")
        path = run_dir / "areas" / "_run.json"
        data = load_json(path, "_run.json") if path.exists() else {"area": "_run", "coverage": [], "findings": []}
        data["findings"] = [f for f in data["findings"] if f.get("id") != patch["id"]] + [patch]
        save_json(path, data)
        emit({"added": patch["id"], "file": str(path), "next": "run `collect` to merge it"})
        return
    if not a.finding:
        deep_merge(run, patch)
        save_json(run_dir / "run.json", run)
        emit({"updated": "run.json", "keys": sorted(patch)})
        return
    store_path = run_dir / "findings.json"
    if not store_path.exists():
        fail(EXIT_INPUT, "findings.json is missing", "Run `collect` before updating a finding.")
    store = load_json(store_path, "findings.json")
    target = next((f for f in store.get("findings", []) if f.get("id") == a.finding), None)
    if target is None:
        fail(EXIT_INPUT, f"no finding with id {a.finding!r}",
             "Run `collect` first, and use an id from findings.json.")
    deep_merge(target, patch)
    for field, allowed in (("status", STATUSES), ("severity", SEVERITIES), ("complexity", COMPLEXITIES)):
        if target.get(field) not in allowed:
            fail(EXIT_INPUT, f"{field} {target.get(field)!r} must be one of {allowed}", "Correct the patch.")
    save_json(store_path, store)
    emit({"updated": a.finding, "status": target.get("status"), "keys": sorted(patch)})


# ---------------------------------------------------------------- build-check

def run_logged(cmd: str, cwd: Path, log: Path, timeout: int) -> dict:
    started = time.time()
    kwargs = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    with open(log, "wb") as handle:
        proc = subprocess.Popen(cmd, shell=True, cwd=str(cwd), stdin=subprocess.DEVNULL, stdout=handle,
                                stderr=subprocess.STDOUT, **kwargs)
        try:
            code = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
            else:
                os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
            code = "timeout"
    return {"cmd": cmd, "exit": code, "seconds": round(time.time() - started, 2), "log": str(log),
            "tail": tail(log, 40)}


def cmd_build_check(a) -> None:
    run_dir, run = open_run(a.run_dir)
    if not a.build and not a.test:
        fail(EXIT_INPUT, "build-check needs --build and/or --test", "Pass the commands from `detect`.")
    if not ID_RE.match(a.label):
        fail(EXIT_INPUT, f"--label {a.label!r} must be lowercase kebab-case", "Use e.g. baseline, final, checkout-1-a1.")
    cwd = Path(a.cwd).expanduser().resolve() if a.cwd else Path(run["root"])
    result = {"label": a.label, "at": iso()}
    for kind in ("build", "test"):
        cmd = getattr(a, kind)
        if cmd:
            result[kind] = run_logged(cmd, cwd, run_dir / "logs" / f"{a.label}-{kind}.log", a.timeout)
    run.setdefault("checks", {})[a.label] = {k: ({kk: vv for kk, vv in v.items() if kk != "tail"}
                                                 if isinstance(v, dict) else v) for k, v in result.items()}
    save_json(run_dir / "run.json", run)
    emit(result)
    if any(isinstance(result.get(k), dict) and result[k]["exit"] != 0 for k in ("build", "test")):
        sys.exit(EXIT_FAIL)


# ---------------------------------------------------------------- checkpoint

def project_path(root: Path, raw: str) -> tuple[Path, str]:
    path = Path(raw).expanduser()
    path = (path if path.is_absolute() else root / path).resolve()
    if root != path and root not in path.parents:
        fail(EXIT_INPUT, f"{raw!r} is outside the project root {root}", "Checkpoint only files inside the project.")
    rel = path.relative_to(root).as_posix()
    if rel.split("/")[0] in (RUN_ROOT, ".git"):
        fail(EXIT_INPUT, f"{raw!r} is inside {rel.split('/')[0]}/", "Checkpoint project source files only.")
    if path.is_dir():
        fail(EXIT_INPUT, f"{raw!r} is a directory", "Pass each file the fix will edit or create.")
    return path, rel


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cmd_checkpoint(a) -> None:
    run_dir, run = open_run(a.run_dir)
    root = Path(run["root"])
    if not ID_RE.match(a.fix):
        fail(EXIT_INPUT, f"--fix {a.fix!r} must be the finding id", "Pass the finding id, e.g. checkout-1.")
    base = run_dir / "checkpoints" / a.fix
    manifest_path = base / "manifest.json"
    manifest = load_json(manifest_path, "checkpoint manifest") if manifest_path.exists() else {"fix": a.fix, "files": []}
    entries = {e["path"]: e for e in manifest["files"]}
    if a.action == "save":
        if not a.paths:
            fail(EXIT_INPUT, "checkpoint save needs at least one file path", "List each file the fix will touch.")
        saved, new, skipped = [], [], []
        for raw in a.paths:
            path, rel = project_path(root, raw)
            if rel in entries:
                skipped.append(rel)
                continue
            if path.exists():
                dest = base / "files" / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, dest)
                entries[rel] = {"path": rel, "existed": True, "sha256": sha256(path)}
                saved.append(rel)
            else:
                entries[rel] = {"path": rel, "existed": False}
                new.append(rel)
        base.mkdir(parents=True, exist_ok=True)
        manifest["files"] = list(entries.values())
        manifest.setdefault("saved_at", iso())
        save_json(manifest_path, manifest)
        emit({"fix": a.fix, "saved": saved, "new": new, "skipped": skipped})
        return
    if not manifest_path.exists():
        fail(EXIT_INPUT, f"no checkpoint for {a.fix!r}", "Run `checkpoint save` before editing files for this fix.")
    if a.action == "restore":
        restored, deleted = [], []
        for entry in manifest["files"]:
            path = root / entry["path"]
            if entry["existed"]:
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(base / "files" / entry["path"], path)
                shutil.copymode(base / "files" / entry["path"], path)
                os.utime(path, None)  # A fresh mtime makes incremental builds pick up the restore.
                restored.append(entry["path"])
            elif path.is_file():
                path.unlink()
                deleted.append(entry["path"])
        manifest["restored_at"] = iso()
        save_json(manifest_path, manifest)
        emit({"fix": a.fix, "restored": restored, "deleted": deleted})
        return
    files, chunks = [], []
    for entry in manifest["files"]:
        path = root / entry["path"]
        before = (base / "files" / entry["path"]).read_text(encoding="utf-8", errors="replace").splitlines(True) \
            if entry["existed"] else []
        after = path.read_text(encoding="utf-8", errors="replace").splitlines(True) if path.is_file() else []
        diff = list(difflib.unified_diff(before, after, f"a/{entry['path']}", f"b/{entry['path']}"))
        added = sum(1 for d in diff if d.startswith("+") and not d.startswith("+++"))
        removed = sum(1 for d in diff if d.startswith("-") and not d.startswith("---"))
        if diff:
            files.append({"path": entry["path"], "added": added, "removed": removed})
            chunks.append("".join(diff))
    patch = base / "fix.diff"
    patch.write_text("\n".join(chunks), encoding="utf-8")
    emit({"fix": a.fix, "files": files, "diff": str(patch.relative_to(run_dir)),
          "lines_changed": sum(f["added"] + f["removed"] for f in files)})


# ---------------------------------------------------------------- report

def report_errors(run_dir: Path, run: dict, store: dict) -> list[str]:
    errors = []
    findings = store.get("findings", [])
    ids = {f.get("id") for f in findings}
    journeys = {r.get("journey") for r in store.get("coverage", [])}
    for f in findings:
        errors += finding_errors(run_dir, f, journeys | {None})
        label = f"finding {f.get('id')!r}"
        status, fix, plan = f.get("status", "open"), f.get("fix") or {}, f.get("plan") or {}
        if status == "fixed-verified":
            if not fix.get("files"):
                errors.append(f"{label}: fixed-verified needs fix.files")
            if (fix.get("build") or {}).get("exit") != 0:
                errors.append(f"{label}: fixed-verified needs fix.build.exit == 0 (the build after the fix)")
            tests = fix.get("tests") or {}
            if tests.get("new_failures") != 0 and tests.get("result") != "no test suite":
                errors.append(f"{label}: fixed-verified needs fix.tests.new_failures == 0 "
                              "(or fix.tests.result == 'no test suite')")
            verification = fix.get("verification") or {}
            if verification.get("verdict") != "pass":
                errors.append(f"{label}: fixed-verified needs fix.verification.verdict == 'pass' from the verifier")
            errors += evidence_errors(run_dir, verification.get("evidence"), f"{label} verification")
        if status == "fix-failed" and not fix.get("restored"):
            errors.append(f"{label}: fix-failed needs fix.restored == true (run `checkpoint restore`)")
        if status in ("open", "fix-failed"):
            if not (plan.get("approach") or "").strip():
                errors.append(f"{label}: needs plan.approach (how to fix or improve it)")
            if plan.get("effort") not in EFFORTS:
                errors.append(f"{label}: plan.effort must be one of {EFFORTS}")
            if plan.get("risk") not in RISKS:
                errors.append(f"{label}: plan.risk must be one of {RISKS}")
        if status == "duplicate" and (f.get("duplicate_of") not in ids or f.get("duplicate_of") == f.get("id")):
            errors.append(f"{label}: duplicate_of must name another finding id")
    if any(f.get("status") in ("fixed-verified", "fix-failed") for f in findings):
        if "final" not in run.get("checks", {}):
            errors.append("fixes were attempted but run.json has no checks.final: run "
                          "`build-check --label final` after the last fix")
    return errors


def run_result(run: dict, store: dict) -> tuple[str, list[str]]:
    coverage = store.get("coverage", [])
    if not any(r.get("status") in ("pass", "fail") for r in coverage):
        why = "the app never became ready" if run.get("app", {}).get("ready") is False else "no journey ran"
        return "BLOCKED", [f"{why}, so no journey was tested"]
    reasons = []
    gaps = [r for r in coverage if r.get("status") in ("blocked", "skipped")]
    if gaps:
        reasons.append(f"{len(gaps)} journey(s) blocked or skipped")
    final = run.get("checks", {}).get("final") or {}
    if any(isinstance(final.get(k), dict) and final[k].get("exit") != 0 for k in ("build", "test")):
        reasons.append("the final build or test check did not exit 0")
    return ("PARTIAL" if reasons else "COMPLETE"), reasons


def decision_lines(run: dict, store: dict) -> list[str]:
    lines = []
    fixed = [f for f in store.get("findings", []) if f.get("status") == "fixed-verified"]
    if fixed and run.get("commits"):
        lines.append(f"Review the {len(fixed)} verified fix(es), committed as: {', '.join(run['commits'])}.")
    elif fixed:
        files = sorted({p for f in fixed for p in (f.get("fix") or {}).get("files", [])})
        lines.append(f"Review and commit the {len(fixed)} verified fix(es); they are uncommitted. "
                     f"Files: {', '.join(files)}.")
    approvals = [r for r in store.get("coverage", [])
                 if r.get("status") == "blocked" and "approval" in (r.get("reason") or "").lower()]
    if approvals:
        lines.append("Approve or decline the side-effect journeys: "
                     + ", ".join(r["journey"] for r in approvals) + ".")
    return lines or ["No approval needed."]


def sort_key(f: dict):
    effort = (f.get("plan") or {}).get("effort")
    return (SEVERITIES.index(f["severity"]) if f.get("severity") in SEVERITIES else 9,
            EFFORTS.index(effort) if effort in EFFORTS else 9, f.get("id", ""))


def summarize(run: dict, features: dict | None, store: dict) -> dict:
    findings = sorted(store.get("findings", []), key=sort_key)
    coverage = store.get("coverage", [])
    live = [f for f in findings if f.get("status") != "duplicate"]
    sev = {s: sum(1 for f in live if f.get("severity") == s) for s in SEVERITIES}
    cov = {s: sum(1 for r in coverage if r.get("status") == s) for s in COVERAGE}
    by_status = {s: [f for f in live if f.get("status") == s] for s in STATUSES}
    result, reasons = run_result(run, store)
    scope = run.get("scope")
    scope = scope if isinstance(scope, str) else ", ".join(scope or [])
    gaps = [r for r in coverage if r.get("status") in ("blocked", "skipped")]
    uncertainty = [f"Not tested: {r['journey']} ({r['status']}): {r.get('reason')}" for r in gaps]
    if any(p.get("build") == "dev" for p in store.get("perf", [])):
        uncertainty.append("Performance samples marked dev come from a development build; "
                           "production numbers usually differ.")
    uncertainty += list(run.get("notes", [])) + list(store.get("notes", []))
    if not uncertainty:
        uncertainty.append("No untested journeys or open questions recorded within the checks above.")
    app = run.get("app", {})
    details = [f"Root: {run.get('root')}",
               f"App: {app.get('url') or run.get('url') or '—'} · start {app.get('start_cmd') or '—'} · ready in "
               f"{app.get('ready_seconds', '—')}s" + (" (reused a running app)" if app.get("reused") else ""),
               f"Driver: {run.get('driver') or '—'}"]
    for label, check in sorted(run.get("checks", {}).items()):
        parts = [f"{k} `{v.get('cmd')}` exit {v.get('exit')} ({v.get('seconds')}s)"
                 for k, v in check.items() if isinstance(v, dict)]
        details.append(f"Check {label}: " + "; ".join(parts))
    return {
        "name": (features or {}).get("app", {}).get("name") or Path(run["root"]).name,
        "result": result, "reasons": reasons,
        "meta": f"{run.get('started_at', '')} · branch {run.get('branch')} · scope {scope} · fix mode {run.get('fix_mode')}",
        "headline": (f"{len(coverage)} journeys: {cov['pass']} pass, {cov['fail']} fail, {cov['blocked']} blocked, "
                     f"{cov['skipped']} skipped. {len(live)} findings: "
                     + ", ".join(f"{sev[s]} {s}" for s in SEVERITIES)
                     + f". {len(by_status['fixed-verified'])} fixed and verified, "
                     f"{len(by_status['fix-failed'])} fix failed, {len(by_status['open'])} open."),
        "cards": [["journeys", len(coverage)], ["pass", cov["pass"]], ["fail", cov["fail"]],
                  ["blocked or skipped", cov["blocked"] + cov["skipped"]], ["findings", len(live)],
                  ["critical + high", sev["critical"] + sev["high"]],
                  ["fixed and verified", len(by_status["fixed-verified"])],
                  ["open", len(by_status["open"]) + len(by_status["fix-failed"])]],
        "decision": decision_lines(run, store), "findings": findings, "coverage": coverage,
        "perf": store.get("perf", []), "by_status": by_status, "uncertainty": uncertainty, "details": details,
    }


def md(text) -> str:
    return "—" if text is None or text == "" else str(text).replace("|", "\\|").replace("\n", " ")


def links(paths) -> str:
    return ", ".join(f"[{p}]({p})" for p in paths or []) or "—"


def build_markdown(s: dict) -> str:
    out = [f"# User test report: {s['name']}", "",
           f"**Result: {s['result']}**" + (f" ({'; '.join(s['reasons'])})" if s["reasons"] else "") + f" · {s['meta']}",
           "", s["headline"], "", "## Decision", ""] + [f"- {line}" for line in s["decision"]]
    fixed = s["by_status"]["fixed-verified"]
    if fixed:
        out += ["", "## Fixed and verified", "", "| ID | Severity | Title | Files | Verification evidence |",
                "|---|---|---|---|---|"]
        for f in fixed:
            fix = f.get("fix") or {}
            out.append(f"| [{f['id']}](#{f['id']}) | {f['severity']} | {md(f['title'])} | "
                       f"{md(', '.join(fix.get('files', [])))} | {links((fix.get('verification') or {}).get('evidence'))} |")
    pending = s["by_status"]["open"] + s["by_status"]["fix-failed"]
    if pending:
        out += ["", "## Plan for open findings", "", "| ID | Kind | Severity | Title | Approach | Effort | Risk |",
                "|---|---|---|---|---|---|---|"]
        for f in sorted(pending, key=sort_key):
            plan = f.get("plan") or {}
            failed = " (fix failed, reverted)" if f.get("status") == "fix-failed" else ""
            out.append(f"| [{f['id']}](#{f['id']}) | {f['kind']} | {f['severity']} | {md(f['title'])}{failed} | "
                       f"{md(plan.get('approach'))} | {md(plan.get('effort'))} | {md(plan.get('risk'))} |")
    out += ["", "## Findings", ""]
    for f in s["findings"]:
        fix, plan = f.get("fix") or {}, f.get("plan") or {}
        dup = f" (duplicate of {f['duplicate_of']})" if f.get("duplicate_of") else ""
        out += [f"### {f['id']}", "", f"**{f['title']}**", "",
                f"- {f['kind']} · {f['category']} · severity **{f['severity']}** · complexity {f['complexity']}"
                f" · status **{f.get('status', 'open')}**{dup}",
                f"- Why this severity: {f['impact']}",
                f"- Where: {f['where']}" + (f" (journey `{f['journey']}`)" if f.get("journey") else ""),
                f"- Complexity: {f['complexity_reason']}", "- Steps:"]
        out += [f"  {i}. {step}" for i, step in enumerate(f.get("steps", []), 1)]
        out += [f"- Expected: {f['expected']}", f"- Actual: {f['actual']}"]
        if f.get("metric"):
            m = f["metric"]
            out.append(f"- Measured: {m.get('name')} = {m.get('value')} {m.get('unit')} "
                       f"(threshold {m.get('threshold')} {m.get('unit')})")
        out.append(f"- Evidence: {links(f.get('evidence'))}")
        if fix:
            verification = fix.get("verification") or {}
            out.append(f"- Fix: {md(fix.get('summary'))} · files {md(', '.join(fix.get('files', [])))}"
                       f" · build exit {md((fix.get('build') or {}).get('exit'))}"
                       f" · tests {md((fix.get('tests') or {}).get('result'))}"
                       f" · attempts {md(fix.get('attempts'))} · verifier {md(verification.get('verdict'))}"
                       f" · verification evidence {links(verification.get('evidence'))}"
                       + (f" · diff [{fix['diff']}]({fix['diff']})" if fix.get("diff") else ""))
        if plan:
            out.append(f"- Plan: {md(plan.get('approach'))} · effort {md(plan.get('effort'))} · risk {md(plan.get('risk'))}")
        out.append("")
    out += ["## Coverage", "", "| Area | Journey | Status | Reason | Findings |", "|---|---|---|---|---|"]
    for row in s["coverage"]:
        found = " (discovered)" if row.get("discovered") else ""
        out.append(f"| {md(row.get('area'))} | {md(row.get('journey'))}{found} | {row.get('status')} | "
                   f"{md(row.get('reason'))} | {', '.join(row.get('findings') or []) or '—'} |")
    if s["perf"]:
        out += ["", "## Performance samples", "", "| Journey | Step | Metric | Value | Threshold | Build |",
                "|---|---|---|---|---|---|"]
        for p in s["perf"]:
            out.append(f"| {md(p.get('journey'))} | {md(p.get('step'))} | {md(p.get('metric'))} | "
                       f"{md(p.get('value'))} {p.get('unit', '')} | {md(p.get('threshold'))} | {md(p.get('build'))} |")
    out += ["", "## Uncertainty", ""] + [f"- {line}" for line in s["uncertainty"]]
    out += ["", "## Run details", ""] + [f"- {line}" for line in s["details"]]
    return "\n".join(out) + "\n"


HTML_TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>User test report</title>
<style>
:root{--bg:#fff;--fg:#1d2330;--muted:#5d6675;--line:#dde1e8;--card:#f6f7f9;--accent:#2457c5;
--critical:#b42318;--high:#c4320a;--medium:#a15c07;--low:#4b5565;--pass:#067647;--fail:#b42318;--blocked:#a15c07}
@media (prefers-color-scheme:dark){:root{--bg:#12151b;--fg:#e6e9ef;--muted:#9aa3b2;--line:#2b313c;--card:#1a1f27;
--accent:#7aa2ff;--critical:#ff8a80;--high:#ffab70;--medium:#f5c46b;--low:#b3bccb;--pass:#6ce0a6;--fail:#ff8a80;--blocked:#f5c46b}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:1100px;margin:0 auto;padding:24px 16px 64px}h1{font-size:1.5rem;margin:0 0 4px}h2{font-size:1.15rem;margin:32px 0 8px}
.muted{color:var(--muted)}.badge{display:inline-block;padding:1px 8px;border-radius:999px;font-size:.8rem;font-weight:600;border:1px solid currentColor}
.result{font-size:1rem;padding:3px 12px}.COMPLETE{color:var(--pass)}.PARTIAL{color:var(--blocked)}.BLOCKED{color:var(--fail)}
.critical{color:var(--critical)}.high{color:var(--high)}.medium{color:var(--medium)}.low{color:var(--low)}
.pass{color:var(--pass)}.fail{color:var(--fail)}.blocked,.skipped{color:var(--blocked)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin:16px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 12px}.card b{display:block;font-size:1.3rem}
.decision{border-left:4px solid var(--accent);background:var(--card);padding:8px 12px;border-radius:4px}
.filters{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:8px 0;position:sticky;top:0;background:var(--bg);padding:8px 0;z-index:1}
select,input,button{font:inherit;color:inherit;background:var(--card);border:1px solid var(--line);border-radius:6px;padding:4px 8px}
button{cursor:pointer}details{border:1px solid var(--line);border-radius:8px;margin:6px 0;background:var(--card)}
summary{cursor:pointer;padding:8px 12px;display:flex;gap:8px;flex-wrap:wrap;align-items:baseline;list-style:none}details[open] summary{border-bottom:1px solid var(--line)}
summary::-webkit-details-marker{display:none}summary::before{content:'▸';color:var(--muted)}details[open]>summary::before{content:'▾'}
#list>details{scroll-margin-top:var(--filters-h,72px)}
.body{padding:8px 16px}.body dt{font-weight:600;margin-top:6px}.body dd{margin:0 0 4px}
.missing{color:var(--muted);font-style:italic}.thumbs{display:flex;flex-wrap:wrap;gap:8px}.thumbs img{max-width:260px;max-height:180px;border:1px solid var(--line);border-radius:4px}
table{border-collapse:collapse;width:100%;font-size:.9rem}th,td{border-bottom:1px solid var(--line);padding:4px 6px;text-align:left;vertical-align:top}
.wrap{overflow-x:auto}.over{color:var(--fail);font-weight:600}code{font-size:.85em}
</style></head><body><main>
<header id="top"></header>
<section><h2>Findings</h2>
<div class="filters" role="group" aria-label="Filter findings">
<select id="f-severity" aria-label="Severity"></select><select id="f-category" aria-label="Category"></select>
<select id="f-status" aria-label="Status"></select><select id="f-kind" aria-label="Kind"></select>
<select id="f-area" aria-label="Area"></select><input id="f-text" type="search" placeholder="Search title or where" aria-label="Search">
<button id="f-reset" type="button">Reset filters</button><span id="f-count" class="muted" aria-live="polite"></span></div>
<div id="list"></div></section>
<section><h2>Coverage</h2><label><input type="checkbox" id="c-open"> Show only fail, blocked and skipped</label>
<div class="wrap"><table id="coverage"></table></div></section>
<section id="perf-section"><h2>Performance samples</h2><div class="wrap"><table id="perf"></table></div></section>
<section><h2>Uncertainty</h2><ul id="uncertainty"></ul></section>
<section><h2>Run details</h2><ul id="details"></ul></section>
</main>
<script type="application/json" id="data">__DATA__</script>
<script>
(()=>{
const D=JSON.parse(document.getElementById('data').textContent);const F=D.findings;
const el=(t,a={},...k)=>{const e=document.createElement(t);for(const[n,v]of Object.entries(a)){if(n==='class')e.className=v;else if(n==='text')e.textContent=v;else e.setAttribute(n,v)}for(const c of k)if(c!=null)e.append(c);return e};
const val=v=>(v===undefined||v===null||v==='')?el('span',{class:'missing',text:'not recorded'}):document.createTextNode(String(v));
const hdr=document.getElementById('top');
hdr.append(el('h1',{text:'User test report: '+D.name}),el('div',{},el('span',{class:'badge result '+D.result,text:D.result}),
document.createTextNode(' '+D.reasons.join('; '))),el('p',{class:'muted',text:D.meta}),el('p',{text:D.headline}));
const cards=el('div',{class:'cards'});for(const[k,v]of D.cards)cards.append(el('div',{class:'card'},el('b',{text:String(v)}),document.createTextNode(k)));hdr.append(cards);
const dec=el('div',{class:'decision'},el('strong',{text:'Decision'}));const dl=el('ul');D.decision.forEach(x=>dl.append(el('li',{text:x})));dec.append(dl);hdr.append(dec);
const opts={severity:D.enums.severity,category:D.enums.category,status:D.enums.status,kind:D.enums.kind,area:[...new Set(F.map(f=>f.area))].sort()};
for(const[k,list]of Object.entries(opts)){const s=document.getElementById('f-'+k);s.append(el('option',{value:'',text:'All '+k}));list.forEach(v=>s.append(el('option',{value:v,text:v})))}
function evidence(paths){const box=el('div',{class:'thumbs'});if(!paths||!paths.length){box.append(el('span',{class:'missing',text:'no evidence recorded'}));return box}
for(const p of paths){const a=el('a',{href:p,target:'_blank',rel:'noopener'});if(/\\.(png|jpe?g|gif|webp)$/i.test(p))a.append(el('img',{src:p,alt:'Evidence '+p,loading:'lazy'}));else a.append(document.createTextNode(p));box.append(a)}return box}
function row(dlist,label,node){dlist.append(el('dt',{text:label}),el('dd',{},node))}
function card(f){const d=el('details',{id:f.id});const st=f.status||'open';
d.append(el('summary',{},el('code',{text:f.id}),el('span',{class:'badge '+f.severity,text:f.severity}),el('strong',{text:f.title}),
el('span',{class:'muted',text:f.kind+' · '+f.category+' · '+st+(f.duplicate_of?' of '+f.duplicate_of:'')})));
const b=el('dl',{class:'body'});row(b,'Why this severity',val(f.impact));row(b,'Where',val(f.where+(f.journey?' (journey '+f.journey+')':'')));
row(b,'Complexity',val(f.complexity+': '+f.complexity_reason));const ol=el('ol');(f.steps||[]).forEach(s=>ol.append(el('li',{text:s})));row(b,'Steps',ol);
row(b,'Expected',val(f.expected));row(b,'Actual',val(f.actual));
if(f.metric){const m=f.metric;const over=Number(m.value)>Number(m.threshold);row(b,'Measured',el('span',{class:over?'over':'',text:m.name+' = '+m.value+' '+m.unit+' (threshold '+m.threshold+' '+m.unit+')'}))}
row(b,'Evidence',evidence(f.evidence));
if(f.fix){const x=f.fix,v=x.verification||{};const fx=el('div');fx.append(el('div',{text:'Summary: '+(x.summary||'—')}),el('div',{text:'Files: '+((x.files||[]).join(', ')||'—')}),
el('div',{text:'Build exit: '+((x.build||{}).exit??'—')+' · Tests: '+((x.tests||{}).result??'—')+' · Attempts: '+(x.attempts??'—')+' · Verifier: '+(v.verdict||'not run')}));
if(x.diff)fx.append(el('div',{},el('a',{href:x.diff,text:'Diff'})));fx.append(evidence(v.evidence));row(b,'Fix',fx)}
if(f.plan){const p=f.plan;row(b,'Plan',val((p.approach||'—')+' · effort '+(p.effort||'—')+' · risk '+(p.risk||'—')))}
d.append(b);return d}
const list=document.getElementById('list');const nodes=F.map(f=>{const n=card(f);list.append(n);return[f,n]});
function apply(){const q=k=>document.getElementById('f-'+k).value;const t=document.getElementById('f-text').value.toLowerCase();let shown=0;
for(const[f,n]of nodes){const ok=['severity','category','status','kind','area'].every(k=>!q(k)||(k==='status'?(f.status||'open'):f[k])===q(k))&&(!t||(f.title+' '+f.where+' '+f.id).toLowerCase().includes(t));n.hidden=!ok;if(ok)shown++}
document.getElementById('f-count').textContent='Showing '+shown+' of '+F.length+' findings'}
document.querySelectorAll('.filters select,#f-text').forEach(e=>e.addEventListener('input',apply));
function resetFilters(){document.querySelectorAll('.filters select').forEach(s=>s.value='');document.getElementById('f-text').value='';apply()}
document.getElementById('f-reset').addEventListener('click',resetFilters);apply();
function reveal(id){const t=document.getElementById(id);if(!t||t.tagName!=='DETAILS')return false;if(t.hidden)resetFilters();t.open=true;
document.documentElement.style.setProperty('--filters-h',(document.querySelector('.filters').offsetHeight+8)+'px');t.scrollIntoView({block:'start'});return true}
const ct=document.getElementById('coverage');ct.append(el('tr',{},...['Area','Journey','Status','Reason','Findings'].map(h=>el('th',{text:h}))));
const crow=D.coverage.map(r=>{const links=el('td');(r.findings||[]).forEach((id,i)=>{if(i)links.append(document.createTextNode(', '));const a=el('a',{href:'#'+id,text:id});a.addEventListener('click',e=>{if(reveal(id)){e.preventDefault();history.pushState(null,'','#'+id)}});links.append(a)});
const tr=el('tr',{},el('td',{text:r.area}),el('td',{text:r.journey+(r.discovered?' (discovered)':'')}),el('td',{class:r.status,text:r.status}),el('td',{},r.reason?document.createTextNode(r.reason):el('span',{class:'missing',text:'—'})),links);ct.append(tr);return[r,tr]});
document.getElementById('c-open').addEventListener('change',e=>{for(const[r,tr]of crow)tr.hidden=e.target.checked&&r.status==='pass'});
const pt=document.getElementById('perf');if(!D.perf.length)document.getElementById('perf-section').hidden=true;else{pt.append(el('tr',{},...['Journey','Step','Metric','Value','Threshold','Build'].map(h=>el('th',{text:h}))));
for(const p of D.perf){const over=p.threshold!=null&&Number(p.value)>Number(p.threshold);pt.append(el('tr',{},el('td',{text:p.journey||'—'}),el('td',{text:p.step||'—'}),el('td',{text:p.metric||'—'}),
el('td',{class:over?'over':'',text:(p.value??'—')+' '+(p.unit||'')}),el('td',{},p.threshold==null?el('span',{class:'missing',text:'none'}):document.createTextNode(String(p.threshold))),el('td',{text:p.build||'—'})))}}
const un=document.getElementById('uncertainty');D.uncertainty.forEach(x=>un.append(el('li',{text:x})));
const de=document.getElementById('details');D.details.forEach(x=>de.append(el('li',{text:x})));
if(location.hash)reveal(decodeURIComponent(location.hash.slice(1)));
})();
</script></body></html>
"""


def build_html(s: dict) -> str:
    data = {key: s[key] for key in ("name", "result", "reasons", "meta", "headline", "cards", "decision",
                                     "findings", "coverage", "perf", "uncertainty", "details")}
    data["enums"] = {"severity": SEVERITIES, "category": CATEGORIES, "status": STATUSES, "kind": KINDS}
    payload = json.dumps(data).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return HTML_TEMPLATE.replace("__DATA__", payload)


def cmd_report(a) -> None:
    run_dir, run = open_run(a.run_dir)
    if not (run_dir / "findings.json").exists():
        fail(EXIT_INPUT, "findings.json is missing", "Run `collect` before `report`.")
    store = load_json(run_dir / "findings.json", "findings.json")
    features = load_json(run_dir / "features.json", "features.json") if (run_dir / "features.json").exists() else None
    errors = report_errors(run_dir, run, store)
    if errors:
        fail(EXIT_FAIL, errors, "Fix each listed field with `update --finding <id>` (or re-run the step that "
             "owns it), then run `report` again. No report was written.")
    s = summarize(run, features, store)
    (run_dir / "report.md").write_text(build_markdown(s), encoding="utf-8")
    (run_dir / "report.html").write_text(build_html(s), encoding="utf-8")
    deep_merge(run, {"result": s["result"], "finished_at": iso()})
    save_json(run_dir / "run.json", run)
    emit({"result": s["result"], "reasons": s["reasons"], "headline": s["headline"],
          "report_md": str(run_dir / "report.md"), "report_html": str(run_dir / "report.html"),
          "decision": s["decision"]})


# ---------------------------------------------------------------- CLI

def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="user_test.py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("init", help="create the run dir and exclude .user-test/ from git")
    s.add_argument("--root", default=".")
    s.add_argument("--url")
    s.add_argument("--scope", default="all", help="'all' or comma-separated feature names")
    s.add_argument("--fix", choices=["on", "off"], default="on")
    s.add_argument("--branch", choices=["local", "local-reuse", "remote"], default="local")
    s.set_defaults(func=cmd_init)

    sub.add_parser("doctor", help="list tools available for driving apps").set_defaults(func=cmd_doctor)

    s = sub.add_parser("detect", help="propose install, start, build and test commands")
    s.add_argument("--root", default=".")
    s.set_defaults(func=cmd_detect)

    app = sub.add_parser("app", help="start, wait for, inspect, or stop app processes").add_subparsers(
        dest="app_command", required=True)
    s = app.add_parser("start")
    s.add_argument("--run-dir", required=True)
    s.add_argument("--cmd", required=True)
    s.add_argument("--cwd")
    s.add_argument("--name", default="app")
    s.add_argument("--port", type=int)
    s.add_argument("--env", action="append", metavar="KEY=VALUE")
    s.set_defaults(func=cmd_app_start)
    s = app.add_parser("wait")
    s.add_argument("--run-dir", required=True)
    s.add_argument("--name", default="app")
    s.add_argument("--url")
    s.add_argument("--timeout", type=int, default=120)
    s.add_argument("--interval", type=float, default=1.0)
    s.set_defaults(func=cmd_app_wait)
    s = app.add_parser("status")
    s.add_argument("--run-dir", required=True)
    s.set_defaults(func=cmd_app_status)
    s = app.add_parser("stop")
    s.add_argument("--run-dir", required=True)
    s.add_argument("--name")
    s.set_defaults(func=cmd_app_stop)

    s = sub.add_parser("check-features", help="validate features.json")
    s.add_argument("--run-dir", required=True)
    s.set_defaults(func=cmd_check_features)

    s = sub.add_parser("collect", help="merge areas/*.json into findings.json and check coverage")
    s.add_argument("--run-dir", required=True)
    s.add_argument("--area", help="check one area file only (implies --check-only)")
    s.add_argument("--check-only", action="store_true", help="validate without writing findings.json")
    s.set_defaults(func=cmd_collect)

    s = sub.add_parser("update", help="patch run.json, patch one finding, or add a run-level finding")
    s.add_argument("--run-dir", required=True)
    s.add_argument("--finding")
    s.add_argument("--add-finding", action="store_true")
    s.add_argument("--note", help="append one line to run.json notes")
    s.add_argument("--json")
    s.add_argument("--json-file")
    s.set_defaults(func=cmd_update)

    s = sub.add_parser("build-check", help="run build and/or test commands and record the result")
    s.add_argument("--run-dir", required=True)
    s.add_argument("--label", required=True)
    s.add_argument("--build")
    s.add_argument("--test")
    s.add_argument("--cwd")
    s.add_argument("--timeout", type=int, default=1200)
    s.set_defaults(func=cmd_build_check)

    checkpoint = sub.add_parser("checkpoint", help="save, restore, or diff the files one fix touches")
    actions = checkpoint.add_subparsers(dest="action", required=True)
    for action in ("save", "restore", "diff"):
        s = actions.add_parser(action)
        s.add_argument("--run-dir", required=True)
        s.add_argument("--fix", required=True, help="the finding id")
        if action == "save":
            s.add_argument("paths", nargs="+", help="each file the fix will edit or create")
        s.set_defaults(func=cmd_checkpoint)

    s = sub.add_parser("report", help="validate findings.json and write report.md and report.html")
    s.add_argument("--run-dir", required=True)
    s.set_defaults(func=cmd_report)
    return p


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        args.func(args)
    except Fail as exc:
        for error in exc.errors:
            print(f"error: {error}", file=sys.stderr)
        print(f"fix: {exc.fix}", file=sys.stderr)
        return exc.code
    return 0


if __name__ == "__main__":
    sys.exit(main())
