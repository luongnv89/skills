#!/usr/bin/env python3
"""App Store competitor tracker: follow how competing apps grow, using only the
public iTunes endpoints (lookup, search, customer-review RSS, genre top charts).

Subcommands
  discover  propose competitors for one of your apps (read-only, saves nothing)
  add       add competitor ids (and search terms) to an app's group
  remove    drop competitor ids or terms from a group
  config    show or set countries and review pages
  status    configured groups, snapshots, last fetch, `ready`
  fetch     snapshot every group: lookup, reviews RSS, genre charts, search rank
  analyze   write <data dir>/data/competitors.json with metrics and signals
  demo      add synthetic competitor data to a `tracker.py demo` dir (no network)

Apple publishes no competitor downloads or revenue. Growth here is measured by
public proxies: new ratings, written reviews, chart rank and search position.
Prices come from the lookup (upfront price) and the public product page on
apps.apple.com (in-app purchases, up to 10 shown per storefront).
Standard library only (Python 3.9+). No authentication, no App Store Connect.
"""

from __future__ import annotations

import argparse
import contextlib
import html as htmllib
import json
import os
import random
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows
    fcntl = None

VERSION = "1.1.1"
DEFAULT_HOME = "~/.appstore-tracker"
USER_AGENT = f"appstore-competitor-tracker/{VERSION} (public iTunes endpoints)"
LOOKUP_URL = "https://itunes.apple.com/lookup?id={ids}&country={cc}"
SEARCH_URL = "https://itunes.apple.com/search?term={q}&entity={entity}&country={cc}&limit={n}"
REVIEWS_URL = "https://itunes.apple.com/{cc}/rss/customerreviews/page={page}/id={id}/sortby=mostrecent/json"
CHART_URL = "https://itunes.apple.com/{cc}/rss/{feed}/limit=200/genre={genre}/json"
CHART_FEEDS = {"free": "topfreeapplications", "paid": "toppaidapplications"}
PAGE_URL = "https://apps.apple.com/{cc}/app/id{id}"
FALLBACK_UA = "curl/8.7.1"  # itunes.apple.com sometimes 403s named or browser UAs; a plain client UA still passes
PAGE_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 "
           "(KHTML, like Gecko) Version/17.5 Safari/605.1.15")
IAP_STORY_ID = "1436214772"  # Apple's "About In-App Purchases" story: marks the IAP block in every language
IAP_SHOWN_MAX = 10           # the product page lists at most 10 in-app purchases
PAUSE = 0.35          # seconds between calls: be polite to a public endpoint
TIMEOUT = 20
LOOKUP_BATCH = 20
MAX_COMPETITORS = 10
MAX_REVIEW_PAGES = 10  # the RSS feed stops at 10 pages of 50 reviews
SEARCH_LIMIT = 50
RELEVANT_POS = 10     # discover: a top-10 search hit counts as relevant even in another genre
DEFAULT_CONFIG = {"countries": ["us"], "review_pages": 3, "apps": {}}

# Signal thresholds (documented in references/competitor-playbook.md)
OUTPACE_RATIO, OUTPACE_MIN = 2.0, 5
RELEASE_DAYS = 14
RANK_GAIN = 10
SEARCH_OWN_OUT, SEARCH_COMP_IN = 10, 5
RATING_GAP, RATING_MIN_COUNT = 0.5, 5
PRICING_FREE_SHARE, PRICING_ENTRY_RATIO, PRICING_MIN_KNOWN = 2 / 3, 2.0, 2
OFFER_SHARE = 0.5     # offer gap: strictly more than half of the competitors with a known IAP list
DELTA_WINDOWS = (7, 28)
REVIEW_WINDOWS = (7, 28, 90)


class CompError(Exception):
    """An error with a fix the user or agent can act on."""

    def __init__(self, what: str, fix: str, code: int = 1):
        super().__init__(what)
        self.what, self.fix, self.code = what, fix, code


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def emit(obj) -> None:
    print(json.dumps(obj, indent=1, ensure_ascii=False))


def today() -> date:
    return datetime.now().date()


def parse_day(text) -> date | None:
    try:
        return datetime.strptime(str(text)[:10], "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def resolve_home(arg: str | None) -> Path:
    raw = arg or os.environ.get("APPSTORE_TRACKER_HOME") or DEFAULT_HOME
    return Path(raw).expanduser().resolve()


def read_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default
    except json.JSONDecodeError as exc:
        raise CompError(f"{path} is not valid JSON (line {exc.lineno}: {exc.msg}).",
                        f"Fix or delete {path}; `fetch` recreates snapshots and review stores.")


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


@contextlib.contextmanager
def comp_lock(cdir: Path):
    cdir.mkdir(parents=True, exist_ok=True)
    if fcntl is None:
        yield
        return
    fh = open(cdir / ".lock", "w")
    try:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise CompError(f"Another competitor run is using {cdir}.", "Wait for it to finish, or pass a different --data-dir.")
        yield
    finally:
        fh.close()


def trim(text, limit: int) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:40] or "term"


def valid_id(x) -> bool:
    return bool(re.fullmatch(r"\d{5,12}", str(x)))


# --------------------------------------------------------------------------
# HTTP: polite, one retry, errors classified (a failed source is a gap, never zero)
# --------------------------------------------------------------------------


class Http:
    def __init__(self, pause: float = PAUSE, timeout: int = TIMEOUT):
        self.pause, self.timeout, self.calls = pause, timeout, 0
        self.headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        self.notes: list[str] = []

    def get(self, url: str):
        last, headers = None, self.headers
        for attempt in range(2):  # retries = 1
            if self.calls:
                time.sleep(self.pause * (6 if attempt else 1))
            self.calls += 1
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    body = resp.read().decode("utf-8", "replace")
                data = json.loads(body) if body.strip() else {}
                if headers is not self.headers:  # the fallback worked: keep it for the rest of the run
                    self.headers = headers
                    src = next((p for p in urllib.parse.urlsplit(url).path.split("/") if len(p) > 2), "itunes")  # skip the /<cc>/ segment
                    self.notes.append(f"{src}: 403 with default User-Agent; retried with fallback")
                return data
            except urllib.error.HTTPError as exc:
                last = exc
                if (exc.code == 403 and not attempt and headers["User-Agent"] != FALLBACK_UA
                        and urllib.parse.urlsplit(url).hostname == "itunes.apple.com"):
                    headers = {"User-Agent": FALLBACK_UA, "Accept": "*/*"}
                    continue
                if exc.code in (400, 403, 404):
                    break  # not transient
            except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
                last = exc
        raise last

    def get_text(self, url: str) -> str:
        """HTML page (the product page); same pacing, retry and call count as `get`."""
        last = None
        for attempt in range(2):
            if self.calls:
                time.sleep(self.pause * (6 if attempt else 1))
            self.calls += 1
            try:
                req = urllib.request.Request(url, headers={"User-Agent": PAGE_UA, "Accept-Language": "en-US,en;q=0.9",
                                                           "Accept": "text/html,application/xhtml+xml"})
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # follows the 301 to the slug URL
                    return resp.read().decode("utf-8", "replace")
            except urllib.error.HTTPError as exc:
                last = exc
                if exc.code in (400, 403, 404):
                    break
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last = exc
        raise last


def err_kind(exc) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        return f"http_{exc.code}"
    if isinstance(exc, ValueError):
        return "bad_json"
    if isinstance(exc, (TimeoutError,)) or "timed out" in str(exc):
        return "timeout"
    return "network"


def slim(r: dict) -> dict:
    return {
        "id": str(r.get("trackId")), "name": r.get("trackName"), "seller": r.get("sellerName"), "kind": r.get("kind"),
        "genre_id": str(r.get("primaryGenreId") or "") or None, "genre": r.get("primaryGenreName"),
        "ratings": r.get("userRatingCount"), "avg": r.get("averageUserRating"),
        "version": r.get("version"), "version_date": r.get("currentVersionReleaseDate"), "released": r.get("releaseDate"),
        "price": r.get("price"), "formatted_price": r.get("formattedPrice"), "currency": r.get("currency"),
        "languages": r.get("languageCodesISO2A"), "url": r.get("trackViewUrl"), "icon": r.get("artworkUrl100"),
        "listed": True,
    }


def platform_of(rec: dict | None) -> str:
    return "mac" if (rec or {}).get("kind") == "mac-software" else "ios"


def lookup(http: Http, ids: list[str], cc: str) -> dict:
    out = {}
    for i in range(0, len(ids), LOOKUP_BATCH):
        chunk = ids[i:i + LOOKUP_BATCH]
        data = http.get(LOOKUP_URL.format(ids=",".join(chunk), cc=cc))
        for r in data.get("results") or []:
            if r.get("trackId") and r.get("kind") in ("software", "mac-software"):
                out[str(r["trackId"])] = slim(r)
    return out


def search(http: Http, term: str, platform: str, cc: str, limit: int = SEARCH_LIMIT) -> list[dict]:
    entity = "macSoftware" if platform == "mac" else "software"
    data = http.get(SEARCH_URL.format(q=urllib.parse.quote_plus(term), entity=entity, cc=cc, n=limit))
    return [slim(r) for r in data.get("results") or [] if r.get("trackId")]


def as_list(x):
    return x if isinstance(x, list) else ([x] if isinstance(x, dict) else [])


def label(node, key):
    v = (node or {}).get(key)
    return v.get("label") if isinstance(v, dict) else None


