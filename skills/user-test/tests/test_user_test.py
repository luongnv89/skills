"""Unit tests for scripts/user_test.py (temp dirs, local processes, no network)."""
import json
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "user_test.py"


def ut(*args, cwd=None):
    proc = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True, cwd=cwd)
    data = json.loads(proc.stdout) if proc.stdout.strip().startswith("{") else None
    return proc.returncode, data, proc.stderr


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


FEATURES = {
    "app": {"name": "Demo", "type": "web", "entry": "http://127.0.0.1/"},
    "areas": [
        {"id": "todos", "name": "Todos", "journeys": [
            {"id": "todos-add", "goal": "Add a todo", "entry": "/", "source": "app.js:1"},
            {"id": "todos-share", "goal": "Share", "entry": "/", "source": "app.js:9",
             "side_effects": ["emails the team"]}]},
        {"id": "admin", "name": "Admin", "in_scope": False, "journeys": []},
    ],
}


def finding(**over):
    base = {"id": "todos-1", "title": "Blank todo can be added", "kind": "defect", "category": "functional",
            "severity": "medium", "impact": "Users get blank items.", "complexity": "simple",
            "complexity_reason": "One check.", "journey": "todos-add", "where": "/ (Add)",
            "steps": ["Open /", "Click Add"], "expected": "Refused", "actual": "Blank item added",
            "evidence": ["evidence/todos/blank.png"]}
    base.update(over)
    return base


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.root = self.tmp / "project"
        self.root.mkdir()

    def init(self, *extra):
        code, data, err = ut("init", "--root", self.root, *extra)
        self.assertEqual(code, 0, err)
        return Path(data["run_dir"])

    def write_area(self, run_dir, coverage, findings, area="todos"):
        (run_dir / "evidence" / area).mkdir(parents=True, exist_ok=True)
        (run_dir / "evidence" / area / "blank.png").write_bytes(b"\x89PNG")
        (run_dir / "areas" / f"{area}.json").write_text(json.dumps(
            {"area": area, "coverage": coverage, "findings": findings, "perf": [], "notes": []}))


