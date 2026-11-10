#!/usr/bin/env python3
"""agent_profile.py: detect agent harnesses, store named agent profiles, run a task with one.

Standard library only. Subcommands:
  detect  [--harness ID] [--json]           what this machine offers: harnesses, harness profiles,
                                            models, thinking levels, permission modes
  list    [--project DIR] [--json]          saved profiles (project overrides global), one brief each
  show    NAME [--project DIR]              one profile as JSON
  save    --name N --harness H --model M [--harness-profile P] [--provider P] [--thinking T]
          [--permissions ask|edits|full] [--scope global|project] [--project DIR] [--replace]
          [--typed-model]                   validate against detect, then write
  delete  NAME --scope global|project [--project DIR]
  command NAME --prompt-file F [--cwd D] [--project DIR]   the exact argv, without running it
  run     NAME --prompt-file F --cwd D [--background] [--timeout SEC] [--confirm-full] [--project DIR]
  status  RUN_DIR                           state of a background run

Exit codes: 0 ok, 1 runtime failure (harness exit, probe failure), 2 bad input.
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

PROBE_TIMEOUT = 30
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
PERMISSIONS = ("ask", "edits", "full")


def die(msg, code=2):
    print(f"agent_profile: error: {msg}", file=sys.stderr)
    sys.exit(code)


def probe(argv, timeout=PROBE_TIMEOUT, retries=0, env=None):
    """Run a read-only probe. Returns (ok, stdout, error)."""
    last = ""
    for _ in range(retries + 1):
        try:
            p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout,
                               stdin=subprocess.DEVNULL, env=env)
        except FileNotFoundError:
            return False, "", f"{argv[0]} not found on PATH"
        except subprocess.TimeoutExpired:
            last = f"`{' '.join(argv)}` timed out after {timeout}s"
            continue
        if p.returncode == 0:
            return True, p.stdout, ""
        last = f"`{' '.join(argv)}` exited {p.returncode}: {(p.stderr or p.stdout).strip()[:200]}"
    return False, "", last


def help_text(argv):
    ok, out, err = probe(argv)
    if ok:
        return out
    # some CLIs print help on stderr or exit non-zero for --help
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=PROBE_TIMEOUT,
                           stdin=subprocess.DEVNULL)
        return (p.stdout or "") + (p.stderr or "")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""


# ---------------------------------------------------------------- adapters
# Each adapter: how to find its version, profiles, models and thinking levels, and how to
# build a headless run. "verified" means a real run on this skill's test machine worked;
# unverified adapters come from the CLI's docs and are checked against `--help` first.

def _claude_models(bin_path):
    text = help_text([bin_path, "--help"])
    block = re.search(r"--model <model>(.*?)(?:\n\s*--[a-z]|\Z)", text, re.S)
    aliases = re.findall(r"'([a-z0-9][a-z0-9.\-]*)'", block.group(1)) if block else []
    models = [{"id": a, "thinking": None, "note": "alias for the latest model"} for a in aliases]
    return models, "claude --help (aliases)", False, ""


def _claude_thinking(bin_path):
    text = help_text([bin_path, "--help"])
    m = re.search(r"--effort <level>.*?\(([^)]*)\)", text, re.S)
    levels = [x.strip() for x in m.group(1).split(",")] if m else []
    return levels, "claude --help (--effort)"


def _mcc_profiles():
    if not shutil.which("mcc"):
        return [{"name": "default", "detail": "~/.claude (mcc not installed)"}], ""
    ok, out, err = probe(["mcc", "list", "--json"])
    if not ok:
        return [{"name": "default", "detail": "~/.claude"}], err
    try:
        rows = json.loads(out)
    except json.JSONDecodeError as e:
        return [{"name": "default", "detail": "~/.claude"}], f"mcc list --json: bad JSON ({e})"
    profs = []
    for r in rows:
        detail = " · ".join(x for x in [r.get("dir"), r.get("organization"),
                                        f"model {r['model']}" if r.get("model") else None,
                                        "default" if r.get("is_default") else None] if x)
        profs.append({"name": r.get("name"), "detail": detail, "model": r.get("model")})
    return profs, ""


def _pi_models(bin_path):
    ok, out, err = probe([bin_path, "--list-models"], retries=1)
    if not ok:
        return [], "pi --list-models", False, err
    models = []
    for line in out.splitlines()[1:]:
        cols = line.split()
        if len(cols) < 5:
            continue
        provider, mid, thinking = cols[0], cols[1], cols[4]
        models.append({"id": mid, "provider": provider,
                       "thinking": thinking == "yes", "note": f"context {cols[2]}"})
    return models, "pi --list-models", True, ""


def _pi_thinking(bin_path):
    text = help_text([bin_path, "--help"])
    m = re.search(r"--thinking <level>\s+Set thinking level:\s*([a-z, ]+)", text)
    return ([x.strip() for x in m.group(1).split(",")] if m else []), "pi --help (--thinking)"


def _opencode_models(bin_path):
    ok, out, err = probe([bin_path, "models"], retries=1)
    if not ok:
        return [], "opencode models", False, err
    ids = [l.strip() for l in out.splitlines() if re.match(r"^[\w.\-]+/[\w.\-:]+$", l.strip())]
    return [{"id": i, "thinking": None, "note": ""} for i in ids], "opencode models", True, ""


def _devin_models(bin_path):
    ok, out, err = probe([bin_path, "models", "list", "--format", "json"])
    if not ok:
        return [], "devin models list", False, err
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return [], "devin models list", False, "not JSON"
    rows = data if isinstance(data, list) else data.get("models", [])
    ids = [r.get("id") or r.get("name") for r in rows if isinstance(r, dict)]
    return [{"id": i, "thinking": None, "note": ""} for i in ids if i], "devin models list", True, ""


def _codex_profiles():
    cfg = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "config.toml"
    if not cfg.is_file():
        return [], ""
    try:
        import tomllib
        data = tomllib.loads(cfg.read_text())
    except Exception as e:  # noqa: BLE001 - report any parse failure
        return [], f"{cfg}: {e}"
    return [{"name": n, "detail": " · ".join(f"{k} {v}" for k, v in p.items()
                                              if k in ("model", "model_reasoning_effort"))}
            for n, p in (data.get("profiles") or {}).items()], ""


def _no_models(source):
    return lambda b: ([], source, False, "this CLI has no model-list command: type the model id")


ADAPTERS = {
    "claude": {
        "name": "Claude Code", "bin": "claude", "verified": True,
        "profiles": _mcc_profiles, "models": _claude_models, "thinking": _claude_thinking,
        "per_model_thinking": False,
        "help": [["--help"]], "flags": ["-p", "--model", "--effort", "--permission-mode"],
        "permissions": {"ask": [], "edits": ["--permission-mode", "acceptEdits"],
                        "full": ["--permission-mode", "bypassPermissions"]},
    },
    "pi": {
        "name": "pi", "bin": "pi", "verified": True,
        "profiles": None, "models": _pi_models, "thinking": _pi_thinking,
        "per_model_thinking": True,
        "help": [["--help"]], "flags": ["-p", "--model", "--provider", "--thinking"],
        "permissions": {"full": []},
        "permission_note": "pi has no permission prompts: every run has full tool access",
    },
    "opencode": {
        "name": "opencode", "bin": "opencode", "verified": True,
        "profiles": None, "models": _opencode_models,
        "thinking": lambda b: ([], "opencode lists no variants: append #variant to the model id to use one"),
        "per_model_thinking": False,
        "help": [["run", "--help"]], "flags": ["--model", "--auto"],
        "permissions": {"ask": [], "full": ["--auto"]},
    },
    "codex": {
        "name": "Codex", "bin": "codex", "verified": False,
        "profiles": lambda: _codex_profiles(), "models": _no_models("codex"),
        "thinking": lambda b: (["minimal", "low", "medium", "high", "xhigh"], "Codex docs (unverified)"),
        "per_model_thinking": False,
        "help": [["exec", "--help"]], "flags": ["--model", "--sandbox", "--profile", "--config"],
        "permissions": {"ask": ["--sandbox", "read-only"], "edits": ["--sandbox", "workspace-write"],
                        "full": ["--sandbox", "danger-full-access"]},
    },
    "droid": {
        "name": "Factory Droid", "bin": "droid", "verified": False,
        "profiles": None, "models": _no_models("droid"),
        "thinking": lambda b: (["off", "low", "medium", "high"], "Droid docs (unverified; model-dependent)"),
        "per_model_thinking": False,
        "help": [["exec", "--help"]], "flags": ["--model", "--reasoning-effort", "--auto", "--file", "--cwd"],
        "permissions": {"ask": [], "edits": ["--auto", "low"], "full": ["--auto", "high"]},
    },
    "devin": {
        "name": "Devin CLI", "bin": "devin", "verified": False,
        "profiles": None, "models": _devin_models,
        "thinking": lambda b: ([], "Devin CLI has no thinking flag"),
        "per_model_thinking": False,
        "help": [["--help"]], "flags": ["--print", "--prompt-file", "--model", "--permission-mode",
                                         "--respect-workspace-trust"],
        "permissions": {"ask": ["--permission-mode", "normal"],
                        "edits": ["--permission-mode", "accept-edits"],
                        "full": ["--permission-mode", "dangerous"]},
    },
    "grok": {
        "name": "Grok Build", "bin": "grok", "verified": False,
        "profiles": None, "models": _no_models("grok"),
        "thinking": lambda b: ([], "set default_reasoning_effort in ~/.grok/config.toml instead"),
        "per_model_thinking": False,
        "help": [["--help"]], "flags": ["-p", "--model"],
        "permissions": {"ask": [], "full": ["--yolo"]},
    },
    "gemini": {
        "name": "Gemini CLI", "bin": "gemini", "verified": False,
        "profiles": None, "models": _no_models("gemini"),
        "thinking": lambda b: ([], "Gemini CLI has no thinking flag"),
        "per_model_thinking": False,
        "help": [["--help"]], "flags": ["--prompt", "--model", "--approval-mode"],
        "permissions": {"ask": [], "edits": ["--approval-mode", "auto_edit"],
                        "full": ["--approval-mode", "yolo"]},
    },
}


def detect_one(hid):
    a = ADAPTERS[hid]
    path = shutil.which(a["bin"])
    row = {"id": hid, "name": a["name"], "bin": a["bin"], "path": path,
           "status": "installed" if path else "missing",
           "adapter": "verified" if a["verified"] else "untested",
           "permissions": sorted(a["permissions"], key=PERMISSIONS.index),
           "permission_note": a.get("permission_note", "")}
    if not path:
        return row
    ok, out, err = probe([path, "--version"])
    ver = out.strip().splitlines()[0] if ok and out.strip() else f"unknown ({err})"
    row["version"] = re.sub(rf"^{re.escape(a['bin'])}\s+", "", ver, flags=re.I)
    if a["profiles"]:
        profs, perr = a["profiles"]()
        row["harness_profiles"], row["harness_profiles_error"] = profs, perr
    else:
        row["harness_profiles"] = []
    models, src, complete, merr = a["models"](path)
    if hid == "claude":  # models configured in mcc profiles are valid choices too
        seen = {m["id"] for m in models}
        for p in row.get("harness_profiles", []):
            if p.get("model") and p["model"] not in seen:
                models.append({"id": p["model"], "thinking": None, "note": f"set in mcc profile {p['name']}"})
                seen.add(p["model"])
    row.update(models=models, models_source=src, models_complete=complete, models_error=merr)
    levels, tsrc = a["thinking"](path)
    row.update(thinking_levels=levels, thinking_source=tsrc, per_model_thinking=a["per_model_thinking"])
    return row


def detect(hids=None):
    hids = hids or list(ADAPTERS)
    return {"detected_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "harnesses": [detect_one(h) for h in hids]}


def print_detect(d):
    for h in d["harnesses"]:
        if h["status"] == "missing":
            print(f"○ {h['id']:<9} {h['name']}: not installed ({h['adapter']} adapter)")
            continue
        print(f"● {h['id']:<9} {h['name']} {h['version']} ({h['adapter']} adapter)")
        for p in h.get("harness_profiles", []):
            print(f"    profile  {p['name']}: {p.get('detail', '')}")
        if h.get("harness_profiles_error"):
            print(f"    profiles: {h['harness_profiles_error']}")
        n = len(h["models"])
        how = "complete list" if h["models_complete"] else "partial: other ids may be typed"
        print(f"    models   {n} from {h['models_source']} ({how})" + (f"; {h['models_error']}" if h["models_error"] else ""))
        for m in h["models"][:40]:
            t = "" if m.get("thinking") is None else (" · thinking" if m["thinking"] else " · no thinking")
            prov = f" [{m['provider']}]" if m.get("provider") else ""
            print(f"      - {m['id']}{prov}{t}" + (f" ({m['note']})" if m.get("note") else ""))
        if n > 40:
            print(f"      … {n - 40} more (use --json)")
        print(f"    thinking {', '.join(h['thinking_levels']) or 'none'} ({h['thinking_source']})")
        print(f"    permissions {', '.join(h['permissions'])}" + (f": {h['permission_note']}" if h["permission_note"] else ""))


# ---------------------------------------------------------------- store

def global_file():
    base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "agent-profile" / "profiles.json"


def project_root(project):
    start = Path(project or os.getcwd()).resolve()
    ok, out, _ = probe(["git", "-C", str(start), "rev-parse", "--show-toplevel"], timeout=10)
    return Path(out.strip()) if ok and out.strip() else start


def project_file(project):
    return project_root(project) / ".agent-profiles.json"


def load(path):
    if not path.is_file():
        return {"version": 1, "profiles": {}}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        die(f"{path} is not valid JSON ({e}); fix or move it, then retry", 1)
    data.setdefault("profiles", {})
    return data


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, path)


def merged(project):
    out = {}
    for scope, path in (("global", global_file()), ("project", project_file(project))):
        for name, p in load(path)["profiles"].items():
            out[name] = dict(p, name=name, scope=scope, overrides_global=name in out)
    return out


def brief(p):
    h = p["harness"] + (f"/{p['harness_profile']}" if p.get("harness_profile") else "")
    model = p["model"] + (" (typed)" if p.get("typed_model") else "")
    extra = " · overrides global" if p.get("overrides_global") else ""
    return f"{p['name']} — {h} · {model} · thinking {p.get('thinking') or 'default'} · permissions {p['permissions']} · {p['scope']}{extra}"


def get_profile(name, project):
    profs = merged(project)
    if name not in profs:
        die(f"no profile named '{name}'. Saved: {', '.join(sorted(profs)) or 'none'}. Create one with `save`.")
    return profs[name]


# ---------------------------------------------------------------- save

def cmd_save(a):
    if not NAME_RE.match(a.name):
        die(f"profile name '{a.name}' is invalid: use 1-40 lowercase letters, digits or hyphens, starting with a letter or digit")
    if a.harness not in ADAPTERS:
        die(f"unknown harness '{a.harness}'. Known: {', '.join(ADAPTERS)}")
    d = detect_one(a.harness)
    if d["status"] != "installed":
        die(f"harness '{a.harness}' ({d['bin']}) is not installed on this machine; install it, then run detect again")
    hp = a.harness_profile
    if hp:
        names = [p["name"] for p in d.get("harness_profiles", [])]
        if hp not in names:
            die(f"harness profile '{hp}' not found for {a.harness}. Detected: {', '.join(names) or 'none'}")
    model = next((m for m in d["models"] if m["id"] == a.model and (not a.provider or m.get("provider") == a.provider)), None)
    typed = model is None
    if typed:
        if d["models_complete"]:
            die(f"model '{a.model}' is not in {a.harness}'s list ({d['models_source']}). Pick one from `detect --harness {a.harness}`")
        if not a.typed_model:
            die(f"model '{a.model}' is not in the detected list; pass --typed-model to confirm the user typed this id")
    provider = a.provider or (model or {}).get("provider")
    if a.thinking:
        levels = d["thinking_levels"]
        if not levels:
            die(f"{a.harness} has no thinking levels ({d['thinking_source']}); omit --thinking")
        if a.thinking not in levels:
            die(f"thinking '{a.thinking}' is not valid for {a.harness}: {', '.join(levels)}")
        if d["per_model_thinking"] and model is not None and model.get("thinking") is False:
            die(f"model '{a.model}' does not support thinking ({d['models_source']}); omit --thinking")
    if a.permissions not in d["permissions"]:
        die(f"{a.harness} supports permissions {', '.join(d['permissions'])}, not '{a.permissions}'")
    path = global_file() if a.scope == "global" else project_file(a.project)
    data = load(path)
    if a.name in data["profiles"] and not a.replace:
        die(f"a {a.scope} profile named '{a.name}' exists; pass --replace after the user confirms, or pick another name")
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    old = data["profiles"].get(a.name, {})
    data["profiles"][a.name] = {k: v for k, v in {
        "harness": a.harness, "harness_profile": hp, "model": a.model, "provider": provider,
        "typed_model": typed, "thinking": a.thinking, "permissions": a.permissions,
        "harness_version": d.get("version"), "created": old.get("created", now), "updated": now,
    }.items() if v not in (None, "")}
    data["profiles"][a.name]["typed_model"] = typed
    write(path, data)
    p = dict(data["profiles"][a.name], name=a.name, scope=a.scope)
    print(json.dumps({"saved": str(path), "brief": brief(p)}, indent=2))


# ---------------------------------------------------------------- command / run

def build(p, prompt_file, cwd):
    """Return (argv, stdin_path, notes). The prompt never passes through a shell."""
    hid = p["harness"]
    a = ADAPTERS[hid]
    path = shutil.which(a["bin"])
    if not path:
        die(f"harness '{hid}' ({a['bin']}) is not installed; run detect")
    prompt = Path(prompt_file).read_text()
    perm = a["permissions"].get(p["permissions"])
    if perm is None:
        die(f"{hid} has no '{p['permissions']}' permission mode")
    t, m = p.get("thinking"), p["model"]
    stdin = None
    if hid == "claude":
        argv = [path, "-p", "--model", m] + (["--effort", t] if t else []) + perm
        stdin = prompt_file
        hp = p.get("harness_profile")
        if hp and hp != "default":
            if not shutil.which("mcc"):
                die(f"profile uses mcc profile '{hp}' but mcc is not installed")
            argv = [shutil.which("mcc"), "exec", hp, "--"] + argv
    elif hid == "pi":
        argv = [path, "-p"] + (["--provider", p["provider"]] if p.get("provider") else []) + ["--model", m] \
            + (["--thinking", t] if t else []) + [prompt]
    elif hid == "opencode":
        argv = [path, "run", "--model", m] + perm + [prompt]
    elif hid == "codex":
        argv = [path, "exec", "--cd", cwd, "--model", m] + (["--profile", p["harness_profile"]] if p.get("harness_profile") else []) \
            + (["--config", f"model_reasoning_effort={t}"] if t else []) + perm + ["-"]
        stdin = prompt_file
    elif hid == "droid":
        argv = [path, "exec", "--cwd", cwd, "--model", m] + (["--reasoning-effort", t] if t else []) + perm + ["--file", prompt_file]
    elif hid == "devin":
        argv = [path, "--print", "--prompt-file", prompt_file, "--model", m, "--respect-workspace-trust", "false"] + perm
    elif hid == "grok":
        argv = [path, "-p", prompt, "--model", m] + perm
    elif hid == "gemini":
        argv = [path, "--model", m] + perm + ["--prompt", prompt]
    notes = []
    if not a["verified"]:
        missing = []
        text = "".join(help_text([path] + h) for h in a["help"])
        for f in a["flags"]:
            if f not in text:
                missing.append(f)
        if missing:
            die(f"untested adapter: `{a['bin']} --help` does not mention {', '.join(missing)}; "
                f"the CLI changed or differs from its docs. Do not run; report this to the user", 1)
        notes.append(f"{a['name']} adapter is untested: flags checked against --help only")
    if a.get("permission_note"):
        notes.append(a["permission_note"])
    return argv, stdin, notes


def display(argv, stdin, prompt_file):
    shown = []
    for x in argv:
        if len(x) > 80 and "\n" in x or len(x) > 200:
            shown.append(f"<prompt from {prompt_file}>")
        else:
            shown.append(x if re.match(r"^[\w@%+=:,./#-]+$", x) else json.dumps(x))
    return " ".join(shown) + (f" < {stdin}" if stdin else "")


def cmd_command(a):
    p = get_profile(a.name, a.project)
    if not Path(a.prompt_file).is_file():
        die(f"prompt file {a.prompt_file} does not exist")
    argv, stdin, notes = build(p, a.prompt_file, os.path.abspath(a.cwd))
    print(json.dumps({"profile": brief(p), "cwd": os.path.abspath(a.cwd), "argv": argv, "stdin": stdin,
                      "display": display(argv, stdin, a.prompt_file), "notes": notes,
                      "needs_full_confirmation": p["permissions"] == "full"}, indent=2))


def runs_root():
    base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return base / "agent-profile" / "runs"


def execute(run_dir, timeout):
    run_dir = Path(run_dir)
    spec = json.loads((run_dir / "command.json").read_text())
    start = time.time()
    status, code = "done", None
    with open(run_dir / "output.log", "wb") as log:
        stdin = open(spec["stdin"], "rb") if spec["stdin"] else subprocess.DEVNULL
        try:
            # Some harnesses (opencode) take their working directory from $PWD, not the
            # process cwd, so set both.
            env = dict(os.environ, PWD=spec["cwd"])
            proc = subprocess.Popen(spec["argv"], cwd=spec["cwd"], stdin=stdin, stdout=log,
                                    stderr=subprocess.STDOUT, start_new_session=True, env=env)
            (run_dir / "child.pid").write_text(str(proc.pid))
            try:
                code = proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                status, code = "timeout", proc.wait()
        except OSError as e:
            status, code = "failed-to-start", None
            log.write(f"agent_profile: could not start {spec['argv'][0]}: {e}\n".encode())
        finally:
            if stdin is not subprocess.DEVNULL:
                stdin.close()
    if status == "done" and code != 0:
        status = "failed"
    result = {"status": status, "exit_code": code, "duration_s": round(time.time() - start, 1),
              "finished": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    (run_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def cmd_run(a):
    p = get_profile(a.name, a.project)
    cwd = os.path.abspath(a.cwd)
    if not Path(cwd).is_dir():
        die(f"--cwd {cwd} is not a directory")
    if not Path(a.prompt_file).is_file():
        die(f"prompt file {a.prompt_file} does not exist")
    if p["permissions"] == "full" and not a.confirm_full:
        die(f"profile '{a.name}' runs with full permissions; ask the user to confirm this run, then pass --confirm-full")
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = runs_root() / f"{stamp}-{a.name}"
    run_dir.mkdir(parents=True, exist_ok=False)
    shutil.copy(a.prompt_file, run_dir / "prompt.md")
    prompt_copy = str(run_dir / "prompt.md")
    argv, stdin, notes = build(p, prompt_copy, cwd)
    (run_dir / "command.json").write_text(json.dumps(
        {"profile": a.name, "brief": brief(p), "cwd": cwd, "argv": argv, "stdin": stdin, "notes": notes}, indent=2) + "\n")
    if a.background:
        runner = subprocess.Popen([sys.executable, os.path.abspath(__file__), "_execute", str(run_dir),
                                   "--timeout", str(a.timeout)], stdin=subprocess.DEVNULL,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        (run_dir / "runner.pid").write_text(str(runner.pid))
        print(json.dumps({"run_dir": str(run_dir), "state": "running", "pid": runner.pid,
                          "log": str(run_dir / "output.log"), "notes": notes}, indent=2))
        return
    result = execute(run_dir, a.timeout)
    tail = (run_dir / "output.log").read_text(errors="replace").splitlines()[-60:]
    print("\n".join(tail))
    print(json.dumps(dict(result, run_dir=str(run_dir), log=str(run_dir / "output.log"), notes=notes), indent=2))
    sys.exit(0 if result["status"] == "done" else 1)


def cmd_status(a):
    run_dir = Path(a.run_dir)
    if not (run_dir / "command.json").is_file():
        die(f"{run_dir} is not a run folder (no command.json)")
    res = run_dir / "result.json"
    if res.is_file():
        out = json.loads(res.read_text())
        out["state"] = out.pop("status")
    else:
        pid = int((run_dir / "runner.pid").read_text()) if (run_dir / "runner.pid").is_file() else None
        alive = False
        if pid:
            try:
                os.kill(pid, 0)
                alive = True
            except OSError:
                alive = False
        out = {"state": "running" if alive else "lost (runner exited without a result)", "pid": pid}
    log = run_dir / "output.log"
    out["log"] = str(log)
    out["log_tail"] = log.read_text(errors="replace").splitlines()[-20:] if log.is_file() else []
    print(json.dumps(out, indent=2))


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("detect"); s.add_argument("--harness", action="append", choices=list(ADAPTERS)); s.add_argument("--json", action="store_true")
    s = sub.add_parser("list"); s.add_argument("--project"); s.add_argument("--json", action="store_true")
    s = sub.add_parser("show"); s.add_argument("name"); s.add_argument("--project")
    s = sub.add_parser("save")
    for f in ("--name", "--harness", "--model"):
        s.add_argument(f, required=True)
    for f in ("--harness-profile", "--provider", "--thinking", "--project"):
        s.add_argument(f)
    s.add_argument("--permissions", choices=PERMISSIONS, default="edits")
    s.add_argument("--scope", choices=("global", "project"), default="global")
    s.add_argument("--replace", action="store_true"); s.add_argument("--typed-model", action="store_true")
    s = sub.add_parser("delete"); s.add_argument("name"); s.add_argument("--scope", choices=("global", "project"), required=True); s.add_argument("--project")
    for c in ("command", "run"):
        s = sub.add_parser(c); s.add_argument("name"); s.add_argument("--prompt-file", required=True)
        s.add_argument("--cwd", default=os.getcwd()); s.add_argument("--project")
        if c == "run":
            s.add_argument("--background", action="store_true"); s.add_argument("--timeout", type=int, default=3600)
            s.add_argument("--confirm-full", action="store_true")
    s = sub.add_parser("status"); s.add_argument("run_dir")
    s = sub.add_parser("_execute"); s.add_argument("run_dir"); s.add_argument("--timeout", type=int, default=3600)
    a = ap.parse_args()

    if a.cmd == "detect":
        d = detect(a.harness)
        print(json.dumps(d, indent=2)) if a.json else print_detect(d)
    elif a.cmd == "list":
        profs = merged(a.project)
        if a.json:
            print(json.dumps({"global": str(global_file()), "project": str(project_file(a.project)),
                              "profiles": list(profs.values())}, indent=2))
        else:
            print("\n".join(f"{i}. {brief(p)}" for i, p in enumerate(sorted(profs.values(), key=lambda x: x["name"]), 1))
                  or "No saved profiles.")
    elif a.cmd == "show":
        print(json.dumps(get_profile(a.name, a.project), indent=2))
    elif a.cmd == "save":
        cmd_save(a)
    elif a.cmd == "delete":
        path = global_file() if a.scope == "global" else project_file(a.project)
        data = load(path)
        if a.name not in data["profiles"]:
            die(f"no {a.scope} profile named '{a.name}' in {path}")
        del data["profiles"][a.name]
        write(path, data)
        print(json.dumps({"deleted": a.name, "file": str(path)}))
    elif a.cmd == "command":
        cmd_command(a)
    elif a.cmd == "run":
        cmd_run(a)
    elif a.cmd == "status":
        cmd_status(a)
    elif a.cmd == "_execute":
        execute(a.run_dir, a.timeout)


if __name__ == "__main__":
    main()
