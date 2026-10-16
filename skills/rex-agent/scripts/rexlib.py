#!/usr/bin/env python3
"""Shared helpers for the rex-agent scripts.

Every helper shells out to the installed `rex` CLI, never to the server
socket, and always passes --autostart=false so a check can never start a new,
empty server. Agent state comes from OSC 7501 program status records, which
the agent CLI reports itself. references/delivery-and-waiting.md has the
per-kind table this module encodes.
"""

from __future__ import annotations

import ctypes
import ctypes.util
import json
import os
import queue
import re
import shutil
import struct
import subprocess
import sys
import threading
import time

REX = "rex"
GLOBAL = ["--autostart=false"]

SHELLS = {"zsh", "bash", "sh", "dash", "ksh", "mksh", "fish", "tcsh", "csh", "nu", "elvish", "xonsh", "login"}
INTERPRETERS = {"node", "bun", "deno", "python", "python3", "env"}
# program status `app` -> agent kind (the CLI binary name)
APP_KIND = {"claude-code": "claude", "codex": "codex", "pi": "pi", "gemini": "gemini"}
# Only an explicit record proves readiness: no record can also mean a dialog
# that reports nothing (Codex's update prompt does exactly that).
READY = {"idle", "done", "error"}
ATTENTION = ["blocked", "error", "done", "working", "idle", "unverified", "unknown", "no-agent", "exited"]
NAME_RE = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
PASTE_ON = re.compile(r"\x1b\[\?(?:[0-9;]*;)?2004(?:;[0-9;]*)?h")
CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")

# agent.py exit codes; references/delivery-and-waiting.md has the table.
EXIT = {"ok": 0, "settled": 0, "error": 1, "blocked": 3, "unverifiable": 4, "no_agent": 5,
        "working": 6, "stalled": 7, "timeout": 8, "exited": 9}


class RexError(Exception):
    """A failed rex call or an unusable target. Scripts report it and exit 1."""


def _shown(args: list[str]) -> str:
    words = [a for a in args if not a.startswith("{")][:4]
    return "rex " + " ".join(words)


