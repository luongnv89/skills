#!/usr/bin/env python3
"""
SEO & AI Bot Audit Script

Scans HTML files in a codebase for common SEO and AI bot issues.
Outputs a structured JSON report.

Usage:
    python audit_seo.py <project-root> [--max-files N]
"""

import argparse
import sys
import os
import re
import json
import urllib.parse
from pathlib import Path
from html.parser import HTMLParser


# Crawlers whose robots.txt access is reported, with what blocking each one affects.
ROBOTS_CRAWLERS = {
    "GPTBot": "OpenAI's crawler for model training",
    "ClaudeBot": "Anthropic's crawler for model training",
    "OAI-SearchBot": "OpenAI's crawler for ChatGPT search answers",
    "Claude-SearchBot": "Anthropic's crawler for Claude search results",
    "PerplexityBot": "Perplexity's crawler for its search results",
    "Googlebot": "Google's crawler for Google Search and all its features",
}
ROBOTS_KEY_PATHS = ("/blog/", "/docs/", "/about/")
# A page other than the homepage, with a prefix no real rule is likely to target.
ROBOTS_DEEP_PROBE = "/zz-seo-audit-probe/page"
# Google reads the first 500 KiB of robots.txt and ignores the rest.
ROBOTS_MAX_BYTES = 500 * 1024

# Text inside these elements is not shown to a reader of the raw HTML.
HIDDEN_TEXT_TAGS = {"script", "style", "template", "noscript"}
APP_MOUNT_IDS = {"root", "app", "__next", "__nuxt", "svelte"}
APP_SHELL_MAX_WORDS = 50

FRAMEWORK_CONFIG_FILES = {
    "next.config.js": "Next.js",
    "next.config.mjs": "Next.js",
    "next.config.ts": "Next.js",
    "nuxt.config.js": "Nuxt",
    "nuxt.config.ts": "Nuxt",
    "astro.config.mjs": "Astro",
    "astro.config.ts": "Astro",
    "svelte.config.js": "SvelteKit",
    "gatsby-config.js": "Gatsby",
    "gatsby-config.ts": "Gatsby",
    "hugo.toml": "Hugo",
    "hugo.yaml": "Hugo",
    "config.toml": "Hugo",  # common Hugo config
    "angular.json": "Angular",
    "remix.config.js": "Remix",
    "vite.config.js": "Vite",
    "vite.config.ts": "Vite",
    "webpack.config.js": "Webpack",
    "_config.yml": "Jekyll",
}
SERVER_RENDERING_DEPS = {"next", "nuxt", "astro", "@sveltejs/kit", "gatsby", "@react-router/dev", "vike", "vite-plugin-ssr"}


