from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bench.run_benchmark import grade


class RunBenchmarkTests(unittest.TestCase):
    def test_grade_records_timeout_as_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            task = Path(directory) / "task"
            workspace = Path(directory) / "workspace"
            task.mkdir()
            workspace.mkdir()
            (task / "grader.py").write_text(
                "import time\ntime.sleep(2)\n", encoding="utf-8"
            )
            passed, output = grade(task, workspace, timeout=1)
            self.assertFalse(passed)
            self.assertEqual(output, "grader timed out after 1 seconds")


if __name__ == "__main__":
    unittest.main()
