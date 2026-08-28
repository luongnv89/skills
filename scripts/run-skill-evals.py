#!/usr/bin/env python3
"""Run a skill's trigger evals: does each prompt make Claude open the skill?

Reads the canonical suite at skills/<name>/evals/evals.json (CONTRIBUTING.md:104)
and replays every `prompt` through `claude -p`, watching the streamed tool calls.
A case triggers when Claude invokes the Skill tool for this skill, or reads its
SKILL.md. `kind: negative-trigger` cases must NOT trigger; every other case must.

A case that declares `files` is SKIPPED: its prompt presupposes on-disk state
("the plan is written -- file the issues"), and replaying it into an empty
directory measures the missing fixture, not the description.

Scope: this measures **triggering only** -- whether the description wins the
prompt. Each case's `expectations` are transcript-level and stay the operator's
job; they are printed as [MANUAL] rather than silently counted as passes.

It evaluates the *installed* skill (~/.claude/skills/<name>), because that is
what Claude actually loads. The description is diffed against this repo's copy
and a mismatch is reported, so a stale install cannot be mistaken for a result
about the catalog.

Usage:
  python3 scripts/run-skill-evals.py <skill-name> [--runs N] [--timeout S]
                                     [--workers N] [--model M] [--json FILE]
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def skill_description(skill_md: Path) -> str:
    text = skill_md.read_text()
    m = re.search(r"^description:\s*(.+?)\s*$", text, re.M)
    return (m.group(1).strip().strip('"') if m else "")


def triggered(events, skill: str, installed: Path) -> bool:
    """A trigger is the Skill tool naming this skill, or a read of its SKILL.md."""
    for e in events:
        if e.get("type") != "assistant":
            continue
        for c in e.get("message", {}).get("content", []):
            if c.get("type") != "tool_use":
                continue
            name, inp = c.get("name", ""), c.get("input", {})
            if name == "Skill" and skill in str(inp.get("skill", "")):
                return True
            if name == "Read" and str(installed) in str(inp.get("file_path", "")):
                return True
    return False


def run_case(case, skill, installed, timeout, model, cwd):
    cmd = ["claude", "-p", case["prompt"],
           "--output-format", "stream-json", "--verbose"]
    if model:
        cmd += ["--model", model]
    # CLAUDECODE guards interactive nesting; a subprocess run is safe without it.
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    try:
        p = subprocess.run(cmd, cwd=cwd, env=env, timeout=timeout,
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or b""
    else:
        out = p.stdout
    events = []
    for ln in out.decode("utf-8", "replace").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            events.append(json.loads(ln))
        except json.JSONDecodeError:
            pass
    return triggered(events, skill, installed)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("skill")
    ap.add_argument("--runs", type=int, default=1, help="runs per case")
    ap.add_argument("--timeout", type=int, default=180, help="seconds per run")
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--model", default=None)
    ap.add_argument("--json", dest="json_out", default=None,
                    help="write the full result set here")
    a = ap.parse_args()

    matches = [p for p in REPO.glob(f"skills/*/{a.skill}") if (p / "SKILL.md").is_file()]
    repo_skill = REPO / "skills" / a.skill
    if not (repo_skill / "SKILL.md").is_file():
        if not matches:
            print(f"✗ no skill at skills/{a.skill}", file=sys.stderr)
            return 2
        repo_skill = matches[0]

    suite = repo_skill / "evals" / "evals.json"
    if not suite.is_file():
        print(f"✗ no eval suite at {suite.relative_to(REPO)}", file=sys.stderr)
        return 2

    if not any(os.access(os.path.join(d, "claude"), os.X_OK)
               for d in os.environ.get("PATH", "").split(os.pathsep) if d):
        print("✗ the 'claude' CLI is required; this runner shells out to it.",
              file=sys.stderr)
        return 1

    installed = Path.home() / ".claude" / "skills" / a.skill
    if not (installed / "SKILL.md").is_file():
        print(f"✗ {a.skill} is not installed at {installed} — Claude can only "
              f"trigger an installed skill. Run install.sh first.", file=sys.stderr)
        return 1
    if skill_description(installed / "SKILL.md") != skill_description(repo_skill / "SKILL.md"):
        print(f"⚠ the installed description differs from {repo_skill.relative_to(REPO)} "
              f"— results describe the INSTALLED copy, not this working tree.",
              file=sys.stderr)

    cases = json.loads(suite.read_text())["evals"]
    results = []
    with tempfile.TemporaryDirectory() as cwd, ThreadPoolExecutor(a.workers) as ex:
        runnable = [c for c in cases if not c.get("files")]
        futures = {
            (c["id"], i): ex.submit(run_case, c, a.skill, installed,
                                    a.timeout, a.model, cwd)
            for c in runnable for i in range(a.runs)
        }
        for c in cases:
            want = c.get("kind") != "negative-trigger"
            row = {"id": c["id"], "name": c.get("name"),
                   "kind": c.get("kind", "happy-path"), "should_trigger": want,
                   "expectations": c.get("expectations", [])}
            if c.get("files"):
                results.append({**row, "skipped": "needs fixtures: "
                                + ", ".join(c["files"]), "pass": None})
                continue
            hits = [futures[(c["id"], i)].result() for i in range(a.runs)]
            rate = sum(hits) / len(hits)
            results.append({**row, "triggers": sum(hits), "runs": len(hits),
                            "pass": (rate >= 0.5) if want else (rate < 0.5)})

    for r in results:
        if r["pass"] is None:
            print(f"  [SKIP] {r['id']} {r['name'] or ''} — {r['skipped']}")
        else:
            print(f"  [{'PASS' if r['pass'] else 'FAIL'}] {r['triggers']}/{r['runs']} "
                  f"expected={r['should_trigger']}  {r['id']} {r['name'] or ''}")
        for e in r["expectations"]:
            print(f"           [MANUAL] {e} — SKIPPED (run by operator)")

    scored = [r for r in results if r["pass"] is not None]
    passed = sum(1 for r in scored if r["pass"])
    skipped = len(results) - len(scored)
    print(f"\nTriggering: {passed}/{len(scored)} passed"
          + (f", {skipped} skipped (fixture-dependent)" if skipped else "")
          + f" ({sum(len(r['expectations']) for r in results)} behavioural "
          f"expectations left to the operator)")
    if a.json_out:
        Path(a.json_out).write_text(json.dumps(
            {"skill": a.skill, "runs_per_case": a.runs, "results": results}, indent=2))
    return 0 if passed == len(scored) else 1


if __name__ == "__main__":
    sys.exit(main())
