#!/usr/bin/env python3
"""Claude adapter regression checks, using stdlib and isolated Git fixtures only."""

import hashlib
import importlib.util
import json
from pathlib import Path
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

    def test_real_catalog_parity_and_runbook_contract(self):
        bundle, original = BUILDER.prepare(ROOT)
        claude, adapted = BUILDER.prepare(ROOT, target="claude")
        self.assertEqual(len(adapted["skill_versions"]), 41)
        self.assertEqual(adapted["skill_versions"], original["skill_versions"])
        self.assertEqual(adapted["files"], original["files"])
        for path, value in bundle.items():
            if path.startswith("skills/"):
                self.assertEqual(claude["plugins/lstack/" + path], value)
        doc = bundle["README.md"][0].decode()
        for command in ("--target claude", "claude --plugin-dir", "claude plugin marketplace add",
                        "claude plugin install lstack@lstack-local", "claude plugin update",
                        "/lstack:code-review", "issue-pr-review", "issue-resolver", "dont-make-me-think"):
            self.assertIn(command, doc)
        self.assertIn("lstack-claude-" + adapted["package_version"], doc)
        manifest = json.loads(bundle["manifest.json"][0])
        prerequisites = {p["name"]: p for p in manifest["external_skill_prerequisites"]}
        self.assertIn("dont-make-me-think", prerequisites["browse"]["used_by"])
        for name in ("issue-pr-review", "issue-resolver"):
            self.assertIn("issue-work-loop", prerequisites[name]["used_by"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
