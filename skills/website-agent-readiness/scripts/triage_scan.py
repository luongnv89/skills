#!/usr/bin/env python3
"""Turn a scan into a phase-assigned worklist.

Reads scan.json (+ optional fixes.md) and emits triage.json plus a human-readable
table. Every field is copied from the scan -- nothing is inferred about the site.

Usage: triage_scan.py <outdir>
"""
import json
import re
import sys
from pathlib import Path

# Which phase a failing check lands in, by category. P0 is reserved for the
# checks the scanner itself names as the next-level requirements.
CATEGORY_PHASE = {
    "discoverability": "P1",
    "contentAccessibility": "P1",
    "botAccessControl": "P2",
    "discovery": "P3",
    "commerce": "P4",
}

PHASE_TITLE = {
    "P0": "Reach the next readiness level",
    "P1": "Discoverability and content access",
    "P2": "Bot access control",
    "P3": "Agent, API and auth discovery",
    "P4": "Agentic commerce",
}

# Effort band per check. Bands are fixed so two runs on the same site agree.
EFFORT = {
    # one-line edits to an existing file
    "robotsTxt": "XS", "robotsTxtAiRules": "XS", "contentSignals": "XS",
    # publish a static file
    "sitemap": "S", "llmsTxt": "S", "llmsFullTxt": "S", "apiCatalog": "S",
    "authMd": "S", "mcpServerCard": "S", "a2aAgentCard": "S", "agentSkills": "S",
    "ard": "S", "acp": "S", "ucp": "S", "mpp": "S",
    # server or edge configuration
    "linkHeaders": "M", "markdownNegotiation": "M", "oauthProtectedResource": "M",
    # new infrastructure or protocol integration
    "dnsAid": "L", "webBotAuth": "L", "oauthDiscovery": "L", "webMcp": "L",
    "x402": "L", "ap2": "L",
}
DEFAULT_EFFORT = "M"

# Guide slugs the camelCase->kebab rule cannot derive. Everything else follows it.
SLUG_OVERRIDES = {
    "robotsTxtAiRules": "ai-rules",
    "webMcp": "webmcp",
}


def slugify(check: str) -> str:
    """camelCase check key -> the scanner's kebab guide slug."""
    if check in SLUG_OVERRIDES:
        return SLUG_OVERRIDES[check]
    return re.sub(r"(?<!^)(?=[A-Z])", "-", check).lower()


def parse_fix_blocks(text: str):
    """Split the agent-format response into one block per failing check.

    Each block is '## <title>\n<prose>\nImplementation guide: <url>'.
    """
    blocks = []
    for chunk in re.split(r"^## ", text, flags=re.M)[1:]:
        lines = chunk.strip().splitlines()
        if not lines:
            continue
        title = lines[0].strip()
        guide = ""
        body = []
        for ln in lines[1:]:
            m = re.match(r"\s*Implementation guide:\s*(\S+)", ln)
            if m:
                guide = m.group(1)
            else:
                body.append(ln)
        blocks.append({
            "title": title,
            "prompt": " ".join(x.strip() for x in body if x.strip()),
            "guide": guide,
            "slug": guide.rstrip("/").split("/")[-2] if guide.count("/") >= 2 else "",
        })
    return blocks


