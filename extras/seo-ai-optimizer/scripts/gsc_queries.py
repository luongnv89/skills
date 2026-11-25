#!/usr/bin/env python3
"""Summarise a Google Search Console Performance export the user supplied.

Reads CSV files only (a Performance export folder, its CSV files, or rows the
user pulled through the Search Console API and saved as CSV). It never contacts
Google, Search Console, an AI assistant or any other network service.

Usage:
    python scripts/gsc_queries.py <export-dir-or-csv> [...]
        [--brand REGEX] [--branded-dates CSV] [--ai-report CSV]
        [--min-impressions N] [--max-ctr F] [--limit N]

Prints one JSON object. Each analysis has a "status" of "covered" or
"not covered"; a "not covered" analysis names what to export. Exit 0 on any
readable input (including none), 2 on a missing or unreadable file.

Practitioner ideas (8+ word queries, how/what/why questions, positions 8-15)
are described in the skill's references/search-performance.md.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

LONG_QUERY = re.compile(r"^(?:\S+\s+){7,}\S+$")  # 8+ words (practitioner)
QUESTION = re.compile(r"\b(?:how|what|why)\b", re.IGNORECASE)  # (practitioner)
STRIKING_MIN, STRIKING_MAX = 8.0, 15.0  # average positions 8-15 (practitioner)
MAX_AI_ROWS = 200

ALIASES = {
    "query": {"top queries", "query", "queries", "search query"},
    "page": {"top pages", "page", "pages", "url", "landing page", "address"},
    "date": {"date", "day"},
    "clicks": {"clicks", "url clicks"},
    "impressions": {"impressions"},
    "ctr": {"ctr", "url ctr", "click-through rate"},
    "position": {"position", "average position", "avg. position", "avg position"},
}

EXPORT_HINT = {
    "queries": "Search Console > Performance > Search results > Export > Download CSV, "
               "then pass the unzipped folder (its queries CSV)",
    "query_page": "rows carrying both query and page: Search Console API searchanalytics.query "
                  "with dimensions [query, page], run with the user's own access and saved as CSV, "
                  "or one export per page (filter Page, then export the Queries tab)",
    "pages": "the same Performance export (its pages CSV)",
    "branded": "Performance filtered by a Query regex matching the brand name, exported with the "
               "Dates tab and passed as --branded-dates, or API rows with dimensions [query, date] "
               "plus --brand",
    "ai_report": "the Search Console Generative AI performance report, exported as CSV and passed "
                 "as --ai-report",
}


def _norm(header: str) -> str:
    return header.replace("﻿", "").strip().strip('"').lower()


def map_headers(headers):
    """Return {canonical: column index} for the headers this script knows."""
    found = {}
    for idx, raw in enumerate(headers):
        name = _norm(raw)
        for key, names in ALIASES.items():
            if name in names and key not in found:
                found[key] = idx
    return found


def parse_number(text):
    """Parse 1234, 1,234, 1.5, 1,5, 3.2% or 3,2 %; return None when unparseable."""
    if text is None:
        return None
    value = str(text).strip().replace(" ", "").replace(" ", "")
    percent = value.endswith("%")
    value = value.rstrip("%")
    if not value:
        return None
    if "," in value and "." in value:
        value = value.replace(",", "")
    elif "," in value:
        head, _, tail = value.rpartition(",")
        value = head.replace(",", "") + ("." if len(tail) != 3 or percent else "") + tail
    try:
        number = float(value)
    except ValueError:
        return None
    return number / 100.0 if percent else number


def read_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        return [], []
    return rows[0], rows[1:]


def classify(cols):
    if "query" in cols:
        return "queries"
    if "page" in cols:
        return "pages"
    if "date" in cols:
        return "dates"
    return None


def load_rows(path: Path, kind_hint=None):
    """Return (kind, rows, skipped, headers) where rows are dicts of canonical keys."""
    headers, body = read_csv(path)
    cols = map_headers(headers)
    kind = classify(cols)
    if kind is None or "impressions" not in cols:
        return None, [], 0, headers
    kind = kind_hint or kind
    rows, skipped = [], 0
    for raw in body:
        if not any(cell.strip() for cell in raw):
            continue
        row = {}
        for key in ("query", "page", "date"):
            if key in cols:
                row[key] = raw[cols[key]].strip() if cols[key] < len(raw) else ""
        for key in ("clicks", "impressions", "ctr", "position"):
            if key in cols:
                row[key] = parse_number(raw[cols[key]]) if cols[key] < len(raw) else None
        if row.get("impressions") is None:
            skipped += 1
            continue
        if row.get("ctr") is None and row.get("clicks") is not None and row["impressions"]:
            row["ctr"] = row["clicks"] / row["impressions"]
        rows.append(row)
    return kind, rows, skipped, headers


def expand(paths):
    files = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            files.extend(sorted(x for x in path.iterdir() if x.suffix.lower() == ".csv"))
        elif path.is_file():
            files.append(path)
        else:
            raise FileNotFoundError(str(path))
    return files


def percentile(values, frac):
    ordered = sorted(values)
    if not ordered:
        return None
    return ordered[int(frac * (len(ordered) - 1))]


def _num(row):
    return {k: row.get(k) for k in ("clicks", "impressions", "ctr", "position") if k in row}


def no_page_hint():
    return ("this export has no page column: find the page that already ranks for this query "
            "(" + EXPORT_HINT["query_page"] + ") before writing anything")


def long_questions(query_rows, limit):
    out = []
    for row in query_rows:
        q = row.get("query", "")
        matched = []
        if LONG_QUERY.match(q):
            matched.append("8+ words")
        if QUESTION.search(q):
            matched.append("how/what/why")
        if not matched:
            continue
        page = row.get("page") or None
        rec = ("Answer this question in plain words in the first lines of %s, the page that "
               "already ranks for it; merge other wordings of it into the same answer" % page
               if page else "Answer it on the page that already ranks; " + no_page_hint())
        item = {"query": q, "page": page, "matched": matched, "recommendation": rec}
        item.update(_num(row))
        out.append(item)
    out.sort(key=lambda r: -(r.get("impressions") or 0))
    return out[:limit], len(out)


def low_ctr(query_rows, min_impr, max_ctr, limit):
    impressions = [r["impressions"] for r in query_rows if r.get("impressions") is not None]
    clicked = [r["ctr"] for r in query_rows if r.get("ctr")]
    derived = {}
    if min_impr is None:
        min_impr = percentile(impressions, 0.75)
        derived["min_impressions"] = "75th percentile of query impressions in this export"
    if max_ctr is None:
        max_ctr = percentile(clicked, 0.5) or 0.0
        derived["max_ctr"] = ("median CTR of the queries with clicks in this export (rows strictly "
                              "below it; a query with no clicks always counts)")
    out = []
    if min_impr is not None and max_ctr is not None:
        for row in query_rows:
            if row.get("ctr") is None:
                continue
            if row["impressions"] >= min_impr and (row["ctr"] < max_ctr or row["ctr"] == 0):
                page = row.get("page") or None
                rec = ("%s already shows for this query but few searchers click: answer the query "
                       "in that page's title, description or first lines" % page
                       if page else "Map it to the page that already ranks; " + no_page_hint())
                item = {"query": row.get("query", ""), "page": page, "recommendation": rec}
                item.update(_num(row))
                out.append(item)
    out.sort(key=lambda r: -(r.get("impressions") or 0))
    thresholds = {"min_impressions": min_impr, "max_ctr": max_ctr, "derived": derived}
    return out[:limit], len(out), thresholds


def striking(rows, label, limit):
    out = []
    for row in rows:
        pos = row.get("position")
        if pos is None or not STRIKING_MIN <= pos <= STRIKING_MAX:
            continue
        if label == "pages":
            rec = ("%s sits at average position %.1f: improve this page first (answer the "
                   "questions it ranks for, add first-hand detail) rather than creating a new one"
                   % (row.get("page", ""), pos))
            item = {"page": row.get("page", ""), "recommendation": rec}
        else:
            page = row.get("page") or None
            rec = ("Improve %s for this query (average position %.1f); do not create a new page"
                   % (page, pos) if page else "Improve the page that already ranks; " + no_page_hint())
            item = {"query": row.get("query", ""), "page": page, "recommendation": rec}
        item.update(_num(row))
        out.append(item)
    out.sort(key=lambda r: -(r.get("impressions") or 0))
    return out[:limit], len(out)


def series(rows):
    by_date = {}
    for row in rows:
        date = row.get("date")
        if not date:
            continue
        bucket = by_date.setdefault(date, {"date": date, "impressions": 0.0, "clicks": 0.0})
        bucket["impressions"] += row.get("impressions") or 0
        bucket["clicks"] += row.get("clicks") or 0
    return [by_date[d] for d in sorted(by_date)]


BRANDED_REC = ("Compare branded impressions in the weeks before and after each launch or "
               "announcement; a rise after a launch means more people searched for the name")


def analyse(args):
    files = expand(args.inputs)
    report = {"tool": "gsc_queries.py", "network": "none", "inputs": [], "unrecognised": []}
    query_rows, page_rows = [], []
    for path in files:
        kind, rows, skipped, headers = load_rows(path)
        if kind is None:
            report["unrecognised"].append({"file": str(path), "headers": [_norm(h) for h in headers]})
            continue
        report["inputs"].append({"file": str(path), "kind": kind, "rows": len(rows), "skipped_rows": skipped})
        if kind == "queries":
            query_rows.extend(rows)
        elif kind == "pages":
            page_rows.extend(rows)

    limit = args.limit
    if query_rows:
        has_page = any(r.get("page") for r in query_rows)
        items, total = long_questions(query_rows, limit)
        report["long_questions"] = {"status": "covered", "total": total, "items": items}
        items, total, thresholds = low_ctr(query_rows, args.min_impressions, args.max_ctr, limit)
        report["high_impression_low_click"] = {"status": "covered", "total": total,
                                               "thresholds": thresholds, "items": items}
        if not has_page:
            for key in ("long_questions", "high_impression_low_click"):
                report[key]["page_mapping"] = "not covered: " + EXPORT_HINT["query_page"]
    else:
        for key in ("long_questions", "high_impression_low_click"):
            report[key] = {"status": "not covered", "export": EXPORT_HINT["queries"]}

    if page_rows or query_rows:
        pages, ptotal = striking(page_rows, "pages", limit)
        queries, qtotal = striking(query_rows, "queries", limit)
        report["positions_8_to_15"] = {"status": "covered", "pages": pages, "pages_total": ptotal,
                                       "queries": queries, "queries_total": qtotal}
        if not page_rows:
            report["positions_8_to_15"]["pages_note"] = "not covered: " + EXPORT_HINT["pages"]
    else:
        report["positions_8_to_15"] = {"status": "not covered", "export": EXPORT_HINT["pages"]}

    branded = {"status": "not covered", "export": EXPORT_HINT["branded"]}
    if args.branded_dates:
        _, rows, _, headers = load_rows(Path(args.branded_dates), kind_hint="dates")
        points = series(rows)
        if points:
            branded = {"status": "covered", "source": "branded-dates export", "series": points,
                       "recommendation": BRANDED_REC}
        else:
            branded["note"] = "no dated rows read from %s (headers: %s)" % (
                args.branded_dates, ", ".join(_norm(h) for h in headers))
    elif args.brand:
        brand = re.compile(args.brand, re.IGNORECASE)
        matched = [r for r in query_rows if brand.search(r.get("query", ""))]
        points = series(matched)
        if points:
            branded = {"status": "covered", "source": "query rows matching --brand", "series": points,
                       "recommendation": BRANDED_REC}
        elif matched:
            total = sum(r.get("impressions") or 0 for r in matched)
            branded["note"] = ("brand queries found (%d impressions in total) but the rows carry "
                               "no date" % total)
    report["branded_impressions"] = branded

    if args.ai_report:
        headers, body = read_csv(Path(args.ai_report))
        report["generative_ai_report"] = {
            "status": "covered", "file": args.ai_report,
            "columns": [h.replace("﻿", "").strip() for h in headers],
            "row_count": len(body), "rows": body[:MAX_AI_ROWS],
            "truncated": len(body) > MAX_AI_ROWS,
            "note": "metrics are reported as labelled in the export; none is renamed or derived",
        }
    else:
        report["generative_ai_report"] = {"status": "not covered", "export": EXPORT_HINT["ai_report"]}

    report["covered"] = any(
        isinstance(v, dict) and v.get("status") == "covered" for v in report.values())
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("inputs", nargs="*", help="export folder(s) or CSV file(s)")
    parser.add_argument("--brand", help="regex matching the brand name in query rows")
    parser.add_argument("--branded-dates", help="Dates CSV of an export filtered to brand queries")
    parser.add_argument("--ai-report", help="CSV export of the Generative AI performance report")
    parser.add_argument("--min-impressions", type=float, help="override the derived impressions cut-off")
    parser.add_argument("--max-ctr", type=float, help="override the derived CTR cut-off (0.02 = 2%%)")
    parser.add_argument("--limit", type=int, default=25, help="rows listed per analysis (default 25)")
    args = parser.parse_args(argv)
    try:
        if args.brand:
            re.compile(args.brand)
        report = analyse(args)
    except (OSError, UnicodeDecodeError, csv.Error, re.error) as exc:
        print(json.dumps({"error": "%s: %s" % (type(exc).__name__, exc)}))
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
