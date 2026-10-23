#!/usr/bin/env python3
"""Check a product-launch kit before the founder uses it.

Checks every Markdown file under the kit folder:
  1. Field markers `<!-- field: <id> [min=N] [max=N] [unit=chars|words] -->` are each
     followed by a fenced block whose value respects the limits. Characters are counted
     in UTF-16 code units, the way browser forms count them.
  2. No field value holds a placeholder (TODO, TBD, [insert, {{, lorem ipsum).
  3. No field value asks for votes ("please upvote", "vote for us", ...).
  4. A file marked `<!-- mode: founder-voice -->` holds no field markers.
  5. Each platforms/*.md has a mode marker and a "## Sources" heading.
  6. README.md, launch-plan.md, copy-bank.md and assets.md exist.

Usage:
  python3 check_kit.py KIT_DIR [--json]
  python3 check_kit.py --self-test

Exit codes: 0 every check passed, 1 at least one check failed, 2 usage error.
Standard library only.
"""
import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

REQUIRED_FILES = ("README.md", "launch-plan.md", "copy-bank.md", "assets.md")
MARKER = re.compile(r"^\s*<!--\s*field:\s*([A-Za-z0-9_.\-]+)((?:\s+[a-z]+=[A-Za-z0-9]+)*)\s*-->\s*$")
MODE = re.compile(r"<!--\s*mode:\s*(paste-ready|founder-voice)\s*-->")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
PLACEHOLDER = re.compile(r"\bTODO\b|\bTBD\b|(?i:\[insert|\{\{|lorem ipsum|<placeholder)")
VOTE_ASKS = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\b(please|pls|kindly|help us|feel free to|don'?t forget to|do not forget to|"
        r"would you|could you|can you|go and|remember to)\b[^.!?\n]{0,40}\b(up-?vote|vote)",
        r"\b(up-?vote|vote for|vote on)\s+(us|me|our|my|it|this|the launch)\b",
        r"\b(every|your) (up-?)?vote (counts|matters|helps)\b",
        r"\bsupport us with (a|an|your) (up-?)?vote\b",
        r"\b(we|i) need your (up-?)?votes?\b",
    )
]


def measure(value, unit):
    if unit == "words":
        return len(value.split())
    return len(value.encode("utf-16-le")) // 2


def parse_limits(raw, problems, where):
    limits = {"unit": "chars"}
    for pair in raw.split():
        key, _, val = pair.partition("=")
        if key in ("min", "max") and val.isdigit():
            limits[key] = int(val)
        elif key == "unit" and val in ("chars", "words"):
            limits["unit"] = val
        else:
            problems.append(f"{where}: unknown marker option '{pair}' — use min=N, max=N, unit=chars|words")
    return limits


def check_file(path, rel, fields, problems):
    lines = path.read_text(encoding="utf-8").splitlines()
    mode_match = MODE.search("\n".join(lines[:5]))
    mode = mode_match.group(1) if mode_match else None
    i, in_fence, fence = 0, False, ""
    while i < len(lines):
        line = lines[i]
        fence_match = FENCE.match(line)
        if in_fence:
            if fence_match and line.strip() == fence[0] * len(line.strip()) and len(line.strip()) >= len(fence):
                in_fence = False
            i += 1
            continue
        if fence_match:
            in_fence, fence = True, fence_match.group(1)
            i += 1
            continue
        marker = MARKER.match(line)
        if not marker:
            i += 1
            continue
        where = f"{rel}:{i + 1}"
        field_id = marker.group(1)
        limits = parse_limits(marker.group(2), problems, where)
        if mode == "founder-voice":
            problems.append(f"{where}: field '{field_id}' in a founder-voice file — founder-voice guides hold facts and structure only; remove the paste-ready value")
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        opener = FENCE.match(lines[j]) if j < len(lines) else None
        if not opener:
            problems.append(f"{where}: field '{field_id}' is not followed by a fenced block — put the value in a ~~~ block on the next line")
            i += 1
            continue
        fence_str = opener.group(1)
        k = j + 1
        body = []
        while k < len(lines):
            stripped = lines[k].strip()
            if stripped and stripped == fence_str[0] * len(stripped) and len(stripped) >= len(fence_str):
                break
            body.append(lines[k])
            k += 1
        if k >= len(lines):
            problems.append(f"{where}: field '{field_id}' block is never closed — add a closing {fence_str} line")
            break
        value = "\n".join(body).strip()
        length = measure(value, limits["unit"])
        record = {"file": rel, "line": i + 1, "id": field_id, "unit": limits["unit"], "length": length,
                  "min": limits.get("min"), "max": limits.get("max"), "problems": []}
        if not value:
            record["problems"].append("empty value — write the value or remove the marker")
        if "max" in limits and length > limits["max"]:
            record["problems"].append(f"{length} {limits['unit']} > max {limits['max']} — shorten it to {limits['max']} or fewer")
        if "min" in limits and length < limits["min"]:
            record["problems"].append(f"{length} {limits['unit']} < min {limits['min']} — lengthen it to at least {limits['min']}")
        found = PLACEHOLDER.search(value)
        if found:
            record["problems"].append(f"placeholder '{found.group(0)}' — move open questions to 'Founder inputs needed'")
        for pattern in VOTE_ASKS:
            ask = pattern.search(value)
            if ask:
                record["problems"].append(f"vote request '{ask.group(0)}' — ask for feedback or a visit instead")
                break
        fields.append(record)
        for problem in record["problems"]:
            problems.append(f"{rel}:{i + 1}: field '{field_id}': {problem}")
        i = k + 1
    return mode


