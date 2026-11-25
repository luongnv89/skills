"""Stdlib fixtures for the seo-ai-optimizer audit script.

Run directly from the repository root::

    python3 -m unittest discover -s meta/seo-ai-optimizer/tests -p 'test_*.py'

Every fixture is written to a per-test temporary directory. The audit matches
robots.txt itself (RFC 9309 groups, longest match, Allow wins a tie), so every
fixture must give the same verdict on Python 3.9 and on 3.13+.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[3] / "extras" / "seo-ai-optimizer"
SCRIPT = SKILL_DIR / "scripts" / "audit_seo.py"
sys.path.insert(0, str(SCRIPT.parent))

import audit_seo  # noqa: E402


CRAWLERS = ["GPTBot", "ClaudeBot", "OAI-SearchBot", "Claude-SearchBot", "PerplexityBot", "Googlebot"]

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Example product home page</title>
<meta name="viewport" content="width=device-width">
<meta name="description" content="A plain example page used to check what the SEO audit reports.">{robots}</head>
<body><h1>Example</h1><p>Plain page.</p></body></html>
"""

SHELL_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>App</title>
<script type="module" crossorigin src="/assets/index-abc123.js"></script></head>
<body><noscript>You need to enable JavaScript to run this app.</noscript>
<div id="root"></div></body></html>
"""

CONTENT_WORDS = " ".join(["word"] * 120)
CONTENT_PAGE = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Product</title>
<script src="/assets/app.js" defer></script></head>
<body><div id="root"><h1>Product</h1><p>{CONTENT_WORDS}</p>
<a href="/pricing">Pricing</a><a href="https://example.com/docs">Docs</a>
<a href="https://other.example.org/">Elsewhere</a><a href="#top">Top</a></div></body></html>
"""

MANIFEST = {"url": "https://example.com/", "final_url": "https://example.com/", "target_type": "live-url"}


