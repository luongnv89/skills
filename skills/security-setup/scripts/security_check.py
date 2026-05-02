#!/usr/bin/env python3
"""Local security summary runner for the security-setup skill.

Copy this file into a target repository at scripts/security_check.py.
It intentionally uses only the Python standard library and external security
tools selected by security/security-tools.json.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
DEFAULT_TIMEOUT_SECONDS = 120
DEFAULT_EXPECTED_RETURNCODES: tuple[int, ...] = (0, 1)
EXPECTED_RETURNCODES: dict[str, tuple[int, ...]] = {
    "gitleaks": (0, 1),
    "trivy": (0, 1),
    "semgrep": (0, 1),
    "bandit": (0, 1),
    "cargo-audit": (0, 1),
}

# File globs that force a full scan (every applicable check runs) when staged.
# Workflow injection, hook tampering, and Dockerfile RCE shouldn't slip past
# scoping just because no source file was in the same commit.
DEFAULT_TRIP_ALL_PATHS: tuple[str, ...] = (
    ".pre-commit-config.yaml",
    "security/**",
    ".github/workflows/**",
    "Dockerfile",
    "Dockerfile.*",
    "**/Dockerfile",
    "**/Dockerfile.*",
    ".dockerignore",
    "scripts/security_check.py",
)

# Per-tool default triggers. Used when a check has no explicit `triggers` field.
# gitleaks runs on every commit (secrets land in .md, .json, .env.example, etc.).
DEFAULT_TRIGGERS: dict[str, dict[str, Any]] = {
    "gitleaks": {"always": True},
    "trivy": {
        "paths": [
            "package.json",
            "package-lock.json",
            "pnpm-lock.yaml",
            "yarn.lock",
            "Cargo.lock",
            "Cargo.toml",
            "go.mod",
            "go.sum",
            "requirements*.txt",
            "Pipfile",
            "Pipfile.lock",
            "pyproject.toml",
            "poetry.lock",
            "composer.json",
            "composer.lock",
            "Gemfile",
            "Gemfile.lock",
            "pom.xml",
            "build.gradle",
            "build.gradle.kts",
            "**/package.json",
            "**/package-lock.json",
            "**/pnpm-lock.yaml",
            "**/yarn.lock",
            "**/Cargo.lock",
            "**/Cargo.toml",
            "**/go.mod",
            "**/go.sum",
            "**/requirements*.txt",
            "**/Pipfile",
            "**/Pipfile.lock",
            "**/pyproject.toml",
            "**/poetry.lock",
            "**/composer.json",
            "**/composer.lock",
            "**/Gemfile",
            "**/Gemfile.lock",
            "**/pom.xml",
            "**/build.gradle",
            "**/build.gradle.kts",
        ],
    },
    "semgrep": {
        "paths": [
            "**/*.py",
            "**/*.js",
            "**/*.jsx",
            "**/*.ts",
            "**/*.tsx",
            "**/*.mjs",
            "**/*.cjs",
            "**/*.go",
            "**/*.rb",
            "**/*.php",
            "**/*.java",
            "**/*.kt",
            "**/*.kts",
            "**/*.scala",
            "**/*.cs",
            "**/*.c",
            "**/*.h",
            "**/*.cc",
            "**/*.cpp",
            "**/*.hpp",
            "**/*.rs",
            "**/*.swift",
            "**/*.sh",
            "**/*.bash",
            "**/*.zsh",
            "**/*.yaml",
            "**/*.yml",
            "**/Dockerfile",
            "**/Dockerfile.*",
        ],
    },
    "bandit": {"paths": ["**/*.py"]},
    "cargo-audit": {"paths": ["Cargo.lock", "Cargo.toml", "**/Cargo.lock", "**/Cargo.toml"]},
}
DEFAULT_CONFIG = {
    "fail_on": ["CRITICAL", "HIGH"],
    "checks": [
        {
            "name": "gitleaks",
            "category": "secrets",
            "required": True,
            "command": [
                "gitleaks",
                "detect",
                "--source",
                ".",
                "--redact",
                "--report-format",
                "json",
                "--report-path",
                "{output}",
            ],
        },
        {
            "name": "trivy",
            "category": "dependencies",
            "required": True,
            "command": [
                "trivy",
                "fs",
                "--scanners",
                "vuln",
                "--skip-db-update",
                "--format",
                "json",
                "--exit-code",
                "0",
                ".",
            ],
        },
        {
            "name": "semgrep",
            "category": "static",
            "required": True,
            "command": [
                "semgrep",
                "--config",
                "security/semgrep-rules.yml",
                "--json",
                "--error",
                ".",
            ],
        },
    ],
}


def load_config(path: Path) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text())
    return DEFAULT_CONFIG


def command_exists(command: list[str]) -> bool:
    return bool(command and shutil.which(command[0]))


def materialize_command(command: list[str], output: Path) -> list[str]:
    return [part.replace("{output}", str(output)) for part in command]


def staged_files() -> list[str] | None:
    """Return staged files (added/copied/modified/renamed) as POSIX paths.

    Returns None when not in a git repo or git is unavailable, so callers can
    fall through to a full scan instead of silently skipping checks.
    """
    if not shutil.which("git"):
        return None
    try:
        proc = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"],
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if proc.returncode != 0:
        return None
    return [p for p in proc.stdout.split("\0") if p]


def matches_any(path: str, patterns: list[str]) -> bool:
    # fnmatch's `*` does not cross `/`, so `**/*.py` matches `src/app.py` but
    # not root-level `app.py`. Treat a leading `**/` as "match anywhere,
    # including the repo root" so a config that uses `**/Cargo.lock` still
    # catches `Cargo.lock` at the top level.
    for pattern in patterns:
        if fnmatch.fnmatch(path, pattern):
            return True
        if pattern.startswith("**/") and fnmatch.fnmatch(path, pattern[3:]):
            return True
    return False


def evaluate_scope(
    config: dict[str, Any],
    files: list[str] | None,
) -> tuple[list[str], dict[str, dict[str, Any]]]:
    """Decide which checks apply to the staged file set.

    Returns (resolved_files, decisions) where `decisions[check_name]` has:
      - run: bool                — should this check execute?
      - reason: str              — human-readable explanation
      - matched_paths: list[str] — staged files that matched this check (or [])

    A None `files` argument means "no staged-file context available" → run every
    check (full scan). Empty list means "git found no staged files" → also run
    every check, because that's the `--all` / verification case.
    """
    decisions: dict[str, dict[str, Any]] = {}
    full_scan = files is None or not files

    trip_globs = list(config.get("trip_all_paths", DEFAULT_TRIP_ALL_PATHS))
    tripped: list[str] = []
    if not full_scan:
        tripped = [p for p in (files or []) if matches_any(p, trip_globs)]

    for check in config.get("checks", []):
        name = check.get("name", "")
        triggers = check.get("triggers")
        if triggers is None:
            triggers = DEFAULT_TRIGGERS.get(name, {"always": True})

        if full_scan:
            decisions[name] = {
                "run": True,
                "reason": "full scan (no staged files or --all)",
                "matched_paths": [],
            }
            continue

        if triggers.get("always"):
            decisions[name] = {
                "run": True,
                "reason": "always-on (e.g. secret scanner)",
                "matched_paths": list(files or []),
            }
            continue

        if tripped:
            decisions[name] = {
                "run": True,
                "reason": f"trip-all path staged ({tripped[0]})",
                "matched_paths": tripped,
            }
            continue

        patterns = triggers.get("paths", [])
        if not patterns:
            decisions[name] = {
                "run": False,
                "reason": "no triggers configured and no staged files match",
                "matched_paths": [],
            }
            continue

        matched = [p for p in (files or []) if matches_any(p, patterns)]
        if matched:
            decisions[name] = {
                "run": True,
                "reason": f"matched {len(matched)} staged file(s)",
                "matched_paths": matched,
            }
        else:
            decisions[name] = {
                "run": False,
                "reason": "no staged file matches this check's triggers",
                "matched_paths": [],
            }

    return list(files or []), decisions


def run_check(check: dict[str, Any], tmpdir: Path, decision: dict[str, Any]) -> dict[str, Any]:
    output = tmpdir / f"{check['name']}.json"
    command = materialize_command(check["command"], output)
    result: dict[str, Any] = {
        "name": check["name"],
        "category": check.get("category", "other"),
        "required": bool(check.get("required", False)),
        "command": command,
        "returncode": None,
        "stdout": "",
        "stderr": "",
        "raw_output": None,
        "findings": [],
        "skipped": not decision["run"],
        "skip_reason": decision["reason"] if not decision["run"] else "",
        "scope_reason": decision["reason"],
        "matched_paths": decision.get("matched_paths", []),
    }

    if not decision["run"]:
        return result

    if not command_exists(command):
        result["tool_error"] = f"Missing tool: {command[0]}"
        return result

    timeout = int(check.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS))
    try:
        proc = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        result["tool_error"] = f"Tool timed out after {timeout}s: {' '.join(command)}"
        result["stdout"] = (exc.stdout or "").strip() if isinstance(exc.stdout, str) else ""
        result["stderr"] = (exc.stderr or "").strip() if isinstance(exc.stderr, str) else ""
        return result
    result["returncode"] = proc.returncode
    result["stdout"] = proc.stdout.strip()
    result["stderr"] = proc.stderr.strip()

    try:
        raw = read_json_output(output, proc.stdout)
    except JsonOutputError as exc:
        result["raw_output"] = None
        result["tool_error"] = str(exc)
        return result
    result["raw_output"] = raw
    result["findings"] = parse_findings(check["name"], check.get("category", "other"), raw)

    if not has_parser(check["name"]):
        result["tool_error"] = (
            f"No parser registered for tool {check['name']!r}; findings cannot be extracted. "
            "Add a parser in scripts/security_check.py or use a supported tool name "
            f"({', '.join(sorted(PARSERS))})."
        )
        return result

    expected = check.get("expected_returncodes")
    if expected is None:
        expected = EXPECTED_RETURNCODES.get(check["name"], DEFAULT_EXPECTED_RETURNCODES)
    if proc.returncode not in tuple(expected):
        result["tool_error"] = (
            result["stderr"]
            or result["stdout"]
            or f"Tool exited with code {proc.returncode}"
        )

    return result


class JsonOutputError(Exception):
    """Raised when a tool's report file or stdout exists but is not valid JSON."""


