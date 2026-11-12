#!/usr/bin/env python3
"""Build the lstack directory edition: the members that pass the Claude plugin directory's
community policy, as a plain folder for the `directory` branch (stdlib only).

The directory accepts only Markdown, text, JSON, YAML and PNG/JPEG/GIF/WebP/ICO images
from organizations it hasn't verified, refuses `#!` files and package-manager settings,
and allows only standard frontmatter keys. This script selects members by those rules,
moves `effort` and `dependencies` under `metadata`, and checks the built tree again.
"""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location("lstack_builder", ROOT / "scripts/build-lstack.py")
BUILDER = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(BUILDER)

SELF = "scripts/build-lstack-directory.py"
PLUGIN = "skills"  # same plugin path as main, so the listing keeps its folder
FULL_INSTALL = "claude plugin marketplace add luongnv89/skills"
TEXT_EXT = {".md", ".markdown", ".txt", ".json", ".yaml", ".yml"}
TEXT_NAMES = {"LICENSE", "README", ".gitignore"}
IMAGE_MAGIC = {".png": (b"\x89PNG\r\n\x1a\n",), ".jpg": (b"\xff\xd8\xff",), ".jpeg": (b"\xff\xd8\xff",),
               ".gif": (b"GIF87a", b"GIF89a"), ".ico": (b"\x00\x00\x01\x00",), ".webp": (b"RIFF",)}
PACKAGE_CONFIG = {".npmrc", ".yarnrc", ".yarnrc.yml", ".pnpmrc", "pnpm-workspace.yaml", "bunfig.toml",
                  "uv.toml", "pip.conf", "pip.ini", ".pypirc", "pyproject.toml", "requirements.txt",
                  "pipfile", "pipfile.lock", "poetry.lock", "package.json", "package-lock.json",
                  "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml", "bun.lock", "bun.lockb",
                  ".tool-versions", "deno.json", "deno.jsonc", "cargo.toml", "go.mod", "gemfile"}
SYSTEM_FILES = {".ds_store", "thumbs.db", "desktop.ini", "__macosx"}
SKILL_KEYS = ("name", "description", "license", "compatibility", "metadata")
MOVED_KEYS = ("effort", "dependencies")
MAX_FILE = 256 * 1024
MAX_FILES = 512
PLAIN = re.compile(r"[A-Za-z0-9_./@+-][^#]*\Z")


def file_problem(path, data):
    """Return why the directory would refuse this file, or None."""
    name = PurePosixPath(path).name
    lower = name.lower()
    suffix = PurePosixPath(lower).suffix
    if lower in SYSTEM_FILES:
        return "operating-system file"
    if lower in PACKAGE_CONFIG:
        return "package-manager configuration"
    if len(data) >= MAX_FILE:
        return "file of 256 KiB or more"
    if suffix in IMAGE_MAGIC:
        ok = any(data.startswith(m) for m in IMAGE_MAGIC[suffix])
        if suffix == ".webp":
            ok = ok and data[8:12] == b"WEBP"
        return None if ok else "image whose bytes are not a " + suffix[1:].upper()
    if suffix not in TEXT_EXT and name not in TEXT_NAMES and lower not in {"license.md", "license.txt"}:
        return "type outside Markdown, text, JSON, YAML and images (" + (suffix or "no extension") + ")"
    if data.lstrip(b"\xef\xbb\xbf").startswith(b"#!"):
        return "starts with #!"
    if b"\0" in data:
        return "holds a NUL byte"
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return "not UTF-8 text"
    return None


def split_frontmatter(text, path):
    if not text.startswith("---\n"):
        raise ValueError("no frontmatter: " + path)
    end = text.find("\n---\n", 3)
    if end < 0:
        raise ValueError("unterminated frontmatter: " + path)
    return text[4:end + 1], text[end + 5:]