class SEOAuditParser(HTMLParser):
    """Parse an HTML file and extract SEO-relevant elements."""

    def __init__(self):
        super().__init__()
        self.title = None
        self.meta_description = None
        self.meta_viewport = None
        self.meta_charset = None
        self.meta_robots = None
        self.og_tags = {}
        self.twitter_tags = {}
        self.canonical = None
        self.headings = []  # list of (level, text)
        self.images = []  # list of {src, alt, width, height, loading, fetchpriority}
        self.links = []  # list of {href, text, rel}
        self.scripts = []  # list of {src, async, defer}
        self.stylesheets = []  # list of {href, media}
        self.json_ld = []
        self.lang = None
        self.has_inline_critical_css = False
        self.visible_words = 0
        self.has_app_mount = False

        self._in_title = False
        self._title_text = ""
        self._in_heading = False
        self._heading_level = 0
        self._heading_text = ""
        self._in_script = False
        self._script_type = None
        self._script_content = ""
        self._in_a = False
        self._a_href = ""
        self._a_rel = ""
        self._a_text = ""
        self._in_style = False
        self._in_head = False
        self._hidden_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == "head":
            self._in_head = True
        elif tag == "body":
            self._in_head = False
        if tag in HIDDEN_TEXT_TAGS:
            self._hidden_depth += 1
        if attrs_dict.get("id") in APP_MOUNT_IDS:
            self.has_app_mount = True

        if tag == "html":
            self.lang = attrs_dict.get("lang")

        elif tag == "title":
            self._in_title = True
            self._title_text = ""

        elif tag == "meta":
            name = attrs_dict.get("name", "").lower()
            prop = attrs_dict.get("property", "").lower()
            content = attrs_dict.get("content", "")
            charset = attrs_dict.get("charset")

            if charset:
                self.meta_charset = charset
            elif name == "description":
                self.meta_description = content
            elif name == "viewport":
                self.meta_viewport = content
            elif name == "robots":
                self.meta_robots = content
            elif prop.startswith("og:"):
                self.og_tags[prop] = content
            elif name.startswith("twitter:"):
                self.twitter_tags[name] = content

        elif tag == "link":
            rel = attrs_dict.get("rel", "")
            href = attrs_dict.get("href", "")
            if rel == "canonical":
                self.canonical = href
            elif rel == "stylesheet":
                self.stylesheets.append({
                    "href": href,
                    "media": attrs_dict.get("media", "all")
                })

        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._in_heading = True
            self._heading_level = int(tag[1])
            self._heading_text = ""

        elif tag == "img":
            self.images.append({
                "src": attrs_dict.get("src", ""),
                "alt": attrs_dict.get("alt"),
                "width": attrs_dict.get("width"),
                "height": attrs_dict.get("height"),
                "loading": attrs_dict.get("loading"),
                "fetchpriority": attrs_dict.get("fetchpriority"),
            })

        elif tag == "a":
            self._in_a = True
            self._a_href = attrs_dict.get("href", "")
            self._a_rel = attrs_dict.get("rel", "")
            self._a_text = ""

        elif tag == "script":
            self._in_script = True
            self._script_type = attrs_dict.get("type", "")
            self._script_content = ""
            src = attrs_dict.get("src")
            if src:
                self.scripts.append({
                    "src": src,
                    "async": "async" in attrs_dict,
                    "defer": "defer" in attrs_dict,
                })

        elif tag == "style":
            self._in_style = True

    def handle_endtag(self, tag):
        if tag == "head":
            self._in_head = False
        if tag in HIDDEN_TEXT_TAGS and self._hidden_depth:
            self._hidden_depth -= 1

        if tag == "title":
            self._in_title = False
            self.title = self._title_text.strip()

        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6") and self._in_heading:
            self._in_heading = False
            self.headings.append((self._heading_level, self._heading_text.strip()))

        elif tag == "a" and self._in_a:
            self._in_a = False
            self.links.append({
                "href": self._a_href,
                "text": self._a_text.strip(),
                "rel": self._a_rel,
            })

        elif tag == "script" and self._in_script:
            self._in_script = False
            if "application/ld+json" in self._script_type:
                try:
                    self.json_ld.append(json.loads(self._script_content))
                except json.JSONDecodeError:
                    self.json_ld.append({"_parse_error": True})

        elif tag == "style":
            self._in_style = False
            self.has_inline_critical_css = True

    def handle_data(self, data):
        if not (self._in_head or self._in_title or self._hidden_depth):
            self.visible_words += len(data.split())

        if self._in_title:
            self._title_text += data
        elif self._in_heading:
            self._heading_text += data
        elif self._in_a:
            self._a_text += data
        elif self._in_script:
            self._script_content += data


