#!/usr/bin/env python3
"""Drive agents in Herdr desktop app terminals: check, get, prompt, wait, read, fleet,
broadcast, dispatch, focus, close.

The app has no agent registry and no prompt-and-wait call, so this CLI adds both
on top of `hc` (herdr-core) and `herdr-app`. A worker's name is its
`hc-agent.name` label; hc itself never sees the name, only the terminal address
(t7), because hc resolves bare words against its own --name namespace. The
fleet is the set of terminals `herdr-app ls` shows in the root's tab. A
worker's state is the OSC 7501 status its CLI reports (`hc get` .status.state);
no status means unverifiable, never idle.

    check                           prerequisites: tools, this terminal, its pane and tab
    get TARGET                      classify one terminal (JSON)
    prompt TARGET TEXT|-            refuse unsafe targets, send TEXT, wait for the turn
    wait TARGET [--until blocked]   wait without sending
    read TARGET [--turn ID]         screen + history, or the lines after that turn's echo
    fleet [--json]                  every terminal in the root's tab, most urgent first
    broadcast TEXT TARGET...        one task to several targets, concurrently
    dispatch FILE|-                 a JSON object {name: task}, concurrently
    focus TARGET                    show that agent to the human (herdr-app agent.focus)
    close TARGET... --confirmed     close worker panes only (after the user confirmed)

Exit codes: 0 ok/settled · 1 error · 2 usage · 3 blocked · 4 unverifiable
· 5 no agent · 6 working (refused) · 7 stalled · 8 timeout · 9 exited
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import hclib
from hclib import EXIT, HC, LABEL, HcError

REFUSE = {"working": "working", "blocked": "blocked", "unverified": "unverifiable",
          "no-agent": "no_agent", "exited": "exited"}
ROLE_ORDER = {"worker": 0, "main": 1, "other": 2, "root": 3}


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


def check() -> dict:
    missing = [tool for tool in (HC, hclib.APP) if not shutil.which(tool)]
    if missing:
        raise HcError(f"{' and '.join(missing)} not on PATH. Install the Herdr desktop app (it ships hc "
                      "and herdr-app, normally in ~/.local/bin) and run this inside one of its terminals.")
    root = hclib.resolve_root()
    status, kind = hclib.classify(root.rec)
    fg_pid = (root.rec.get("foreground") or {}).get("pid")
    confirmed = None
    if fg_pid:
        confirmed = fg_pid in ancestors()
        if not confirmed:
            print(f"warning: terminal {root.addr}'s foreground process ({fg_pid}) is not an ancestor of this "
                  "command, so HC_TERMINAL_ID may be inherited from another terminal. Confirm with the user "
                  "before treating it as root.", file=sys.stderr)
    return {"terminal": root.addr, "pane": root.pane, "space": root.space, "tab": root.tab,
            "cwd": (root.rec.get("foreground") or {}).get("cwd") or root.rec.get("cwd") or os.getcwd(),
            "kind": kind, "status": status, "tab_terminals": len(root.tab_terminals),
            "terminal_confirmed": confirmed}


def resolve(root: hclib.Root, target: str, members: dict[str, str] | None = None) -> tuple[str, str]:
    """(address, pane) of one terminal in the root's tab: an exact name label or a t… address."""
    members = root.panes() if members is None else members
    found = {target} if hclib.ADDRESS_RE.match(target) and target in members else set()
    if hclib.NAME_RE.match(target):
        rows = hclib.ls_labeled(f"{LABEL}.name={target}", f"{LABEL}.tab={root.tab}")
        found |= {r.get("address") for r in rows if r.get("address") in members}
    if not found:
        raise HcError(f"no terminal named or addressed '{target}' in the root's tab ({root.tab}). List the "
                      "fleet with 'agent.py fleet'; this skill only drives its own tab.")
    if len(found) > 1:
        raise HcError(f"'{target}' names {len(found)} terminals ({', '.join(sorted(found))}). Pass a t… address.")
    addr = found.pop()
    return addr, members[addr]


def not_root(root: hclib.Root, addr: str, target: str) -> None:
    if addr == root.addr:
        raise HcError(f"'{target}' is your own terminal ({addr}); never prompt, steer or close the "
                      "orchestrator's own pane.")