def read_json_output(output_path: Path, stdout: str) -> Any:
    try:
        if output_path.exists():
            text = output_path.read_text()
            if text.strip():
                return json.loads(text)
        if stdout.strip().startswith(("{", "[")):
            return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise JsonOutputError(f"malformed JSON output: {exc}") from exc
    except OSError as exc:
        raise JsonOutputError(f"failed to read report file: {exc}") from exc
    return None


def finding(
    category: str,
    severity: str,
    tool: str,
    title: str,
    path: str = "",
    hint: str = "",
) -> dict[str, str]:
    return {
        "category": category,
        "severity": normalize_severity(severity),
        "tool": tool,
        "title": title,
        "path": path,
        "hint": hint,
    }


def normalize_severity(value: str | None) -> str:
    if not value:
        return "INFO"
    value = str(value).upper()
    if value == "ERROR":
        return "HIGH"
    if value == "WARNING":
        return "MEDIUM"
    if value in SEVERITY_ORDER:
        return value
    return "INFO"


def parse_findings(tool: str, category: str, raw: Any) -> list[dict[str, str]]:
    if raw is None:
        return []
    parser = PARSERS.get(tool)
    if parser is None:
        return []
    return parser(raw, category, tool)


def has_parser(tool: str) -> bool:
    return tool in PARSERS