def audit_file(filepath):
    """Audit a single HTML file and return issues."""
    issues = []
    info = []

    try:
        content = Path(filepath).read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return [{"severity": "error", "category": "file", "message": f"Cannot read file: {e}"}], []

    parser = SEOAuditParser()
    try:
        parser.feed(content)
    except Exception as e:
        return [{"severity": "error", "category": "parse", "message": f"HTML parse error: {e}"}], []

    # --- Technical SEO ---

    # Title
    if not parser.title:
        issues.append({"severity": "critical", "category": "technical-seo", "message": "Missing <title> tag"})
    elif len(parser.title) < 10:
        issues.append({"severity": "warning", "category": "technical-seo", "message": f"Title too short ({len(parser.title)} chars): '{parser.title}'"})
    elif len(parser.title) > 60:
        issues.append({"severity": "warning", "category": "technical-seo", "message": f"Title too long ({len(parser.title)} chars, recommended: 50-60)"})

    # Meta description
    if not parser.meta_description:
        issues.append({"severity": "critical", "category": "technical-seo", "message": "Missing meta description"})
    elif len(parser.meta_description) < 50:
        issues.append({"severity": "warning", "category": "technical-seo", "message": f"Meta description too short ({len(parser.meta_description)} chars)"})
    elif len(parser.meta_description) > 160:
        issues.append({"severity": "warning", "category": "technical-seo", "message": f"Meta description too long ({len(parser.meta_description)} chars, recommended: 140-160)"})

    # Viewport
    if not parser.meta_viewport:
        issues.append({"severity": "critical", "category": "technical-seo", "message": "Missing viewport meta tag (required for mobile-first indexing)"})

    # Charset
    if not parser.meta_charset:
        issues.append({"severity": "warning", "category": "technical-seo", "message": "Missing charset declaration (recommended: <meta charset=\"UTF-8\">)"})

    # Canonical
    if not parser.canonical:
        issues.append({"severity": "warning", "category": "technical-seo", "message": "Missing canonical URL (<link rel=\"canonical\">)"})

    # Lang attribute
    if not parser.lang:
        issues.append({"severity": "warning", "category": "technical-seo", "message": "Missing lang attribute on <html> tag"})

    # Meta robots noindex
    if parser.meta_robots:
        robots_tokens = {token.strip().lower() for token in parser.meta_robots.split(",")}
        if robots_tokens & {"noindex", "none"}:
            issues.append({
                "severity": "warning",
                "category": "technical-seo",
                "message": f"Meta robots is '{parser.meta_robots}', so search engines will not index this page. Is this intentional?"
            })

    # --- Content SEO ---

    # Heading hierarchy
    h1_count = sum(1 for h in parser.headings if h[0] == 1)
    if h1_count == 0:
        issues.append({"severity": "critical", "category": "content-seo", "message": "Missing H1 heading"})
    elif h1_count > 1:
        issues.append({"severity": "warning", "category": "content-seo", "message": f"Multiple H1 tags found ({h1_count}). Use exactly one H1 per page."})

    # Check heading hierarchy skips
    prev_level = 0
    for level, text in parser.headings:
        if prev_level > 0 and level > prev_level + 1:
            issues.append({
                "severity": "warning",
                "category": "content-seo",
                "message": f"Heading hierarchy skip: H{prev_level} -> H{level} ('{text[:40]}')"
            })
        prev_level = level

    # Images
    imgs_missing_alt = [img for img in parser.images if img["alt"] is None]
    imgs_missing_dimensions = [img for img in parser.images if not img["width"] or not img["height"]]

    if imgs_missing_alt:
        issues.append({
            "severity": "critical",
            "category": "content-seo",
            "message": f"{len(imgs_missing_alt)} image(s) missing alt attribute"
        })

    if imgs_missing_dimensions:
        issues.append({
            "severity": "warning",
            "category": "content-seo",
            "message": f"{len(imgs_missing_dimensions)} image(s) missing width/height (causes CLS)"
        })

    # --- Structured Data ---

    if not parser.json_ld:
        issues.append({"severity": "warning", "category": "structured-data", "message": "No JSON-LD structured data found"})
    else:
        for ld in parser.json_ld:
            if ld.get("_parse_error"):
                issues.append({"severity": "critical", "category": "structured-data", "message": "JSON-LD parse error (invalid JSON)"})
        info.append({"category": "structured-data", "message": f"Found {len(parser.json_ld)} JSON-LD block(s)"})

    # OpenGraph
    if not parser.og_tags:
        issues.append({"severity": "warning", "category": "structured-data", "message": "No OpenGraph meta tags found"})
    else:
        required_og = ["og:title", "og:type", "og:image", "og:url"]
        missing_og = [t for t in required_og if t not in parser.og_tags]
        if missing_og:
            issues.append({
                "severity": "warning",
                "category": "structured-data",
                "message": f"Missing OpenGraph tags: {', '.join(missing_og)}"
            })

    # Twitter Cards
    if not parser.twitter_tags:
        issues.append({"severity": "info", "category": "structured-data", "message": "No Twitter Card meta tags found"})
    elif "twitter:card" not in parser.twitter_tags:
        issues.append({"severity": "warning", "category": "structured-data", "message": "Missing twitter:card tag"})

    # --- Page Speed Hints ---

    # Render-blocking scripts
    blocking_scripts = [s for s in parser.scripts if not s["async"] and not s["defer"]]
    if blocking_scripts:
        issues.append({
            "severity": "warning",
            "category": "performance",
            "message": f"{len(blocking_scripts)} render-blocking script(s) (missing async/defer)"
        })

    # Lazy loading on LCP candidates (first image)
    if parser.images and parser.images[0].get("loading") == "lazy":
        issues.append({
            "severity": "warning",
            "category": "performance",
            "message": "First image has loading=\"lazy\" -- above-fold images should use loading=\"eager\" or fetchpriority=\"high\""
        })

    return issues, info


