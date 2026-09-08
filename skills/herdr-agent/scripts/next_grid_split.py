#!/usr/bin/env python3
"""Plan (and optionally drive) an equal-width column grid in a Herdr tab.

All panes in the tab (root + every sub-agent) are kept as equal-width
columns side by side, left to right. This models the *real* Herdr 0.7.4
`pane split` / `pane resize` semantics, verified live against a running
herdr server (see SKILL.md "Equal-width columns — verified semantics"):

  * `herdr pane split <pane> --direction right --ratio R`
        R is the fraction the EXISTING (first/left) child keeps of the
        pane being split; the new pane gets (1 - R). It only resizes the
        pane you split — the other columns are untouched. So a single
        split can NEVER equalize N >= 3 columns on its own.

  * `herdr pane resize --pane P --direction D --amount A`
        A is a DELTA expressed as a fraction of the whole tab area width
        (A * area_width cells), NOT an absolute target width. `--direction`
        moves the edge on side D: for a pane that has a neighbor on side D
        it GROWS toward that neighbor; against a wall it shrinks. The freed
        or absorbed cells redistribute *proportionally* among the panes on
        the other side of the moved boundary. Because that redistribution
        perturbs columns you already placed, a single left-to-right sweep
        does not land equal — but the sweep is a contraction: iterating it
        converges to equal width within ~1 cell in a handful of passes
        (verified: spread 25 -> 13 -> 5 -> 3 -> 1 for a 4-column decay).

So the reliable strategy this script encodes is:

  1. Add column N by splitting the current rightmost column `right` with
     `--ratio 1/N`. `--ratio R` is the fraction the EXISTING (left) child of
     the split column keeps, so the NEW (right) pane gets `1 - R = (N-1)/N`
     of that column — which, since the rightmost column is `1/(N-1)` of the
     tab when the N-1 existing columns are equal, equals `1/N` of the whole
     tab (the equal target). See `split_ratio()` for the derivation.
  2. Run an iterative boundary equalizer: sweep internal boundaries left
     to right, moving each toward its target cumulative position by GROWING
     the neighbor-bearing pane; repeat until the width spread is <= 1 cell
     (or a small iteration cap). Each pass re-reads the live layout. A resize
     command failure or non-convergence is a HARD error (exit 1), never
     suppressed — the caller must not launch workers into an unequal layout.

Usage:
    # plan the split for the next column (default)
    python3 next_grid_split.py [--root-pane PANE_ID] [--layout-json PATH|-]

    # run the live iterative equalizer over the current tab
    python3 next_grid_split.py --equalize [--root-pane PANE_ID]

Default output (one split line a caller feeds to `herdr pane split`):

    split <rightmost_pane_id> right --ratio <1/N>

where N is the column count AFTER the split. Follow it with `--equalize`
(see SKILL.md Phase 2a).

Exit codes:
    0 success
    1 usage / environment / parse error
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys

# Equal within this many cells is "done" — herdr rounds column widths to
# whole terminal cells, so exact equality is impossible when area_width is
# not divisible by the column count.
EQUAL_TOLERANCE_CELLS = 1
# Safety cap so a pathological layout can't loop forever. The sweep is a
# contraction; real layouts converge in ~5 passes.
MAX_EQUALIZE_PASSES = 12


def _finite_float(value: object, label: str, *, positive: bool = False) -> float:
    """Convert `value` to a float that is guaranteed FINITE (and, for
    dimensions, strictly positive).

    Every geometry coordinate/dimension routes through here. `json.loads`
    accepts `NaN`/`Infinity` by default, and a non-finite value silently defeats
    every downstream comparison: `nan <= 0`, `nan > tol`, `abs(nan - x) > tol`
    are all False, so a NaN width/coord would sail past the positive-width and
    single-row checks and drive a bogus resize. Reject it here instead.

    `positive=True` for dimensions (width/height); coordinates (x/y) may be 0
    or negative, they just must be finite.
    """
    try:
        f = float(value)
    except (TypeError, ValueError) as e:
        raise SystemExit(f"{label} is not numeric: {value!r}") from e
    if not math.isfinite(f):
        raise SystemExit(f"{label} is not finite: {value!r}")
    if positive and f <= 0:
        raise SystemExit(f"{label} must be positive: {f:g}")
    return f


def load_layout(root_pane: str | None, layout_json: str | None) -> dict:
    if layout_json == "-":
        return json.load(sys.stdin)
    if layout_json:
        with open(layout_json, encoding="utf-8") as f:
            return json.load(f)

    if not shutil.which("herdr"):
        raise SystemExit("herdr not on PATH")

    cmd = ["herdr", "pane", "layout"]
    if root_pane:
        cmd.extend(["--pane", root_pane])
    else:
        cmd.append("--current")
    cp = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if cp.returncode != 0:
        raise SystemExit(cp.stderr.strip() or cp.stdout.strip() or "herdr pane layout failed")
    return json.loads(cp.stdout)


def _unwrap_layout(data: dict) -> dict:
    """Return the inner `layout` object regardless of whether `data` is the
    raw CLI envelope (`{"result": {"layout": {...}}}`), a `{"layout": {...}}`
    fixture, or the layout dict itself."""
    # A top-level `null` (or any non-object) parses to a non-dict here; calling
    # .get() on it would raise an uncaught AttributeError. Reject cleanly.
    if not isinstance(data, dict):
        raise SystemExit("layout JSON is not an object")
    node = data.get("result", data)
    if isinstance(node, dict) and "layout" in node:
        node = node["layout"]
    if not isinstance(node, dict):
        raise SystemExit("layout JSON is not an object")
    return node


def panes_from_layout(data: dict) -> list[dict]:
    layout = _unwrap_layout(data)
    panes = layout.get("panes")
    if not isinstance(panes, list) or not panes:
        raise SystemExit("layout JSON has no panes")
    # A null / non-object element (e.g. `panes: [null]`) would crash every
    # `pane.get(...)` downstream with an uncaught AttributeError. Validate the
    # element shape here, once, so callers get a clean SystemExit instead.
    for i, pane in enumerate(panes):
        if not isinstance(pane, dict):
            raise SystemExit(f"layout JSON pane #{i} is not an object")
    return panes


def area_width_from_layout(data: dict) -> float:
    layout = _unwrap_layout(data)
    area = layout.get("area") or {}
    raw = area.get("width", 0)
    # A PRESENT area width must be finite: NaN/inf would defeat the `<= 0`
    # fallback trigger AND the `<= 0` error below, returning a poisoned width.
    # (An absent width reads 0 → finite → falls through to the summed-pane
    # fallback, which is unchanged.)
    width = _finite_float(raw, "area width")
    if width <= 0:
        # Fall back to the summed pane widths so fixtures without an explicit
        # area still work.
        width = sum(_ordered_columns(panes_from_layout(data))[1])
    if width <= 0:
        raise SystemExit("layout JSON has no usable area width")
    return width


def validate_single_row(data: dict, tolerance: int = 1) -> None:
    """Reject layouts this script cannot safely treat as a row of columns.

    The split/equalize model assumes every pane is a full-height column
    tiling the tab left to right. A 2D layout (vertically stacked panes, or a
    partial-height pane) breaks that: panes sharing an `x` would be counted as
    separate columns, inflating the column total and making the "rightmost
    column" split target ambiguous. This validates x/y/width/height BEFORE any
    mutation and raises SystemExit on anything that isn't a single clean row.

    Requires a real `area` rect (the summed-width fallback in
    `area_width_from_layout` is unsafe here — stacked panes double-count).
    """
    layout = _unwrap_layout(data)
    area = layout.get("area")
    if not isinstance(area, dict):
        raise SystemExit(
            "layout has no 'area' rect; cannot validate a single-row column "
            "grid (refusing to split/equalize a layout of unknown shape)"
        )
    for k in ("x", "y", "width", "height"):
        if k not in area:
            raise SystemExit(f"layout 'area' rect missing {k}")
    ax = _finite_float(area["x"], "area x"); ay = _finite_float(area["y"], "area y")
    aw = _finite_float(area["width"], "area width", positive=True)
    ah = _finite_float(area["height"], "area height", positive=True)

    panes = panes_from_layout(data)
    # Reject missing / non-string / empty / duplicate pane ids up front — a
    # malformed id here would otherwise flow into the split planner and mis-
    # target a column (see _validate_pane_ids).
    _validate_pane_ids(panes)
    rects: list[tuple[float, float, float, float, str]] = []
    for pane in panes:
        pid = pane["pane_id"]  # validated: unique non-empty str
        rect = pane.get("rect")
        if not isinstance(rect, dict):
            raise SystemExit(f"pane {pid!r} has no rect; cannot validate layout shape")
        for k in ("x", "y", "width", "height"):
            if k not in rect:
                raise SystemExit(f"pane {pid!r} rect missing {k}")
        x = _finite_float(rect["x"], f"pane {pid!r} x"); y = _finite_float(rect["y"], f"pane {pid!r} y")
        w = _finite_float(rect["width"], f"pane {pid!r} width", positive=True)
        h = _finite_float(rect["height"], f"pane {pid!r} height", positive=True)
        rects.append((x, y, w, h, str(pid)))

    # Every pane must be a full-height column, top-aligned with the area.
    for x, y, w, h, pid in rects:
        if abs(y - ay) > tolerance or abs(h - ah) > tolerance:
            raise SystemExit(
                f"pane {pid} is not a full-height column (y={y:g} h={h:g} vs "
                f"area y={ay:g} h={ah:g}): this looks like a 2D / stacked "
                f"layout, which this skill does not support. Rearrange to a "
                f"single row of columns (or spawn agents in separate tabs)."
            )

    # Columns must tile left-to-right with no overlaps or gaps.
    rects.sort(key=lambda t: t[0])
    cursor = ax
    for x, _y, w, _h, pid in rects:
        if abs(x - cursor) > tolerance:
            raise SystemExit(
                f"column {pid} starts at x={x:g}, expected {cursor:g} — panes "
                f"overlap or leave a gap; not a clean single row. Refusing to "
                f"split/equalize."
            )
        cursor += w
    if abs(cursor - (ax + aw)) > tolerance:
        raise SystemExit(
            f"columns span to x={cursor:g} but area ends at {ax + aw:g}; the "
            f"row does not fill the tab width. Refusing to split/equalize."
        )


def _validate_pane_ids(panes: list[dict]) -> None:
    """Require every pane to carry a unique, non-empty STRING pane_id.

    Runs as a first pass over the FULL input list, before any rect-based drop.
    A pane with a missing / non-string / empty / duplicate id is a layout we
    cannot safely plan against: `_ordered_columns` used to *silently drop* such
    panes, so a malformed rightmost column would vanish and the planner would
    split the WRONG pane. Reject up front instead of dropping. Also rejects a
    non-object element (e.g. `panes: [null]`) rather than crashing on `.get`.
    """
    seen_ids: set[str] = set()
    for i, pane in enumerate(panes):
        if not isinstance(pane, dict):
            raise SystemExit(f"layout pane #{i} is not an object")
        pane_id = pane.get("pane_id")
        if not isinstance(pane_id, str) or not pane_id:
            raise SystemExit(f"pane #{i} has a missing / non-string / empty pane_id: {pane_id!r}")
        if pane_id in seen_ids:
            raise SystemExit(f"duplicate pane_id {pane_id!r} in layout")
        seen_ids.add(pane_id)


def _ordered_columns(panes: list[dict]) -> tuple[list[str], list[float]]:
    """Order panes by rect.x and return parallel (ids, widths) lists.

    EVERY pane must carry a valid geometry: a `rect` object with a numeric `x`
    and a strictly-positive numeric `width`. A pane that fails this is a HARD
    error, never a silent drop — dropping one during a live equalize re-read
    would compute resize ops for a PARTIAL grid (a column omitted), scrambling
    the layout. Defaulting a missing `x` to 0 (the old behaviour) also misorders
    columns. Pane ids are validated first via `_validate_pane_ids`.
    """
    _validate_pane_ids(panes)
    ordered: list[tuple[float, str, float]] = []
    for pane in panes:
        pane_id = pane["pane_id"]  # validated above: a non-empty unique str
        rect = pane.get("rect")
        if not isinstance(rect, dict):
            raise SystemExit(f"pane {pane_id!r} has no rect object; cannot order columns")
        if "x" not in rect or "width" not in rect:
            raise SystemExit(f"pane {pane_id!r} rect is missing x/width")
        # _finite_float rejects NaN/inf (which would defeat the width>0 check and
        # the ordering sort) and, with positive=True, non-positive width.
        x = _finite_float(rect["x"], f"pane {pane_id!r} x")
        width = _finite_float(rect["width"], f"pane {pane_id!r} width", positive=True)
        ordered.append((x, pane_id, width))
    if not ordered:
        raise SystemExit("no usable pane rects in layout")
    ordered.sort(key=lambda t: t[0])
    return [pid for _, pid, _ in ordered], [w for _, _, w in ordered]


def _pane_ids_left_to_right(panes: list[dict]) -> list[str]:
    return _ordered_columns(panes)[0]


def equal_targets(n: int, area_width: float) -> list[int]:
    """Equal-width integer column targets summing to `area_width`.

    Splits the +/-1 rounding remainder onto the leftmost columns, matching
    how herdr distributes cells that don't divide evenly.
    """
    if n <= 0:
        raise SystemExit("column count must be positive")
    total = int(round(area_width))
    base = total // n
    rem = total - base * n
    return [base + (1 if i < rem else 0) for i in range(n)]


def boundary_resize_op(
    ids: list[str],
    widths: list[float],
    targets: list[int],
    area_width: float,
    boundary: int,
) -> tuple[str, str, float] | None:
    """Compute the single resize op that moves internal `boundary`
    (between column `boundary` and `boundary+1`) toward its target
    cumulative position, always by GROWING the neighbor-bearing pane.

    Returns `(pane_id, direction, amount)` or None if already on target.
    `amount` is a fraction of `area_width` (the herdr `--amount` unit).

    * boundary must move RIGHT  -> grow left column: resize ids[boundary] right
    * boundary must move LEFT   -> grow right column: resize ids[boundary+1] left
    """
    target_cum = sum(targets[: boundary + 1])
    cur_cum = sum(widths[: boundary + 1])
    delta = target_cum - cur_cum  # >0: boundary too far left, must move right
    if abs(delta) < 1:  # sub-cell; nothing herdr can act on
        return None
    amount = abs(delta) / area_width
    if delta > 0:
        return (ids[boundary], "right", amount)
    return (ids[boundary + 1], "left", amount)


def require_root_membership(ids: list[str], root_pane: str | None) -> None:
    """Fail HARD if a requested root pane isn't part of the layout.

    If the caller named a `root_pane` but it isn't among the ordered column
    ids, the layout we're about to split/equalize is NOT the root's tab — so
    the "rightmost column" target and the whole equal-width plan would apply
    to the wrong tab. That must abort before any mutation, not warn and
    proceed. `root_pane is None` means "no specific root requested" and is
    fine (plan from whatever layout was supplied).
    """
    if root_pane and root_pane not in ids:
        raise SystemExit(
            f"requested root pane {root_pane!r} is not in this layout "
            f"(columns: {ids}); refusing to split/equalize the wrong tab"
        )


def plan_next_split(panes: list[dict], root_pane: str | None) -> tuple[str, int]:
    """Return `(rightmost_pane_id, new_column_count)` for adding a column."""
    ordered = _pane_ids_left_to_right(panes)
    require_root_membership(ordered, root_pane)
    return ordered[-1], len(ordered) + 1


def split_ratio(new_count: int) -> float:
    """`--ratio` for `herdr pane split` when adding column `new_count` (= N).

    In herdr 0.7.4 `--ratio R` is the fraction the EXISTING (left) child of
    the split pane keeps; the NEW (right) pane gets `1 - R` of that pane. We
    split the current rightmost column, which — when the N-1 existing columns
    are already equal — is `1/(N-1)` of the whole tab. To make the new pane
    the equal target `1/N` of the tab, it must take `((1/N)/(1/(N-1))) =
    (N-1)/N` of the split column, so the existing child keeps `R = 1/N`.

    Verified live against herdr 0.7.4: from two equal 105/105 columns,
    splitting the rightmost with `--ratio 0.333` (=1/3) yields a new pane of
    width 70 (= 210/3, the equal target). See SKILL.md / herdr-recipes.md.
    """
    if new_count < 2:
        raise SystemExit("new column count must be >= 2 to split")
    return 1.0 / new_count


def _run_herdr(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["herdr", *args], text=True, capture_output=True, check=False)


def validate_live_layout(data: dict, root_pane: str | None) -> tuple[list[str], list[float]]:
    """FULL validation of one live layout read, centralized so EVERY re-read
    (initial, each pass, each boundary, and the final convergence check) applies
    the SAME checks — shape (single clean row of full-height columns, finite
    geometry) AND root membership. Omitting either on any re-read is a hole:
    the post-cap convergence check used to run only `_ordered_columns`, so a
    final stacked/gapped layout with coincidentally-equal widths returned
    success, and rereads never reconfirmed the root was still present.

    Returns the ordered (ids, widths) so callers don't re-parse.
    """
    validate_single_row(data)
    ids, widths = _ordered_columns(panes_from_layout(data))
    require_root_membership(ids, root_pane)
    return ids, widths


def equalize_live(root_pane: str | None) -> int:
    """Drive the iterative boundary equalizer against a live herdr server.

    Re-reads the layout each pass (resizes perturb downstream columns), and
    stops once the width spread is within EQUAL_TOLERANCE_CELLS or the pass
    cap is hit. Returns 0 on convergence, 1 if it never converged.
    """
    if not shutil.which("herdr"):
        raise SystemExit("herdr not on PATH")

    # Reject 2D / stacked layouts (and a missing root) BEFORE any resize —
    # mutating a layout the column model misreads would scramble the panes.
    initial = load_layout(root_pane, None)
    validate_live_layout(initial, root_pane)

    for _ in range(MAX_EQUALIZE_PASSES):
        data = load_layout(root_pane, None)
        # FULL revalidation on every live re-read (shape + root membership), not
        # just once up front: a resize or an external client could turn the tab
        # into a 2D/stacked/gappy layout, or drop the root, mid-equalize — and
        # computing resize ops for that would scramble the panes.
        ids, widths = validate_live_layout(data, root_pane)
        area = area_width_from_layout(data)
        n = len(ids)
        if n < 2:
            return 0  # single column is trivially "equal"
        targets = equal_targets(n, area)
        spread = max(widths) - min(widths)
        if spread <= EQUAL_TOLERANCE_CELLS:
            return 0
        for boundary in range(n - 1):
            # Re-read after each resize: one resize shifts every column to the
            # right of the moved boundary, so later ops in this pass need the
            # updated widths to aim correctly. FULL revalidation each time too.
            data = load_layout(root_pane, None)
            ids, widths = validate_live_layout(data, root_pane)
            area = area_width_from_layout(data)
            targets = equal_targets(len(ids), area)
            if boundary >= len(ids) - 1:
                break
            op = boundary_resize_op(ids, widths, targets, area, boundary)
            if op is None:
                continue
            pane_id, direction, amount = op
            cp = _run_herdr(
                "pane", "resize", "--pane", pane_id,
                "--direction", direction, "--amount", f"{amount:.6f}",
            )
            # A failed resize is a HARD error — silently swallowing it (the
            # old `|| true` behaviour) leaves an unequal layout that the
            # caller then launches workers into. Surface the exact command
            # and herdr's message so the caller can act.
            if cp.returncode != 0:
                detail = (cp.stderr.strip() or cp.stdout.strip()
                          or f"exit {cp.returncode}")
                raise SystemExit(
                    f"herdr pane resize failed for {pane_id} "
                    f"(--direction {direction} --amount {amount:.6f}): {detail}. "
                    f"Layout left unequal; inspect with "
                    f"`herdr pane layout --pane {root_pane or '--current'}`."
                )

    # Final check after the cap. FULL validation here too — the convergence
    # check previously ran only `_ordered_columns`, so a final stacked/gapped
    # layout (or one that lost the root) with coincidentally-equal widths would
    # return success. Non-convergence is also a hard error — do not report
    # "best-effort" and let the caller proceed onto an unequal grid.
    data = load_layout(root_pane, None)
    _, widths = validate_live_layout(data, root_pane)
    spread = max(widths) - min(widths)
    if spread <= EQUAL_TOLERANCE_CELLS:
        return 0
    raise SystemExit(
        f"columns did not converge to equal width after {MAX_EQUALIZE_PASSES} "
        f"passes (widths {[int(w) for w in widths]}, spread {spread:.0f} cells). "
        f"Do NOT launch workers into this layout; inspect with "
        f"`herdr pane layout --pane {root_pane or '--current'}` and retry, or "
        f"reduce the column count."
    )


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--root-pane",
        help="root/orchestrator pane id; checked for presence, not otherwise special",
    )
    ap.add_argument(
        "--layout-json",
        help="layout JSON path, or '-' for stdin (skips herdr pane layout)",
    )
    ap.add_argument(
        "--equalize",
        action="store_true",
        help="run the live iterative boundary equalizer over the current tab and exit",
    )
    args = ap.parse_args()

    if args.equalize:
        try:
            return equalize_live(args.root_pane)
        except (OSError, json.JSONDecodeError, SystemExit) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    try:
        data = load_layout(args.root_pane, args.layout_json)
        # FULL validation (shape + finite geometry + root membership) before
        # planning — the "rightmost column" target is ambiguous in a 2D/stacked
        # layout and the caller would split blindly. Same centralized check the
        # equalizer uses on every re-read.
        validate_live_layout(data, args.root_pane)
        rightmost, new_count = plan_next_split(panes_from_layout(data), args.root_pane)
    except (OSError, json.JSONDecodeError, SystemExit) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # `--ratio R` = the existing/left child's fraction of the split column.
    # R = 1/N makes the NEW (right) pane the equal 1/N target (see split_ratio).
    ratio = split_ratio(new_count)
    print(f"split {rightmost} right --ratio {ratio:.6f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