def parse_gitleaks(raw: Any, category: str, tool: str) -> list[dict[str, str]]:
    findings = []
    for item in raw if isinstance(raw, list) else []:
        title = item.get("Description") or item.get("RuleID") or "Potential secret"
        path = item.get("File") or ""
        hint = "Rotate exposed credential and remove it from git history if committed."
        findings.append(finding(category, "HIGH", tool, title, path, hint))
    return findings


def parse_trivy(raw: Any, category: str, tool: str) -> list[dict[str, str]]:
    findings = []
    for result in raw.get("Results", []) if isinstance(raw, dict) else []:
        target = result.get("Target", "")
        for vuln in result.get("Vulnerabilities", []) or []:
            title = f"{vuln.get('VulnerabilityID', 'Vulnerability')} in {vuln.get('PkgName', 'package')}"
            fixed = vuln.get("FixedVersion")
            hint = f"Upgrade to {fixed}." if fixed else "Review advisory and upgrade or pin a safe version."
            findings.append(finding(category, vuln.get("Severity", "INFO"), tool, title, target, hint))
    return findings


def parse_semgrep(raw: Any, category: str, tool: str) -> list[dict[str, str]]:
    findings = []
    for item in raw.get("results", []) if isinstance(raw, dict) else []:
        extra = item.get("extra", {})
        check_id = item.get("check_id", "semgrep finding")
        path = item.get("path", "")
        title = extra.get("message") or check_id
        findings.append(finding(category, extra.get("severity", "INFO"), tool, title, path, "Review the matching code and apply the rule guidance."))
    return findings


