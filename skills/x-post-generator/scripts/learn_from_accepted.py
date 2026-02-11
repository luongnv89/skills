#!/usr/bin/env python3
"""Learn brand preferences from accepted X posts.

- Appends accepted post to references/accepted_posts.jsonl
- Keeps only last 10 accepted posts
- Updates AUTO_LEARNED section in references/brand.md
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

AUTO_START = "<!-- AUTO_LEARNED_START -->"
AUTO_END = "<!-- AUTO_LEARNED_END -->"
MAX_POSTS = 10


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--post", help="Accepted post text")
    p.add_argument("--skill-dir", default=str(Path(__file__).resolve().parents[1]))
    return p.parse_args()


def read_post(args: argparse.Namespace) -> str:
    if args.post and args.post.strip():
        return args.post.strip()
    data = ""
    try:
        data = input().strip()
    except EOFError:
        pass
    if not data:
        raise SystemExit("[ERR] Missing --post text")
    return data


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    items: list[dict] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return items


def save_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n"
    path.write_text(text, encoding="utf-8")


def extract_hashtags(text: str) -> list[str]:
    tags = re.findall(r"#([A-Za-z0-9_]+)", text)
    return [f"#{t}" for t in tags]


def extract_media_links(text: str) -> list[str]:
    return re.findall(r"https?://\S+", text)


def build_auto_learned(rows: list[dict]) -> str:
    if not rows:
        return "No accepted posts yet."

    posts = [r.get("post", "") for r in rows if r.get("post")]
    hashtags = Counter(tag.lower() for p in posts for tag in extract_hashtags(p))

    avg_len = int(sum(len(p) for p in posts) / len(posts)) if posts else 0
    top_tags = [tag for tag, _ in hashtags.most_common(8)]

    sample_lines = []
    for r in rows[-3:]:
        ts = r.get("accepted_at", "")
        post = r.get("post", "").replace("\n", " ").strip()
        if len(post) > 140:
            post = post[:137] + "..."
        sample_lines.append(f"- {ts}: {post}")

    out = []
    out.append(f"Accepted posts tracked: {len(rows)} (max {MAX_POSTS})")
    out.append(f"Average post length: {avg_len} chars")
    out.append("Top hashtags: " + (", ".join(top_tags) if top_tags else "(none)"))
    out.append("")
    out.append("Recent accepted examples:")
    out.extend(sample_lines or ["- (none)"])
    return "\n".join(out)


def update_brand_md(path: Path, auto_text: str) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "# Brand Reference for X Posts\n\n"
            "## Learned from accepted posts (auto-updated)\n"
            f"{AUTO_START}\n{auto_text}\n{AUTO_END}\n",
            encoding="utf-8",
        )
        return

    content = path.read_text(encoding="utf-8", errors="ignore")
    block = f"{AUTO_START}\n{auto_text}\n{AUTO_END}"

    if AUTO_START in content and AUTO_END in content:
        content = re.sub(
            rf"{re.escape(AUTO_START)}.*?{re.escape(AUTO_END)}",
            block,
            content,
            flags=re.S,
        )
    else:
        content = content.rstrip() + "\n\n## Learned from accepted posts (auto-updated)\n" + block + "\n"

    path.write_text(content, encoding="utf-8")


def main() -> int:
    args = parse_args()
    post = read_post(args)

    skill_dir = Path(args.skill_dir).resolve()
    refs = skill_dir / "references"
    db_path = refs / "accepted_posts.jsonl"
    brand_path = refs / "brand.md"

    rows = load_jsonl(db_path)
    rows.append(
        {
            "accepted_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "post": post,
            "hashtags": extract_hashtags(post),
            "media_links": extract_media_links(post),
        }
    )
    rows = rows[-MAX_POSTS:]

    save_jsonl(db_path, rows)
    auto_text = build_auto_learned(rows)
    update_brand_md(brand_path, auto_text)

    print(f"[OK] Learned from accepted post. Stored {len(rows)} entries.")
    print(f"[OK] Updated: {db_path}")
    print(f"[OK] Updated: {brand_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
