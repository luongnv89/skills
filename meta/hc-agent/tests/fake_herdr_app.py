#!/usr/bin/env python3
"""Fake `herdr-app` CLI for the hc-agent tests. Not shipped with the skill.

COMMANDS is the argument table `herdr-app commands` printed for Herdr.app
0.1.15. Every `do` call is checked against it: an unknown command or argument
fails, as the real CLI does. Only the four commands hc-agent uses are modeled:
pane.split, pane.focus, agent.focus and pane.close. Any other known command is
logged and refused, so a test that asserts the call log catches it.

Shapes copy the live app: `ls` -> {"spaces": [{id, name, tabs: [{id, name,
terminals: [{terminal, pane, status, app, name, sub_agents}]}]}]}, `status` ->
{space, tab, focused_pane, ...}, pane.split -> {"pane", "terminal"} and the new
pane takes focus, errors -> {"error": "..."} with exit 1. Bare `herdr-app`
opens the person's window, so it exits 2 here.

State is shared with fake_hc.py through $FAKE_HC_STATE.
"""

from __future__ import annotations

import json
import sys

from fake_hc import locked, schedule

COMMANDS = {
    'space.new': ('name', 'folder', 'tab', 'argv', 'task', 'machine'),
    'space.close': ('id', 'confirmed'),
    'space.rename': ('id', 'name'),
    'space.move': ('id', 'index'),
    'tab.new': ('name', 'space', 'folder', 'argv', 'task', 'mod', 'props'),
    'tab.close': ('id', 'confirmed'),
    'tab.rename': ('id', 'name'),
    'tab.move': ('id', 'index'),
    'pane.split': ('direction', 'pane', 'argv', 'mod', 'props'),
    'pane.close': ('pane',),
    'terminal.open': ('argv', 'folder', 'place', 'name'),
    'terminal.keep': ('terminal', 'place'),
    'terminal.park': ('terminal',),
    'terminal.right_click': ('to', 'terminal'),
    'terminal.pin': ('terminal', 'pinned'),
    'terminal.kill': ('terminal',),
    'space.select': ('index', 'id'),
    'space.next': (),
    'space.prev': (),
    'tab.select': ('index', 'id'),
    'tab.settle': ('id',),
    'tab.unsettle': ('id',),
    'tab.next': (),
    'tab.prev': (),
    'pane.zoom': ('pane',),
    'pane.focus': ('pane', 'terminal'),
    'pane.go': ('direction',),
    'pane.swap': ('direction', 'pane', 'target'),
    'terminal.peek': ('terminal',),
    'terminal.show': ('terminal', 'pane'),
    'terminal.copy': (),
    'terminal.scroll': ('lines', 'pages', 'to', 'terminal'),
    'terminal.paste': (),
    'terminal.paste_image': (),
    'terminal.search': (),
    'agent.focus': ('terminal',),
    'agent.next': (),
    'agent.prev': (),
    'layout.switch': ('name',),
    'layout.clone': ('name', 'as'),
    'mod.clone': ('name', 'as'),
    'layout.set': ('layout',),
    'layout.toggle': ('id',),
    'layout.show': ('id',),
    'layout.hide': ('id',),
    'layout.resize': ('id', 'px', 'weight'),
    'layout.select': ('stack', 'child'),
    'layout.reset': ('name',),
    'mod.open': ('name',),
    'overlay.close': ('id',),
    'app.help': (),
    'app.welcome': (),
    'app.whats_new': (),
    'app.feedback': ('message', 'from'),
    'app.palette': (),
    'app.settings': ('section',),
    'app.check_updates': (),
    'app.update_core': (),
    'app.reset': (),
    'app.theme': ('name',),
    'app.zoom_in': (),
    'app.zoom_out': (),
    'app.zoom_reset': (),
    'app.update': (),
    'app.quit': (),
    'app.hide': (),
    'app.hide_others': (),
    'app.show_all': (),
    'window.close': (),
    'window.minimize': (),
    'window.maximize': (),
}


def error(message: str) -> int:
    print(json.dumps({"error": message}))
    return 1


