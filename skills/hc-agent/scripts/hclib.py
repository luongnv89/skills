#!/usr/bin/env python3
"""Shared helpers for the hc-agent scripts.

Every helper shells out to the installed `hc` (herdr-core) and `herdr-app`
CLIs. Nothing here calls `herdr`: inside the Herdr desktop app that CLI talks
to a separate TUI server and acts on someone else's panes.

hc prints JSON when piped and reports errors as {"error": {kind, message,
hint}} on stderr with exit codes 3 not_found, 7 needs_target, 9 blocked,
10 status_mismatch and 11 finished. herdr-app prints {"error": "..."} and
exits 1. Agent state is the OSC 7501 status a program reports itself
(`hc get` .status.state); a terminal without one is unverifiable, never idle.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time

HC, APP = "hc", "herdr-app"

SHELLS = {"zsh", "bash", "sh", "dash", "ksh", "mksh", "fish", "tcsh", "csh", "nu", "elvish", "xonsh", "login"}
INTERPRETERS = {"node", "bun", "deno", "python", "python3", "env"}
# `hc get` .status.app -> agent kind (the CLI binary name)
APP_KIND = {"claude-code": "claude", "codex": "codex", "pi": "pi", "gemini": "gemini"}
STATES = {"idle", "working", "done", "blocked", "error"}
READY = {"idle", "done", "error"}
ATTENTION = ["blocked", "error", "done", "working", "idle", "unverified", "no-agent", "exited", "unknown"]
NAME_RE = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
# hc addresses seen live: t7, t14, t1b, t2x, t999, machine/t2. A worker name never looks like one.
ADDRESS_RE = re.compile(r"^(?:[A-Za-z0-9._-]+/)?t[0-9][0-9a-z]*$")
CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")
LABEL = "hc-agent"  # label namespace: hc-agent.role, .name, .space, .tab

# agent.py exit codes; references/delivery-and-waiting.md has the table.
EXIT = {"ok": 0, "settled": 0, "error": 1, "blocked": 3, "unverifiable": 4, "no_agent": 5,
        "working": 6, "stalled": 7, "timeout": 8, "exited": 9}
HC_EXIT = {3: "not_found", 7: "needs_target", 9: "blocked", 10: "status_mismatch", 11: "finished"}


class HcError(Exception):
    """A failed hc/herdr-app call or an unusable target. Scripts report it and exit 1."""

    def __init__(self, message: str, kind: str = "", code: int = 1):
        super().__init__(message)
        self.kind, self.code = kind, code


def _shown(tool: str, args: list[str]) -> str:
    return " ".join([tool, *[a for a in args if not a.startswith(("[", "{"))][:4]])


def _error_detail(proc: subprocess.CompletedProcess) -> tuple[str, str]:
    text = (proc.stderr or "").strip() or (proc.stdout or "").strip()
    try:
        err = json.loads(text).get("error")
    except (ValueError, AttributeError):
        err = None
    if isinstance(err, dict):
        hint = f" ({err['hint']})" if err.get("hint") else ""
        return str(err.get("kind") or ""), f"{err.get('message') or 'error'}{hint}"
    if isinstance(err, str):
        return "", err
    lines = text.splitlines()
    return "", lines[0] if lines else "no output"


def run(tool: str, args: list[str], *, timeout: float = 30.0, check: bool = True) -> subprocess.CompletedProcess:
    if shutil.which(tool) is None:
        raise HcError(f"{tool} is not on PATH. Run this inside a terminal of the Herdr desktop app, "
                      "where hc and herdr-app are installed (normally ~/.local/bin).")
    try:
        proc = subprocess.run([tool, *args], capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise HcError(f"'{_shown(tool, args)}' timed out after {timeout:.0f}s. Inspect the state "
                      "before retrying: the command may have succeeded.") from None
    if check and proc.returncode != 0:
        kind, detail = _error_detail(proc)
        kind = kind or HC_EXIT.get(proc.returncode, "")
        raise HcError(f"'{_shown(tool, args)}' failed (exit {proc.returncode}{', ' + kind if kind else ''}): "
                      f"{detail}", kind=kind, code=proc.returncode)
    return proc


def run_json(tool: str, args: list[str], **kw) -> dict:
    proc = run(tool, args, **kw)
    try:
        data = json.loads(proc.stdout or "null")
    except ValueError:
        raise HcError(f"'{_shown(tool, args)}' printed output that is not JSON; check that the "
                      f"installed {tool} supports this command.") from None
    return data if isinstance(data, dict) else {"value": data}


# --- hc ---------------------------------------------------------------------

def get(addr: str) -> dict:
    return run_json(HC, ["get", addr, "--json"])


def ls_labeled(*labels: str) -> list[dict]:
    args = ["ls", "--json"]
    for label in labels:
        args += ["--label", label]
    return run_json(HC, args).get("terminals") or []


def label(addr: str, pairs: dict[str, str]) -> None:
    run(HC, ["label", addr, *[f"{k}={v}" for k, v in pairs.items()], "--json"])


def read_screen(addr: str, lines: int) -> str:
    return run(HC, ["read", addr, "--lines", str(lines)]).stdout


# --- herdr-app ----------------------------------------------------------------

def app_ls() -> dict:
    return run_json(APP, ["ls"])


def app_status() -> dict:
    return run_json(APP, ["status"])


def app_do(command: str, **args: str) -> dict:
    words = ["do", command]
    for key, value in args.items():
        words += [f"--{key}", value]
    return run_json(APP, words)


# --- terminals ----------------------------------------------------------------

def binary_name(token: str | None) -> str:
    base = os.path.basename(token or "").lstrip("-")
    for ext in (".js", ".mjs", ".cjs", ".ts"):
        if base.endswith(ext):
            return base[: -len(ext)]
    return base


def foreground_argv(rec: dict) -> list[str]:
    argv = ((rec or {}).get("foreground") or {}).get("argv")
    return [a for a in argv if isinstance(a, str)] if isinstance(argv, list) else []


def process_kind(argv: list[str]) -> str:
    """The agent CLI from argv0, or from the script an interpreter runs."""
    if not argv:
        return ""
    base = binary_name(argv[0])
    if base in INTERPRETERS and len(argv) > 1:
        return binary_name(argv[1])
    return base


def classify(rec: dict) -> tuple[str, str]:
    """(status, kind) for one `hc get` record.

    status is an OSC 7501 state, or exited / no-agent / unverified. A record
    reported while a shell is in the foreground is stale (hc misses a nested
    shell returning), so it fails closed as unverified.
    """
    if rec.get("state") == "finished":
        return "exited", ""
    argv = foreground_argv(rec)
    base = process_kind(argv)
    st = rec.get("status") if isinstance(rec.get("status"), dict) else None
    kind = APP_KIND.get((st or {}).get("app") or "", base if base not in SHELLS else "")
    if not st or not st.get("state"):
        return ("no-agent" if not argv or base in SHELLS else "unverified"), kind
    if base in SHELLS:
        return "unverified", kind
    state = st["state"]
    return (state if state in STATES else "unverified"), kind


def labels(rec: dict) -> dict:
    lab = rec.get("labels")
    return lab if isinstance(lab, dict) else {}


def describe(addr: str, rec: dict, pane: str = "") -> dict:
    status, kind = classify(rec)
    lab, st = labels(rec), rec.get("status") if isinstance(rec.get("status"), dict) else {}
    return {"name": lab.get(f"{LABEL}.name") or "", "terminal": addr, "pane": pane, "kind": kind,
            "status": status, "msg": (st or {}).get("msg"), "turn": rec.get("turn"),
            "status_ms": rec.get("status_ms"), "role_label": lab.get(f"{LABEL}.role") or "",
            "cwd": (rec.get("foreground") or {}).get("cwd") or rec.get("cwd")}


class Root:
    """The orchestrator's own terminal, its pane, and the app space/tab it sits in."""

    def __init__(self, addr: str, rec: dict, space: str, tab: str, pane: str, tab_terminals: list[dict]):
        self.addr, self.rec, self.space, self.tab, self.pane = addr, rec, space, tab, pane
        self.tab_terminals = tab_terminals

    def panes(self) -> dict[str, str]:
        return {t.get("terminal"): t.get("pane") for t in self.tab_terminals if t.get("terminal")}