def robots_rule(is_allow, pattern):
    """Compile one rule once as (is_allow, pattern length, regex or None for an empty pattern).

    Runs of `*` collapse to one, so a rule such as `/*****X` cannot backtrack exponentially.
    """
    anchored = pattern.endswith("$")
    body = re.sub(r"\*+", "*", pattern[:-1] if anchored else pattern)
    regex = ".*".join(re.escape(part) for part in body.split("*")) + (r"\Z" if anchored else "")
    return is_allow, len(pattern), re.compile(regex) if pattern else None


def robots_groups(robots_text):
    """Split robots.txt into RFC 9309 groups of (user-agent values, [compiled rule]).

    Consecutive User-agent lines share a group and a User-agent line after a rule starts
    a new one. Blank lines, comments and other fields (Sitemap, Crawl-delay) are skipped.
    """
    groups = []
    for line in robots_text.splitlines():
        field, sep, value = line.split("#", 1)[0].partition(":")
        field, value = field.strip().lower(), value.strip()
        if not sep:
            continue
        if field == "user-agent":
            if not groups or groups[-1][1]:
                groups.append(([], []))
            groups[-1][0].append(value)
        elif field in ("allow", "disallow") and groups:
            groups[-1][1].append(robots_rule(field == "allow", value))
    return groups


def robots_rules_for(crawler, groups):
    """Return (source_group, merged rules) for the crawler's own groups, else the `*` groups.

    A matching group with no rules still counts, so it allows everything (RFC 9309, Google).
    """
    for wanted in (crawler.lower(), "*"):
        matched = []
        for agents, rules in groups:
            for agent in agents:
                token = "*" if agent.startswith("*") else re.match(r"[A-Za-z_-]*", agent).group().lower()
                if token == wanted:
                    matched.append((agent, rules))
                    break
        if matched:
            return f"User-agent: {matched[0][0]}", [rule for _, rules in matched for rule in rules]
    return None, []


def robots_allows(rules, path):
    """Longest matching pattern wins, with `*` and a trailing `$`; on a tie Allow wins."""
    best_length, allowed = -1, True
    for is_allow, length, regex in rules:
        if regex is None or not regex.match(path):
            continue
        if length > best_length or (length == best_length and is_allow):
            best_length, allowed = length, is_allow
    return allowed