class InitTests(Base):
    def test_creates_run_dir_and_run_json(self):
        run_dir = self.init("--scope", "search, filter", "--fix", "off")
        run = json.loads((run_dir / "run.json").read_text())
        self.assertEqual(run["scope"], ["search", "filter"])
        self.assertEqual(run["fix_mode"], "off")
        for sub in ("evidence", "areas", "logs", "checkpoints", "work"):
            self.assertTrue((run_dir / sub).is_dir())

    @unittest.skipUnless(shutil.which("git"), "git not installed")
    def test_excludes_run_root_from_git_once(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.init()
        self.init()
        exclude = (self.root / ".git" / "info" / "exclude").read_text()
        self.assertEqual(exclude.count(".user-test/"), 1)

    def test_remote_forces_fix_off_and_needs_url(self):
        code, _, err = ut("init", "--root", self.root, "--branch", "remote")
        self.assertEqual(code, 2)
        self.assertIn("--url", err)
        run_dir = self.init("--branch", "remote", "--url", "http://127.0.0.1:1/", "--fix", "on")
        self.assertEqual(json.loads((run_dir / "run.json").read_text())["fix_mode"], "off")


class DetectTests(Base):
    def test_node_project(self):
        (self.root / "package.json").write_text(json.dumps({
            "scripts": {"dev": "vite", "build": "vite build", "test": "vitest run"},
            "devDependencies": {"vite": "5"}}))
        (self.root / "package-lock.json").write_text("{}")
        code, data, _ = ut("detect", "--root", self.root)
        self.assertEqual(code, 0)
        self.assertEqual(data["install"][0]["cmd"], "npm ci")
        self.assertTrue(data["deps_missing"])
        self.assertEqual(data["start"][0], {"cmd": "npm run dev", "source": "package.json scripts.dev",
                                            "confidence": "high", "port": 5173})
        self.assertEqual(data["build"][0]["cmd"], "npm run build")
        self.assertEqual(data["test"][0]["cmd"], "npm test")
        self.assertIn("web", data["types"])

    def test_django_and_readme_commands(self):
        (self.root / "manage.py").write_text("")
        (self.root / "README.md").write_text("Run it:\n\n```\n$ python manage.py runserver\n```\n")
        code, data, _ = ut("detect", "--root", self.root)
        self.assertEqual(code, 0)
        self.assertEqual(data["start"][0]["port"], 8000)
        self.assertEqual(data["readme_commands"], [{"line": 4, "cmd": "python manage.py runserver"}])

    def test_compose_is_a_service_not_a_start_command(self):
        (self.root / "compose.yaml").write_text("services: {db: {image: postgres}}\n")
        code, data, _ = ut("detect", "--root", self.root)
        self.assertEqual(data["start"], [])
        self.assertEqual(data["services"]["stop"], "docker compose stop <service>")
        self.assertTrue(any("never `docker compose down`" in n for n in data["notes"]))

    def test_nothing_found(self):
        code, data, _ = ut("detect", "--root", self.root)
        self.assertEqual(code, 0)
        self.assertEqual(data["start"], [])
        self.assertTrue(any("No start command" in n for n in data["notes"]))


class AppTests(Base):
    def test_start_wait_status_stop(self):
        run_dir = self.init()
        port = free_port()
        code, data, err = ut("app", "start", "--run-dir", run_dir, "--port", port,
                             "--cmd", f"{sys.executable} -m http.server {port} --bind 127.0.0.1")
        self.assertEqual(code, 0, err)
        pid = data["pid"]
        self.addCleanup(lambda: ut("app", "stop", "--run-dir", run_dir))
        code, data, err = ut("app", "wait", "--run-dir", run_dir, "--timeout", 20)
        self.assertEqual(code, 0, err)
        self.assertTrue(data["ready"])
        self.assertEqual(data["status"], 200)
        run = json.loads((run_dir / "run.json").read_text())
        self.assertTrue(run["app"]["ready"])
        self.assertIn("http.server", run["app"]["start_cmd"])
        code, data, _ = ut("app", "status", "--run-dir", run_dir)
        self.assertEqual(data["running"], ["app"])
        code, data, _ = ut("app", "start", "--run-dir", run_dir, "--cmd", "sleep 5")
        self.assertEqual(code, 3, "a second start under the same name must conflict")
        code, data, _ = ut("app", "stop", "--run-dir", run_dir)
        self.assertEqual(code, 0)
        self.assertIn(data["stopped"]["app"], ("stopped", "killed"))
        time.sleep(0.3)
        code, data, _ = ut("app", "status", "--run-dir", run_dir)
        self.assertEqual(data["running"], [])
        with self.assertRaises(OSError):
            socket.create_connection(("127.0.0.1", port), timeout=0.5).close()
        self.assertGreater(pid, 0)

    def test_wait_finds_url_in_log(self):
        run_dir = self.init()
        port = free_port()
        code, _, err = ut("app", "start", "--run-dir", run_dir, "--name", "web",
                          "--cmd", f"{sys.executable} -u -m http.server {port} --bind 127.0.0.1")
        self.assertEqual(code, 0, err)
        self.addCleanup(lambda: ut("app", "stop", "--run-dir", run_dir))
        code, data, err = ut("app", "wait", "--run-dir", run_dir, "--name", "web", "--timeout", 20)
        self.assertEqual(code, 0, err)
        self.assertEqual(data["url"], f"http://127.0.0.1:{port}/")

    def test_start_reports_immediate_exit_with_log_tail(self):
        run_dir = self.init()
        code, _, err = ut("app", "start", "--run-dir", run_dir,
                          "--cmd", f"{sys.executable} -c \"import sys; print('boom: missing KEY'); sys.exit(3)\"")
        self.assertEqual(code, 1)
        self.assertIn("boom: missing KEY", err)
        self.assertIn("fix:", err)
        self.assertIs(json.loads((run_dir / "run.json").read_text())["app"]["ready"], False)
        code, _, err = ut("app", "wait", "--run-dir", run_dir, "--timeout", 30)
        self.assertEqual(code, 1, "waiting on a process that already exited must fail at once")

    def test_port_in_use_is_a_conflict(self):
        run_dir = self.init()
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            sock.listen()
            code, _, err = ut("app", "start", "--run-dir", run_dir, "--port", sock.getsockname()[1],
                              "--cmd", "sleep 5")
        self.assertEqual(code, 3)
        self.assertIn("already in use", err)

    def test_wait_without_url_or_process_is_bad_input(self):
        run_dir = self.init()
        code, _, err = ut("app", "wait", "--run-dir", run_dir, "--timeout", 1)
        self.assertEqual(code, 2)
        self.assertIn("--url", err)


class FeatureAndCollectTests(Base):
    def setUp(self):
        super().setUp()
        self.run_dir = self.init()
        (self.run_dir / "features.json").write_text(json.dumps(FEATURES))

    def test_check_features_summary_and_errors(self):
        code, data, _ = ut("check-features", "--run-dir", self.run_dir)
        self.assertEqual(code, 0)
        self.assertEqual(data["journeys"], 2)
        self.assertEqual(data["in_scope_areas"], 1)
        bad = {"areas": [{"id": "A", "name": "x", "journeys": [{"id": "j", "goal": "", "entry": "/", "source": "s"},
                                                               {"id": "j", "goal": "g", "entry": "/", "source": "s"}]}]}
        (self.run_dir / "features.json").write_text(json.dumps(bad))
        code, _, err = ut("check-features", "--run-dir", self.run_dir)
        self.assertEqual(code, 1)
        self.assertIn("kebab-case", err)
        self.assertIn("duplicated", err)
        self.assertIn("'goal'", err)

    def test_focus_name_must_match_an_area(self):
        ut("update", "--run-dir", self.run_dir, "--json", '{"scope": ["todos", "checkout"]}')
        code, _, err = ut("check-features", "--run-dir", self.run_dir)
        self.assertEqual(code, 1)
        self.assertIn("'checkout' matches no in-scope area", err)

    def test_collect_requires_every_journey(self):
        self.write_area(self.run_dir, [{"journey": "todos-add", "status": "pass"}], [])
        code, _, err = ut("collect", "--run-dir", self.run_dir)
        self.assertEqual(code, 1)
        self.assertIn("todos-share", err)
        self.assertFalse((self.run_dir / "findings.json").exists())

    def test_collect_checks_evidence_and_fail_rows(self):
        self.write_area(self.run_dir, [
            {"journey": "todos-add", "status": "fail", "findings": []},
            {"journey": "todos-share", "status": "blocked", "reason": ""}],
            [finding(evidence=["evidence/todos/missing.png"])])
        code, _, err = ut("collect", "--run-dir", self.run_dir)
        self.assertEqual(code, 1)
        self.assertIn("does not exist", err)
        self.assertIn("must list the finding ids", err)
        self.assertIn("needs a reason", err)

    def test_collect_merges_and_keeps_fix_state(self):
        coverage = [{"journey": "todos-add", "status": "fail", "findings": ["todos-1"]},
                    {"journey": "todos-share", "status": "blocked", "reason": "needs approval: emails the team"},
                    {"journey": "todos-bulk", "status": "pass"}]
        self.write_area(self.run_dir, coverage, [finding()])
        code, data, err = ut("collect", "--run-dir", self.run_dir, "--area", "todos")
        self.assertEqual(code, 0, err)
        self.assertFalse(data["written"])
        self.assertFalse((self.run_dir / "findings.json").exists())
        code, data, err = ut("collect", "--run-dir", self.run_dir)
        self.assertEqual(code, 0, err)
        self.assertTrue(data["written"])
        self.assertEqual(data["discovered_journeys"], ["todos-bulk"])
        code, _, err = ut("update", "--run-dir", self.run_dir, "--finding", "todos-1",
                          "--json", '{"status": "fix-failed", "fix": {"restored": true}}')
        self.assertEqual(code, 0, err)
        ut("collect", "--run-dir", self.run_dir)
        store = json.loads((self.run_dir / "findings.json").read_text())
        self.assertEqual(store["findings"][0]["status"], "fix-failed")
        self.assertTrue(store["findings"][0]["fix"]["restored"])

    def test_performance_finding_needs_metric(self):
        self.write_area(self.run_dir, [{"journey": "todos-add", "status": "fail", "findings": ["todos-1"]},
                                       {"journey": "todos-share", "status": "skipped", "reason": "x"}],
                        [finding(category="performance")])
        code, _, err = ut("collect", "--run-dir", self.run_dir)
        self.assertEqual(code, 1)
        self.assertIn("metric", err)


class UpdateTests(Base):
    def test_patch_run_and_reject_bad_values(self):
        run_dir = self.init()
        code, _, _ = ut("update", "--run-dir", run_dir, "--json", '{"driver": "playwright-mcp"}')
        self.assertEqual(code, 0)
        self.assertEqual(json.loads((run_dir / "run.json").read_text())["driver"], "playwright-mcp")
        code, _, err = ut("update", "--run-dir", run_dir, "--json", "{not json")
        self.assertEqual(code, 2)
        self.assertIn("--json-file", err)
        code, _, err = ut("update", "--run-dir", run_dir, "--finding", "x-1", "--json", "{}")
        self.assertEqual(code, 2)
        self.assertIn("collect", err)

    def test_note_appends(self):
        run_dir = self.init("--branch", "remote", "--url", "http://127.0.0.1:1/")
        before = len(json.loads((run_dir / "run.json").read_text())["notes"])
        ut("update", "--run-dir", run_dir, "--note", "ran inline")
        notes = json.loads((run_dir / "run.json").read_text())["notes"]
        self.assertEqual(len(notes), before + 1, "a note must append, not replace")
        self.assertEqual(notes[-1], "ran inline")

    def test_add_finding_rejects_incomplete(self):
        run_dir = self.init()
        code, _, err = ut("update", "--run-dir", run_dir, "--add-finding", "--json", '{"id": "run-1"}')
        self.assertEqual(code, 2)
        self.assertIn("'title'", err)

    def test_add_finding_goes_to_run_area(self):
        run_dir = self.init()
        (run_dir / "evidence" / "todos").mkdir(parents=True)
        (run_dir / "evidence" / "todos" / "blank.png").write_bytes(b"x")
        code, data, _ = ut("update", "--run-dir", run_dir, "--add-finding",
                           "--json", json.dumps(finding(id="run-1", journey=None)))
        self.assertEqual(code, 0)
        self.assertTrue((run_dir / "areas" / "_run.json").exists())


class BuildCheckTests(Base):
    def test_records_exits_and_fails_on_nonzero(self):
        run_dir = self.init()
        code, data, _ = ut("build-check", "--run-dir", run_dir, "--label", "baseline",
                           "--build", "echo built", "--test", "echo 1 failed; exit 1")
        self.assertEqual(code, 1)
        self.assertEqual(data["build"]["exit"], 0)
        self.assertEqual(data["test"]["exit"], 1)
        self.assertIn("1 failed", data["test"]["tail"])
        run = json.loads((run_dir / "run.json").read_text())
        self.assertEqual(run["checks"]["baseline"]["test"]["exit"], 1)
        self.assertNotIn("tail", run["checks"]["baseline"]["test"])
        code, _, _ = ut("build-check", "--run-dir", run_dir, "--label", "Bad Label", "--build", "true")
        self.assertEqual(code, 2)


class CheckpointTests(Base):
    def test_save_diff_restore_round_trip(self):
        run_dir = self.init()
        src = self.root / "src" / "app.py"
        src.parent.mkdir()
        src.write_text("a = 1\nb = 2\n")
        code, data, _ = ut("checkpoint", "save", "--run-dir", run_dir, "--fix", "todos-1", "src/app.py", "src/new.py")
        self.assertEqual(code, 0)
        self.assertEqual((data["saved"], data["new"]), (["src/app.py"], ["src/new.py"]))
        src.write_text("a = 1\nb = 3\n")
        (self.root / "src" / "new.py").write_text("x = 1\n")
        code, data, _ = ut("checkpoint", "save", "--run-dir", run_dir, "--fix", "todos-1", "src/app.py")
        self.assertEqual(data["skipped"], ["src/app.py"], "a second save must keep the first copy")
        code, data, _ = ut("checkpoint", "diff", "--run-dir", run_dir, "--fix", "todos-1")
        self.assertEqual(code, 0)
        self.assertEqual(data["lines_changed"], 3)
        self.assertTrue((run_dir / data["diff"]).is_file())
        code, data, _ = ut("checkpoint", "restore", "--run-dir", run_dir, "--fix", "todos-1")
        self.assertEqual(code, 0)
        self.assertEqual(src.read_text(), "a = 1\nb = 2\n")
        self.assertFalse((self.root / "src" / "new.py").exists())
        self.assertEqual(data["deleted"], ["src/new.py"])

    def test_rejects_paths_outside_project_and_in_run_dir(self):
        run_dir = self.init()
        outside = self.tmp / "outside.txt"
        outside.write_text("x")
        code, _, err = ut("checkpoint", "save", "--run-dir", run_dir, "--fix", "f-1", str(outside))
        self.assertEqual(code, 2)
        self.assertIn("outside the project root", err)
        code, _, err = ut("checkpoint", "save", "--run-dir", run_dir, "--fix", "f-1", "../outside.txt")
        self.assertEqual(code, 2)
        code, _, err = ut("checkpoint", "save", "--run-dir", run_dir, "--fix", "f-1",
                          str(run_dir.relative_to(self.root) / "run.json"))
        self.assertEqual(code, 2)
        code, _, err = ut("checkpoint", "restore", "--run-dir", run_dir, "--fix", "never-saved")
        self.assertEqual(code, 2)


class ReportTests(Base):
    def setUp(self):
        super().setUp()
        self.run_dir = self.init()
        (self.run_dir / "features.json").write_text(json.dumps(FEATURES))

    def collect(self, findings, share_status="blocked"):
        coverage = [{"journey": "todos-add", "status": "fail", "findings": [f["id"] for f in findings]},
                    {"journey": "todos-share", "status": share_status,
                     "reason": "needs approval: emails the team" if share_status != "pass" else ""}]
        self.write_area(self.run_dir, coverage, findings)
        code, _, err = ut("collect", "--run-dir", self.run_dir)
        self.assertEqual(code, 0, err)

    def test_refuses_open_finding_without_plan(self):
        self.collect([finding()])
        code, _, err = ut("report", "--run-dir", self.run_dir)
        self.assertEqual(code, 1)
        self.assertIn("plan.approach", err)
        self.assertFalse((self.run_dir / "report.md").exists())

    def test_refuses_unverified_fix_and_missing_final_check(self):
        self.collect([finding()])
        ut("update", "--run-dir", self.run_dir, "--finding", "todos-1", "--json",
           '{"status": "fixed-verified", "fix": {"files": ["app.js"], "build": {"exit": 0}}}')
        code, _, err = ut("report", "--run-dir", self.run_dir)
        self.assertEqual(code, 1)
        self.assertIn("verifier", err)
        self.assertIn("checks.final", err)

    def test_writes_reports_with_safe_payload(self):
        hostile = finding(title="Title </script><script>alert(1)</script>", id="todos-1")
        self.collect([hostile, finding(id="todos-2", kind="improvement", category="ux", severity="low")])
        plan = '{"plan": {"approach": "Validate titles", "effort": "S", "risk": "low"}}'
        for fid in ("todos-1", "todos-2"):
            ut("update", "--run-dir", self.run_dir, "--finding", fid, "--json", plan)
        code, data, err = ut("report", "--run-dir", self.run_dir)
        self.assertEqual(code, 0, err)
        self.assertEqual(data["result"], "PARTIAL")
        self.assertIn("Approve or decline the side-effect journeys: todos-share.", data["decision"])
        html = (self.run_dir / "report.html").read_text()
        self.assertEqual(html.count("</script>"), 2, "finding text must not close the data script")
        self.assertIn("f-reset", html)
        markdown = (self.run_dir / "report.md").read_text()
        self.assertTrue(markdown.startswith("# User test report: Demo"))
        self.assertIn("**Result: PARTIAL**", markdown)
        self.assertIn("## Plan for open findings", markdown)
        self.assertIn("Not tested: todos-share (blocked)", markdown)

    def test_fixed_needs_no_new_test_failures(self):
        self.collect([finding()])
        (self.run_dir / "evidence" / "todos" / "v.png").write_bytes(b"x")
        ut("build-check", "--run-dir", self.run_dir, "--label", "final", "--build", "true")
        patch = {"status": "fixed-verified", "fix": {"files": ["a"], "build": {"exit": 0}, "tests": {"exit": 1},
                                                     "verification": {"verdict": "pass", "evidence": ["evidence/todos/v.png"]}}}
        ut("update", "--run-dir", self.run_dir, "--finding", "todos-1", "--json", json.dumps(patch))
        code, _, err = ut("report", "--run-dir", self.run_dir)
        self.assertEqual(code, 1)
        self.assertIn("new_failures", err)

    def test_zero_tested_journeys_is_blocked(self):
        self.collect([finding()], share_status="skipped")
        store = json.loads((self.run_dir / "findings.json").read_text())
        for row in store["coverage"]:
            row.update(status="blocked", reason="no driver", findings=[])
        (self.run_dir / "findings.json").write_text(json.dumps(store))
        ut("update", "--run-dir", self.run_dir, "--finding", "todos-1", "--json",
           '{"plan": {"approach": "a", "effort": "S", "risk": "low"}}')
        code, data, err = ut("report", "--run-dir", self.run_dir)
        self.assertEqual(code, 0, err)
        self.assertEqual(data["result"], "BLOCKED")

    def test_complete_when_every_journey_ran(self):
        self.collect([finding()], share_status="pass")
        evidence = self.run_dir / "evidence" / "todos" / "verify.png"
        evidence.write_bytes(b"\x89PNG")
        ut("build-check", "--run-dir", self.run_dir, "--label", "final", "--build", "true", "--test", "true")
        patch = {"status": "fixed-verified", "fix": {"files": ["app.js"], "build": {"exit": 0},
                                                     "tests": {"exit": 0, "new_failures": 0},
                                                     "verification": {"verdict": "pass",
                                                                      "evidence": ["evidence/todos/verify.png"]}}}
        ut("update", "--run-dir", self.run_dir, "--finding", "todos-1", "--json", json.dumps(patch))
        code, data, err = ut("report", "--run-dir", self.run_dir)
        self.assertEqual(code, 0, err)
        self.assertEqual(data["result"], "COMPLETE")
        self.assertTrue(data["decision"][0].startswith("Review and commit the 1 verified fix"))
        ut("update", "--run-dir", self.run_dir, "--json", '{"commits": ["abc1234"]}')
        code, data, _ = ut("report", "--run-dir", self.run_dir)
        self.assertIn("committed as: abc1234", data["decision"][0])

    def test_blocked_when_app_never_started(self):
        ut("update", "--run-dir", self.run_dir, "--json", '{"app": {"ready": false}}')
        (self.run_dir / "features.json").unlink()
        (self.run_dir / "evidence" / "_run").mkdir(parents=True)
        (self.run_dir / "evidence" / "_run" / "app.log.txt").write_text("TypeError")
        launch = finding(id="run-1", journey=None, category="crash", severity="critical",
                         evidence=["evidence/_run/app.log.txt"],
                         plan={"approach": "Fix seed()", "effort": "S", "risk": "low"})
        ut("update", "--run-dir", self.run_dir, "--add-finding", "--json", json.dumps(launch))
        code, _, err = ut("collect", "--run-dir", self.run_dir)
        self.assertEqual(code, 0, err)
        code, data, err = ut("report", "--run-dir", self.run_dir)
        self.assertEqual(code, 0, err)
        self.assertEqual(data["result"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
