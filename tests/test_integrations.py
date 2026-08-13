from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class IntegrationTests(unittest.TestCase):
    def test_generated_adapters_are_current(self) -> None:
        result = subprocess.run(
            ["python3", str(ROOT / "scripts/generate_integrations.py"), "--check"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_json_manifests_parse_and_identify_dopamine(self) -> None:
        manifests = [
            ".agents/plugins/marketplace.json",
            ".claude-plugin/marketplace.json",
            ".claude-plugin/plugin.json",
            ".codex-plugin/plugin.json",
            ".devin-plugin/plugin.json",
            ".github/plugin/marketplace.json",
            ".github/plugin/plugin.json",
            ".grok-plugin/marketplace.json",
            ".qoder-plugin/plugin.json",
            "gemini-extension.json",
            "package.json",
            "plugin.json",
        ]
        for relative in manifests:
            with self.subTest(relative=relative):
                data = json.loads((ROOT / relative).read_text(encoding="utf-8"))
                self.assertNotIn("ponytail", json.dumps(data).lower())
                if "marketplace" not in relative and relative != "package.json":
                    self.assertEqual(data.get("name"), "dopamine")

    def test_manifest_component_paths_exist(self) -> None:
        self.assertTrue((ROOT / "skills/dopamine/SKILL.md").is_file())
        self.assertTrue((ROOT / ".opencode/skills/dopamine/SKILL.md").is_file())
        self.assertTrue((ROOT / ".openclaw/skills/dopamine/SKILL.md").is_file())
        codex = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())
        qoder = json.loads((ROOT / ".qoder-plugin/plugin.json").read_text())
        copilot = json.loads((ROOT / ".github/plugin/plugin.json").read_text())
        package = json.loads((ROOT / "package.json").read_text())
        self.assertTrue((ROOT / codex["skills"]).is_dir())
        self.assertTrue((ROOT / qoder["skills"]).is_dir())
        self.assertTrue((ROOT / qoder["rules"]).is_dir())
        self.assertTrue((ROOT / copilot["skills"]).is_dir())
        self.assertEqual(package["pi"]["skills"], ["./skills"])
        self.assertNotIn("dependencies", package)
        self.assertNotIn("devDependencies", package)

    def test_rule_adapters_are_original_and_within_host_limits(self) -> None:
        rules = [
            "AGENTS.md",
            ".agents/rules/dopamine.md",
            ".clinerules/dopamine.md",
            ".cursor/rules/dopamine.mdc",
            ".github/copilot-instructions.md",
            ".kiro/steering/dopamine.md",
            ".qoder/rules/dopamine.md",
            ".windsurf/rules/dopamine.md",
        ]
        for relative in rules:
            with self.subTest(relative=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                self.assertIn("Maximize verified progress per unit of code, time, tokens, and cost.", text)
                self.assertNotIn("ponytail", text.lower())
                self.assertLess(len(text), 12_000)

    def test_format_specific_frontmatter(self) -> None:
        cursor = (ROOT / ".cursor/rules/dopamine.mdc").read_text()
        windsurf = (ROOT / ".windsurf/rules/dopamine.md").read_text()
        kiro = (ROOT / ".kiro/steering/dopamine.md").read_text()
        self.assertIn("alwaysApply: true", cursor)
        self.assertIn("trigger: always_on", windsurf)
        self.assertIn("inclusion: always", kiro)

    def test_integration_guide_names_every_supported_host(self) -> None:
        guide = (ROOT / "docs/INTEGRATIONS.md").read_text(encoding="utf-8")
        hosts = [
            "Claude Code", "Codex", "GitHub Copilot CLI", "Pi", "OpenCode",
            "Gemini CLI", "Qoder", "Antigravity CLI", "Hermes Agent",
            "CodeWhale", "Swival", "Devin CLI", "OpenClaw", "Grok Build",
            "Cursor", "Windsurf", "Cline", "GitHub Copilot Chat/editor",
            "Aider", "Kiro", "Zed", "JetBrains Junie", "Amp", "Jules",
        ]
        for host in hosts:
            with self.subTest(host=host):
                self.assertIn(f"| {host} |", guide)


if __name__ == "__main__":
    unittest.main()