def check_robots(robots_file):
    """Report each listed crawler that robots.txt blocks from the site or a key path."""
    try:
        with robots_file.open("rb") as handle:
            robots_bytes = handle.read(ROBOTS_MAX_BYTES + 1)
    except OSError as e:
        print(
            f"Error: cannot read robots.txt at {robots_file}: {e}. "
            "Make it a readable text file, then re-run the audit.",
            file=sys.stderr,
        )
        return [{
            "severity": "error",
            "category": "ai-bot",
            "message": f"Cannot read robots.txt at {robots_file}: {e}",
        }]

    findings = []
    if len(robots_bytes) > ROBOTS_MAX_BYTES:
        robots_bytes = robots_bytes[:ROBOTS_MAX_BYTES]
        print(f"Note: {robots_file} is over 500 KiB; only the first 500 KiB was read, as Google does.", file=sys.stderr)
        findings.append({
            "severity": "warning",
            "category": "ai-bot",
            "message": f"robots.txt at {robots_file} is over 500 KiB. Google ignores rules past 500 KiB, so the audit did too.",
        })
    # utf-8-sig drops a byte-order mark, which would otherwise be read as part of the first field.
    groups = robots_groups(robots_bytes.decode("utf-8-sig", errors="replace"))

    for crawler, role in ROBOTS_CRAWLERS.items():
        group, rules = robots_rules_for(crawler, groups)
        home_blocked = not robots_allows(rules, "/")
        deep_blocked = not robots_allows(rules, ROBOTS_DEEP_PROBE)
        if home_blocked or deep_blocked:
            scope = "the whole site" if home_blocked and deep_blocked else (
                "the homepage" if home_blocked else "every page except the homepage")
            findings.append({
                "severity": "critical" if crawler == "Googlebot" else "warning",
                "category": "ai-bot",
                "crawler": crawler,
                "source_group": group,
                "message": f"robots.txt blocks {crawler} ({role}) from {scope} through `{group}`. Is this block intentional?",
            })
            continue
        blocked_paths = [path for path in ROBOTS_KEY_PATHS if not robots_allows(rules, path)]
        if blocked_paths:
            findings.append({
                "severity": "info",
                "category": "ai-bot",
                "crawler": crawler,
                "source_group": group,
                "message": f"robots.txt blocks {crawler} from {', '.join(blocked_paths)} through `{group}`. Is this intentional?",
            })

    if not any(finding.get("crawler") for finding in findings):
        findings.append({
            "severity": "info",
            "category": "ai-bot",
            "message": f"robots.txt allows {', '.join(ROBOTS_CRAWLERS)} to crawl the site",
        })
    return findings


def raw_html_check(page_file, manifest_file):
    """Count what a crawler that does not run JavaScript sees in the saved raw HTML."""
    findings = []
    site_host = None
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        site_host = urllib.parse.urlsplit(manifest.get("final_url") or manifest.get("url") or "").netloc.lower()
    except (OSError, ValueError, AttributeError, TypeError) as e:
        print(
            f"Error: cannot read the page URL from {manifest_file}: {e}. "
            "Counting only relative links as internal; fix manifest.json to count absolute same-site links too.",
            file=sys.stderr,
        )
        findings.append({
            "severity": "error",
            "category": "raw-html",
            "message": f"Cannot read manifest.json ({e}); internal_links counts relative links only",
        })

    parser = SEOAuditParser()
    parser.feed(page_file.read_text(encoding="utf-8", errors="replace"))

    internal_links = 0
    for link in parser.links:
        href = link["href"].strip()
        if not href or href.startswith("#"):
            continue
        parts = urllib.parse.urlsplit(href)
        if parts.scheme in ("", "http", "https") and (not parts.netloc or parts.netloc.lower() == site_host):
            internal_links += 1

    stats = {
        "raw_text_words": parser.visible_words,
        "h1_count": sum(1 for level, _ in parser.headings if level == 1),
        "internal_links": internal_links,
    }
    if parser.has_app_mount and parser.scripts and parser.visible_words < APP_SHELL_MAX_WORDS:
        findings.append({
            "severity": "warning",
            "category": "raw-html",
            "message": (
                f"page.html is a JavaScript app shell ({parser.visible_words} visible words, an app mount element and script bundles): "
                "the page may look empty to crawlers that do not run JavaScript (practitioner: GPTBot and similar)"
            ),
        })
    return stats, findings


def has_server_rendering(project_root):
    """True when package.json names a server-rendering or static-generation framework.

    Called only when detect_framework returned Vite or React, which already rules out
    the Next, Nuxt, Astro, SvelteKit, Gatsby and Remix config files.
    """
    pkg_json = project_root / "package.json"
    if not pkg_json.exists():
        return False
    try:
        pkg = json.loads(pkg_json.read_text())
        all_deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    except (json.JSONDecodeError, KeyError):
        return False
    return any(
        dep in SERVER_RENDERING_DEPS or dep.startswith("@remix-run/") or (dep.startswith("@tanstack/") and dep.endswith("start"))
        for dep in all_deps
    )


