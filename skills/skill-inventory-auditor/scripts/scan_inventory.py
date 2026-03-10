#!/usr/bin/env python3
"""
Skill Inventory Scanner - Scan installed skills and detect duplicates.

Usage:
    scan_inventory.py --scope global|project|both [--project-dir PATH]

Scans skill directories, extracts metadata, and detects duplicates via name
matching and description similarity. Outputs JSON to stdout.

Dependencies: Python stdlib only (no pip packages required).
"""

import argparse
import difflib
import json
import os
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# YAML frontmatter parsing (regex fallback, no dependency)
# ---------------------------------------------------------------------------

def parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from markdown content using regex fallback."""
    if not content.startswith("---"):
        return {}

    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}

    raw = match.group(1)

    # Try yaml module if available
    try:
        import yaml
        data = yaml.safe_load(raw)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # Regex fallback for simple key: value pairs
    result = {}
    for line in raw.splitlines():
        m = re.match(r"^(\w[\w-]*)\s*:\s*(.+)$", line.strip())
        if m:
            key = m.group(1).strip()
            val = m.group(2).strip().strip("'\"")
            result[key] = val
    return result


# ---------------------------------------------------------------------------
# Per-skill metadata extraction
# ---------------------------------------------------------------------------

def location_label(path: Path) -> str:
    """Classify a skill path into a location bucket."""
    s = str(path)
    if "/.claude/skills" in s and "/.agents/" not in s:
        return "global-claude"
    if "/.agents/skills" in s:
        return "global-agents"
    return "project"


def extract_skill_metadata(skill_dir: Path, scan_root: Path | None = None) -> dict | None:
    """Extract metadata from a single skill directory."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return None

    try:
        content = skill_md.read_text(errors="replace")
    except Exception:
        return None

    fm = parse_frontmatter(content)
    resolved = skill_dir.resolve()

    is_symlink = skill_dir.is_symlink()
    symlink_target = str(os.readlink(skill_dir)) if is_symlink else None

    # Count files
    file_count = 0
    try:
        for f in sorted(skill_dir.rglob("*")):
            if f.is_file() and not f.name.startswith("."):
                file_count += 1
    except Exception:
        pass

    loc_path = scan_root if scan_root is not None else resolved.parent
    location = location_label(loc_path)

    return {
        "dir_name": skill_dir.name,
        "name": fm.get("name", skill_dir.name),
        "description": fm.get("description", ""),
        "version": fm.get("version", ""),
        "path": str(resolved),
        "original_path": str(skill_dir),
        "location": location,
        "is_symlink": is_symlink,
        "symlink_target": symlink_target,
        "file_count": file_count,
    }


# ---------------------------------------------------------------------------
# Duplicate detection (union-find + description similarity)
# ---------------------------------------------------------------------------

class UnionFind:
    """Simple union-find for grouping duplicates."""

    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1


