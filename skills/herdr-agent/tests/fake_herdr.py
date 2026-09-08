#!/usr/bin/env python3
"""Fake `herdr` CLI for tests. Not shipped as part of the skill.

State lives in a JSON file at $FAKE_HERDR_STATE, shaped:
{
  "panes": {
    "<pane_id>": {
      "agent_status": "idle|working|done|blocked|unknown",
      "text": "<current transcript>",
      "name": "<agent name or null>",
      "fail_run": true  # optional: "pane run" on this pane returns exit 1
                        # without mutating state, to simulate a dispatch
                        # failure partway through a broadcast fan-out.
      "status_after": 1,        # optional: report agent_status for the first
      "status_flip_to": "working"  # N gets, then flip to status_flip_to. Models
                        # a target that was safe at preflight but turned
                        # working/blocked before its pre-dispatch recheck.
    }
  }
}

Per-pane test hooks beyond the fields above:
  "fail_prompt": "<error_code>"  # `agent prompt` fails with this code
  "no_agent": true               # agent-surface commands report agent_not_found
  "fail_metadata": true          # `pane report-metadata` fails

Supported subcommands (only what the scripts under test call):
  pane get <id>
  pane read <id> --source ... --lines N
  pane split <id> --direction d --cwd c --no-focus
  pane rename <id> <name>
  pane run <id> <text...>
  pane send-keys <id> enter
  pane report-metadata <id> --source S [--title T] [--token K=V] [--ttl-ms N] ...
  agent get <name-or-id>
  agent list
  agent read <name-or-id> --source ... --lines N
  agent prompt <name-or-id> <text> [--wait] [--until S] [--timeout MS]
  agent wait <name-or-id> [--until S] [--timeout MS]
  agent start <name> --kind K --pane ID [--timeout MS] [-- args...]
  agent rename <id> <name>
  api snapshot

Server errors are JSON on stderr with exit status 1, matching the real CLI.
"""

from __future__ import annotations

import json
import os
import sys
import time


def load_state():
    path = os.environ["FAKE_HERDR_STATE"]
    # os.replace() is atomic, but a reader can still land in the brief gap
    # where the old inode was just unlinked; retry a few times rather than
    # let a concurrent writer flake the test.
    for _ in range(20):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            time.sleep(0.01)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    # Concurrent `herdr` invocations (broadcast waits on several panes at
    # once) can read this file mid-write; write-then-rename makes each
    # update atomic so a reader never sees a truncated/partial JSON file.
    path = os.environ["FAKE_HERDR_STATE"]
    tmp_path = f"{path}.tmp.{os.getpid()}.{id(state)}"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(state, f)
    os.replace(tmp_path, path)


def find_pane_by_id(state, pane_id):
    """`pane <verb> <id>` only accepts literal pane ids, like real herdr."""
    return pane_id if pane_id in state["panes"] else None


def find_pane(state, ident):
    """`agent <verb> <ident>` accepts a pane id OR an agent name."""
    panes = state["panes"]
    if ident in panes:
        return ident
    for pid, p in panes.items():
        if p.get("name") == ident:
            return pid
    return None


def cmd_pane_get(args):
    state = load_state()
    pid = find_pane_by_id(state, args[0])
    if pid is None:
        print(json.dumps({"error": "not found"}))
        return 1
    p = state["panes"][pid]
    if p.get("fail_get"):
        # Simulate a failing `herdr pane get` (server hiccup / gone pane):
        # non-zero exit, so a preflight must reject rather than fall open.
        print(json.dumps({"error": "simulated pane get failure"}), file=sys.stderr)
        return 1
    # Counter-based fault: succeed the first `fail_get_after` calls, then fail
    # every subsequent one. Deterministic "valid status, THEN lookup failure"
    # with no timing race. The counter is persisted in the state file.
    remaining = p.get("fail_get_after")
    if remaining is not None:
        if remaining <= 0:
            print(json.dumps({"error": "simulated pane get failure (after N)"}), file=sys.stderr)
            return 1
        p["fail_get_after"] = remaining - 1
        save_state(state)
    if p.get("malformed_get"):
        # Simulate a 0-exit but unparseable/unexpected-shape response.
        print("not json at all {[")
        return 0
    if p.get("null_pane_get"):
        # Valid JSON, 0 exit, but a null `pane` — .get() on it would crash a
        # naive parser. Must be treated as unverifiable, not raise.
        print(json.dumps({"result": {"pane": None}}))
        return 0
    # Counter-based status FLIP: report agent_status for the first
    # `status_after` gets, then switch to `status_flip_to` on every get after.
    # Deterministic "was idle at preflight, turned working/blocked before
    # dispatch" with no timing race — mirrors the fail_get_after pattern.
    status = p["agent_status"]
    n = p.get("status_after")
    if n is not None:
        if n <= 0:
            status = p.get("status_flip_to", status)
        else:
            p["status_after"] = n - 1
            save_state(state)
    print(json.dumps({"result": {"pane": {"pane_id": pid, "agent_status": status}}}))
    return 0


