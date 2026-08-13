#!/usr/bin/env python3
"""Materialize untouched public SkillsBench tasks after Dopamine v3 was frozen."""

from __future__ import annotations

import pathlib
import shutil


ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "bench" / "vendor" / "skillsbench" / "tasks"
TARGET = ROOT / "bench" / "holdout-v3-tasks"


def body(task_md: pathlib.Path) -> str:
    text = task_md.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    return parts[2].strip() if len(parts) == 3 else text.strip()


def reset(name: str) -> tuple[pathlib.Path, pathlib.Path]:
    source = SOURCE / name
    target = TARGET / name
    if target.exists():
        shutil.rmtree(target)
    (target / "workspace").mkdir(parents=True)
    return source, target


def path_rewriting_grader(source: pathlib.Path, replacements: dict[str, str]) -> str:
    """Run the pinned official verifier with only container paths rewritten."""
    verifier = source / "verifier" / "test_outputs.py"
    return (
        "import pathlib, subprocess, sys, tempfile\n"
        "workspace = pathlib.Path(sys.argv[1]).resolve()\n"
        f"source = pathlib.Path({str(verifier)!r})\n"
        "text = source.read_text(encoding='utf-8')\n"
        f"replacements = {replacements!r}\n"
        "for old, relative in replacements.items():\n"
        "    text = text.replace(old, str(workspace / relative))\n"
        "with tempfile.TemporaryDirectory(prefix='dopamine-verifier-') as temp:\n"
        "    adapted = pathlib.Path(temp) / 'test_outputs.py'\n"
        "    adapted.write_text(text, encoding='utf-8')\n"
        "    result = subprocess.run([sys.executable, '-m', 'pytest', '-q', str(adapted)], cwd=workspace, text=True, capture_output=True)\n"
        "print(result.stdout, end='')\n"
        "print(result.stderr, end='')\n"
        "raise SystemExit(result.returncode)\n"
    )


def import_manufacturing() -> None:
    source, target = reset("manufacturing-codebook-normalization")
    shutil.copytree(source / "environment" / "data", target / "workspace" / "data")
    shutil.copy2(
        source / "environment" / "skills" / "reference.md",
        target / "workspace" / "reference.md",
    )
    prompt = body(source / "task.md")
    prompt = prompt.replace("/app/data/", "data/").replace(
        "/app/output/solution.json", "output/solution.json"
    )
    prompt += "\nThe available domain guidance is reference.md."
    (target / "task.txt").write_text(prompt + "\n", encoding="utf-8")
    (target / "grader.py").write_text(
        path_rewriting_grader(
            source,
            {"/app/output": "output", "/app/data": "data"},
        ),
        encoding="utf-8",
    )


def import_lab() -> None:
    source, target = reset("lab-unit-harmonization")
    shutil.copytree(source / "environment" / "data", target / "workspace" / "data")
    prompt = body(source / "task.md")
    prompt = prompt.replace(
        "/root/environment/data/ckd_lab_data.csv", "data/ckd_lab_data.csv"
    ).replace(
        "/root/environment/data/ckd_feature_descriptions.csv",
        "data/ckd_feature_descriptions.csv",
    ).replace("/root/ckd_lab_data_harmonized.csv", "ckd_lab_data_harmonized.csv")
    (target / "task.txt").write_text(prompt + "\n", encoding="utf-8")
    (target / "grader.py").write_text(
        path_rewriting_grader(
            source,
            {"/root/ckd_lab_data_harmonized.csv": "ckd_lab_data_harmonized.csv"},
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    import_manufacturing()
    import_lab()