def scalar(raw, path):
    """Unquote one YAML scalar written in the forms this repository uses; refuse others."""
    raw = raw.strip()
    if raw.startswith('"'):
        return json.loads(raw)
    if raw.startswith("'") and raw.endswith("'") and len(raw) >= 2:
        return raw[1:-1].replace("''", "'")
    if raw and PLAIN.fullmatch(raw) and ": " not in raw:
        return raw
    raise ValueError("unsupported frontmatter value " + repr(raw) + " in " + path)


def parse_frontmatter(block, path):
    """Parse top-level `key: value`, a `metadata` map and a `dependencies` list."""
    top, metadata, deps, current = {}, {}, [], None
    for line in block.splitlines():
        if not line.strip():
            continue
        if not line.startswith(" "):
            key, sep, value = line.partition(":")
            if not sep or not re.fullmatch(r"[a-z][a-z0-9_-]*", key) or key in top:
                raise ValueError("unsupported frontmatter line " + repr(line) + " in " + path)
            top[key] = value.strip()
            current = key if not value.strip() else None
            if key == "dependencies" and value.strip().startswith("["):
                inner = value.strip()
                if not inner.endswith("]"):
                    raise ValueError("unsupported dependencies list in " + path)
                deps.extend(scalar(v, path) for v in inner[1:-1].split(",") if v.strip())
            continue
        item = re.fullmatch(r"  - (.+)", line)
        pair = re.fullmatch(r"  ([A-Za-z][A-Za-z0-9_-]*): (.+)", line)
        if current == "dependencies" and item:
            deps.append(scalar(item[1], path))
        elif current == "metadata" and pair and pair[1] not in metadata:
            metadata[pair[1]] = scalar(pair[2], path)
        else:
            raise ValueError("unsupported frontmatter line " + repr(line) + " in " + path)
    return top, metadata, deps


def standard_skill_md(data, path):
    """Rewrite SKILL.md frontmatter to the allowed keys; keep the body byte for byte."""
    block, body = split_frontmatter(data.decode("utf-8"), path)
    top, metadata, deps = parse_frontmatter(block, path)
    unknown = set(top) - set(SKILL_KEYS) - set(MOVED_KEYS)
    if unknown:
        raise ValueError("frontmatter keys outside the allowed list in " + path + ": " + ", ".join(sorted(unknown)))
    if "effort" in top:
        metadata.setdefault("effort", scalar(top["effort"], path))
    if deps:
        metadata.setdefault("dependencies", ", ".join(deps))
    lines = ["---"]
    for key in SKILL_KEYS[:-1]:
        if key in top:
            lines.append(key + ": " + top[key])
    if metadata:
        lines.append("metadata:")
        lines.extend("  " + k + ": " + json.dumps(v, ensure_ascii=False) for k, v in metadata.items())
    lines.append("---")
    return ("\n".join(lines) + "\n" + body).encode("utf-8")


def check_tree(root):
    """Re-check a built edition folder against the file and frontmatter rules."""
    root = Path(root)
    plugin = root / PLUGIN
    problems, files, notes = [], [], []
    for current, dirs, names in os.walk(plugin):
        dirs[:] = [d for d in dirs if d != ".git"]
        for entry in [*dirs, *names]:
            p = Path(current) / entry
            rel = p.relative_to(plugin).as_posix()
            if p.is_symlink():
                problems.append(rel + ": symlink")
            elif entry.lower() in SYSTEM_FILES:
                problems.append(rel + ": operating-system file")
        for name in names:
            p = Path(current) / name
            if p.is_symlink() or not p.is_file():
                continue
            rel = p.relative_to(plugin).as_posix()
            files.append(rel)
            data = p.read_bytes()
            problem = file_problem(rel, data)
            if problem:
                problems.append(rel + ": " + problem)
            elif name.endswith(".md") and name != "SKILL.md" and data.startswith(b"---\n"):
                keys = re.findall(r"^([A-Za-z][\w-]*):", data.decode().split("\n---\n", 1)[0], re.M)
                if set(keys) - {"name", "description"}:
                    notes.append(rel + ": resource frontmatter keys " + ", ".join(keys))
            elif name == "SKILL.md":
                try:
                    top, metadata, deps = parse_frontmatter(split_frontmatter(data.decode(), rel)[0], rel)
                except ValueError as exc:
                    problems.append(str(exc))
                    continue
                extra = sorted(set(top) - set(SKILL_KEYS))
                if extra or deps:
                    problems.append(rel + ": frontmatter keys outside the allowed list: " + ", ".join(extra))
                for key, value in metadata.items():
                    raw = re.search(r"^  " + re.escape(key) + r": (.*)$", data.decode(), re.M)[1]
                    if not raw.startswith('"'):
                        problems.append(rel + ": metadata." + key + " is not a quoted string")
    if len(files) > MAX_FILES:
        problems.append("plugin folder has %d files (limit %d)" % (len(files), MAX_FILES))
    if not (plugin / ".claude-plugin/plugin.json").is_file():
        problems.append(".claude-plugin/plugin.json missing")
    return problems, len(files), notes


