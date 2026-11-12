#!/usr/bin/env python3
"""Directory-edition checks for lstack, using stdlib and isolated Git fixtures only."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("base_tests", ROOT / "tests/test-lstack-packaging.py")
BASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BASE)
DSPEC = importlib.util.spec_from_file_location("lstack_directory", ROOT / "scripts/build-lstack-directory.py")
EDITION = importlib.util.module_from_spec(DSPEC)
DSPEC.loader.exec_module(EDITION)
ALLOWED = set(EDITION.SKILL_KEYS)


def skill(name, extra="", body="# Body\n\nKeep these bytes: `effort: max`.\n"):
    return ("---\nname: " + name + "\ndescription: \"Fixture skill " + name + ". Second sentence.\"\n"
            "license: MIT\n" + extra + "metadata:\n  version: 1.2.3\n  author: \"Fixture <f@example.invalid>\"\n"
            "---\n" + body)


class DirectoryEditionTests(unittest.TestCase):
    git = BASE.PackagingTests.git
    put = BASE.PackagingTests.put
    commit = BASE.PackagingTests.commit
    update_manifest = BASE.PackagingTests.update_manifest

    def setUp(self):
        BASE.PackagingTests.setUp(self)
        # parent ships scripts/run.sh (#!), child is Markdown only.
        self.put("skills/parent/SKILL.md", skill("parent"))
        self.put("skills/parent/child/SKILL.md", skill("child", "effort: high\n"))
        self.manifest["claude"] = {
            "description": "Fixture skills", "author": {"name": "Fixture author"},
            "repository": "https://example.invalid/fixture", "license": "MIT",
            "marketplace_name": "lstack-local"}
        self.update_manifest()

    def add_member(self, name, text, files=None):
        self.put("skills/" + name + "/SKILL.md", text)
        for rel, data in (files or {}).items():
            self.put("skills/" + name + "/" + rel, data)
        self.manifest["members"].append({"name": name, "source": "skills/" + name})
        self.update_manifest()

    def build(self):
        files, summary = EDITION.prepare(self.repo)
        out = Path(self.tmp.name) / "edition"
        EDITION.write(out, files)
        return out, files, summary

    def frontmatter(self, data):
        block = EDITION.split_frontmatter(data.decode(), "x")[0]
        return EDITION.parse_frontmatter(block, "x")

    def test_selects_members_and_builds_a_clean_plugin_folder(self):
        out, files, summary = self.build()
        self.assertEqual(summary["included"], ["child"])
        self.assertIn("scripts/run.sh", summary["excluded"]["parent"])
        self.assertIn("skills/child/SKILL.md", files)
        self.assertFalse(any(p.startswith("skills/parent/") for p in files))
        plugin = json.loads(files["skills/.claude-plugin/plugin.json"])
        self.assertEqual((plugin["name"], plugin["version"]), ("lstack", "0.1.0"))
        self.assertTrue(plugin["description"].startswith("1 first-party"))
        self.assertEqual(plugin["skills"], ["./"])  # members sit at the plugin root, not in ./skills/
        self.assertGreaterEqual(EDITION.readme_words(files["skills/README.md"].decode()), 40)
        self.assertIn("parent", files["skills/README.md"].decode())
        for path in ("skills/LICENSE", "LICENSE", "README.md", "provenance.json"):
            self.assertIn(path, files)
        provenance = json.loads(files["provenance.json"])
        self.assertEqual(provenance["source_commit"], self.git("rev-parse", "HEAD").decode().strip())
        self.assertEqual(EDITION.check_tree(out)[0], [])
        self.assertTrue(all(oct(p.stat().st_mode & 0o777) == "0o644" for p in out.rglob("*") if p.is_file()))

    def test_moves_effort_and_dependencies_into_metadata_and_keeps_the_body(self):
        body = "# Router\n\nRun `asm deps acquire child`.\r\n---\nnot frontmatter: here\n"
        self.add_member("router", skill("router", "effort: max\ndependencies:\n  - child\n", body),
                        {"references/a.md": "ref\n"})
        _, files, summary = self.build()
        self.assertIn("router", summary["included"])
        data = files["skills/router/SKILL.md"]
        top, metadata, deps = self.frontmatter(data)
        self.assertEqual(set(top), {"name", "description", "license", "metadata"})
        self.assertEqual(deps, [])
        self.assertEqual(metadata, {"version": "1.2.3", "author": "Fixture <f@example.invalid>",
                                    "effort": "max", "dependencies": "child"})
        self.assertTrue(data.endswith(b"---\n" + body.encode()))
        self.assertIn(b'  version: "1.2.3"\n', data)
        self.assertEqual(files["skills/router/references/a.md"], b"ref\n")

    def test_flow_list_dependencies_are_moved_too(self):
        self.add_member("flow", skill("flow", "dependencies: [child, \"child\"]\n"))
        _, files, _ = self.build()
        self.assertEqual(self.frontmatter(files["skills/flow/SKILL.md"])[1]["dependencies"], "child, child")

    def test_leaves_out_skills_whose_dependencies_are_not_in_the_edition(self):
        self.add_member("needs-parent", skill("needs-parent", "dependencies:\n  - parent\n"))
        self.add_member("needs-needer", skill("needs-needer", "dependencies:\n  - needs-parent\n"))
        self.add_member("needs-external", skill("needs-external", "dependencies:\n  - \"github:o/r:skills/x\"\n"))
        _, files, summary = self.build()
        self.assertEqual(summary["included"], ["child"])
        self.assertIn("parent", summary["excluded"]["needs-parent"])
        self.assertIn("needs-parent", summary["excluded"]["needs-needer"])
        self.assertIn("github:o/r:skills/x", summary["excluded"]["needs-external"])

    def test_file_rule_cases(self):
        png = b"\x89PNG\r\n\x1a\n" + b"\0" * 8
        cases = {
            ("a/x.py", b"print(1)\n"): "type outside", ("a/x.sh", b"echo\n"): "type outside",
            ("a/x.html", b"<p>\n"): "type outside", ("a/LICENSE-MIT", b"MIT\n"): "type outside",
            ("a/x.md", b"#!/bin/sh\n"): "starts with #!", ("a/x.md", b"\xef\xbb\xbf#!/bin/sh\n"): "starts with #!",
            ("a/x.md", b"a\0b"): "NUL", ("a/x.md", b"\xff\xfe"): "not UTF-8",
            ("a/package.json", b"{}"): "package-manager", ("a/.npmrc", b"x=1\n"): "package-manager",
            ("a/pnpm-workspace.yaml", b"a: 1\n"): "package-manager",
            ("a/x.md", b"a" * (256 * 1024)): "256 KiB", ("a/.DS_Store", b"x"): "operating-system",
            ("a/x.png", b"MZ\x90\0"): "not a PNG", ("a/x.webp", b"RIFF0000AVI "): "not a WEBP",
            ("a/x.svg", b"<svg/>"): "type outside", ("a/x.ico", b"\0\0\1\0"): "type outside",
            ("a/Makefile", b"all:\n"): "type outside", ("a/COPYING", b"GPL\n"): "type outside",
            ("a/X.PY", b"x\n"): "type outside", ("a/__MACOSX", b"x"): "operating-system",
            ("a/composer.json", b"{}"): "package-manager", ("a/requirements-dev.txt", b"x\n"): "package-manager",
            ("a/environment.yml", b"a: 1\n"): "package-manager", ("a/Package.JSON", b"{}"): "package-manager",
        }
        for (path, data), expected in cases.items():
            self.assertIn(expected, EDITION.file_problem(path, data) or "", path)
        for path, data in [("a/x.md", b"# ok\n"), ("a/x.yml", b"a: 1\n"), ("a/x.json", b"{}\n"),
                           ("a/x.png", png), ("a/LICENSE", b"MIT\n"), ("a/.gitignore", b"x\n"),
                           ("a/x.txt", "é\n".encode()), ("a/X.PNG", png), ("a/README.MD", b"# x\n")]:
            self.assertIsNone(EDITION.file_problem(path, data), path)

    def test_check_tree_refuses_each_kind_of_problem(self):
        out, _, _ = self.build()
        child = out / "skills/child"
        planted = [("helper.py", b"x\n"), ("note.md", b"#!/usr/bin/env python3\n"), ("bin.md", b"\0"),
                   ("package.json", b"{}\n"), ("big.md", b"a" * (300 * 1024))]
        for name, data in planted:
            (child / name).write_bytes(data)
        (child / "link.md").symlink_to(out / "README.md")
        (child / "__MACOSX").mkdir()
        skill_md = child / "SKILL.md"
        skill_md.write_text(skill_md.read_text().replace("license: MIT\n", "license: MIT\nhooks: x\n")
                            .replace('  version: "1.2.3"', "  version: 1.2.3"))
        problems = "\n".join(EDITION.check_tree(out)[0])
        for needle in ("helper.py", "note.md: starts with #!", "bin.md", "package.json", "big.md",
                       "link.md: symlink", "__MACOSX: operating-system file",
                       "outside the allowed list: hooks", "metadata.version is not a quoted"):
            self.assertIn(needle, problems)

    def test_check_tree_counts_files_and_notes_resource_frontmatter(self):
        out, _, _ = self.build()
        (out / "skills/child/agents").mkdir()
        (out / "skills/child/agents/a.md").write_text("---\nname: a\ndescription: d\nrole: r\n---\nx\n")
        problems, count, notes = EDITION.check_tree(out)
        self.assertEqual(problems, [])
        self.assertIn("agents/a.md", notes[0])
        for i in range(EDITION.MAX_FILES):
            (out / "skills/child" / ("f%03d.md" % i)).write_text("x\n")
        self.assertIn("files (limit 512)", "\n".join(EDITION.check_tree(out)[0]))

    def test_check_tree_refuses_a_plugin_that_loads_no_skills_or_a_bad_root(self):
        out, files, _ = self.build()
        manifest = out / "skills/.claude-plugin/plugin.json"
        data = json.loads(manifest.read_text())
        del data["skills"]
        manifest.write_text(json.dumps(data))
        self.assertIn("load only with", "\n".join(EDITION.check_tree(out)[0]))
        manifest.unlink()
        self.assertIn("plugin.json missing", "\n".join(EDITION.check_tree(out)[0]))
        (out / ".git").mkdir()
        (out / "skills/child/.git").mkdir()
        (out / "skills/child/.git/hook").write_bytes(b"#!/bin/sh\n")
        self.assertIn(".git/hook", "\n".join(EDITION.check_tree(out)[0]))
        linked = Path(self.tmp.name) / "linked"
        (linked).mkdir()
        (linked / "skills").symlink_to(out / "skills")
        self.assertIn("missing or a symlink", EDITION.check_tree(linked)[0][0])

    def test_refuses_unsafe_values_duplicates_and_conflicts(self):
        base = skill("v")
        for text, pattern in [
                (base.replace("Second sentence.", "a\\u007fb"), "unsupported character"),
                (base.replace("Second sentence.", "a\\u0085b"), "unsupported character"),
                (base.replace("Second sentence.", "a\\u2028b"), "unsupported character"),
                (base.replace("license: MIT\n", "license: MIT\nlicense: MIT\n"), "unsupported frontmatter line"),
                (base.replace("  version: 1.2.3\n", "  version: 1.2.3\n  version: 1.2.4\n"), "unsupported frontmatter line"),
                (base.replace("license: MIT\n", "license: MIT # c\n"), "unsupported frontmatter value"),
                (base.replace("license: MIT\n", "license: a: b\n"), "unsupported frontmatter value"),
                (base.replace("license: MIT\n", "effort: high\n").replace("  version: 1.2.3\n", "  version: 1.2.3\n  effort: low\n"), "both effort"),
                (base.replace("license: MIT\n", "dependencies: [a, b\n"), "unsupported dependencies"),
                ("---\nname: v\ndescription: d\nmetadata: {version: 1.0.0}\n---\nx\n", "flow-form metadata")]:
            with self.assertRaisesRegex(ValueError, pattern):
                EDITION.standard_skill_md(text.encode(), "v/SKILL.md")

    def test_self_dependency_is_kept(self):
        self.add_member("selfish", skill("selfish", "dependencies:\n  - selfish\n"))
        self.assertIn("selfish", self.build()[2]["included"])

    def test_refuses_unknown_keys_and_unsupported_yaml(self):
        self.add_member("hooked", skill("hooked", "hooks: {}\n"))
        with self.assertRaisesRegex(ValueError, "outside the allowed list.*hooks"):
            EDITION.prepare(self.repo)
        self.put("skills/hooked/SKILL.md", skill("hooked").replace(
            'description: "Fixture skill hooked. Second sentence."', "description: >\n  folded text"))
        self.commit()
        with self.assertRaisesRegex(ValueError, "unsupported frontmatter"):
            EDITION.prepare(self.repo)

    def test_write_needs_a_new_or_empty_folder(self):
        files, _ = EDITION.prepare(self.repo)
        target = Path(self.tmp.name) / "busy"
        target.mkdir()
        (target / ".git").write_text("gitdir: elsewhere\n")
        EDITION.write(target, files)  # a worktree's .git file is allowed
        with self.assertRaisesRegex(ValueError, "new or empty folder"):
            EDITION.write(target, files)
        with self.assertRaisesRegex(ValueError, "inside this repository"):
            EDITION.write(ROOT / "dist" / "edition-test-never-created", files)
        empty = Path(self.tmp.name) / "empty"
        empty.mkdir()
        link = Path(self.tmp.name) / "link"
        link.symlink_to(empty)
        afile = Path(self.tmp.name) / "afile"
        afile.write_text("x")
        for bad in (link, afile):
            with self.assertRaisesRegex(ValueError, "new or empty folder"):
                EDITION.write(bad, files)
        self.assertEqual(list(empty.iterdir()), [])

    def test_real_catalog_builds_and_passes_its_own_check(self):
        files, summary = EDITION.prepare(ROOT)
        members = {m["name"] for m in json.loads((ROOT / "packages/lstack/manifest.json").read_text())["members"]}
        self.assertEqual(set(summary["included"]) | set(summary["excluded"]), members)
        self.assertTrue(summary["included"])
        readme = files["skills/README.md"].decode()
        self.assertIn(" %d first-party" % len(summary["included"]), readme)
        self.assertIn("full %d-skill" % len(members), json.loads(files["skills/.claude-plugin/plugin.json"])["description"])
        for path, data in files.items():
            self.assertIsNone(EDITION.file_problem(path, data), path)
            if path.endswith("/SKILL.md"):
                self.assertLessEqual(set(self.frontmatter(data)[0]), ALLOWED, path)
        with tempfile.TemporaryDirectory() as tmp:
            EDITION.write(Path(tmp) / "e", files)
            self.assertEqual(EDITION.check_tree(Path(tmp) / "e")[0], [])
            cli = subprocess.run([sys.executable, str(ROOT / "scripts/build-lstack-directory.py"),
                                  "--check", str(Path(tmp) / "e")], capture_output=True, text=True,
                                 env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
            self.assertEqual(cli.returncode, 0, cli.stderr)
            self.assertEqual(json.loads(cli.stdout)["problems"], [])


    def test_cli_refuses_a_builder_that_differs_from_the_revision(self):
        repo = Path(self.tmp.name) / "clone"
        subprocess.run(["git", "clone", "-q", str(ROOT), str(repo)], check=True)
        subprocess.run(["git", "-C", str(repo), "checkout", "-q", subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"]).decode().strip()], check=True)
        # Test the builder under test (the working tree), not the one in the commit.
        for script in ("scripts/build-lstack-directory.py", "scripts/build-lstack.py"):
            (repo / script).write_bytes((ROOT / script).read_bytes())
        subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid",
                        "-c", "core.hooksPath=/dev/null", "commit", "-qam", "builder", "--allow-empty"],
                       check=True)
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        for script in ("scripts/build-lstack-directory.py", "scripts/build-lstack.py"):
            target = repo / script
            original = target.read_bytes()
            target.write_bytes(original + b"\n# local edit\n")
            cli = subprocess.run([sys.executable, str(repo / "scripts/build-lstack-directory.py"), "--list"],
                                 capture_output=True, text=True, env=env)
            self.assertEqual(cli.returncode, 1, script)
            self.assertIn("differs from the selected revision", cli.stderr)
            target.write_bytes(original)
        cli = subprocess.run([sys.executable, str(repo / "scripts/build-lstack-directory.py"), "--list",
                              "--revision", "HEAD~1000000"], capture_output=True, text=True, env=env)
        self.assertEqual(cli.returncode, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
