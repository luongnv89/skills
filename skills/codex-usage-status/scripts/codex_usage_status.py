#!/usr/bin/env python3

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from typing import Any, Dict, Optional


def _run_openclaw_status_usage_json(timeout_ms: int) -> Dict[str, Any]:
    cmd = ["openclaw", "status", "--usage", "--json", "--timeout", str(timeout_ms)]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except FileNotFoundError:
        raise RuntimeError("openclaw CLI not found in PATH")
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").strip()
        stdout = (e.stdout or "").strip()
        msg = stderr or stdout or f"openclaw exited {e.returncode}"
        raise RuntimeError(msg)

    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse JSON from openclaw status: {e}")


def _parse_window_seconds(label: str) -> Optional[int]:
    s = (label or "").strip().lower()

    # Common named windows
    if s in {"day", "daily"}:
        return 24 * 3600
    if s in {"week", "weekly"}:
        return 7 * 24 * 3600
    if s in {"month", "monthly"}:
        # Approx; only used for optional projections
        return 30 * 24 * 3600

    # Compact formats: 5h, 30m, 7d
    m = re.match(r"^(\d+(?:\.\d+)?)([hmd])$", s)
    if m:
        num = float(m.group(1))
        unit = m.group(2)
        mult = {"m": 60, "h": 3600, "d": 86400}[unit]
        return int(num * mult)

    # Other formats (best-effort)
    m = re.match(r"^(\d+)\s*hours?$", s)
    if m:
        return int(m.group(1)) * 3600
    m = re.match(r"^(\d+)\s*days?$", s)
    if m:
        return int(m.group(1)) * 86400

    return None


def _human_td(seconds: float) -> str:
    seconds = max(0, int(seconds))
    d, rem = divmod(seconds, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)

    parts = []
    if d:
        parts.append(f"{d}d")
    if h:
        parts.append(f"{h}h")
    if m:
        parts.append(f"{m}m")
    if not parts:
        parts.append(f"{s}s")
    return " ".join(parts[:3])


def _pace_projection_percent(
    used_percent: Optional[float],
    now: dt.datetime,
    window_start: dt.datetime,
    window_end: dt.datetime,
) -> Optional[float]:
    if used_percent is None:
        # If there's no usage data yet, define pace as 0%
        return 0.0

    used_percent = float(used_percent)
    if used_percent <= 0:
        return 0.0

    elapsed = (now - window_start).total_seconds()
    remaining = (window_end - now).total_seconds()

    if elapsed <= 0:
        return None

    projected = used_percent + (used_percent / elapsed) * max(0.0, remaining)
    return projected


def _week_bounds_from_day_reset(
    now: dt.datetime,
    day_reset_at: Optional[dt.datetime],
) -> tuple[dt.datetime, dt.datetime]:
    """
    Define the week window from Day reset timing:
    - week_end = next Day reset time
    - week_start = week_end - 7 days
    """
    if day_reset_at is None:
        # Fallback if provider didn't expose Day resetAt
        midnight = dt.datetime(now.year, now.month, now.day, tzinfo=dt.timezone.utc)
        week_start = midnight - dt.timedelta(days=midnight.weekday())
        week_end = week_start + dt.timedelta(days=7)
        return week_start, week_end

    week_end = day_reset_at
    # Guard stale snapshots: ensure week_end is in the future
    while week_end <= now:
        week_end += dt.timedelta(days=1)

    week_start = week_end - dt.timedelta(days=7)
    return week_start, week_end


