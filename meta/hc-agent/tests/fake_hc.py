#!/usr/bin/env python3
"""Fake `hc` (herdr-core) CLI for the hc-agent tests. Not shipped with the skill.

Output shapes copy what hc 0.1.20 printed on a live machine: `hc get --json`
records (argv, foreground {argv, cwd, pid}, labels, state, status {app, state,
msg}, status_ms, turn, created_ms, parent, die_with_parent), `hc ls --json`
rows without labels, `hc send` replying {"started", "status", "turn"}, and
errors as {"error": {"kind", "message", "hint"}} on stderr with exit codes
3 not_found, 7 needs_target, 9 blocked, 10 status_mismatch, 11 finished.

State is one JSON file at $FAKE_HC_STATE, shared with fake_herdr_app.py:
    terminals   address -> hc get record, plus a fake-only "screen" string
    app         the `herdr-app ls` document; status: the `herdr-app status` one
    pending     [{addr, at, status|null, screen?, finish?}] applied when due
    on_send     address -> list of schedules; each send pops the first one:
                [[delay_s, status|null, screen_text?], ...]
    spawn       the schedule a new pane.split terminal runs at boot
    flip_after_get / label_fails / split_fails   race and failure hooks
    log         every call: ["hc", ...] or ["herdr-app", ...]

The fake is strict: a subcommand, flag or --if value the skill must not use
exits 2, so a test can never pass on an invented or forbidden command.
"""

from __future__ import annotations

import contextlib
import fcntl
import json
import os
import sys
import time

STATE = os.environ.get("FAKE_HC_STATE", "")