class AuditFixture(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        (self.root / "index.html").write_text(PAGE.format(robots=""), encoding="utf-8")

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def audit(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            report = audit_seo.audit_project(self.root)
        self.stderr = err.getvalue()
        self.assertEqual(json.loads(out.getvalue()), report)
        return report

    @staticmethod
    def robots_blocks(report):
        return {
            check["crawler"]: check
            for check in report["project_checks"]
            if check.get("crawler") and check["severity"] in ("warning", "critical")
        }

    @staticmethod
    def messages(report, category):
        return [check["message"] for check in report["project_checks"] if check["category"] == category]


class RobotsTests(AuditFixture):
    def test_named_gptbot_block_reports_only_gptbot_and_asks_intent(self):
        self.write("robots.txt", "User-agent: GPTBot\nDisallow: /\n")
        blocks = self.robots_blocks(self.audit())
        self.assertEqual(list(blocks), ["GPTBot"])
        self.assertEqual(blocks["GPTBot"]["severity"], "warning")
        self.assertEqual(blocks["GPTBot"]["source_group"], "User-agent: GPTBot")
        self.assertIn("intentional", blocks["GPTBot"]["message"])

    def test_wildcard_block_reports_all_six_and_googlebot_is_critical(self):
        self.write("robots.txt", "User-agent: *\nDisallow: /\n")
        report = self.audit()
        blocks = self.robots_blocks(report)
        self.assertEqual(sorted(blocks), sorted(CRAWLERS))
        for crawler, check in blocks.items():
            self.assertEqual(check["source_group"], "User-agent: *")
            self.assertIn("intentional", check["message"])
            self.assertEqual(check["severity"], "critical" if crawler == "Googlebot" else "warning")
        # The page itself has no critical issue, so the only critical is the Googlebot block.
        file_criticals = [i for fr in report["file_reports"] for i in fr["issues"] if i["severity"] == "critical"]
        self.assertEqual(file_criticals, [])
        self.assertEqual(report["summary"]["critical"], 1)

    def test_googlebot_group_with_empty_disallow_overrides_wildcard(self):
        self.write("robots.txt", "User-agent: *\nDisallow: /\n\nUser-agent: Googlebot\nDisallow:\n")
        blocks = self.robots_blocks(self.audit())
        self.assertNotIn("Googlebot", blocks)
        self.assertIn("GPTBot", blocks)

    def test_claudebot_block_does_not_block_claude_searchbot(self):
        self.write("robots.txt", "User-agent: ClaudeBot\nDisallow: /\n")
        blocks = self.robots_blocks(self.audit())
        self.assertEqual(list(blocks), ["ClaudeBot"])

    def test_empty_disallow_reports_no_block(self):
        self.write("robots.txt", "User-agent: *\nDisallow:\n")
        report = self.audit()
        self.assertEqual(self.robots_blocks(report), {})
        self.assertTrue(any("allows GPTBot" in m for m in self.messages(report, "ai-bot")))

    def test_byte_order_mark_does_not_hide_a_wildcard_block(self):
        (self.root / "robots.txt").write_bytes("﻿User-agent: *\nDisallow: /\n".encode("utf-8"))
        self.assertIn("Googlebot", self.robots_blocks(self.audit()))

    def test_key_path_block_is_info_and_names_the_path(self):
        self.write("robots.txt", "User-agent: PerplexityBot\nDisallow: /docs/\n")
        report = self.audit()
        self.assertEqual(self.robots_blocks(report), {})
        info = [c for c in report["project_checks"] if c.get("crawler") == "PerplexityBot"]
        self.assertEqual(len(info), 1)
        self.assertEqual(info[0]["severity"], "info")
        self.assertIn("/docs/", info[0]["message"])

    def test_missing_robots_keeps_existing_warning(self):
        report = self.audit()
        self.assertIn("No robots.txt found", self.messages(report, "ai-bot"))
        self.assertEqual(self.robots_blocks(report), {})

    def test_unreadable_robots_is_an_error_finding_not_a_crash(self):
        (self.root / "robots.txt").mkdir()
        report = self.audit()
        errors = [c for c in report["project_checks"] if c["severity"] == "error" and c["category"] == "ai-bot"]
        self.assertEqual(len(errors), 1)
        self.assertIn("Cannot read robots.txt", errors[0]["message"])
        self.assertIn("cannot read robots.txt", self.stderr)

    def test_disallow_star_blocks_the_whole_site(self):
        self.write("robots.txt", "User-agent: *\nDisallow: /*\n")
        blocks = self.robots_blocks(self.audit())
        self.assertEqual(sorted(blocks), sorted(CRAWLERS))
        self.assertEqual(blocks["Googlebot"]["severity"], "critical")
        self.assertIn("from the whole site", blocks["Googlebot"]["message"])

    def test_blank_line_inside_a_group_keeps_the_rule_in_the_group(self):
        self.write("robots.txt", "User-agent: GPTBot\n\nDisallow: /\n")
        blocks = self.robots_blocks(self.audit())
        self.assertEqual(list(blocks), ["GPTBot"])
        self.assertEqual(blocks["GPTBot"]["source_group"], "User-agent: GPTBot")

    def test_trailing_rule_less_named_group_allows_that_crawler(self):
        # RFC 9309 and Google: a matching group with no rules allows everything; `*` does not apply.
        self.write("robots.txt", "User-agent: *\nDisallow: /\n\nUser-agent: GPTBot\n")
        blocks = self.robots_blocks(self.audit())
        self.assertEqual(sorted(blocks), sorted(c for c in CRAWLERS if c != "GPTBot"))
        for check in blocks.values():
            self.assertEqual(check["source_group"], "User-agent: *")

    def test_homepage_only_allow_counts_as_a_site_block(self):
        self.write("robots.txt", "User-agent: *\nDisallow: /\nAllow: /$\n")
        blocks = self.robots_blocks(self.audit())
        self.assertEqual(sorted(blocks), sorted(CRAWLERS))
        self.assertEqual(blocks["Googlebot"]["severity"], "critical")
        self.assertIn("every page except the homepage", blocks["Googlebot"]["message"])
        self.assertIn("intentional", blocks["Googlebot"]["message"])

    def test_homepage_only_disallow_is_a_homepage_block(self):
        self.write("robots.txt", "User-agent: *\nDisallow: /$\n")
        blocks = self.robots_blocks(self.audit())
        self.assertEqual(sorted(blocks), sorted(CRAWLERS))
        self.assertEqual(blocks["Googlebot"]["severity"], "critical")
        self.assertIn("from the homepage", blocks["Googlebot"]["message"])

    def test_about_only_disallow_stays_a_key_path_info(self):
        self.write("robots.txt", "User-agent: *\nDisallow: /about/\n")
        report = self.audit()
        self.assertEqual(self.robots_blocks(report), {})
        googlebot = [c for c in report["project_checks"] if c.get("crawler") == "Googlebot"]
        self.assertEqual([c["severity"] for c in googlebot], ["info"])
        self.assertIn("/about/", googlebot[0]["message"])

    def test_long_star_run_is_fast_and_keeps_the_verdict(self):
        self.write("robots.txt", "User-agent: *\nDisallow: /" + "*" * 30 + "X\nDisallow: /*" + "*" * 30 + "\n")
        start = time.monotonic()
        blocks = self.robots_blocks(self.audit())
        self.assertLess(time.monotonic() - start, 2)
        self.assertEqual(sorted(blocks), sorted(CRAWLERS))
        self.assertIn("from the whole site", blocks["Googlebot"]["message"])

    def test_rules_past_500_kib_are_ignored_and_reported(self):
        self.write("robots.txt", "User-agent: *\n" + "# padding\n" * 60000 + "Disallow: /\n")
        report = self.audit()
        self.assertEqual(self.robots_blocks(report), {})
        self.assertTrue(any("over 500 KiB" in m for m in self.messages(report, "ai-bot")))
        self.assertIn("500 KiB", self.stderr)

    def test_allow_wins_a_tie_with_disallow(self):
        self.write("robots.txt", "User-agent: *\nDisallow: /\nAllow: /\n\nUser-agent: PerplexityBot\nDisallow: /docs/\nAllow: /docs/\n")
        report = self.audit()
        self.assertEqual(self.robots_blocks(report), {})
        self.assertTrue(any("allows GPTBot" in m for m in self.messages(report, "ai-bot")))

    def test_longer_allow_opens_a_key_path_inside_a_disallowed_prefix(self):
        self.write("robots.txt", "User-agent: PerplexityBot\nDisallow: /d\nAllow: /docs/\n")
        report = self.audit()
        self.assertEqual(self.robots_blocks(report), {})
        self.assertEqual([c for c in report["project_checks"] if c.get("crawler")], [])

    def test_live_evidence_dir_reports_robots_block(self):
        self.write("manifest.json", json.dumps(MANIFEST))
        self.write("page.html", CONTENT_PAGE)
        self.write("robots.txt", "User-agent: GPTBot\nDisallow: /\n")
        self.assertEqual(list(self.robots_blocks(self.audit())), ["GPTBot"])


class NoindexTests(AuditFixture):
    def noindex_issues(self, robots_value):
        meta = f'<meta name="robots" content="{robots_value}">'
        self.write("index.html", PAGE.format(robots=meta))
        report = self.audit()
        return [
            issue
            for file_report in report["file_reports"]
            for issue in file_report["issues"]
            if "Meta robots" in issue["message"]
        ]

    def test_noindex_nofollow_is_flagged(self):
        issues = self.noindex_issues("noindex, nofollow")
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["severity"], "warning")
        self.assertEqual(issues[0]["category"], "technical-seo")
        self.assertIn("'noindex, nofollow'", issues[0]["message"])
        self.assertIn("intentional", issues[0]["message"])

    def test_none_is_flagged_case_insensitively(self):
        self.assertEqual(len(self.noindex_issues("NONE")), 1)

    def test_index_follow_is_not_flagged(self):
        self.assertEqual(self.noindex_issues("index, follow"), [])


class RawHtmlTests(AuditFixture):
    def live_evidence(self, page):
        self.write("manifest.json", json.dumps(MANIFEST))
        self.write("page.html", page)
        return self.audit()

    def shell_warnings(self, report):
        return [c for c in report["project_checks"] if "app shell" in c["message"]]

    def test_shell_page_warns_once_with_raw_html_stats(self):
        report = self.live_evidence(SHELL_PAGE)
        warnings = self.shell_warnings(report)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["severity"], "warning")
        self.assertIn("crawlers that do not run JavaScript", warnings[0]["message"])
        self.assertEqual(report["raw_html"], {"raw_text_words": 0, "h1_count": 0, "internal_links": 0})
        per_file = [i for fr in report["file_reports"] for i in fr["issues"] if "app shell" in i["message"]]
        self.assertEqual(per_file, [])

    def test_content_rich_page_has_no_shell_warning(self):
        report = self.live_evidence(CONTENT_PAGE)
        self.assertEqual(self.shell_warnings(report), [])
        self.assertEqual(report["raw_html"]["h1_count"], 1)
        self.assertEqual(report["raw_html"]["internal_links"], 2)
        self.assertGreaterEqual(report["raw_html"]["raw_text_words"], 120)

    def test_unreadable_manifest_is_reported_and_counts_relative_links_only(self):
        self.write("manifest.json", "{not json")
        self.write("page.html", CONTENT_PAGE)
        report = self.audit()
        errors = [c for c in report["project_checks"] if c["severity"] == "error" and c["category"] == "raw-html"]
        self.assertEqual(len(errors), 1)
        self.assertIn("cannot read the page URL", self.stderr)
        self.assertEqual(report["raw_html"]["internal_links"], 1)

    @staticmethod
    def shell_page(words, mount=True, bundle=True):
        script = '<script type="module" src="/assets/index.js"></script>' if bundle else "<script>window.x = 1;</script>"
        body = " ".join(["word"] * words)
        div = f'<div id="root"><p>{body}</p></div>' if mount else f"<main><p>{body}</p></main>"
        return f'<!doctype html><html lang="en"><head><title>App</title>{script}</head><body>{div}</body></html>'

    def test_shell_boundary_warns_at_49_words_not_at_50(self):
        self.assertEqual(len(self.shell_warnings(self.live_evidence(self.shell_page(49)))), 1)
        self.assertEqual(self.shell_warnings(self.live_evidence(self.shell_page(50))), [])

    def test_mount_element_without_script_src_gets_no_shell_warning(self):
        self.assertEqual(self.shell_warnings(self.live_evidence(self.shell_page(0, bundle=False))), [])

    def test_script_bundle_without_mount_element_gets_no_shell_warning(self):
        self.assertEqual(self.shell_warnings(self.live_evidence(self.shell_page(0, mount=False))), [])

    def test_page_html_without_manifest_gets_no_shell_check(self):
        self.write("page.html", SHELL_PAGE)
        report = self.audit()
        self.assertEqual(self.shell_warnings(report), [])
        self.assertNotIn("raw_html", report)

    def spa_info(self, files):
        for name, text in files.items():
            self.write(name, text)
        return [m for m in self.messages(self.audit(), "raw-html") if "Client-only SPA" in m]

    def test_vite_react_without_ssr_gets_spa_info(self):
        deps = {"dependencies": {"react": "18.3.1", "react-dom": "18.3.1"}, "devDependencies": {"vite": "5.4.0"}}
        self.assertEqual(len(self.spa_info({"vite.config.ts": "", "package.json": json.dumps(deps)})), 1)

    def test_nextjs_project_gets_no_spa_info(self):
        deps = {"dependencies": {"next": "14.2.0", "react": "18.3.1"}}
        self.assertEqual(self.spa_info({"next.config.js": "", "package.json": json.dumps(deps)}), [])

    def test_nextjs_with_vite_config_for_tests_gets_no_spa_info(self):
        deps = {"dependencies": {"next": "14.2.0", "react": "18.3.1"}, "devDependencies": {"vitest": "2.0.0"}}
        self.assertEqual(self.spa_info({"vite.config.ts": "", "package.json": json.dumps(deps)}), [])


class LlmsTxtTests(AuditFixture):
    def test_missing_llms_txt_is_optional_info_only(self):
        without = self.audit()
        message = "No llms.txt found (optional; used by some AI tools, not by Google Search)."
        llms = [c for c in without["project_checks"] if c["message"] == message]
        self.assertEqual(len(llms), 1)
        self.assertEqual(llms[0]["severity"], "info")

        self.write("llms.txt", "# Example\n")
        with_llms = self.audit()
        self.assertEqual(with_llms["summary"]["critical"], without["summary"]["critical"])
        self.assertEqual(with_llms["summary"]["warning"], without["summary"]["warning"])
        self.assertEqual(with_llms["summary"]["info"], without["summary"]["info"] - 1)


if __name__ == "__main__":
    unittest.main()