def print_report(report):
    """Add project-level findings to the summary totals and print the report."""
    for check in report["project_checks"]:
        report["summary"][check["severity"]] = report["summary"].get(check["severity"], 0) + 1
    print(json.dumps(report, indent=2))


def audit_project(project_root, max_files=50):
    """Audit an entire project directory."""
    project_root = Path(project_root).resolve()
    report = {
        "project_root": str(project_root),
        "files_audited": 0,
        "files_skipped": 0,
        "summary": {"critical": 0, "warning": 0, "info": 0},
        "file_reports": [],
        "project_checks": [],
    }

    # Find HTML files
    html_extensions = {".html", ".htm", ".vue", ".svelte", ".astro", ".njk", ".ejs", ".hbs", ".jsx", ".tsx"}
    html_files = []
    for ext in html_extensions:
        html_files.extend(project_root.rglob(f"*{ext}"))

    # Filter out node_modules, build dirs, etc.
    skip_dirs = {"node_modules", ".next", ".nuxt", ".svelte-kit", "dist", "build", ".git", "__pycache__", "vendor"}
    html_files = [
        f for f in html_files
        if not any(part in skip_dirs for part in f.parts)
    ]

    if not html_files:
        report["project_checks"].append({
            "severity": "critical",
            "category": "structure",
            "message": "No HTML/template files found. This skill is designed for web frontends."
        })
        print_report(report)
        return report

    # Sample if too many files
    total = len(html_files)
    if total > max_files:
        report["files_skipped"] = total - max_files
        # Prioritize: index files, layouts, key templates
        priority_patterns = ["index", "layout", "base", "app", "page", "home", "head", "default"]
        priority = [f for f in html_files if any(p in f.stem.lower() for p in priority_patterns)]
        remaining = [f for f in html_files if f not in priority]
        html_files = (priority + remaining)[:max_files]
        report["project_checks"].append({
            "severity": "info",
            "category": "scope",
            "message": f"Large project ({total} files). Auditing {max_files} representative files. Run with --max-files to increase."
        })

    # Audit each file
    for filepath in sorted(html_files):
        rel_path = str(filepath.relative_to(project_root))
        issues, info = audit_file(filepath)
        report["files_audited"] += 1

        for issue in issues:
            report["summary"][issue["severity"]] = report["summary"].get(issue["severity"], 0) + 1

        if issues or info:
            report["file_reports"].append({
                "file": rel_path,
                "issues": issues,
                "info": info,
            })

    # --- Project-level checks ---

    # robots.txt
    robots_path = project_root / "robots.txt"
    public_robots = project_root / "public" / "robots.txt"
    static_robots = project_root / "static" / "robots.txt"

    robots_file = None
    for candidate in [robots_path, public_robots, static_robots]:
        if candidate.exists():
            robots_file = candidate
            break

    if not robots_file:
        report["project_checks"].append({
            "severity": "warning",
            "category": "ai-bot",
            "message": "No robots.txt found"
        })
    else:
        report["project_checks"].extend(check_robots(robots_file))

    # Raw HTML as fetched without JavaScript (live-evidence mode: a search-optimizer evidence dir)
    manifest_file = project_root / "manifest.json"
    page_file = project_root / "page.html"
    live_evidence = manifest_file.is_file() and page_file.is_file()
    if live_evidence:
        report["raw_html"], raw_findings = raw_html_check(page_file, manifest_file)
        report["project_checks"].extend(raw_findings)

    # sitemap.xml
    sitemap_candidates = [
        project_root / "sitemap.xml",
        project_root / "public" / "sitemap.xml",
        project_root / "static" / "sitemap.xml",
    ]
    sitemap_found = any(c.exists() for c in sitemap_candidates)
    if not sitemap_found:
        # Check if dynamically generated (e.g., next-sitemap, @astrojs/sitemap)
        pkg_json = project_root / "package.json"
        has_sitemap_pkg = False
        if pkg_json.exists():
            try:
                pkg = json.loads(pkg_json.read_text())
                all_deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                sitemap_pkgs = ["next-sitemap", "@astrojs/sitemap", "nuxt-simple-sitemap", "sitemap", "gatsby-plugin-sitemap"]
                has_sitemap_pkg = any(p in all_deps for p in sitemap_pkgs)
            except (json.JSONDecodeError, KeyError):
                pass

        if not has_sitemap_pkg:
            report["project_checks"].append({
                "severity": "warning",
                "category": "technical-seo",
                "message": "No sitemap.xml found (and no sitemap generation package detected)"
            })

    # llms.txt
    llms_candidates = [
        project_root / "llms.txt",
        project_root / "public" / "llms.txt",
        project_root / "static" / "llms.txt",
    ]
    llms_found = any(c.exists() for c in llms_candidates)
    if not llms_found:
        report["project_checks"].append({
            "severity": "info",
            "category": "ai-bot",
            "message": "No llms.txt found (optional; used by some AI tools, not by Google Search)."
        })

    # ai-plugin.json
    ai_plugin_candidates = [
        project_root / ".well-known" / "ai-plugin.json",
        project_root / "public" / ".well-known" / "ai-plugin.json",
        project_root / "static" / ".well-known" / "ai-plugin.json",
    ]
    ai_plugin_found = any(c.exists() for c in ai_plugin_candidates)
    if not ai_plugin_found:
        report["project_checks"].append({
            "severity": "info",
            "category": "ai-bot",
            "message": "No .well-known/ai-plugin.json found (optional -- for AI agent discovery)"
        })

    # Framework detection
    framework = detect_framework(project_root)
    if framework:
        report["project_checks"].append({
            "severity": "info",
            "category": "framework",
            "message": f"Detected framework: {framework}"
        })
    if not live_evidence and framework in ("Vite", "React") and not has_server_rendering(project_root):
        report["project_checks"].append({
            "severity": "info",
            "category": "raw-html",
            "message": f"Client-only SPA ({framework}, no server rendering or static generation found): raw HTML is likely empty for crawlers that do not run JavaScript"
        })

    print_report(report)
    return report


