#!/usr/bin/env python3
"""Ponytail-style agentic benchmark: real repo diff LOC, tokens, cost, and time."""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import threading
import time


ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "bench" / "vendor" / "full-stack-fastapi-template"
RUNS = ROOT / "bench" / "runs"
SKILLS = {
    "baseline": None,
    "caveman": ROOT / "bench" / "vendor" / "caveman" / "skills" / "caveman" / "SKILL.md",
    "ponytail": ROOT / "bench" / "vendor" / "ponytail" / "skills" / "ponytail" / "SKILL.md",
    "dopamine": ROOT / "skills" / "dopamine" / "SKILL.md",
}
TASKS = {
    "fe-datepicker": "Add a date picker component to the frontend.",
    "fe-colorpicker": "Add a color picker component to the frontend.",
    "fe-command": "Add a command palette (searchable command menu) to the frontend.",
    "fe-dropzone": "Add a file upload dropzone component to the frontend.",
    "fe-wizard": "Add a multi-step form wizard component to the frontend.",
    "fe-rating": "Add a star rating input component to the frontend.",
    "be-duplicate": "Add an endpoint to duplicate an item.",
    "be-search": "Add an endpoint to search items by title.",
    "be-count": "Add an endpoint that returns how many items the current user has.",
    "be-archive": "Add the ability to archive and unarchive an item.",
    "be-bulkdelete": "Add an endpoint to delete several items at once.",
    "be-csv": "Add an endpoint to export the current user's items as CSV.",
}
CODE_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css"}
SKIP_FRAGMENTS = ("-lock", ".lock", ".gen.ts", "lock.json", "routeTree.gen", "node_modules")
NO_RUN = (
    "Write the implementation, including tests only if you normally would for this change. "
    "Do not run a development server, install dependencies, run a database, or open a browser. "
    "Inspect the existing code, write the code, and stop. Only the delivered source diff is measured."
)
# Official standard GPT-5.6 Terra rates retrieved 2026-08-12. Actual Codex subscription billing may differ.
PRICE_PER_MILLION = {"fresh_input": 2.00, "cached_input": 0.20, "output": 12.00}
PRICING_SOURCE = "https://developers.openai.com/api/docs/models/gpt-5.6-terra"
WRITE_LOCK = threading.Lock()


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_fixture(destination: pathlib.Path) -> None:
    shutil.copytree(
        FIXTURE,
        destination,
        ignore=shutil.ignore_patterns(
            ".git", "node_modules", ".venv", "venv", "dist", "build", "__pycache__", ".pytest_cache"
        ),
    )


def git(workspace: pathlib.Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=workspace, text=True, capture_output=True, check=check
    )


def initialize_git(workspace: pathlib.Path) -> None:
    environment = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Benchmark",
        "GIT_AUTHOR_EMAIL": "benchmark@example.invalid",
        "GIT_COMMITTER_NAME": "Benchmark",
        "GIT_COMMITTER_EMAIL": "benchmark@example.invalid",
    }
    subprocess.run(["git", "init", "-q"], cwd=workspace, check=True)
    subprocess.run(["git", "add", "-A"], cwd=workspace, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "pinned fixture"], cwd=workspace, env=environment, check=True
    )


def is_test(path: str) -> bool:
    parts = pathlib.PurePosixPath(path).parts
    name = parts[-1].lower()
    return (
        name.startswith("test_")
        or name.endswith("_test.py")
        or any(part.lower() in {"test", "tests"} for part in parts[:-1])
    )


def diff_loc(workspace: pathlib.Path) -> dict[str, int]:
    git(workspace, "add", "-A", check=False)
    result = git(workspace, "diff", "--cached", "--numstat", "HEAD", check=False)
    source_loc = source_files = test_loc = test_files = 0
    for line in result.stdout.splitlines():
        fields = line.split("\t")
        if len(fields) != 3 or fields[0] == "-":
            continue
        added, _, filename = fields
        if pathlib.PurePosixPath(filename).suffix not in CODE_EXTENSIONS:
            continue
        if any(fragment in filename for fragment in SKIP_FRAGMENTS):
            continue
        if is_test(filename):
            test_loc += int(added)
            test_files += 1
        else:
            source_loc += int(added)
            source_files += 1
    return {
        "loc": source_loc,
        "source_files": source_files,
        "test_loc": test_loc,
        "test_files": test_files,
    }


def usage_from_events(text: str) -> dict[str, int]:
    usage: dict[str, int] = {}
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "turn.completed":
            usage = event.get("usage", {})
    return usage


def estimated_cost(usage: dict[str, int]) -> float:
    input_tokens = usage.get("input_tokens", 0)
    cached = usage.get("cached_input_tokens", 0)
    fresh = max(0, input_tokens - cached)
    output = usage.get("output_tokens", 0)
    return (
        fresh * PRICE_PER_MILLION["fresh_input"]
        + cached * PRICE_PER_MILLION["cached_input"]
        + output * PRICE_PER_MILLION["output"]
    ) / 1_000_000


