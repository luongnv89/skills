#!/usr/bin/env python3
"""Portable Codex adapter checks; stdlib, temporary Git fixtures, no installed agents."""

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


class CodexPackagingTests(unittest.TestCase):
    git = BASE.PackagingTests.git
    put = BASE.PackagingTests.put
    commit = BASE.PackagingTests.commit
    update_manifest = BASE.PackagingTests.update_manifest
    artifact = BASE.PackagingTests.artifact

    def setUp(self):
        BASE.PackagingTests.setUp(self)
        self.manifest["codex"] = {
            "description": "Fixture skills", "author": {"name": "Fixture author"},
            "repository": "https://example.invalid/fixture", "license": "MIT",
            "marketplace_name": "lstack-local"}
        self.update_manifest()

    def test_portable_schema_identity_and_skills_only_layout(self):
        entries, provenance = BUILDER.prepare(self.repo, target="codex")
        plugin = json.loads(entries["plugins/lstack/plugin.json"][0])
        # Closed field set/types from the official Agent Plugins 1.0.0 schema;
        # this is a focused contract check, not a general JSON Schema validator.
        self.assertEqual(set(plugin), {"$schema", "name", "version", "description", "author", "repository", "license"})
        self.assertEqual(plugin["$schema"], "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json")
        self.assertEqual(plugin["name"], "lstack")
        self.assertEqual(plugin["version"], self.manifest["version"])
        for key in ("version", "description", "repository", "license"):
            self.assertIsInstance(plugin[key], str)
        self.assertEqual(plugin["author"], {"name": "Fixture author"})
        for forbidden in (".codex-plugin", ".claude-plugin", "hooks", "commands", "agents"):
            self.assertFalse(any(p.startswith("plugins/lstack/" + forbidden + "/") for p in entries))
        self.assertNotIn("plugins/lstack/mcp.json", entries)
        for name in ("parent", "child"):
            self.assertIn("plugins/lstack/skills/" + name + "/SKILL.md", entries)
        self.assertFalse(any("skills/parent/child/" in p for p in entries))
        self.assertEqual(provenance["target"], "codex")
        self.assertEqual({r["path"] for r in provenance["generated_metadata"]},
                         {"plugins/lstack/plugin.json", ".agents/plugins/marketplace.json"})
        for record in provenance["generated_metadata"]:
            self.assertEqual(record["sha256"], hashlib.sha256(entries[record["path"]][0]).hexdigest())

    def test_marketplace_policy_and_contained_resolvable_source(self):
        entries, _ = BUILDER.prepare(self.repo, target="codex")
        market = json.loads(entries[".agents/plugins/marketplace.json"][0])
        self.assertEqual(set(market), {"name", "interface", "plugins"})
        self.assertEqual(market["name"], "lstack-local")
        self.assertEqual(market["interface"], {"displayName": "lstack local"})
        self.assertEqual(len(market["plugins"]), 1)
        entry = market["plugins"][0]
        self.assertEqual(entry, {"name": "lstack", "source": {"source": "local", "path": "./plugins/lstack"},
                                 "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                                 "category": "Productivity"})
        source = entry["source"]["path"]
        BUILDER.safe_path(source[2:])
        self.assertIn(source[2:] + "/plugin.json", entries)

    def test_complete_member_bytes_modes_versions_match_bundle(self):
        bundle, original = BUILDER.prepare(self.repo)
        codex, adapted = BUILDER.prepare(self.repo, target="codex")
        self.assertEqual(original["files"], adapted["files"])
        self.assertEqual(original["skill_versions"], adapted["skill_versions"])
        for path, value in bundle.items():
            if path != "provenance.json":
                self.assertEqual(codex["plugins/lstack/" + path], value)
        self.assertEqual(codex["plugins/lstack/skills/parent/scripts/run.sh"][1], 0o755)

    def test_cli_check_build_extract_relocated_marketplace_and_archive_modes(self):
        cmd = ["python3", str(self.repo / "scripts/build-lstack.py"), "--target", "codex"]
        subprocess.run(cmd + ["--check"], check=True, capture_output=True)
        self.assertFalse((self.repo / "dist").exists())
        result = json.loads(subprocess.check_output(cmd, text=True))
        self.assertEqual(Path(result["output"]).resolve(), (self.repo / "dist/lstack-codex-0.1.0.zip").resolve())
        self.assertEqual(result["target"], "codex")
        stage = Path(self.tmp.name) / "relocated marketplace with spaces"
        subprocess.run(["python3", "-m", "zipfile", "-e", result["output"], str(stage)], check=True)
        root = stage / result["marketplace_root"]
        market = json.loads((root / ".agents/plugins/marketplace.json").read_text())
        plugin = root / market["plugins"][0]["source"]["path"]
        self.assertEqual(plugin.resolve(), (stage / result["plugin_root"]).resolve())
        self.assertTrue(plugin.resolve().is_relative_to(root.resolve()))
        self.assertTrue((plugin / "plugin.json").is_file())
        self.assertTrue((plugin / "skills/child/references/detail.md").is_file())
        with zipfile.ZipFile(result["output"]) as archive:
            self.assertEqual(len(archive.namelist()), len(set(archive.namelist())))
            self.assertEqual(archive.namelist(), sorted(archive.namelist()))
            for info in archive.infolist():
                BUILDER.safe_path(info.filename)
                self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
            self.assertEqual(archive.getinfo(result["plugin_root"] + "/skills/parent/scripts/run.sh").external_attr >> 16, 0o100755)

    def test_deterministic_committed_metadata_and_payload_only(self):
        first, second = self.artifact("first.zip"), self.artifact("second.zip")
        BUILDER.build(self.repo, output=first, target="codex")
        self.put("packages/lstack/manifest.json", "local invalid metadata")
        self.put("skills/parent/SKILL.md", "uncommitted skill change")
        self.put(".agents/plugins/marketplace.json", "untracked runtime metadata")
        BUILDER.build(self.repo, output=second, target="codex")
        self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_rejects_invalid_adapter_and_runtime_component_injection(self):
        for key, value in (("hooks", {}), ("marketplace_name", "../escape"),
                           ("description", ""), ("author", "invalid"), ("repository", "file:///tmp")):
            with self.subTest(key=key):
                valid = dict(self.manifest["codex"])
                self.manifest["codex"][key] = value
                self.update_manifest()
                with self.assertRaisesRegex(ValueError, "invalid Codex adapter"):
                    BUILDER.prepare(self.repo, target="codex")
                self.manifest["codex"] = valid

    def test_safety_excludes_symlinks_and_no_partial_artifact(self):
        for path in (".env.example", "credentials-local.json", "evals/input.md", ".agents/runtime.txt"):
            self.put("skills/parent/" + path, "excluded")
        self.commit()
        entries, _ = BUILDER.prepare(self.repo, target="codex")
        self.assertFalse(any(".env" in p or "credentials" in p or "/evals/" in p or p.endswith("runtime.txt") for p in entries))
        (self.repo / "skills/parent/references/link").symlink_to("/etc/passwd")
        self.commit()
        with self.assertRaisesRegex(ValueError, "non-regular"):
            BUILDER.build(self.repo, output=self.artifact(), target="codex")
        self.assertFalse(self.artifact().exists())

    def test_rejects_secret_content_existing_and_source_outputs(self):
        out = self.artifact()
        out.write_bytes(b"preserve")
        with self.assertRaisesRegex(ValueError, "new .zip"):
            BUILDER.build(self.repo, output=out, target="codex")
        self.assertEqual(out.read_bytes(), b"preserve")
        with self.assertRaisesRegex(ValueError, "inside source"):
            BUILDER.build(self.repo, output=self.repo / "skills/output.zip", target="codex")
        self.put("skills/parent/references/data.txt", "-----BEGIN " + "PRIVATE KEY-----\nfixture")
        self.commit()
        with self.assertRaisesRegex(ValueError, "secret-like"):
            BUILDER.prepare(self.repo, target="codex")

    def test_real_catalog_parity_and_runbook_contract(self):
        bundle, original = BUILDER.prepare(ROOT)
        codex, adapted = BUILDER.prepare(ROOT, target="codex")
        self.assertEqual(len(adapted["skill_versions"]), 41)
        self.assertEqual(len(adapted["files"]), 396)
        self.assertEqual(original["skill_versions"], adapted["skill_versions"])
        self.assertEqual(original["files"], adapted["files"])
        for path, value in bundle.items():
            if path.startswith("skills/"):
                self.assertEqual(codex["plugins/lstack/" + path], value)
        doc = bundle["README.md"][0].decode()
        for text in ("--target codex", "codex plugin marketplace add", "/plugins", "new session",
                     "IDE extension", "not a hosted Codex marketplace", "CODEX_HOME",
                     "lstack-codex-" + adapted["package_version"]):
            self.assertIn(text, doc)


if __name__ == "__main__":
    unittest.main(verbosity=2)