def tab_of(state: dict, pane: str) -> tuple[dict, dict, int] | None:
    for space in state["app"]["spaces"]:
        for tab in space["tabs"]:
            for i, term in enumerate(tab["terminals"]):
                if term["pane"] == pane:
                    return space, tab, i
    return None


def pane_of(state: dict, terminal: str) -> str | None:
    for space in state["app"]["spaces"]:
        for tab in space["tabs"]:
            for term in tab["terminals"]:
                if term["terminal"] == terminal:
                    return term["pane"]
    return None


def split(state: dict, args: dict) -> int:
    if args.get("direction") not in ("right", "down"):
        return error("direction must be \"right\" or \"down\"")
    pane = args.get("pane") or state["status"].get("focused_pane")
    found = tab_of(state, pane)
    if found is None:
        return error(f"no pane {pane}")
    space, tab, index = found
    if state.get("split_fails"):
        return error("split refused")
    argv = json.loads(args["argv"]) if args.get("argv") else ["/bin/zsh", "-l"]
    parent = state["terminals"][tab["terminals"][index]["terminal"]]
    cwd, fg = parent.get("cwd"), list(argv)
    if argv[:3] == ["/bin/sh", "-c", 'cd "$0" && exec "$@"'] and len(argv) > 4:
        cwd, fg = argv[3], argv[4:]
    state["next"] = state.get("next", 100) + 1
    addr, new_pane = f"t{state['next']:x}", f"p{state['next']:032x}"
    state["terminals"][addr] = {
        "address": addr, "argv": argv, "cwd": cwd, "created_ms": 2000 + state["next"],
        "die_with_parent": False, "exit_code": None, "finished_ms": None,
        "foreground": {"argv": fg, "cwd": cwd, "name": "2.1.322", "pid": 4200000 + state["next"]},
        "labels": {"herdr.space": space["id"], "herdr.tab": tab["id"]}, "name": None, "parent": None,
        "pid": 4200000 + state["next"], "state": "live", "status": None, "status_ms": 0, "turn": 0,
        "screen": "",
    }
    tab["terminals"].insert(index + 1, {"terminal": addr, "pane": new_pane, "status": None, "app": None,
                                        "name": None, "sub_agents": []})
    state["status"]["focused_pane"] = new_pane
    schedule(state, addr, state.get("spawn") or [])
    print(json.dumps({"pane": new_pane, "terminal": addr}))
    return 0


def main(argv: list[str]) -> int:
    with locked() as state:
        state.setdefault("log", []).append(["herdr-app", *argv])
        if not argv:
            print("fake herdr-app: bare herdr-app opens the window; never run it", file=sys.stderr)
            return 2
        if argv == ["ls"]:
            print(json.dumps(state["app"]))
            return 0
        if argv == ["status"]:
            print(json.dumps(state["status"]))
            return 0
        if argv[0] != "do" or len(argv) < 2:
            print(f"fake herdr-app: '{' '.join(argv)}' is not modeled", file=sys.stderr)
            return 2
        command, rest = argv[1], argv[2:]
        if command not in COMMANDS:
            return error(f"unknown command {command}")
        if len(rest) % 2 or any(not w.startswith("--") for w in rest[::2]):
            return error("arguments are --key value pairs")
        args = {k[2:]: v for k, v in zip(rest[::2], rest[1::2])}
        unknown = [k for k in args if k not in COMMANDS[command]]
        if unknown:
            return error(f"unknown argument {unknown[0]}; valid: {', '.join(COMMANDS[command])}")
        if command == "pane.split":
            return split(state, args)
        if command in ("pane.focus", "agent.focus"):
            pane = args.get("pane") or pane_of(state, args.get("terminal", ""))
            if not pane or tab_of(state, pane) is None:
                return error("no such pane or terminal")
            state["status"]["focused_pane"] = pane
            print(json.dumps({"ok": True}))
            return 0
        if command == "pane.close":
            found = tab_of(state, args.get("pane", ""))
            if found is None:
                return error("no such pane")
            _, tab, index = found
            term = tab["terminals"].pop(index)
            rec = state["terminals"].get(term["terminal"])
            if rec:
                rec["state"], rec["status"] = "finished", None
            print(json.dumps({"ok": True}))
            return 0
        return error(f"fake herdr-app: {command} is not modeled; hc-agent must not call it")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
