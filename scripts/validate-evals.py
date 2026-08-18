#!/usr/bin/env python3
# Validates: every skills/*/evals/evals.json against the canonical eval schema
# Usage: python3 scripts/validate-evals.py [--path skills]
#
# The canonical shape is defined by skill-creator, which is external to this repo
# (CONTRIBUTING.md:18, :24-27):
#     ~/.claude/skills/skill-creator/references/schemas.md:9-45
#
#     {"skill_name": str,
#      "evals": [{"id": int, "kind": str, "prompt": str,
#                 "expected_output": str, "files": list, "expectations": list}]}
#
# `kind` defaults to "happy-path" when omitted (schemas.md:39), so a missing `kind`
# is a WARN, never a FAIL — writing `"kind": "happy-path"` into a file that never
# declared one would be a semantic guess, not a translation.
#
# This repo has no npm/pnpm/make/pytest (CLAUDE.md:12). Stdlib only.

import json
import sys
from pathlib import Path

# Canonical keys (schemas.md:9-45), plus `name`: an optional human slug this repo
# uses to preserve the original descriptive id of a file whose ids were strings.
TOP_KEYS = {"skill_name", "evals"}
CASE_KEYS = {"id", "kind", "prompt", "expected_output", "files", "expectations", "name"}
REQUIRED_CASE_KEYS = ("prompt", "expected_output")

# Assertion lists seen parked under non-canonical keys in this catalog's history.
# The runner reads `expectations` and nothing else, so these are silently dead.
DRIFTED_ASSERTION_KEYS = ("assertions", "expected_behavior")


def check_file(path: Path):
    """Return (fails, warns) as two lists of human-readable strings."""
    fails, warns = [], []

    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        return ["unreadable JSON — %s" % exc], []

    if not isinstance(data, dict):
        return ["top level is %s, expected an object" % type(data).__name__], []

    unknown_top = sorted(set(data) - TOP_KEYS)
    if unknown_top:
        fails.append("unknown top-level key(s): %s" % ", ".join(unknown_top))

    skill_dir = path.parent.parent.name
    if "skill_name" not in data:
        fails.append("missing top-level 'skill_name'")
    elif data["skill_name"] != skill_dir:
        fails.append(
            "skill_name %r does not match the skill directory %r"
            % (data["skill_name"], skill_dir)
        )

    evals = data.get("evals")
    if evals is None:
        fails.append("missing top-level 'evals'")
        return fails, warns
    if not isinstance(evals, list):
        fails.append("'evals' is %s, expected a list" % type(evals).__name__)
        return fails, warns
    if not evals:
        fails.append("'evals' is empty")
        return fails, warns

    seen_ids = {}
    any_kind = False
    for pos, case in enumerate(evals, start=1):
        where = "case #%d" % pos
        if not isinstance(case, dict):
            fails.append("%s is %s, expected an object" % (where, type(case).__name__))
            continue

        case_id = case.get("id")
        if case_id is None:
            fails.append("%s has no 'id'" % where)
        elif isinstance(case_id, bool) or not isinstance(case_id, int):
            fails.append(
                "%s has a non-integer id %r (%s)"
                % (where, case_id, type(case_id).__name__)
            )
        elif case_id in seen_ids:
            fails.append(
                "%s duplicates id %r (first seen at case #%d)"
                % (where, case_id, seen_ids[case_id])
            )
        else:
            seen_ids[case_id] = pos

        label = "id %r" % case_id if case_id is not None else where
        for key in REQUIRED_CASE_KEYS:
            if not case.get(key):
                fails.append("%s is missing '%s'" % (label, key))

        for key in DRIFTED_ASSERTION_KEYS:
            if key in case:
                fails.append(
                    "%s parks its assertion list under '%s' — the runner only reads "
                    "'expectations'" % (label, key)
                )

        unknown_case = sorted(set(case) - CASE_KEYS - set(DRIFTED_ASSERTION_KEYS))
        if unknown_case:
            fails.append("%s has unknown key(s): %s" % (label, ", ".join(unknown_case)))

        if "kind" in case:
            any_kind = True
        if "files" not in case:
            warns.append("%s has no 'files' key" % label)
        if "expectations" in case and not case["expectations"]:
            warns.append("%s has an empty 'expectations' list" % label)
        elif "expectations" not in case:
            warns.append("%s has no 'expectations' key" % label)

    if not any_kind:
        warns.append(
            "no case declares 'kind' — every case defaults to happy-path "
            "(schemas.md:39); a negative-trigger or edge case would be mislabelled"
        )

    return fails, warns


def main(argv):
    root = Path(__file__).resolve().parent.parent
    base = root / "skills"
    if len(argv) >= 2 and argv[0] == "--path":
        base = (root / argv[1]).resolve()

    files = sorted(base.glob("*/evals/evals.json")) + sorted(
        base.glob("*/*/evals/evals.json")
    )
    if not files:
        print("no evals.json found under %s" % base)
        return 1

    fail_count = 0
    warn_count = 0
    for path in files:
        rel = path.relative_to(root)
        fails, warns = check_file(path)
        if fails:
            fail_count += 1
            print("[FAIL] %s" % rel)
            for msg in fails:
                print("       %s" % msg)
        else:
            print("[PASS] %s" % rel)
        for msg in warns:
            warn_count += 1
            print("[WARN] %s: %s" % (rel, msg))

    print(
        "\n%d/%d structural PASS, %d WARN"
        % (len(files) - fail_count, len(files), warn_count)
    )
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
