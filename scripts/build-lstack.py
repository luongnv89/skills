#!/usr/bin/env python3
"""Build the lstack bundle or Claude Code plugin from one Git commit (stdlib only)."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import zipfile

MANIFEST = "packages/lstack/manifest.json"
BUILDER = "scripts/build-lstack.py"
NAME = re.compile(r"[a-z][a-z0-9-]{0,63}\Z")
VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+\Z")
# Deny known live-key formats, not ordinary placeholders or instructions.
SECRET = re.compile(
    rb"(?:sk-(?:proj-)?[A-Za-z0-9_-]{20,}|sk_live_[A-Za-z0-9]{20,}|"
    rb"(?:AKIA|ASIA)[0-9A-Z]{16}|gh[opsu]_[A-Za-z0-9]{30,}|"
    rb"github_pat_[A-Za-z0-9_]{40,}|xox[abprs]-[A-Za-z0-9-]{10,}|"
    rb"glpat-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{30,}|"
    rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)"
)
RUNTIME = {".git", ".gitissue", ".claude", ".agents", ".pi", ".asm-improver",
           "node_modules", "dist", "build", "__pycache__", ".venv", "venv"}


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.PIPE)


def safe_path(value):
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("invalid package path")
    p = PurePosixPath(value)
    if p.is_absolute() or str(p) != value or any(
        part in {".", ".."} or ":" in part or any(ord(c) < 32 or ord(c) == 127 for c in part)
        for part in value.split("/")
    ):
        raise ValueError("unsafe package path: " + repr(value))
    return p


def excluded(relative):
    p = safe_path(relative)
    parts = p.parts
    if parts[0] in {"evals", "tests"}:
        return True
    return any(
        part in RUNTIME or part.endswith("-workspace") or part.startswith(".env")
        or part.lower().startswith(("credentials", "secrets"))
        or part in {".DS_Store", "Thumbs.db", "scheduled_tasks.lock", "SKILL.md.bak"}
        or part.startswith("id_rsa") or part.startswith("id_ed25519")
        or part.lower().endswith((".pem", ".key", ".p12", ".pfx", ".cer", ".pyc", ".swp", ".tmp", "~"))
        for part in parts
    )


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode()


def prepare(repo, revision="HEAD", target="bundle"):
    """Return validated archive entries and provenance; never read working-tree payloads."""
    if target not in {"bundle", "claude"}:
        raise ValueError("unknown package target: " + str(target))
    sha = git(repo, "rev-parse", "--verify", revision + "^{commit}").decode().strip()
    tree = {}
    for record in git(repo, "ls-tree", "-rz", "--full-tree", sha).split(b"\0"):
        if not record:
            continue
        header, raw_path = record.split(b"\t", 1)
        mode, kind, oid = header.decode().split()
        path = raw_path.decode("utf-8")
        tree[path] = (mode, kind, oid)

    def blob(path):
        safe_path(path)
        if path not in tree or tree[path][0] not in {"100644", "100755"} or tree[path][1] != "blob":
            raise ValueError("missing or non-regular source: " + path)
        data = git(repo, "cat-file", "blob", tree[path][2])
        if SECRET.search(data):
            raise ValueError("secret-like content in source: " + path)
        return data

    manifest_bytes = blob(MANIFEST)
    manifest = json.loads(manifest_bytes)
    if (not isinstance(manifest, dict) or manifest.get("schema_version") != 1
            or manifest.get("name") != "lstack" or not isinstance(manifest.get("version"), str)
            or not VERSION.fullmatch(manifest["version"])):
        raise ValueError("invalid lstack manifest identity/schema/version")
    members = manifest.get("members")
    if not isinstance(members, list) or not members:
        raise ValueError("manifest members must be a non-empty list")
    roots, names = {}, set()
    for member in members:
        if not isinstance(member, dict) or set(member) != {"name", "source"}:
            raise ValueError("member must contain name and source only")
        name, source = member["name"], member["source"]
        if not isinstance(name, str) or not NAME.fullmatch(name):
            raise ValueError("invalid member name")
        path = safe_path(source)
        if len(path.parts) < 2 or path.parts[0] != "skills" or path.name != name:
            raise ValueError("member source/name mismatch: " + source)
        if source in roots or name in names:
            raise ValueError("duplicate member source/name")
        roots[source] = name
        names.add(name)
    catalog = {str(PurePosixPath(p).parent) for p in tree
               if p.startswith("skills/") and p.endswith("/SKILL.md")}
    if set(roots) != catalog:
        raise ValueError("manifest/catalog mismatch; missing=" + repr(sorted(catalog - set(roots)))
                         + "; stale=" + repr(sorted(set(roots) - catalog)))
    # Deepest member owns its subtree; children never occur inside umbrella copies.
    owners = sorted(roots, key=lambda p: (-len(PurePosixPath(p).parts), p))
    entries, files, versions = {}, [], {}
    for path in sorted(tree):
        owner = next((root for root in owners if path.startswith(root + "/")), None)
        if owner is None:
            continue
        relative = path[len(owner) + 1:]
        if excluded(relative):
            continue
        data = blob(path)
        destination = "skills/" + roots[owner] + "/" + relative
        safe_path(destination)
        if destination in entries:
            raise ValueError("duplicate archive destination: " + destination)
        mode = 0o755 if tree[path][0] == "100755" else 0o644
        entries[destination] = (data, mode)
        files.append({"source": path, "path": destination, "sha256": hashlib.sha256(data).hexdigest(),
                      "mode": format(mode, "04o")})
        if relative == "SKILL.md":
            text = data.decode("utf-8")
            frontmatter = text.split("---", 2)
            if len(frontmatter) != 3 or frontmatter[0].strip():
                raise ValueError("missing skill frontmatter: " + path)
            declared = re.search(r"^name: *[\"']?([a-z][a-z0-9-]*)[\"']? *$", frontmatter[1], re.M)
            metadata = re.search(r"^metadata: *\n((?:[ \t]+[^\n]*\n)*)", frontmatter[1], re.M)
            version = re.search(r"^[ \t]+version: *[\"']?([0-9]+\.[0-9]+\.[0-9]+)[\"']? *$",
                                metadata[1] if metadata else "", re.M)
            if not declared or declared[1] != roots[owner] or not version:
                raise ValueError("skill name/version mismatch: " + path)
            versions[roots[owner]] = version[1]
    if set(versions) != names:
        raise ValueError("missing packaged skill definitions")
    for source, destination in [(MANIFEST, "manifest.json"),
                                ("packages/lstack/README.md", "README.md"), ("LICENSE", "LICENSE")]:
        entries[destination] = (blob(source), 0o644)
    provenance = {"schema_version": 1, "package": "lstack", "package_version": manifest["version"],
                  "source_commit": sha, "builder_sha256": hashlib.sha256(blob(BUILDER)).hexdigest(),
                  "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
                  "skill_versions": versions, "files": files}
    if target == "claude":
        adapter = manifest.get("claude")
        fields = {"description", "author", "repository", "license", "marketplace_name"}
        if (not isinstance(adapter, dict) or set(adapter) != fields
                or not isinstance(adapter["description"], str) or not adapter["description"].strip()
                or not isinstance(adapter["author"], dict) or set(adapter["author"]) != {"name"}
                or not isinstance(adapter["author"]["name"], str) or not adapter["author"]["name"].strip()
                or not isinstance(adapter["repository"], str) or not adapter["repository"].startswith("https://")
                or adapter["license"] != "MIT"
                or not isinstance(adapter["marketplace_name"], str)
                or not NAME.fullmatch(adapter["marketplace_name"])):
            raise ValueError("invalid Claude adapter metadata")
        plugin = {key: value for key, value in adapter.items() if key != "marketplace_name"}
        plugin.update({"name": manifest["name"], "version": manifest["version"]})
        marketplace = {"name": adapter["marketplace_name"], "owner": adapter["author"],
                       "plugins": [{"name": manifest["name"], "source": "./plugins/lstack",
                                    "description": adapter["description"]}]}
        generated = {"plugins/lstack/.claude-plugin/plugin.json": json_bytes(plugin),
                     ".claude-plugin/marketplace.json": json_bytes(marketplace)}
        # A marketplace container surrounds the native plugin; payload bytes/modes never change.
        entries = {"plugins/lstack/" + path: value for path, value in entries.items()}
        entries.update({path: (data, 0o644) for path, data in generated.items()})
        provenance["target"] = target
        provenance["generated_metadata"] = [
            {"path": path, "sha256": hashlib.sha256(data).hexdigest()}
            for path, data in sorted(generated.items())]
        provenance_path = "plugins/lstack/provenance.json"
    else:
        provenance_path = "provenance.json"
    entries[provenance_path] = (json_bytes(provenance), 0o644)
    for path in entries:
        safe_path(path)
    return entries, provenance


def build(repo, revision="HEAD", output=None, check=False, target="bundle"):
    entries, provenance = prepare(repo, revision, target)
    prefix = "lstack-" + ("claude-" if target == "claude" else "") + provenance["package_version"]
    result = {"package": "lstack", "version": provenance["package_version"],
              "source_commit": provenance["source_commit"],
              "skills": len(provenance["skill_versions"]), "files": len(entries)}
    if target == "claude":
        result.update({"target": target, "marketplace_root": prefix,
                       "plugin_root": prefix + "/plugins/lstack"})
    if check:
        return result
    output = Path(output) if output else Path(repo) / "dist" / (prefix + ".zip")
    output = output.absolute()
    # Only a new .zip file; never overwrite source, old artifacts, or symlinks.
    if output.suffix != ".zip" or output.exists() or output.is_symlink():
        raise ValueError("output must be a new .zip file: " + str(output))
    resolved = output.resolve()
    repo_root = Path(repo).resolve()
    if any(resolved.is_relative_to(repo_root / root) for root in ("skills", "packages", "scripts", ".git")):
        raise ValueError("output cannot be inside source/runtime directories")
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".lstack-", suffix=".tmp", dir=output.parent)
    try:
        with os.fdopen(fd, "wb") as stream, zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED) as archive:
            for path, (data, mode) in sorted(entries.items()):
                info = zipfile.ZipInfo(prefix + "/" + path, date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = (0o100000 | mode) << 16
                archive.writestr(info, data)
        # Exclusive publication: a concurrent build must not replace another artifact.
        os.link(temp, output)
    finally:
        os.unlink(temp)
    result.update({"output": str(output), "sha256": hashlib.sha256(output.read_bytes()).hexdigest()})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", default="HEAD", help="immutable source commit or Git ref (default HEAD)")
    parser.add_argument("--target", choices=("bundle", "claude"), default="bundle",
                        help="platform-neutral bundle (default) or Claude Code plugin/local marketplace")
    parser.add_argument("--output", type=Path, help="new ZIP path (default dist/lstack[-claude]-VERSION.zip)")
    parser.add_argument("--check", action="store_true", help="validate committed inputs without writing an archive")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parent.parent
    try:
        # Use the builder committed at the selected revision, not mismatched local code.
        sha = git(repo, "rev-parse", "--verify", args.revision + "^{commit}").decode().strip()
        if git(repo, "show", sha + ":" + BUILDER) != Path(__file__).read_bytes():
            raise ValueError("builder differs from selected revision; check out that revision first")
        print(json.dumps(build(repo, sha, args.output, args.check, args.target), sort_keys=True))
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print("lstack: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