def run(args: list[str], *, stdin: str | None = None, timeout: float = 30.0,
        check: bool = True) -> subprocess.CompletedProcess:
    if shutil.which(REX) is None:
        raise RexError("rex is not on PATH. Run this inside a Rex terminal, where rex is on "
                       "PATH automatically, or add the Rex CLI directory to PATH.")
    try:
        proc = subprocess.run([REX, *GLOBAL, *args], input=stdin, capture_output=True,
                              text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise RexError(f"'{_shown(args)}' timed out after {timeout:.0f}s. Inspect the state "
                       "before retrying: the command may have succeeded.") from None
    if check and proc.returncode != 0:
        lines = (proc.stderr or proc.stdout).strip().splitlines()
        detail = lines[0] if lines else "no output"
        hint = " The Rex server is unreachable; start the Rex app." if proc.returncode == 4 else ""
        raise RexError(f"'{_shown(args)}' failed (exit {proc.returncode}): {detail}.{hint}")
    return proc


def run_json(args: list[str], **kw) -> dict:
    proc = run(args, **kw)
    try:
        data = json.loads(proc.stdout or "null")
    except ValueError:
        raise RexError(f"'{_shown(args)}' printed output that is not JSON; check that the "
                       "installed rex supports --json for this command.") from None
    return data if isinstance(data, dict) else {"value": data}


def whoami() -> dict:
    return run_json(["whoami", "--json"])


def session_view(session: str) -> dict:
    return run_json(["session", "inspect", session, "--json"])


def list_blocks(session: str) -> list[dict]:
    return run_json(["block", "ls", "-s", session, "--json"]).get("blocks") or []


def block_call(session: str, block: str, method: str, args: dict | None = None) -> dict:
    cmd = ["block", "call", "-s", session, "-b", block, method]
    if args is not None:
        cmd.append(json.dumps(args))
    return run_json(cmd)


def api_call(session: str, method: str, args: dict) -> dict:
    return run_json(["api", "call", "-s", session, method, json.dumps(args)])


def require_capabilities(session: str, block: str) -> None:
    """Fail closed when the server lacks what the skill relies on."""
    methods = (run_json(["block", "inspect", "-s", session, block, "--json"]).get("api") or {}).get("methods") or {}
    if "program_status" not in methods:
        raise RexError(f"block {block} has no program_status method, so agent state cannot be "
                       "read. Update Rex; this skill needs OSC 7501 program status support.")
    run(["api", "describe", "session.resize_pane", "--json"])


def root_record(records: list[dict]) -> dict | None:
    for rec in records or []:
        if not rec.get("id"):
            return rec
    return None


def _base(path: str | None) -> str:
    base = os.path.basename(path or "").lstrip("-")
    for ext in (".js", ".mjs", ".cjs", ".ts"):
        if base.endswith(ext):
            return base[: -len(ext)]
    return base


def process_kind(proc: dict) -> str:
    """The agent CLI in the foreground, from argv0 or the script it runs, never `name`."""
    fg = (proc or {}).get("foreground") or {}
    for key in ("argv0", "script", "invoked_path"):
        base = _base(fg.get(key))
        if base and base not in INTERPRETERS:
            return base
    return _base(fg.get("name"))


_LOCAL: list[bool] = []


def is_local_server() -> bool:
    """True when the server is on this machine, so its pids are local pids."""
    if not _LOCAL:
        try:
            _LOCAL.append(str(whoami().get("endpoint") or "").startswith("unix:"))
        except RexError:
            _LOCAL.append(False)
    return _LOCAL[0]


def _procargs(pid: int) -> bytes | None:
    libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
    argmax, size = ctypes.c_int(), ctypes.c_size_t(ctypes.sizeof(ctypes.c_int))
    if libc.sysctl((ctypes.c_int * 2)(1, 8), 2, ctypes.byref(argmax), ctypes.byref(size), None, 0):
        return None
    buf, size = ctypes.create_string_buffer(argmax.value), ctypes.c_size_t(argmax.value)
    if libc.sysctl((ctypes.c_int * 3)(1, 49, pid), 3, buf, ctypes.byref(size), None, 0):
        return None
    return buf.raw[: size.value]


def read_process(pid: int) -> tuple[list[str] | None, dict | None]:
    """Exact argv and environment of a local process: /proc on Linux, KERN_PROCARGS2 on macOS.

    Either part is None when unreadable (no such process, another user's, or no support).
    """
    if os.path.isdir(f"/proc/{pid}"):
        def parts(name):
            try:
                with open(f"/proc/{pid}/{name}", "rb") as fh:
                    return [p.decode("utf-8", "replace") for p in fh.read().split(b"\0") if p]
            except OSError:
                return None
        argv, env = parts("cmdline"), parts("environ")
        return argv or None, (dict(e.split("=", 1) for e in env if "=" in e) if env is not None else None)
    if sys.platform != "darwin":
        return None, None
    raw = _procargs(pid)
    if not raw or len(raw) < 4:
        return None, None
    argc = struct.unpack("i", raw[:4])[0]
    rest = raw[4:]
    rest = rest[rest.find(b"\0"):].lstrip(b"\0")  # skip the exec path and its padding
    items = rest.split(b"\0")
    argv = [a.decode("utf-8", "replace") for a in items[:argc]]
    env: dict[str, str] = {}
    for item in items[argc:]:
        if not item:
            break
        key, _, value = item.decode("utf-8", "replace").partition("=")
        env[key] = value
    return (argv if len(argv) == argc and all(argv) else None), env


def process_env(pid: int) -> dict | None:
    return read_process(pid)[1]


def inspect_agent(session: str, block: dict | str) -> dict:
    """Classify one block. Status is a record state, or unverified/no-agent/exited."""
    info = block if isinstance(block, dict) else {"block_id": block}
    block_id = info["block_id"]
    proc = block_call(session, block_id, "process")
    rec = root_record(block_call(session, block_id, "program_status").get("records") or [])
    fg = proc.get("foreground") or {}
    kind = process_kind(proc)
    owner = (rec or {}).get("owner") or {}
    fresh = bool(rec) and (not owner or owner.get("pid") == fg.get("pid"))
    if proc.get("child") is None:
        status = "exited"
    elif not fg or kind in SHELLS:
        status = "no-agent"
    elif fresh:
        status = rec.get("state") or "unverified"
        kind = APP_KIND.get(rec.get("app") or "", kind)
    else:
        status = "unverified"
    env = process_env(fg.get("pid")) if fg.get("pid") and is_local_server() else None
    return {
        "name": info.get("label") or "",
        "block_id": block_id,
        "window_id": info.get("window_id") or "",
        "kind": kind,
        "status": status,
        "worker_role": (env or {}).get("REX_AGENT_ROLE") or None,
        "env_readable": env is not None,
        "app": (rec or {}).get("app") if fresh else None,
        "blocked_kind": (rec or {}).get("kind") if fresh else None,
        "msg": (rec or {}).get("msg") if fresh else None,
        "updated_at": (rec or {}).get("updated_at") if fresh else None,
        "pid": fg.get("pid"),
        "last_exit": proc.get("last_exit"),
    }


def resolve(session: str, target: str, blocks: list[dict] | None = None) -> dict:
    """Exact label or full block ID. Never a bare suffix: a hex name can match an ID tail."""
    blocks = list_blocks(session) if blocks is None else blocks
    if target.startswith("block:"):
        matches = [b for b in blocks if b.get("block_id") == target]
    else:
        matches = [b for b in blocks if (b.get("label") or "").lower() == target.lower()]
    if not matches:
        raise RexError(f"no block labeled '{target}' in session {session}. List the fleet with "
                       "'agent.py fleet', or pass a full block:… ID.")
    if len(matches) > 1:
        ids = ", ".join(b["block_id"] for b in matches)
        raise RexError(f"'{target}' labels {len(matches)} blocks ({ids}). Rename one with "
                       "'rex block rename', or pass a full block:… ID.")
    return matches[0]


def sanitize(text: str) -> str:
    """Drop ESC and other controls: an embedded ESC[201~ would end the paste early."""
    return CONTROL.sub("", text.replace("\r\n", "\n").replace("\r", "\n"))


def bracketed_paste(session: str, block: str) -> bool:
    dump = block_call(session, block, "format", {"format": "vt", "extra_modes": True})
    return bool(PASTE_ON.search(dump.get("content") or ""))


def capture(session: str, block: str) -> str:
    return run(["capture", "-s", session, "-b", block, "--unwrap"]).stdout


def send_prompt(session: str, block: str, text: str, tag: str = "") -> bool:
    """Type text (and a trailing turn tag), then Enter. Returns whether it was a bracketed paste."""
    clean = sanitize(text).strip("\n")
    if not clean.strip():
        raise RexError("the prompt is empty after removing control characters; pass the task text.")
    paste = bracketed_paste(session, block)
    if tag:
        clean += ("\n\n" if paste else " ") + tag
    if "\n" in clean and not paste:
        raise RexError(f"block {block} has bracketed paste off, so each newline would submit "
                       "early. Write the text to a file and send one line naming the path.")
    run(["send", "-s", session, "-b", block], stdin=f"\x1b[200~{clean}\x1b[201~" if paste else clean)
    time.sleep(0.15)
    run(["send-key", "-s", session, "-b", block, "enter"])
    return paste


class Watch:
    """Follow block events through `rex events`; callers also poll, so a late stream is safe.

    A reader thread moves each line into a queue as it arrives, so events that
    arrive in one write are never left sitting in a pipe buffer.
    """

    def __init__(self, session: str):
        self.events: list[dict] = []
        self.lines: queue.Queue = queue.Queue()
        self.proc = self.reader = None
        try:
            self.proc = subprocess.Popen([REX, *GLOBAL, "events", "-s", session, "--json"],
                                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            self.reader = threading.Thread(target=self._read, args=(self.proc.stdout,), daemon=True)
            self.reader.start()
        except OSError:
            self.proc = None
        time.sleep(0.3)  # let the stream attach before the caller writes anything

    def _read(self, stream) -> None:
        for line in stream:
            self.lines.put(line)

    def pump(self, timeout: float) -> None:
        end = time.monotonic() + timeout
        while True:
            try:
                line = self.lines.get(timeout=max(0.0, end - time.monotonic()))
            except queue.Empty:
                return
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            inner = ((ev.get("payload") or {}).get("event") or {})
            if inner.get("type") == "block_event":
                self.events.append(inner.get("payload") or {})
                del self.events[:-2000]

    def take(self, block: str) -> list[dict]:
        mine = [e for e in self.events if e.get("block_id") == block]
        self.events = [e for e in self.events if e.get("block_id") != block]
        return mine

    def close(self) -> None:
        if self.proc is not None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()
            if self.reader is not None:
                self.reader.join(timeout=2)
            self.proc.stdout.close()
            self.proc = None


def poll_root(session: str, block: str) -> tuple[dict | None, dict]:
    proc = block_call(session, block, "process")
    rec = root_record(block_call(session, block, "program_status").get("records") or [])
    return rec, proc


def wait_turn(session: str, block: str, watch: Watch, *, baseline: dict | None,
              activity_timeout: float, timeout: float, active: bool = False,
              until: str = "settled") -> tuple[str, dict | None, bool]:
    """Wait for one turn to end. Returns (outcome, last record, working observed).

    A turn needs activity: a record newer than the baseline. `working` marks it
    active; then the first newer `idle`, `done` or `error` ends it. A newer `done`
    or `error` ends it even if `working` was missed between polls, because only a
    finished turn writes them; a newer `idle` without `working` does not. A blocked
    record ends it at once (a human is needed), and a removed record ends it as
    unverifiable: the agent stopped reporting, which can also mean a dialog is up.
    """
    base_stamp = (baseline or {}).get("updated_at")
    last_stamp, present = base_stamp, baseline is not None
    start = time.monotonic()
    next_poll = start
    while True:
        now = time.monotonic()
        if now - start > timeout:
            return "timeout", None, active
        if not active and now - start > activity_timeout:
            return "stalled", None, active
        watch.pump(0.25)
        updates: list[tuple[str, dict | None]] = []
        for ev in watch.take(block):
            body = ev.get("payload") or {}
            if ev.get("name") == "program_status_changed" and not body.get("id"):
                updates.append(("record", body.get("record") or {}))
            elif ev.get("name") == "program_status_removed" and "" in (body.get("ids") or []):
                updates.append(("removed", None))
            elif ev.get("name") == "child_exited":
                updates.append(("exited", None))
        if time.monotonic() >= next_poll:
            next_poll = time.monotonic() + 0.5
            rec, proc = poll_root(session, block)
            if proc.get("child") is None:
                updates.append(("exited", None))
            elif rec and rec.get("updated_at") != last_stamp:
                updates.append(("record", rec))
            elif rec is None and present:
                updates.append(("removed", None))
        for what, rec in updates:
            if what == "exited":
                return "exited", None, active
            if what == "removed":
                present = False
                if active:
                    return "unverifiable", None, active
                continue
            present = True
            if rec.get("updated_at") == last_stamp:
                continue
            last_stamp = rec.get("updated_at")
            state = rec.get("state")
            if state == "blocked":
                return "blocked", rec, active
            if state == "working":
                active = True
            elif (until == "settled" and rec.get("updated_at") != base_stamp
                  and (state in ("done", "error") or (state == "idle" and active))):
                return "settled", rec, active
