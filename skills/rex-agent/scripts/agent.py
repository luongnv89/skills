#!/usr/bin/env python3
"""Drive agents in Rex blocks: check, get, prompt, wait, read, fleet, broadcast, dispatch.

Rex has no agent registry and no one-call prompt-and-wait, so this CLI adds
both on top of the rex command. A worker's name is its block label, resolved
by exact match (never an ID suffix). Its state is the root OSC 7501 program
status record its CLI reports, trusted only while the record's owner is the
block's foreground process: a `done` left behind by an agent that exited to
its shell is stale.

    check                          prerequisites: server, this terminal, capabilities
    get TARGET                     classify one block (JSON)
    prompt TARGET TEXT|-           refuse unsafe targets, type TEXT + Enter, wait for the turn
    wait TARGET [--until blocked]  wait without sending
    read TARGET [--turn ID]        the visible screen, or the rows after that turn's echo
    fleet [--all] [--json]         every block in the root window, most urgent first
    broadcast TEXT TARGET...       one task to several targets, concurrently
    dispatch FILE|-                a JSON object {name: task}, concurrently

prompt starts `rex events` before writing and records the pre-send record, so
the turn it waits for is the one it caused. It appends a per-turn tag,
`(rex-agent turn ID)`, so `read --turn ID` finds exactly that turn's echo.

Exit codes: 0 ok/settled · 1 error · 2 usage · 3 blocked · 4 unverifiable
(no program status) · 5 no agent · 6 working (refused) · 7 stalled · 8 timeout
· 9 exited
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import rexlib
from rexlib import EXIT, RexError

REFUSE = {"working": "working", "blocked": "blocked", "unverified": "unverifiable",
          "no-agent": "no_agent", "exited": "exited", "unknown": "unverifiable"}
ROLE_ORDER = {"worker": 0, "unknown": 1, "other": 2, "root": 3}


def ancestors() -> list[int]:
    pids, pid = [], os.getpid()
    for _ in range(40):
        try:
            out = subprocess.run(["ps", "-o", "ppid=", "-p", str(pid)], capture_output=True,
                                 text=True, timeout=5).stdout.strip()
            pid = int(out)
        except (OSError, ValueError, subprocess.TimeoutExpired):
            break
        if pid <= 1:
            break
        pids.append(pid)
    return pids


def check(session: str) -> dict:
    """Confirm the server, that REX_SESSION/REX_BLOCK are this terminal, and capabilities."""
    block = os.environ.get("REX_BLOCK", "")
    if not block:
        raise RexError("REX_BLOCK is unset, so this is not a Rex terminal. Run the orchestrator "
                       "inside Rex; never act on whatever session the app happens to show.")
    me = rexlib.whoami()
    if (me.get("session_id"), me.get("block_id")) != (session, block):
        raise RexError(f"REX_SESSION/REX_BLOCK ({session}, {block}) do not exist as this session and "
                       f"block according to 'rex whoami' ({me.get('session_id')}, {me.get('block_id')}). "
                       "Open a new Rex terminal, or pass the IDs that whoami reports.")
    rexlib.require_capabilities(session, block)
    fg = rexlib.block_call(session, block, "process").get("foreground") or {}
    confirmed = None
    if str(me.get("endpoint") or "").startswith("unix:") and fg.get("pid"):
        confirmed = fg["pid"] in ancestors()
        if not confirmed:
            print(f"warning: block {block}'s foreground process ({fg['pid']}) is not an ancestor of "
                  "this command, so REX_BLOCK may be inherited from another terminal. Confirm with the "
                  "user before treating that block as root.", file=sys.stderr)
    return {"session_id": session, "window_id": me.get("window_id"), "block_id": block,
            "endpoint": me.get("endpoint"), "rex_version": me.get("rex_version"),
            "cwd": fg.get("cwd") or os.getcwd(), "capabilities": "ok", "terminal_confirmed": confirmed}


def target_block(session: str, target: str, blocks: list[dict] | None = None) -> dict:
    block = rexlib.resolve(session, target, blocks)
    if block["block_id"] == os.environ.get("REX_BLOCK"):
        raise RexError(f"'{target}' is your own block ({block['block_id']}); never prompt or "
                       "steer the orchestrator's own pane.")
    return block


def preflight(session: str, block: dict, settle: str) -> tuple[str | None, dict]:
    """Return (refusal outcome or None, agent). Nothing is sent on a refusal."""
    agent = rexlib.inspect_agent(session, block)
    status = agent["status"]
    if status == "unverified" and settle == "screen":
        return None, agent
    if status in rexlib.READY:
        return None, agent
    return REFUSE.get(status, "unverifiable"), agent


def screen_settle(session: str, block: str, before: str, activity_timeout: float,
                  timeout: float, quiet: float) -> str:
    """Weaker wait for agents with no program status: the screen changes, then holds still."""
    start, last, still_since, changed = time.monotonic(), before, None, False
    while time.monotonic() - start < timeout:
        time.sleep(0.5)
        now_text = rexlib.capture(session, block)
        if now_text != last:
            changed, last, still_since = True, now_text, time.monotonic()
        elif changed and still_since and time.monotonic() - still_since >= quiet:
            return "settled"
        if not changed and time.monotonic() - start > activity_timeout:
            return "stalled"
    return "timeout"


def do_prompt(session: str, target: str, text: str, timeout: float, activity_timeout: float,
              settle: str = "status", quiet: float = 5.0, blocks: list[dict] | None = None,
              raw: bool = False) -> dict:
    if not raw and rexlib.sanitize(text).lstrip().startswith("!"):
        raise RexError("the task starts with '!', which Claude Code runs as a shell command instead of "
                       "a prompt. Reword it, or pass --raw to send the text exactly as given.")
    block = target_block(session, target, blocks)
    refusal, agent = preflight(session, block, settle)
    turn = "" if raw else secrets.token_hex(3)
    result = {"target": target, "block_id": block["block_id"], "kind": agent["kind"],
              "status": agent["status"], "sent": False, "turn": turn}
    if refusal:
        return {**result, "outcome": refusal}
    tag = f"(rex-agent turn {turn})" if turn else ""
    started = time.monotonic()
    if agent["status"] == "unverified":
        before = rexlib.capture(session, block["block_id"])
        result["paste"] = rexlib.send_prompt(session, block["block_id"], text, tag)
        outcome = screen_settle(session, block["block_id"], before, activity_timeout, timeout, quiet)
        return {**result, "sent": True, "outcome": outcome, "state": "screen-quiet",
                "waited_s": round(time.monotonic() - started, 1)}
    baseline, _ = rexlib.poll_root(session, block["block_id"])
    watch = rexlib.Watch(session)
    try:
        result["paste"] = rexlib.send_prompt(session, block["block_id"], text, tag)
        result["sent"] = True
        outcome, rec, worked = rexlib.wait_turn(session, block["block_id"], watch, baseline=baseline,
                                                activity_timeout=activity_timeout, timeout=timeout)
    finally:
        watch.close()
    return {**result, "outcome": outcome, "state": (rec or {}).get("state"), "observed_working": worked,
            "msg": (rec or {}).get("msg"), "waited_s": round(time.monotonic() - started, 1)}


def do_wait(session: str, target: str, until: str, timeout: float) -> dict:
    block = target_block(session, target)
    agent = rexlib.inspect_agent(session, block)
    result = {"target": target, "block_id": block["block_id"], "kind": agent["kind"]}
    status = agent["status"]
    if status in ("unverified", "no-agent", "exited"):
        return {**result, "outcome": REFUSE[status], "state": status}
    if status == "blocked" or (until == "settled" and status in rexlib.READY):
        return {**result, "outcome": "blocked" if status == "blocked" else "settled", "state": status}
    baseline, _ = rexlib.poll_root(session, block["block_id"])
    watch = rexlib.Watch(session)
    try:
        outcome, rec, _ = rexlib.wait_turn(session, block["block_id"], watch, baseline=baseline,
                                           activity_timeout=timeout, timeout=timeout,
                                           active=status == "working", until=until)
    finally:
        watch.close()
    return {**result, "outcome": outcome, "state": (rec or {}).get("state")}


def locate(rows: list[str], needle: str, last: bool) -> int | None:
    """Index of the row holding the end of needle, matched with whitespace removed."""
    flat, starts = "", []
    for row in rows:
        starts.append(len(flat))
        flat += "".join(row.split())
    pos = (flat.rfind(needle) if last else flat.find(needle)) if needle else -1
    if pos < 0:
        return None
    end = pos + len(needle) - 1
    return max(i for i, start in enumerate(starts) if start <= end)


def do_read(session: str, target: str, turn: str, after: str, lines: int) -> tuple[int, str]:
    """The visible screen, or the rows after one turn's echo.

    --turn anchors on the unique tag `prompt` appended, so a reply that repeats
    the task cannot move the anchor. --after anchors on the last 24 non-space
    characters of a task sent without a tag. Matching ignores whitespace across
    rows, because TUIs hard-wrap long prompts. Exit 4: the anchor scrolled off.
    """
    block = target_block(session, target)
    rows = rexlib.capture(session, block["block_id"]).rstrip("\n").split("\n")
    while rows and not rows[-1].strip():
        rows.pop()
    if turn or after:
        if turn:
            index, what = locate(rows, f"(rex-agentturn{turn})", last=False), f"turn {turn}'s tag"
        else:
            index, what = locate(rows, "".join(rexlib.sanitize(after).split())[-24:], last=True), "the task's end"
        if index is None:
            return EXIT["unverifiable"], (f"{what} is not on {target}'s screen: the reply pushed it above "
                                          "the visible rows. Use the file fallback in "
                                          "references/delivery-and-waiting.md.")
        rows = rows[index + 1:]
    rows = [row for i, row in enumerate(rows) if row.strip() or (i and rows[i - 1].strip())]
    return 0, "\n".join(rows[-lines:] if lines else rows).strip("\n")


def fleet(session: str, window: str, all_windows: bool) -> list[dict]:
    """Every block, with role root (this block), worker (started with REX_AGENT_ROLE),
    other (a readable process without it), or unknown (process environment unreadable)."""
    blocks = [b for b in rexlib.list_blocks(session) if all_windows or b.get("window_id") == window]
    me = os.environ.get("REX_BLOCK")
    rows = []
    for block in blocks:
        try:
            row = rexlib.inspect_agent(session, block)
        except RexError as err:
            row = {"name": block.get("label") or "", "block_id": block["block_id"], "kind": "",
                   "status": "unknown", "msg": str(err), "worker_role": None, "env_readable": False}
        if block["block_id"] == me:
            row["role"] = "root"
        elif row.get("worker_role"):
            row["role"] = "worker"
        else:
            row["role"] = "other" if row.get("env_readable") else "unknown"
        rows.append(row)
    rank = {s: i for i, s in enumerate(rexlib.ATTENTION)}
    return sorted(rows, key=lambda r: (ROLE_ORDER[r["role"]], rank.get(r["status"], 99), r["name"]))


def render(rows: list[dict]) -> str:
    out = []
    for r in rows:
        note = r.get("msg") or (r.get("blocked_kind") and f"needs {r['blocked_kind']}") or ""
        role = "" if r["role"] == "worker" else f"  ({r['role']})"
        out.append(f"{r['status']:<10} {r['name'] or '-':<16} {r['kind'] or '-':<8} "
                   f"{r['block_id']}{role}{'  · ' + note[:70] if note else ''}")
    counts: dict[str, int] = {}
    for r in rows:
        if r["role"] == "worker":
            counts[r["status"]] = counts.get(r["status"], 0) + 1
    order = {s: i for i, s in enumerate(rexlib.ATTENTION)}
    tally = ", ".join(f"{n} {s}" for s, n in sorted(counts.items(), key=lambda kv: order.get(kv[0], 99)))
    others = sum(1 for r in rows if r["role"] in ("other", "unknown"))
    out.append(f"Fleet: {sum(counts.values())} worker(s){': ' + tally if tally else ''}"
               f"{f' · {others} other block(s)' if others else ''} · polled {time.strftime('%H:%M:%S')}")
    return "\n".join(out)


def fan_out(session: str, jobs: list[tuple[str, str]], timeout: float, activity_timeout: float) -> list[dict]:
    """Prompt each (target, task) pair concurrently; one listing resolves every target."""
    blocks = rexlib.list_blocks(session)
    seen, todo, results = set(), [], []
    for target, task in jobs:
        try:
            block = target_block(session, target, blocks)
        except RexError as err:
            results.append({"target": target, "outcome": "error", "reason": str(err)})
            continue
        if block["block_id"] in seen:
            continue
        seen.add(block["block_id"])
        todo.append((target, task))
    with ThreadPoolExecutor(max_workers=max(1, len(todo))) as pool:
        futures = {t: pool.submit(do_prompt, session, t, task, timeout, activity_timeout, "status", 5.0, blocks)
                   for t, task in todo}
        for target, fut in futures.items():
            try:
                results.append(fut.result())
            except RexError as err:
                results.append({"target": target, "outcome": "error", "reason": str(err)})
    return results


def read_text(value: str) -> str:
    return sys.stdin.read() if value == "-" else value


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="agent.py", description=__doc__.splitlines()[0])
    parser.add_argument("--session", default=os.environ.get("REX_SESSION", ""),
                        help="session ID (default: $REX_SESSION)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    p = sub.add_parser("get")
    p.add_argument("target")
    p = sub.add_parser("prompt")
    p.add_argument("target")
    p.add_argument("text", help="the task, or - to read it from stdin")
    p.add_argument("--timeout", type=float, default=180.0, help="seconds to wait for the turn (default 180)")
    p.add_argument("--activity-timeout", type=float, default=10.0,
                   help="seconds to see working or blocked after sending (default 10)")
    p.add_argument("--settle", choices=("status", "screen"), default="status",
                   help="screen: weaker screen-quiet wait for agents with no program status")
    p.add_argument("--quiet", type=float, default=5.0, help="with --settle screen: seconds of no change")
    p.add_argument("--raw", action="store_true", help="send the text exactly: no turn tag, no '!' check")
    p = sub.add_parser("wait")
    p.add_argument("target")
    p.add_argument("--until", choices=("settled", "blocked"), default="settled")
    p.add_argument("--timeout", type=float, default=180.0)
    p = sub.add_parser("read")
    p.add_argument("target")
    p.add_argument("--turn", default="", help="the turn ID a prompt printed: print the rows after its echo")
    p.add_argument("--after", default="", help="for an untagged task: its text or last line")
    p.add_argument("--lines", type=int, default=0, help="keep only the last N lines")
    p = sub.add_parser("fleet")
    p.add_argument("--window", default="", help="window ID (default: the window of $REX_BLOCK)")
    p.add_argument("--all", action="store_true", help="every window in the session")
    p.add_argument("--json", action="store_true")
    p.add_argument("--fail-on-blocked", action="store_true", help="exit 3 when any block but root is blocked")
    for name, helptext in (("broadcast", "one task to several targets"), ("dispatch", "a {name: task} JSON object")):
        p = sub.add_parser(name, help=helptext)
        if name == "broadcast":
            p.add_argument("text", help="the task, or - to read it from stdin")
            p.add_argument("targets", nargs="+")
        else:
            p.add_argument("file", help="JSON file mapping each target to its task, or - for stdin")
        p.add_argument("--timeout", type=float, default=180.0)
        p.add_argument("--activity-timeout", type=float, default=10.0)
        p.add_argument("--json", action="store_true", help="print one JSON result per target")
    args = parser.parse_args(argv)
    if not args.session:
        parser.error("--session is empty: run inside a Rex terminal, or pass the ID from 'rex whoami --json'")
    if args.cmd == "fleet" and not (args.window or args.all or os.environ.get("REX_BLOCK")):
        parser.error("fleet needs --window or --all outside a Rex terminal ($REX_BLOCK is unset)")
    try:
        if args.cmd == "check":
            print(json.dumps(check(args.session)))
            return 0
        if args.cmd == "get":
            agent = rexlib.inspect_agent(args.session, rexlib.resolve(args.session, args.target))
            print(json.dumps(agent))
            return 0
        if args.cmd == "prompt":
            res = do_prompt(args.session, args.target, read_text(args.text), args.timeout,
                            args.activity_timeout, args.settle, args.quiet, raw=args.raw)
            print(json.dumps(res))
            return EXIT.get(res["outcome"], 1)
        if args.cmd == "wait":
            res = do_wait(args.session, args.target, args.until, args.timeout)
            print(json.dumps(res))
            if args.until == "blocked" and res["outcome"] == "blocked":
                return 0
            return EXIT.get(res["outcome"], 1)
        if args.cmd == "read":
            code, text = do_read(args.session, args.target, args.turn, args.after, args.lines)
            print(text, file=sys.stderr if code else sys.stdout)
            return code
        if args.cmd == "fleet":
            window = args.window or rexlib.run_json(["block", "inspect", "-s", args.session,
                                                     os.environ.get("REX_BLOCK", ""), "--json"])["block"]["window_id"]
            rows = fleet(args.session, window, args.all)
            print(json.dumps(rows) if args.json else render(rows))
            blocked = any(r["status"] == "blocked" and r["role"] != "root" for r in rows)
            return EXIT["blocked"] if args.fail_on_blocked and blocked else 0
        if args.cmd == "broadcast":
            text = read_text(args.text)
            jobs = [(t, text) for t in args.targets]
        else:
            try:
                tasks = json.loads(read_text(args.file) if args.file == "-" else open(args.file).read())
            except (OSError, ValueError) as err:
                raise RexError(f"cannot read the dispatch file {args.file}: {err}. Pass a JSON object "
                               'such as {"reviewer": "review the diff", "tests": "run the suite"}.') from None
            if not isinstance(tasks, dict) or not all(isinstance(v, str) for v in tasks.values()):
                raise RexError(f"{args.file} must hold one JSON object mapping each target name to its task text.")
            jobs = list(tasks.items())
        results = fan_out(args.session, jobs, args.timeout, args.activity_timeout)
        for r in results:
            if args.json:
                print(json.dumps(r))
                continue
            line = f"{r['target']}: {r['outcome']}"
            if r.get("state"):
                line += f" ({r['state']})"
            if r.get("sent") and r.get("turn"):
                line += f" · turn {r['turn']}"
            if r.get("reason"):
                line += f" — {r['reason']}"
            print(line)
        return 0 if all(r["outcome"] == "settled" for r in results) else 1
    except RexError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
