from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


class InstallTests(unittest.TestCase):
    def test_project_install_for_all_native_targets_and_overwrite_protection(self) -> None:
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
            self.assertTrue((project / ".opencode/skills/dopamine/SKILL.md").is_file())
            self.assertTrue((project / ".grok/skills/dopamine/SKILL.md").is_file())
            self.assertTrue((project / ".openclaw/skills/dopamine/SKILL.md").is_file())
            self.assertTrue((project / ".cursor/rules/dopamine.mdc").is_file())
            self.assertTrue((project / ".windsurf/rules/dopamine.md").is_file())
            self.assertTrue((project / ".clinerules/dopamine.md").is_file())
            self.assertTrue((project / ".github/copilot-instructions.md").is_file())
            self.assertTrue((project / ".kiro/steering/dopamine.md").is_file())
            self.assertTrue((project / ".qoder/rules/dopamine.md").is_file())

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

    def test_user_install_uses_verified_targets(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            result = subprocess.run(
                [str(root / "scripts/install.sh"), "--agent", "all", "--scope", "user"],
                env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            expected = [
                ".agents/skills/dopamine/SKILL.md",
                ".claude/skills/dopamine/SKILL.md",
                ".config/opencode/skills/dopamine/SKILL.md",
                ".grok/skills/dopamine/SKILL.md",
                ".openclaw/skills/dopamine/SKILL.md",
                ".codeium/windsurf/memories/global_rules.md",
                "Documents/Cline/Rules/dopamine.md",
                ".copilot/copilot-instructions.md",
                ".kiro/steering/dopamine.md",
            ]
            for relative in expected:
                self.assertTrue((home / relative).is_file(), relative)

    def test_rejects_unverified_user_target(self) -> None:
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [str(root / "scripts/install.sh"), "--agent", "cursor", "--scope", "user"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("does not expose a verified", result.stderr)


if __name__ == "__main__":
    unittest.main()
