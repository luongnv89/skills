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
  status  RUN_DIR                           state of a run (running, done, failed, orphaned, ...)
  stop    RUN_DIR                           stop a running run (harness process group and runner)

`_execute` is internal: `run --background` starts it. It refuses a run folder that already
has a result.

Exit codes: 0 ok, 1 runtime failure (harness exit, probe failure), 2 bad input.
"""
import argparse
import datetime as dt
import json
import os
import re
import secrets
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

try:
    import fcntl
except ImportError:  # Windows: saves are atomic but not locked
    fcntl = None

PROBE_TIMEOUT = 30
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
PERMISSIONS = ("ask", "edits", "full")
ARGV_PROMPT_LIMIT = 100_000  # bytes; larger tasks need a harness that reads a file or stdin
FOREGROUND_TIMEOUT = 540     # fits a 10-minute shell-tool cap; longer tasks run in Background
BACKGROUND_TIMEOUT = 3600
OPENCODE_MESSAGE = "Follow the instructions in the attached file."
# Values that reach a harness argv: never option-like, no whitespace or control characters.
VALUE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@#\[\]+=-]{0,199}$")
# Passed as OPENCODE_CONFIG_CONTENT; honoured with --standalone (tested with 2.2.6). Deny everything,
# then allow by name, so a renamed tool (2.2.6 calls its shell tool `shell`, not `bash`) stays denied.
_OC_READ = {"*": "deny", "read": "allow", "glob": "allow", "grep": "allow", "list": "allow"}
OPENCODE_PERMS = {
    "ask": {"permission": _OC_READ},
    "edits": {"permission": dict(_OC_READ, edit="allow", write="allow")},
}


def die(msg, code=2):
    print(f"agent_profile: error: {msg}", file=sys.stderr)
    sys.exit(code)


def warn(msg):
    print(f"agent_profile: warning: {msg}", file=sys.stderr)


def probe(argv, timeout=PROBE_TIMEOUT, retries=0):
    """Run a read-only probe. Returns (ok, stdout, error)."""
    last = ""
    for _ in range(retries + 1):
        try:
            p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout,
                               stdin=subprocess.DEVNULL)
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
    """Help output, from stdout or stderr, whatever the exit code."""
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=PROBE_TIMEOUT,
                           stdin=subprocess.DEVNULL)
        return (p.stdout or "") + (p.stderr or "")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""


def has_token(text, token):
    """True when `token` appears as a whole flag or value, not inside a longer one."""
    return re.search(rf"(?<![\w-]){re.escape(token)}(?![\w-])", text) is not None


def is_git_dir(path):
    ok, out, _ = probe(["git", "-C", str(path), "rev-parse", "--is-inside-work-tree"], timeout=10)
    return ok and out.strip() == "true"


# ---------------------------------------------------------------- adapters
# models_complete: True = the list is everything the harness accepts; False = the harness
# cannot list (or lists only examples), so a typed id is allowed; None = the list probe
# failed, so nothing may be saved until detect succeeds.

def _claude_models(bin_path):
    text = help_text([bin_path, "--help"])
    block = re.search(r"--model <model>(.*?)(?:\n\s*--[a-z]|\Z)", text, re.S)
    aliases = re.findall(r"'([a-z0-9][a-z0-9.\-]*)'", block.group(1)) if block else []
    models = [{"id": a, "thinking": None, "note": "alias named in claude --help"} for a in aliases]
    return models, "claude --help (example aliases; other aliases and full ids may be typed)", False, ""


def _claude_thinking(bin_path):
    text = help_text([bin_path, "--help"])
    m = re.search(r"--effort <level>.*?\(([^)]*)\)", text, re.S)
    levels = [x.strip() for x in m.group(1).split(",")] if m else []
    return levels, "claude --help (--effort); which levels a model honours is not reported"


def _mcc_profiles():
    default = {"name": "default", "detail": "~/.claude"}
    if not shutil.which("mcc"):
        return [dict(default, detail="~/.claude (mcc not installed)")], ""
    ok, out, err = probe(["mcc", "list", "--json"])
    if not ok:
        return [default], err
    try:
        rows = json.loads(out)
    except json.JSONDecodeError as e:
        return [default], f"mcc list --json: bad JSON ({e})"
    profs = []
    for r in rows:
        detail = " · ".join(x for x in [r.get("dir"), r.get("organization"),
                                        f"model {r['model']}" if r.get("model") else None,
                                        "mcc default" if r.get("is_default") else None] if x)
        profs.append({"name": r.get("name"), "detail": detail, "model": r.get("model")})
    if not any(p["name"] == "default" for p in profs):
        profs.insert(0, default)
    return profs, ""


def _pi_models(bin_path):
    ok, out, err = probe([bin_path, "--list-models"], retries=1)
    if not ok:
        return [], "pi --list-models", None, err
    models = []
    for line in out.splitlines()[1:]:
        cols = line.split()
        if len(cols) < 5:
            continue
        models.append({"id": cols[1], "provider": cols[0], "thinking": cols[4] == "yes",
                       "note": f"context {cols[2]}"})
    return models, "pi --list-models", True, ""


def _pi_thinking(bin_path):
    text = help_text([bin_path, "--help"])
    m = re.search(r"--thinking <level>\s+Set thinking level:\s*([a-z, ]+)", text)
    levels = [x.strip() for x in m.group(1).split(",")] if m else []
    return levels, "pi --help (--thinking); only for models marked thinking; a model's maximum is not reported"


def _opencode_models(bin_path):
    ok, out, err = probe([bin_path, "models"], retries=1)
    if not ok:
        return [], "opencode models", None, err
    ids = [l.strip() for l in out.splitlines() if re.match(r"^[\w.\-]+/[\w.\-:]+$", l.strip())]
    return [{"id": i, "thinking": None, "note": ""} for i in ids], "opencode models", True, ""


def _devin_models(bin_path):
    ok, out, err = probe([bin_path, "models", "list", "--format", "json"])
    if not ok:
        return [], "devin models list", None, err
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return [], "devin models list", None, "not JSON"
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


def _no_models(cli, note="this CLI has no model-list command: type the model id"):
    return lambda b: ([], cli, False, note)


ADAPTERS = {
    "claude": {
        "name": "Claude Code", "bin": "claude", "verified": True,
        "profiles": _mcc_profiles, "default_profile": "default",
        "models": _claude_models, "thinking": _claude_thinking, "per_model_thinking": False,
        "help": [["--help"]], "flags": ["-p", "--model", "--effort", "--permission-mode"],
        "permissions": {"ask": ["--permission-mode", "dontAsk"],
                        "edits": ["--permission-mode", "acceptEdits"],
                        "full": ["--permission-mode", "bypassPermissions"]},
    },
    "pi": {
        "name": "pi", "bin": "pi", "verified": True,
        "profiles": None, "models": _pi_models, "thinking": _pi_thinking, "per_model_thinking": True,
        "help": [["--help"]], "flags": ["-p", "--model", "--provider", "--thinking"],
        "permissions": {"ask": ["--tools", "read,grep,find,ls"], "full": []},
        "permission_note": "pi has no permission prompts: `ask` limits it to read-only tools, "
                           "`full` gives every tool; there is no tested `edits` mode",
    },
    "opencode": {
        "name": "opencode", "bin": "opencode", "verified": True,
        "profiles": None, "models": _opencode_models,
        "thinking": lambda b: ([], "opencode lists no variants: type <model>#<variant> to use one"),
        "per_model_thinking": False, "variants": True,
        "help": [["run", "--help"]], "flags": ["--model", "--auto", "--file", "--standalone"],
        "permissions": {"ask": [], "edits": ["--auto"], "full": ["--auto"]},
        "permission_note": "",
    },
    "codex": {
        "name": "Codex", "bin": "codex", "verified": False,
        "profiles": _codex_profiles, "models": _no_models("codex"),
        "thinking": lambda b: (["minimal", "low", "medium", "high", "xhigh"], "Codex docs (unverified)"),
        "per_model_thinking": False,
        "help": [["exec", "--help"]], "flags": ["--model", "--sandbox", "--config", "--cd"],
        "permissions": {"ask": ["--sandbox", "read-only"], "edits": ["--sandbox", "workspace-write"],
                        "full": ["--sandbox", "danger-full-access"]},
    },
    "droid": {
        "name": "Factory Droid", "bin": "droid", "verified": False,
        "profiles": None,
        "models": _no_models("droid", "type the model id (`droid exec --help` lists the available ones)"),
        "thinking": lambda b: (["off", "low", "medium", "high"], "Droid docs (unverified; model-dependent)"),
        "per_model_thinking": False,
        "help": [["exec", "--help"]], "flags": ["--model", "--reasoning-effort", "--auto", "--file", "--cwd"],
        "permissions": {"ask": [], "edits": ["--auto", "low"], "full": ["--auto", "high"]},
    },
    "devin": {
        "name": "Devin CLI", "bin": "devin", "verified": False,
        "profiles": None, "models": _devin_models,
        "thinking": lambda b: ([], "Devin CLI has no thinking flag"), "per_model_thinking": False,
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
        "thinking": lambda b: ([], "Gemini CLI has no thinking flag"), "per_model_thinking": False,
        "help": [["--help"]], "flags": ["--prompt", "--model", "--approval-mode"],
        "permissions": {"ask": [], "edits": ["--approval-mode", "auto_edit"],
                        "full": ["--approval-mode", "yolo"]},
    },
}


def clean_version(raw, name, bin_name):
    v = re.sub(rf"^{re.escape(bin_name)}(-cli)?\s+", "", raw.strip(), flags=re.I)
    return re.sub(rf"\s*\({re.escape(name)}\)\s*$", "", v).strip()


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
    raw = out.strip().splitlines()[0] if ok and out.strip() else f"unknown ({err})"
    row["version"] = clean_version(raw, a["name"], a["bin"])
    if a["profiles"]:
        profs, perr = a["profiles"]()
        row["harness_profiles"], row["harness_profiles_error"] = profs, perr
    else:
        row["harness_profiles"] = []
    models, src, complete, merr = a["models"](path)
    if hid == "claude":  # models set in mcc profiles are valid choices too
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
    return {"detected_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "harnesses": [detect_one(h) for h in (hids or list(ADAPTERS))]}


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
        n, c = len(h["models"]), h["models_complete"]
        how = {True: "complete list", False: "partial: other ids may be typed",
               None: "LIST FAILED: fix the harness, then run detect again"}[c]
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


def entry_problem(name, p):
    """Why a stored entry cannot be used, or None."""
    if not isinstance(name, str) or not NAME_RE.match(name):
        return "invalid name"
    if not isinstance(p, dict):
        return "not an object"
    if p.get("harness") not in ADAPTERS:
        return f"unknown harness {p.get('harness')!r}"
    if not isinstance(p.get("model"), str) or not p["model"]:
        return "no model"
    if p.get("permissions") not in PERMISSIONS:
        return f"bad permissions {p.get('permissions')!r}"
    for k in ("model", "harness_profile", "provider", "thinking"):
        if k in p and not (isinstance(p[k], str) and VALUE_RE.match(p[k])):
            return f"bad {k} {p[k]!r}"
    return None


def load(path, strict=False):
    if not path.is_file():
        return {"version": 1, "profiles": {}}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        die(f"{path} is not valid JSON ({e}); fix or move it, then retry", 1)
    if not isinstance(data, dict) or not isinstance(data.get("profiles", {}), dict):
        die(f"{path} does not hold a profiles object; fix or move it, then retry", 1)
    data.setdefault("profiles", {})
    if not strict:
        for name in list(data["profiles"]):
            why = entry_problem(name, data["profiles"][name])
            if why:
                warn(f"skipping profile {name!r} in {path}: {why}")
                del data["profiles"][name]
    return data


class Locked:
    """Exclusive lock for a read-modify-write of one profile file (lock kept in the cache)."""

    def __init__(self, path):
        import hashlib  # keep lock files out of repos: one per profile file, in the cache
        digest = hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:16]
        self.lock = runs_root().parent / "locks" / f"{digest}.lock"

    def __enter__(self):
        self.lock.parent.mkdir(parents=True, exist_ok=True)
        self.fh = open(self.lock, "w")
        if fcntl:
            fcntl.flock(self.fh, fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        if fcntl:
            fcntl.flock(self.fh, fcntl.LOCK_UN)
        self.fh.close()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write(json.dumps(data, indent=2, sort_keys=True) + "\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def merged(project):
    out = {}
    for scope, path in (("global", global_file()), ("project", project_file(project))):
        for name, p in load(path)["profiles"].items():
            out[name] = dict(p, name=name, scope=scope, overrides_global=name in out, _file=str(path))
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


def find_model(d, model_id, provider=None):
    """(model_row, variant) when model_id, or its base before '#', is detected."""
    candidates = [(model_id, None)]
    if "#" in model_id and ADAPTERS[d["id"]].get("variants"):
        base, variant = model_id.split("#", 1)
        candidates.append((base, variant))
    for mid, variant in candidates:
        for m in d.get("models", []):
            if m["id"] == mid and (not provider or m.get("provider") == provider):
                return m, variant
    return None, None


# ---------------------------------------------------------------- save

def cmd_save(a):
    if not NAME_RE.match(a.name):
        die(f"profile name '{a.name}' is invalid: use 1-40 lowercase letters, digits or hyphens, starting with a letter or digit")
    if a.harness not in ADAPTERS:
        die(f"unknown harness '{a.harness}'. Known: {', '.join(ADAPTERS)}")
    for flag, v in (("--model", a.model), ("--harness-profile", a.harness_profile),
                    ("--provider", a.provider), ("--thinking", a.thinking)):
        if v is not None and not VALUE_RE.match(v):
            die(f"{flag} {v!r} is not a valid value: it must start with a letter or digit and hold no spaces")
    d = detect_one(a.harness)
    if d["status"] != "installed":
        die(f"harness '{a.harness}' ({d['bin']}) is not installed on this machine; install it, then run detect again")
    hp = a.harness_profile or ADAPTERS[a.harness].get("default_profile")
    if hp:
        names = [p["name"] for p in d.get("harness_profiles", [])]
        if hp not in names:
            die(f"harness profile '{hp}' not found for {a.harness}. Detected: {', '.join(names) or 'none'}")
    if d["models_complete"] is None:
        die(f"{a.harness} could not list its models ({d['models_error']}); fix the harness, then run detect again", 1)
    model, variant = find_model(d, a.model, a.provider)
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
    with Locked(path):
        data = load(path, strict=True)
        if a.name in data["profiles"] and not a.replace:
            die(f"a {a.scope} profile named '{a.name}' exists; pass --replace after the user confirms, or pick another name")
        now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        old = data["profiles"].get(a.name)
        created = old.get("created", now) if isinstance(old, dict) else now
        entry = {k: v for k, v in {
            "harness": a.harness, "harness_profile": hp, "model": a.model, "provider": provider,
            "variant": variant, "thinking": a.thinking, "permissions": a.permissions,
            "harness_version": d.get("version"), "created": created, "updated": now,
        }.items() if v not in (None, "")}
        entry["typed_model"] = typed
        data["profiles"][a.name] = entry
        write(path, data)
    p = dict(entry, name=a.name, scope=a.scope)
    print(json.dumps({"saved": str(path), "brief": brief(p)}, indent=2))


def cmd_delete(a):
    path = global_file() if a.scope == "global" else project_file(a.project)
    with Locked(path):
        data = load(path, strict=True)
        if a.name not in data["profiles"]:
            die(f"no {a.scope} profile named '{a.name}' in {path}")
        del data["profiles"][a.name]
        write(path, data)
    print(json.dumps({"deleted": a.name, "file": str(path)}))


# ---------------------------------------------------------------- command / run

def recheck(p):
    """Compare a saved profile with what is installed now. Returns notes; dies on a hard mismatch."""
    d = detect_one(p["harness"])
    if d["status"] != "installed":
        die(f"harness '{p['harness']}' ({d['bin']}) is not installed; run detect and pick or create another profile")
    notes = []
    hp = p.get("harness_profile")
    if hp and hp not in [x["name"] for x in d.get("harness_profiles", [])]:
        die(f"harness profile '{hp}' is not detected for {p['harness']}; edit the profile")
    t = p.get("thinking")
    if t and t not in d.get("thinking_levels", []):
        die(f"thinking '{t}' is not a level {p['harness']} reports ({', '.join(d.get('thinking_levels', [])) or 'none'}); edit the profile")
    if p["permissions"] not in d["permissions"]:
        die(f"{p['harness']} has no '{p['permissions']}' permission mode; edit the profile")
    model, _ = find_model(d, p["model"], p.get("provider"))
    if model is None:
        if d["models_complete"]:
            die(f"model '{p['model']}' is no longer in {p['harness']}'s list ({d['models_source']}); edit the profile")
        notes.append(f"model '{p['model']}' is typed, not detected: the harness may reject it")
    if p.get("harness_version") and d.get("version") and p["harness_version"] != d["version"]:
        notes.append(f"{d['name']} changed from {p['harness_version']} to {d['version']} since the profile was saved")
    if p.get("scope") == "project":
        notes.append(f"project profile from {p.get('_file', '.agent-profiles.json')}: check it is one you trust")
    return notes


def argv_prompt(prompt, hid):
    if len(prompt.encode()) > ARGV_PROMPT_LIMIT:
        die(f"the task is over {ARGV_PROMPT_LIMIT} bytes and {hid} takes it as an argument; "
            "shorten it or use claude, pi, opencode, codex, droid or devin, which read a file")
    # a leading dash would be parsed as an option
    return ("Task:\n" + prompt) if prompt.lstrip().startswith("-") else prompt


def build(p, prompt_file, cwd):
    """Return (argv, stdin_path, env_unset, env_set, notes). The prompt never passes through a shell."""
    hid = p["harness"]
    a = ADAPTERS[hid]
    notes = recheck(p)
    path = shutil.which(a["bin"])
    perm = a["permissions"][p["permissions"]]
    t, m = p.get("thinking"), p["model"]
    stdin, env_unset, env_set = None, [], {}
    if hid == "claude":
        argv = [path, "-p", "--model", m] + (["--effort", t] if t else []) + perm
        stdin = prompt_file
        hp = p.get("harness_profile") or "default"
        if shutil.which("mcc"):
            argv = [shutil.which("mcc"), "exec", hp, "--"] + argv
        elif hp == "default":
            env_unset = ["CLAUDE_CONFIG_DIR"]  # run as ~/.claude, not as the caller's profile
        else:
            die(f"profile uses mcc profile '{hp}' but mcc is not installed")
    elif hid == "pi":
        argv = [path, "-p"] + (["--provider", p["provider"]] if p.get("provider") else []) + ["--model", m] \
            + (["--thinking", t] if t else []) + perm + ["--", "@" + prompt_file]
    elif hid == "opencode":
        # --standalone: a private server in this run's process tree, so permission config is read
        # fresh and stop/timeout reach the tools (the shared background service would escape both)
        argv = [path, "run", "--standalone", "--model", m] + perm + ["--file", prompt_file, "--", OPENCODE_MESSAGE]
        if p["permissions"] in OPENCODE_PERMS:
            env_set["OPENCODE_CONFIG_CONTENT"] = json.dumps(OPENCODE_PERMS[p["permissions"]], separators=(",", ":"))
            if any((Path(cwd) / f).exists() for f in ("opencode.json", "opencode.jsonc", ".opencode")):
                notes.append("the working directory has its own opencode config, which may change what "
                             f"`{p['permissions']}` allows: check its permission rules")
    elif hid == "codex":
        argv = [path, "exec", "--cd", cwd, "--model", m] \
            + (["--profile", p["harness_profile"]] if p.get("harness_profile") else []) \
            + (["--config", f"model_reasoning_effort={t}"] if t else []) + perm \
            + ([] if is_git_dir(cwd) else ["--skip-git-repo-check"]) + ["-"]
        stdin = prompt_file
    elif hid == "droid":
        argv = [path, "exec", "--cwd", cwd, "--model", m] + (["--reasoning-effort", t] if t else []) \
            + perm + ["--file", prompt_file]
    elif hid == "devin":
        argv = [path, "--print", "--prompt-file", prompt_file, "--model", m,
                "--respect-workspace-trust", "false"] + perm
    elif hid == "grok":
        argv = [path, "--model", m] + perm + ["-p", argv_prompt(Path(prompt_file).read_text(), hid)]
    elif hid == "gemini":
        argv = [path, "--model", m] + perm + ["--prompt=" + argv_prompt(Path(prompt_file).read_text(), hid)]
    if not a["verified"]:
        text = "".join(help_text([path] + h) for h in a["help"])
        needed = set(a["flags"]) | set(perm)
        for extra in ("--profile", "--skip-git-repo-check"):
            if extra in argv:
                needed.add(extra)
        missing = sorted(f for f in needed if not has_token(text, f))
        if missing:
            die(f"untested adapter: `{a['bin']} --help` does not mention {', '.join(missing)}; "
                f"the CLI changed or differs from its docs. Do not run; report this to the user", 1)
        notes.append(f"{a['name']} adapter is untested: flags checked against --help only")
    if a.get("permission_note"):
        notes.append(a["permission_note"])
    return argv, stdin, env_unset, env_set, notes


def display(argv, stdin, prompt_file, env_unset, env_set=None):
    shown = [f"<task from {prompt_file}>" if (len(x) > 200 or "\n" in x) else x for x in argv]
    prefix = "".join(f"env -u {v} " for v in env_unset) + "".join(
        f"{k}={shlex.quote(v)} " for k, v in (env_set or {}).items())
    return prefix + shlex.join(shown) + (f" < {shlex.quote(stdin)}" if stdin else "")


def cmd_command(a):
    p = get_profile(a.name, a.project)
    if not Path(a.prompt_file).is_file():
        die(f"prompt file {a.prompt_file} does not exist")
    cwd = os.path.abspath(a.cwd)
    prompt_file = os.path.abspath(a.prompt_file)
    argv, stdin, env_unset, env_set, notes = build(p, prompt_file, cwd)
    print(json.dumps({"profile": brief(p), "cwd": cwd, "argv": argv, "stdin": stdin, "env_unset": env_unset,
                      "env_set": env_set, "display": display(argv, stdin, prompt_file, env_unset, env_set),
                      "notes": notes,
                      "needs_full_confirmation": p["permissions"] == "full"}, indent=2))


def runs_root():
    base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return base / "agent-profile" / "runs"


def pid_alive(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    try:  # a zombie counts as gone
        with open(f"/proc/{pid}/stat") as fh:
            return fh.read().rsplit(")", 1)[-1].split()[0] != "Z"
    except OSError:
        return True


def read_pid(run_dir, name):
    try:
        return int((Path(run_dir) / name).read_text().strip())
    except (OSError, ValueError):
        return None


def write_result(run_dir, result):
    tmp = Path(run_dir) / "result.json.tmp"
    tmp.write_text(json.dumps(result, indent=2) + "\n")
    os.replace(tmp, Path(run_dir) / "result.json")


def descendants(pid):
    """Every live descendant of pid, found through /proc parent links (Linux; else empty)."""
    children = {}
    for d in Path("/proc").glob("[0-9]*"):
        try:
            ppid = int((d / "stat").read_text().rsplit(")", 1)[-1].split()[1])
        except (OSError, ValueError, IndexError):
            continue
        children.setdefault(ppid, []).append(int(d.name))
    out, todo = [], [pid]
    while todo:
        for c in children.get(todo.pop(), []):
            out.append(c)
            todo.append(c)
    return out


def kill_group(pid):
    """SIGTERM the harness's process group and every descendant (some start their own
    session), then SIGKILL whatever is left after 10 s."""
    targets = [pid] + descendants(pid)
    for sig, wait in ((signal.SIGTERM, 10), (signal.SIGKILL, 2)):
        targets += [x for x in descendants(pid) if x not in targets]
        try:
            os.killpg(pid, sig)
        except OSError:
            pass
        for t in targets:
            try:
                os.kill(t, sig)
            except OSError:
                pass
        end = time.time() + wait
        while time.time() < end and any(pid_alive(t) for t in targets):
            time.sleep(0.2)
        if not any(pid_alive(t) for t in targets):
            return


def execute(run_dir, timeout):
    run_dir = Path(run_dir)
    if (run_dir / "result.json").exists():
        die(f"{run_dir} already has a result; start a new run with `run`")
    spec = json.loads((run_dir / "command.json").read_text())
    (run_dir / "runner.pid").write_text(str(os.getpid()))
    start = time.time()
    state = {"proc": None, "status": None}

    def on_signal(signum, _frame):
        state["status"] = "interrupted"
        if state["proc"] is not None:
            kill_group(state["proc"].pid)

    for s in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(s, on_signal)
    code = None
    with open(run_dir / "output.log", "ab") as log:
        stdin = open(spec["stdin"], "rb") if spec["stdin"] else subprocess.DEVNULL
        try:
            # Some harnesses (opencode) take their working directory from $PWD, so set it too.
            env = dict(os.environ, PWD=spec["cwd"])
            for v in spec.get("env_unset", []):
                env.pop(v, None)
            env.update(spec.get("env_set", {}))
            proc = subprocess.Popen(spec["argv"], cwd=spec["cwd"], stdin=stdin, stdout=log,
                                    stderr=subprocess.STDOUT, start_new_session=True, env=env)
            state["proc"] = proc
            (run_dir / "child.pid").write_text(str(proc.pid))
            try:
                code = proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                state["status"] = "timeout"
                kill_group(proc.pid)
                code = proc.wait()
        except OSError as e:
            state["status"] = "failed-to-start"
            log.write(f"agent_profile: could not start {spec['argv'][0]}: {e}\n".encode())
        finally:
            if stdin is not subprocess.DEVNULL:
                stdin.close()
    status = state["status"] or ("done" if code == 0 else "failed")
    if not (run_dir / "result.json").exists():  # `stop` may have written it already
        write_result(run_dir, {"status": status, "exit_code": code,
                               "duration_s": round(time.time() - start, 1),
                               "finished": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")})
    return json.loads((run_dir / "result.json").read_text())


def new_run_dir(name):
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    root = runs_root()
    root.mkdir(parents=True, exist_ok=True)
    for _ in range(20):
        d = root / f"{stamp}-{name}-{secrets.token_hex(3)}"
        try:
            d.mkdir()
            return d
        except FileExistsError:
            continue
    die("could not create a unique run folder", 1)


def cmd_run(a):
    p = get_profile(a.name, a.project)
    cwd = os.path.abspath(a.cwd)
    if not Path(cwd).is_dir():
        die(f"--cwd {cwd} is not a directory")
    if not Path(a.prompt_file).is_file():
        die(f"prompt file {a.prompt_file} does not exist")
    if p["permissions"] == "full" and not a.confirm_full:
        die(f"profile '{a.name}' runs with full permissions; ask the user to confirm this run, then pass --confirm-full")
    timeout = a.timeout or (BACKGROUND_TIMEOUT if a.background else FOREGROUND_TIMEOUT)
    run_dir = new_run_dir(p["name"])
    try:
        shutil.copy(a.prompt_file, run_dir / "prompt.md")
        argv, stdin, env_unset, env_set, notes = build(p, str(run_dir / "prompt.md"), cwd)
    except BaseException:  # a refused build leaves no half-made run folder
        shutil.rmtree(run_dir, ignore_errors=True)
        raise
    (run_dir / "command.json").write_text(json.dumps(
        {"profile": p["name"], "brief": brief(p), "cwd": cwd, "argv": argv, "stdin": stdin,
         "env_unset": env_unset, "env_set": env_set, "notes": notes, "timeout_s": timeout}, indent=2) + "\n")
    if a.background:
        runner = subprocess.Popen([sys.executable, os.path.abspath(__file__), "_execute", str(run_dir),
                                   "--timeout", str(timeout)], stdin=subprocess.DEVNULL,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        print(json.dumps({"run_dir": str(run_dir), "state": "running", "pid": runner.pid, "timeout_s": timeout,
                          "log": str(run_dir / "output.log"), "notes": notes}, indent=2))
        return
    result = execute(run_dir, timeout)
    tail = (run_dir / "output.log").read_text(errors="replace").splitlines()[-60:]
    print("\n".join(tail))
    print(json.dumps(dict(result, run_dir=str(run_dir), log=str(run_dir / "output.log"), notes=notes), indent=2))
    sys.exit(0 if result["status"] == "done" else 1)


def run_state(run_dir):
    run_dir = Path(run_dir)
    if not (run_dir / "command.json").is_file():
        die(f"{run_dir} is not a run folder (no command.json)")
    runner, child = read_pid(run_dir, "runner.pid"), read_pid(run_dir, "child.pid")
    if (run_dir / "result.json").is_file():
        out = json.loads((run_dir / "result.json").read_text())
        out["state"] = out.pop("status")
        if pid_alive(child):
            out["warning"] = f"the harness (pid {child}) is still alive"
    elif pid_alive(runner):
        out = {"state": "running"}
    elif pid_alive(child):
        out = {"state": "orphaned (the runner died; the harness is still running: use `stop`)"}
    else:
        out = {"state": "lost (runner and harness exited without a result)"}
    out.update(runner_pid=runner, child_pid=child)
    return out


def cmd_status(a):
    out = run_state(a.run_dir)
    log = Path(a.run_dir) / "output.log"
    out["log"] = str(log)
    out["log_tail"] = log.read_text(errors="replace").splitlines()[-20:] if log.is_file() else []
    print(json.dumps(out, indent=2))


def cmd_stop(a):
    run_dir = Path(a.run_dir)
    st = run_state(run_dir)
    if not (st["state"] == "running" or st["state"].startswith("orphaned")):
        die(f"run is not running (state: {st['state']})")
    child, runner = st["child_pid"], st["runner_pid"]
    if not (run_dir / "result.json").exists():
        write_result(run_dir, {"status": "stopped", "exit_code": None, "duration_s": None,
                               "finished": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")})
    if child and pid_alive(child):
        kill_group(child)
    if runner and pid_alive(runner):
        try:
            os.kill(runner, signal.SIGTERM)
        except OSError:
            pass
    time.sleep(0.5)
    print(json.dumps(run_state(run_dir), indent=2))


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
            s.add_argument("--background", action="store_true")
            s.add_argument("--timeout", type=int,
                           help=f"seconds; default {FOREGROUND_TIMEOUT} foreground, {BACKGROUND_TIMEOUT} background")
            s.add_argument("--confirm-full", action="store_true")
    s = sub.add_parser("status"); s.add_argument("run_dir")
    s = sub.add_parser("stop"); s.add_argument("run_dir")
    s = sub.add_parser("_execute"); s.add_argument("run_dir"); s.add_argument("--timeout", type=int, default=BACKGROUND_TIMEOUT)
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
        cmd_delete(a)
    elif a.cmd == "command":
        cmd_command(a)
    elif a.cmd == "run":
        cmd_run(a)
    elif a.cmd == "status":
        cmd_status(a)
    elif a.cmd == "stop":
        cmd_stop(a)
    elif a.cmd == "_execute":
        execute(a.run_dir, a.timeout)


if __name__ == "__main__":
    main()
