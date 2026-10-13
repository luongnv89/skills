"""Unit tests for scripts/pages_publish.py: sync-site, check-site and workflow --offline.

Every test runs the CLI against a throwaway git repo in a temp folder. Nothing touches the
network or GitHub, and the user's global git config is ignored.

Run from the skill folder:
    python3 -m unittest discover -s tests -p 'test_*.py' -v
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "scripts", "pages_publish.py")

GIT_ENV = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
               GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.com",
               GIT_LITERAL_PATHSPECS="1")


def write(root, files):
    for rel, body in files.items():
        full = os.path.join(root, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as f:
            f.write(body.encode() if isinstance(body, str) else body)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pages-publish-test-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.repo)
        self.git("init", "-q", "-b", "main")
        self.n = 0

    def git(self, *args):
        p = subprocess.run(["git", "-C", self.repo] + list(args), env=GIT_ENV,
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        return p.stdout

    def cli(self, *args, code=0):
        p = subprocess.run([sys.executable, SCRIPT] + list(args), env=GIT_ENV,
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, code, p.stdout + p.stderr)
        return json.loads(p.stdout)

    def content(self, files):
        """A fresh source folder holding `files`."""
        self.n += 1
        src = os.path.join(self.tmp, "content%d" % self.n)
        os.makedirs(src)
        write(src, files)
        return src

    def commit_initial(self, files):
        write(self.repo, files)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "init")

    def publish(self, files, site_dir, *extra, code=0):
        """Run sync-site like the skill does, then commit only the paths it listed."""
        paths = os.path.join(self.tmp, "paths%d.txt" % (self.n + 1))
        res = self.cli("sync-site", "--src", self.content(files), "--repo-dir", self.repo,
                       "--site-dir", site_dir, "--paths-out", paths, *extra, code=code)
        listed = read(paths).splitlines() if os.path.exists(paths) else []
        if listed:
            self.git("add", "-A", "-f", "--pathspec-from-file=" + paths)
            self.git("commit", "-q", "-m", "publish", "--pathspec-from-file=" + paths)
        return res, listed

    def committed(self):
        return set(self.git("ls-tree", "-r", "--name-only", "HEAD").split())

    def manifest(self):
        return json.loads(self.git("show", "HEAD:.github/pages-publish.json"))


class SyncSiteTest(Base):
    def test_republish_deletes_files_dropped_from_the_site(self):
        self.publish({"index.html": "v1", "old.html": "old"}, "docs")
        res, listed = self.publish({"index.html": "v2"}, "docs")
        self.assertEqual(res["deleted"], ["old.html"])
        self.assertEqual(res["changed"], ["index.html"])
        self.assertIn("docs/old.html", listed)
        self.assertNotIn("docs/old.html", self.committed())
        self.assertEqual(self.manifest()["files"], ["index.html"])

    def test_first_publish_to_root_without_manifest_sweeps_nothing(self):
        self.commit_initial({"README.md": "readme", "other.html": "x", "src/main.py": "print()"})
        res, _ = self.publish({"index.html": "home"}, ".")
        self.assertEqual(res["deleted"], [])
        self.assertFalse(res["first_publish_sweep"])
        self.assertIn("other.html", res["stale_not_deleted"])
        self.assertTrue({"README.md", "other.html", "src/main.py", "index.html"} <= self.committed())

    def test_cname_is_kept_when_sweeping_a_site_folder(self):
        self.commit_initial({"docs/CNAME": "example.com\n", "docs/old.html": "old"})
        res, _ = self.publish({"index.html": "home"}, "docs")
        self.assertEqual(res["deleted"], ["old.html"])
        self.assertTrue(res["first_publish_sweep"])
        self.assertIn("docs/CNAME", self.committed())
        self.assertTrue(os.path.exists(os.path.join(self.repo, "docs", "CNAME")))

    def test_untracked_identical_file_is_still_committed(self):
        write(self.repo, {"docs/index.html": "home"})  # on disk, never committed
        res, listed = self.publish({"index.html": "home"}, "docs")
        self.assertEqual(res["added"], ["index.html"])
        self.assertIn("docs/index.html", listed)
        self.assertIn("docs/index.html", self.committed())

    def test_rerun_with_same_content_is_a_noop(self):
        files = {"index.html": "home", "css/a.css": "body{}"}
        self.publish(files, "docs")
        res, listed = self.publish(files, "docs")
        self.assertEqual((res["added"], res["changed"], res["deleted"]), ([], [], []))
        self.assertFalse(res["manifest_changed"])
        self.assertEqual(listed, [])
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_rerun_is_a_noop_with_autocrlf(self):
        self.git("config", "core.autocrlf", "true")
        files = {"index.html": "<p>a</p>\r\n<p>b</p>\r\n"}
        self.publish(files, "docs")
        res, listed = self.publish(files, "docs")
        self.assertEqual((res["added"], res["changed"], res["deleted"]), ([], [], []))
        self.assertFalse(res["manifest_changed"])
        self.assertEqual(listed, [])

    def test_site_dir_change_without_move_from_is_a_conflict(self):
        self.publish({"index.html": "home"}, "docs")
        res, _ = self.publish({"index.html": "home"}, ".", code=3)
        self.assertEqual(res["conflict"], "site-dir-changed")

    def test_move_without_overlap_deletes_the_old_folder(self):
        self.publish({"index.html": "home", "about.html": "about"}, "docs")
        res, listed = self.publish({"index.html": "home2"}, "site", "--move-from", "docs")
        self.assertEqual(res["moved_from"], "docs")
        self.assertEqual(sorted(res["deleted_from_old_dir"]), ["docs/about.html", "docs/index.html"])
        self.assertTrue({"docs/about.html", "docs/index.html", "site/index.html"} <= set(listed))
        tree = self.committed()
        self.assertIn("site/index.html", tree)
        self.assertFalse({"docs/about.html", "docs/index.html"} & tree)
        self.assertEqual(self.manifest()["site_dir"], "site")

    def test_move_root_to_docs_keeps_overlapping_page(self):
        # Issue 418: the old root site already had docs/a.html; the new docs/ site has a.html.
        self.publish({"index.html": "home", "docs/a.html": "old a", "gone.html": "x"}, ".")
        res, listed = self.publish({"index.html": "new home", "a.html": "new a"}, "docs",
                                   "--move-from", ".")
        self.assertNotIn("docs/a.html", res["deleted_from_old_dir"])
        self.assertIn("gone.html", res["deleted_from_old_dir"])
        self.assertEqual(read(os.path.join(self.repo, "docs", "a.html")), "new a")
        self.assertIn("docs/a.html", listed)
        tree = self.committed()
        self.assertIn("docs/a.html", tree)
        self.assertNotIn("gone.html", tree)
        self.assertEqual(self.git("show", "HEAD:docs/a.html"), "new a")
        self.assertEqual(self.manifest()["files"], ["a.html", "index.html"])

    def test_move_root_to_docs_keeps_identical_overlapping_page(self):
        # Same overlap, but the page is unchanged: it is neither copied nor re-added, so only
        # the delete list could lose it.
        self.publish({"index.html": "home", "docs/a.html": "same"}, ".")
        res, listed = self.publish({"index.html": "home", "a.html": "same"}, "docs",
                                   "--move-from", ".")
        self.assertNotIn("docs/a.html", res["deleted_from_old_dir"])
        self.assertNotIn("docs/a.html", listed)
        self.assertTrue(os.path.exists(os.path.join(self.repo, "docs", "a.html")))
        self.assertIn("docs/a.html", self.committed())

    def test_move_docs_to_root_keeps_overlapping_page(self):
        # Issue 418, other direction: the new root site has a docs/ subfolder.
        self.publish({"index.html": "home", "a.html": "old a"}, "docs")
        res, listed = self.publish({"index.html": "root home", "docs/a.html": "new a"}, ".",
                                   "--move-from", "docs")
        self.assertNotIn("docs/a.html", res["deleted_from_old_dir"])
        self.assertIn("docs/index.html", res["deleted_from_old_dir"])
        self.assertEqual(read(os.path.join(self.repo, "docs", "a.html")), "new a")
        tree = self.committed()
        self.assertIn("docs/a.html", tree)
        self.assertNotIn("docs/index.html", tree)
        self.assertEqual(self.git("show", "HEAD:docs/a.html"), "new a")
        self.assertIn("docs/a.html", listed)


class CheckSiteTest(Base):
    def check(self, files, *extra, code=0):
        src = self.content(files)
        return src, self.cli("check-site", "--dir", src, *extra, code=code)

    def test_project_site_fix_rewrites_quoted_links_and_keeps_base_path(self):
        files = {
            "index.html": ('<link href="/css/a.css" rel="stylesheet"><a href="/demo/sub/">x</a>'
                           '<img src="/img/a.png" srcset="/img/a.png 1x, /demo/img/b.png 2x">'
                           '<div style="background:url(/img/a.png)"></div>'),
            "sub/index.html": '<a href="/">home</a><img src="/img/a.png">',
            "css/a.css": "body{background:url('/img/a.png')} p{background:url(/demo/img/b.png)}",
            "img/a.png": "a", "img/b.png": "b",
        }
        src, res = self.check(files, "--project-site", "demo", "--fix-root-links")
        self.assertTrue(res["ok"], res["errors"])
        index = read(os.path.join(src, "index.html"))
        self.assertIn('href="css/a.css"', index)
        self.assertIn('href="/demo/sub/"', index)
        self.assertIn('srcset="img/a.png 1x, /demo/img/b.png 2x"', index)
        self.assertIn("url(img/a.png)", index)
        sub = read(os.path.join(src, "sub", "index.html"))
        self.assertIn('href="../"', sub)
        self.assertIn('src="../img/a.png"', sub)
        css = read(os.path.join(src, "css", "a.css"))
        self.assertIn("url('../img/a.png')", css)
        self.assertIn("url(/demo/img/b.png)", css)

    def test_project_site_without_fix_reports_root_links(self):
        _, res = self.check({"index.html": '<a href="/x.html">x</a>', "x.html": "x"},
                            "--project-site", "demo", code=1)
        self.assertEqual([e["id"] for e in res["errors"]], ["root-absolute-link"])

    def test_unquoted_root_link_is_reported(self):
        _, res = self.check({"index.html": "<a href=/x.html>x</a>", "x.html": "x"},
                            "--project-site", "demo", code=1)
        self.assertEqual([(e["id"], e["link"]) for e in res["errors"]],
                         [("root-absolute-link", "/x.html")])

    def test_fix_rewrites_unquoted_links_in_one_run(self):
        # Issue 419: minified output (Hugo --minify) drops attribute quotes.
        files = {
            "index.html": ("<link rel=stylesheet href=/css/a.css><a href=/sub/page.html>p</a>"
                           "<a href=/demo/sub/page.html>kept</a><img src=/img/a.png "
                           "srcset=/img/a.png,/demo/img/b.png><video poster=/img/a.png></video>"
                           "<form action=/sub/page.html></form><object data=/img/b.png></object>"
                           "<a href=/>home</a><div data-src=/nope></div>"),
            "sub/page.html": "<a href=/index.html>up</a><img src=/img/a.png>",
            "css/a.css": "", "img/a.png": "a", "img/b.png": "b",
        }
        src, res = self.check(files, "--project-site", "demo", "--fix-root-links")
        self.assertTrue(res["ok"], res["errors"])
        index = read(os.path.join(src, "index.html"))
        for frag in ("href=css/a.css>", "href=sub/page.html>", "href=/demo/sub/page.html>",
                     "src=img/a.png ", "srcset=img/a.png,/demo/img/b.png>", "poster=img/a.png>",
                     "action=sub/page.html>", "data=img/b.png>", "href=./>",
                     "data-src=/nope>"):
            self.assertIn(frag, index)
        sub = read(os.path.join(src, "sub", "page.html"))
        self.assertIn("href=../index.html>", sub)
        self.assertIn("src=../img/a.png>", sub)
        # A second check, without the fix, finds nothing left to rewrite.
        again = self.cli("check-site", "--dir", src, "--project-site", "demo")
        self.assertTrue(again["ok"], again["errors"])


class WorkflowTest(Base):
    def test_offline_workflow_is_created_then_unchanged(self):
        paths = os.path.join(self.tmp, "paths.txt")
        res = self.cli("workflow", "--repo-dir", self.repo, "--site-dir", "docs", "--branch", "main",
                       "--offline", "--paths-out", paths)
        self.assertEqual(res["action"], "created")
        self.assertEqual(set(res["version_source"].values()), {"fallback"})
        text = read(os.path.join(self.repo, ".github", "workflows", "pages.yml"))
        self.assertIn("Managed by the github-pages-publish skill", text)
        self.assertIn("- 'docs/**'", text)
        self.assertIn("path: docs", text)
        self.assertEqual(read(paths).splitlines(), [".github/workflows/pages.yml"])
        again = self.cli("workflow", "--repo-dir", self.repo, "--site-dir", "docs", "--branch", "main",
                         "--offline", "--keep-versions")
        self.assertEqual(again["action"], "unchanged")

    def test_unmanaged_building_workflow_is_a_conflict(self):
        write(self.repo, {".github/workflows/site.yml": (
            "jobs:\n  b:\n    steps:\n      - run: npm run build\n"
            "      - uses: actions/deploy-pages@v4\n")})
        res = self.cli("workflow", "--repo-dir", self.repo, "--site-dir", "docs", "--branch", "main",
                       "--offline", code=3)
        self.assertEqual(res["conflict"], "existing-pages-workflow")


if __name__ == "__main__":
    unittest.main()
