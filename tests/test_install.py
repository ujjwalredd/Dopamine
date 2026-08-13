from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


class InstallTests(unittest.TestCase):
    def test_project_install_for_both_agents_and_overwrite_protection(self) -> None:
        root = Path(__file__).resolve().parents[1]
        installer = root / "scripts/install.sh"
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            command = [
                str(installer), "--agent", "all", "--scope", "project",
                "--project", str(project),
            ]
            first = subprocess.run(command, text=True, capture_output=True, check=False)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertTrue((project / ".agents/skills/dopamine/SKILL.md").is_file())
            self.assertTrue((project / ".claude/skills/dopamine/SKILL.md").is_file())

            second = subprocess.run(command, text=True, capture_output=True, check=False)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("Refusing to overwrite", second.stderr)

    def test_rejects_filesystem_root_as_project(self) -> None:
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [
                str(root / "scripts/install.sh"), "--agent", "codex",
                "--scope", "project", "--project", "/",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("filesystem root", result.stderr)


if __name__ == "__main__":
    unittest.main()