def wait_turn(addr: str, base_turn, base_ms, activity_timeout: float, timeout: float,
              until: str = "settled", active: bool = False) -> tuple[str, dict]:
    """Wait for the turn after a baseline. Returns (outcome, last record).

    A turn needs activity: a status newer than the baseline (`status_ms` or
    `turn` changed). `working` marks it active; a newer `done` or `error`, or
    `idle` once working was seen or the turn counter moved, settles it. `blocked`
    ends it at once, a vanished status mid-turn is unverifiable, and a finished
    terminal is exited. While working, `hc wait` blocks instead of polling.
    """
    start = time.monotonic()
    rec: dict = {}
    while True:
        rec = hclib.get(addr)
        status, _ = hclib.classify(rec)
        newer = rec.get("status_ms") != base_ms or rec.get("turn") != base_turn
        moved = rec.get("turn") != base_turn
        if status == "exited":
            return "exited", rec
        if status == "blocked" and (newer or until == "blocked"):
            return "blocked", rec
        if status == "working":
            active = True
        elif until == "settled" and status in ("done", "error") and newer:
            return "settled", rec
        elif until == "settled" and status == "idle" and (active or moved):
            return "settled", rec
        elif status in ("unverified", "no-agent") and (active or newer):
            return "unverifiable", rec
        elapsed = time.monotonic() - start
        if elapsed > timeout:
            return "timeout", rec
        if not active and not newer and elapsed > activity_timeout:
            return "stalled", rec
        if active:
            left = max(1, int(min(timeout - elapsed, 30)))
            hclib.run(HC, ["wait", addr, "--timeout", str(left), "--json"], timeout=left + 15, check=False)
        else:
            time.sleep(0.25)


def do_prompt(root: hclib.Root, target: str, text: str, timeout: float, activity_timeout: float,
              members: dict[str, str] | None = None, raw: bool = False) -> dict:
    clean = hclib.sanitize(text).strip("\n")
    if not raw and clean.lstrip().startswith("!"):
        raise HcError("the task starts with '!', which Claude Code runs as a shell command instead of a "
                      "prompt. Reword it, or pass --raw to send the text exactly as given.")
    if not clean.strip():
        raise HcError("the prompt is empty after removing control characters; pass the task text.")
    addr, pane = resolve(root, target, members)
    not_root(root, addr, target)
    rec = hclib.get(addr)
    status, kind = hclib.classify(rec)
    turn = "" if raw else secrets.token_hex(3)
    result = {"target": target, "terminal": addr, "pane": pane, "kind": kind, "status": status,
              "sent": False, "turn": turn}
    if status not in hclib.READY:
        return {**result, "outcome": REFUSE.get(status, "unverifiable")}
    payload = clean + (f"\n\n(hc-agent turn {turn})" if turn else "")
    args = ["send", "--json", *(["--if", "idle"] if status == "idle" else []), "--", addr, payload]
    started = time.monotonic()
    try:
        hclib.run(HC, args, timeout=90)
    except HcError as err:
        if err.kind in ("status_mismatch", "blocked", "finished"):
            now, _ = hclib.classify(hclib.get(addr))
            outcome = {"blocked": "blocked", "finished": "exited"}.get(err.kind) or REFUSE.get(now, "unverifiable")
            return {**result, "status": now, "outcome": outcome, "reason": str(err)}
        raise
    result["sent"] = True
    outcome, last = wait_turn(addr, rec.get("turn"), rec.get("status_ms"), activity_timeout, timeout)
    st = last.get("status") if isinstance(last.get("status"), dict) else {}
    return {**result, "outcome": outcome, "state": (st or {}).get("state"), "msg": (st or {}).get("msg"),
            "waited_s": round(time.monotonic() - started, 1)}


def do_wait(root: hclib.Root, target: str, until: str, timeout: float) -> dict:
    addr, pane = resolve(root, target)
    not_root(root, addr, target)
    rec = hclib.get(addr)
    status, kind = hclib.classify(rec)
    result = {"target": target, "terminal": addr, "pane": pane, "kind": kind}
    if status in ("unverified", "no-agent", "exited"):
        return {**result, "outcome": REFUSE[status], "state": status}
    if status == "blocked" or (until == "settled" and status in hclib.READY):
        return {**result, "outcome": "blocked" if status == "blocked" else "settled", "state": status}
    outcome, last = wait_turn(addr, rec.get("turn"), rec.get("status_ms"), timeout, timeout, until=until,
                              active=status == "working")
    return {**result, "outcome": outcome, "state": ((last.get("status") or {}) if isinstance(
        last.get("status"), dict) else {}).get("state")}


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


def do_read(root: hclib.Root, target: str, turn: str, after: str, lines: int, tail: int) -> tuple[int, str]:
    """Screen plus `lines` of history, or only the lines after one turn's echo.

    --turn anchors on the unique tag `prompt` appended, so a reply that repeats the
    task cannot move the anchor. --after anchors on the last 24 non-space characters
    of a task sent without a tag. Exit 4: the anchor is not in the text read.
    """
    addr, _ = resolve(root, target)
    if (turn or after) and not lines:
        lines = 400
    rows = hclib.read_screen(addr, lines).rstrip("\n").split("\n")
    while rows and not rows[-1].strip():
        rows.pop()
    if turn or after:
        if turn:
            index, what = locate(rows, f"(hc-agentturn{turn})", last=False), f"turn {turn}'s tag"
        else:
            index, what = locate(rows, "".join(hclib.sanitize(after).split())[-24:], last=True), "the task's end"
        if index is None:
            return EXIT["unverifiable"], (f"{what} is not in the last {lines} history lines of {target}. Raise "
                                          "--lines, or use the file fallback in references/delivery-and-waiting.md.")
        rows = rows[index + 1:]
    rows = [row for i, row in enumerate(rows) if row.strip() or (i and rows[i - 1].strip())]
    return 0, "\n".join(rows[-tail:] if tail else rows).strip("\n")