def fetch_reviews(http: Http, aid: str, cc: str, pages: int) -> tuple[list[dict], dict]:
    """Newest reviews first. Stops at the first short page (the feed is exhausted)."""
    got, complete, fetched_pages = [], False, 0
    for page in range(1, pages + 1):
        try:
            data = http.get(REVIEWS_URL.format(cc=cc, page=page, id=aid))
        except urllib.error.HTTPError as exc:
            if page > 1 and exc.code in (400, 404):
                complete = True  # past the last page
                break
            raise
        fetched_pages += 1
        entries = [e for e in as_list((data.get("feed") or {}).get("entry")) if label(e, "im:rating")]
        for e in entries:
            rid, day = label(e, "id"), (label(e, "updated") or "")[:10]
            try:
                rating = int(label(e, "im:rating"))
            except (TypeError, ValueError):
                continue
            if rid and parse_day(day):
                got.append({"id": rid, "date": day, "rating": rating, "version": label(e, "im:version"),
                            "title": trim(label(e, "title"), 200), "body": trim(label(e, "content"), 1200), "country": cc})
        if len(entries) < 50:
            complete = True
            break
    oldest = min((r["date"] for r in got), default=None)
    return got, {"fetched": len(got), "pages": fetched_pages, "oldest": oldest, "complete": complete}


def chart_ids(http: Http, feed: str, genre: str, cc: str) -> list[str]:
    data = http.get(CHART_URL.format(cc=cc, feed=feed, genre=genre))
    out = []
    for e in as_list((data.get("feed") or {}).get("entry")):
        attrs = ((e.get("id") or {}).get("attributes") or {})
        if attrs.get("im:id"):
            out.append(str(attrs["im:id"]))
    return out


# --------------------------------------------------------------------------
# Product page: upfront price and in-app purchases
# --------------------------------------------------------------------------


class PageParseError(ValueError):
    pass


_SPACES = re.compile(r"[\s\u00a0\u202f\u200a\u2009\u2007\u00ad]+")


def parse_price(text) -> float | None:
    """'$1.99' -> 1.99, '6,99 €' -> 6.99, '¥2,500' -> 2500.0, '1.234,56 €' -> 1234.56, 'R$ 5,90' -> 5.9."""
    m = re.search(r"\d[\d.,']*", _SPACES.sub("", str(text or "")))
    if not m:
        return None
    n = m.group(0).replace("'", "").rstrip(".,")
    seps = [i for i, ch in enumerate(n) if ch in ".,"]
    if seps:
        last = seps[-1]
        if len(n) - last - 1 == 3:  # a final separator before exactly 3 digits is a thousands mark
            n = re.sub(r"[.,]", "", n)
        else:
            n = re.sub(r"[.,]", "", n[:last]) + "." + n[last + 1:]
    try:
        return float(n)
    except ValueError:
        return None


def looks_like_price(text) -> bool:
    t = _SPACES.sub("", str(text or ""))
    return bool(re.fullmatch(r"\D{0,5}\d[\d.,']*\D{0,5}", t) and re.search(r"[^\d.,']", t))


def _json_script(page: str, needle: str):
    for m in re.finditer(r"<script\b([^>]*)>(.*?)</script>", page, re.S | re.I):
        if needle in m.group(1):
            try:
                return json.loads(m.group(2))
            except ValueError:
                return None
    return None


def _is_iap_annotation(node: dict) -> bool:
    for it in node.get("items") or []:
        if not isinstance(it, dict) or it.get("$kind") != "button":
            continue
        act = it.get("action") or {}
        if str((act.get("destination") or {}).get("id")) == IAP_STORY_ID or f"id{IAP_STORY_ID}" in str(act.get("pageUrl") or ""):
            return True
    return False