def readme_words(text):
    return len(re.sub(r"```.*?```", " ", text, flags=re.S).split())


def first_sentence(description):
    text = description.strip()
    cut = re.search(r"(?<=[.!?])\s", text)
    return text[:cut.start()] if cut else text


def prepare(repo, revision="HEAD"):
    entries, provenance = BUILDER.prepare(repo, revision, "bundle")
    sha = provenance["source_commit"]
    manifest = json.loads(entries["manifest.json"][0])
    members = {}
    for path, (data, _mode) in entries.items():
        parts = PurePosixPath(path).parts
        if parts[0] == "skills" and len(parts) > 2:
            members.setdefault(parts[1], {})["/".join(parts[2:])] = data
    excluded = {}
    for name, files in sorted(members.items()):
        bad = [rel + " (" + p + ")" for rel, data in sorted(files.items()) if (p := file_problem(rel, data))]
        if bad:
            excluded[name] = "ships files the directory refuses: " + "; ".join(bad)
    deps = {name: parse_frontmatter(split_frontmatter(files["SKILL.md"].decode(), name)[0], name)[2]
            for name, files in members.items()}
    changed = True
    while changed:  # a skill whose dependency is left out would fetch it at run time
        changed = False
        for name in sorted(members):
            if name in excluded:
                continue
            missing = [d for d in deps[name] if d not in members or d in excluded]
            if missing:
                excluded[name] = "depends on skills outside this edition: " + ", ".join(missing)
                changed = True
    included = sorted(set(members) - set(excluded))
    if not included:
        raise ValueError("no member passes the directory rules")
    out = {}
    descriptions = {}
    for name in included:
        for rel, data in members[name].items():
            if rel == "SKILL.md":
                data = standard_skill_md(data, name + "/SKILL.md")
                top = parse_frontmatter(split_frontmatter(data.decode(), name)[0], name)[0]
                descriptions[name] = scalar(top["description"], name)
            out[PLUGIN + "/" + name + "/" + rel] = data
    plugin = BUILDER.plugin_metadata(manifest, "claude")
    plugin["description"] = ("%d first-party Agent Skills for Claude Code, Markdown instructions only; "
                             "the full %d-skill lstack installs from the luongnv89/skills marketplace."
                             % (len(included), len(members)))
    out[PLUGIN + "/.claude-plugin/plugin.json"] = BUILDER.json_bytes(plugin)
    if "icon" in plugin:
        out[PLUGIN + "/" + plugin["icon"][2:]] = BUILDER.git(
            repo, "show", sha + ":" + BUILDER.PLUGIN_ROOT + "/" + plugin["icon"][2:])
    license_text = entries["LICENSE"][0]
    out[PLUGIN + "/LICENSE"] = license_text
    out["LICENSE"] = license_text
    rows = "\n".join("- **%s**: %s" % (n, first_sentence(descriptions[n])) for n in included)
    left_out = ", ".join(sorted(excluded))
    readme = f"""# lstack (directory edition)

lstack {manifest['version']} for the Claude plugin directory: {len(included)} first-party Agent
Skills for everyday engineering and product work. Every skill here is plain Markdown: a
`SKILL.md` playbook with optional reference files. The plugin has no scripts, hooks, MCP
servers, native agents or binaries, and installing it installs no packages.

The skills use tools and accounts you already have. Some tell Claude to run your local
`git`, `gh`, npm or other command-line tools, to push or publish when you ask for it
(`auto-push`, `ship`), or to look things up on the web (for example the domain, trademark
and package-registry checks in `brand-name-checker`). Read a skill's `SKILL.md` to see
exactly what it does before you run it.

The full lstack ({len(members)} skills, including the ones that ship helper scripts) installs
from this project's own marketplace:

```bash
{FULL_INSTALL}
claude plugin install lstack@lstack --scope user
```

Source: [github.com/luongnv89/skills](https://github.com/luongnv89/skills) · License: MIT

## Skills

{rows}

Left out of this edition (they ship scripts or depend on skills that do): {left_out}.
"""
    if readme_words(readme) < 40:
        raise ValueError("edition README is under 40 words")
    out[PLUGIN + "/README.md"] = readme.encode()
    out["README.md"] = (
        "# lstack directory edition\n\nThis branch is generated by `" + SELF + "` from luongnv89/skills "
        "commit `" + sha + "`. Do not edit it by hand. The plugin folder is `" + PLUGIN + "/`. "
        "Rebuild and publish it as `packages/lstack/README.md` describes.\n").encode()
    out["provenance.json"] = BUILDER.json_bytes({
        "schema_version": 1, "edition": "directory", "package_version": manifest["version"],
        "source_commit": sha, "included": included, "excluded": excluded,
        "files": [{"path": p, "sha256": hashlib.sha256(d).hexdigest()} for p, d in sorted(out.items())]})
    return out, {"version": manifest["version"], "source_commit": sha, "included": included,
                 "excluded": excluded}