def main() -> int:
    outdir = Path(sys.argv[1] if len(sys.argv) > 1 else ".agent-ready")
    scan = json.loads((outdir / "scan.json").read_text())

    fixes_path = outdir / "fixes.md"
    blocks = parse_fix_blocks(fixes_path.read_text()) if fixes_path.exists() else []

    # Ordered list of failing checks, in the scanner's own category order.
    fails, passes, neutrals = [], [], []
    for cat, checks in scan.get("checks", {}).items():
        for name, c in checks.items():
            if not isinstance(c, dict):
                continue
            row = {"check": name, "category": cat,
                   "message": c.get("message", ""), "status": c.get("status")}
            {"fail": fails, "pass": passes}.get(c.get("status"), neutrals).append(row)

    # Join fix prose to failing checks. Same source, same order, same count --
    # so position is the primary key; the guide slug is the fallback.
    joined_by = "position"
    if len(blocks) != len(fails):
        joined_by = "slug"
        by_slug = {b["slug"]: b for b in blocks if b["slug"]}
        for f in fails:
            b = by_slug.get(slugify(f["check"]), {})
            f.update(title=b.get("title", ""), prompt=b.get("prompt", ""),
                     guide=b.get("guide", ""))
    else:
        for f, b in zip(fails, blocks):
            f.update(title=b["title"], prompt=b["prompt"], guide=b["guide"])

    # nextLevel requirements take priority -- they are the shortest path to +1.
    next_level = scan.get("nextLevel") or {}
    p0_checks = {r.get("check") for r in next_level.get("requirements", [])}
    by_check = {r.get("check"): r for r in next_level.get("requirements", [])}

    is_commerce = bool(scan.get("isCommerce"))
    for f in fails:
        if f["check"] in p0_checks:
            f["phase"] = "P0"
            req = by_check[f["check"]]
            # nextLevel carries a richer prompt than the agent-format summary.
            f["prompt"] = req.get("prompt") or f.get("prompt", "")
            f["title"] = req.get("description") or f.get("title", "")
            f["guide"] = req.get("skillUrl") or f.get("guide", "")
            f["specUrls"] = req.get("specUrls", [])
        else:
            f["phase"] = CATEGORY_PHASE.get(f["category"], "P3")
        f["effort"] = EFFORT.get(f["check"], DEFAULT_EFFORT)
        # A non-commerce site gets no commerce issues -- they go to Deferred.
        f["deferred"] = (f["phase"] == "P4" and not is_commerce)

    phases = {}
    for f in fails:
        if f["deferred"]:
            continue
        phases.setdefault(f["phase"], []).append(f)
    for p in phases:
        phases[p].sort(key=lambda r: (r["category"], r["check"]))

    triage = {
        "url": scan.get("url"),
        "targetUrl": scan.get("targetUrl"),
        "redirectedFrom": scan.get("targetRedirectedFrom"),
        "scannedAt": scan.get("scannedAt"),
        "level": scan.get("level"),
        "levelName": scan.get("levelName"),
        "nextLevel": {"target": next_level.get("target"), "name": next_level.get("name")},
        "isCommerce": is_commerce,
        "counts": {"pass": len(passes), "fail": len(fails), "neutral": len(neutrals)},
        "joined_by": joined_by,
        "phases": [
            {"id": p, "title": PHASE_TITLE.get(p, p), "tasks": phases[p]}
            for p in ["P0", "P1", "P2", "P3", "P4"] if phases.get(p)
        ],
        "deferred": [f for f in fails if f["deferred"]],
        "passing": passes,
        "neutral": neutrals,
    }
    (outdir / "triage.json").write_text(json.dumps(triage, indent=2))

    # --- human table -------------------------------------------------------
    tgt = triage["targetUrl"] or triage["url"]
    print(f"Site      {tgt}")
    if triage["redirectedFrom"] and triage["redirectedFrom"] != tgt:
        print(f"          (redirected from {triage['redirectedFrom']})")
    print(f"Score     {triage['level']}/5 — {triage['levelName']}")
    nl = triage["nextLevel"]
    if nl.get("target") is not None:
        print(f"Next      {nl['target']}/5 — {nl['name']}")
    c = triage["counts"]
    print(f"Checks    {c['pass']} pass · {c['fail']} fail · {c['neutral']} neutral")
    print(f"Commerce  {'yes' if is_commerce else 'no (commerce checks deferred)'}")
    print()
    for ph in triage["phases"]:
        print(f"── Phase {ph['id']} — {ph['title']}  ({len(ph['tasks'])} tasks)")
        for t in ph["tasks"]:
            print(f"     {t['effort']:<3} {t['check']:<24} {t['message'][:56]}")
    if triage["deferred"]:
        print(f"── Deferred ({len(triage['deferred'])})")
        for t in triage["deferred"]:
            print(f"     {'—':<3} {t['check']:<24} {t['message'][:56]}")
    print()
    if joined_by == "slug":
        print("⚠ fix-block count did not match failing-check count; joined by guide slug.")
        missing = [f["check"] for f in fails if not f.get("prompt")]
        if missing:
            print(f"⚠ no fix prose for: {', '.join(missing)} — use the check message instead.")
    print(f"✓ wrote {outdir / 'triage.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
