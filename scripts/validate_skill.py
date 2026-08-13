#!/usr/bin/env python3
"""Dependency-free validation for the Dopamine skill package."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/dopamine/SKILL.md"


def main() -> int:
    errors: list[str] = []
    text = SKILL.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        errors.append("SKILL.md must start with YAML frontmatter")
    parts = text.split("---\n", 2)
    frontmatter = parts[1] if len(parts) == 3 else ""
    fields = {
        match.group(1): match.group(2).strip()
        for match in re.finditer(r"^([a-z_]+):\s*(.+)$", frontmatter, re.MULTILINE)
    }
    if set(fields) != {"name", "description"}:
        errors.append("frontmatter must contain exactly name and description")
    if fields.get("name") != "dopamine":
        errors.append("skill name must be dopamine")
    if not fields.get("description"):
        errors.append("description must not be empty")
    if len(text.splitlines()) > 500:
        errors.append("SKILL.md must stay below 500 lines")
    for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
        if "://" not in target and not (SKILL.parent / target).resolve().is_file():
            errors.append(f"missing linked file: {target}")
    metadata = ROOT / "skills/dopamine/agents/openai.yaml"
    if not metadata.is_file() or "$dopamine" not in metadata.read_text(encoding="utf-8"):
        errors.append("agents/openai.yaml must include a $dopamine default prompt")
    marketplace_path = ROOT / ".claude-plugin/marketplace.json"
    try:
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
        plugins = marketplace.get("plugins", [])
        if marketplace.get("name") != "dopamine-skills":
            errors.append("Claude marketplace name must be dopamine-skills")
        if len(plugins) != 1 or plugins[0].get("name") != "dopamine":
            errors.append("Claude marketplace must expose exactly the dopamine plugin")
        if plugins and plugins[0].get("source") != "./":
            errors.append("Claude marketplace plugin source must be the repository root")
        if plugins and "skills" in plugins[0]:
            errors.append("Claude marketplace must defer component discovery to plugin.json")
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"invalid Claude marketplace manifest: {error}")
    plugin_path = ROOT / ".claude-plugin/plugin.json"
    try:
        plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
        if plugin.get("name") != "dopamine" or plugin.get("version") != "0.1.0":
            errors.append("Claude plugin manifest must identify dopamine 0.1.0")
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"invalid Claude plugin manifest: {error}")
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors), file=sys.stderr)
        return 1
    print("Dopamine skill validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