def run_trial(
    run_root: pathlib.Path,
    task: str,
    arm: str,
    repeat: int,
    model: str,
    effort: str,
    timeout: int,
) -> dict[str, object]:
    trial = run_root / f"repeat-{repeat}" / arm / task
    workspace = trial / "workspace"
    trial.mkdir(parents=True, exist_ok=True)
    copy_fixture(workspace)
    initialize_git(workspace)

    prompt_parts = []
    skill = SKILLS[arm]
    if skill:
        prompt_parts.append("Follow these active skill instructions:\n\n" + skill.read_text(encoding="utf-8"))
    prompt_parts.extend(
        [
            TASKS[task],
            NO_RUN,
            "Work only inside the current workspace. Finish the requested implementation and briefly report the files changed.",
        ]
    )
    command = [
        "codex", "exec", "--ephemeral", "--skip-git-repo-check", "--approve-for-me",
        "--json", "--color", "never", "--ignore-user-config", "--ignore-rules",
        "-m", model, "-c", f'model_reasoning_effort="{effort}"', "\n\n".join(prompt_parts),
    ]
    started = time.monotonic()
    timed_out = False
    try:
        result = subprocess.run(
            command, cwd=workspace, stdin=subprocess.DEVNULL, capture_output=True,
            text=True, timeout=timeout, check=False,
        )
        stdout, stderr, exit_code = result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired as error:
        timed_out = True
        stdout = error.stdout or ""
        stderr = error.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        exit_code = 124
    wall = time.monotonic() - started
    usage = usage_from_events(stdout)
    record: dict[str, object] = {
        "task": task,
        "arm": arm,
        "repeat": repeat,
        "model": model,
        "effort": effort,
        "agent_exit_code": exit_code,
        "timed_out": timed_out,
        "wall_seconds": round(wall, 3),
        "usage": usage,
        "estimated_api_cost_usd": round(estimated_cost(usage), 6),
        **diff_loc(workspace),
    }
    (trial / "events.jsonl").write_text(stdout, encoding="utf-8")
    (trial / "stderr.txt").write_text(stderr, encoding="utf-8")
    (trial / "result.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", nargs="+", choices=TASKS, default=list(TASKS))
    parser.add_argument("--arms", nargs="+", choices=SKILLS, default=list(SKILLS))
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--model", default="gpt-5.6-terra")
    parser.add_argument("--effort", default="medium")
    parser.add_argument("--timeout", type=int, default=360)
    parser.add_argument("--run-name")
    args = parser.parse_args()

    name = args.run_name or dt.datetime.now(dt.timezone.utc).strftime("agentic-%Y%m%dT%H%M%SZ")
    run_root = RUNS / name
    run_root.mkdir(parents=True, exist_ok=False)
    manifest = {
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "method": "Ponytail-style real-repository agentic diff benchmark",
        "fixture": "tiangolo/full-stack-fastapi-template",
        "fixture_commit": git(FIXTURE, "rev-parse", "HEAD").stdout.strip(),
        "codex_version": subprocess.run(["codex", "--version"], text=True, capture_output=True).stdout.strip(),
        "model": args.model,
        "effort": args.effort,
        "tasks": args.tasks,
        "arms": args.arms,
        "repeats": args.repeats,
        "pricing_usd_per_million": PRICE_PER_MILLION,
        "pricing_source": PRICING_SOURCE,
        "cost_label": "API-equivalent estimate; actual Codex subscription billing may differ",
        "skill_sha256": {arm: sha256(path) if path else None for arm, path in SKILLS.items()},
    }
    (run_root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    jobs = [
        (repeat, task, arm)
        for repeat in range(1, args.repeats + 1)
        for task in args.tasks
        for arm in args.arms
    ]
    records: list[dict[str, object]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(run_trial, run_root, task, arm, repeat, args.model, args.effort, args.timeout): (repeat, task, arm)
            for repeat, task, arm in jobs
        }
        for future in concurrent.futures.as_completed(futures):
            repeat, task, arm = futures[future]
            try:
                record = future.result()
            except Exception as error:
                record = {"repeat": repeat, "task": task, "arm": arm, "harness_error": repr(error)}
            records.append(record)
            with WRITE_LOCK:
                (run_root / "results.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
                print(
                    f"DONE {len(records)}/{len(jobs)} task={task} arm={arm} "
                    f"loc={record.get('loc')} out={record.get('usage', {}).get('output_tokens')} "
                    f"cost={record.get('estimated_api_cost_usd')} wall={record.get('wall_seconds')}",
                    flush=True,
                )
    print(run_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