def cmd_pane_read(args):
    state = load_state()
    pid = find_pane_by_id(state, args[0])
    if pid is None:
        print("")
        return 1
    if state["panes"][pid].get("fail_read"):
        print(json.dumps({"error": "simulated pane read failure"}), file=sys.stderr)
        return 1
    print(state["panes"][pid]["text"])
    return 0


def cmd_pane_split(args):
    state = load_state()
    src = args[0]
    new_id = f"{src}-split{len(state['panes'])}"
    state["panes"][new_id] = {"agent_status": "unknown", "text": "", "name": None}
    save_state(state)
    print(json.dumps({"result": {"pane": {"pane_id": new_id}}}))
    return 0


def cmd_pane_rename(args):
    state = load_state()
    pid = find_pane_by_id(state, args[0])
    if pid is not None:
        state["panes"][pid]["name"] = args[1]
        save_state(state)
    print(json.dumps({"result": {}}))
    return 0


def cmd_pane_run(args):
    state = load_state()
    pid = find_pane_by_id(state, args[0])
    text = args[1] if len(args) > 1 else ""
    if pid is not None:
        if state["panes"][pid].get("fail_run"):
            print(json.dumps({"error": "simulated pane run failure"}), file=sys.stderr)
            return 1
        state["panes"][pid]["agent_status"] = "working"
        state["panes"][pid]["text"] += f"\n$ {text}\n"
        save_state(state)
    print(json.dumps({"result": {}}))
    return 0


def cmd_pane_send_keys(args):
    print(json.dumps({"result": {}}))
    return 0


def herdr_error(code, message):
    """Emit a server error exactly as the real CLI does: JSON on stderr, exit 1."""
    print(json.dumps({"error": {"code": code, "message": message}}), file=sys.stderr)
    return 1


def effective_status(state, pid, consume=False):
    """Report agent_status for the first `status_after` reads, then flip.

    Models a target that was safe on the roster read but turned working or
    blocked before its pre-dispatch recheck, with no timing race.
    """
    p = state["panes"][pid]
    status = p["agent_status"]
    n = p.get("status_after")
    if n is None:
        return status
    if n <= 0:
        return p.get("status_flip_to", status)
    if consume:
        p["status_after"] = n - 1
        save_state(state)
    return status


def agent_record(state, pid, consume=False, raw=True):
    """raw=True reports the stored status; raw=False applies the flip counter.

    `agent list` (the roster) reports raw, so a flip models a change that
    happened AFTER the roster read — which is the window the pre-dispatch
    recheck exists to close.
    """
    p = state["panes"][pid]
    return {
        "agent": p.get("kind", "claude"),
        "agent_status": (
            p["agent_status"] if raw
            else effective_status(state, pid, consume=consume)
        ),
        "name": p.get("name"),
        "pane_id": pid,
        "tab_id": p.get("tab_id", "w1:t1"),
        "workspace_id": p.get("workspace_id", "w1"),
        "focused": bool(p.get("focused")),
        "title": p.get("title"),
        "tokens": p.get("tokens", {}),
    }


def resolve_agent(state, ident):
    """Agent-surface resolution: a pane with no detected agent is not a target."""
    pid = find_pane(state, ident)
    if pid is None or state["panes"][pid].get("no_agent"):
        return None
    return pid


def cmd_agent_get(args):
    state = load_state()
    pid = resolve_agent(state, args[0])
    if pid is None:
        return herdr_error("agent_not_found", f"agent target {args[0]} not found")
    print(
        json.dumps(
            {"result": {"agent": agent_record(state, pid, consume=True, raw=False)}}
        )
    )
    return 0


def cmd_agent_list(_args):
    state = load_state()
    agents = [
        agent_record(state, pid)
        for pid, p in state["panes"].items()
        if not p.get("no_agent")
    ]
    print(json.dumps({"result": {"agents": agents}}))
    return 0


def cmd_agent_read(args):
    state = load_state()
    pid = resolve_agent(state, args[0])
    if pid is None:
        return herdr_error("agent_not_found", f"agent target {args[0]} not found")
    print(state["panes"][pid]["text"])
    return 0


