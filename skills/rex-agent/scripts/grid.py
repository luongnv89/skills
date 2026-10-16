#!/usr/bin/env python3
"""Plan the next column split, and equalize the root window's columns exactly.

Rex lays out a window as a binary tree of splits. session.resize_pane sets one
split's ratio exactly: the share of its `before` side. In a row of N columns,
each horizontal split gets leaves(before) / leaves(split), so every column
lands on 1/N of the window in one pass, with no iterative convergence.

The fleet layout is one row: every split in the root window's tiled layer must
be horizontal. A pane stacked above or below another is refused, so the caller
asks the user instead of reshaping their layout.

Usage:
    grid.py plan     [--session S] [--root-block B]   # rightmost column's block ID
    grid.py equalize [--session S] [--root-block B]   # set every ratio, then verify

Exit codes: 0 ok · 1 error (not one row, resize failed, widths unequal) · 2 usage
"""

from __future__ import annotations

import argparse
import os
import sys

import rexlib
from rexlib import RexError

TOLERANCE = 0.002  # fraction of the window width, about a cell on a wide window


def tiled_layout(view: dict, block: str) -> tuple[dict, dict]:
    for win in view.get("windows") or []:
        for layer in win.get("layers") or []:
            if layer.get("kind") != "tiled":
                continue
            if any(b.get("block_id") == block for b in layer.get("blocks") or []):
                return win, layer.get("layout") or {}
    raise RexError(f"block {block} is not in a tiled layer of session {view.get('session_id')}: "
                   "it may be floating or detached. Pass the orchestrator's own block with "
                   "--root-block.")


def leaves(node: dict) -> list[dict]:
    split = node.get("split")
    if split:
        return leaves(split["before"]) + leaves(split["after"])
    return [node]


def splits(node: dict):
    split = node.get("split")
    if split:
        yield split
        yield from splits(split["before"])
        yield from splits(split["after"])


def columns(session: str, root: str) -> tuple[dict, dict, list[dict]]:
    win, layout = tiled_layout(rexlib.session_view(session), root)
    for split in splits(layout):
        if split.get("direction") != "horizontal":
            raise RexError("the root window is not a single row of columns: a pane is stacked "
                           "above or below another. Ask the user before adding workers. They "
                           "can close or move that pane, or choose one tab per worker "
                           "(launch_profile.py --new-window).")
    return win, layout, sorted(leaves(layout), key=lambda n: n["rect"][0])


def plan(session: str, root: str) -> tuple[str, int]:
    _, _, cols = columns(session, root)
    return cols[-1]["block_id"], len(cols)


def equalize(session: str, root: str) -> list[float]:
    _, layout, _ = columns(session, root)
    for split in splits(layout):
        before, after = leaves(split["before"]), leaves(split["after"])
        ratio = len(before) / (len(before) + len(after))
        if abs((split.get("ratio") or 0) - ratio) < 1e-6:
            continue
        rexlib.api_call(session, "session.resize_pane", {
            "direction": "horizontal",
            "before_block_id": max(before, key=lambda n: n["rect"][0])["block_id"],
            "after_block_id": min(after, key=lambda n: n["rect"][0])["block_id"],
            "ratio": ratio,
        })
    _, _, cols = columns(session, root)
    widths = [c["rect"][2] for c in cols]
    if max(widths) - min(widths) > TOLERANCE:
        shown = " ".join(f"{w:.1%}" for w in widths)
        raise RexError(f"columns are still unequal after resizing ({shown}). Read the layout "
                       f"with 'rex session inspect {session} --json' before adding workers.")
    return widths


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="grid.py", description=__doc__.splitlines()[0])
    parser.add_argument("action", choices=("plan", "equalize"))
    parser.add_argument("--session", default=os.environ.get("REX_SESSION", ""),
                        help="session ID (default: $REX_SESSION)")
    parser.add_argument("--root-block", default=os.environ.get("REX_BLOCK", ""),
                        help="the orchestrator's block (default: $REX_BLOCK)")
    args = parser.parse_args(argv)
    if not args.session or not args.root_block:
        parser.error("--session and --root-block are empty: run inside a Rex terminal, or pass "
                     "the IDs from 'rex whoami --json'")
    try:
        if args.action == "plan":
            anchor, count = plan(args.session, args.root_block)
            print(anchor)
            print(f"{count} column(s); split from the rightmost, {anchor}", file=sys.stderr)
        else:
            widths = equalize(args.session, args.root_block)
            print(f"Columns: {len(widths)} · widths " + " ".join(f"{w:.1%}" for w in widths))
    except RexError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
