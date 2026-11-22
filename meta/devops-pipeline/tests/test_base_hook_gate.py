"""Tests for the CI guard's base-branch gate in references/github-actions.md.

Each test builds a scratch git repository with a base commit and a pull request
commit, then runs, exactly as the reference writes them, the guard's own hook
run and the "Re-run the base branch's hooks if the PR changes them" step, with
scripts/base-hook-gate.py extracted from the same reference. Nothing touches the
network or GitHub, and the user's git config and pre-commit cache are ignored.

Needs pre-commit and PyYAML on the Python running the tests (skipped otherwise):
    python3 -m unittest discover -s meta/devops-pipeline/tests -p 'test_*.py' -v
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REFERENCE = os.path.join(HERE, "..", "..", "..", "skills", "devops-pipeline",
                         "references", "github-actions.md")
STEP_NAME = "Re-run the base branch's hooks if the PR changes them"
GUARD_NAME = "name: Verify hooks were not bypassed"

GIT_ENV = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
               GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.com")

BASE_CONFIG = """\
default_stages: [pre-commit]
repos:
  - repo: local
    hooks:
      - id: no-todo
        name: no TODO in src
        language: pygrep
        entry: TODO
        files: ^src/
      - id: forbidden
        name: no FORBIDDEN in src
        language: system
        entry: bash scripts/check.sh
        files: ^src/
      - id: suite
        name: push-stage suite
        language: system
        entry: "true"
        pass_filenames: false
        always_run: true
        stages: [pre-push]
"""
CHECK_SH = 'if grep -l FORBIDDEN "$@"; then exit 1; fi\n'


def reference():
    with open(REFERENCE, encoding="utf-8") as f:
        return f.read()


def gate_script(text):
    section = text.split("## The base branch judges hook changes", 1)[1]
    return re.search(r"```python\n(.*?)```", section, re.S).group(1)


def gate_steps(text):
    """Every copy of the step's run block, dedented to plain shell."""
    blocks = []
    for part in text.split(f"- name: {STEP_NAME}\n")[1:]:
        lines = part.splitlines()
        assert lines[0].strip() == "run: |", lines[0]
        body = []
        for line in lines[1:]:
            if not line.startswith(" " * 10):
                break
            body.append(line[10:])
        blocks.append("\n".join(body) + "\n")
    return blocks


def guard_jobs(text):
    """The body of each guard job inside the reference's YAML blocks."""
    jobs = []
    for block in re.findall(r"```yaml\n(.*?)```", text, re.S):
        for m in re.finditer(r"^  hooks:\n(.*?)(?=^  [a-z][\w-]*:\n|\Z)", block, re.S | re.M):
            jobs.append(m.group(1))
    return jobs