def _annotations(obj, out: list) -> list:
    if isinstance(obj, dict):
        if obj.get("$kind") == "Annotation":
            out.append(obj)
        for v in obj.values():
            _annotations(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _annotations(v, out)
    return out


def _text_fallback(page: str) -> list | None:
    """English-only rescue when the structured data is missing: a list when the heading is found, else None (never [])."""
    i = page.find("In-App Purchases")
    if i < 0:
        return None
    j = page.find("Copyright", i)
    chunk = page[i:j if j > i else i + 6000]
    lines = [htmllib.unescape(x).strip() for x in re.sub(r"<[^>]+>", "\n", chunk).split("\n")]
    lines = [x for x in lines if x and x not in ("In-App Purchases", "Yes", "Learn More")]
    out, k = [], 0
    while k < len(lines) - 1:
        if not looks_like_price(lines[k]) and looks_like_price(lines[k + 1]):
            out.append((lines[k], lines[k + 1]))
            k += 2
        else:
            k += 1
    return out or None


def parse_product_page(page: str) -> dict:
    """{upfront_price, currency, iap: [...] | None, iap_count, iap_capped, rating_page}.

    `iap: []` only when the structured page data parsed and its information shelf holds no IAP block;
    any other shape raises PageParseError (unknown, never "no IAPs")."""
    ld = _json_script(page, "software-application") or {}
    offers = ld.get("offers") if isinstance(ld, dict) else None
    offers = offers[0] if isinstance(offers, list) and offers else offers
    offers = offers if isinstance(offers, dict) else {}
    currency = offers.get("priceCurrency")
    try:
        upfront = float(offers["price"]) if offers.get("price") is not None else None
    except (TypeError, ValueError):
        upfront = None
    pairs, source = None, "structured"
    data = _json_script(page, "serialized-server-data")
    if isinstance(data, (dict, list)):
        anns = _annotations(data, [])
        iap_anns = [a for a in anns if _is_iap_annotation(a)]
        if iap_anns:
            pairs = [(str(it.get("leadingText") or "").strip(), str(it.get("trailingText") or "").strip())
                     for it in iap_anns[0].get("items") or []
                     if isinstance(it, dict) and it.get("$kind") == "textPair" and it.get("trailingText")]
            if not pairs:
                raise PageParseError("the in-app purchase block has no name/price rows")
        elif any(it.get("$kind") == "textPair" and looks_like_price(it.get("trailingText"))
                 for a in anns for it in a.get("items") or [] if isinstance(it, dict)):
            raise PageParseError("price rows without the in-app purchase marker (page layout changed?)")
        elif anns:
            pairs = []  # the information shelf parsed and shows no in-app purchases
    if pairs is None:
        pairs, source = _text_fallback(page), "text"
    if pairs is None:
        raise PageParseError("no structured page data and no in-app purchase heading")
    iap = [{"name": trim(n, 120), "price_text": _SPACES.sub(" ", p).strip(), "price": parse_price(p), "currency": currency}
           for n, p in pairs]
    rating = (ld.get("aggregateRating") or {}) if isinstance(ld, dict) else {}
    return {"upfront_price": upfront, "currency": currency, "iap": iap, "iap_count": len(iap),
            "iap_capped": len(iap) >= IAP_SHOWN_MAX, "parsed_from": source,
            "page_rating": {"value": rating.get("ratingValue"), "count": rating.get("reviewCount")} if rating else None}


def fetch_product_page(http: Http, aid: str, cc: str) -> dict:
    return parse_product_page(http.get_text(PAGE_URL.format(cc=cc, id=aid)))


# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------


def cdir_of(home: Path) -> Path:
    return home / "competitors"


def load_config(home: Path) -> dict:
    cfg = dict(DEFAULT_CONFIG)
    cfg["apps"] = {}
    raw = read_json(cdir_of(home) / "config.json", {}) or {}
    cfg.update({k: v for k, v in raw.items() if k in ("countries", "review_pages", "apps", "demo")})
    if not isinstance(cfg.get("apps"), dict):
        cfg["apps"] = {}
    return cfg


def save_config(home: Path, cfg: dict) -> None:
    write_json(cdir_of(home) / "config.json", cfg)


def account_apps(home: Path) -> list[dict]:
    apps = read_json(home / "raw" / "apps.json", []) or []
    return [a for a in apps if isinstance(a, dict) and a.get("id")]


def descriptive(name: str) -> str:
    """'CUStats Go - AI Usage Tracker' -> 'AI Usage Tracker'; 'Bear: Markdown Notes' -> 'Markdown Notes'."""
    for sep in (":", " - ", " – ", " — ", " | "):
        if sep in name:
            tail = name.split(sep, 1)[1].strip()
            if len(tail) >= 3:
                return tail
    return name.strip()


def lookup_any(http: Http, ids: list[str], countries: list[str]) -> tuple[dict, list[dict]]:
    found, errors = {}, []
    for cc in countries:
        missing = [i for i in ids if i not in found]
        if not missing:
            break
        try:
            for k, v in lookup(http, missing, cc).items():
                found[k] = dict(v, country=cc)
        except Exception as exc:  # noqa: BLE001 - recorded, never fatal on its own
            errors.append({"source": "lookup", "country": cc, "kind": err_kind(exc), "message": trim(exc, 160)})
    return found, errors


# --------------------------------------------------------------------------
# discover / add / remove / config / status
# --------------------------------------------------------------------------


def cmd_discover(args) -> int:
    home = resolve_home(args.data_dir)
    own_id = str(args.app)
    if not valid_id(own_id):
        raise CompError(f"--app '{own_id}' is not an App Store id.", "Pass the numeric app id (the digits after 'id' in its App Store URL).")
    cc = args.country.lower()
    http = Http()
    try:
        own = lookup(http, [own_id], cc).get(own_id)
    except Exception as exc:  # noqa: BLE001
        raise CompError(f"lookup of {own_id} failed ({err_kind(exc)}).", "Check the network and rerun; nothing was saved.")
    if not own:
        raise CompError(f"app {own_id} is not on the {cc.upper()} App Store.", "Pass --country with a storefront where it is listed.")
    mine = account_apps(home)
    local = next((a for a in mine if str(a["id"]) == own_id), None)
    name = (local or {}).get("name") or own["name"] or own_id
    cfg = load_config(home)  # read-only: discover never writes
    configured = ((cfg["apps"].get(own_id) or {}).get("terms")) or []
    terms = []
    for t in (args.term or [descriptive(name)]) + configured:
        if t and t.strip() and t.strip().lower() not in [x.lower() for x in terms]:
            terms.append(t.strip())
    platform = platform_of(own)
    excluded = {str(a["id"]) for a in mine} | {own_id}
    cands, errors, dropped = {}, [], set()
    for t in terms:
        try:
            results = search(http, t, platform, cc)
        except Exception as exc:  # noqa: BLE001
            errors.append({"source": "search", "term": t, "kind": err_kind(exc), "message": trim(exc, 160)})
            continue
        for pos, r in enumerate(results, 1):
            if r["id"] in excluded or (own.get("seller") and r.get("seller") == own["seller"]):
                dropped.add(r["id"])
                continue
            c = cands.setdefault(r["id"], dict(r, terms={}))
            c["terms"][t] = pos
    if errors and not cands and len(errors) == len(terms):
        emit({"own": {"id": own_id, "name": name}, "errors": errors})
        return 1
    for c in cands.values():
        c["relevant"] = c.get("genre_id") == own.get("genre_id") or min(c["terms"].values()) <= RELEVANT_POS
    # Relevant first (same genre or top search hit), then by public rating count.
    ranked = sorted(cands.values(), key=lambda c: (not c["relevant"], -(c.get("ratings") or 0), min(c["terms"].values())))
    emit({
        "own": {"id": own_id, "name": name, "seller": own.get("seller"), "platform": platform, "genre": own.get("genre"),
                "ratings": own.get("ratings"), "avg": own.get("avg"), "price": own.get("formatted_price")},
        "country": cc, "terms": terms, "dropped_own_apps": len(dropped),
        "candidates": [{
            "id": c["id"], "name": c["name"], "seller": c["seller"], "ratings": c.get("ratings"),
            "avg": round(c["avg"], 2) if c.get("avg") is not None else None, "price": c.get("formatted_price"),
            "genre": c.get("genre"), "same_genre": c.get("genre_id") == own.get("genre_id"), "relevant": c["relevant"],
            "last_release": (c.get("version_date") or "")[:10] or None, "search_positions": c["terms"],
        } for c in ranked[: args.limit]],
        "errors": errors,
        "note": "read-only: nothing saved. Confirm picks with the user, then run `competitors.py add --app <id> <ids...>`.",
    })
    return 3 if errors else 0


def cmd_add(args) -> int:
    home = resolve_home(args.data_dir)
    own_id = str(args.app)
    ids = [str(x) for x in args.ids]
    bad = [x for x in [own_id] + ids if not valid_id(x)]
    if bad:
        raise CompError(f"not App Store ids: {', '.join(bad)}.", "Pass numeric app ids (from `discover` or the App Store URL).")
    if own_id in ids:
        raise CompError("an app cannot be its own competitor.", f"Remove {own_id} from the competitor ids.")
    mine = {str(a["id"]) for a in account_apps(home)}
    clash = [x for x in ids if x in mine]
    if clash:
        raise CompError(f"{', '.join(clash)} are your own apps.", "Competitors must be other developers' apps.")
    with comp_lock(cdir_of(home)):
        cfg = load_config(home)
        group = cfg["apps"].get(own_id) or {"competitors": [], "terms": []}
        merged = list(dict.fromkeys([str(x) for x in group.get("competitors", [])] + ids))
        if len(merged) > MAX_COMPETITORS:
            raise CompError(f"{len(merged)} competitors for {own_id}; the limit is {MAX_COMPETITORS}.",
                            "Remove some with `competitors.py remove --app <id> <ids...>` first.")
        new = [x for x in merged if x not in group.get("competitors", [])]
        found, errors = lookup_any(Http(), [own_id] + new, cfg["countries"])
        if errors and not found:
            raise CompError("lookup failed for every configured country; nothing saved.", "Check the network and rerun `add`.")
        missing = [x for x in [own_id] + new if x not in found]
        if missing:
            raise CompError(f"not found on the {', '.join(c.upper() for c in cfg['countries'])} App Store: {', '.join(missing)}; nothing saved.",
                            "Check the ids, or add a storefront where they are listed with `config --countries`.")
        mixed = [x for x in new if platform_of(found[x]) != platform_of(found[own_id])]
        terms = list(group.get("terms", []))
        for t in args.term or []:
            if t.strip() and t.strip().lower() not in [x.lower() for x in terms]:
                terms.append(t.strip())
        cfg["apps"][own_id] = {"competitors": merged, "terms": terms}
        save_config(home, cfg)
    out = {"app": {"id": own_id, "name": found[own_id]["name"]},
           "competitors": [{"id": x, "name": (found.get(x) or {}).get("name")} for x in merged], "terms": terms,
           "config": str(cdir_of(home) / "config.json")}
    warn = []
    if mine and own_id not in mine:
        warn.append(f"{own_id} is not in raw/apps.json, so appstore-tracker will not show this group under an app.")
    if mixed:
        warn.append(f"{', '.join(mixed)} are on another platform than {own_id}; search rank compares within one platform.")
    if not terms:
        warn.append("no search terms: search position is not tracked until you add --term.")
    if warn:
        out["warnings"] = warn
    emit(out)
    return 0


def cmd_remove(args) -> int:
    home = resolve_home(args.data_dir)
    own_id = str(args.app)
    if not args.ids and not args.term:
        raise CompError("nothing to remove.", "Pass competitor ids and/or --term TEXT.")
    with comp_lock(cdir_of(home)):
        cfg = load_config(home)
        group = cfg["apps"].get(own_id)
        if not group:
            raise CompError(f"no competitor group for {own_id}.", "Run `competitors.py status` to list groups.")
        drop = {str(x) for x in args.ids or []}
        unknown = sorted(drop - set(map(str, group.get("competitors", []))))
        group["competitors"] = [x for x in group.get("competitors", []) if str(x) not in drop]
        dterms = {t.lower() for t in args.term or []}
        group["terms"] = [t for t in group.get("terms", []) if t.lower() not in dterms]
        if group["competitors"]:
            cfg["apps"][own_id] = group
        else:
            cfg["apps"].pop(own_id, None)
        save_config(home, cfg)
    emit({"app": own_id, "group": cfg["apps"].get(own_id) or "removed (no competitors left)",
          **({"not_in_group": unknown} if unknown else {})})
    return 0


def cmd_config(args) -> int:
    home = resolve_home(args.data_dir)
    changed = args.countries is not None or args.review_pages is not None
    if not changed:
        emit(dict(load_config(home), file=str(cdir_of(home) / "config.json")))
        return 0
    with comp_lock(cdir_of(home)):
        cfg = load_config(home)
        if args.countries is not None:
            ccs = [c.strip().lower() for c in args.countries.split(",") if c.strip()]
            if not ccs or any(not re.fullmatch(r"[a-z]{2}", c) for c in ccs):
                raise CompError(f"--countries '{args.countries}' is not a list of 2-letter storefront codes.", "Example: --countries us,de,jp")
            cfg["countries"] = list(dict.fromkeys(ccs))
        if args.review_pages is not None:
            if not 1 <= args.review_pages <= MAX_REVIEW_PAGES:
                raise CompError(f"--review-pages {args.review_pages} is out of range.", f"Use 1-{MAX_REVIEW_PAGES} (50 reviews per page).")
            cfg["review_pages"] = args.review_pages
        save_config(home, cfg)
    emit(dict(cfg, file=str(cdir_of(home) / "config.json")))
    return 0


def snapshot_files(home: Path) -> list[Path]:
    d = cdir_of(home) / "snapshots"
    return sorted(p for p in d.glob("*.json") if parse_day(p.stem)) if d.is_dir() else []


def cmd_status(args) -> int:
    home = resolve_home(args.data_dir)
    cfg = load_config(home)
    snaps = snapshot_files(home)
    state = read_json(cdir_of(home) / "state.json", {}) or {}
    analysis = read_json(home / "data" / "competitors.json", None)
    groups = [{"app": k, "competitors": len(v.get("competitors", [])), "terms": v.get("terms", [])} for k, v in cfg["apps"].items()]
    emit({
        "data_dir": str(home), "config_file": str(cdir_of(home) / "config.json"),
        "ready": any(g["competitors"] for g in groups), "countries": cfg["countries"], "review_pages": cfg["review_pages"],
        "groups": groups, "snapshots": len(snaps), "first_snapshot": snaps[0].stem if snaps else None,
        "last_snapshot": snaps[-1].stem if snaps else None, "last_fetch": state.get("last_fetch"),
        "analysis": {"file": str(home / "data" / "competitors.json"), "as_of": ((analysis or {}).get("meta") or {}).get("as_of")} if analysis else None,
        "demo": bool(cfg.get("demo")),
        **({} if groups else {"fix": "Run `competitors.py discover --app <id>`, confirm picks, then `add`."}),
    })
    return 0


# --------------------------------------------------------------------------
# fetch
# --------------------------------------------------------------------------


def merge_reviews(path: Path, fresh: list[dict]) -> int:
    store = read_json(path, {}) or {}
    new = 0
    for r in fresh:
        if r["id"] not in store:
            new += 1
        store[r["id"]] = r
    write_json(path, store)
    return new


def cmd_fetch(args) -> int:
    home = resolve_home(args.data_dir)
    cdir = cdir_of(home)
    cfg = load_config(home)
    groups = {k: v for k, v in cfg["apps"].items() if v.get("competitors")}
    if not groups:
        raise CompError("no competitor groups configured.", "Run `discover --app <id>`, confirm picks, then `add --app <id> <ids...>`.")
    if cfg.get("demo"):
        raise CompError("this is a demo data dir; fetch would mix live data into synthetic data.", "Use `analyze` on the demo, or a real data dir.")
    countries, pages = cfg["countries"], int(cfg.get("review_pages") or 3)
    run_day = today().isoformat()
    started = datetime.now().isoformat(timespec="seconds")
    ids = list(dict.fromkeys([g for g in groups] + [c for v in groups.values() for c in v["competitors"]]))
    http = Http()
    snap = {"date": run_day, "generated_at": started, "tool_version": VERSION, "countries": countries, "review_pages": pages,
            "groups": {k: {"competitors": list(v["competitors"]), "terms": list(v.get("terms", []))} for k, v in groups.items()},
            "apps": {}, "reviews": {}, "pages": {}, "charts": {}, "search": {}, "errors": []}
    errors = snap["errors"]
    reviews_new = 0
    with comp_lock(cdir):
        for cc in countries:
            log(f"[{cc}] lookup of {len(ids)} apps")
            try:
                found = lookup(http, ids, cc)
            except Exception as exc:  # noqa: BLE001
                errors.append({"source": "lookup", "country": cc, "kind": err_kind(exc), "message": trim(exc, 160)})
                found = None
            if found is not None:
                for aid in ids:
                    snap["apps"].setdefault(aid, {})[cc] = found.get(aid) or {"listed": False}
            for aid in ids:
                log(f"[{cc}] reviews {aid}")
                try:
                    got, cov = fetch_reviews(http, aid, cc, pages)
                except Exception as exc:  # noqa: BLE001
                    errors.append({"source": "reviews", "app": aid, "country": cc, "kind": err_kind(exc), "message": trim(exc, 160)})
                    continue
                reviews_new += merge_reviews(cdir / "reviews" / f"{aid}.json", got)
                snap["reviews"].setdefault(aid, {})[cc] = cov
            for aid in ids:
                if found is not None and not (found.get(aid) or {}).get("listed"):
                    snap["pages"].setdefault(aid, {})[cc] = {"iap": None, "listed": False}  # not sold here: no page, no error
                    continue
                log(f"[{cc}] product page {aid}")
                try:
                    snap["pages"].setdefault(aid, {})[cc] = fetch_product_page(http, aid, cc)
                except Exception as exc:  # noqa: BLE001 - unknown, never "no in-app purchases"
                    kind = "parse" if isinstance(exc, PageParseError) else err_kind(exc)
                    snap["pages"].setdefault(aid, {})[cc] = {"iap": None, "error": kind}
                    errors.append({"source": "product_page", "app": aid, "country": cc, "kind": kind, "message": trim(exc, 160)})
            chart_cache, search_cache = {}, {}
            for own, g in groups.items():
                rec = (snap["apps"].get(own) or {}).get(cc) or {}
                platform = platform_of(rec) if rec.get("listed") else None
                group_ids = [own] + g["competitors"]
                ch = {"genre_id": rec.get("genre_id"), "genre": rec.get("genre")}
                if platform == "mac":
                    ch.update(available=False, reason="Apple publishes no Mac genre top charts in the RSS feed")
                elif not rec.get("genre_id"):
                    ch.update(available=False, reason="own app not listed or genre unknown in this storefront")
                else:
                    ch["available"] = True
                    for kind, feed in CHART_FEEDS.items():
                        key = (feed, rec["genre_id"])
                        if key not in chart_cache:
                            try:
                                chart_cache[key] = chart_ids(http, feed, rec["genre_id"], cc)
                            except Exception as exc:  # noqa: BLE001
                                chart_cache[key] = exc
                        res = chart_cache[key]
                        if isinstance(res, Exception):
                            ch[kind] = {"error": err_kind(res)}
                            errors.append({"source": "chart", "app": own, "country": cc, "chart": kind, "kind": err_kind(res), "message": trim(res, 160)})
                        elif not res:
                            ch[kind] = {"entries": 0, "ranks": {}, "unavailable": True}
                        else:
                            ch[kind] = {"entries": len(res), "ranks": {i: res.index(i) + 1 for i in group_ids if i in res}}
                    if all((ch.get(k) or {}).get("unavailable") for k in CHART_FEEDS):
                        ch.update(available=False, reason="the genre chart feed returned no entries")
                snap["charts"].setdefault(own, {})[cc] = ch
                for term in g.get("terms", []):
                    if platform is None:
                        continue
                    key = (term.lower(), platform)
                    if key not in search_cache:
                        try:
                            search_cache[key] = [r["id"] for r in search(http, term, platform, cc)]
                        except Exception as exc:  # noqa: BLE001
                            search_cache[key] = exc
                    res = search_cache[key]
                    if isinstance(res, Exception):
                        errors.append({"source": "search", "app": own, "country": cc, "term": term, "kind": err_kind(res), "message": trim(res, 160)})
                        continue
                    snap["search"].setdefault(own, {}).setdefault(cc, {})[term] = {
                        "entries": len(res), "positions": {i: (res.index(i) + 1 if i in res else None) for i in group_ids}}
        if not snap["apps"]:
            write_json(cdir / "state.json", {"last_fetch": {"date": run_day, "started": started, "finished": datetime.now().isoformat(timespec="seconds"),
                                                            "fatal": True, "errors": errors[:20]}})
            emit({"snapshot": None, "errors": errors, "fix": "Every lookup failed: check the network and rerun `fetch`."})
            return 1
        path = cdir / "snapshots" / f"{run_day}.json"
        write_json(path, snap)  # one per day: a same-day rerun overwrites
        write_json(cdir / "state.json", {"last_fetch": {"date": run_day, "started": started, "finished": datetime.now().isoformat(timespec="seconds"),
                                                        "partial": bool(errors), "errors": len(errors), "calls": http.calls}})
    emit({"snapshot": str(path), "date": run_day, "groups": len(groups), "apps": len(ids), "countries": countries,
          "calls": http.calls, "reviews_new": reviews_new, "errors": errors, **({"notes": http.notes} if http.notes else {}),
          "next": "competitors.py analyze"})
    return 3 if errors else 0


# --------------------------------------------------------------------------
# analyze
# --------------------------------------------------------------------------


def sig(scope, kind, severity, title, detail, **metrics) -> dict:
    return {"id": f"{scope}/{kind}", "scope": scope, "kind": kind, "severity": severity, "title": title, "detail": detail,
            "metrics": {k: v for k, v in metrics.items() if v is not None}}


def load_snapshots(home: Path) -> list[dict]:
    out = []
    for p in snapshot_files(home):
        s = read_json(p, {}) or {}
        if isinstance(s, dict) and parse_day(s.get("date")):
            out.append(s)
    return sorted(out, key=lambda s: s["date"])


def rec_in(snap: dict | None, aid: str, cc: str) -> dict:
    return (((snap or {}).get("apps") or {}).get(aid) or {}).get(cc) or {}


def baseline_snap(snaps: list[dict], as_of: date, days: int, aid: str, cc: str, need: str = "ratings") -> dict | None:
    """Newest snapshot at least `days` old that holds `need` for the app."""
    for s in reversed(snaps):
        d = parse_day(s["date"])
        if d <= as_of - timedelta(days=days) and rec_in(s, aid, cc).get(need) is not None:
            return s
    return None


def ref_snap(snaps: list[dict], as_of: date, aid: str, cc: str, key: str, days: int = 7) -> dict | None:
    """Reference for 'change' metrics: the newest snapshot at least `days` old, else the oldest one."""
    older = [s for s in snaps[:-1] if rec_in(s, aid, cc).get(key) is not None]
    week = [s for s in older if parse_day(s["date"]) <= as_of - timedelta(days=days)]
    return week[-1] if week else (older[0] if older else None)


TIER_RULES = (  # heuristic: first match on the product name wins
    ("weekly", r"\bweek(ly)?\b|\b7[- ]?days?\b"),
    ("monthly", r"\bmonth(ly)?\b|\b1[- ]?month\b"),
    ("yearly", r"\byear(ly)?\b|\bannual(ly)?\b|\b12[- ]?months?\b"),
    ("lifetime", r"\blife[- ]?time\b|\bforever\b|\bpermanent\b|\bone[- ]?time\b|\blifelong\b"),
    ("remove_ads", r"\b(remove|no|block)[- ]?ads?\b|\bad[- ]?free\b|\bads[- ]?free\b"),
    ("tip", r"\btip(s|\s+jar)?\b|\bcoffee\b|\bdonat|\blunch\b|\bbeer\b|\bawesome\b|\bthank|\bsupport (the )?dev"),
    ("consumable", r"\bcoins?\b|\bcredits?\b|\bgems?\b|\btokens?\b|\bpoints\b|\b\d+\s*(x|pcs|uses)\b"),
    ("unlock", r"\bpro\b|\bpremium\b|\bplus\b|\bfull\b|\bunlock|\bupgrade\b|\bvip\b"),
)
PERIODS = ("weekly", "monthly", "yearly")
ZERO_DECIMAL = {"JPY", "KRW", "CLP", "VND", "HUF", "TWD", "ISK", "IDR", "COP"}


def tier_of(name) -> str:
    for kind, rx in TIER_RULES:
        if re.search(rx, str(name or ""), re.I):
            return kind
    return "other"


def money(v, cur) -> str | None:
    if v is None:
        return None
    num = f"{v:,.0f}" if cur in ZERO_DECIMAL else f"{v:,.2f}"
    return f"${num}" if cur == "USD" else f"{num} {cur or ''}".strip()


def page_in(snap: dict | None, aid: str, cc: str) -> dict:
    return (((snap or {}).get("pages") or {}).get(aid) or {}).get(cc) or {}


def pricing_of(page: dict, rec: dict) -> dict:
    """Upfront price, model and heuristically labelled in-app purchases for one app in one storefront."""
    upfront = page.get("upfront_price") if page.get("upfront_price") is not None else rec.get("price")
    cur = page.get("currency") or rec.get("currency")
    iap = page.get("iap")
    if upfront is None:
        model = None
    elif upfront > 0:
        model = "paid"
    else:
        model = None if iap is None else ("freemium" if iap else "free")
    items = None if iap is None else [dict(x, tier=tier_of(x.get("name"))) for x in iap]
    priced = [x for x in items or [] if x.get("price") is not None]
    pick = lambda x: {"name": x["name"], "price_text": x.get("price_text"), "price": x["price"], "tier": x["tier"]}  # noqa: E731
    entry, basis = None, None
    if model == "paid":
        entry, basis = upfront, "upfront price"
    elif model == "free":
        entry, basis = 0.0, "free, no in-app purchases"
    elif model == "freemium":
        real = [x["price"] for x in priced if x["tier"] not in ("tip", "consumable")]
        entry, basis = (min(real), "cheapest in-app purchase (tips and consumables excluded)") if real else (0.0, "free to use: only tips or consumables")
    tiers = {}
    for x in priced:
        if x["tier"] != "other":
            t = tiers.setdefault(x["tier"], {"count": 0, "from": x["price"], "from_text": x.get("price_text")})
            t["count"] += 1
            if x["price"] < t["from"]:
                t["from"], t["from_text"] = x["price"], x.get("price_text")
    kinds = {x["tier"] for x in items or []}
    out = {
        "upfront": upfront, "upfront_text": rec.get("formatted_price") if rec.get("price") == upfront else money(upfront, cur),
        "currency": cur, "model": model, "entry_price": entry, "entry_text": money(entry, cur), "entry_basis": basis,
        "iap": items, "iap_count": None if items is None else len(items), "iap_capped": bool(page.get("iap_capped")),
        "cheapest": pick(min(priced, key=lambda x: x["price"])) if priced else None,
        "most_expensive": pick(max(priced, key=lambda x: x["price"])) if priced else None,
        "tiers": tiers if items is not None else None,
        "offers": None if items is None else {"free_download": upfront == 0 if upfront is not None else None,
                                               "subscription": bool(kinds & set(PERIODS)), "weekly": "weekly" in kinds,
                                               "lifetime": "lifetime" in kinds, "remove_ads": "remove_ads" in kinds, "tips": "tip" in kinds},
        "tiers_heuristic": "tier labels are guessed from product names",
    }
    if items is None:
        out["iap_unknown_reason"] = ("not listed in this storefront" if page.get("listed") is False
                                     else f"product page failed ({page['error']})" if page.get("error")
                                     else "no product page in this snapshot")
    return out


def iap_diff(old: list[dict], new: list[dict]) -> dict | None:
    """Multiset diff of (name, price): page order is not stable, and names can repeat."""
    from collections import Counter
    key = lambda x: (x.get("name"), x["price"] if x.get("price") is not None else x.get("price_text"))  # noqa: E731
    oc, nc = Counter(map(key, old)), Counter(map(key, new))

    def take(items, extra):  # the surplus rows, in page order
        out = []
        for x in items:
            if extra[key(x)] > 0:
                extra[key(x)] -= 1
                out.append(x)
        return out
    removed, added = take(old, oc - nc), take(new, nc - oc)
    changed = []
    for r in list(removed):
        a = next((x for x in added if x.get("name") == r.get("name")), None)
        if a:
            changed.append({"name": r["name"], "from": r.get("price_text"), "to": a.get("price_text"),
                            "from_value": r.get("price"), "to_value": a.get("price")})
            removed.remove(r)
            added.remove(a)
    if not (changed or added or removed):
        return None
    slim_ = lambda x: {"name": x.get("name"), "price_text": x.get("price_text"), "price": x.get("price")}  # noqa: E731
    return {"changed": changed, "added": [slim_(x) for x in added], "removed": [slim_(x) for x in removed]}


def iap_change(snaps: list[dict], as_of: date, aid: str, cc: str, days: int = 7) -> dict | None:
    """IAP list now vs the newest snapshot at least `days` old with a known list in the same currency (else the oldest)."""
    cur = page_in(snaps[-1], aid, cc)
    if cur.get("iap") is None:
        return None
    older = [s for s in snaps[:-1] if page_in(s, aid, cc).get("iap") is not None
             and page_in(s, aid, cc).get("currency") == cur.get("currency")]
    week = [s for s in older if parse_day(s["date"]) <= as_of - timedelta(days=days)]
    ref = week[-1] if week else (older[0] if older else None)
    if not ref:
        return None
    old = page_in(ref, aid, cc)
    d = iap_diff(old["iap"], cur["iap"])
    if d:
        d["since"] = ref["date"]
        d["capped"] = bool(old.get("iap_capped") or cur.get("iap_capped")) or None
    return d


def chart_pos(snap: dict | None, own: str, cc: str, aid: str) -> dict:
    ch = (((snap or {}).get("charts") or {}).get(own) or {}).get(cc)
    if not ch:
        return {"available": None}
    if not ch.get("available"):
        return {"available": False, "reason": ch.get("reason")}
    for kind in CHART_FEEDS:
        c = ch.get(kind) or {}
        if aid in (c.get("ranks") or {}):
            return {"available": True, "chart": kind, "rank": c["ranks"][aid], "entries": c.get("entries")}
    return {"available": True, "chart": None, "rank": None,
            "entries": {k: (ch.get(k) or {}).get("entries") for k in CHART_FEEDS},
            "errors": [k for k in CHART_FEEDS if (ch.get(k) or {}).get("error")] or None}


def review_metrics(store: dict, as_of: date, coverage: dict, countries: list[str]) -> dict:
    revs = [r for r in store.values() if isinstance(r, dict) and parse_day(r.get("date")) and r.get("country") in countries]
    out = {}
    for w in REVIEW_WINDOWS:
        lo = as_of - timedelta(days=w - 1)
        sel = [r for r in revs if lo <= parse_day(r["date"]) <= as_of]
        # A window reaching past what the capped feed returned is a lower bound, never a full count.
        lb = False
        for cc in countries:
            cov = coverage.get(cc)
            if cov and not cov.get("complete"):
                oldest = min((parse_day(r["date"]) for r in revs if r["country"] == cc), default=None)
                if oldest is None or oldest > lo:
                    lb = True
        out[f"reviews_{w}d"] = len(sel)
        out.setdefault("reviews_lower_bound", {})[f"{w}d"] = lb
        if w == 90:
            out["avg_stars_90d"] = round(sum(r["rating"] for r in sel) / len(sel), 2) if sel else None
    return out


def review_sample(store: dict, countries: list[str]) -> list[dict]:
    revs = sorted((r for r in store.values() if isinstance(r, dict) and r.get("country") in countries),
                  key=lambda r: r.get("date") or "", reverse=True)
    low = [r for r in revs if (r.get("rating") or 5) <= 2][:10]
    high = [r for r in revs if (r.get("rating") or 0) >= 4][:5]
    return [{"id": r["id"], "date": r["date"], "rating": r["rating"], "version": r.get("version"), "country": r.get("country"),
             "title": trim(r.get("title"), 100), "body": trim(r.get("body"), 300)} for r in low + high]


def app_metrics(home, snaps, own, aid, role, terms, cc, countries) -> dict:
    latest = snaps[-1]
    as_of = parse_day(latest["date"])
    cur = rec_in(latest, aid, cc)
    m = {"id": aid, "role": role, "name": cur.get("name"), "seller": cur.get("seller"),
         "listed": cur.get("listed") if cur else None, "url": cur.get("url"), "icon": cur.get("icon")}
    if not cur:  # added after the last fetch, or the lookup failed: unknown, not zero
        m["no_data"] = True
        for s in reversed(snaps):
            older = rec_in(s, aid, cc)
            if older.get("name"):
                m["name"], m["seller"] = older["name"], older.get("seller")
                break
    m["ratings"], m["avg_rating"] = cur.get("ratings"), (round(cur["avg"], 2) if cur.get("avg") is not None else None)
    m["ratings_by_country"] = {c: {"ratings": rec_in(latest, aid, c).get("ratings"), "avg": rec_in(latest, aid, c).get("avg")}
                               for c in countries if rec_in(latest, aid, c)}
    for w in DELTA_WINDOWS:
        base = baseline_snap(snaps, as_of, w, aid, cc) if m["ratings"] is not None else None
        if m["ratings"] is None:
            m[f"ratings_delta_{w}d"] = {"value": None, "reason": "no public rating count in this storefront"}
        elif base:
            m[f"ratings_delta_{w}d"] = {"value": m["ratings"] - rec_in(base, aid, cc)["ratings"], "baseline_date": base["date"],
                                        "span_days": (as_of - parse_day(base["date"])).days}
        else:
            m[f"ratings_delta_{w}d"] = {"value": None, "baseline": True}
    store = read_json(cdir_of(home) / "reviews" / f"{aid}.json", {}) or {}
    coverage = ((latest.get("reviews") or {}).get(aid)) or {}
    if coverage:
        m.update(review_metrics(store, as_of, coverage, countries))
    else:
        m.update({f"reviews_{w}d": None for w in REVIEW_WINDOWS}, avg_stars_90d=None, reviews_lower_bound=None)
    m["version"], m["version_date"] = cur.get("version"), (cur.get("version_date") or "")[:10] or None
    vd = parse_day(m["version_date"])
    m["days_since_release"] = (as_of - vd).days if vd else None
    versions = [rec_in(s, aid, cc).get("version") for s in snaps if rec_in(s, aid, cc).get("version")]
    m["version_changes"] = sum(1 for a, b in zip(versions, versions[1:]) if a != b)
    m["price"], m["formatted_price"] = cur.get("price"), cur.get("formatted_price")
    ps = ref_snap(snaps, as_of, aid, cc, "price")
    p_old = rec_in(ps, aid, cc) if ps else {}
    m["price_change"] = ({"from": p_old.get("formatted_price"), "to": m["formatted_price"], "from_value": p_old.get("price"),
                          "to_value": m["price"], "since": ps["date"]}
                         if ps and m["price"] is not None and p_old.get("price") != m["price"] else None)
    m["pricing"] = pricing_of(page_in(latest, aid, cc), cur)
    m["pricing"]["iap_change"] = iap_change(snaps, as_of, aid, cc)
    ch = chart_pos(latest, own, cc, aid)
    if ch.get("available"):
        # Compare with the newest snapshot a week old, else the previous one.
        older = [s for s in snaps[:-1] if parse_day(s["date"]) <= as_of - timedelta(days=7)]
        ref = older[-1] if older else (snaps[-2] if len(snaps) > 1 else None)
        if ref:
            pv = chart_pos(ref, own, cc, aid)
            if pv.get("available"):
                ch["vs"] = ref["date"]
                ch["prev_rank"], ch["prev_chart"] = pv.get("rank"), pv.get("chart")
                if pv.get("rank") and ch.get("rank") and pv.get("chart") == ch.get("chart"):
                    ch["change"] = pv["rank"] - ch["rank"]  # positive = moved up
    m["chart"] = ch
    m["search"] = {}
    prev_any = snaps[-2] if len(snaps) > 1 else None
    for t in terms:
        cur_t = ((((latest.get("search") or {}).get(own) or {}).get(cc) or {}).get(t))
        if not cur_t:
            m["search"][t] = {"position": None, "unknown": True}
            continue
        pos = (cur_t.get("positions") or {}).get(aid)
        prev_t = ((((prev_any or {}).get("search") or {}).get(own) or {}).get(cc) or {}).get(t) if prev_any else None
        pp = (prev_t.get("positions") or {}).get(aid) if prev_t else None
        m["search"][t] = {"position": pos, "entries": cur_t.get("entries"), "prev": pp if prev_t else None,
                          "change": (pp - pos) if (pos and pp) else None, "vs": prev_any["date"] if prev_t else None}
    if role == "competitor":
        m["review_sample"] = review_sample(store, countries)
    return m


def median(xs: list[float]) -> float | None:
    xs = sorted(xs)
    if not xs:
        return None
    mid = len(xs) // 2
    return xs[mid] if len(xs) % 2 else round((xs[mid - 1] + xs[mid]) / 2, 2)


def pricing_compare(apps: list[dict]) -> dict:
    """Own app's pricing vs the group, same storefront and currency only."""
    me = apps[0].get("pricing") or {}
    cur = me.get("currency")
    comps = [a for a in apps[1:] if (a.get("pricing") or {}).get("currency") in (cur, None) or cur is None]
    cp = [a["pricing"] for a in comps]
    up = [p for p in cp if p.get("upfront") is not None]
    entries = [(p["entry_price"], a) for p, a in zip(cp, comps) if p.get("entry_price") is not None]
    iap_known = [p for p in cp if p.get("offers")]
    low = min(entries, key=lambda e: e[0]) if entries else None
    return {
        "currency": cur, "own_model": me.get("model"), "own_upfront": me.get("upfront"), "own_entry": me.get("entry_price"),
        "competitors_upfront_known": len(up), "competitors_free_download": sum(1 for p in up if p["upfront"] == 0),
        "competitors_models": {m: sum(1 for p in cp if p.get("model") == m) for m in ("paid", "freemium", "free")},
        "competitor_entry_known": len(entries), "competitor_entry_median": median([e for e, _ in entries]),
        "competitor_entry_min": low[0] if low else None,
        "competitor_entry_min_app": {"id": low[1]["id"], "name": low[1].get("name")} if low else None,
        "competitors_iap_known": len(iap_known),
        "competitors_with": {k: sum(1 for p in iap_known if p["offers"].get(k)) for k in ("subscription", "weekly", "lifetime", "remove_ads")},
        "own_offers": me.get("offers"),
        "excluded_other_currency": len(apps) - 1 - len(comps) or None,
        "note": "entry price = upfront price, or the cheapest in-app purchase of a free download (tips and consumables excluded); tier labels are heuristic",
    }


def pricing_signals(own: str, g: dict, name: str, cc: str) -> list[dict]:
    out = []
    P = g.get("pricing") or {}
    me = (g["apps"][0].get("pricing") or {})
    cur = P.get("currency")
    reasons, n_up, n_free = [], P.get("competitors_upfront_known") or 0, P.get("competitors_free_download") or 0
    if (P.get("own_upfront") or 0) > 0 and n_up >= PRICING_MIN_KNOWN and n_free / n_up >= PRICING_FREE_SHARE:
        reasons.append(f"{name} costs {me.get('upfront_text') or money(P['own_upfront'], cur)} upfront while {n_free} of {n_up} competitors are free to download")
    med, own_e = P.get("competitor_entry_median"), P.get("own_entry")
    ratio = round(own_e / med, 1) if (own_e is not None and med) else None
    if ratio and (P.get("competitor_entry_known") or 0) >= PRICING_MIN_KNOWN and own_e > PRICING_ENTRY_RATIO * med:
        reasons.append(f"its entry price {money(own_e, cur)} is {ratio}× the competitors' median entry price {money(med, cur)}")
    if reasons:
        low = P.get("competitor_entry_min_app") or {}
        out.append(sig(own, "competitor_pricing_gap", "warning", reasons[0][0].upper() + reasons[0][1:] if len(reasons) == 1 else f"{name} is priced well above its competitors",
                       "; ".join(reasons) + f" ({cc.upper()} storefront). Lowest competitor entry: {low.get('name') or '—'} at {money(P.get('competitor_entry_min'), cur) or '—'}. "
                       "Prices are per storefront; tier labels are guessed from product names.",
                       currency=cur, own_model=P.get("own_model"), own_upfront=P.get("own_upfront"), own_entry=own_e,
                       competitors_upfront_known=n_up, competitors_free_download=n_free, competitor_entry_median=med,
                       competitor_entry_min=P.get("competitor_entry_min"), entry_ratio=ratio))
    own_offers, n_iap = P.get("own_offers"), P.get("competitors_iap_known") or 0
    # A paid-upfront app already sells permanent access and usually shows no ads: compare like with like.
    if own_offers is not None and P.get("own_model") in ("free", "freemium") and n_iap >= PRICING_MIN_KNOWN:
        labels = {"lifetime": "a lifetime purchase", "remove_ads": "a remove-ads purchase", "subscription": "a subscription"}
        for kind, what in labels.items():
            k = (P.get("competitors_with") or {}).get(kind) or 0
            if not own_offers.get(kind) and k / n_iap > OFFER_SHARE:
                sellers = [a.get("name") for a in g["apps"][1:] if ((a.get("pricing") or {}).get("offers") or {}).get(kind)]
                out.append(sig(own, f"competitor_offer_gap_{kind}", "info", f"{k} of {n_iap} competitors sell {what}; {name} does not",
                               f"From the in-app purchase names on their {cc.upper()} product pages (heuristic labels): {', '.join(sellers)}."
                               + (" Only relevant if your app shows ads." if kind == "remove_ads" else ""),
                               offer=kind, competitors_with=k, competitors_known=n_iap, sellers=sellers))
    return out


def change_text(pc: dict | None, ic: dict | None) -> list[str]:
    parts = [f"price {pc['from']} → {pc['to']}"] if pc else []
    for c in (ic or {}).get("changed", []):
        parts.append(f"{c['name']} {c['from']} → {c['to']}")
    for x in (ic or {}).get("added", []):
        parts.append(f"new {x['name']} {x['price_text']}")
    for x in (ic or {}).get("removed", []):
        parts.append(f"{x['name']} {x['price_text']} " + ("no longer among the 10 shown" if (ic or {}).get("capped") else "removed"))
    return parts


def group_signals(own: str, g: dict, snaps: list[dict], cc: str) -> list[dict]:
    out = []
    apps = g["apps"]
    me = apps[0]
    comps = apps[1:]
    name = me.get("name") or own
    as_of = parse_day(snaps[-1]["date"])
    first = snaps[0]["date"]
    if not any(parse_day(s["date"]) <= as_of - timedelta(days=7) for s in snaps):
        ready = (parse_day(first) + timedelta(days=7)).isoformat()
        out.append(sig(own, "competitor_baseline", "info", "Competitor tracking is building its baseline",
                       f"The first competitor snapshot is from {first} ({len(snaps)} day(s) so far). Rating deltas start on {ready}; review counts from the RSS feed are already usable.",
                       first_snapshot=first, snapshot_days=len(snaps), deltas_from=ready))
    own_rv = me.get("reviews_28d")
    if own_rv is not None:
        fast = [c for c in comps if c.get("reviews_28d") is not None and c["reviews_28d"] >= OUTPACE_MIN
                and c["reviews_28d"] >= OUTPACE_RATIO * max(own_rv, 0) and (own_rv > 0 or c["reviews_28d"] >= OUTPACE_MIN)]
        fast.sort(key=lambda c: -c["reviews_28d"])
        if fast:
            top = fast[0]
            lb = any((c.get("reviews_lower_bound") or {}).get("28d") for c in fast)
            out.append(sig(own, "competitor_outpacing", "warning",
                           f"{top['name']} got {'≥' if lb else ''}{top['reviews_28d']} written reviews in 28 days vs {own_rv} for {name}",
                           f"{len(fast)} competitor(s) collected at least {OUTPACE_RATIO:g}× your written reviews in the last 28 days ({cc.upper()} and the other tracked storefronts). "
                           "Written reviews are a proxy for active users, not downloads or revenue.",
                           proxy="written reviews (public RSS)", own_reviews_28d=own_rv, lower_bound=lb or None,
                           competitors=[{"id": c["id"], "name": c["name"], "reviews_28d": c["reviews_28d"]} for c in fast]))
    for c in comps:
        vd = parse_day(c.get("version_date"))
        if vd and (as_of - vd).days <= RELEASE_DAYS:
            out.append(sig(own, f"competitor_release_{c['id']}", "info", f"{c['name']} shipped version {c.get('version')} on {vd.isoformat()}",
                           f"{c['name']} released {c.get('version')} {(as_of - vd).days} day(s) ago. Read its release notes and the reviews that follow.",
                           competitor_id=c["id"], version=c.get("version"), released=vd.isoformat()))
        pc, ic = c.get("price_change"), (c.get("pricing") or {}).get("iap_change")
        if pc or ic:
            parts = change_text(pc, ic)
            out.append(sig(own, f"competitor_price_change_{c['id']}", "info",
                           f"{c['name']} changed pricing: " + "; ".join(parts[:3]) + (f" (+{len(parts) - 3} more)" if len(parts) > 3 else ""),
                           f"In the {cc.upper()} storefront, compared with the snapshot about a week back ({(pc or ic)['since']}): " + "; ".join(parts) + ".",
                           competitor_id=c["id"], price_from=(pc or {}).get("from_value"), price_to=(pc or {}).get("to_value"),
                           since=(pc or {}).get("since"), iap_since=(ic or {}).get("since"),
                           iap_changed=(ic or {}).get("changed") or None, iap_added=(ic or {}).get("added") or None,
                           iap_removed=(ic or {}).get("removed") or None, iap_capped=(ic or {}).get("capped")))
        ch = c.get("chart") or {}
        if ch.get("available") and ch.get("vs") and ch.get("rank"):
            entries = ch.get("entries") if isinstance(ch.get("entries"), int) else 200
            prev = ch.get("prev_rank") if ch.get("prev_chart") in (None, ch.get("chart")) else None
            gain = (prev or entries + 1) - ch["rank"]
            if gain >= RANK_GAIN:
                mine = me.get("chart") or {}
                above = mine.get("chart") == ch.get("chart") and (not mine.get("rank") or mine["rank"] > ch["rank"])
                out.append(sig(own, f"competitor_rank_gain_{c['id']}", "warning" if above else "info",
                               f"{c['name']} climbed to #{ch['rank']} in top {ch['chart']} {g.get('genre') or ''}".rstrip(),
                               f"Up {gain} places since {ch['vs']} (was {'#' + str(prev) if prev else 'outside the top ' + str(entries)})."
                               + (f" It now ranks above {name} in the same chart." if above else ""),
                               competitor_id=c["id"], chart=ch["chart"], rank=ch["rank"], prev_rank=prev, gain=gain))
    for t in g.get("terms", []):
        mine = (me.get("search") or {}).get(t) or {}
        if mine.get("unknown"):
            continue
        best = sorted(((c["search"][t]["position"], c) for c in comps
                       if ((c.get("search") or {}).get(t) or {}).get("position")), key=lambda x: x[0])
        my = mine.get("position")
        kind = f"competitor_search_rank_{slug(t)}"
        if (my is None or my > SEARCH_OWN_OUT) and best and best[0][0] <= SEARCH_COMP_IN:
            out.append(sig(own, kind, "warning", f"Search '{t}': {name} {'#' + str(my) if my else 'not in top ' + str(mine.get('entries') or SEARCH_LIMIT)}, {best[0][1]['name']} #{best[0][0]}",
                           f"In {cc.upper()} App Store search for '{t}', a competitor sits in the top {SEARCH_COMP_IN} while {name} is outside the top {SEARCH_OWN_OUT}. Search order is approximate and can be personalised.",
                           term=t, own_position=my, competitor_id=best[0][1]["id"], competitor_position=best[0][0]))
        elif mine.get("prev") is not None or (my is not None and mine.get("vs")):
            pp = mine.get("prev")
            if pp != my:
                out.append(sig(own, kind, "info", f"Search '{t}': {name} {'#' + str(pp) if pp else 'unranked'} → {'#' + str(my) if my else 'unranked'}",
                               f"Position of {name} for '{t}' in {cc.upper()} search changed since {mine.get('vs')}.",
                               term=t, own_position=my, prev_position=pp))
    out.extend(pricing_signals(own, g, name, cc))
    my_avg, my_n = me.get("avg_rating"), me.get("ratings") or 0
    rated = [c for c in comps if c.get("avg_rating") is not None and (c.get("ratings") or 0) >= RATING_MIN_COUNT]
    if my_avg is not None and my_n >= 1 and rated:
        avg = round(sum(c["avg_rating"] for c in rated) / len(rated), 2)
        gap = round(avg - my_avg, 2)
        if abs(gap) >= RATING_GAP:
            up = gap > 0
            out.append(sig(own, "competitor_rating_gap", "warning" if up else "good",
                           f"Competitors average {avg}★ vs {my_avg}★ for {name}",
                           f"Mean public rating of {len(rated)} competitor(s) with at least {RATING_MIN_COUNT} ratings in {cc.upper()} is {abs(gap)}★ {'above' if up else 'below'} yours. Ratings are cumulative per storefront.",
                           competitors_avg=avg, own_avg=my_avg, gap=gap, competitors=len(rated)))
    return out


def cmd_analyze(args) -> int:
    home = resolve_home(args.data_dir)
    cfg = load_config(home)
    snaps = load_snapshots(home)
    if not snaps:
        raise CompError(f"no competitor snapshots in {cdir_of(home) / 'snapshots'}.", "Run `competitors.py fetch` first (or `demo` on a demo dir).")
    latest = snaps[-1]
    countries = latest.get("countries") or cfg["countries"]
    cc = countries[0]
    groups_cfg = {k: v for k, v in cfg["apps"].items() if v.get("competitors")} or latest.get("groups") or {}
    groups, signals = [], []
    for own, gc in groups_cfg.items():
        terms = list(gc.get("terms", []))
        apps = [app_metrics(home, snaps, own, own, "own", terms, cc, countries)]
        apps += [app_metrics(home, snaps, own, c, "competitor", terms, cc, countries) for c in gc["competitors"]]
        known = [a.get("reviews_28d") for a in apps]
        total = sum(x for x in known if x is not None)
        for a in apps:
            a["growth_share_28d"] = round(a["reviews_28d"] / total, 3) if total and a.get("reviews_28d") is not None and None not in known else None
        ch = (((latest.get("charts") or {}).get(own) or {}).get(cc)) or {}
        own_rec = next((rec_in(s, own, cc) for s in reversed(snaps) if rec_in(s, own, cc).get("kind")), {})
        g = {"app_id": own, "name": apps[0].get("name"), "platform": platform_of(own_rec) if own_rec else None,
             "country": cc, "as_of": latest["date"], "genre": ch.get("genre"), "genre_id": ch.get("genre_id"), "terms": terms,
             "chart": {"available": ch.get("available"), "reason": ch.get("reason"),
                       "entries": {k: (ch.get(k) or {}).get("entries") for k in CHART_FEEDS}},
             "apps": apps, "pricing": pricing_compare(apps)}
        sigs = group_signals(own, g, snaps, cc)
        g["signals"] = [s["id"] for s in sigs]
        groups.append(g)
        signals.extend(sigs)
    out = {
        "meta": {"tool": "appstore-competitor-tracker", "version": VERSION, "generated_at": datetime.now().isoformat(timespec="seconds"),
                 "as_of": latest["date"], "snapshot_days": len(snaps), "first_snapshot": snaps[0]["date"], "countries": countries,
                 "primary_country": cc, "errors": latest.get("errors") or [], "demo": bool(cfg.get("demo")),
                 "proxies": "ratings, written reviews (RSS), chart rank, search position; never downloads or revenue",
                 "pricing": "upfront price (lookup) and up to 10 in-app purchases from the public product page, per storefront; tier labels are heuristic",
                 "review_feed_cap": "the RSS feed returns at most 500 recent reviews per storefront; windows past it are lower bounds"},
        "groups": groups, "signals": signals,
    }
    path = home / "data" / "competitors.json"
    write_json(path, out)
    sev = {}
    for s in signals:
        sev[s["severity"]] = sev.get(s["severity"], 0) + 1
    emit({"file": str(path), "as_of": latest["date"], "snapshot_days": len(snaps), "groups": len(groups),
          "signals": sev, "errors_last_fetch": len(out["meta"]["errors"])})
    return 0


# --------------------------------------------------------------------------
# demo: synthetic competitor data for a `tracker.py demo` dir (no network)
# --------------------------------------------------------------------------


DEMO_OWN = {"900000001": "ios", "900000003": "mac"}
DEMO_COMP = {
    "900000101": ("Demo Rival Notes Pro", "Rival Labs (demo)", "ios", 0.0, "Free", 1200, 4.8, 2.4),
    "900000102": ("Demo Jot", "Jot Co (demo)", "ios", 4.99, "$4.99", 310, 4.7, 0.5),
    "900000103": ("Demo Quick Memo", "Memo Studio (demo)", "ios", 0.0, "Free", 95, 4.6, 0.2),
    "900000301": ("Demo DevKit", "DevKit Ltd (demo)", "mac", 9.99, "$9.99", None, None, 0.6),
    "900000302": ("Demo Terminal Buddy", "Buddy Apps (demo)", "mac", 0.0, "Free", None, None, 0.1),
}
DEMO_IAP = {  # (name, price); the rival's monthly price rises and a lifetime tier appears 2 days ago
    "900000001": [],
    "900000101": [("Pro Weekly", 2.99), ("Pro Monthly", 4.99), ("Pro Yearly", 29.99), ("Remove Ads", 1.99)],
    "900000102": [],
    "900000103": [("Remove Ads", 1.99), ("Tip Jar", 0.99)],
    "900000003": [("Monthly", 1.99), ("Yearly", 14.99)],
    "900000301": [("Lifetime Pro Upgrade", 19.99)],
    "900000302": [("Lifetime Unlock", 24.99), ("Yearly Plan", 9.99)],
}
DEMO_LOW = ["Sync lost my notes after the update", "Too many ads since the redesign", "Subscription price doubled",
            "Crashes when opening large files", "Search no longer finds old notes"]
DEMO_HIGH = ["Fast and clean", "Best widget on the store", "Great markdown support"]


def cmd_demo(args) -> int:
    if not args.data_dir:
        raise CompError("demo needs an explicit --data-dir.", "Run `tracker.py --data-dir DIR demo`, then `competitors.py --data-dir DIR demo`.")
    home = resolve_home(args.data_dir)
    tcfg = read_json(home / "config.json", {}) or {}
    if not tcfg.get("demo"):
        raise CompError(f"{home} is not a tracker demo dir.", "Create one with `tracker.py --data-dir DIR demo` first; demo never writes into real data.")
    names = {str(a["id"]): a.get("name") for a in account_apps(home)}
    if not all(i in names for i in DEMO_OWN):
        raise CompError("the demo apps are missing from raw/apps.json.", "Recreate the dir with `tracker.py --data-dir DIR demo`.")
    cdir = cdir_of(home)
    if cdir.exists():
        import shutil
        shutil.rmtree(cdir)
    rng = random.Random(args.seed)
    last = today()
    days = [last - timedelta(days=args.days - 1 - i) for i in range(args.days)]
    groups = {"900000001": {"competitors": ["900000101", "900000102", "900000103"], "terms": ["notes", "markdown notes"]},
              "900000003": {"competitors": ["900000301", "900000302"], "terms": ["developer tools"]}}
    save_config(home, {"countries": ["us"], "review_pages": 3, "apps": groups, "demo": True})
    own_meta = {"900000001": (names["900000001"], "Demo Developer", "ios", 2.99, "$2.99", 40, 4.2, 0.25),
                "900000003": (names["900000003"], "Demo Developer", "mac", 0.0, "Free", None, None, 0.1)}
    meta = dict(DEMO_COMP, **own_meta)
    reviews = {aid: {} for aid in meta}
    n_rev = 0
    for aid, (nm, _s, _p, _pr, _fp, _r, avg, rate) in meta.items():
        for d in days:
            k = sum(1 for _ in range(6) if rng.random() < rate / 6 * (1.8 if aid == "900000101" and d > last - timedelta(days=6) else 1))
            for _ in range(k):
                n_rev += 1
                low = rng.random() < (0.35 if aid == "900000102" else 0.12)
                rating = rng.choice([1, 2]) if low else rng.choice([4, 5, 5])
                title = rng.choice(DEMO_LOW if low else DEMO_HIGH)
                rid = f"demo-{aid}-{n_rev}"
                reviews[aid][rid] = {"id": rid, "date": d.isoformat(), "rating": rating, "version": "1.0", "country": "us",
                                     "title": title, "body": f"(synthetic demo review) {title}.", }
    for aid, store in reviews.items():
        write_json(cdir / "reviews" / f"{aid}.json", store)
    for i, d in enumerate(days):
        age = len(days) - 1 - i
        snap = {"date": d.isoformat(), "generated_at": d.isoformat() + "T09:00:00", "tool_version": VERSION, "demo": True,
                "countries": ["us"], "review_pages": 3, "groups": groups, "apps": {}, "reviews": {}, "pages": {}, "charts": {}, "search": {}, "errors": []}
        for aid, (nm, seller, plat, price, fprice, ratings, avg, rate) in meta.items():
            if aid == "900000102" and age >= 3:
                price, fprice = 4.99, "$4.99"
            elif aid == "900000102":
                price, fprice = 1.99, "$1.99"
            version, vdate = "2.3", (last - timedelta(days=80)).isoformat()
            if aid == "900000101":
                version, vdate = ("3.0", (last - timedelta(days=5)).isoformat()) if age <= 5 else ("2.9", (last - timedelta(days=40)).isoformat())
            cnt = None if ratings is None else ratings + int((len(days) - age) * rate * 3.2)
            snap["apps"][aid] = {"us": {"id": aid, "name": nm, "seller": seller, "kind": "mac-software" if plat == "mac" else "software",
                                        "genre_id": "6026" if plat == "mac" else "6007", "genre": "Developer Tools" if plat == "mac" else "Productivity",
                                        "ratings": cnt, "avg": avg, "version": version, "version_date": vdate + "T07:00:00Z",
                                        "price": price, "formatted_price": fprice, "currency": "USD", "url": "https://apps.apple.com/",
                                        "listed": True}}
            snap["reviews"][aid] = {"us": {"fetched": len(reviews[aid]), "pages": 1, "oldest": None, "complete": True}}
            iap = list(DEMO_IAP[aid])
            if aid == "900000101" and age <= 2:
                iap = [("Pro Monthly", 5.99) if n == "Pro Monthly" else (n, v) for n, v in iap] + [("Lifetime Pro", 49.99)]
            snap["pages"][aid] = {"us": {"upfront_price": price, "currency": "USD", "parsed_from": "demo", "iap_capped": False,
                                         "iap_count": len(iap), "iap": [{"name": n, "price_text": f"${v:.2f}", "price": v, "currency": "USD"} for n, v in iap]}}
        rival_rank = 40 - int(18 * max(0, 7 - age) / 7) if age < 7 else 40
        snap["charts"]["900000001"] = {"us": {"genre_id": "6007", "genre": "Productivity", "available": True,
                                              "free": {"entries": 100, "ranks": {"900000101": rival_rank, "900000103": 88}},
                                              "paid": {"entries": 100, "ranks": {"900000001": 61 - (i // 10), "900000102": 14}}}}
        snap["charts"]["900000003"] = {"us": {"genre_id": "6026", "genre": "Developer Tools", "available": False,
                                              "reason": "Apple publishes no Mac genre top charts in the RSS feed"}}
        snap["search"]["900000001"] = {"us": {
            "notes": {"entries": 50, "positions": {"900000001": 14, "900000101": 2, "900000102": 6, "900000103": None}},
            "markdown notes": {"entries": 50, "positions": {"900000001": 6 if age else 3, "900000101": 4, "900000102": 1, "900000103": 12}}}}
        snap["search"]["900000003"] = {"us": {
            "developer tools": {"entries": 50, "positions": {"900000003": 9, "900000301": 3, "900000302": 21}}}}
        write_json(cdir / "snapshots" / f"{d.isoformat()}.json", snap)
    write_json(cdir / "state.json", {"last_fetch": {"date": last.isoformat(), "demo": True, "partial": False, "errors": 0}})
    emit({"data_dir": str(home), "groups": len(groups), "snapshots": len(days), "reviews": n_rev,
          "note": "synthetic demo competitors; never mix with a real data dir", "next": "competitors.py --data-dir DIR analyze"})
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="competitors.py", description="Track App Store competitors with public data.")
    ap.add_argument("--data-dir", help="data dir (default: $APPSTORE_TRACKER_HOME or ~/.appstore-tracker)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("discover", help="propose competitors for one of your apps (read-only)")
    p.add_argument("--app", required=True)
    p.add_argument("--term", action="append", help="search term (repeatable; default: the descriptive part of the app name)")
    p.add_argument("--country", default="us")
    p.add_argument("--limit", type=int, default=10)
    p = sub.add_parser("add", help="add competitors (and search terms) to an app's group")
    p.add_argument("--app", required=True)
    p.add_argument("ids", nargs="+")
    p.add_argument("--term", action="append")
    p = sub.add_parser("remove", help="remove competitors or terms from a group")
    p.add_argument("--app", required=True)
    p.add_argument("ids", nargs="*")
    p.add_argument("--term", action="append")
    p = sub.add_parser("config", help="show or set countries and review pages")
    p.add_argument("--countries")
    p.add_argument("--review-pages", type=int)
    sub.add_parser("status", help="groups, snapshots, last fetch, ready")
    sub.add_parser("fetch", help="snapshot all groups from the public endpoints")
    sub.add_parser("analyze", help="write data/competitors.json")
    p = sub.add_parser("demo", help="add synthetic competitor data to a tracker demo dir")
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--seed", type=int, default=11)
    args = ap.parse_args(argv)
    if args.cmd == "discover" and not 1 <= args.limit <= 50:
        ap.error("--limit must be 1-50")
    if args.cmd == "demo" and not 8 <= args.days <= 120:
        ap.error("--days must be 8-120")
    fn = {"discover": cmd_discover, "add": cmd_add, "remove": cmd_remove, "config": cmd_config, "status": cmd_status,
          "fetch": cmd_fetch, "analyze": cmd_analyze, "demo": cmd_demo}[args.cmd]
    try:
        return fn(args)
    except CompError as err:
        log(f"Error: {err.what}\nFix: {err.fix}")
        return err.code
    except KeyboardInterrupt:
        log("Interrupted.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