def write(root, files):
    root = Path(root)
    if root.exists() and (root.is_symlink() or not root.is_dir()
                          or any(p.name != ".git" for p in root.iterdir())):
        raise ValueError("output must be a new or empty folder (a .git entry is allowed): " + str(root))
    repo = ROOT.resolve()
    if root.resolve().is_relative_to(repo) and root.resolve() != repo:
        raise ValueError("output cannot be inside this repository: " + str(root))
    for path, data in sorted(files.items()):
        target = root / BUILDER.safe_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        os.chmod(target, 0o644)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--revision", default="HEAD", help="source commit or Git ref (default HEAD)")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--output", type=Path, help="new or empty folder (e.g. a `directory` branch worktree)")
    modes.add_argument("--check", type=Path, metavar="DIR", help="re-check an existing edition folder")
    modes.add_argument("--list", action="store_true", help="print included and excluded members only")
    args = parser.parse_args()
    try:
        if args.check:
            problems, count, notes = check_tree(args.check)
            print(json.dumps({"files": count, "problems": problems, "notes": notes}, indent=2))
            return 1 if problems else 0
        sha = BUILDER.git(ROOT, "rev-parse", "--verify", args.revision + "^{commit}").decode().strip()
        if BUILDER.git(ROOT, "show", sha + ":" + SELF) != Path(__file__).read_bytes():
            raise ValueError("builder differs from the selected revision; check out that revision first")
        files, summary = prepare(ROOT, sha)
        if args.output:
            write(args.output, files)
            problems, count, notes = check_tree(args.output)
            summary.update({"output": str(args.output), "files": count, "problems": problems,
                            "notes": notes})
            print(json.dumps(summary, indent=2))
            return 1 if problems else 0
        print(json.dumps(summary, indent=2))
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print("lstack-directory: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