def fleet(root: hclib.Root) -> list[dict]:
    """Every terminal in the root's tab, with role root, worker, main (a HANDOFF successor) or other."""
    rows = []
    for term in root.tab_terminals:
        addr = term.get("terminal")
        if not addr:
            continue
        try:
            row = hclib.describe(addr, hclib.get(addr), term.get("pane") or "")
        except HcError as err:
            row = {"name": "", "terminal": addr, "pane": term.get("pane") or "", "kind": "",
                   "status": "unknown", "msg": str(err), "role_label": ""}
        if addr == root.addr:
            row["role"] = "root"
        else:
            row["role"] = row["role_label"] if row["role_label"] in ("worker", "main") else "other"
        rows.append(row)
    rank = {s: i for i, s in enumerate(hclib.ATTENTION)}
    return sorted(rows, key=lambda r: (ROLE_ORDER[r["role"]], rank.get(r["status"], 99), r["name"]))


def render(rows: list[dict]) -> str:
    out = []
    for r in rows:
        role = "" if r["role"] == "worker" else f"  ({r['role']})"
        note = r.get("msg") or ""
        out.append(f"{r['status']:<11} {r['name'] or '-':<16} {r['kind'] or '-':<8} {r['terminal']:<8} "
                   f"{r['pane']}{role}{'  · ' + note[:70] if note else ''}")
    counts: dict[str, int] = {}
    for r in rows:
        if r["role"] == "worker":
            counts[r["status"]] = counts.get(r["status"], 0) + 1
    order = {s: i for i, s in enumerate(hclib.ATTENTION)}
    tally = ", ".join(f"{n} {s}" for s, n in sorted(counts.items(), key=lambda kv: order.get(kv[0], 99)))
    others = sum(1 for r in rows if r["role"] in ("other", "main"))
    out.append(f"Fleet: {sum(counts.values())} worker(s){': ' + tally if tally else ''}"
               f"{f' · {others} other terminal(s)' if others else ''} · polled {time.strftime('%H:%M:%S')}")
    return "\n".join(out)


def fan_out(root: hclib.Root, jobs: list[tuple[str, str]], timeout: float, activity_timeout: float) -> list[dict]:
    """Prompt each (target, task) pair concurrently; one listing resolves every target."""
    members = root.panes()
    seen, todo, results = set(), [], []
    for target, task in jobs:
        try:
            addr, _ = resolve(root, target, members)
            not_root(root, addr, target)
        except HcError as err:
            results.append({"target": target, "outcome": "error", "reason": str(err)})
            continue
        if addr in seen:
            continue
        seen.add(addr)
        todo.append((target, task))
    with ThreadPoolExecutor(max_workers=max(1, len(todo))) as pool:
        futures = {t: pool.submit(do_prompt, root, t, task, timeout, activity_timeout, members)
                   for t, task in todo}
        for target, fut in futures.items():
            try:
                results.append(fut.result())
            except HcError as err:
                results.append({"target": target, "outcome": "error", "reason": str(err)})
    return results


def do_focus(root: hclib.Root, target: str) -> dict:
    addr, pane = resolve(root, target)
    try:
        hclib.app_do("agent.focus", terminal=addr)
        how = "agent.focus"
    except HcError:
        hclib.app_do("pane.focus", pane=pane)
        how = "pane.focus"
    return {"target": target, "terminal": addr, "pane": pane, "focused_with": how}


def do_close(root: hclib.Root, targets: list[str]) -> list[dict]:
    """Close worker panes only: labeled hc-agent.role=worker and listed in the root's tab."""
    members, results = root.panes(), []
    for target in targets:
        try:
            addr, pane = resolve(root, target, members)
            not_root(root, addr, target)
            role = hclib.labels(hclib.get(addr)).get(f"{LABEL}.role")
            if role != "worker":
                raise HcError(f"'{target}' ({addr}) is not an hc-agent worker (role {role or 'none'}); "
                              "close it only if the user names that pane, with herdr-app do pane.close.")
            hclib.app_do("pane.close", pane=pane)
            results.append({"target": target, "terminal": addr, "pane": pane, "outcome": "closed"})
        except HcError as err:
            results.append({"target": target, "outcome": "refused", "reason": str(err)})
    return results


