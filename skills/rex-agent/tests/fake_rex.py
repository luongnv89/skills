#!/usr/bin/env python3
"""A fake `rex` CLI for the rex-agent tests, shaped on output captured from Rex.

State lives in the JSON file named by $FAKE_REX_STATE, guarded by a lock so the
`rex events` tailer and one-shot calls can run at once. Scheduled transitions
(`pending`) fire lazily on any call once due, and append events in the real
wrapping: session_event > block_event > payload.

A block's `on_enter` is a list of scripts; each Enter pops one and schedules
its steps: [delay_s, action], where action is a record dict, "remove",
{"exit": code} or {"screen": text}. `spawn` holds the steps a newly split or
windowed block runs.
"""

from __future__ import annotations

import fcntl
import json
import os
import sys
import time
from contextlib import contextmanager

STATE = os.environ.get("FAKE_REX_STATE", "")


@contextmanager
def locked():
    with open(STATE + ".lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        with open(STATE) as fh:
            state = json.load(fh)
        yield state
        with open(STATE + ".tmp", "w") as fh:
            json.dump(state, fh)
        os.replace(STATE + ".tmp", STATE)


def stamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + f".{time.time_ns() % 10**9:09d}Z"


def emit(state: dict, block: str, name: str, payload: dict) -> None:
    state["events"].append({"type": "session_event", "payload": {"session_id": state["session"], "event": {
        "type": "block_event", "payload": {"block_id": block, "creator_name": "com.superlogical.terminal",
                                           "name": name, "payload": payload}}}})


def apply(state: dict, block_id: str, action) -> None:
    block = state["blocks"].get(block_id)
    if block is None:
        return
    if action == "remove":
        block["records"] = []
        emit(state, block_id, "program_status_removed", {"ids": [""], "reason": "clear"})
    elif isinstance(action, dict) and "screen" in action:
        block["screen"] = action["screen"]
    elif isinstance(action, dict) and "exit" in action:
        block["process"]["child"] = None
        block["process"]["foreground"] = None
        block["process"]["last_exit"] = {"exit_code": action["exit"]}
        emit(state, block_id, "child_exited", {"exit_code": action["exit"]})
    else:
        fg = block["process"].get("foreground") or {}
        rec = {**action, "updated_at": stamp(), "owner": {"pid": fg.get("pid", 0), "name": fg.get("name", "")}}
        block["records"] = [rec]
        emit(state, block_id, "program_status_changed", {"id": "", "record": rec, "reason": "report"})


def apply_due(state: dict) -> None:
    now = time.time()
    due = [p for p in state["pending"] if p["at"] <= now]
    state["pending"] = [p for p in state["pending"] if p["at"] > now]
    for p in sorted(due, key=lambda p: p["at"]):
        apply(state, p["block"], p["action"])


def schedule(state: dict, block: str, steps: list) -> None:
    now = time.time()
    for delay, action in steps:
        state["pending"].append({"at": now + delay, "block": block, "action": action})


def leaves(node: dict) -> list[str]:
    if "split" in node:
        return leaves(node["split"]["before"]) + leaves(node["split"]["after"])
    return [node["block_id"]]


def with_rects(node: dict, x: float = 0.0, w: float = 1.0) -> dict:
    if "split" not in node:
        return {"rect": [x, 0, w, 1], "block_id": node["block_id"]}
    s = node["split"]
    r = s["ratio"]
    horizontal = s["direction"] == "horizontal"
    before = with_rects(s["before"], x, w * r if horizontal else w)
    after = with_rects(s["after"], x + w * r if horizontal else x, w * (1 - r) if horizontal else w)
    return {"rect": [x, 0, w, 1], "split": {**s, "before": before, "after": after}}


def replace_leaf(node: dict, block: str, new: dict) -> dict:
    if "split" not in node:
        return new if node["block_id"] == block else node
    s = node["split"]
    return {"split": {**s, "before": replace_leaf(s["before"], block, new),
                      "after": replace_leaf(s["after"], block, new)}}


def remove_leaf(node: dict, block: str):
    if "split" not in node:
        return None if node["block_id"] == block else node
    s = node["split"]
    before, after = remove_leaf(s["before"], block), remove_leaf(s["after"], block)
    if before is None:
        return after
    if after is None:
        return before
    return {"split": {**s, "before": before, "after": after}}


def find_split(node: dict, before: str, after: str):
    if "split" not in node:
        return None
    s = node["split"]
    if before in leaves(s["before"]) and after in leaves(s["after"]):
        return s
    return find_split(s["before"], before, after) or find_split(s["after"], before, after)


def opt(args: list[str], name: str, default: str = "") -> str:
    for i, a in enumerate(args):
        if a == name and i + 1 < len(args):
            return args[i + 1]
        if a.startswith(name + "="):
            return a.split("=", 1)[1]
    return default


def new_block(state: dict, window: str, label: str, command: list[str]) -> str:
    state["next_id"] += 1
    block_id = f"block:{state['next_id']:08x}-0000-0000-0000-000000000000"
    words = command[:]
    if words[1:3] == ["-ic", 'exec "$0" "$@"']:
        words = words[3:]
    if words[:1] == ["env"]:
        words = words[1:]
        while words and "=" in words[0] and not words[0].startswith("-"):
            words = words[1:]
    binary = words[0] if words else "zsh"
    # pids above any pid_max, so no test ever reads a real process's argv or environment
    fg = {"pid": 4200000 + state["next_id"], "user_id": 501, "name": os.path.basename(binary), "argv0": binary}
    state["blocks"][block_id] = {"label": label or "shell", "window_id": window, "records": [], "paste": True,
                                 "screen": f"$ {' '.join(command)}\n", "typed": [], "keys": [], "on_enter": [],
                                 "process": {"last_exit": None, "child": dict(fg), "foreground": fg},
                                 "command": command}
    schedule(state, block_id, state.get("spawn", []))
    return block_id


def out(obj) -> None:
    print(json.dumps(obj))


def fail(msg: str, code: int = 1) -> None:
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(code)


def block_or_fail(state: dict, block_id: str) -> dict:
    if block_id not in state["blocks"]:
        fail(f'block target "{block_id}" not found', 3)
    return state["blocks"][block_id]


def main(argv: list[str]) -> None:
    args = [a for a in argv if not a.startswith("--autostart")]
    command: list[str] = []
    if "--" in args:
        command = args[args.index("--") + 1:]
        args = args[: args.index("--")]
    stdin = sys.stdin.read() if args[:1] == ["send"] else ""
    with locked() as state:
        state["log"].append(args + (["--", *command] if command else []))
        apply_due(state)
        if args[:1] == ["events"]:
            start = len(state["events"])
        else:
            dispatch(state, args, command, stdin)
            return
    deadline = time.time() + float(os.environ.get("FAKE_REX_EVENTS_MAX", "30"))
    while time.time() < deadline:
        with locked() as state:
            apply_due(state)
            fresh = state["events"][start:]
            start = len(state["events"])
        for ev in fresh:
            print(json.dumps(ev), flush=True)
        time.sleep(0.05)


def dispatch(state: dict, args: list[str], command: list[str], stdin: str) -> None:
    head = args[:2]
    session = state["session"]
    if args[:1] == ["whoami"]:
        out({"session_id": session, "window_id": state["windows"][0]["window_id"],
             "block_id": state.get("me", ""), "endpoint": state.get("endpoint", "unix:///tmp/fake.sock"),
             "rex_version": "0.0.1-fake"})
    elif head == ["session", "inspect"]:
        windows = []
        for win in state["windows"]:
            ids = leaves(win["layout"])
            blocks = [{"block_id": b, "label": state["blocks"][b]["label"]} for b in ids]
            windows.append({"window_id": win["window_id"], "label": win.get("label", ""),
                            "layers": [{"kind": "tiled", "layout": with_rects(win["layout"]), "blocks": blocks}]})
        out({"session_id": session, "windows": windows})
    elif head == ["block", "ls"]:
        out({"blocks": [{"block_id": b, "label": v["label"], "window_id": v["window_id"], "placement": "placed"}
                        for b, v in state["blocks"].items()]})
    elif head == ["block", "inspect"]:
        block_id = [a for a in args[2:] if a.startswith("block:")][0]
        block = block_or_fail(state, block_id)
        methods = {"process": {}, "format": {}, "write": {}}
        if not state.get("no_program_status"):
            methods["program_status"] = {}
        out({"session_id": session, "block": {"block_id": block_id, "label": block["label"],
                                              "window_id": block["window_id"]}, "api": {"methods": methods}})
    elif head == ["block", "call"]:
        block = block_or_fail(state, opt(args, "-b"))
        method = args[-1] if not args[-1].startswith("{") else args[-2]
        if method == "process":
            out(block["process"])
        elif method == "program_status":
            out({"records": block["records"]})
        elif method == "format":
            out({"content": "\x1b[?1049h\x1b[?2004h" if block.get("paste") else "\x1b[?1h"})
        else:
            fail(f"unknown method {method}", 3)
    elif head == ["block", "rename"]:
        block_or_fail(state, args[-2])["label"] = args[-1]
    elif head == ["block", "close"]:
        for block_id in [a for a in args[2:] if a.startswith("block:")]:
            state["blocks"].pop(block_id, None)
            for win in state["windows"]:
                win["layout"] = remove_leaf(win["layout"], block_id) or win["layout"]
    elif head == ["api", "describe"]:
        if args[2] != "session.resize_pane" or state.get("no_resize"):
            fail(f'API method "{args[2]}" not found. Run rex api list', 3)
        out({"description": "Move the shared border between two blocks."})
    elif head == ["api", "call"]:
        body = json.loads(args[-1])
        for win in state["windows"]:
            split = find_split(win["layout"], body["before_block_id"], body["after_block_id"])
            if split is not None:
                split["ratio"] = body["ratio"]
                out({"revision": 1})
                return
        fail("no shared border between those blocks")
    elif args[:1] == ["split"]:
        anchor = opt(args, "-b")
        block_or_fail(state, anchor)
        window = state["blocks"][anchor]["window_id"]
        block_id = new_block(state, window, opt(args, "--label"), command)
        for win in state["windows"]:
            if win["window_id"] == window:
                win["layout"] = replace_leaf(win["layout"], anchor, {"split": {
                    "split_id": f"split:{block_id[6:14]}", "direction": "horizontal", "ratio": 0.5,
                    "before": {"block_id": anchor}, "after": {"block_id": block_id}}})
        out({"anchor_block_id": anchor, "block_ids": [block_id], "revision": 2})
    elif head == ["window", "new"]:
        state["next_id"] += 1
        window = f"window:{state['next_id']:08x}"
        label = next((a for a in args[2:] if not a.startswith("-") and a not in (session, opt(args, "-c"))), "")
        block_id = new_block(state, window, "shell", command)
        state["windows"].append({"window_id": window, "label": label, "layout": {"block_id": block_id}})
        out({"window_id": window, "block_ids": [block_id], "revision": 3})
    elif args[:1] == ["send"]:
        block_or_fail(state, opt(args, "-b"))["typed"].append(stdin)
    elif args[:1] == ["send-key"]:
        block = block_or_fail(state, opt(args, "-b"))
        block["keys"].append(args[-1])
        if args[-1] == "enter" and block["on_enter"]:
            schedule(state, opt(args, "-b"), block["on_enter"].pop(0))
    elif args[:1] == ["capture"]:
        print(block_or_fail(state, opt(args, "-b"))["screen"], end="")
    elif args[:1] in (["focus"], ["kill"]):
        pass
    else:
        fail(f"fake rex does not implement: {' '.join(args)}", 2)


if __name__ == "__main__":
    main(sys.argv[1:])