def cmd_agent_prompt(args):
    state = load_state()
    pid = resolve_agent(state, args[0])
    if pid is None:
        return herdr_error("agent_not_found", f"agent target {args[0]} not found")
    pane = state["panes"][pid]
    # Real `agent prompt` refuses a blocked target BEFORE writing any input.
    if pane["agent_status"] == "blocked":
        return herdr_error("agent_blocked", f"{pid} is waiting at a dialog")
    forced = pane.get("fail_prompt")
    if forced:
        return herdr_error(forced, f"simulated {forced} for {pid}")
    text = args[1] if len(args) > 1 else ""
    pane["text"] += f"\n> {text}\n<reply>\n"
    pane["agent_status"] = "idle"
    save_state(state)
    print(json.dumps({"result": {"agent": agent_record(state, pid)}}))
    return 0


def cmd_agent_wait(args):
    state = load_state()
    pid = resolve_agent(state, args[0])
    if pid is None:
        return herdr_error("agent_not_found", f"agent target {args[0]} not found")
    until = []
    timeout_ms = 1000
    it = iter(args[1:])
    for a in it:
        if a == "--until":
            until.append(next(it))
        elif a == "--timeout":
            timeout_ms = int(next(it))
    settled = set(until) or {"idle", "done", "blocked"}
    deadline = time.time() + timeout_ms / 1000.0
    while time.time() < deadline:
        st = load_state()["panes"][pid]["agent_status"]
        if st in settled:
            return 0
        time.sleep(0.02)
    return herdr_error("timeout", f"{pid} did not settle")


def cmd_agent_start(args):
    state = load_state()
    name = args[0]
    pane_id = None
    it = iter(args[1:])
    for a in it:
        if a == "--pane":
            pane_id = next(it)
    pid = find_pane_by_id(state, pane_id) if pane_id else None
    if pid is None:
        return herdr_error("not_found", f"pane {pane_id} not found")
    pane = state["panes"][pid]
    if pane.get("blocked_on_start"):
        return herdr_error("agent_not_ready", f"{pid} booted into a dialog")
    pane["name"] = name
    pane["agent_status"] = "idle"
    pane["no_agent"] = False
    save_state(state)
    print(json.dumps({"result": {"agent": agent_record(state, pid)}}))
    return 0


def cmd_pane_report_metadata(args):
    state = load_state()
    pid = find_pane_by_id(state, args[0])
    if pid is None:
        return herdr_error("not_found", f"pane {args[0]} not found")
    pane = state["panes"][pid]
    if pane.get("fail_metadata"):
        return herdr_error("invalid_request", "simulated metadata rejection")
    it = iter(args[1:])
    for a in it:
        if a == "--title":
            pane["title"] = next(it)
        elif a == "--token":
            k, _, v = next(it).partition("=")
            pane.setdefault("tokens", {})[k] = v
        elif a in ("--source", "--display-agent", "--state-label", "--ttl-ms"):
            next(it)
    save_state(state)
    print(json.dumps({"result": {"type": "ok"}}))
    return 0


def cmd_api_snapshot(_args):
    state = load_state()
    agents = [
        agent_record(state, pid)
        for pid, p in state["panes"].items()
        if not p.get("no_agent")
    ]
    panes = [agent_record(state, pid) for pid in state["panes"]]
    print(
        json.dumps(
            {
                "result": {
                    "snapshot": {
                        "version": "0.9.0",
                        "focused_pane_id": next(iter(state["panes"]), None),
                        "agents": agents,
                        "panes": panes,
                        "tabs": [],
                        "workspaces": [],
                        "layouts": [],
                    }
                }
            }
        )
    )
    return 0


def cmd_agent_rename(args):
    return cmd_pane_rename(args)


def main(argv):
    if not argv:
        return 1
    group = argv[0]
    if group == "pane":
        sub = argv[1]
        rest = argv[2:]
        if sub == "get":
            return cmd_pane_get(rest)
        if sub == "read":
            return cmd_pane_read(rest)
        if sub == "split":
            return cmd_pane_split(rest)
        if sub == "rename":
            return cmd_pane_rename(rest)
        if sub == "run":
            return cmd_pane_run(rest)
        if sub == "send-keys":
            return cmd_pane_send_keys(rest)
        if sub == "report-metadata":
            return cmd_pane_report_metadata(rest)
    elif group == "agent":
        sub = argv[1]
        rest = argv[2:]
        if sub == "get":
            return cmd_agent_get(rest)
        if sub == "list":
            return cmd_agent_list(rest)
        if sub == "rename":
            return cmd_agent_rename(rest)
        if sub == "read":
            return cmd_agent_read(rest)
        if sub == "prompt":
            return cmd_agent_prompt(rest)
        if sub == "wait":
            return cmd_agent_wait(rest)
        if sub == "start":
            return cmd_agent_start(rest)
    elif group == "api":
        if argv[1] == "snapshot":
            return cmd_api_snapshot(argv[2:])
    print(f"fake_herdr: unhandled command: {argv}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