def read_text(value: str) -> str:
    return sys.stdin.read() if value == "-" else value


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="agent.py", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    p = sub.add_parser("get")
    p.add_argument("target")
    p = sub.add_parser("prompt")
    p.add_argument("target")
    p.add_argument("text", help="the task, or - to read it from stdin")
    p.add_argument("--timeout", type=float, default=180.0, help="seconds to wait for the turn (default 180)")
    p.add_argument("--activity-timeout", type=float, default=15.0,
                   help="seconds to see a newer status after sending (default 15)")
    p.add_argument("--raw", action="store_true", help="send the text exactly: no turn tag, no '!' check")
    p = sub.add_parser("wait")
    p.add_argument("target")
    p.add_argument("--until", choices=("settled", "blocked"), default="settled")
    p.add_argument("--timeout", type=float, default=180.0)
    p = sub.add_parser("read")
    p.add_argument("target")
    p.add_argument("--turn", default="", help="the turn ID a prompt printed: print the lines after its echo")
    p.add_argument("--after", default="", help="for an untagged task: its text or last line")
    p.add_argument("--lines", type=int, default=0, help="history lines above the screen (default 0; 400 with --turn)")
    p.add_argument("--tail", type=int, default=0, help="keep only the last N lines")
    p = sub.add_parser("fleet")
    p.add_argument("--json", action="store_true")
    p.add_argument("--fail-on-blocked", action="store_true", help="exit 3 when any terminal but root is blocked")
    for name, helptext in (("broadcast", "one task to several targets"), ("dispatch", "a {name: task} JSON object")):
        p = sub.add_parser(name, help=helptext)
        if name == "broadcast":
            p.add_argument("text", help="the task, or - to read it from stdin")
            p.add_argument("targets", nargs="+")
        else:
            p.add_argument("file", help="JSON file mapping each target to its task, or - for stdin")
        p.add_argument("--timeout", type=float, default=180.0)
        p.add_argument("--activity-timeout", type=float, default=15.0)
        p.add_argument("--json", action="store_true", help="print one JSON result per target")
    p = sub.add_parser("focus")
    p.add_argument("target")
    p = sub.add_parser("close")
    p.add_argument("targets", nargs="+")
    p.add_argument("--confirmed", action="store_true", help="the user explicitly confirmed this teardown")
    args = parser.parse_args(argv)
    if args.cmd == "close" and not args.confirmed:
        parser.error("close needs --confirmed: ask the user first, and close nothing if they decline")
    try:
        if args.cmd == "check":
            print(json.dumps(check()))
            return 0
        root = hclib.resolve_root()
        if args.cmd == "get":
            addr, pane = resolve(root, args.target)
            print(json.dumps(hclib.describe(addr, hclib.get(addr), pane)))
            return 0
        if args.cmd == "prompt":
            res = do_prompt(root, args.target, read_text(args.text), args.timeout, args.activity_timeout,
                            raw=args.raw)
            print(json.dumps(res))
            return EXIT.get(res["outcome"], 1)
        if args.cmd == "wait":
            res = do_wait(root, args.target, args.until, args.timeout)
            print(json.dumps(res))
            if args.until == "blocked" and res["outcome"] == "blocked":
                return 0
            return EXIT.get(res["outcome"], 1)
        if args.cmd == "read":
            code, text = do_read(root, args.target, args.turn, args.after, args.lines, args.tail)
            print(text, file=sys.stderr if code else sys.stdout)
            return code
        if args.cmd == "fleet":
            rows = fleet(root)
            print(json.dumps(rows) if args.json else render(rows))
            blocked = any(r["status"] == "blocked" and r["role"] != "root" for r in rows)
            return EXIT["blocked"] if args.fail_on_blocked and blocked else 0
        if args.cmd == "focus":
            print(json.dumps(do_focus(root, args.target)))
            return 0
        if args.cmd == "close":
            results = do_close(root, args.targets)
            for r in results:
                print(json.dumps(r))
            return 0 if all(r["outcome"] == "closed" for r in results) else 1
        if args.cmd == "broadcast":
            text = read_text(args.text)
            jobs = [(t, text) for t in args.targets]
        else:
            try:
                tasks = json.loads(read_text(args.file) if args.file == "-" else open(args.file).read())
            except (OSError, ValueError) as err:
                raise HcError(f"cannot read the dispatch file {args.file}: {err}. Pass a JSON object "
                              'such as {"reviewer": "review the diff", "tests": "run the suite"}.') from None
            if not isinstance(tasks, dict) or not all(isinstance(v, str) for v in tasks.values()):
                raise HcError(f"{args.file} must hold one JSON object mapping each target name to its task text.")
            jobs = list(tasks.items())
        results = fan_out(root, jobs, args.timeout, args.activity_timeout)
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
    except HcError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