def parse_bandit(raw: Any, category: str, tool: str) -> list[dict[str, str]]:
    findings = []
    for item in raw.get("results", []) if isinstance(raw, dict) else []:
        title = item.get("issue_text") or item.get("test_id") or "Bandit finding"
        path = item.get("filename", "")
        findings.append(finding(category, item.get("issue_severity", "INFO"), tool, title, path, "Follow Bandit remediation guidance."))
    return findings


def parse_cargo_audit(raw: Any, category: str, tool: str) -> list[dict[str, str]]:
    findings = []
    vulns = raw.get("vulnerabilities", {}) if isinstance(raw, dict) else {}
    for item in vulns.get("list", []) or []:
        advisory = item.get("advisory", {})
        package = item.get("package", {})
        title = f"{advisory.get('id', 'Advisory')} in {package.get('name', 'crate')}"
        severity = advisory.get("severity") or "HIGH"
        findings.append(
            finding(
                category,
                severity,
                tool,
                title,
                "Cargo.lock",
                "Update the affected crate or apply the advisory workaround.",
            )
        )
    return findings


PARSERS = {
    "gitleaks": parse_gitleaks,
    "trivy": parse_trivy,
    "semgrep": parse_semgrep,
    "bandit": parse_bandit,
    "cargo-audit": parse_cargo_audit,
}


def add_tool_error_findings(results: list[dict[str, Any]], no_fail_on_missing_tools: bool) -> None:
    for result in results:
        if result.get("skipped"):
            continue
        error = result.get("tool_error")
        if not error:
            continue
        severity = "INFO" if no_fail_on_missing_tools and "Missing tool:" in error else "HIGH"
        result["findings"].append(
            finding(
                "tool-errors",
                severity,
                result["name"],
                error,
                "",
                "Install the selected tool or mark it optional in security/security-tools.json.",
            )
        )


def summarize(results: list[dict[str, Any]]) -> tuple[list[dict[str, str]], dict[str, Any]]:
    findings = [item for result in results for item in result["findings"]]
    severity_counts = Counter(item["severity"] for item in findings)
    category_counts = Counter(item["category"] for item in findings)
    executed = [r for r in results if not r.get("skipped")]
    skipped = [r for r in results if r.get("skipped")]
    return findings, {
        "checks_run": len(executed),
        "checks_skipped": len(skipped),
        "checks_configured": len(results),
        "finding_count": len(findings),
        "severity_counts": dict(severity_counts),
        "category_counts": dict(category_counts),
    }


def write_reports(json_path: Path, md_path: Path, payload: dict[str, Any]) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    md_path.write_text(render_markdown(payload))


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    scope = payload.get("scope", {})
    lines = [
        "# Security Check Report",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Mode: {scope.get('mode', 'full')}",
        f"- Staged files considered: {len(scope.get('files', []))}",
        f"- Checks run: {summary['checks_run']} of {summary.get('checks_configured', summary['checks_run'])}"
        f" (skipped: {summary.get('checks_skipped', 0)})",
        f"- Findings: {summary['finding_count']}",
        f"- Severity: {format_counter(summary['severity_counts'])}",
        f"- Categories: {format_counter(summary['category_counts'])}",
        "",
        "## Scope Decisions",
        "",
    ]
    for check in payload.get("checks", []):
        status = "skipped" if check.get("skipped") else "ran"
        reason = check.get("scope_reason") or check.get("skip_reason") or ""
        lines.append(f"- **{check['name']}**: {status} — {reason}")
    lines.extend(["", "## Findings", ""])
    if not payload["findings"]:
        lines.append("No findings.")
    for item in payload["findings"]:
        path = f" ({item['path']})" if item.get("path") else ""
        lines.append(f"- **{item['severity']}** [{item['category']}/{item['tool']}] {item['title']}{path}")
        if item.get("hint"):
            lines.append(f"  - Hint: {item['hint']}")
    lines.append("")
    return "\n".join(lines)


def format_counter(counter: dict[str, int]) -> str:
    if not counter:
        return "none"
    ordered = []
    for key in SEVERITY_ORDER:
        if key in counter:
            ordered.append(f"{key}={counter[key]}")
    for key in sorted(set(counter) - set(SEVERITY_ORDER)):
        ordered.append(f"{key}={counter[key]}")
    return ", ".join(ordered)