def check_kit(kit):
    fields, problems = [], []
    for name in REQUIRED_FILES:
        if not (kit / name).is_file():
            problems.append(f"{name}: missing — Step 5 must write it before the kit check")
    platform_dir = kit / "platforms"
    platform_files = sorted(platform_dir.glob("*.md")) if platform_dir.is_dir() else []
    if not platform_files:
        problems.append("platforms/: no platform guides — Step 5b writes one per approved platform")
    founder_voice = 0
    for path in sorted(kit.rglob("*.md")):
        rel = path.relative_to(kit).as_posix()
        mode = check_file(path, rel, fields, problems)
        if path.parent == platform_dir:
            if mode is None:
                problems.append(f"{rel}: no '<!-- mode: paste-ready -->' or '<!-- mode: founder-voice -->' marker in the first 5 lines")
            elif mode == "founder-voice":
                founder_voice += 1
            if not re.search(r"^## Sources\s*$", path.read_text(encoding="utf-8"), re.MULTILINE):
                problems.append(f"{rel}: no '## Sources' heading — list the platform sources and the live-check result")
    failed = sum(1 for f in fields if f["problems"])
    summary = {"fields_checked": len(fields), "fields_failed": failed, "platform_files": len(platform_files),
               "founder_voice_files": founder_voice,
               "required_files_present": sum((kit / n).is_file() for n in REQUIRED_FILES)}
    return {"kit": str(kit), "ok": not problems, "summary": summary, "problems": problems, "fields": fields}


def print_text(result):
    s = result["summary"]
    print(f"check_kit: {result['kit']} — fields {s['fields_checked']} checked, {s['fields_failed']} failed · "
          f"platform files {s['platform_files']} (founder-voice {s['founder_voice_files']}) · "
          f"required files {s['required_files_present']}/{len(REQUIRED_FILES)}")
    for problem in result["problems"]:
        print(f"FAIL {problem}")
    print("PASS" if result["ok"] else f"FAIL ({len(result['problems'])} problems)")


def self_test():
    def check_files(files):
        with tempfile.TemporaryDirectory(prefix="check-kit-") as tmp:
            root = Path(tmp)
            for name, text in files.items():
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text, encoding="utf-8")
            return check_kit(root)

    base = {
        "README.md": "# Kit\n", "launch-plan.md": "# Plan\n", "assets.md": "# Assets\n",
        "copy-bank.md": "# Copy\n<!-- field: copy.tagline-60 max=60 -->\n~~~text\nLet users upvote feature requests\n~~~\n",
        "platforms/product-hunt.md": "# PH\n<!-- mode: paste-ready -->\n<!-- field: product-hunt.tagline max=60 -->\n"
                                     "~~~\nShip launch plans fast 🚀\n~~~\n\n## Sources\n- x\n",
        "platforms/hacker-news.md": "# HN\n<!-- mode: founder-voice -->\nFacts only.\n\n## Sources\n- y\n",
    }
    cases = [
        ("clean kit passes", {}, True, None),
        ("too long fails", {"platforms/product-hunt.md": base["platforms/product-hunt.md"].replace(
            "Ship launch plans fast 🚀", "x" * 61)}, False, "> max 60"),
        ("founder-voice marker fails", {"platforms/hacker-news.md": "# HN\n<!-- mode: founder-voice -->\n"
                                        "<!-- field: hacker-news.title max=80 -->\n~~~\nShow HN: X\n~~~\n## Sources\n"},
         False, "founder-voice file"),
        ("vote request fails", {"copy-bank.md": "<!-- field: copy.outreach -->\n~~~\nWe're live! Please upvote us today.\n~~~\n"},
         False, "vote request"),
        ("placeholder fails", {"copy-bank.md": "<!-- field: copy.pitch-80 max=80 -->\n~~~\nTODO write pitch\n~~~\n"},
         False, "placeholder"),
        ("words unit", {"copy-bank.md": "<!-- field: copy.headline-8w max=8 unit=words -->\n~~~\none two three four five six seven eight nine\n~~~\n"},
         False, "9 words > max 8"),
        ("missing sources fails", {"platforms/hacker-news.md": "# HN\n<!-- mode: founder-voice -->\nFacts.\n"},
         False, "Sources"),
        ("marker inside a code fence is ignored", {"README.md": "```\n<!-- field: x.y max=1 -->\n```\n"}, True, None),
        ("utf-16 counts emoji as 2", {"platforms/product-hunt.md": base["platforms/product-hunt.md"].replace(
            "Ship launch plans fast 🚀", "a" * 59 + "🚀")}, False, "61 chars > max 60"),
    ]
    failures = 0
    for name, overrides, expect_ok, needle in cases:
        files = dict(base)
        files.update(overrides)
        result = check_files(files)
        text = "\n".join(result["problems"])
        passed = result["ok"] == expect_ok and (needle is None or needle in text)
        if not passed:
            failures += 1
            print(f"self-test FAIL: {name}: ok={result['ok']} problems={result['problems']}", file=sys.stderr)
    if failures:
        print(f"self-test: {failures} of {len(cases)} cases failed", file=sys.stderr)
        return 1
    print(f"self-test: {len(cases)} cases passed")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Check a product-launch kit folder.")
    parser.add_argument("kit", nargs="?", help="path to the launch-kit folder")
    parser.add_argument("--json", action="store_true", help="print the full result as JSON")
    parser.add_argument("--self-test", action="store_true", help="run the built-in test cases")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.kit:
        print("Error: no kit folder given. Usage: python3 check_kit.py launch-kit [--json]", file=sys.stderr)
        return 2
    kit = Path(args.kit)
    if not kit.is_dir():
        print(f"Error: kit folder '{kit}' not found. Pass the folder Step 5 wrote, e.g. "
              f"python3 check_kit.py launch-kit", file=sys.stderr)
        return 2
    result = check_kit(kit)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_text(result)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
