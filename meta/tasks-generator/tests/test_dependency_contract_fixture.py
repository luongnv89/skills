"""Run the focused dependency contract fixture as a unittest.

    python3 -m unittest discover -s meta/tasks-generator/tests -p 'test_*.py'
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE = Path(__file__).with_name("contract_fixture.py")


class DependencyContractFixture(unittest.TestCase):
    def test_contract_fixture_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(FIXTURE), str(REPO_ROOT)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("contract fixture: PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
