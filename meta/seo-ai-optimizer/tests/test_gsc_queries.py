"""Stdlib fixtures for the seo-ai-optimizer Search Console export reader.

Run directly from the repository root::

    python3 -m unittest discover -s meta/seo-ai-optimizer/tests -p 'test_*.py'

Fixtures are written to a per-test temporary directory. The script reads CSV
only, so no test touches the network.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[3] / "extras" / "seo-ai-optimizer"
SCRIPT = SKILL_DIR / "scripts" / "gsc_queries.py"
sys.path.insert(0, str(SCRIPT.parent))

import gsc_queries  # noqa: E402


QUERIES = (
    "﻿Top queries,Clicks,Impressions,CTR,Position\n"
    "acme,120,400,30%,1.2\n"
    "how do i export invoices from acme to a spreadsheet,2,900,0.22%,9.4\n"
    "invoice tool,5,1000,0.5%,12\n"
    "what is an invoice,40,300,13.33%,3\n"
    "cheap invoices,1,50,2%,22\n"
)

PAGES = (
    "Top pages,Clicks,Impressions,CTR,Position\n"
    "https://example.com/,300,5000,6%,4.1\n"
    "https://example.com/docs/export,20,2000,1%,8\n"
    "https://example.com/blog/old,1,800,0.13%,15.0\n"
    "https://example.com/pricing,3,700,0.43%,16\n"
)

QUERY_PAGE = (
    "query,page,clicks,impressions,ctr,position\n"
    "invoice tool,https://example.com/,5,1000,0.005,12\n"
    "what is an invoice,https://example.com/guide,40,300,0.1333,3\n"
    "acme login,https://example.com/login,90,100,0.9,1\n"
    "invoice template free,https://example.com/templates,1,600,0.0017,8.5\n"
)

QUERY_DATE = (
    "query,date,clicks,impressions,ctr,position\n"
    "acme,2026-11-01,10,100,0.1,1\n"
    "acme app,2026-11-01,2,20,0.1,2\n"
    "acme,2026-11-08,30,400,0.075,1\n"
    "invoice tool,2026-11-08,1,500,0.002,12\n"
)


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def put(self, name, text):
        path = self.dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return str(path)

    def run_script(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = gsc_queries.main(list(argv))
        return code, json.loads(out.getvalue())


class NoData(Base):
    def test_no_input_reports_every_check_not_covered_with_export_hint(self):
        code, report = self.run_script()
        self.assertEqual(code, 0)
        self.assertFalse(report["covered"])
        self.assertEqual(report["network"], "none")
        for key in ("long_questions", "high_impression_low_click", "positions_8_to_15",
                    "branded_impressions", "generative_ai_report"):
            self.assertEqual(report[key]["status"], "not covered", key)
            self.assertTrue(report[key]["export"], key)

    def test_unrecognised_headers_are_named_not_read_as_zero_findings(self):
        path = self.put("Filters.csv", "Filter,Value\nSearch type,Web\n")
        code, report = self.run_script(path)
        self.assertEqual(code, 0)
        self.assertFalse(report["covered"])
        self.assertEqual(report["unrecognised"][0]["headers"], ["filter", "value"])
        self.assertEqual(report["long_questions"]["status"], "not covered")

    def test_missing_file_exits_2(self):
        code, report = self.run_script(str(self.dir / "nope.csv"))
        self.assertEqual(code, 2)
        self.assertIn("error", report)


class UiExport(Base):
    def setUp(self):
        super().setUp()
        self.put("export/Queries.csv", QUERIES)
        self.put("export/Pages.csv", PAGES)
        self.put("export/Filters.csv", "Filter,Value\nSearch type,Web\n")
        _, self.report = self.run_script(str(self.dir / "export"))

    def test_folder_files_are_classified(self):
        kinds = sorted(i["kind"] for i in self.report["inputs"])
        self.assertEqual(kinds, ["pages", "queries"])
        self.assertEqual(len(self.report["unrecognised"]), 1)

    def test_long_and_question_queries(self):
        items = {i["query"]: i["matched"] for i in self.report["long_questions"]["items"]}
        self.assertEqual(items["how do i export invoices from acme to a spreadsheet"],
                         ["8+ words", "how/what/why"])
        self.assertEqual(items["what is an invoice"], ["how/what/why"])
        self.assertNotIn("invoice tool", items)

    def test_seven_words_is_not_long(self):
        self.assertIsNone(gsc_queries.LONG_QUERY.match("one two three four five six seven"))
        self.assertTrue(gsc_queries.LONG_QUERY.match("one two three four five six seven eight"))

    def test_low_ctr_uses_thresholds_derived_from_the_export(self):
        section = self.report["high_impression_low_click"]
        self.assertEqual(section["thresholds"]["min_impressions"], 900)
        self.assertAlmostEqual(section["thresholds"]["max_ctr"], 0.02)
        self.assertIn("min_impressions", section["thresholds"]["derived"])
        queries = [i["query"] for i in section["items"]]
        self.assertEqual(queries, ["invoice tool", "how do i export invoices from acme to a spreadsheet"])

    def test_queries_without_page_are_never_mapped_to_a_guessed_page(self):
        for item in self.report["high_impression_low_click"]["items"]:
            self.assertIsNone(item["page"])
            self.assertIn("no page column", item["recommendation"])
        self.assertTrue(self.report["high_impression_low_click"]["page_mapping"].startswith("not covered"))

    def test_positions_8_to_15_inclusive(self):
        pages = [p["page"] for p in self.report["positions_8_to_15"]["pages"]]
        self.assertEqual(pages, ["https://example.com/docs/export", "https://example.com/blog/old"])
        for item in self.report["positions_8_to_15"]["pages"]:
            self.assertIn("rather than creating a new one", item["recommendation"])

    def test_percent_ctr_is_a_fraction(self):
        rows = gsc_queries.load_rows(self.dir / "export" / "Queries.csv")[1]
        self.assertAlmostEqual(rows[0]["ctr"], 0.30)

    def test_no_recommendation_suggests_a_new_page(self):
        text = json.dumps(self.report).lower()
        self.assertNotIn("create a page", text)
        self.assertNotIn("new page for", text)


class ZeroClicks(Base):
    def test_high_impression_zero_click_query_is_listed_when_most_rows_have_no_clicks(self):
        path = self.put("Queries.csv", (
            "Top queries,Clicks,Impressions,CTR,Position\n"
            "invoice software for freelancers,0,5000,0%,11\n"
            "acme,30,100,30%,1\n"
            "a,0,10,0%,40\n"
            "b,0,20,0%,35\n"
            "c,0,30,0%,30\n"))
        _, report = self.run_script(path)
        section = report["high_impression_low_click"]
        self.assertAlmostEqual(section["thresholds"]["max_ctr"], 0.30)
        self.assertEqual([i["query"] for i in section["items"]], ["invoice software for freelancers"])

    def test_all_zero_click_export_still_lists_high_impression_queries(self):
        path = self.put("Queries.csv", (
            "Top queries,Clicks,Impressions,CTR,Position\n"
            "big,0,900,0%,9\nsmall,0,10,0%,30\nmid,0,50,0%,20\n"))
        _, report = self.run_script(path)
        # 75th percentile of [10, 50, 900] is 50, so "small" stays out.
        self.assertEqual([i["query"] for i in report["high_impression_low_click"]["items"]], ["big", "mid"])


class QueryPageRows(Base):
    def test_low_ctr_query_maps_to_the_page_that_ranks(self):
        path = self.put("api.csv", QUERY_PAGE)
        _, report = self.run_script(path, "--min-impressions", "500", "--max-ctr", "0.01")
        items = report["high_impression_low_click"]["items"]
        self.assertEqual([(i["query"], i["page"]) for i in items],
                         [("invoice tool", "https://example.com/"),
                          ("invoice template free", "https://example.com/templates")])
        self.assertIn("https://example.com/", items[0]["recommendation"])
        self.assertEqual(report["high_impression_low_click"]["thresholds"]["derived"], {})
        self.assertNotIn("page_mapping", report["high_impression_low_click"])

    def test_question_answer_goes_on_the_ranking_page(self):
        path = self.put("api.csv", QUERY_PAGE)
        _, report = self.run_script(path)
        item = report["long_questions"]["items"][0]
        self.assertEqual(item["page"], "https://example.com/guide")
        self.assertIn("first lines of https://example.com/guide", item["recommendation"])


class Branded(Base):
    def test_brand_regex_builds_a_series_by_date(self):
        path = self.put("dates.csv", QUERY_DATE)
        _, report = self.run_script(path, "--brand", "^acme")
        series = report["branded_impressions"]["series"]
        self.assertEqual([(p["date"], p["impressions"]) for p in series],
                         [("2026-11-01", 120.0), ("2026-11-08", 400.0)])
        self.assertEqual(report["branded_impressions"]["status"], "covered")

    def test_branded_dates_export(self):
        path = self.put("Dates.csv", "Date,Clicks,Impressions,CTR,Position\n2026-11-02,5,50,10%,1.1\n2026-11-01,1,10,10%,1.4\n")
        _, report = self.run_script("--branded-dates", path)
        self.assertEqual([p["date"] for p in report["branded_impressions"]["series"]],
                         ["2026-11-01", "2026-11-02"])

    def test_brand_without_dates_is_not_covered(self):
        path = self.put("Queries.csv", QUERIES)
        _, report = self.run_script(path, "--brand", "acme")
        self.assertEqual(report["branded_impressions"]["status"], "not covered")
        self.assertIn("no date", report["branded_impressions"]["note"])

    def test_bad_brand_regex_exits_2(self):
        code, report = self.run_script("--brand", "(")
        self.assertEqual(code, 2)


class GenerativeAiReport(Base):
    def test_columns_are_passed_through_as_labelled(self):
        path = self.put("genai.csv", "﻿Page,Some metric,Another metric\nhttps://example.com/,12,3\n")
        _, report = self.run_script("--ai-report", path)
        section = report["generative_ai_report"]
        self.assertEqual(section["status"], "covered")
        self.assertEqual(section["columns"], ["Page", "Some metric", "Another metric"])
        self.assertEqual(section["rows"], [["https://example.com/", "12", "3"]])
        self.assertTrue(report["covered"])


class Numbers(unittest.TestCase):
    def test_parse_number(self):
        cases = {"1234": 1234.0, "1,234": 1234.0, "1.5": 1.5, "1,5": 1.5, "3.2%": 0.032,
                 "3,2 %": 0.032, "": None, "n/a": None}
        for text, expected in cases.items():
            value = gsc_queries.parse_number(text)
            if expected is None:
                self.assertIsNone(value, text)
            else:
                self.assertAlmostEqual(value, expected, msg=text)


if __name__ == "__main__":
    unittest.main()
