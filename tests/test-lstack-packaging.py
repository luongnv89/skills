#!/usr/bin/env python3
"""Focused stdlib packaging checks; run directly, without installed agent skills."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("lstack_builder", ROOT / "scripts/build-lstack.py")
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "packaging-test@example.invalid")
        self.git("config", "user.name", "Packaging test")
        self.manifest = {"schema_version": 1, "name": "lstack", "version": "0.1.0", "members": [
            {"name": "parent", "source": "skills/parent"},
            {"name": "child", "source": "skills/parent/child"}]}
        self.put("packages/lstack/manifest.json", json.dumps(self.manifest))
        self.put("packages/lstack/README.md", "# lstack\nObtain and use documentation.\n")
        self.put("LICENSE", "MIT\n")
        self.put("scripts/build-lstack.py", (ROOT / "scripts/build-lstack.py").read_bytes())
        for name, source in [("parent", "skills/parent"), ("child", "skills/parent/child")]:
            self.put(source + "/SKILL.md", "---\nname: " + name + "\nmetadata:\n  version: 1.2.3\n---\n# " + name + "\n")
            self.put(source + "/references/detail.md", "resource bytes\r\n")
        self.put("skills/parent/scripts/run.sh", "#!/bin/sh\nprintf fixture\n")
        os.chmod(self.repo / "skills/parent/scripts/run.sh", 0o755)
        self.commit()

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], stderr=subprocess.PIPE)

    def put(self, path, data):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data.encode() if isinstance(data, str) else data)
        return target

    def commit(self):
        self.git("add", "-A")
        self.git("-c", "core.hooksPath=/dev/null", "commit", "-qm", "fixture")

    def update_manifest(self):
        self.put("packages/lstack/manifest.json", json.dumps(self.manifest))
        self.commit()

    def artifact(self, name="artifact.zip"):
        return Path(self.tmp.name) / name

    def test_package_identity_layout_versions_and_mode(self):
        out = self.artifact()
        result = BUILDER.build(self.repo, output=out)
        self.assertEqual((result["package"], result["version"], result["skills"]), ("lstack", "0.1.0", 2))
        with zipfile.ZipFile(out) as z:
            names = z.namelist()
            self.assertEqual(len(names), len(set(names)))
            self.assertIn("lstack-0.1.0/skills/child/SKILL.md", names)
            self.assertFalse(any("skills/parent/child/" in n for n in names))
            self.assertEqual(z.read("lstack-0.1.0/skills/parent/references/detail.md"), b"resource bytes\r\n")
            self.assertEqual(z.getinfo("lstack-0.1.0/skills/parent/scripts/run.sh").external_attr >> 16, 0o100755)
            p = json.loads(z.read("lstack-0.1.0/provenance.json"))
            self.assertEqual(p["source_commit"], self.git("rev-parse", "HEAD").decode().strip())
            self.assertEqual(p["skill_versions"], {"child": "1.2.3", "parent": "1.2.3"})

    def test_reproducible_despite_untracked_edits_and_mtime(self):
        first, second = self.artifact("first.zip"), self.artifact("second.zip")
        BUILDER.build(self.repo, output=first)
        self.put("skills/untracked/SKILL.md", "not catalog content")
        self.put("skills/parent/references/detail.md", "uncommitted edit")
        os.utime(self.repo / "skills/parent/SKILL.md", (1800000000, 1800000000))
        BUILDER.build(self.repo, output=second)
        self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_excludes_tracked_runtime_secret_and_development_files(self):
        paths = ["evals/files/input.md", "tests/test.py", "work-workspace/data.txt", ".env.example",
                 "credentials-local.json", "secrets.yaml", "key.pem", "id_ed25519.pub",
                 ".gitissue/state.json", ".claude/runtime.txt", "__pycache__/x.pyc", "SKILL.md.bak"]
        for path in paths:
            self.put("skills/parent/" + path, "not a resource")
        self.commit()
        entries, _ = BUILDER.prepare(self.repo)
        for path in paths:
            self.assertNotIn("skills/parent/" + path, entries)

    def test_manifest_requires_explicit_complete_catalog(self):
        self.put("skills/new/SKILL.md", "new skill")
        self.commit()
        with self.assertRaisesRegex(ValueError, "manifest/catalog mismatch"):
            BUILDER.prepare(self.repo)

    def test_stale_manifest_member_rejected(self):
        self.manifest["members"].append({"name": "gone", "source": "skills/gone"})
        self.update_manifest()
        with self.assertRaisesRegex(ValueError, "stale"):
            BUILDER.prepare(self.repo)

    def test_duplicate_member_rejected(self):
        self.manifest["members"].append(self.manifest["members"][0])
        self.update_manifest()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            BUILDER.prepare(self.repo)

    def test_destination_name_collision_rejected(self):
        self.manifest["members"][1] = {"name": "parent", "source": "skills/other/parent"}
        self.update_manifest()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            BUILDER.prepare(self.repo)

    def test_traversal_and_platform_paths_rejected(self):
        for path in ["/abs", "../escape", "skills/x/../parent", "skills//parent", "skills/./parent",
                     "C:/skills", "skills\\parent", "skills/x\nname", "skills/parent/"]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                BUILDER.safe_path(path)

    def test_symlink_rejected_without_artifact(self):
        (self.repo / "skills/parent/references/link").symlink_to("/etc/passwd")
        self.commit()
        with self.assertRaisesRegex(ValueError, "non-regular"):
            BUILDER.build(self.repo, output=self.artifact())
        self.assertFalse(self.artifact().exists())

    def test_submodule_rejected(self):
        sha = self.git("rev-parse", "HEAD").decode().strip()
        self.git("update-index", "--add", "--cacheinfo", "160000," + sha + ",skills/parent/vendor")
        self.git("-c", "core.hooksPath=/dev/null", "commit", "-qm", "submodule fixture")
        with self.assertRaisesRegex(ValueError, "non-regular"):
            BUILDER.prepare(self.repo)

    def test_private_key_content_rejected_without_leaking_value(self):
        self.put("skills/parent/references/data.txt", "-----BEGIN " + "PRIVATE KEY-----\nfixture")
        self.commit()
        with self.assertRaisesRegex(ValueError, "secret-like content in source") as error:
            BUILDER.build(self.repo, output=self.artifact())
        self.assertNotIn("PRIVATE KEY", str(error.exception))
        self.assertFalse(self.artifact().exists())

    def test_skill_name_and_version_checked(self):
        self.put("skills/parent/SKILL.md", "---\nname: wrong\nmetadata:\n  version: 1.2.3\n---\n")
        self.commit()
        with self.assertRaisesRegex(ValueError, "name/version mismatch"):
            BUILDER.prepare(self.repo)

    def test_check_is_read_only_and_existing_output_preserved(self):
        result = BUILDER.build(self.repo, check=True)
        self.assertEqual(result["skills"], 2)
        self.assertFalse((self.repo / "dist").exists())
        out = self.artifact()
        out.write_bytes(b"existing artifact")
        with self.assertRaisesRegex(ValueError, "new .zip"):
            BUILDER.build(self.repo, output=out)
        self.assertEqual(out.read_bytes(), b"existing artifact")

    def test_cli_obtain_build_check_and_extract(self):
        cmd = ["python3", str(self.repo / "scripts/build-lstack.py")]
        subprocess.run(cmd + ["--check"], check=True, capture_output=True)
        out = self.artifact()
        completed = subprocess.run(cmd + ["--output", str(out)], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(completed.stdout)["skills"], 2)
        staging = Path(self.tmp.name) / "extracted"
        subprocess.run(["python3", "-m", "zipfile", "-e", str(out), str(staging)], check=True)
        self.assertTrue((staging / "lstack-0.1.0/skills/child/SKILL.md").is_file())
        self.assertTrue((staging / "lstack-0.1.0/README.md").is_file())

    def test_cli_rejects_mismatched_builder(self):
        script = self.repo / "scripts/build-lstack.py"
        script.write_bytes(script.read_bytes() + b"\n# local modification\n")
        completed = subprocess.run(["python3", str(script), "--check"], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("builder differs", completed.stderr)

    def test_real_catalog_resource_parity_and_separate_discovery(self):
        entries, provenance = BUILDER.prepare(ROOT)
        manifest = json.loads(BUILDER.git(ROOT, "show", provenance["source_commit"] + ":packages/lstack/manifest.json"))
        self.assertEqual(len(manifest["members"]), 41)
        # Independent expected mapping: walking each manifest source and excluding other members.
        all_paths = BUILDER.git(ROOT, "ls-tree", "-r", "--name-only", "-z", provenance["source_commit"]).decode().split("\0")
        expected = set()
        for member in manifest["members"]:
            root = member["source"]
            for path in all_paths:
                if not path.startswith(root + "/"):
                    continue
                if any(other["source"] != root and other["source"].startswith(root + "/")
                       and path.startswith(other["source"] + "/") for other in manifest["members"]):
                    continue
                rel = path[len(root) + 1:]
                if BUILDER.excluded(rel):
                    continue
                destination = "skills/" + member["name"] + "/" + rel
                expected.add(destination)
                self.assertEqual(entries[destination][0], BUILDER.git(ROOT, "show", provenance["source_commit"] + ":" + path))
        self.assertEqual({p for p in entries if p.startswith("skills/")}, expected)
        definitions = {p for p in entries if p.endswith("/SKILL.md")}
        self.assertEqual(definitions, {"skills/" + m["name"] + "/SKILL.md" for m in manifest["members"]})
        for record in provenance["files"]:
            self.assertEqual(record["sha256"], hashlib.sha256(entries[record["path"]][0]).hexdigest())


if __name__ == "__main__":
    unittest.main(verbosity=2)