def print_summary(payload: dict[str, Any], json_path: Path, md_path: Path) -> None:
    summary = payload["summary"]
    scope = payload.get("scope", {})
    print("Security Check Summary")
    print("======================")
    print(f"Mode: {scope.get('mode', 'full')}")
    if scope.get("mode") == "staged":
        print(f"Staged files: {len(scope.get('files', []))}")
    skipped = summary.get("checks_skipped", 0)
    configured = summary.get("checks_configured", summary["checks_run"])
    print(f"Checks run: {summary['checks_run']} of {configured} (skipped: {skipped})")
    if skipped:
        skipped_names = [c["name"] for c in payload.get("checks", []) if c.get("skipped")]
        print(f"Skipped: {', '.join(skipped_names)}")
    print(f"Findings: {summary['finding_count']}")
    print(f"Severity: {format_counter(summary['severity_counts'])}")
    print(f"Categories: {format_counter(summary['category_counts'])}")
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {md_path}")
    if payload["findings"]:
        print("\nTop findings:")
        for item in payload["findings"][:10]:
            path = f" ({item['path']})" if item.get("path") else ""
            print(f"- {item['severity']} [{item['category']}/{item['tool']}] {item['title']}{path}")
            if item.get("hint"):
                print(f"  Hint: {item['hint']}")


def should_fail(findings: list[dict[str, str]], fail_on: list[str]) -> bool:
    fail_set = {normalize_severity(item) for item in fail_on}
    return any(item["severity"] in fail_set for item in findings)


def maybe_force_override(force: bool) -> bool:
    if not force:
        return False
    if not sys.stdin.isatty():
        print(
            "Refusing --force in a non-interactive context. Run from a terminal and type YES.",
            file=sys.stderr,
        )
        return False
    try:
        answer = input("Type YES to override security checks and force-push: ")
    except EOFError:
        print("No confirmation received; bypass denied.", file=sys.stderr)
        return False
    return answer == "YES"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local security checks and print a summary report.")
    parser.add_argument("--config", default="security/security-tools.json", help="Path to tool config JSON.")
    parser.add_argument("--output", default="security/security-report.json", help="Path for JSON report.")
    parser.add_argument("--markdown", default="security/security-report.md", help="Path for Markdown report.")
    parser.add_argument("--force", action="store_true", help="Allow explicit YES-confirmed bypass when findings would fail.")
    parser.add_argument("--no-fail-on-missing-tools", action="store_true", help="Treat missing tools as info for first-run verification.")
    parser.add_argument("--all", dest="all_files", action="store_true", help="Force a full repo scan even when run from pre-commit.")
    parser.add_argument("--staged-only", action="store_true", help="Force staged-file scoping; error if no staged files.")
    extra = os.environ.get("SECURITY_CHECK_ARGS", "").strip()
    argv = sys.argv[1:] + (shlex.split(extra, posix=os.name != "nt") if extra else [])
    args = parser.parse_args(argv)

    config = load_config(Path(args.config))

    scope_env = os.environ.get("SECURITY_CHECK_SCOPE", "").strip().lower()
    if args.all_files or scope_env == "all":
        files: list[str] | None = None
        mode = "full"
    elif args.staged_only or scope_env == "staged":
        files = staged_files()
        if not files:
            print("--staged-only requires a git repo with staged files.", file=sys.stderr)
            return 2
        mode = "staged"
    else:
        files = staged_files()
        mode = "staged" if files else "full"
        if files is None:
            files = []

    _, decisions = evaluate_scope(config, files if mode == "staged" else None)

    with tempfile.TemporaryDirectory(prefix="security-check-") as tmp:
        results = [
            run_check(check, Path(tmp), decisions[check["name"]])
            for check in config.get("checks", [])
        ]

    add_tool_error_findings(results, args.no_fail_on_missing_tools)
    findings, summary = summarize(results)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": {
            "mode": mode,
            "files": files if mode == "staged" else [],
        },
        "summary": summary,
        "findings": findings,
        "checks": results,
    }

    output_path = Path(args.output)
    markdown_path = Path(args.markdown)
    write_reports(output_path, markdown_path, payload)
    print_summary(payload, output_path, markdown_path)

    if should_fail(findings, config.get("fail_on", ["CRITICAL", "HIGH"])):
        if maybe_force_override(args.force):
            print("Override accepted. Security findings remain in the report.")
            return 0
        print("Security checks failed. Fix findings or rerun with --force and type YES to override.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
