#!/usr/bin/env python3
"""Validate UX/AX report structure, never evidence truth (stdlib only)."""


def validate_report(report, markdown=None):
    """Return readable, field-specific structural errors; [] means PASS."""
    import math
    errors = []
    stack = [("report", report)]
    visited = set()
    while stack:
        path, value = stack.pop()
        if isinstance(value, float) and not math.isfinite(value):
            errors.append(f"{path}: nonfinite number is not permitted")
        if isinstance(value, (dict, list)) and id(value) not in visited:
            visited.add(id(value))
            if isinstance(value, dict):
                stack.extend((f"{path}.{key}", child) for key, child in value.items())
            else:
                stack.extend((f"{path}[{index}]", child) for index, child in enumerate(value))
    if not isinstance(report, dict):
        return ["report: expected an object"]
    if type(report.get("schema_version")) is not int or report["schema_version"] != 1:
        errors.append("schema_version: expected integer 1")
    def string(value, path, allow_empty=False):
        if not isinstance(value, str) or (not allow_empty and not value.strip()):
            errors.append(f"{path}: expected {'a string' if allow_empty else 'a nonempty string'}")
            return False
        return True

    def string_array(value, path):
        if not isinstance(value, list):
            errors.append(f"{path}: expected an array of nonempty strings")
            return []
        valid = []
        for index, item in enumerate(value):
            if string(item, f"{path}[{index}]"):
                valid.append(item)
        return valid

    scope = report.get("scope")
    if not isinstance(scope, dict):
        errors.append("scope: expected an object")
    else:
        for field in ("target", "mode", "audience", "primary_goal"):
            string(scope.get(field), f"scope.{field}")
        for field in ("sampled_surfaces", "limitations"):
            string_array(scope.get(field), f"scope.{field}")
    rows = {}
    for key in ("evidence", "coverage", "findings", "plan"):
        value = report.get(key)
        rows[key] = []
        if not isinstance(value, list):
            errors.append(f"{key}: expected an array")
            continue
        for index, item in enumerate(value):
            path = f"{key}[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{path}: expected an object")
            else:
                rows[key].append((path, item))
    fields = {
        "evidence": ("id", "source", "method", "observation", "limitations"),
        "coverage": ("aspect", "status", "rationale", "evidence_ids", "finding_ids"),
        "findings": ("id", "aspect", "kind", "severity", "confidence", "title", "evidence_ids", "recommendation"),
        "plan": ("id", "phase", "priority", "finding_ids", "title", "owner", "effort", "dependencies", "expected_impact", "acceptance_checks"),
    }
    array_fields = {"evidence_ids", "finding_ids", "dependencies", "acceptance_checks"}
    for collection, keys in fields.items():
        for path, item in rows[collection]:
            for field in keys:
                value = item.get(field)
                if field in array_fields:
                    string_array(value, f"{path}.{field}")
                elif field == "phase":
                    if type(value) is not int:
                        errors.append(f"{path}.phase: expected an integer")
                else:
                    string(value, f"{path}.{field}", allow_empty=(collection == "evidence" and field == "limitations"))
    def enum(value, path, choices):
        if not isinstance(value, str) or value not in choices:
            errors.append(f"{path}: expected one of {', '.join(choices)}")

    if isinstance(scope, dict):
        enum(scope.get("mode"), "scope.mode", ("live-web", "repo", "evidence-only", "native-app"))
    domains = {
        "coverage": {"status": ("pass", "issues", "not-tested", "not-applicable")},
        "findings": {"kind": ("observed", "hypothesis"),
                     "severity": ("critical", "high", "medium", "low"),
                     "confidence": ("high", "medium", "low")},
        "plan": {"priority": ("P0", "P1", "P2", "P3"), "effort": ("XS", "S", "M", "L")},
    }
    for collection, domain in domains.items():
        for path, item in rows[collection]:
            for field, choices in domain.items():
                enum(item.get(field), f"{path}.{field}", choices)
            if collection == "plan" and type(item.get("phase")) is int and item["phase"] not in range(4):
                errors.append(f"{path}.phase: expected integer 0, 1, 2 or 3")
    aspects = (
        "clarity", "brand", "responsive", "accessibility", "performance", "conversion",
        "robots-sitemap", "structured-data", "markdown-pages", "llms-txt",
        "crawler-access", "ai-actions",
    )
    seen_aspects = set()
    coverage_value = report.get("coverage")
    if isinstance(coverage_value, list) and len(coverage_value) != len(aspects):
        errors.append("coverage: expected exactly 12 entries")
    for path, item in rows["coverage"]:
        aspect = item.get("aspect")
        enum(aspect, f"{path}.aspect", aspects)
        if isinstance(aspect, str):
            if aspect in seen_aspects:
                errors.append(f"{path}.aspect: duplicate aspect {aspect!r}")
            seen_aspects.add(aspect)
    for aspect in aspects:
        if aspect not in seen_aspects:
            errors.append(f"coverage: missing aspect {aspect!r}")
    for path, item in rows["findings"]:
        enum(item.get("aspect"), f"{path}.aspect", aspects)
    def supports(finding, aspect):
        related = finding.get("related_aspects", [])
        return finding.get("aspect") == aspect or (isinstance(related, list) and aspect in related)

    for path, item in rows["findings"]:
        if "related_aspects" in item:
            for index, aspect in enumerate(string_array(item["related_aspects"], f"{path}.related_aspects")):
                enum(aspect, f"{path}.related_aspects[{index}]", aspects)
    records = {}
    for collection in ("evidence", "findings", "plan"):
        records[collection] = {}
        for path, item in rows[collection]:
            identifier = item.get("id")
            if isinstance(identifier, str) and identifier.strip():
                if identifier in records[collection]:
                    errors.append(f"{path}.id: duplicate id {identifier!r}")
                else:
                    records[collection][identifier] = item
    references = {
        "coverage": {"evidence_ids": "evidence", "finding_ids": "findings"},
        "findings": {"evidence_ids": "evidence"},
        "plan": {"finding_ids": "findings", "dependencies": "plan"},
    }
    for collection, links in references.items():
        for path, item in rows[collection]:
            for field, target in links.items():
                values = item.get(field)
                if isinstance(values, list):
                    for index, value in enumerate(values):
                        if isinstance(value, str) and value not in records[target]:
                            errors.append(f"{path}.{field}[{index}]: unknown {target} id {value!r}")
    for path, item in rows["findings"]:
        if item.get("kind") == "observed" and not item.get("evidence_ids"):
            errors.append(f"{path}.evidence_ids: observed findings require evidence")
    for path, item in rows["coverage"]:
        if item.get("status") in ("pass", "issues") and not item.get("evidence_ids"):
            errors.append(f"{path}.evidence_ids: pass/issues coverage requires evidence")
    for path, item in rows["coverage"]:
        links = item.get("finding_ids")
        if isinstance(links, list):
            for index, identifier in enumerate(links):
                finding = records["findings"].get(identifier) if isinstance(identifier, str) else None
                if finding is not None and not supports(finding, item.get("aspect")):
                    errors.append(f"{path}.finding_ids[{index}]: finding aspect must match coverage aspect")
    for path, item in rows["coverage"]:
        if item.get("status") == "issues":
            links = item.get("finding_ids")
            linked = [records["findings"][identifier] for identifier in links
                      if isinstance(identifier, str) and identifier in records["findings"]] if isinstance(links, list) else []
            if not any(finding.get("kind") == "observed" and supports(finding, item.get("aspect"))
                       for finding in linked):
                errors.append(f"{path}.finding_ids: issues requires a linked observed finding for this aspect")
    for path, item in rows["plan"]:
        if not item.get("acceptance_checks"):
            errors.append(f"{path}.acceptance_checks: at least one check is required")
    task_order = {item.get("id"): index for index, (_, item) in enumerate(rows["plan"])
                  if isinstance(item.get("id"), str)}
    for index, (path, item) in enumerate(rows["plan"]):
        dependencies = item.get("dependencies")
        if isinstance(dependencies, list):
            for dep_index, dependency in enumerate(dependencies):
                if isinstance(dependency, str) and dependency in task_order and task_order[dependency] >= index:
                    errors.append(f"{path}.dependencies[{dep_index}]: dependency must precede task (self/cyclic/forward links forbidden)")
    planned = set()
    for _, item in rows["plan"]:
        links = item.get("finding_ids")
        if isinstance(links, list):
            planned.update(link for link in links if isinstance(link, str))
    for path, item in rows["findings"]:
        identifier = item.get("id")
        if isinstance(identifier, str) and identifier not in planned:
            errors.append(f"{path}.id: finding {identifier!r} has no plan task")
    if markdown is not None:
        headings = ("Executive Summary", "Scope and Evidence", "Human UX", "AI/Search AX",
                    "Prioritized Findings", "Improvement Plan", "Limitations and Next Step")
        if not isinstance(markdown, str):
            errors.append("markdown: expected a string")
        else:
            found = set()
            fence = None
            for line in markdown.splitlines():
                stripped = line.lstrip(" ")
                if len(line) - len(stripped) > 3:
                    continue
                if stripped.startswith(("```", "~~~")):
                    marker = stripped[0]
                    length = len(stripped) - len(stripped.lstrip(marker))
                    if fence is None:
                        fence = (marker, length)
                    elif marker == fence[0] and length >= fence[1] and not stripped[length:].strip():
                        fence = None
                    continue
                if fence is None and line.startswith("## "):
                    found.add(line[3:].strip())
            for heading in headings:
                if heading not in found:
                    errors.append(f"markdown: missing H2 heading {heading!r}")
    return errors


def main(argv=None):
    """Read report artifacts and emit only structural PASS or actionable errors."""
    import argparse
    import json
    from pathlib import Path
    import sys

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="Path to ux-ax-findings.json")
    parser.add_argument("--markdown", type=Path, help="Optional UX_AX_REVIEW.md to check")
    args = parser.parse_args(argv)
    def reject_constant(value):
        raise ValueError(f"nonfinite JSON number {value!r} is not permitted")

    try:
        report = json.loads(args.report.read_text(encoding="utf-8"), parse_constant=reject_constant)
        markdown = args.markdown.read_text(encoding="utf-8") if args.markdown else None
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        print(f"report/markdown: cannot read or parse artifact: {error}", file=sys.stderr)
        return 1
    errors = validate_report(report, markdown)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("PASS: report structure, coverage and references validated (not evidence truth)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