def detect_duplicates(skills: list[dict]) -> tuple[list[dict], dict]:
    """
    Detect duplicate skills. Returns (duplicate_groups, symlink_map).

    Steps:
    1. Identify symlinks pointing to same target (shared installations, NOT duplicates)
    2. Group by name field
    3. Pairwise description similarity >= 0.70
    4. Build connected components via union-find
    """
    symlink_map = {}  # target_path -> list of symlink paths

    # Build symlink map
    for s in skills:
        if s["is_symlink"] and s["symlink_target"]:
            target = s["symlink_target"]
            if target not in symlink_map:
                symlink_map[target] = []
            symlink_map[target].append(s["path"])

    # Filter to unique resolved paths (skip symlink duplicates of same target)
    unique_indices = []
    seen_resolved = set()
    for i, s in enumerate(skills):
        resolved = s["path"]
        if resolved not in seen_resolved:
            seen_resolved.add(resolved)
            unique_indices.append(i)

    n = len(unique_indices)
    if n <= 1:
        return [], symlink_map

    uf = UnionFind(n)

    # Group by name
    name_groups = {}
    for ui, idx in enumerate(unique_indices):
        name = skills[idx]["name"].lower().strip()
        if name not in name_groups:
            name_groups[name] = []
        name_groups[name].append(ui)

    for name, members in name_groups.items():
        if len(members) > 1:
            for j in range(1, len(members)):
                uf.union(members[0], members[j])

    # Pairwise description similarity
    descs = []
    for ui in unique_indices:
        descs.append(skills[ui].get("description", "").lower().strip())

    for i in range(n):
        if not descs[i]:
            continue
        for j in range(i + 1, n):
            if not descs[j]:
                continue
            ratio = difflib.SequenceMatcher(None, descs[i], descs[j]).ratio()
            if ratio >= 0.70:
                uf.union(i, j)

    # Build connected components
    components = {}
    for ui in range(n):
        root = uf.find(ui)
        if root not in components:
            components[root] = []
        components[root].append(unique_indices[ui])

    # Filter to groups with 2+ members
    duplicate_groups = []
    for root, members in components.items():
        if len(members) < 2:
            continue

        group_skills = [skills[m] for m in members]

        # Compute pairwise similarity for the group
        similarities = []
        for i in range(len(group_skills)):
            for j in range(i + 1, len(group_skills)):
                d1 = group_skills[i].get("description", "")
                d2 = group_skills[j].get("description", "")
                if d1 and d2:
                    sim = difflib.SequenceMatcher(None, d1.lower(), d2.lower()).ratio()
                    similarities.append({
                        "skill_a": group_skills[i]["name"],
                        "skill_b": group_skills[j]["name"],
                        "similarity": round(sim, 3),
                    })

        duplicate_groups.append({
            "skills": [
                {
                    "name": s["name"],
                    "dir_name": s["dir_name"],
                    "path": s["path"],
                    "location": s["location"],
                    "version": s.get("version", ""),
                    "description": s.get("description", "")[:200],
                    "file_count": s.get("file_count", 0),
                }
                for s in group_skills
            ],
            "reason": "same_name" if len(set(s["name"] for s in group_skills)) == 1 else "similar_description",
            "similarities": similarities,
        })

    return duplicate_groups, symlink_map


# ---------------------------------------------------------------------------
# Directory scanning
# ---------------------------------------------------------------------------

def scan_directory(base_dir: Path) -> list[dict]:
    """Scan a directory for skill subdirectories (each containing SKILL.md)."""
    skills = []
    if not base_dir.is_dir():
        return skills

    try:
        entries = sorted(base_dir.iterdir())
    except PermissionError:
        return skills

    for entry in entries:
        if not entry.is_dir():
            continue
        if entry.name.startswith("."):
            continue

        meta = extract_skill_metadata(entry, scan_root=base_dir)
        if meta is not None:
            skills.append(meta)

    return skills


def get_scan_dirs(scope: str, project_dir: str | None) -> list[Path]:
    """Return the list of directories to scan based on scope."""
    dirs = []
    home = Path.home()

    if scope in ("global", "both"):
        dirs.append(home / ".claude" / "skills")
        dirs.append(home / ".agents" / "skills")

    if scope in ("project", "both"):
        if project_dir:
            dirs.append(Path(project_dir) / ".claude" / "skills")
        else:
            dirs.append(Path.cwd() / ".claude" / "skills")

    return dirs


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Scan installed agent skills and detect duplicates."
    )
    parser.add_argument(
        "--scope",
        choices=["global", "project", "both"],
        default="both",
        help="Scope to scan: global (~/.claude/skills, ~/.agents/skills), project (.claude/skills), or both",
    )
    parser.add_argument(
        "--project-dir",
        default=None,
        help="Project directory path (for project scope). Defaults to cwd.",
    )
    args = parser.parse_args()

    scan_dirs = get_scan_dirs(args.scope, args.project_dir)

    all_skills = []
    location_summary = {}

    for d in scan_dirs:
        found = scan_directory(d)
        loc = location_label(d)
        if loc not in location_summary:
            location_summary[loc] = {"directory": str(d), "count": 0}
        location_summary[loc]["count"] += len(found)
        all_skills.extend(found)

    # Detect duplicates
    duplicate_groups, symlink_map = detect_duplicates(all_skills)

    # Count unique (by resolved path)
    unique_paths = set(s["path"] for s in all_skills)

    # Count symlink shared installations
    shared_count = sum(1 for s in all_skills if s["is_symlink"])

    output = {
        "summary": {
            "total_skills": len(all_skills),
            "unique_skills": len(unique_paths),
            "shared_installations": shared_count,
            "duplicate_groups": len(duplicate_groups),
        },
        "location_summary": location_summary,
        "skills": all_skills,
        "duplicate_groups": duplicate_groups,
        "symlink_map": symlink_map,
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
