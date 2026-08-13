#!/usr/bin/env python3
"""Materialize pinned public SkillsBench holdouts for the local paired harness."""

from __future__ import annotations

import pathlib
import shutil


ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "bench" / "vendor" / "skillsbench" / "tasks"
TARGET = ROOT / "bench" / "holdout-tasks"


def body(task_md: pathlib.Path) -> str:
    text = task_md.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    return parts[2].strip() if len(parts) == 3 else text.strip()


def reset(name: str) -> pathlib.Path:
    target = TARGET / name
    if target.exists():
        shutil.rmtree(target)
    (target / "workspace").mkdir(parents=True)
    return target


def import_dialogue() -> None:
    name = "dialogue-parser"
    source = SOURCE / name
    target = reset(name)
    shutil.copy2(source / "environment" / "script.txt", target / "workspace" / "script.txt")
    (target / "task.txt").write_text(
        body(source / "task.md").replace("/app/", "the current workspace/") + "\n",
        encoding="utf-8",
    )
    (target / "grader.py").write_text(
        '''import pathlib, subprocess, sys\n'''
        '''workspace = pathlib.Path(sys.argv[1]).resolve()\n'''
        f'''verifier = pathlib.Path({str(source / "verifier" / "test_outputs.py")!r})\n'''
        '''result = subprocess.run([sys.executable, "-m", "pytest", "-q", str(verifier)], cwd=workspace, text=True, capture_output=True)\n'''
        '''print(result.stdout, end="")\nprint(result.stderr, end="")\nraise SystemExit(result.returncode)\n''',
        encoding="utf-8",
    )


def import_cache() -> None:
    name = "llm-prefix-cache-replay"
    source = SOURCE / name
    target = reset(name)
    for filename in ("trace.jsonl", "config.json"):
        shutil.copy2(source / "environment" / filename, target / "workspace" / filename)
    (target / "task.txt").write_text(
        body(source / "task.md")
        .replace("/root/trace.jsonl", "trace.jsonl")
        .replace("/root/config.json", "config.json")
        .replace("/root/report.json", "report.json")
        + "\n",
        encoding="utf-8",
    )
    (target / "grader.py").write_text(
        '''import json, pathlib, sys\n'''
        '''workspace = pathlib.Path(sys.argv[1]).resolve()\n'''
        f'''sys.path.insert(0, {str(source / "verifier")!r})\n'''
        '''from oracle_helpers import load_trace, simulate\n'''
        '''cfg = json.loads((workspace / "config.json").read_text())\n'''
        '''trace = load_trace(workspace / "trace.jsonl")\n'''
        '''s3 = cfg["s3fifo"]\n'''
        '''expected = simulate(trace, cfg["block_size"], cfg["cache_capacity_blocks"], s3["small_ratio"], s3["max_freq"])\n'''
        '''actual = json.loads((workspace / "report.json").read_text())\n'''
        '''for key in ("total_requests", "total_prompt_tokens", "total_hit_tokens", "final_cache_blocks"):\n    assert actual[key] == expected[key], (key, actual[key], expected[key])\n'''
        '''assert abs(actual["overall_hit_rate"] - expected["overall_hit_rate"]) < 1e-6\n'''
        '''assert len(actual["per_request"]) == len(expected["per_request"])\n'''
        '''for idx in (133, 601, 968, 1459, 1999):\n    assert actual["per_request"][idx] == expected["per_request"][idx]\n'''
        '''assert sum(row["hit_tokens"] for row in actual["per_request"]) == actual["total_hit_tokens"]\n'''
        '''assert sum(row["prompt_tokens"] for row in actual["per_request"]) == actual["total_prompt_tokens"]\n'''
        '''print("PASS")\n''',
        encoding="utf-8",
    )


if __name__ == "__main__":
    import_dialogue()
    import_cache()