@contextlib.contextmanager
def locked():
    with open(STATE + ".lock", "a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        with open(STATE) as fh:
            state = json.load(fh)
        apply_due(state)
        yield state
        with open(STATE + ".tmp", "w") as fh:
            json.dump(state, fh)
        os.replace(STATE + ".tmp", STATE)


def now_ms(rec: dict | None = None) -> int:
    stamp = int(time.time() * 1000)
    return max(stamp, ((rec or {}).get("status_ms") or 0) + 1)


def set_status(rec: dict, status: dict | None) -> None:
    if status and status.get("state") == "working" and (rec.get("status") or {}).get("state") != "working":
        rec["turn"] = (rec.get("turn") or 0) + 1
    rec["status"] = status
    rec["status_ms"] = now_ms(rec)


def schedule(state: dict, addr: str, items: list) -> None:
    start = time.time()
    for item in items:
        delay, status = item[0], item[1]
        entry = {"addr": addr, "at": start + delay, "status": status}
        if len(item) > 2:
            entry["screen"] = item[2]
        if status == "finish":
            entry = {"addr": addr, "at": start + delay, "finish": True}
        state.setdefault("pending", []).append(entry)


def apply_due(state: dict) -> None:
    keep, now = [], time.time()
    for item in sorted(state.get("pending") or [], key=lambda i: i["at"]):
        rec = state["terminals"].get(item["addr"])
        if item["at"] > now or rec is None:
            keep.append(item)
            continue
        if item.get("finish"):
            rec["state"], rec["status"] = "finished", None
            continue
        set_status(rec, item.get("status"))
        if item.get("screen"):
            rec["screen"] = rec.get("screen", "") + item["screen"]
    state["pending"] = keep


def fail(kind: str, message: str, code: int, hint: str = "") -> int:
    print(json.dumps({"error": {"hint": hint, "kind": kind, "message": message}}), file=sys.stderr)
    return code


def usage(message: str) -> int:
    print(f"fake hc: {message}", file=sys.stderr)
    return 2


def public(rec: dict) -> dict:
    return {k: v for k, v in rec.items() if k != "screen"}


def lookup(state: dict, word: str) -> dict | None:
    """hc resolves an address, or a name given with `hc run --name`; never a label."""
    rec = state["terminals"].get(word)
    if rec is None:
        rec = next((r for r in state["terminals"].values() if r.get("name") == word), None)
    return rec


def parse(args: list[str], flags: dict[str, bool]) -> tuple[dict, list[str]] | None:
    """flags: name -> takes a value. Repeatable values collect into lists."""
    opts: dict = {}
    words: list[str] = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--":
            words.extend(args[i + 1:])
            break
        if arg.startswith("--"):
            name, _, inline = arg[2:].partition("=")
            if name not in flags:
                return None
            if flags[name]:
                value = inline or (args[i + 1] if i + 1 < len(args) else None)
                if value is None:
                    return None
                opts.setdefault(name, []).append(value)
                i += 1 if inline else 2
                continue
            opts[name] = True
        else:
            words.append(arg)
        i += 1
    return opts, words


def main(argv: list[str]) -> int:
    if not STATE:
        return usage("FAKE_HC_STATE is unset")
    with locked() as state:
        state.setdefault("log", []).append(["hc", *argv])
    if not argv:
        return usage("bare hc attaches a picker; the skill must never run it")
    cmd, rest = argv[0], argv[1:]
    table = {
        "get": {"json": False},
        "ls": {"json": False, "all": False, "label": True},
        "label": {"json": False},
        "send": {"json": False, "if": True, "force": False, "wait": False, "timeout": True},
        "read": {"json": False, "lines": True},
        "wait": {"json": False, "timeout": True, "children": True, "output": True},
    }
    if cmd not in table:
        return usage(f"'{cmd}' is not modeled; hc-agent must not call it")
    parsed = parse(rest, table[cmd])
    if parsed is None:
        return usage(f"unknown or incomplete option in 'hc {' '.join(argv)}'")
    opts, words = parsed

    if cmd == "ls":
        wanted = [v.split("=", 1) for v in opts.get("label", [])]
        with locked() as state:
            rows = []
            for addr, rec in state["terminals"].items():
                if rec.get("state") != "live" and not opts.get("all"):
                    continue
                labels = rec.get("labels") or {}
                if all(len(w) == 2 and labels.get(w[0]) == w[1] for w in wanted):
                    st = rec.get("status") or {}
                    row = {"address": addr, "agent": st.get("app") or "zsh", "cwd": rec.get("cwd"),
                           "state": rec.get("state"), "turn": rec.get("turn") or 0,
                           "where": labels.get("where", "")}
                    if st.get("state"):
                        row["status"] = st["state"]
                    rows.append(row)
        print(json.dumps({"hidden_finished": 0, "machines": [], "terminals": rows}))
        return 0

    if not words:
        return fail("needs_target", "name a terminal", 7)
    with locked() as state:
        rec = lookup(state, words[0])
        if rec is None:
            return fail("not_found", f'no terminal "{words[0]}"', 3, "see `hc ls --all`")
        addr = rec["address"]
        if cmd == "get":
            print(json.dumps(public(rec)))
            flip = (state.get("flip_after_get") or {}).get(addr)
            if flip:  # test hook: change status after the Nth get (a race the preflight cannot see)
                flip[0] -= 1
                if flip[0] <= 0:
                    set_status(rec, flip[1])
                    del state["flip_after_get"][addr]
            return 0
        if cmd == "label":
            if state.get("label_fails"):
                return fail("not_found", f'no terminal "{addr}"', 3)
            if len(words) < 2 or any("=" not in w for w in words[1:]):
                return usage("label needs key=value pairs")
            labels = rec.setdefault("labels", {})
            for pair in words[1:]:
                key, _, value = pair.partition("=")
                if value:
                    labels[key] = value
                else:
                    labels.pop(key, None)
            print(json.dumps({"address": addr, "labels": labels}))
            return 0
        if cmd == "read":
            print(rec.get("screen", ""))
            return 0
        if cmd == "send":
            if len(words) != 2:
                return usage("send takes <terminal> <text>")
            cond = (opts.get("if") or [None])[0]
            if cond not in (None, "idle", "working"):
                return usage(f"--if {cond}: possible values are idle, working")
            if rec.get("state") == "finished":
                return fail("finished", f"{addr} has finished", 11)
            st = (rec.get("status") or {}).get("state")
            if st == "blocked" and not opts.get("force"):
                return fail("blocked", f"{addr} is blocked", 9, "read it; --force types anyway")
            if cond and st != cond:
                return fail("status_mismatch", f"{addr} is {st or 'silent'}, not {cond}", 10)
            rec["screen"] = rec.get("screen", "") + f"\n> {words[1]}\n"
            queue = (state.get("on_send") or {}).get(addr) or []
            if queue:
                schedule(state, addr, queue.pop(0))
            print(json.dumps({"started": None, "status": None, "turn": rec.get("turn") or 0}))
            return 0
    # wait: poll the shared state until the terminal stops working
    limit = time.time() + float((opts.get("timeout") or ["180"])[0])
    while True:
        with locked() as state:
            rec = state["terminals"][addr]
            working = rec.get("state") == "live" and (rec.get("status") or {}).get("state") == "working"
        if not working:
            print(json.dumps({"reason": "stopped"}))
            return 0
        if time.time() >= limit:
            print(json.dumps({"reason": "timeout"}))
            return 0
        time.sleep(0.05)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