def _find_provider(payload: Dict[str, Any], provider: str) -> Dict[str, Any]:
    usage = payload.get("usage") or {}
    providers = usage.get("providers") or []
    for p in providers:
        if (p.get("provider") or "").strip() == provider:
            return p
    known = ", ".join(sorted({(p.get("provider") or "").strip() for p in providers if p.get("provider")}))
    raise RuntimeError(f"Provider '{provider}' not found in openclaw status usage. Known: {known or '(none)'}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Show OpenAI Codex usage/quota windows and pace (week projection from Day usage, anchored to Day resetAt)"
    )
    ap.add_argument("--provider", default="openai-codex", help="Provider id (default: openai-codex)")
    ap.add_argument("--timeout", type=int, default=10000, help="openclaw status probe timeout ms (default: 10000)")
    ap.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = ap.parse_args()

    now = dt.datetime.now(dt.timezone.utc)

    payload = _run_openclaw_status_usage_json(timeout_ms=args.timeout)
    p = _find_provider(payload, provider=args.provider)

    display = p.get("displayName") or p.get("provider")
    plan = p.get("plan")
    windows = p.get("windows") or []

    rows = []
    day_used = None
    day_reset_at = None

    for w in windows:
        label = w.get("label")
        used = w.get("usedPercent")
        reset_at_ms = w.get("resetAt")

        reset_at = None
        if isinstance(reset_at_ms, (int, float)) and reset_at_ms > 0:
            reset_at = dt.datetime.fromtimestamp(reset_at_ms / 1000.0, tz=dt.timezone.utc)

        label_s = str(label or "")
        if label_s.strip().lower() in {"day", "daily"}:
            day_used = used
            day_reset_at = reset_at

        rows.append(
            {
                "label": label,
                "usedPercent": used,
                "resetAt": reset_at.isoformat() if reset_at else None,
                "resetInSeconds": (reset_at - now).total_seconds() if reset_at else None,
                "windowSecondsGuess": _parse_window_seconds(label_s),
            }
        )

    # Pace: compute weekly projection using Day usage, with week anchored to Day resetAt
    week_start, week_end = _week_bounds_from_day_reset(now, day_reset_at)
    pace_week = _pace_projection_percent(day_used, now=now, window_start=week_start, window_end=week_end)

    if args.json:
        out = {
            "provider": args.provider,
            "displayName": display,
            "plan": plan,
            "updatedAt": payload.get("usage", {}).get("updatedAt"),
            "now": now.isoformat(),
            "windows": rows,
            "pace": {
                "mode": "week-anchored-to-day-reset",
                "usedPercentBasis": day_used,
                "dayResetAt": day_reset_at.isoformat() if day_reset_at else None,
                "weekStart": week_start.isoformat(),
                "weekEnd": week_end.isoformat(),
                "projectedPercent": pace_week,
            },
        }
        print(json.dumps(out, indent=2, sort_keys=False))
        return 0

    print(f"{display} ({args.provider})" + (f" — {plan}" if plan else ""))

    for r in rows:
        label = str(r.get("label") or "?")
        used = r.get("usedPercent")
        used_s = "?" if used is None else f"{int(round(float(used)))}%"

        reset_at = r.get("resetAt")
        reset_in = r.get("resetInSeconds")
        reset_s = ""
        if reset_at and isinstance(reset_in, (int, float)):
            reset_s = f"reset in {_human_td(reset_in)} ({reset_at.replace('T', ' ').replace('+00:00', ' UTC')})"

        if reset_s:
            print(f"- {label}: {used_s} used · {reset_s}")
        else:
            print(f"- {label}: {used_s} used")

    # Show pace line (weekly projection based on Day used%)
    if day_used is None:
        print("\nPace: n/a (no 'Day' usage window found in this snapshot)")
        return 0

    pace_s = "n/a" if pace_week is None else f"{pace_week:.0f}%"
    elapsed = (now - week_start).total_seconds()
    remaining = (week_end - now).total_seconds()

    print(
        "\nPace (from Day usage, week window anchored to Day resetAt): "
        + f"{pace_s} projected by {week_end.isoformat().replace('T', ' ').replace('+00:00', ' UTC')} "
        + f"(elapsed {_human_td(elapsed)}, remaining {_human_td(remaining)})"
    )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