@unittest.skipUnless(shutil.which("pre-commit"), "pre-commit is not installed")
class GateOnScratchRepo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        text = reference()
        cls.script = gate_script(text)
        cls.step = gate_steps(text)[0]

    def setUp(self):
        try:
            import yaml  # noqa: F401  the gate's only dependency
        except ImportError:
            self.skipTest("PyYAML is not installed")
        self.tmp = tempfile.mkdtemp()
        self.repo = os.path.join(self.tmp, "repo")
        self.runner_temp = os.path.join(self.tmp, "runner")
        os.makedirs(self.repo)
        os.makedirs(self.runner_temp)
        bindir = os.path.join(self.tmp, "bin")
        os.makedirs(bindir)
        os.symlink(sys.executable, os.path.join(bindir, "python"))  # the step calls `python`
        self.env = dict(GIT_ENV, RUNNER_TEMP=self.runner_temp,
                        PRE_COMMIT_HOME=os.path.join(self.tmp, "pre-commit-cache"),
                        PATH=bindir + os.pathsep + os.environ["PATH"])
        self.git("init", "-q", "-b", "main")
        self.write({".pre-commit-config.yaml": BASE_CONFIG, "scripts/check.sh": CHECK_SH,
                    "scripts/base-hook-gate.py": self.script, "src/app.txt": "ok\n"})
        self.base = self.commit("base")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, env=self.env, check=True,
                              capture_output=True, text=True).stdout.strip()

    def write(self, files):
        for rel, body in files.items():
            path = os.path.join(self.repo, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(body)

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-qm", message)
        return self.git("rev-parse", "HEAD")

    def pull_request(self, files, remove=()):
        self.git("checkout", "-qb", "pr")
        self.write(files)
        for rel in remove:
            os.remove(os.path.join(self.repo, rel))
        self.commit("pr")

    def guard(self):
        """The guard's own run: both stages with the PR's config."""
        codes = []
        for stage in ("pre-commit", "pre-push"):
            codes.append(subprocess.run(
                ["pre-commit", "run", "--hook-stage", stage, "--from-ref", self.base, "--to-ref", "HEAD"],
                cwd=self.repo, env=self.env, capture_output=True, text=True).returncode)
        return max(codes)

    def gate(self, stages="pre-commit pre-push"):
        script = (self.step.replace("${{ github.event.pull_request.base.sha }}", self.base)
                  .replace("${{ matrix.stages || 'pre-commit pre-push' }}", stages))
        run = subprocess.run(["bash", "-e", "-c", script], cwd=self.repo, env=self.env,
                             capture_output=True, text=True)
        return run.returncode, run.stdout + run.stderr

    def edited_config(self, old, new):
        assert old in BASE_CONFIG
        return {".pre-commit-config.yaml": BASE_CONFIG.replace(old, new)}

    # Without a hook-config change ------------------------------------------

    def test_source_only_change_skips_the_gate(self):
        self.pull_request({"src/app.txt": "ok\nstill ok\n"})
        self.assertEqual(self.guard(), 0)
        code, out = self.gate()
        self.assertEqual(code, 0, out)
        self.assertIn("skipped", out)
        self.assertNotIn("no TODO in src", out)  # no hook ran a second time

    def test_source_only_violation_still_fails_the_guard_itself(self):
        self.pull_request({"src/app.txt": "TODO\n"})
        self.assertNotEqual(self.guard(), 0)
        self.assertEqual(self.gate()[0], 0)  # the gate adds nothing here

    # With a hook-config change ----------------------------------------------

    def test_removed_hook_fails_the_gate(self):
        removed = self.edited_config(
            "      - id: no-todo\n        name: no TODO in src\n        language: pygrep\n"
            "        entry: TODO\n        files: ^src/\n", "")
        self.pull_request({**removed, "src/app.txt": "TODO\n"})
        self.assertEqual(self.guard(), 0)  # the PR's own config no longer checks it
        code, out = self.gate()
        self.assertEqual(code, 1, out)
        self.assertIn("runs hook 'no-todo' on pre-commit; this PR removes it", out)
        self.assertRegex(out, r"no TODO in src\.+Failed")

    def test_removed_hook_fails_even_when_the_code_passes_it(self):
        self.pull_request(self.edited_config("        entry: TODO\n        files: ^src/\n",
                                             "        entry: TODO\n        files: ^nothing/\n"
                                             "        stages: [manual]\n"))
        code, out = self.gate()
        self.assertEqual(code, 1, out)
        self.assertIn("runs hook 'no-todo' on pre-commit; this PR removes it", out)

    def test_removed_push_hook_fails_only_the_push_leg(self):
        self.pull_request(self.edited_config("        stages: [pre-push]\n", "        stages: [manual]\n"))
        self.assertEqual(self.gate("pre-commit")[0], 0)
        code, out = self.gate("pre-push")
        self.assertEqual(code, 1, out)
        self.assertIn("runs hook 'suite' on pre-push; this PR removes it", out)

    def test_neutered_hook_script_fails_on_the_base_script(self):
        self.pull_request({"scripts/check.sh": "exit 0\n", "src/app.txt": "FORBIDDEN\n"})
        self.assertEqual(self.guard(), 0)
        code, out = self.gate()
        self.assertEqual(code, 1, out)
        self.assertNotIn("this PR removes it", out)
        self.assertRegex(out, r"no FORBIDDEN in src\.+Failed")

    def test_weakened_gate_script_is_not_used(self):
        removed = self.edited_config("      - id: no-todo\n", "      - id: no-todo-renamed\n")
        self.pull_request({**removed, "scripts/base-hook-gate.py": "import sys\nsys.exit(0)\n"})
        code, out = self.gate()
        self.assertEqual(code, 1, out)
        self.assertIn("runs hook 'no-todo' on pre-commit; this PR removes it", out)

    def test_added_hook_with_clean_code_passes(self):
        added = self.edited_config(
            "      - id: suite\n",
            "      - id: no-fixme\n        name: no FIXME\n        language: pygrep\n"
            "        entry: FIXME\n        files: ^src/\n      - id: suite\n")
        self.pull_request({**added, "src/app.txt": "ok\nclean\n"})
        self.assertEqual(self.guard(), 0)
        code, out = self.gate()
        self.assertEqual(code, 0, out)
        self.assertIn("the PR changes .pre-commit-config.yaml", out)
        self.assertRegex(out, r"no TODO in src\.+Passed")

    def test_workflow_only_change_runs_the_base_hooks(self):
        self.pull_request({".github/workflows/ci.yml": "name: CI\n"})
        code, out = self.gate()
        self.assertEqual(code, 0, out)
        self.assertIn("the PR changes .github/workflows/ci.yml", out)

    def test_deleted_config_fails_on_every_base_hook(self):
        self.pull_request({}, remove=[".pre-commit-config.yaml"])
        code, out = self.gate()
        self.assertEqual(code, 1, out)
        for hook in ("no-todo", "forbidden", "suite"):
            self.assertIn(f"runs hook '{hook}'", out)

    def test_first_pull_request_adding_the_gate_runs_its_own_copy(self):
        self.git("rm", "-q", "scripts/base-hook-gate.py")
        self.base = self.commit("base without the gate")
        self.pull_request({"scripts/base-hook-gate.py": self.script})
        code, out = self.gate()
        self.assertEqual(code, 0, out)
        self.assertIn("the PR changes scripts/base-hook-gate.py", out)


class TemplatesKeepTheGuardNames(unittest.TestCase):
    def test_every_guard_job_ends_with_the_same_gate_step(self):
        text = reference()
        jobs = guard_jobs(text)
        self.assertGreaterEqual(len(jobs), 7)
        templates = [job for job in jobs if STEP_NAME in job]
        self.assertEqual(len(templates), len(jobs) - 1)  # the intro excerpt has no step
        for job in templates:
            self.assertIn(GUARD_NAME, job)
            last_step = job.rstrip().rsplit("\n      - ", 1)[1]
            self.assertTrue(last_step.startswith(f"name: {STEP_NAME}"), last_step[:80])
        self.assertEqual(len(set(gate_steps(text))), 1)

    def test_guard_job_id_and_name_are_unchanged(self):
        text = reference()
        self.assertEqual(text.count(GUARD_NAME), len(guard_jobs(text)))
        self.assertEqual(text.count("\n  hooks:\n"), len(guard_jobs(text)))


if __name__ == "__main__":
    unittest.main()
