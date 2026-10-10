#!/usr/bin/env python3
"""Claude adapter regression checks, using stdlib and isolated Git fixtures only."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest
import zipfile

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("base_tests", ROOT / "tests/test-lstack-packaging.py")
BASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BASE)
BUILDER = BASE.BUILDER


class ClaudePackagingTests(unittest.TestCase):
    git = BASE.PackagingTests.git
    put = BASE.PackagingTests.put
    commit = BASE.PackagingTests.commit
    update_manifest = BASE.PackagingTests.update_manifest
    artifact = BASE.PackagingTests.artifact

    def setUp(self):
        BASE.PackagingTests.setUp(self)
        self.manifest["claude"] = {
            "description": "Fixture skills", "author": {"name": "Fixture author"},
            "repository": "https://example.invalid/fixture", "license": "MIT",
            "marketplace_name": "lstack-local"}
        self.update_manifest()

    def test_metadata_native_layout_and_existing_marketplace_source(self):
        entries, provenance = BUILDER.prepare(self.repo, target="claude")
        plugin = json.loads(entries["plugins/lstack/.claude-plugin/plugin.json"][0])
        market = json.loads(entries[".claude-plugin/marketplace.json"][0])
        self.assertEqual(plugin["name"], "lstack")
        self.assertEqual(plugin["version"], self.manifest["version"])
        self.assertEqual(plugin["license"], "MIT")
        self.assertEqual(set(plugin), {"name", "version", "description", "author", "license", "repository"})
        self.assertEqual(market["name"], "lstack-local")
        self.assertEqual(market["description"], self.manifest["claude"]["description"])
        source = market["plugins"][0]["source"]
        self.assertEqual(source, "./plugins/lstack")
        self.assertEqual(market["plugins"][0]["name"], plugin["name"])
        self.assertIn(source[2:] + "/.claude-plugin/plugin.json", entries)
        for name in ("parent", "child"):
            self.assertIn(source[2:] + "/skills/" + name + "/SKILL.md", entries)
        self.assertFalse(any("skills/parent/child/" in p for p in entries))
        self.assertFalse(any(p.startswith("plugins/lstack/" + component + "/")
                             for component in ("agents", "hooks", "commands") for p in entries))
        self.assertEqual(provenance["target"], "claude")
        for record in provenance["generated_metadata"]:
            self.assertEqual(record["sha256"], hashlib.sha256(entries[record["path"]][0]).hexdigest())

    def test_complete_member_bytes_modes_and_versions_match_bundle(self):
        bundle, original = BUILDER.prepare(self.repo)
        claude, adapted = BUILDER.prepare(self.repo, target="claude")
        self.assertEqual(original["skill_versions"], adapted["skill_versions"])
        self.assertEqual(original["files"], adapted["files"])
        for path, value in bundle.items():
            if path != "provenance.json":
                self.assertEqual(claude["plugins/lstack/" + path], value)
        self.assertEqual(claude["plugins/lstack/skills/parent/scripts/run.sh"][1], 0o755)

    def test_cli_build_extract_and_documented_paths(self):
        cmd = ["python3", str(self.repo / "scripts/build-lstack.py"), "--target", "claude"]
        subprocess.run(cmd + ["--check"], check=True, capture_output=True)
        self.assertFalse((self.repo / "dist").exists())
        completed = subprocess.run(cmd, check=True, capture_output=True, text=True)
        result = json.loads(completed.stdout)
        self.assertEqual(Path(result["output"]).resolve(), (self.repo / "dist/lstack-claude-0.1.0.zip").resolve())
        stage = Path(self.tmp.name) / "extracted"
        subprocess.run(["python3", "-m", "zipfile", "-e", result["output"], str(stage)], check=True)
        plugin_root = stage / result["plugin_root"]
        marketplace_root = stage / result["marketplace_root"]
        market = json.loads((marketplace_root / ".claude-plugin/marketplace.json").read_text())
        self.assertEqual((marketplace_root / market["plugins"][0]["source"]).resolve(), plugin_root.resolve())
        self.assertTrue((plugin_root / "skills/child/references/detail.md").is_file())
        self.assertTrue((plugin_root / "README.md").is_file())
        with zipfile.ZipFile(result["output"]) as archive:
            self.assertEqual(len(archive.namelist()), len(set(archive.namelist())))
            self.assertEqual(archive.getinfo(result["plugin_root"] + "/skills/parent/scripts/run.sh").external_attr >> 16, 0o100755)

    def test_reproducible_and_ignores_local_metadata_and_payload_edits(self):
        first, second = self.artifact("one.zip"), self.artifact("two.zip")
        BUILDER.build(self.repo, output=first, target="claude")
        self.put("packages/lstack/manifest.json", "uncommitted invalid metadata")
        self.put("skills/parent/SKILL.md", "local modified definition")
        self.put(".claude-plugin/plugin.json", "untracked runtime metadata")
        BUILDER.build(self.repo, output=second, target="claude")
        self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_adapter_metadata_cannot_add_runtime_components(self):
        for key, value in (("hooks", {}), ("marketplace_name", "../escape"), ("author", "invalid")):
            with self.subTest(key=key):
                valid = dict(self.manifest["claude"])
                self.manifest["claude"][key] = value
                self.update_manifest()
                with self.assertRaisesRegex(ValueError, "invalid Claude adapter"):
                    BUILDER.prepare(self.repo, target="claude")
                self.manifest["claude"] = valid

    def test_claude_target_retains_input_safety_and_no_partial_output(self):
        self.put("skills/parent/.env.example", "excluded")
        self.put("skills/parent/evals/fixture.txt", "excluded")
        self.commit()
        entries, _ = BUILDER.prepare(self.repo, target="claude")
        self.assertFalse(any(".env" in p or "/evals/" in p for p in entries))
        link = self.repo / "skills/parent/references/link"
        link.symlink_to("/etc/passwd")
        self.commit()
        with self.assertRaisesRegex(ValueError, "non-regular"):
            BUILDER.build(self.repo, output=self.artifact(), target="claude")
        self.assertFalse(self.artifact().exists())

    def test_claude_target_rejects_secrets_existing_and_source_outputs(self):
        out = self.artifact()
        out.write_bytes(b"preserve")
        with self.assertRaisesRegex(ValueError, "new .zip"):
            BUILDER.build(self.repo, output=out, target="claude")
        self.assertEqual(out.read_bytes(), b"preserve")
        with self.assertRaisesRegex(ValueError, "inside source"):
            BUILDER.build(self.repo, output=self.repo / "skills/output.zip", target="claude")
        self.put("skills/parent/references/key.txt", "-----BEGIN " + "PRIVATE KEY-----\nfixture")
        self.commit()
        with self.assertRaisesRegex(ValueError, "secret-like"):
            BUILDER.prepare(self.repo, target="claude")

    def test_unknown_target_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown package target"):
            BUILDER.prepare(self.repo, target="unsupported")

    def snapshot_catalog(self):
        """Commit current authoring inputs only in a disposable, independent Git repo."""
        repo = Path(self.tmp.name) / "catalog"
        repo.mkdir()
        paths = subprocess.check_output([
            "git", "-C", str(ROOT), "ls-files", "-z", "skills", "packages/lstack",
            "scripts/build-lstack.py", "README.md", "LICENSE"]).decode().split("\0")
        paths += [".claude-plugin/plugin.json", ".claude-plugin/marketplace.json"]
        for relative in filter(None, paths):
            source, destination = ROOT / relative, repo / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if source.is_symlink():
                destination.symlink_to(os.readlink(source))
            else:
                shutil.copy2(source, destination)
        for args in [("init", "-q"), ("config", "user.email", "packaging-test@example.invalid"),
                     ("config", "user.name", "Packaging test"), ("add", "-A"),
                     ("-c", "core.hooksPath=/dev/null", "commit", "-qm", "fixture snapshot")]:
            subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)
        return repo

    def test_real_catalog_parity_and_runbook_contract(self):
        repo = self.snapshot_catalog()
        bundle, original = BUILDER.prepare(repo)
        claude, adapted = BUILDER.prepare(repo, target="claude")
        self.assertEqual(len(adapted["skill_versions"]), 42)
        self.assertEqual(adapted["skill_versions"], original["skill_versions"])
        self.assertEqual(adapted["files"], original["files"])
        for path, value in bundle.items():
            if path.startswith("skills/"):
                self.assertEqual(claude["plugins/lstack/" + path], value)
        doc = bundle["README.md"][0].decode()
        for command in ("--target claude", "claude --plugin-dir", "claude plugin marketplace add",
                        "claude plugin install lstack@lstack", "claude plugin update",
                        "/lstack:code-review", "issue-pr-review", "issue-resolver", "dont-make-me-think"):
            self.assertIn(command, doc)
        self.assertIn("lstack-claude-" + adapted["package_version"], doc)
        self.assertEqual(adapted["package_version"], "0.4.0")
        plugin = json.loads(claude["plugins/lstack/.claude-plugin/plugin.json"][0])
        self.assertNotIn("skills", plugin)  # Root additive paths do not exist in flattened exports.
        market = json.loads(claude[".claude-plugin/marketplace.json"][0])
        self.assertEqual(market["name"], "lstack")
        cmd = ["python3", str(repo / "scripts/build-lstack.py")]
        for flags in [("--check",), ("--target", "claude", "--check"),
                      ("--target", "codex", "--check"), ("--check-plugin-metadata",)]:
            result = json.loads(subprocess.check_output(cmd + list(flags)))
            self.assertEqual((result["version"], result["skills"]), ("0.4.0", 42))
        first, second = self.artifact("catalog-one.zip"), self.artifact("catalog-two.zip")
        BUILDER.build(repo, output=first, target="claude")
        BUILDER.build(repo, output=second, target="claude")
        self.assertEqual(first.read_bytes(), second.read_bytes())
        codex, _ = BUILDER.prepare(repo, target="codex")
        codex_market = json.loads(codex[".agents/plugins/marketplace.json"][0])
        self.assertEqual(codex_market["name"], "lstack-local")
        for path, value in bundle.items():
            if path.startswith("skills/"):
                self.assertEqual(codex["plugins/lstack/" + path], value)
        root_doc = (repo / "README.md").read_text()
        for command in ("claude plugin marketplace add luongnv89/skills",
                        "--write-plugin-metadata", "--check-plugin-metadata", "lstack 0.4.0"):
            self.assertIn(command, root_doc)
        manifest = json.loads(bundle["manifest.json"][0])
        prerequisites = {p["name"]: p for p in manifest["external_skill_prerequisites"]}
        self.assertIn("dont-make-me-think", prerequisites["browse"]["used_by"])
        for name in ("issue-pr-review", "issue-resolver"):
            self.assertIn("issue-work-loop", prerequisites[name]["used_by"])

    def test_root_metadata_projection_and_additive_discovery_exactly_once(self):
        result = BUILDER.sync_plugin_metadata(ROOT)
        self.assertEqual((result["version"], result["skills"]), ("0.4.0", 42))
        plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_bytes())
        market = json.loads((ROOT / ".claude-plugin/marketplace.json").read_bytes())
        self.assertEqual(set(plugin), {"name", "version", "description", "author", "repository", "license", "skills"})
        self.assertEqual(plugin["skills"], ["./skills/diagram-generator/drawio-generator",
                                           "./skills/diagram-generator/excalidraw-generator"])
        self.assertEqual((market["name"], market["plugins"][0]["source"]), ("lstack", "./"))
        self.assertEqual(market["description"], plugin["description"])
        self.assertEqual(market["plugins"][0]["description"], plugin["description"])
        self.assertEqual((ROOT / market["plugins"][0]["source"]).resolve(), ROOT)
        self.assertTrue((ROOT / market["plugins"][0]["source"] / ".claude-plugin/plugin.json").is_file())
        paths = list((ROOT / "skills").glob("*/SKILL.md"))
        self.assertEqual(len(paths), 40)
        paths += [ROOT / source / "SKILL.md" for source in plugin["skills"]]
        self.assertEqual(len(paths), 42)
        self.assertEqual(len({p.resolve() for p in paths}), 42)
        manifest = json.loads((ROOT / BUILDER.MANIFEST).read_bytes())
        self.assertEqual({p.parent.resolve() for p in paths},
                         {(ROOT / m["source"]).resolve() for m in manifest["members"]})
        self.assertEqual(len(manifest["claude"]), 5)
        self.assertEqual(len(manifest["codex"]), 5)

    def test_native_modes_read_working_manifest_not_committed_archive(self):
        self.manifest["version"] = "0.4.0"
        self.manifest["claude"]["marketplace_name"] = "lstack"
        self.put(BUILDER.MANIFEST, json.dumps(self.manifest))  # Deliberately not committed.
        cmd = ["python3", str(self.repo / "scripts/build-lstack.py")]
        written = json.loads(subprocess.check_output(cmd + ["--write-plugin-metadata"]))
        checked = json.loads(subprocess.check_output(cmd + ["--check-plugin-metadata"]))
        self.assertEqual((written["version"], checked["inputs"]), ("0.4.0", "working-tree"))
        archived = json.loads(subprocess.check_output(cmd + ["--target", "claude", "--check"]))
        self.assertEqual(archived["version"], "0.1.0")
        plugin = json.loads((self.repo / ".claude-plugin/plugin.json").read_bytes())
        self.assertEqual(plugin["skills"], ["./skills/parent/child"])
        self.assertFalse((self.repo / "dist").exists())

    def test_native_check_rejects_stale_version_paths_and_components(self):
        mutations = [("plugin.json", "version", "9.9.9"),
                     ("plugin.json", "skills", ["./skills/missing"]),
                     ("plugin.json", "skills", ["./skills/parent", "./skills/parent/child"]),
                     ("plugin.json", "hooks", {}), ("plugin.json", "mcpServers", {}),
                     ("plugin.json", "agents", []), ("plugin.json", "commands", []),
                     ("marketplace.json", "name", "other"),
                     ("marketplace.json", "description", "stale description"),
                     ("marketplace.json", "plugins", [{"name": "lstack", "source": "./missing"}])]
        for filename, key, value in mutations:
            with self.subTest(filename=filename, key=key, value=value):
                BUILDER.sync_plugin_metadata(self.repo, write=True)
                path = self.repo / ".claude-plugin" / filename
                mutated = json.loads(path.read_bytes())
                mutated[key] = value
                path.write_bytes(BUILDER.json_bytes(mutated))
                with self.assertRaisesRegex(ValueError, "stale native plugin metadata"):
                    BUILDER.sync_plugin_metadata(self.repo)

    def test_native_check_rejects_manifest_version_and_render_drift(self):
        BUILDER.sync_plugin_metadata(self.repo, write=True)
        self.manifest["version"] = "0.4.0"
        self.put(BUILDER.MANIFEST, json.dumps(self.manifest))
        with self.assertRaisesRegex(ValueError, "stale native plugin metadata"):
            BUILDER.sync_plugin_metadata(self.repo)
        BUILDER.sync_plugin_metadata(self.repo, write=True)
        path = self.repo / ".claude-plugin/plugin.json"
        path.write_bytes(path.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "stale native plugin metadata"):
            BUILDER.sync_plugin_metadata(self.repo)

    def test_native_check_rejects_missing_malformed_and_unknown_metadata(self):
        with self.assertRaisesRegex(ValueError, "stale native plugin metadata"):
            BUILDER.sync_plugin_metadata(self.repo)
        self.put(".claude-plugin/plugin.json", "malformed JSON")
        self.put(".claude-plugin/marketplace.json", "{}")
        self.put(".claude-plugin/unknown.json", "preserve me")
        with self.assertRaisesRegex(ValueError, "stale native plugin metadata"):
            BUILDER.sync_plugin_metadata(self.repo)
        BUILDER.sync_plugin_metadata(self.repo, write=True)
        self.assertEqual((self.repo / ".claude-plugin/unknown.json").read_text(), "preserve me")

    def test_native_rejects_stale_missing_and_unsafe_canonical_members(self):
        valid = json.loads(json.dumps(self.manifest))
        for source in ("skills/gone/child", "./skills/parent/child", "skills/../child"):
            with self.subTest(source=source):
                self.manifest = json.loads(json.dumps(valid))
                self.manifest["members"][1]["source"] = source
                self.put(BUILDER.MANIFEST, json.dumps(self.manifest))
                with self.assertRaises(ValueError):
                    BUILDER.sync_plugin_metadata(self.repo, write=True)
                self.assertFalse((self.repo / ".claude-plugin").exists())
        self.put(BUILDER.MANIFEST, json.dumps(valid))
        (self.repo / "skills/parent/child/SKILL.md").unlink()
        with self.assertRaisesRegex(ValueError, "stale"):
            BUILDER.sync_plugin_metadata(self.repo, write=True)

    def test_native_rejects_symlinked_member_and_metadata_destinations(self):
        child = self.repo / "skills/parent/child/SKILL.md"
        content = child.read_bytes()
        child.unlink()
        child.symlink_to(self.put("outside.md", content))
        with self.assertRaisesRegex(ValueError, "non-regular canonical"):
            BUILDER.sync_plugin_metadata(self.repo, write=True)
        child.unlink()
        child.write_bytes(content)
        outside = Path(self.tmp.name) / "metadata"
        outside.mkdir()
        directory = self.repo / ".claude-plugin"
        directory.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "regular directory"):
            BUILDER.sync_plugin_metadata(self.repo, write=True)
        self.assertEqual(list(outside.iterdir()), [])
        directory.unlink()
        directory.mkdir()
        marker = self.put("preserve.txt", "untouched")
        (directory / "plugin.json").symlink_to(marker)
        with self.assertRaisesRegex(ValueError, "regular files"):
            BUILDER.sync_plugin_metadata(self.repo, write=True)
        self.assertEqual(marker.read_text(), "untouched")

    def test_native_adapter_cannot_inject_components(self):
        self.manifest["claude"]["hooks"] = {}
        self.put(BUILDER.MANIFEST, json.dumps(self.manifest))
        with self.assertRaisesRegex(ValueError, "invalid Claude adapter"):
            BUILDER.sync_plugin_metadata(self.repo, write=True)

    def test_native_cli_rejects_archive_options_and_mode_conflicts(self):
        cmd = ["python3", str(self.repo / "scripts/build-lstack.py")]
        for flags in [("--check-plugin-metadata", "--target", "claude"),
                      ("--write-plugin-metadata", "--revision", "other"),
                      ("--write-plugin-metadata", "--output", str(self.artifact())),
                      ("--check-plugin-metadata", "--check"),
                      ("--write-plugin-metadata", "--check-plugin-metadata")]:
            with self.subTest(flags=flags):
                result = subprocess.run(cmd + list(flags), capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.artifact().exists())

    def test_archive_safe_path_still_rejects_dot_root(self):
        # './' is marketplace metadata, never a valid archive entry filename.
        for path in ("./", "./skills/parent", "skills/../child", "../escape"):
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "unsafe package path"):
                BUILDER.safe_path(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
