#!/usr/bin/env python3
"""App Store tracker: collect App Store Connect data with the `asc` CLI, keep a
day-by-day history on disk, and render a self-contained HTML dashboard.

Subcommands
  status   check asc, credentials, vendor number, data access and the data dir
  config   show or change tracker settings (profiles, vendor, currency, window)
  fetch    pull apps, versions, reviews, ratings, store listings, daily sales, FX
  analyze  aggregate the history; write data/digest.json for the agent
  render   validate the day's insights file; write dashboard.html + history copy
           (both pick up data/competitors.json from appstore-competitor-tracker when present)
  demo     write a synthetic data dir (no network) for previews and tests

Every App Store Connect call runs with ASC_READ_ONLY=1, so nothing is changed in
App Store Connect. Standard library only (Python 3.9+).
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import gzip
import io
import json
import math
import os
import random
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

try:
    from zoneinfo import ZoneInfo

    PT = ZoneInfo("America/Los_Angeles")
except Exception:  # pragma: no cover - zoneinfo missing on very old Pythons
    PT = timezone(timedelta(hours=-8))

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows
    fcntl = None

VERSION = "1.1.1"
SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "assets" / "dashboard.html"
DEFAULT_HOME = "~/.appstore-tracker"
MAX_BACKFILL = 365  # Apple keeps daily Sales and Trends reports for about a year
ISO_CURRENCIES = set(  # ISO 4217 codes; config checks a base currency against these before the first FX fetch
    "AED AFN ALL AMD ANG AOA ARS AUD AWG AZN BAM BBD BDT BGN BHD BIF BMD BND BOB BRL BSD BTN BWP BYN BZD CAD CDF CHF "
    "CLP CNY COP CRC CUP CVE CZK DJF DKK DOP DZD EGP ERN ETB EUR FJD FKP GBP GEL GHS GIP GMD GNF GTQ GYD HKD HNL HTG "
    "HUF IDR ILS INR IQD IRR ISK JMD JOD JPY KES KGS KHR KMF KPW KRW KWD KYD KZT LAK LBP LKR LRD LSL LYD MAD MDL MGA "
    "MKD MMK MNT MOP MRU MUR MVR MWK MXN MYR MZN NAD NGN NIO NOK NPR NZD OMR PAB PEN PGK PHP PKR PLN PYG QAR RON RSD "
    "RUB RWF SAR SBD SCR SDG SEK SGD SHP SLE SOS SRD SSP STN SVC SYP SZL THB TJS TMT TND TOP TRY TTD TWD TZS UAH UGX "
    "USD UYU UZS VED VES VND VUV WST XAF XCD XOF XPF YER ZAR ZMW ZWG ZWL SLL".split())
PENDING_DAYS = 3  # a missing report this recent may still be published
WINDOWS = [7, 28, 90, 365]
FX_URL = "https://open.er-api.com/v6/latest/USD"
LOOKUP_URL = "https://itunes.apple.com/lookup?id={id}&country={cc}"
USER_AGENT = "appstore-tracker/" + VERSION

DEFAULT_CONFIG = {
    "profile": None,
    "sales_profile": None,
    "vendor_number": None,
    "base_currency": "USD",
    "backfill_days": 90,
    "include_apps": None,
    "exclude_apps": [],
}

# Apple's Product Type Identifiers (App Store Connect Help > Reporting >
# Product type identifiers). Codes outside these sets are counted as "other".
DOWNLOAD = {"1", "1F", "1T", "1E", "1EP", "1EU", "F1", "1-B", "F1-B"}
REDOWNLOAD = {"3", "3F", "3T", "F3"}
UPDATE = {"7", "7F", "7T", "F7"}
SUBSCRIPTION = {"IAY", "IAY-M", "1AY", "IA9", "IA9-M"}
IAP = {"IA1", "IA1-M", "FI1", "IAC", "IAC-M"}
RESTORE = {"IA3"}

# App Store country -> languages a listing should support to read natively.
COUNTRY_LANGS = {
    "US": ["EN"], "GB": ["EN"], "CA": ["EN", "FR"], "AU": ["EN"], "NZ": ["EN"],
    "IE": ["EN"], "IN": ["EN", "HI"], "SG": ["EN", "ZH"], "PH": ["EN"],
    "ZA": ["EN"], "NG": ["EN"], "KE": ["EN"], "FR": ["FR"], "BE": ["FR", "NL"],
    "CH": ["DE", "FR", "IT"], "LU": ["FR", "DE"], "DE": ["DE"], "AT": ["DE"],
    "IT": ["IT"], "ES": ["ES"], "MX": ["ES"], "AR": ["ES"], "CO": ["ES"],
    "CL": ["ES"], "PE": ["ES"], "PT": ["PT"], "BR": ["PT"], "NL": ["NL"],
    "SE": ["SV"], "NO": ["NB", "NO"], "DK": ["DA"], "FI": ["FI"], "PL": ["PL"],
    "CZ": ["CS"], "SK": ["SK"], "HU": ["HU"], "RO": ["RO"], "GR": ["EL"],
    "TR": ["TR"], "RU": ["RU"], "UA": ["UK"], "IL": ["HE"], "SA": ["AR"],
    "AE": ["AR", "EN"], "EG": ["AR"], "JP": ["JA"], "KR": ["KO"], "CN": ["ZH"],
    "TW": ["ZH"], "HK": ["ZH"], "VN": ["VI"], "TH": ["TH"], "ID": ["ID"],
    "MY": ["MS", "EN"],
}


# --------------------------------------------------------------------------
# Errors and small helpers
# --------------------------------------------------------------------------


class TrackerError(Exception):
    """An error with a fix the user or agent can act on."""

    def __init__(self, what: str, fix: str, code: int = 1):
        super().__init__(what)
        self.what, self.fix, self.code = what, fix, code


class AscError(Exception):
    def __init__(self, kind: str, message: str, command: list[str]):
        super().__init__(message)
        self.kind, self.message, self.command = kind, message, command


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def today_local() -> date:
    return datetime.now().date()


def today_pt() -> date:
    return datetime.now(PT).date()


def parse_day(text: str) -> date:
    return datetime.strptime(text, "%Y-%m-%d").date()


def day_range(first: date, last: date) -> list[date]:
    return [first + timedelta(days=i) for i in range((last - first).days + 1)]


def read_json(path: Path, default=None, fix: str | None = None, code: int = 1):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default
    except json.JSONDecodeError as exc:
        raise TrackerError(
            f"{path} is not valid JSON (line {exc.lineno}, column {exc.colno}: {exc.msg}).",
            fix or f"Fix or delete {path}; `fetch` recreates raw files on its next run.",
            code,
        )


# An insights file is written by the agent, never by fetch; a broken one exits 2 like a schema error.
INSIGHTS_FIX = "Rewrite it as valid JSON from data/digest.json (schema: references/analysis-playbook.md > Insights file), then rerun."


def unknown_apps_error(bad, apps) -> "TrackerError":
    valid = ", ".join(f"{a['id']} ({a.get('name') or '?'})" for a in sorted(apps, key=lambda a: a["id"])) or "none"
    return TrackerError(f"app id(s) not in this account: {', '.join(sorted(bad))}.",
                        f"Use ids from this account: {valid}. `tracker.py fetch` refreshes this list.")


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1, sort_keys=False)
    os.replace(tmp, path)


def to_float(text) -> float:
    try:
        return float(str(text).replace(",", "").strip() or 0)
    except ValueError:
        return 0.0


def resolve_home(arg: str | None) -> Path:
    raw = arg or os.environ.get("APPSTORE_TRACKER_HOME") or DEFAULT_HOME
    return Path(raw).expanduser().resolve()


@contextlib.contextmanager
def home_lock(home: Path):
    home.mkdir(parents=True, exist_ok=True)
    if fcntl is None:
        yield
        return
    fh = open(home / ".lock", "w")
    try:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise TrackerError(
                f"Another tracker run is using {home}.",
                "Wait for it to finish, or pass a different --data-dir.",
            )
        yield
    finally:
        fh.close()


def mask_digits(text: str) -> str:
    """Hide vendor numbers and other long digit runs that follow --vendor."""
    return re.sub(r"(--vendor[ =]\s*)(\d{2})\d+(\d{2})", r"\1\2…\3", text or "")


def public_config(cfg: dict) -> dict:
    out = dict(cfg)
    v = str(out.get("vendor_number") or "")
    if v:
        out["vendor_number"] = v[:2] + "…" + v[-2:]
    return out


def load_config(home: Path) -> dict:
    cfg = dict(DEFAULT_CONFIG)
    cfg.update(read_json(home / "config.json", {}) or {})
    return cfg


# --------------------------------------------------------------------------
# asc wrapper: read-only, JSON, timeout, classified errors
# --------------------------------------------------------------------------


def classify_asc_error(text: str) -> str:
    low = text.lower()
    if "forbidden" in low or "does not allow this request" in low or " 403" in low:
        return "forbidden"
    if "not found" in low or " 404" in low:
        return "not_found"
    if "rate limit" in low or " 429" in low:
        return "rate_limit"
    if any(k in low for k in ("401", "not_authorized", "unauthorized", "credential", "authentication", "private key")):
        return "auth"
    if any(k in low for k in ("no such host", "connection", "network", "dial tcp", "tls", "timeout")):
        return "network"
    return "error"


def asc(args: list[str], profile: str | None = None, timeout: int = 90, parse: bool = True):
    if shutil.which("asc") is None:
        raise AscError("missing", "the asc CLI is not on PATH", ["asc"] + args)
    cmd = ["asc"] + (["--profile", profile] if profile else []) + args
    env = dict(os.environ, ASC_READ_ONLY="1")
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, env=env, stdin=subprocess.DEVNULL
        )
    except subprocess.TimeoutExpired:
        raise AscError("timeout", f"no answer within {timeout}s", cmd)
    if proc.returncode != 0:
        text = "\n".join(x for x in (proc.stderr, proc.stdout) if x).strip()
        first = next((ln.strip() for ln in text.splitlines() if ln.strip()), "exit code %d" % proc.returncode)
        raise AscError(classify_asc_error(text), mask_digits(first[:400]), cmd)
    if not parse:
        return proc.stdout
    out = proc.stdout.strip()
    if not out:
        return {}
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        raise AscError("bad_output", "asc printed non-JSON output: " + out[:200], cmd)


def asc_fix(err: AscError, what: str, profile: str | None) -> str:
    who = f"profile '{profile}'" if profile else "the default asc profile"
    cmd = " ".join(err.command[:4])
    if err.kind == "missing":
        return "Install it with `brew install asc` (https://asccli.sh), then `asc auth login`."
    if err.kind == "timeout":
        return (f"`{cmd}` hung. On macOS this usually means a Keychain dialog is waiting: click "
                "'Always Allow' for asc, then rerun. Otherwise run `asc auth doctor`.")
    if err.kind == "forbidden":
        return (f"The API key of {who} may not {what}. Sales reports need a key with the Sales, "
                "Finance or Admin role: `asc auth login --name Sales ...`, then "
                "`tracker.py config --sales-profile Sales`.")
    if err.kind == "auth":
        return "asc could not authenticate. Run `asc auth status` and `asc auth doctor`."
    if err.kind == "network":
        return "Check the network connection, then rerun `fetch`."
    if err.kind == "rate_limit":
        return "Apple rate-limited the requests. Wait a few minutes, then rerun with --workers 1."
    return mask_digits(f"Run the command by hand to see the full error: {' '.join(err.command)}")


def asc_config_paths() -> list[Path]:
    paths = []
    if os.environ.get("ASC_CONFIG_PATH"):
        paths.append(Path(os.environ["ASC_CONFIG_PATH"]).expanduser())
    cur = Path.cwd()
    for parent in [cur] + list(cur.parents):
        paths.append(parent / ".asc" / "config.json")
    paths.append(Path("~/.asc/config.json").expanduser())
    return paths


def resolve_vendor(cfg: dict) -> tuple[str | None, str | None]:
    if cfg.get("vendor_number"):
        return str(cfg["vendor_number"]), "tracker config"
    for env in ("ASC_VENDOR_NUMBER", "ASC_ANALYTICS_VENDOR_NUMBER"):
        if os.environ.get(env):
            return os.environ[env], f"${env}"
    for path in asc_config_paths():
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            for key in ("vendor_number", "analytics_vendor_number"):  # read only these keys
                if data.get(key):
                    return str(data[key]), f"{path} ({key})"
            break
    return None, None


# --------------------------------------------------------------------------
# Collectors
# --------------------------------------------------------------------------


def http_json(url: str, timeout: int = 20):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_apps(profile, timeout) -> list[dict]:
    data = asc(["apps", "list", "--paginate", "--limit", "200", "--output", "json"], profile, timeout)
    apps = []
    for item in data.get("data", []):
        a = item.get("attributes", {})
        apps.append({
            "id": str(item.get("id")), "name": a.get("name") or str(item.get("id")),
            "bundle_id": a.get("bundleId"), "sku": a.get("sku"), "primary_locale": a.get("primaryLocale"),
        })
    return apps


def fetch_versions(app_id, profile, timeout) -> list[dict]:
    data = asc(["versions", "list", "--app", app_id, "--paginate", "--limit", "200", "--output", "json"], profile, timeout)
    out = []
    for item in data.get("data", []):
        a = item.get("attributes", {})
        out.append({
            "id": item.get("id"), "platform": a.get("platform"), "version": a.get("versionString"),
            "state": a.get("appStoreState") or a.get("appVersionState"),
            "created": (a.get("createdDate") or "")[:10], "release_type": a.get("releaseType"),
        })
    return out


BLOCKED_PRODUCT_STATES = {"MISSING_METADATA", "DEVELOPER_ACTION_NEEDED", "REJECTED", "WAITING_FOR_UPLOAD"}


def fetch_products(app_id, profile, timeout) -> list[dict]:
    """In-app purchases and subscriptions with their review state (a product not APPROVED cannot be bought)."""
    out = []
    for kind, args in (("iap", ["iap", "list"]), ("subscription", ["subscriptions", "list"])):
        data = asc(args + ["--app", app_id, "--paginate", "--limit", "200", "--output", "json"], profile, timeout)
        for item in data.get("data", []):
            a = item.get("attributes", {})
            out.append({"id": item.get("id"), "kind": kind, "name": a.get("name"), "product_id": a.get("productId"),
                        "type": a.get("inAppPurchaseType") or a.get("subscriptionPeriod"), "state": a.get("state")})
    return out


WEB_MEASURES = {  # App Analytics measure -> tracker metric
    "units": "downloads", "redownloads": "redownloads", "updates": "updates", "proceeds": "proceeds",
    "iap": "iap", "impressionsTotal": "impressions", "pageViewCount": "page_views",
}
REJECTED_STATES = {"REJECTED", "METADATA_REJECTED", "INVALID_BINARY"}


def web_session_ok(timeout) -> tuple[bool, str]:
    """True when asc has a cached Apple web session; never logs in or prompts."""
    try:
        st = asc(["web", "auth", "status", "--output", "json"], None, min(timeout, 60))
    except AscError as err:
        return False, err.message
    return bool(st.get("authenticated")), "not authenticated"


def fetch_web_analytics(home: Path, app_id: str, first: date, last: date, timeout: int) -> tuple[int, int]:
    """Merge App Analytics daily values into raw/web/<app>.json; the newest fetch wins (Apple revises recent days).
    Returns (days added by this fetch, days stored in total)."""
    data = asc(["web", "analytics", "overview", "--app", app_id, "--start", first.isoformat(),
                "--end", last.isoformat(), "--output", "json"], None, max(timeout, 180))
    path = home / "raw" / "web" / f"{app_id}.json"
    store = read_json(path, {}) or {}
    measures = store.setdefault("measures", {})
    held = {d for series in measures.values() for d in series}
    for block in ("acquisition", "sales"):
        for m in data.get(block) or []:
            name = WEB_MEASURES.get(m.get("measure"))
            if not name:
                continue
            series = measures.setdefault(name, {})
            for point in m.get("data") or []:
                day = str(point.get("date", ""))[:10]
                if not day:
                    continue
                if m.get("meetsThreshold") is False:  # below Apple's privacy threshold: unknown, not zero
                    series.pop(day, None)
                    continue
                series[day] = point.get("value") or 0
    store["updated"] = datetime.now().isoformat(timespec="seconds")
    write_json(path, store)
    days = {d for series in measures.values() for d in series}
    return len(days - held), len(days)


def fetch_rejection(app_id: str, timeout: int) -> dict:
    """Guideline ids and plain-text reason of the latest unresolved review; actor and key ids are dropped."""
    data = asc(["web", "review", "show", "--app", app_id, "--plain-text", "--output", "json"], None, max(timeout, 120))
    messages = [m for th in data.get("threads") or [] for m in th.get("messages") or []]
    text = " ".join((m.get("messageBodyPlain") or "") for m in messages)
    guidelines = sorted(set(re.findall(r"Guideline (\d+(?:\.\d+)*(?:\([a-z]\))?) - ([A-Za-z ,&-]+?)(?= Issue| [A-Z][a-z]+ [a-z]|$)", text)))
    created = max((m.get("createdDate") or "" for m in messages), default="")[:10]
    return {"date": created, "state": (data.get("submission") or {}).get("state"),
            "guidelines": [f"{g} - {title.strip()}" for g, title in guidelines],
            "spam": any(g.startswith("4.3") for g, _ in guidelines), "message": trim(text, 1500)}


def fetch_reviews(app_id, profile, timeout) -> list[dict]:
    data = asc(["reviews", "--app", app_id, "--paginate", "--limit", "200", "--sort", "-createdDate",
                "--include-response", "--output", "json"], profile, timeout)
    responses = {
        inc.get("id"): inc.get("attributes", {})
        for inc in data.get("included", []) or []
        if inc.get("type") == "customerReviewResponses"
    }
    out = []
    for item in data.get("data", []):
        a = item.get("attributes", {})
        rel = ((item.get("relationships") or {}).get("response") or {}).get("data")
        resp = responses.get(rel.get("id")) if isinstance(rel, dict) else None
        out.append({
            "id": item.get("id"), "rating": a.get("rating"), "title": a.get("title") or "",
            "body": a.get("body") or "", "nickname": a.get("reviewerNickname") or "",
            "territory": a.get("territory") or "", "created": a.get("createdDate") or "",
            "response": ({"body": resp.get("responseBody"), "state": resp.get("state"),
                          "date": (resp.get("lastModifiedDate") or "")[:10]} if resp else None),
        })
    return out


def fetch_ratings(app_id, timeout) -> dict:
    try:
        data = asc(["reviews", "ratings", "--app", app_id, "--all", "--output", "json"], None, max(timeout, 180))
    except AscError as err:
        if err.kind == "not_found" or "not found in any country" in err.message:
            return {"listed": False}
        raise
    by_country = data.get("byCountry") or []
    if isinstance(by_country, dict):
        by_country = [dict(v, country=k) if isinstance(v, dict) else {"country": k, "count": v} for k, v in by_country.items()]
    top = sorted(by_country, key=lambda c: -(c.get("count") or c.get("totalCount") or 0))[:10]
    return {"listed": True, "average": data.get("averageRating") or 0, "count": data.get("totalCount") or 0,
            "countries": data.get("countryCount") or 0, "top": top}


def fetch_store(app_id, countries) -> dict:
    tried = []
    for cc in countries:
        cc = cc.lower()
        if cc in tried:
            continue
        tried.append(cc)
        data = http_json(LOOKUP_URL.format(id=app_id, cc=cc))
        if data.get("resultCount"):
            r = data["results"][0]
            keep = ("kind", "trackName", "formattedPrice", "price", "currency", "version",
                    "currentVersionReleaseDate", "releaseDate", "primaryGenreName", "trackViewUrl",
                    "artworkUrl100", "averageUserRating", "userRatingCount", "languageCodesISO2A",
                    "minimumOsVersion", "sellerName", "contentAdvisoryRating")
            out = {k: r.get(k) for k in keep}
            out["listed"], out["country"] = True, cc
            return out
    return {"listed": False, "countries_tried": tried}


def fetch_fx(home: Path, day: str) -> dict:
    path = home / "raw" / "fx" / f"{day}.json"
    if path.exists():
        return {"state": "cached", "path": str(path)}
    data = http_json(FX_URL)
    if data.get("result") != "success" or not data.get("rates"):
        raise TrackerError("the exchange-rate service returned no rates.", "Rerun later, or pass --skip fx.")
    write_json(path, {"base": "USD", "date": day, "source": "open.er-api.com (ExchangeRate-API)",
                      "updated": data.get("time_last_update_utc"), "rates": data["rates"]})
    return {"state": "downloaded", "path": str(path)}


def sales_status(home: Path) -> dict:
    return read_json(home / "raw" / "sales" / "status.json", {}) or {}


def fetch_sales_day(day: date, vendor: str, profile, timeout, sales_dir: Path) -> str:
    final = sales_dir / f"{day.isoformat()}.tsv.gz"
    with tempfile.TemporaryDirectory(dir=sales_dir, prefix=".dl-") as tmp:
        target = Path(tmp) / "report.tsv.gz"
        meta = asc(["analytics", "sales", "--vendor", vendor, "--type", "SALES", "--subtype", "SUMMARY",
                    "--frequency", "DAILY", "--date", day.isoformat(), "--allow-missing",
                    "--output", str(target), "--output-format", "json"], profile, timeout)
        if isinstance(meta, dict) and meta.get("available") is False:
            return "missing"
        produced = [p for p in Path(tmp).iterdir() if p.is_file() and p.stat().st_size > 0]
        if not produced and isinstance(meta, dict):
            for value in meta.values():
                if isinstance(value, str) and os.path.isfile(value):
                    produced = [Path(value)]
                    break
        if not produced:
            return "missing"
        src = produced[0]
        raw = src.read_bytes()
        if raw[:2] != b"\x1f\x8b":
            raw = gzip.compress(raw)
        gzip.decompress(raw)  # a truncated download raises here instead of landing on disk
        part = Path(tmp) / "final.part"
        part.write_bytes(raw)
        os.replace(part, final)  # atomic: an interrupted run never leaves a half-written day
    return "ok"


def collect_sales(home, cfg, vendor, days, workers, timeout, summary) -> None:
    sales_dir = home / "raw" / "sales" / "daily"
    sales_dir.mkdir(parents=True, exist_ok=True)
    status = sales_status(home)
    last = today_pt() - timedelta(days=1)
    first = last - timedelta(days=min(days, MAX_BACKFILL) - 1)
    todo = []
    for d in day_range(first, last):
        key = d.isoformat()
        if (sales_dir / f"{key}.tsv.gz").exists() or status.get(key) == "empty":
            continue
        todo.append(d)
    profile = cfg.get("sales_profile") or cfg.get("profile")
    info = {"window": [first.isoformat(), last.isoformat()], "requested": len(todo), "ok": 0,
            "empty": 0, "pending": 0, "errors": 0, "profile": profile or "default"}
    summary["sales"] = info
    if not todo:
        return
    log(f"fetch: downloading {len(todo)} daily sales report(s) {todo[0]}..{todo[-1]}")
    blocked: list[AscError] = []

    def one(d: date):
        if blocked:
            return d, "skipped", None
        try:
            return d, fetch_sales_day(d, vendor, profile, timeout, sales_dir), None
        except AscError as err:
            if err.kind in ("forbidden", "auth", "missing", "timeout"):
                blocked.append(err)
            return d, "error", err

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        results = list(pool.map(one, todo))
    first_err = None
    published = [p.name[:10] for p in sales_dir.glob("*.tsv.gz")]
    newest = max(published) if published else ""
    for d, state, err in results:
        key = d.isoformat()
        if state == "ok":
            info["ok"] += 1
            status.pop(key, None)
        elif state == "missing":
            # A missing day means "no activity" only once Apple has published a later day
            # and the day is old enough; otherwise keep retrying it.
            if (today_pt() - d).days > PENDING_DAYS and newest > key:
                info["empty"] += 1
                status[key] = "empty"
            else:
                info["pending"] += 1
                status[key] = "pending"
        elif state == "error":
            info["errors"] += 1
            first_err = first_err or err
    write_json(home / "raw" / "sales" / "status.json", status)
    err = blocked[0] if blocked else first_err
    if err:
        info["error_kind"] = err.kind
        summary["errors"].append({"source": "sales", "kind": err.kind, "message": err.message,
                                  "fix": asc_fix(err, "download Sales and Trends reports", profile)})


def merge_reviews(home: Path, app_id: str, fresh: list[dict], day: str) -> int:
    path = home / "raw" / "reviews" / f"{app_id}.json"
    store = read_json(path, {}) or {}
    added = 0
    for r in fresh:
        old = store.get(r["id"])
        if old is None:
            added += 1
            r["first_seen"] = day
        else:
            r["first_seen"] = old.get("first_seen", day)
        r["last_seen"] = day
        store[r["id"]] = r
    write_json(path, store)
    return added


def cmd_fetch(args) -> int:
    home = resolve_home(args.data_dir)
    with home_lock(home):
        cfg = load_config(home)
        if cfg.get("demo"):
            raise TrackerError(f"{home} holds synthetic demo data.",
                               "Use another --data-dir for real data, or delete the demo directory first.")
        skip = {s.strip() for s in (args.skip or "").split(",") if s.strip()}
        unknown = skip - {"versions", "reviews", "ratings", "store", "products", "analytics", "sales", "fx"}
        if unknown:
            raise TrackerError(f"unknown --skip value(s): {', '.join(sorted(unknown))}.",
                               "Use any of: versions, reviews, ratings, store, products, analytics, sales, fx.")
        day = today_local().isoformat()
        profile = cfg.get("profile")
        summary = {"date": day, "data_dir": str(home), "started": datetime.now().isoformat(timespec="seconds"),
                   "apps": 0, "errors": [], "sources": {}}
        try:
            apps = fetch_apps(profile, args.timeout)
        except AscError as err:
            raise TrackerError(f"could not list apps with asc ({err.kind}: {err.message}).",
                               asc_fix(err, "list apps", profile))
        include = set(cfg.get("include_apps") or [])
        exclude = set(cfg.get("exclude_apps") or [])
        only = {a.strip() for a in (args.apps or "").split(",") if a.strip()}
        known_ids = {a["id"] for a in apps}
        write_json(home / "raw" / "account_apps.json", apps)  # every app in the account; config validates ids against it
        bad = (include | only) - known_ids
        if bad:
            raise unknown_apps_error(bad, apps)
        apps = [a for a in apps if (not include or a["id"] in include) and a["id"] not in exclude]
        write_json(home / "raw" / "apps.json", apps)  # the tracked scope, even when --apps narrows this run
        if only:
            apps = [a for a in apps if a["id"] in only]
        summary["apps"] = len(apps)
        log(f"fetch: {len(apps)} app(s) in this run")

        snap_path = home / "snapshots" / f"{day}.json"
        snapshot = read_json(snap_path, {}) or {}
        snapshot.setdefault("apps", {})
        snapshot["date"] = day

        def per_app(app):
            aid, res, errs = app["id"], {}, []
            if "versions" not in skip:
                try:
                    res["versions"] = fetch_versions(aid, profile, args.timeout)
                except AscError as err:
                    errs.append(("versions", err, "read app versions", profile))
            if "reviews" not in skip:
                try:
                    res["reviews"] = fetch_reviews(aid, profile, args.timeout)
                except AscError as err:
                    errs.append(("reviews", err, "read customer reviews", profile))
            if "products" not in skip:
                try:
                    res["products"] = fetch_products(aid, profile, args.timeout)
                except AscError as err:
                    errs.append(("products", err, "read in-app purchases and subscriptions", profile))
            if "store" not in skip:
                try:
                    res["store"] = fetch_store(aid, ["us", "gb", "fr", "de", "jp", "vn"])
                except (urllib.error.URLError, OSError, ValueError) as err:
                    errs.append(("store", AscError("network", str(err), ["itunes lookup"]), "look up the store listing", None))
            return app, res, errs

        counts = defaultdict(int)
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            for app, res, errs in pool.map(per_app, apps):
                aid = app["id"]
                entry = snapshot["apps"].setdefault(aid, {})
                entry["name"] = app["name"]
                if "versions" in res:
                    write_json(home / "raw" / "versions" / f"{aid}.json", res["versions"])
                    counts["versions"] += 1
                if "reviews" in res:
                    counts["reviews_new"] += merge_reviews(home, aid, res["reviews"], day)
                    counts["reviews"] += len(res["reviews"])
                if "store" in res:
                    entry["store"] = res["store"]
                    counts["store"] += 1
                if "products" in res:
                    entry["products"] = res["products"]
                    counts["products"] += len(res["products"])
                for source, err, what, prof in errs:
                    summary["errors"].append({"source": source, "app": aid, "kind": err.kind,
                                              "message": err.message, "fix": asc_fix(err, what, prof)})

        if "ratings" not in skip:
            log("fetch: public ratings (about 4 s per app)")

            def rating(app):
                try:
                    return app, fetch_ratings(app["id"], args.timeout), None
                except AscError as err:
                    return app, None, err

            with ThreadPoolExecutor(max_workers=2) as pool:
                for app, res, err in pool.map(rating, apps):
                    if res is not None:
                        snapshot["apps"][app["id"]]["ratings"] = res
                        counts["ratings"] += 1
                    else:
                        summary["errors"].append({"source": "ratings", "app": app["id"], "kind": err.kind,
                                                  "message": err.message, "fix": asc_fix(err, "read public ratings", None)})

        if "analytics" not in skip:
            ok, why = web_session_ok(args.timeout)
            if not ok:
                summary["errors"].append({"source": "analytics", "kind": "no_web_session", "message": f"no Apple web session ({why})",
                                          "fix": "Ask the user to run `! asc web auth login` themselves; the skill never logs in. "
                                                 "Without it, impressions, page views and conversion are not collected."})
            else:
                last = today_pt() - timedelta(days=1)
                span = min(args.days or cfg.get("backfill_days") or 90, MAX_BACKFILL)
                log(f"fetch: App Analytics through the web session (about 12 s per app)")

                def web(app):
                    stored = (read_json(home / "raw" / "web" / f"{app['id']}.json", {}) or {}).get("measures", {}).get("downloads", {})
                    first = last - timedelta(days=span - 1)
                    if stored:  # refetch the trailing week, which Apple still revises
                        first = max(first, min(parse_day(max(stored)) - timedelta(days=7), last))
                    try:
                        return app, fetch_web_analytics(home, app["id"], first, last, args.timeout), None
                    except AscError as err:
                        return app, None, err

                with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
                    for app, web_days, err in pool.map(web, apps):
                        if err:
                            summary["errors"].append({"source": "analytics", "app": app["id"], "kind": err.kind, "message": err.message,
                                                      "fix": asc_fix(err, "read App Analytics", None)})
                        else:
                            counts["analytics_days_added"] += web_days[0]  # 0 on a same-day rerun
                            counts["analytics_days_total"] += web_days[1]
                for app in apps:
                    versions = read_json(home / "raw" / "versions" / f"{app['id']}.json", []) or []
                    latest = max(versions, key=lambda v: v.get("created") or "", default=None)
                    if latest and latest.get("state") in REJECTED_STATES:
                        try:
                            snapshot["apps"][app["id"]]["rejection"] = fetch_rejection(app["id"], args.timeout)
                            counts["rejections"] += 1
                        except AscError as err:
                            summary["errors"].append({"source": "rejection", "app": app["id"], "kind": err.kind,
                                                      "message": err.message, "fix": asc_fix(err, "read the App Review message", None)})

        snapshot["generated_at"] = datetime.now().isoformat(timespec="seconds")
        write_json(snap_path, snapshot)

        if "sales" not in skip:
            vendor, source = resolve_vendor(cfg)
            if not vendor:
                summary["sales"] = {"state": "no_vendor"}
                summary["errors"].append({
                    "source": "sales", "kind": "no_vendor", "message": "no vendor number configured",
                    "fix": "Find it in App Store Connect > Payments and Financial Reports (top left), then "
                           "`tracker.py config --vendor 12345678` or set vendor_number in ~/.asc/config.json."})
            else:
                days = args.days or cfg.get("backfill_days") or 90
                collect_sales(home, cfg, vendor, days, args.workers, args.timeout, summary)
                summary["sales"]["vendor_source"] = source
        if "fx" not in skip:
            try:
                summary["sources"]["fx"] = fetch_fx(home, day)
            except (urllib.error.URLError, OSError, ValueError, TrackerError) as err:
                summary["errors"].append({"source": "fx", "kind": "network", "message": str(err),
                                          "fix": "Rerun later; the dashboard uses the newest cached rates meanwhile."})

        summary["sources"].update({k: v for k, v in counts.items()})
        summary["finished"] = datetime.now().isoformat(timespec="seconds")
        summary["partial"] = bool(summary["errors"])
        state = read_json(home / "state.json", {}) or {}
        state["last_fetch"] = summary
        write_json(home / "state.json", state)
    for e in summary["errors"]:
        log(f"warning: {e['source']}{' ' + e['app'] if e.get('app') else ''}: {e['kind']}: {e['message']}\n  fix: {e['fix']}")
    print(json.dumps(summary, indent=1))
    return 3 if summary["partial"] else 0


# --------------------------------------------------------------------------
# Analysis
# --------------------------------------------------------------------------


def sales_category(ptype: str) -> str:
    p = ptype.strip().upper()
    if p in UPDATE:
        return "update"
    if p in REDOWNLOAD:
        return "redownload"
    if p in DOWNLOAD:
        return "download"
    if p in RESTORE:
        return "restore"
    if p in SUBSCRIPTION:
        return "subscription"
    if p in IAP or p.startswith("IA") or p.startswith("FI"):
        return "iap"
    return "other"


def read_tsv_gz(path: Path) -> list[dict]:
    raw = path.read_bytes()
    if raw[:2] != b"\x1f\x8b":
        raise ValueError("not a gzip sales report")
    text = gzip.decompress(raw).decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    if "Units" not in [(f or "").strip() for f in (reader.fieldnames or [])]:
        raise ValueError("no Units column in the report header")
    rows = []
    for row in reader:
        # Extra fields land under the None key as a list; ignore them.
        rows.append({k.strip(): (v or "").strip() for k, v in row.items() if isinstance(k, str) and not isinstance(v, list)})
    return rows


def pick(row: dict, *names: str) -> str:
    for n in names:
        if n in row:
            return row[n]
    return ""


class FX:
    def __init__(self, home: Path, base: str):
        self.base = base.upper()
        files = sorted((home / "raw" / "fx").glob("*.json"))
        self.data = read_json(files[-1], {}) if files else {}
        self.rates = (self.data or {}).get("rates") or {}
        self.unconverted = defaultdict(float)

    def convert(self, amount: float, cur: str) -> float | None:
        cur = (cur or self.base).upper()
        if cur == self.base:
            return amount
        if cur in self.rates and self.base in self.rates and self.rates[cur]:
            return amount / self.rates[cur] * self.rates[self.base]
        self.unconverted[cur] += amount
        return None

    def meta(self) -> dict:
        return {"base": self.base, "date": (self.data or {}).get("date"), "source": (self.data or {}).get("source"),
                "updated": (self.data or {}).get("updated"),
                "unconverted": {k: round(v, 2) for k, v in self.unconverted.items()}}


METRICS = ["downloads", "redownloads", "updates", "iap", "subs", "restores", "refunds",
           "proceeds", "proceeds_app", "proceeds_iap", "promo", "impressions", "page_views"]


def new_day() -> dict:
    return {m: 0.0 for m in METRICS}


def pct(cur, prev):
    if prev in (None, 0) or cur is None:
        return None
    return round((cur - prev) / abs(prev) * 100, 1)


COMPETITOR_STALE_DAYS = 2
COMPETITOR_SEVERITIES = {"critical", "warning", "good", "info"}


def load_competitors(home: Path, app_ids) -> tuple[dict | None, list[dict]]:
    """Read data/competitors.json (written by appstore-competitor-tracker). Absent -> (None, []).
    A broken or stale file becomes a data gap, never a failed run."""
    path = home / "data" / "competitors.json"
    if not path.exists():
        return None, []
    fix = "Rerun `competitors.py fetch` and `competitors.py analyze` (appstore-competitor-tracker)."
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, [{"source": "competitors", "kind": "invalid", "message": f"data/competitors.json is unreadable ({exc})", "fix": fix}]
    if not isinstance(data, dict) or not isinstance(data.get("groups"), list) or not isinstance(data.get("meta"), dict):
        return None, [{"source": "competitors", "kind": "invalid", "message": "data/competitors.json has no meta/groups", "fix": fix}]
    gaps, meta = [], data["meta"]
    as_of = meta.get("as_of")
    try:
        age = (today_local() - parse_day(str(as_of))).days
    except ValueError:
        age = None
    if age is None or age > COMPETITOR_STALE_DAYS:
        gaps.append({"source": "competitors", "kind": "stale",
                     "message": f"competitor data is from {as_of or 'an unknown day'}" + (f", {age} days old" if age is not None else ""),
                     "fix": fix})
    errs = [e for e in meta.get("errors") or [] if isinstance(e, dict)]
    if errs:
        kinds = sorted({f"{e.get('source')}:{e.get('kind')}" for e in errs})
        gaps.append({"source": "competitors", "kind": "partial", "message": f"{len(errs)} competitor source(s) failed in the last fetch ({', '.join(kinds[:6])}); their metrics are unknown, not zero",
                     "fix": fix})
    groups = []
    for g in data["groups"]:
        if not isinstance(g, dict) or not isinstance(g.get("apps"), list):
            continue
        if str(g.get("app_id")) not in app_ids:
            gaps.append({"source": "competitors", "kind": "unknown_app", "message": f"competitor group for app {g.get('app_id')} is not in this account; skipped",
                         "fix": "Track that app, or `competitors.py remove` its group."})
            continue
        groups.append(g)
    signals = []
    for x in data.get("signals") or []:
        if not isinstance(x, dict):
            continue
        scope, kind = str(x.get("scope") or ""), str(x.get("kind") or "")
        if scope not in app_ids or not kind.startswith("competitor_") or x.get("id") != f"{scope}/{kind}" or x.get("severity") not in COMPETITOR_SEVERITIES:
            continue
        signals.append(sig(scope, kind, x["severity"], trim(str(x.get("title") or kind), 200), trim(str(x.get("detail") or ""), 600),
                           **(x.get("metrics") if isinstance(x.get("metrics"), dict) else {})))
    return {"meta": meta, "groups": groups, "signals": signals, "stale": bool(age is None or age > COMPETITOR_STALE_DAYS)}, gaps


def competitor_overview(comp: dict) -> dict:
    """Compact block for the portfolio: per app, how many competitors and who grows fastest."""
    meta = comp["meta"]
    rows = []
    for g in comp["groups"]:
        apps = g["apps"]
        own = next((a for a in apps if a.get("role") == "own"), {})
        rivals = [a for a in apps if a.get("role") == "competitor"]
        fast = max((a for a in rivals if a.get("reviews_28d") is not None), key=lambda a: a["reviews_28d"], default=None)
        rows.append({"app_id": g["app_id"], "name": g.get("name"), "competitors": len(rivals),
                     "own_share_28d": own.get("growth_share_28d"), "own_reviews_28d": own.get("reviews_28d"),
                     "top_competitor": {"id": fast["id"], "name": fast.get("name"), "reviews_28d": fast["reviews_28d"],
                                        "share_28d": fast.get("growth_share_28d")} if fast else None,
                     "outpacing": any(str(s).endswith("/competitor_outpacing") for s in g.get("signals") or [])})
    return {"meta": {k: meta.get(k) for k in ("as_of", "snapshot_days", "first_snapshot", "countries", "primary_country", "demo", "proxies")},
            "stale": comp["stale"], "errors": len(meta.get("errors") or []), "groups": rows}


def build_model(home: Path, as_of_arg: str | None = None) -> dict:
    cfg = load_config(home)
    apps = read_json(home / "raw" / "apps.json", None)
    if apps is None:
        raise TrackerError(f"no data in {home}: raw/apps.json is missing.",
                           "Run `tracker.py fetch` first (or `tracker.py demo` for a preview).")
    state = read_json(home / "state.json", {}) or {}
    last_fetch = state.get("last_fetch") or {}
    by_id = {a["id"]: a for a in apps}
    by_sku = {a["sku"]: a["id"] for a in apps if a.get("sku")}
    fx = FX(home, cfg.get("base_currency") or "USD")

    # ---- sales days: ok files, empty markers, pending markers
    sales_dir = home / "raw" / "sales" / "daily"
    status = sales_status(home)
    files = {p.name[:10]: p for p in sales_dir.glob("*.tsv.gz")} if sales_dir.is_dir() else {}
    known = set(files) | {d for d, s in status.items() if s == "empty"}
    pending = sorted(d for d, s in status.items() if s == "pending" and d not in files)
    sales_available = bool(files)
    web = {a["id"]: (read_json(home / "raw" / "web" / f"{a['id']}.json", {}) or {}).get("measures", {}) for a in apps}
    web_days = sorted({d for m in web.values() for d in (m.get("downloads") or {})})
    # Sales reports win for volume; App Analytics fills it when no report exists, and always supplies the funnel.
    volume_source = "sales" if sales_available else ("analytics" if web_days else None)
    if volume_source == "analytics":
        known = set(web_days)
    if known:
        first_day, last_day = parse_day(min(known)), parse_day(max(known))
    else:
        last_day = today_pt() - timedelta(days=1)
        first_day = last_day - timedelta(days=89)
    max_day = last_day  # the last day with known data; later days are unknown, never zero
    if as_of_arg is not None:  # '' is an invalid date, not "no value"
        try:
            last_day = parse_day(as_of_arg)
        except ValueError:
            raise TrackerError(f"--as-of '{as_of_arg}' is not a YYYY-MM-DD date.", f"Pass a date between {first_day} and {max_day}, or omit --as-of.")
        if last_day < first_day:
            raise TrackerError(f"--as-of {as_of_arg} is before the first sales day {first_day}.",
                               f"Pass a date between {first_day} and {max_day}.")
        if last_day > max_day:
            raise TrackerError(f"--as-of {as_of_arg} is after the last day with data, {max_day}; later days are not published yet.",
                               f"Pass a date between {first_day} and {max_day}, or omit --as-of.")
    # Review windows follow the calendar, not the sales history, so stale sales never freeze them.
    review_end = last_day if as_of_arg is not None else max(last_day, today_pt() - timedelta(days=1))
    days = day_range(first_day, last_day)
    idx = {d.isoformat(): i for i, d in enumerate(days)}
    n = len(days)
    day_known = [d.isoformat() in known for d in days]

    daily = defaultdict(lambda: [new_day() for _ in range(n)])
    country = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: [0.0, 0.0])))
    device = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    product = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: [0.0, 0.0])))
    first_seen = defaultdict(dict)
    unattributed = defaultdict(float)
    parse_errors = []
    for key, path in sorted(files.items()):
        if key not in idx:
            continue
        i = idx[key]
        try:
            rows = read_tsv_gz(path)
        except (OSError, EOFError, ValueError, gzip.BadGzipFile, csv.Error) as exc:
            parse_errors.append(f"{path.name}: {exc}")
            day_known[i] = False  # a corrupt day is unknown, never zero
            continue
        for row in rows:
            ptype = pick(row, "Product Type Identifier")
            cat = sales_category(ptype)
            units = to_float(pick(row, "Units"))
            per_unit = to_float(pick(row, "Developer Proceeds", "Developer Proceeds (per unit)"))
            apple_id = pick(row, "Apple Identifier")
            parent, sku = pick(row, "Parent Identifier"), pick(row, "SKU")
            aid = apple_id if apple_id in by_id else by_sku.get(parent) or by_sku.get(sku)
            if aid is None:
                unattributed[pick(row, "Title") or apple_id] += units
                aid = "_other"
            rec = daily[aid][i]
            amount = fx.convert(units * per_unit, pick(row, "Currency of Proceeds"))
            amount = amount or 0.0
            credit = pick(row, "CMB").upper() == "CMB-C"
            if units < 0 and not credit:
                rec["refunds"] += -units
            elif units > 0:
                if cat == "download":
                    rec["downloads"] += units
                elif cat == "redownload":
                    rec["redownloads"] += units
                elif cat == "update":
                    rec["updates"] += units
                elif cat == "iap":
                    rec["iap"] += units
                elif cat == "subscription":
                    rec["subs"] += units
                elif cat == "restore":
                    rec["restores"] += units
                if pick(row, "Promo Code"):
                    rec["promo"] += units
            rec["proceeds"] += amount
            if cat in ("iap", "subscription"):
                rec["proceeds_iap"] += amount
            else:
                rec["proceeds_app"] += amount
            cc = pick(row, "Country Code") or "??"
            if cat == "download" and units > 0:
                country[aid][i][cc][0] += units
                device[aid][i][pick(row, "Device") or "Unknown"] += units
            country[aid][i][cc][1] += amount
            if cat in ("iap", "subscription", "restore"):
                p = product[aid][i][pick(row, "Title") or pick(row, "SKU") or "?"]
                p[0] += units
                p[1] += amount
            version = pick(row, "Version")
            if version and cat in ("download", "redownload") and units > 0:
                prev = first_seen[aid].get(version)
                if prev is None or key < prev:
                    first_seen[aid][version] = key

    web_metrics = ["impressions", "page_views"] + (["downloads", "redownloads", "updates", "proceeds", "iap"] if volume_source == "analytics" else [])
    for aid, measures in web.items():
        for metric in web_metrics:
            for day, value in (measures.get(metric) or {}).items():
                i = idx.get(day)
                if i is not None:
                    daily[aid][i][metric] += float(value or 0)
                    if metric == "proceeds":
                        daily[aid][i]["proceeds_app"] += float(value or 0)  # App Analytics has no app/IAP split
    funnel_available = any((m.get("impressions") or {}) for m in web.values())

    # ---- reviews and snapshots
    reviews = {}
    for a in apps:
        store = read_json(home / "raw" / "reviews" / f"{a['id']}.json", {}) or {}
        reviews[a["id"]] = sorted(store.values(), key=lambda r: r.get("created") or "", reverse=True)
    snapshots = []
    for p in sorted((home / "snapshots").glob("*.json")):
        s = read_json(p, {}) or {}
        if s.get("date"):
            snapshots.append(s)
    prev_snap = snapshots[-2] if len(snapshots) > 1 else None

    def window_bounds(w):
        if w == "all":
            return 0, n - 1
        return max(0, n - w), n - 1

    def prev_bounds(w):
        if w == "all":
            return None
        lo, hi = n - 2 * w, n - w - 1
        if lo < 0 or not all(day_known[lo:hi + 1]):
            return None
        return lo, hi

    def sum_series(series, lo, hi, metric):
        return sum(series[i][metric] for i in range(lo, hi + 1))

    def review_window(rs, w, back=0):
        if w == "all":
            if back:
                return None, None
            sel = rs
        else:
            hi_d = review_end - timedelta(days=back * w)
            lo_d = (hi_d - timedelta(days=w - 1)).isoformat()
            sel = [r for r in rs if lo_d <= (r.get("created") or "")[:10] <= hi_d.isoformat()]
        avg = round(sum(r["rating"] for r in sel) / len(sel), 2) if sel else None
        return len(sel), avg

    def aggregate(ids):
        series = [new_day() for _ in range(n)]
        for aid in ids:
            for i, rec in enumerate(daily.get(aid, [])):
                for m in METRICS:
                    series[i][m] += rec[m]
        return series

    def breakdown(ids, lo, hi):
        cty, dev, prod = defaultdict(lambda: [0.0, 0.0]), defaultdict(float), defaultdict(lambda: [0.0, 0.0])
        for aid in ids:
            for i in range(lo, hi + 1):
                for cc, (u, p) in country[aid].get(i, {}).items():
                    cty[cc][0] += u
                    cty[cc][1] += p
                for dv, u in device[aid].get(i, {}).items():
                    dev[dv] += u
                for t, (u, p) in product[aid].get(i, {}).items():
                    prod[t][0] += u
                    prod[t][1] += p
        countries = sorted(([cc, round(v[0]), round(v[1], 2)] for cc, v in cty.items()), key=lambda x: (-x[1], -x[2]))[:20]
        devices = sorted(([k, round(v)] for k, v in dev.items() if v), key=lambda x: -x[1])
        products = sorted(([k, round(v[0]), round(v[1], 2)] for k, v in prod.items()), key=lambda x: -x[2])[:20]
        return countries, devices, products

    def windows_for(ids, rs):
        out = {}
        series = aggregate(ids)
        for w in WINDOWS + ["all"]:
            lo, hi = window_bounds(w)
            cur ={m: round(sum_series(series, lo, hi, m), 2) for m in METRICS}
            pb = prev_bounds(w) if all(day_known[lo:hi + 1]) else None  # no delta against an unknown day
            prev = {m: round(sum_series(series, pb[0], pb[1], m), 2) for m in METRICS} if pb else None
            cnt, avg = review_window(rs, w)
            pcnt, pavg = review_window(rs, w, back=1)
            countries, devices, products = breakdown(ids, lo, hi)
            out[str(w)] = {
                "from": days[lo].isoformat(), "to": days[hi].isoformat(), "days": hi - lo + 1,
                "known_days": sum(day_known[lo:hi + 1]), "complete": all(day_known[lo:hi + 1]), "kpis": cur, "prev": prev,
                "reviews": {"count": cnt, "avg": avg, "prev_count": pcnt, "prev_avg": pavg},
                "countries": countries, "devices": devices, "products": products,
            }
        return out

    def review_stats(rs):
        dist = {str(k): 0 for k in range(1, 6)}
        for r in rs:
            if r.get("rating") in (1, 2, 3, 4, 5):
                dist[str(r["rating"])] += 1
        total = sum(dist.values())
        avg = round(sum(int(k) * v for k, v in dist.items()) / total, 2) if total else None
        unanswered = [r for r in rs if not r.get("response")]
        monthly = defaultdict(lambda: [0, 0])
        for r in rs:
            m = (r.get("created") or "")[:7]
            if m and r.get("rating"):
                monthly[m][0] += 1
                monthly[m][1] += r["rating"]
        months = [[m, c, round(s / c, 2)] for m, (c, s) in sorted(monthly.items())]
        daily_new = [0] * n
        for r in rs:
            i = idx.get((r.get("created") or "")[:10])
            if i is not None:
                daily_new[i] += 1
        return {"count": total, "avg": avg, "dist": dist, "unanswered": len(unanswered),
                "unanswered_negative": sum(1 for r in unanswered if (r.get("rating") or 5) <= 3),
                "monthly": months, "daily_new": daily_new}

    # ---- stable color slots: rank by all-time downloads + proceeds
    def weight(aid):
        s = daily.get(aid)
        return (sum(r["downloads"] for r in s) + sum(abs(r["proceeds"]) for r in s)) if s else 0
    order = sorted(by_id, key=lambda a: (-weight(a), by_id[a]["name"].lower()))
    slot = {aid: (i + 1 if i < 7 else 0) for i, aid in enumerate(order)}

    model_apps, all_signals = [], []
    for aid in order:
        a = by_id[aid]
        # Newest snapshot that actually holds each source: a failed lookup today must not
        # turn a live app into "not listed" or erase its ratings.
        def newest(key):
            for s in reversed(snapshots):
                v = ((s.get("apps") or {}).get(aid) or {}).get(key)
                if v:
                    return v, s["date"]
            return {}, None
        store, store_date = newest("store")
        ratings, _ = newest("ratings")
        products, _ = newest("products")
        rejection, _ = newest("rejection")
        series = daily.get(aid) or [new_day() for _ in range(n)]
        if not store.get("listed") and sum(r["downloads"] + r["redownloads"] for r in series[-28:]) > 0:
            store = dict(store, listed=True, listed_from="sales")  # it sells, so it is on the store
        rs = reviews.get(aid, [])
        versions = read_json(home / "raw" / "versions" / f"{aid}.json", []) or []
        for v in versions:
            v["first_seen"] = first_seen[aid].get(v.get("version"))
        rating_hist = []
        for s in snapshots:
            r = ((s.get("apps") or {}).get(aid) or {}).get("ratings")
            if r and r.get("listed"):
                rating_hist.append([s["date"], r.get("average"), r.get("count")])
        kind = store.get("kind") or ""
        platform = "Mac" if kind == "mac-software" or any(v.get("platform") == "MAC_OS" for v in versions[:1]) else (
            "iOS" if store or versions else "Unknown")
        app_model = {
            "id": aid, "name": a["name"], "sku": a.get("sku"), "bundle_id": a.get("bundle_id"),
            "slot": slot[aid], "platform": platform, "listed": bool(store.get("listed")), "store_date": store_date,
            "store": store, "ratings": ratings, "products": products or [], "rejection": rejection or None,
            "funnel_available": funnel_available, "rating_history": rating_hist,
            "series": {m: [round(r[m], 2) for r in series] for m in METRICS},
            "windows": windows_for([aid], rs), "reviews": review_stats(rs),
            "review_list": rs[:1500], "versions": versions,
        }
        prev_price = (((prev_snap or {}).get("apps") or {}).get(aid) or {}).get("store", {}).get("formattedPrice") if prev_snap else None
        app_model["signals"] = app_signals(app_model, days, day_known, volume_source is not None, prev_price, fx.base if volume_source == "sales" else "(as reported)")
        all_signals.extend(app_model["signals"])
        model_apps.append(app_model)

    comp, comp_gaps = load_competitors(home, set(by_id))
    if comp:
        groups = {str(g["app_id"]): g for g in comp["groups"]}
        for am in model_apps:
            g = groups.get(am["id"])
            if g:
                am["competitors"] = g
                extra = [x for x in comp["signals"] if x["scope"] == am["id"]]
                am["signals"].extend(extra)
                all_signals.extend(extra)

    ids = list(by_id) + (["_other"] if "_other" in daily else [])
    portfolio_reviews = sorted((r for rs in reviews.values() for r in rs), key=lambda r: r.get("created") or "", reverse=True)
    portfolio = {
        "series": {m: [round(r[m], 2) for r in aggregate(ids)] for m in METRICS},
        "windows": windows_for(ids, portfolio_reviews), "reviews": review_stats(portfolio_reviews),
    }
    if "_other" in daily:
        portfolio["unattributed"] = {
            "series": {m: [round(r[m], 2) for r in daily["_other"]] for m in METRICS},
            "titles": {k: round(v, 2) for k, v in sorted(unattributed.items(), key=lambda kv: -kv[1])[:10]},
        }
    portfolio["signals"] = portfolio_signals(model_apps, portfolio, sales_available, last_fetch, cfg, volume_source, max_day.isoformat())
    all_signals = portfolio["signals"] + all_signals

    gaps = data_gaps(sales_available, last_fetch, fx, pending, parse_errors, model_apps, volume_source, funnel_available) + comp_gaps
    insights_dir = home / "insights"
    runs = []
    for p in sorted((home / "history").glob("*.html")):
        ins = read_json(insights_dir / f"{p.stem}.json", None, INSIGHTS_FIX, 2) if (insights_dir / f"{p.stem}.json").exists() else None
        runs.append({"date": p.stem, "file": p.name, "headline": (ins or {}).get("headline") if isinstance(ins, dict) else None})
    model = {
        "meta": {
            "tool": "appstore-tracker", "version": VERSION, "generated_at": datetime.now().isoformat(timespec="seconds"),
            "run_date": today_local().isoformat(), "as_of": days[-1].isoformat() if days else None,
            "first_day": days[0].isoformat() if days else None, "data_dir": str(home),
            "base_currency": fx.base, "fx": fx.meta(), "sales_available": sales_available,
            "volume_source": volume_source, "funnel_available": funnel_available,
            "pending_days": pending, "known_days": sum(day_known), "total_days": n, "demo": bool(cfg.get("demo")),
            "last_fetch": {k: last_fetch.get(k) for k in ("date", "started", "finished", "apps", "partial", "sales")},
        },
        "days": [d.isoformat() for d in days], "known": [1 if k else 0 for k in day_known],
        "apps": model_apps, "portfolio": portfolio, "signals": all_signals, "gaps": gaps, "runs": runs,
    }
    if comp:  # only when competitor data exists, so a run without it is unchanged
        model["competitors"] = competitor_overview(comp)
    return model


def sig(scope, kind, severity, title, detail, **metrics) -> dict:
    sid = f"{scope}/{kind}"
    return {"id": sid, "scope": scope, "kind": kind, "severity": severity, "title": title, "detail": detail,
            "metrics": {k: v for k, v in metrics.items() if v is not None}}


def trend_signal(scope, name, w, metric, label, cur, prev, unit_floor, money=False, base=""):
    if prev is None or cur is None:
        return None
    delta = cur - prev
    change = pct(cur, prev)
    low = (cur + prev) < (4 * unit_floor)
    if abs(delta) < unit_floor or change is None or abs(change) < 20:
        severity = "info"
    else:
        severity = "good" if delta > 0 else "warning"
    if low and severity != "info":
        severity = "info"
    fmt = (lambda v: f"{v:,.2f} {base}") if money else (lambda v: f"{v:,.0f}")
    word = "up" if delta > 0 else ("down" if delta < 0 else "flat")
    if delta == 0:
        detail = f"{name}: {label} flat — {fmt(cur)} in the last {w} days and in the previous {w} days."
    else:
        detail = f"{name}: {label} {word} {fmt(abs(delta))} ({'new' if change is None else f'{change:+.1f}%'}) — last {w} days {fmt(cur)} vs previous {w} days {fmt(prev)}."
    if low:
        detail += " Low volume: treat the change as noise."
    return sig(scope, f"trend_{metric}_{w}d", severity, f"{label.capitalize()} {word} over {w} days", detail,
               current=round(cur, 2), previous=round(prev, 2), change_pct=change, low_volume=low)


def app_signals(app, days, day_known, sales_available, prev_price, base) -> list[dict]:
    out, aid, name = [], app["id"], app["name"]
    w28, w90, w7 = app["windows"]["28"], app["windows"]["90"], app["windows"]["7"]
    rv = app["reviews"]
    store = app["store"]
    if not app["listed"]:
        latest = max(app["versions"], key=lambda v: v.get("created") or "", default=None)
        state = (latest or {}).get("state") or "unknown"
        severity = "warning" if state in REJECTED_STATES or state == "DEVELOPER_REJECTED" else "info"
        where = f" Latest version {latest.get('version')} ({latest.get('platform')}) is {state}, created {latest.get('created')}." if latest else ""
        rej = app.get("rejection") or {}
        if rej.get("guidelines"):
            where += f" App Review ({rej.get('date')}): {'; '.join(rej['guidelines'])}."
            if rej.get("spam"):
                severity = "critical"
                where += " A 4.3 spam rejection warns that repeat submissions of similar apps risk extended review and account removal."
        out.append(sig(aid, "not_listed", severity, "Not on the public App Store" + (f" ({state})" if latest else ""),
                       f"{name} has no public store listing in the storefronts checked, so it cannot sell.{where}",
                       version_state=state, version=(latest or {}).get("version"), created=(latest or {}).get("created"),
                       guidelines=rej.get("guidelines"), spam=rej.get("spam")))
    funnel = app.get("funnel_available")
    if funnel and w28["prev"] is not None:
        k, pv = w28["kpis"], w28["prev"]
        s = trend_signal(aid, name, 28, "impressions", "impressions", k["impressions"], pv["impressions"], 100)
        if s and (k["impressions"] + pv["impressions"]) > 0:
            out.append(s)
        if k["page_views"] >= 30 and pv["page_views"] >= 30:
            cr, pcr = k["downloads"] / k["page_views"], pv["downloads"] / pv["page_views"]
            if cr > 1:  # installs straight from search results skip the product page
                out.append(sig(aid, "page_conversion_28d", "info", "Product page conversion not measurable (28 days)",
                               f"{name}: {k['downloads']:.0f} first-time downloads vs {k['page_views']:.0f} product page views in 28 days ({pv['downloads']:.0f} vs {pv['page_views']:.0f} in the previous 28). More downloads than page views means many installs came without a product page view, so page conversion is not a share of page views here.",
                               downloads=k["downloads"], page_views=k["page_views"], previous_downloads=pv["downloads"], previous_page_views=pv["page_views"]))
            elif pcr > 1:
                out.append(sig(aid, "page_conversion_28d", "info", "Product page conversion (28 days)",
                               f"{name}: {cr:.1%} of product page views became first-time downloads ({k['page_views']:.0f} page views). No comparison: the previous 28 days had more downloads than page views ({pv['downloads']:.0f} vs {pv['page_views']:.0f}).",
                               rate=round(cr, 4), page_views=k["page_views"]))
            else:
                change = pct(cr, pcr)
                sev = "info" if change is None or abs(change) < 20 else ("good" if cr > pcr else "warning")
                out.append(sig(aid, "page_conversion_28d", sev, "Product page conversion (28 days)",
                               f"{name}: {cr:.1%} of product page views became first-time downloads vs {pcr:.1%} in the previous 28 days ({k['page_views']:.0f} vs {pv['page_views']:.0f} page views).",
                               rate=round(cr, 4), previous=round(pcr, 4), change_pct=change, page_views=k["page_views"]))
    if funnel and w28["kpis"]["impressions"] >= 1000:
        k = w28["kpis"]
        ttr = k["page_views"] / k["impressions"]
        if ttr < 0.03:
            out.append(sig(aid, "low_tap_through_28d", "warning", "Few searchers open the product page",
                           f"{name}: {k['impressions']:.0f} impressions but {k['page_views']:.0f} product page views ({ttr:.1%}) in 28 days. Icon, name, subtitle and first screenshots decide this tap.",
                           impressions=k["impressions"], page_views=k["page_views"], tap_through=round(ttr, 4)))
    if sales_available:
        for w, win in ((7, w7), (28, w28)):
            if win["prev"] and win["complete"]:
                s = trend_signal(aid, name, w, "downloads", "downloads", win["kpis"]["downloads"], win["prev"]["downloads"], 5)
                if s and (win["kpis"]["downloads"] + win["prev"]["downloads"]) > 0:
                    out.append(s)
        if w28["prev"] and w28["complete"] and (w28["kpis"]["proceeds"] or w28["prev"]["proceeds"]):
            s = trend_signal(aid, name, 28, "proceeds", "proceeds", w28["kpis"]["proceeds"], w28["prev"]["proceeds"], 5, True, base)
            if s:
                out.append(s)
        k = w28["kpis"]
        if app["listed"] and k["downloads"] == 0 and w28["known_days"] >= 21:
            out.append(sig(aid, "dormant", "warning", "No new downloads in 28 days",
                           f"{name} is listed but had 0 first-time downloads from {w28['from']} to {w28['to']}.",
                           redownloads=k["redownloads"], updates=k["updates"]))
        if k["downloads"] > 0:
            arpd = k["proceeds"] / k["downloads"]
            attach = (k["iap"] + k["subs"]) / k["downloads"]
            out.append(sig(aid, "monetization_28d", "info", "Revenue per download (28 days)",
                           f"{name}: {arpd:,.2f} {base} proceeds per first-time download; {attach:.2f} in-app purchases or subscriptions per download.",
                           proceeds_per_download=round(arpd, 3), purchases_per_download=round(attach, 3),
                           downloads=k["downloads"], proceeds=k["proceeds"]))
        k90 = w90["kpis"]
        gross = k90["downloads"] + k90["iap"] + k90["subs"]
        if k90["refunds"] >= 3 and gross and k90["refunds"] / gross >= 0.05:
            out.append(sig(aid, "refund_rate_90d", "warning", "High refund rate (90 days)",
                           f"{name}: {k90['refunds']:.0f} refunded units vs {gross:.0f} paid or free units ({k90['refunds'] / gross:.1%}).",
                           refunds=k90["refunds"], units=gross, rate=round(k90["refunds"] / gross, 3)))
        countries = w90["countries"]
        total = sum(c[1] for c in countries)
        if total >= 10 and countries:
            top = countries[0]
            if top[1] / total >= 0.4:
                out.append(sig(aid, "country_concentration_90d", "info", f"{top[0]} drives {top[1] / total:.0%} of downloads",
                               f"{name}: {top[0]} accounts for {top[1]:.0f} of {total:.0f} first-time downloads over 90 days.",
                               country=top[0], share=round(top[1] / total, 3)))
            langs = {l.upper() for l in (store.get("languageCodesISO2A") or [])}
            if langs:
                for cc, units, _ in countries[:5]:
                    need = COUNTRY_LANGS.get(cc)
                    if need and units / total >= 0.08 and not (set(need) & langs):
                        out.append(sig(aid, f"localization_gap_{cc}", "warning", f"Not localized for {cc}",
                                       f"{name}: {cc} gives {units:.0f} of {total:.0f} downloads ({units / total:.0%}) over 90 days, but the listing supports {', '.join(sorted(langs))} and not {'/'.join(need)}.",
                                       country=cc, share=round(units / total, 3), languages=sorted(langs)))
        series = app["series"]["downloads"]
        n = len(series)
        for i in range(max(28, n - 28), n):
            base = series[i - 28:i]
            if len(base) < 28 or not all(day_known[i - 28:i]):
                continue
            mean = statistics.fmean(base)
            sd = statistics.pstdev(base)
            v = series[i]
            if v >= 5 and v > mean + 3 * max(sd, 1):
                out.append(sig(aid, f"spike_{days[i].isoformat()}", "good", f"Download spike on {days[i].isoformat()}",
                               f"{name}: {v:.0f} downloads on {days[i].isoformat()} vs a 28-day average of {mean:.1f}.",
                               value=v, mean=round(mean, 2)))
        keys = [d.isoformat() for d in days]
        for v in app["versions"]:
            fs = v.get("first_seen")
            if not fs or fs not in keys:
                continue
            i = keys.index(fs)
            if i < 7 or i + 7 > n or not all(day_known[i - 7:i + 7]):
                continue
            before = sum(series[i - 7:i]) / 7
            after = sum(series[i:i + 7]) / 7
            if before + after == 0:
                continue
            change = pct(after, before)
            sev = "info" if change is None or abs(change) < 20 or abs(after - before) < 1 else ("good" if after > before else "warning")
            out.append(sig(aid, f"release_{v.get('version')}", sev, f"Version {v.get('version')}: downloads {'up' if after >= before else 'down'} after release",
                           f"{name}: {before:.1f}/day in the 7 days before {v.get('version')} first appeared in sales ({fs}) vs {after:.1f}/day in the 7 days after.",
                           before_per_day=round(before, 2), after_per_day=round(after, 2), change_pct=change))
        if w90["kpis"]["downloads"] >= 300 and (w90["reviews"]["count"] or 0) <= 2:
            out.append(sig(aid, "few_reviews_90d", "info", "Few reviews for the download volume",
                           f"{name}: {w90['kpis']['downloads']:.0f} downloads but {w90['reviews']['count']} written reviews in 90 days.",
                           downloads=w90["kpis"]["downloads"], reviews=w90["reviews"]["count"]))
    blocked = [x for x in app.get("products") or [] if x.get("state") in BLOCKED_PRODUCT_STATES]
    if blocked:
        names = ", ".join(f"{x.get('name')} ({x.get('state')})" for x in blocked[:6])
        out.append(sig(aid, "products_not_sellable", "warning" if app["listed"] else "info",
                       f"{len(blocked)} in-app product{'s' if len(blocked) > 1 else ''} cannot be bought",
                       f"{name}: {names}. A product that is not approved is invisible to buyers.",
                       products=[x.get("product_id") for x in blocked], states=sorted({x.get("state") for x in blocked})))
    if rv["unanswered_negative"]:
        out.append(sig(aid, "unanswered_negative_reviews", "warning", f"{rv['unanswered_negative']} unanswered review(s) of 3 stars or less",
                       f"{name}: {rv['unanswered_negative']} of {rv['unanswered']} unanswered reviews are 3 stars or less.",
                       unanswered=rv["unanswered"], unanswered_negative=rv["unanswered_negative"]))
    elif rv["unanswered"]:
        many = rv["unanswered"] > 1
        out.append(sig(aid, "unanswered_reviews", "info", f"{rv['unanswered']} unanswered review{'s' if many else ''}",
                       f"{name}: {rv['unanswered']} review{'s have' if many else ' has'} no developer response.", unanswered=rv["unanswered"]))
    recent = w90["reviews"]
    if rv["avg"] is not None and recent["count"] and recent["count"] >= 3 and recent["avg"] is not None and recent["avg"] <= rv["avg"] - 0.5:
        out.append(sig(aid, "rating_drop_90d", "warning", "Recent reviews rate lower",
                       f"{name}: reviews in the last 90 days average {recent['avg']:.2f}★ vs {rv['avg']:.2f}★ all time ({recent['count']} recent).",
                       recent_avg=recent["avg"], all_time_avg=rv["avg"], recent_count=recent["count"]))
    ratings = app["ratings"]
    if ratings.get("listed") and not ratings.get("count") and rv["count"]:
        out.append(sig(aid, "ratings_hidden", "info", "Public rating not shown",
                       f"{name}: the public App Store shows no rating count, although App Store Connect lists {rv['count']} written review(s). Apple hides ratings below a threshold, and Mac App Store ratings are not exposed by the public lookup.",
                       reviews=rv["count"]))
    released = (store.get("currentVersionReleaseDate") or "")[:10]
    if released:
        age = (parse_day(days[-1].isoformat()) - parse_day(released)).days if days else 0
        if age > 120:
            out.append(sig(aid, "stale_release", "info", f"Last update {age} days ago",
                           f"{name}: version {store.get('version')} was released on {released}.", days_since_release=age))
    if prev_price and store.get("formattedPrice") and prev_price != store.get("formattedPrice"):
        out.append(sig(aid, "price_change", "info", "Price changed",
                       f"{name}: price moved from {prev_price} to {store.get('formattedPrice')} (US storefront).",
                       old=prev_price, new=store.get("formattedPrice")))
    return out


def portfolio_signals(apps, portfolio, sales_available, last_fetch, cfg, volume_source=None, newest_day=None) -> list[dict]:
    out = []
    if not sales_available:
        reason = ((last_fetch.get("sales") or {}).get("error_kind") or (last_fetch.get("sales") or {}).get("state") or "not fetched")
        if volume_source == "analytics":
            out.append(sig("portfolio", "sales_unavailable", "warning", "No Sales reports: volume comes from App Analytics",
                           f"Daily Sales and Trends reports are not available ({reason}). Downloads and proceeds come from App Analytics instead, without country, device, refund or product detail, and its proceeds carry no currency field.",
                           reason=reason))
        else:
            out.append(sig("portfolio", "sales_unavailable", "critical", "No sales data",
                           f"Daily Sales and Trends reports are not available ({reason}), and no App Analytics data was collected. Downloads, proceeds and countries cannot be analysed.",
                           reason=reason))
            return out
    w7, w28 = portfolio["windows"]["7"], portfolio["windows"]["28"]
    sales = last_fetch.get("sales") or {}
    # Measure staleness from the newest report on disk, not the --as-of day, so a back-dated run does not warn.
    newest = newest_day or w7["to"]
    lag = (today_pt() - parse_day(newest)).days
    if sales_available and (sales.get("error_kind") or lag > PENDING_DAYS + 1):
        why = sales.get("error_kind") or "no new reports"
        out.append(sig("portfolio", "sales_stale", "critical" if sales.get("error_kind") else "warning",
                       f"Sales data stops on {newest}",
                       f"The newest sales report on disk is {newest}, {lag} days ago ({why} in the last fetch). Recent trends are missing, not flat.",
                       as_of=newest, lag_days=lag, reason=why))
    for w, win in ((7, w7), (28, w28)):
        if win["prev"] and win["complete"]:
            s = trend_signal("portfolio", "All apps", w, "downloads", "downloads", win["kpis"]["downloads"], win["prev"]["downloads"], 5)
            if s:
                out.append(s)
    cur = (cfg.get("base_currency") or "USD") if sales_available else "(as reported)"
    if w28["prev"] and w28["complete"]:
        s = trend_signal("portfolio", "All apps", 28, "proceeds", "proceeds", w28["kpis"]["proceeds"], w28["prev"]["proceeds"], 5, True, cur)
        if s:
            out.append(s)
    totals = [(a["name"], a["windows"]["90"]["kpis"]["proceeds"]) for a in apps]
    total = sum(max(0, t) for _, t in totals)
    if total > 0:
        name, top = max(totals, key=lambda x: x[1])
        if top / total >= 0.7 and len(apps) > 1:
            out.append(sig("portfolio", "revenue_concentration_90d", "info", f"{name} earns {top / total:.0%} of proceeds",
                           f"{name} brought {top:,.2f} of {total:,.2f} {cur} proceeds over 90 days.",
                           app=name, share=round(top / total, 3)))
    dormant = [a["name"] for a in apps if any(s["kind"] == "dormant" for s in a["signals"])]
    if dormant:
        out.append(sig("portfolio", "dormant_apps", "warning", f"{len(dormant)} listed app(s) without downloads",
                       "No first-time downloads in 28 days: " + ", ".join(dormant) + ".", apps=dormant))
    return out


def data_gaps(sales_available, last_fetch, fx, pending, parse_errors, apps, volume_source=None, funnel_available=False) -> list[dict]:
    gaps = []
    for e in last_fetch.get("errors") or []:
        gaps.append({"source": e.get("source"), "app": e.get("app"), "kind": e.get("kind"),
                     "message": e.get("message"), "fix": e.get("fix")})
    if not sales_available and not any(g["source"] == "sales" for g in gaps):
        gaps.append({"source": "sales", "kind": "missing", "message": "no daily sales reports in the data dir",
                     "fix": "Run `tracker.py fetch` with a key that has the Sales, Finance or Admin role."})
    if pending:
        gaps.append({"source": "sales", "kind": "pending", "message": f"{len(pending)} recent day(s) not published by Apple yet: {', '.join(pending)}",
                     "fix": "The next `fetch` retries them."})
    if fx.unconverted:
        gaps.append({"source": "fx", "kind": "unconverted", "message": "proceeds in " + ", ".join(sorted(fx.unconverted)) + " were not converted (no rate)",
                     "fix": "Rerun `fetch` to refresh exchange rates."})
    for err in parse_errors:
        gaps.append({"source": "sales", "kind": "parse", "message": err, "fix": "Delete the file; the next `fetch` downloads it again."})
    if not funnel_available and not any(g["source"] == "analytics" for g in gaps):
        gaps.append({"source": "analytics", "kind": "not_collected",
                     "message": "App Analytics (impressions, product page views, conversion) was not collected",
                     "fix": "Ask the user to run `! asc web auth login`, then fetch again; until then make no conversion claims."})
    return gaps


# --------------------------------------------------------------------------
# Digest for the agent and insights validation
# --------------------------------------------------------------------------


def trim(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def make_digest(model: dict) -> dict:
    def kp(win):
        k, p = win["kpis"], win["prev"]
        keep = ("downloads", "redownloads", "updates", "iap", "subs", "refunds", "proceeds", "proceeds_app", "proceeds_iap", "impressions", "page_views")
        out = {m: k[m] for m in keep}
        if p:
            out["prev"] = {m: p[m] for m in keep}
        out["reviews"] = win["reviews"]
        out["range"] = [win["from"], win["to"]]
        out["known_days"] = f"{win['known_days']}/{win['days']}"  # under full: some days unknown, not zero
        return out

    apps = []
    for a in model["apps"]:
        rs = a["review_list"]
        pick_ids, picked = set(), []

        def add(r, why):
            # Every unanswered review (up to 60) so reply drafts can cover them all; 6 recent others.
            limit = 60 if why.startswith("unanswered") else 6
            if r["id"] in pick_ids or sum(1 for x in picked if x["why"].startswith("unanswered") == why.startswith("unanswered")) >= limit:
                return
            pick_ids.add(r["id"])
            picked.append({"id": r["id"], "why": why, "rating": r.get("rating"), "date": (r.get("created") or "")[:10],
                           "territory": r.get("territory"), "title": trim(r.get("title"), 100),
                           "body": trim(r.get("body"), 300), "answered": bool(r.get("response"))})
        for r in rs:
            if not r.get("response") and (r.get("rating") or 5) <= 3:
                add(r, "unanswered_negative")
        for r in rs:
            if not r.get("response"):
                add(r, "unanswered")
        for r in rs[:6]:
            add(r, "recent")
        apps.append({
            "id": a["id"], "name": a["name"], "platform": a["platform"], "listed": a["listed"],
            "price": a["store"].get("formattedPrice"), "genre": a["store"].get("primaryGenreName"),
            "store_version": a["store"].get("version"), "released": (a["store"].get("currentVersionReleaseDate") or "")[:10] or None,
            "languages": a["store"].get("languageCodesISO2A"),
            "public_ratings": {k: a["ratings"].get(k) for k in ("listed", "average", "count", "countries")} if a["ratings"] else None,
            "kpis_7d": kp(a["windows"]["7"]), "kpis_28d": kp(a["windows"]["28"]), "kpis_90d": kp(a["windows"]["90"]),
            "top_countries_90d": a["windows"]["90"]["countries"][:6], "devices_90d": a["windows"]["90"]["devices"],
            "products_90d": a["windows"]["90"]["products"][:6],
            "store_products": [{k: x.get(k) for k in ("name", "product_id", "kind", "type", "state")} for x in a["products"]],
            "reviews": {k: a["reviews"][k] for k in ("count", "avg", "dist", "unanswered", "unanswered_negative")},
            "versions": [{k: v.get(k) for k in ("version", "platform", "state", "created", "first_seen")} for v in a["versions"][:5]],
            "rejection": a.get("rejection"),
            "signals": [s["id"] for s in a["signals"]], "review_sample": picked,
            **({"competitors": a["competitors"]} if a.get("competitors") else {}),
        })
    p = model["portfolio"]
    return {
        "meta": model["meta"], "gaps": model["gaps"],
        "portfolio": {"kpis_7d": kp(p["windows"]["7"]), "kpis_28d": kp(p["windows"]["28"]), "kpis_90d": kp(p["windows"]["90"]),
                      "top_countries_90d": p["windows"]["90"]["countries"][:8], "reviews": {k: p["reviews"][k] for k in ("count", "avg", "dist", "unanswered", "unanswered_negative")}},
        "signals": [{k: s[k] for k in ("id", "severity", "title", "detail", "metrics")} for s in model["signals"]],
        "apps": apps,
        **({"competitors": model["competitors"]} if model.get("competitors") else {}),
        "insights_file": None,
    }


IMPACT = ("high", "medium", "low")
MAX_ACTIONS = 5


def validate_insights(ins, model) -> list[str]:
    """Return every problem in an insights file; never raise on malformed input."""
    problems = []
    if not isinstance(ins, dict):
        return ["the file must hold one JSON object"]
    signal_ids = {s["id"] for s in model["signals"]}
    app_ids = {a["id"] for a in model["apps"]}
    review_ids = {r["id"] for a in model["apps"] for r in a["review_list"]}
    rival_ids = {a["id"]: {str(x.get("id")) for x in (a.get("competitors") or {}).get("apps", []) if x.get("role") == "competitor"}
                 for a in model["apps"]}
    is_str = lambda v: isinstance(v, str) and v.strip() != ""
    if not (isinstance(ins.get("date"), str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", ins["date"])):
        problems.append("date: required, a YYYY-MM-DD string")
    if not is_str(ins.get("headline")) or len(ins["headline"]) > 220:
        problems.append("headline: required string, 1-220 characters")
    for key in ("summary", "assumptions", "data_gaps"):
        val = ins.get(key, [])
        if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
            problems.append(f"{key}: must be a list of strings")
    actions = ins.get("actions")
    if not isinstance(actions, list) or not 1 <= len(actions) <= MAX_ACTIONS:
        problems.append(f"actions: required list of 1-{MAX_ACTIONS} items")
        actions = actions if isinstance(actions, list) else []
    for i, a in enumerate(actions):
        where = f"actions[{i}]"
        if not isinstance(a, dict):
            problems.append(f"{where}: must be an object")
            continue
        pr = a.get("priority")
        if not isinstance(pr, int) or isinstance(pr, bool) or pr < 1:
            problems.append(f"{where}.priority: integer >= 1")
        aid = a.get("app_id")
        if not isinstance(aid, str) or (aid != "portfolio" and aid not in app_ids):
            problems.append(f"{where}.app_id: must be the string 'portfolio' or an app id string ({', '.join(sorted(app_ids))})")
        for key in ("action", "why"):
            if not is_str(a.get(key)):
                problems.append(f"{where}.{key}: required non-empty string")
        ev = a.get("evidence")
        if not isinstance(ev, list) or not ev:
            problems.append(f"{where}.evidence: a list of at least one signal id string from data/digest.json")
        else:
            for e in ev:
                if not isinstance(e, str):
                    problems.append(f"{where}.evidence: {json.dumps(e)[:60]} is not a string signal id")
                elif e not in signal_ids:
                    problems.append(f"{where}.evidence: '{e}' is not a signal id in data/digest.json")
            scopes = {e.split("/", 1)[0] for e in ev if isinstance(e, str)}
            if isinstance(aid, str) and aid != "portfolio" and scopes and aid not in scopes and "portfolio" not in scopes:
                problems.append(f"{where}.evidence: cites no signal of app {aid} or of the portfolio")
        for key in ("impact", "effort"):
            if not (isinstance(a.get(key), str) and a[key] in IMPACT):
                problems.append(f"{where}.{key}: one of high, medium, low")
    per_app = ins.get("apps", {})
    if not isinstance(per_app, dict):
        problems.append("apps: must be an object keyed by app id")
        per_app = {}
    for aid, block in per_app.items():
        where = f"apps.{aid}"
        if aid not in app_ids:
            problems.append(f"{where}: unknown app id")
            continue
        if not isinstance(block, dict):
            problems.append(f"{where}: must be an object")
            continue
        if "summary" in block and not isinstance(block["summary"], str):
            problems.append(f"{where}.summary: string")
        for key in ("review_themes", "reply_drafts"):
            if not isinstance(block.get(key, []), list):
                problems.append(f"{where}.{key}: must be a list")
        themes = block.get("review_themes") if isinstance(block.get("review_themes"), list) else []
        for j, th in enumerate(themes):
            if not isinstance(th, dict) or not is_str(th.get("theme")):
                problems.append(f"{where}.review_themes[{j}]: object with a 'theme' string")
                continue
            if th.get("sentiment") not in (None, "positive", "negative", "mixed", "neutral"):
                problems.append(f"{where}.review_themes[{j}].sentiment: positive, negative, mixed or neutral")
            rids = th.get("review_ids", [])
            if not isinstance(rids, list):
                problems.append(f"{where}.review_themes[{j}].review_ids: must be a list")
                continue
            for rid in rids:
                if not isinstance(rid, str) or rid not in review_ids:
                    problems.append(f"{where}.review_themes[{j}].review_ids: {json.dumps(rid)[:60]} is not a known review id")
        if "competitors_summary" in block:
            if not isinstance(block["competitors_summary"], str):
                problems.append(f"{where}.competitors_summary: string")
            elif not rival_ids.get(aid):
                problems.append(f"{where}.competitors_summary: no competitor data for this app in data/competitors.json")
        cthemes = block.get("competitor_themes", [])
        if not isinstance(cthemes, list):
            problems.append(f"{where}.competitor_themes: must be a list")
            cthemes = []
        for j, th in enumerate(cthemes):
            w2 = f"{where}.competitor_themes[{j}]"
            if not isinstance(th, dict) or not is_str(th.get("theme")):
                problems.append(f"{w2}: object with a 'theme' string")
                continue
            if not isinstance(th.get("competitor_id"), str) or th["competitor_id"] not in rival_ids.get(aid, set()):
                problems.append(f"{w2}.competitor_id: {json.dumps(th.get('competitor_id'))[:60]} is not a competitor of app {aid} in data/competitors.json")
            if th.get("sentiment") not in (None, "positive", "negative", "mixed", "neutral"):
                problems.append(f"{w2}.sentiment: positive, negative, mixed or neutral")
            cnt = th.get("count")
            if cnt is not None and (not isinstance(cnt, int) or isinstance(cnt, bool) or cnt < 0):
                problems.append(f"{w2}.count: integer >= 0")
        drafts = block.get("reply_drafts") if isinstance(block.get("reply_drafts"), list) else []
        for j, d in enumerate(drafts):
            if not isinstance(d, dict) or not isinstance(d.get("review_id"), str) or d["review_id"] not in review_ids or not is_str(d.get("draft")):
                problems.append(f"{where}.reply_drafts[{j}]: needs a known review_id string and a non-empty draft")
    return problems


def render_html(model: dict, insights, link_prefix: str) -> str:
    if not TEMPLATE.is_file():
        raise TrackerError(f"the dashboard template is missing: {TEMPLATE}.",
                           "Reinstall the skill so assets/dashboard.html exists next to scripts/.")
    payload = dict(model)
    # Competitor review samples feed the agent's themes; the dashboard shows only the themes.
    def without_samples(group):
        return dict(group, apps=[{k: v for k, v in x.items() if k != "review_sample"} for x in group.get("apps", [])])
    payload["apps"] = [dict(a, competitors=without_samples(a["competitors"])) if a.get("competitors") else a for a in model["apps"]]
    payload["insights"] = insights
    payload["meta"] = dict(model["meta"], link_prefix=link_prefix)
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    data = data.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    data = data.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    html = TEMPLATE.read_text(encoding="utf-8")
    marker = "/*__APPSTORE_DATA__*/null"
    if marker not in html:
        raise TrackerError("the dashboard template has no data marker.", f"Restore '{marker}' in {TEMPLATE}.")
    return html.replace(marker, data)


def cmd_analyze(args) -> int:
    home = resolve_home(args.data_dir)
    model = build_model(home, args.as_of)
    digest = make_digest(model)
    run_date = args.date or today_local().isoformat()
    digest["insights_file"] = str(home / "insights" / f"{run_date}.json")
    out = home / "data" / "digest.json"
    write_json(out, digest)
    sev = defaultdict(int)
    for s in model["signals"]:
        sev[s["severity"]] += 1
    print(json.dumps({
        "digest": str(out), "insights_file": digest["insights_file"], "as_of": model["meta"]["as_of"],
        "sales_available": model["meta"]["sales_available"], "days": model["meta"]["total_days"],
        "known_days": model["meta"]["known_days"], "apps": len(model["apps"]), "signals": dict(sev),
        "gaps": [f"{g['source']}: {g['message']}" for g in model["gaps"]],
    }, indent=1))
    return 0


def cmd_render(args) -> int:
    home = resolve_home(args.data_dir)
    with home_lock(home):
        model = build_model(home, args.as_of)
        run_date = args.date or today_local().isoformat()
        ins_path = Path(args.insights).expanduser() if args.insights else home / "insights" / f"{run_date}.json"
        insights = None
        if args.no_insights:
            pass  # numbers-only run: ignore any insights file written earlier today
        elif ins_path.exists():
            insights = read_json(ins_path, None, INSIGHTS_FIX, 2)
            problems = validate_insights(insights, model)
            if problems:
                log(f"Error: {ins_path} failed validation ({len(problems)} problem(s)):")
                for p in problems:
                    log(f"  - {p}")
                log("Fix: edit the file (schema: references/analysis-playbook.md > Insights file), then rerun render.")
                return 2
        elif not (args.allow_missing_insights or args.no_insights):
            raise TrackerError(f"no insights file at {ins_path}.",
                               "Write it from data/digest.json (references/analysis-playbook.md), "
                               "or pass --allow-missing-insights to render signals only.", 2)
        history = home / "history"
        history.mkdir(parents=True, exist_ok=True)
        archive = history / f"{run_date}.html"
        # One archive per day. A numbers-only refresh never replaces an archive that embeds insights.
        keep_archive = bool(args.no_insights and archive.exists()
                            and '"insights":null' not in archive.read_text(encoding="utf-8"))
        if not any(r["date"] == run_date for r in model["runs"]):
            model["runs"].append({"date": run_date, "file": archive.name, "headline": (insights or {}).get("headline")})
        elif not keep_archive:  # a kept archive keeps the headline build_model read from its insights file
            for r in model["runs"]:
                if r["date"] == run_date:
                    r["headline"] = (insights or {}).get("headline")
        latest = home / "dashboard.html"
        latest.write_text(render_html(model, insights, "history/"), encoding="utf-8")
        if not keep_archive:
            archive.write_text(render_html(model, insights, ""), encoding="utf-8")
    print(json.dumps({
        "dashboard": str(latest), "archive": str(archive),
        "archive_written": not keep_archive,
        **({"archive_note": "kept: it holds today's report with insights"} if keep_archive else {}),
        "as_of": model["meta"]["as_of"],
        "insights": "embedded" if insights else "none (signals only)", "apps": len(model["apps"]),
        "signals": len(model["signals"]), "size_kb": round(latest.stat().st_size / 1024),
        "open": f"open '{latest}'",
    }, indent=1))
    return 0


# --------------------------------------------------------------------------
# status and config
# --------------------------------------------------------------------------


def cmd_status(args) -> int:
    home = resolve_home(args.data_dir)
    cfg = load_config(home)
    rep = {"data_dir": str(home), "config": public_config(cfg), "checks": {}}
    checks = rep["checks"]
    path = shutil.which("asc")
    checks["asc"] = {"ok": bool(path), "path": path}
    if not path:
        checks["asc"]["fix"] = "Install it with `brew install asc` (https://asccli.sh)."
    vendor, source = resolve_vendor(cfg)
    checks["vendor"] = {"ok": bool(vendor), "source": source, "value": (vendor[:2] + "…" + vendor[-2:]) if vendor else None}
    if not vendor:
        checks["vendor"]["fix"] = "`tracker.py config --vendor NUMBER` (App Store Connect > Payments and Financial Reports)."
    if path:
        try:
            st = asc(["auth", "status"], None, args.timeout)
            checks["auth"] = {"ok": True, "profiles": [c.get("name") for c in st.get("credentials", [])],
                              "default": next((c.get("name") for c in st.get("credentials", []) if c.get("isDefault")), None)}
        except AscError as err:
            checks["auth"] = {"ok": False, "kind": err.kind, "message": err.message, "fix": asc_fix(err, "read credentials", None)}
        if checks["auth"].get("ok"):
            prof = cfg.get("profile")
            try:
                apps = asc(["apps", "list", "--limit", "1", "--output", "json"], prof, args.timeout)
                checks["apps_access"] = {"ok": True, "profile": prof or "default"}
                first = (apps.get("data") or [{}])[0].get("id")
                if first:
                    try:
                        asc(["reviews", "--app", str(first), "--limit", "1", "--output", "json"], prof, args.timeout)
                        checks["reviews_access"] = {"ok": True}
                    except AscError as err:
                        checks["reviews_access"] = {"ok": False, "kind": err.kind, "fix": asc_fix(err, "read customer reviews", prof)}
            except AscError as err:
                checks["apps_access"] = {"ok": False, "kind": err.kind, "message": err.message, "fix": asc_fix(err, "list apps", prof)}
            if vendor:
                sprof = cfg.get("sales_profile") or prof
                probe_day = (today_pt() - timedelta(days=PENDING_DAYS + 1)).isoformat()
                with tempfile.TemporaryDirectory() as tmp:
                    try:
                        meta = asc(["analytics", "sales", "--vendor", vendor, "--type", "SALES", "--subtype", "SUMMARY",
                                    "--frequency", "DAILY", "--date", probe_day, "--allow-missing",
                                    "--output", os.path.join(tmp, "probe.tsv.gz"), "--output-format", "json"], sprof, args.timeout)
                        checks["sales_access"] = {"ok": True, "profile": sprof or "default", "probe_day": probe_day,
                                                  "report_available": (meta or {}).get("available", True) if isinstance(meta, dict) else True}
                    except AscError as err:
                        checks["sales_access"] = {"ok": False, "profile": sprof or "default", "kind": err.kind,
                                                  "message": err.message, "fix": asc_fix(err, "download Sales and Trends reports", sprof)}
    if path:
        ok, why = web_session_ok(args.timeout)
        checks["web_session"] = {"ok": ok, "use": "App Analytics: downloads, proceeds, impressions, page views, rejection messages"}
        if not ok:
            checks["web_session"].update(message=why, fix="Optional. Ask the user to run `! asc web auth login` themselves; the skill never logs in.")
    sales_dir = home / "raw" / "sales" / "daily"
    files = sorted(p.name[:10] for p in sales_dir.glob("*.tsv.gz")) if sales_dir.is_dir() else []
    state = read_json(home / "state.json", {}) or {}
    rep["data"] = {"exists": home.exists(), "sales_days": len(files), "first": files[0] if files else None,
                   "last": files[-1] if files else None,
                   "snapshots": len(list((home / "snapshots").glob("*.json"))) if (home / "snapshots").is_dir() else 0,
                   "last_fetch": (state.get("last_fetch") or {}).get("finished")}
    ok = checks["asc"]["ok"] and checks.get("auth", {}).get("ok") and checks.get("apps_access", {}).get("ok")
    rep["ready"] = bool(ok)
    rep["sales_ready"] = bool(ok and checks.get("sales_access", {}).get("ok"))
    rep["analytics_ready"] = bool(ok and checks.get("web_session", {}).get("ok"))
    print(json.dumps(rep, indent=1))
    for name, c in checks.items():
        if not c.get("ok"):
            log(f"warning: {name}: {c.get('message') or c.get('kind') or 'not ok'}\n  fix: {c.get('fix')}")
    return 0 if ok else 1


def cmd_config(args) -> int:
    home = resolve_home(args.data_dir)
    cfg = load_config(home)
    changed = False

    def setv(key, val, conv=lambda v: v):
        nonlocal changed
        if val is None:
            return
        cfg[key] = None if str(val).lower() in ("none", "default", "") else conv(val)
        changed = True

    setv("profile", args.profile)
    setv("sales_profile", args.sales_profile)
    if args.vendor is not None and str(args.vendor).lower() not in ("none", "") and not re.fullmatch(r"\d{5,12}", str(args.vendor)):
        raise TrackerError(f"vendor number '{args.vendor}' is not numeric.", "Use the digits shown in Payments and Financial Reports.")
    setv("vendor_number", args.vendor)
    if args.base_currency is not None:
        if not re.fullmatch(r"[A-Za-z]{3}", args.base_currency):
            raise TrackerError(f"currency '{args.base_currency}' is not an ISO code.", "Use a 3-letter code such as USD or EUR.")
        fx_files = sorted((home / "raw" / "fx").glob("*.json"))
        rates = ((read_json(fx_files[-1], {}) or {}).get("rates") or {}) if fx_files else {}
        if args.base_currency.upper() not in (rates or ISO_CURRENCIES):
            raise TrackerError(f"currency '{args.base_currency}' has no exchange rate.",
                               ("Use a code from the cached rates: " + ", ".join(sorted(rates)) + ".") if rates
                               else "Use an ISO 4217 code such as USD or EUR.")
        setv("base_currency", args.base_currency.upper())
    if args.backfill_days is not None:
        if not 1 <= args.backfill_days <= MAX_BACKFILL:
            raise TrackerError(f"--backfill-days {args.backfill_days} is out of range.", f"Use 1-{MAX_BACKFILL}; Apple keeps about a year of daily reports.")
        setv("backfill_days", args.backfill_days)
    if args.include_apps is not None and args.include_apps.lower() not in ("none", "default", ""):
        account = read_json(home / "raw" / "account_apps.json", None)
        bad = {x.strip() for x in args.include_apps.split(",") if x.strip()} - {a["id"] for a in account or []}
        if account is not None and bad:
            raise unknown_apps_error(bad, account)
    setv("include_apps", args.include_apps, lambda v: [x.strip() for x in v.split(",") if x.strip()] or None)
    setv("exclude_apps", args.exclude_apps, lambda v: [x.strip() for x in v.split(",") if x.strip()])
    if changed:
        write_json(home / "config.json", cfg)
    print(json.dumps({"data_dir": str(home), "changed": changed, "config": public_config(cfg)}, indent=1))
    return 0


# --------------------------------------------------------------------------
# demo data (synthetic, deterministic, no network)
# --------------------------------------------------------------------------


DEMO_IDS = ["900000001", "900000002", "900000003", "900000004"]  # 9 digits: never a real-looking phone pattern
DEMO_HEADER = ["Provider", "Provider Country", "SKU", "Developer", "Title", "Version", "Product Type Identifier",
               "Units", "Developer Proceeds", "Begin Date", "End Date", "Customer Currency", "Country Code",
               "Currency of Proceeds", "Apple Identifier", "Customer Price", "Promo Code", "Parent Identifier",
               "Subscription", "Period", "Category", "CMB", "Device", "Supported Platforms", "Proceeds Reason",
               "Preserved Pricing", "Client", "Order Type"]


def cmd_demo(args) -> int:
    if not args.data_dir:
        raise TrackerError("demo needs an explicit --data-dir.",
                           "Run `tracker.py --data-dir /path/to/new-dir demo`; it never writes into the real data dir.")
    home = resolve_home(args.data_dir)
    existing = next(p for p in (home, *home.parents) if p.exists())  # a file anywhere on the path blocks mkdir
    if not existing.is_dir():
        raise TrackerError(f"{existing} is a file, not a directory.", "Pass a new or empty directory path as --data-dir.")
    if not 30 <= args.days <= MAX_BACKFILL:
        raise TrackerError(f"--days {args.days} is out of range.", f"Use 30-{MAX_BACKFILL}; the demo shows a release 30 days back.")
    if home.exists() and any(home.iterdir()):
        cfg = read_json(home / "config.json", {}) or {}
        if not cfg.get("demo"):
            raise TrackerError(f"{home} is not empty and is not a demo directory.",
                               "Pass an empty or new --data-dir; the demo never overwrites real data.")
        shutil.rmtree(home)
    rng = random.Random(args.seed)
    days_n = args.days
    last = today_pt() - timedelta(days=1)
    first = last - timedelta(days=days_n - 1)
    apps = [
        {"id": DEMO_IDS[0], "name": "Demo Notes", "bundle_id": "demo.notes", "sku": "demo-notes", "primary_locale": "en-US"},
        {"id": DEMO_IDS[1], "name": "Demo Puzzle", "bundle_id": "demo.puzzle", "sku": "demo-puzzle", "primary_locale": "en-US"},
        {"id": DEMO_IDS[2], "name": "Demo Mac Tool", "bundle_id": "demo.mactool", "sku": "demo-mactool", "primary_locale": "en-US"},
        {"id": DEMO_IDS[3], "name": "Demo Unreleased", "bundle_id": "demo.unreleased", "sku": "demo-unreleased", "primary_locale": "en-US"},
    ]
    write_json(home / "config.json", dict(DEFAULT_CONFIG, demo=True, vendor_number="00000000"))
    write_json(home / "raw" / "apps.json", apps)
    write_json(home / "raw" / "account_apps.json", apps)
    countries = [("US", "USD", 0.45), ("JP", "JPY", 0.18), ("FR", "EUR", 0.12), ("DE", "EUR", 0.08),
                 ("GB", "GBP", 0.07), ("VN", "USD", 0.06), ("BR", "BRL", 0.04)]
    fx = {"USD": 1, "EUR": 0.92, "JPY": 150.0, "GBP": 0.79, "BRL": 5.0}
    release_day = first + timedelta(days=days_n - 30)
    sales_dir = home / "raw" / "sales" / "daily"
    sales_dir.mkdir(parents=True, exist_ok=True)
    status = {}
    for d in day_range(first, last):
        if d == first + timedelta(days=10):
            status[d.isoformat()] = "empty"
            continue
        weekend = 1.25 if d.weekday() >= 5 else 1.0
        rows = []
        t = (d - first).days

        def add(app, ptype, units, proceeds_usd, cc, cur, version="1.0", parent="", title=None, device="iPhone", promo="", sub=""):
            rows.append({"Provider": "APPLE", "Provider Country": "US", "SKU": app["sku"] if not parent else title,
                         "Developer": "Demo Dev", "Title": title or app["name"], "Version": version,
                         "Product Type Identifier": ptype, "Units": str(units),
                         "Developer Proceeds": f"{proceeds_usd * fx[cur]:.2f}", "Begin Date": d.strftime("%m/%d/%Y"),
                         "End Date": d.strftime("%m/%d/%Y"), "Customer Currency": cur, "Country Code": cc,
                         "Currency of Proceeds": cur, "Apple Identifier": app["id"] if not parent else "2000000" + str(len(title or "")),
                         "Customer Price": f"{proceeds_usd * 1.43 * fx[cur]:.2f}", "Promo Code": promo,
                         "Parent Identifier": parent, "Subscription": sub, "Period": "1 Month" if sub else "",
                         "Category": "Productivity", "CMB": "", "Device": device, "Supported Platforms": "iOS",
                         "Proceeds Reason": "", "Preserved Pricing": "", "Client": "", "Order Type": ""})
        notes, puzzle, mac = apps[0], apps[1], apps[2]
        notes_ver = "1.3" if d >= release_day else "1.2"
        for cc, cur, share in countries:
            base = 6 * share * weekend * (1 + t / days_n * 0.6)
            u = sum(1 for _ in range(int(base * 2 + 1)) if rng.random() < 0.5)
            if u:
                add(notes, "1", u, 2.09, cc, cur, notes_ver, device=rng.choice(["iPhone", "iPhone", "iPad"]))
            pu = sum(1 for _ in range(int(14 * share * weekend * (1.3 if d >= release_day else 1.0) + 1)) if rng.random() < 0.7)
            if pu:
                add(puzzle, "1F", pu, 0.0, cc, cur, "2.0", device=rng.choice(["iPhone", "iPad"]))
            if pu and rng.random() < 0.35:
                add(puzzle, "IA1", max(1, pu // 4), 1.39, cc, cur, "", parent=puzzle["sku"], title="demo.puzzle.hints")
            if rng.random() < 0.3 * share * 5:
                add(mac, "F1", 1, 0.0, cc, cur, "3.1", device="Desktop")
            if rng.random() < 0.08 * share * 5:
                add(mac, "IAY-M", 1, 3.49, cc, cur, "", parent=mac["sku"], title="demo.mactool.pro.monthly", device="Desktop",
                    sub=rng.choice(["New", "Renewal"]))
        add(notes, "7", rng.randint(3, 12), 0.0, "US", "USD", "1.2")
        add(puzzle, "3F", rng.randint(0, 4) or 1, 0.0, "US", "USD", "2.0")
        if rng.random() < 0.06:
            add(notes, "1", -1, 2.09, "US", "USD", notes_ver)
        if t > days_n - 3 and d == last:
            status[d.isoformat()] = "pending"
            continue
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=DEMO_HEADER, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        (sales_dir / f"{d.isoformat()}.tsv.gz").write_bytes(gzip.compress(buf.getvalue().encode("utf-8"), mtime=0))
    write_json(home / "raw" / "sales" / "status.json", status)
    for k, app in enumerate(apps[:3]):  # synthetic App Analytics funnel: impressions and product page views
        scale = (300, 3000, 90)[k]  # Demo Puzzle: many impressions, low tap-through, page views above downloads
        imp, pv = {}, {}
        for d in day_range(first, last - timedelta(days=1)):
            base = scale * (1.25 if d.weekday() >= 5 else 1.0) * (0.75 if k == 2 and d > last - timedelta(days=28) else 1.0)
            imp[d.isoformat()] = int(base * rng.uniform(0.8, 1.2))
            pv[d.isoformat()] = int(imp[d.isoformat()] * (0.012 if k == 1 else 0.07) * rng.uniform(0.7, 1.3))
        write_json(home / "raw" / "web" / f"{app['id']}.json", {"measures": {"impressions": imp, "page_views": pv}, "updated": last.isoformat()})
    write_json(home / "raw" / "fx" / f"{last.isoformat()}.json", {"base": "USD", "date": last.isoformat(),
                                                                  "source": "demo (fixed rates)", "rates": fx})
    texts = {  # review texts per demo app, so a preview never shows a puzzle review on a notes app
        DEMO_IDS[0]: [(5, "Love it", "Fast and simple. Exactly what I needed."),
                      (4, "Good but", "Great app but please add dark mode."),
                      (2, "Sync broke", "Since the last update my notes do not sync between iPhone and iPad."),
                      (1, "Crashes", "Crashes every time I open a long note. Please fix.")],
        DEMO_IDS[1]: [(5, "Best puzzle game", "Addictive levels, I play every day."),
                      (3, "Hints too pricey", "Fun but the hint prices are high."),
                      (1, "Stuck on level 40", "Level 40 cannot be solved after the update.")],
        DEMO_IDS[2]: [(4, "Nice tool", "Does the job on my Mac. Wish it had keyboard shortcuts."),
                      (5, "Saves me time", "Runs quietly in the menu bar."),
                      (2, "Subscription", "The monthly price is too high for what it does.")],
    }
    for app in apps[:3]:
        store = {}
        for k in range(rng.randint(6, 12)):
            rating, title, body = rng.choice(texts[app["id"]])
            created = last - timedelta(days=rng.randint(0, days_n - 1))
            rid = f"demo-{app['id']}-{k}"
            store[rid] = {"id": rid, "rating": rating, "title": title, "body": body, "nickname": f"user{k}",
                          "territory": rng.choice(["USA", "JPN", "FRA", "DEU"]),
                          "created": created.isoformat() + "T10:00:00-07:00",
                          "response": ({"body": "Thanks for the feedback!", "state": "PUBLISHED", "date": created.isoformat()}
                                       if rng.random() < 0.4 else None),
                          "first_seen": created.isoformat(), "last_seen": last.isoformat()}
        write_json(home / "raw" / "reviews" / f"{app['id']}.json", store)
    write_json(home / "raw" / "versions" / f"{DEMO_IDS[0]}.json", [
        {"id": "v13", "platform": "IOS", "version": "1.3", "state": "READY_FOR_SALE", "created": (release_day - timedelta(days=5)).isoformat()},
        {"id": "v12", "platform": "IOS", "version": "1.2", "state": "READY_FOR_SALE", "created": (first - timedelta(days=40)).isoformat()}])
    write_json(home / "raw" / "versions" / f"{DEMO_IDS[1]}.json", [
        {"id": "v20", "platform": "IOS", "version": "2.0", "state": "READY_FOR_SALE", "created": (first - timedelta(days=200)).isoformat()}])
    write_json(home / "raw" / "versions" / f"{DEMO_IDS[2]}.json", [
        {"id": "v31", "platform": "MAC_OS", "version": "3.1", "state": "READY_FOR_SALE", "created": (first - timedelta(days=90)).isoformat()}])
    write_json(home / "raw" / "versions" / f"{DEMO_IDS[3]}.json", [
        {"id": "v01", "platform": "IOS", "version": "0.1", "state": "PREPARE_FOR_SUBMISSION", "created": last.isoformat()}])
    store_meta = {
        DEMO_IDS[0]: {"kind": "software", "formattedPrice": "$2.99", "price": 2.99, "currency": "USD", "version": "1.3",
                       "currentVersionReleaseDate": release_day.isoformat() + "T07:00:00Z", "primaryGenreName": "Productivity",
                       "languageCodesISO2A": ["EN", "FR"], "trackViewUrl": "https://apps.apple.com/", "listed": True},
        DEMO_IDS[1]: {"kind": "software", "formattedPrice": "Free", "price": 0, "currency": "USD", "version": "2.0",
                       "currentVersionReleaseDate": (first - timedelta(days=150)).isoformat() + "T07:00:00Z",
                       "primaryGenreName": "Games", "languageCodesISO2A": ["EN"], "trackViewUrl": "https://apps.apple.com/", "listed": True},
        DEMO_IDS[2]: {"kind": "mac-software", "formattedPrice": "Free", "price": 0, "currency": "USD", "version": "3.1",
                       "currentVersionReleaseDate": (first - timedelta(days=60)).isoformat() + "T07:00:00Z",
                       "primaryGenreName": "Developer Tools", "languageCodesISO2A": ["EN", "DE"], "trackViewUrl": "https://apps.apple.com/", "listed": True},
        DEMO_IDS[3]: {"listed": False},
    }
    for k, snap_day in enumerate([last - timedelta(days=2), last - timedelta(days=1), last]):
        snap = {"date": snap_day.isoformat(), "generated_at": snap_day.isoformat() + "T09:00:00", "apps": {}}
        for app in apps:
            entry = {"name": app["name"], "store": store_meta[app["id"]]}
            if app["id"] == DEMO_IDS[1]:
                entry["products"] = [
                    {"id": "p1", "kind": "iap", "name": "Hint pack", "product_id": "demo.puzzle.hints", "type": "CONSUMABLE", "state": "APPROVED"},
                    {"id": "p2", "kind": "iap", "name": "Remove ads", "product_id": "demo.puzzle.noads", "type": "NON_CONSUMABLE", "state": "MISSING_METADATA"}]
            if app["id"] == DEMO_IDS[3]:
                entry["ratings"] = {"listed": False}
            elif app["id"] == DEMO_IDS[2]:
                entry["ratings"] = {"listed": True, "average": 0, "count": 0, "countries": 0, "top": []}
            else:
                entry["ratings"] = {"listed": True, "average": round(4.1 + 0.1 * k, 1), "count": 40 + 3 * k + (20 if app["id"] == DEMO_IDS[1] else 0), "countries": 5, "top": []}
            snap["apps"][app["id"]] = entry
        write_json(home / "snapshots" / f"{snap_day.isoformat()}.json", snap)
    write_json(home / "state.json", {"last_fetch": {"date": last.isoformat(), "started": None, "finished": None, "apps": 4,
                                                    "partial": False, "errors": [], "sales": {"state": "demo"}}})
    print(json.dumps({"data_dir": str(home), "apps": len(apps), "days": days_n, "first": first.isoformat(),
                      "last": last.isoformat(), "note": "synthetic data; never mix it with a real data dir"}, indent=1))
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="tracker.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("--data-dir", help=f"data directory (default ${{APPSTORE_TRACKER_HOME}} or {DEFAULT_HOME})")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("status", help="check asc, credentials, vendor number and data access")
    p.add_argument("--timeout", type=int, default=90)

    p = sub.add_parser("config", help="show or change settings")
    p.add_argument("--profile", help="asc profile for apps, versions and reviews ('none' = asc default)")
    p.add_argument("--sales-profile", help="asc profile for Sales and Trends reports ('none' = same as --profile)")
    p.add_argument("--vendor", help="vendor number for Sales and Trends reports")
    p.add_argument("--base-currency", help="currency for proceeds totals, e.g. USD or EUR")
    p.add_argument("--backfill-days", type=int, help=f"daily sales history to keep complete (1-{MAX_BACKFILL})")
    p.add_argument("--include-apps", help="comma-separated app ids to track ('none' = all)")
    p.add_argument("--exclude-apps", help="comma-separated app ids to ignore ('none' = no exclusions)")

    p = sub.add_parser("fetch", help="pull data from App Store Connect into the data dir")
    p.add_argument("--days", type=int, help="sales history window in days (default: config backfill_days)")
    p.add_argument("--apps", help="comma-separated app ids for this run only")
    p.add_argument("--skip", help="comma-separated sources to skip: versions,reviews,ratings,store,products,analytics,sales,fx")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--timeout", type=int, default=90, help="seconds before an asc call is abandoned")

    p = sub.add_parser("analyze", help="aggregate history and write data/digest.json")
    p.add_argument("--as-of", help="last sales day to analyse (YYYY-MM-DD)")
    p.add_argument("--date", help="run date for the insights file name (default: today)")

    p = sub.add_parser("render", help="write dashboard.html and its history copy")
    p.add_argument("--as-of", help="last sales day to analyse (YYYY-MM-DD)")
    p.add_argument("--date", help="run date (default: today)")
    p.add_argument("--insights", help="insights JSON (default: <data-dir>/insights/<date>.json)")
    p.add_argument("--allow-missing-insights", action="store_true", help="render signals only when no insights file exists")
    p.add_argument("--no-insights", action="store_true", help="numbers only: ignore the day's insights file even if it exists")

    p = sub.add_parser("demo", help="write synthetic data into an empty --data-dir")
    p.add_argument("--days", type=int, default=120)
    p.add_argument("--seed", type=int, default=7)

    args = ap.parse_args(argv)
    handlers = {"status": cmd_status, "config": cmd_config, "fetch": cmd_fetch, "analyze": cmd_analyze,
                "render": cmd_render, "demo": cmd_demo}
    try:
        return handlers[args.cmd](args)
    except TrackerError as err:
        log(f"Error: {err.what}\nFix: {err.fix}")
        return err.code
    except KeyboardInterrupt:
        log("Error: interrupted.\nFix: rerun the same command; downloaded days are kept.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