def detect_framework(project_root):
    """Detect the web framework used in the project."""
    for filename, framework in FRAMEWORK_CONFIG_FILES.items():
        if (project_root / filename).exists():
            return framework

    # Check package.json for framework deps
    pkg_json = project_root / "package.json"
    if pkg_json.exists():
        try:
            pkg = json.loads(pkg_json.read_text())
            all_deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            framework_deps = {
                "next": "Next.js", "nuxt": "Nuxt", "astro": "Astro",
                "@sveltejs/kit": "SvelteKit", "gatsby": "Gatsby",
                "@angular/core": "Angular", "@remix-run/react": "Remix",
                "vue": "Vue", "react": "React",
            }
            for dep, fw in framework_deps.items():
                if dep in all_deps:
                    return fw
        except (json.JSONDecodeError, KeyError):
            pass

    return None


def positive_file_limit(value):
    """Parse a strictly positive --max-files value for argparse."""
    try:
        limit = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"must be an integer greater than 0, got {value!r}; "
            "use a value such as `--max-files 50`"
        ) from exc

    if limit <= 0:
        raise argparse.ArgumentTypeError(
            f"must be greater than 0, got {value!r}; "
            "use a value such as `--max-files 50`"
        )
    return limit


def main():
    parser = argparse.ArgumentParser(
        description="Audit a web project for common SEO and AI bot issues."
    )
    parser.add_argument("project_root", metavar="project-root")
    parser.add_argument(
        "--max-files",
        type=positive_file_limit,
        default=50,
        metavar="N",
        help="maximum number of representative files to audit (must be greater than 0)",
    )
    args = parser.parse_args()

    if not Path(args.project_root).exists():
        print(
            f"Error: project root does not exist: {args.project_root!r}. "
            "Pass the path to an existing web project directory.",
            file=sys.stderr,
        )
        sys.exit(1)

    audit_project(args.project_root, args.max_files)


if __name__ == "__main__":
    main()