def find_tab(app: dict, space: str, tab: str) -> list[dict] | None:
    for sp in app.get("spaces") or []:
        if sp.get("id") != space:
            continue
        for tb in sp.get("tabs") or []:
            if tb.get("id") == tab:
                return [t for t in tb.get("terminals") or [] if isinstance(t, dict)]
    return None


def resolve_root(addr: str | None = None) -> Root:
    """Confirm this is an app terminal shown in the window, and find its pane and tab."""
    if os.environ.get("HERDR_ENV") == "1":
        raise HcError("HERDR_ENV=1: this is a Herdr TUI pane, not the desktop app. Use the herdr-agent "
                      "skill instead.", kind="herdr_tui")
    addr = addr or os.environ.get("HC_TERMINAL_ID", "")
    if not addr:
        raise HcError("HC_TERMINAL_ID is unset, so this is not a terminal of the Herdr desktop app. Run "
                      "the orchestrator inside the app; never act on whatever the window shows.")
    rec = get(addr)
    if rec.get("state") == "finished":
        raise HcError(f"terminal {addr} is finished according to 'hc get'.")
    lab = labels(rec)
    space, tab = lab.get("herdr.space"), lab.get("herdr.tab")
    if not space or not tab:
        raise HcError(f"terminal {addr} has no herdr.space/herdr.tab labels, so the app window does not "
                      "show it (a background hc terminal). Run the orchestrator in a visible app pane.")
    terminals = find_tab(app_ls(), space, tab)
    if terminals is None:
        raise HcError(f"'herdr-app ls' shows no tab {tab} in space {space}. Is the Herdr window open?")
    pane = next((t.get("pane") for t in terminals if t.get("terminal") == addr), "")
    if not pane:
        raise HcError(f"'herdr-app ls' lists no pane for terminal {addr} in its own tab.")
    return Root(addr, rec, space, tab, pane, terminals)


def sanitize(text: str) -> str:
    """Drop ESC and other controls: an embedded ESC[201~ would end a paste early."""
    return CONTROL.sub("", text.replace("\r\n", "\n").replace("\r", "\n"))


def poll_ready(addr: str, timeout: float, interval: float = 0.5) -> tuple[str, dict]:
    """Wait for a booting agent: ready, blocked, error, exited or timeout.

    Ready needs an idle or done status. hc's own `wait` would wait for exit on a
    terminal with no status yet, so this polls `hc get` within a fixed budget.
    """
    end = time.monotonic() + timeout
    rec: dict = {}
    while True:
        rec = get(addr)
        status, _ = classify(rec)
        if status in ("idle", "done"):
            return "ready", rec
        if status in ("blocked", "error", "exited"):
            return status, rec
        if time.monotonic() >= end:
            return "timeout", rec
        time.sleep(interval)
