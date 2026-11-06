#!/usr/bin/env python3
"""Fake `tmux` CLI for tests. Not shipped as part of the skill.

State lives in a JSON file at $FAKE_TMUX_STATE, shaped:
{
  "sessions": {
    "<name>": {
      "text": "<current pane capture>",
      "fail_capture": false,
      "fail_send": false
    }
  }
}

Supported subcommands (only what the scripts under test call):
  has-session -t <name>
  capture-pane -t <name> -p [-S -N]
  send-keys -t <name> <args...>
  list-sessions
"""

from __future__ import annotations

import json
import os
import sys
import time


def load_state():
    path = os.environ["FAKE_TMUX_STATE"]
    for _ in range(20):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            time.sleep(0.01)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    path = os.environ["FAKE_TMUX_STATE"]
    tmp_path = f"{path}.tmp.{os.getpid()}.{id(state)}"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(state, f)
    os.replace(tmp_path, path)


def get_session(state, name):
    return state.get("sessions", {}).get(name)


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: tmux <cmd> ...", file=sys.stderr)
        return 1

    cmd = argv[0]
    args = argv[1:]
    state = load_state()

    if cmd == "has-session":
        # tmux has-session -t name
        target = None
        if "-t" in args:
            target = args[args.index("-t") + 1]
        elif args:
            target = args[0]
        if target and get_session(state, target) is not None:
            return 0
        print(f"can't find session: {target}", file=sys.stderr)
        return 1

    if cmd == "list-sessions":
        for name in state.get("sessions", {}):
            print(f"{name}: 1 windows")
        return 0

    if cmd == "capture-pane":
        target = None
        if "-t" in args:
            target = args[args.index("-t") + 1]
        sess = get_session(state, target) if target else None
        if sess is None:
            print(f"can't find pane: {target}", file=sys.stderr)
            return 1
        if sess.get("fail_capture"):
            print("capture failed", file=sys.stderr)
            return 1
        # -p prints plain text; -S is ignored for fake content.
        sys.stdout.write(sess.get("text", ""))
        if not sess.get("text", "").endswith("\n"):
            sys.stdout.write("\n")
        return 0

    if cmd == "send-keys":
        target = None
        keys = []
        i = 0
        while i < len(args):
            if args[i] == "-t" and i + 1 < len(args):
                target = args[i + 1]
                i += 2
                continue
            if args[i] == "-l":
                i += 1
                continue
            keys.append(args[i])
            i += 1
        sess = get_session(state, target) if target else None
        if sess is None:
            print(f"can't find pane: {target}", file=sys.stderr)
            return 1
        if sess.get("fail_send"):
            print("send-keys failed", file=sys.stderr)
            return 1
        # Append non-Enter keys to the pane text so tests can observe delivery.
        payload = " ".join(k for k in keys if k != "Enter")
        if payload:
            text = sess.get("text", "")
            if text and not text.endswith("\n"):
                text += "\n"
            text += payload + "\n"
            sess["text"] = text
            # Optional auto-behavior: if payload contains TAC_DONE_ split
            # instruction, append the joined marker after a short delay is
            # simulated by the test harness (not here).
            state["sessions"][target] = sess
            save_state(state)
        return 0

    print(f"fake_tmux: unsupported command: {cmd}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
