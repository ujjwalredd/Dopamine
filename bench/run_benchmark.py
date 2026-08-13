#!/usr/bin/env python3
"""Run isolated, paired Codex skill trials and retain every raw artifact."""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import time


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_TASKS_ROOT = ROOT / "bench" / "tasks"
SKILLS = {
    "baseline": None,
    "caveman": ROOT / "bench" / "vendor" / "caveman" / "skills" / "caveman" / "SKILL.md",
    "ponytail": ROOT / "bench" / "vendor" / "ponytail" / "skills" / "ponytail" / "SKILL.md",
    "adhd": ROOT / "bench" / "vendor" / "adhd" / "skills" / "adhd" / "SKILL.md",
    "dopamine": ROOT / "skills" / "dopamine" / "SKILL.md",
}
INVOCATIONS = {
    "baseline": "",
    "caveman": "Use Caveman full mode. ",
    "ponytail": "Use Ponytail full mode. ",
    "adhd": "Use ADHD mode. ",
    "dopamine": "Use Dopamine. ",
}


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_snapshot(folder: pathlib.Path) -> dict[str, str]:
    snapshot = {}
    for path in sorted(folder.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        try:
            snapshot[str(path.relative_to(folder))] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
    return snapshot


def diff_stats(before: dict[str, str], after_folder: pathlib.Path) -> dict[str, int]:
    after = source_snapshot(after_folder)
    added = deleted = 0
    for name in sorted(before.keys() | after.keys()):
        old = before.get(name, "").splitlines()
        new = after.get(name, "").splitlines()
        for line in difflib.ndiff(old, new):
            if line.startswith("+ "):
                added += 1
            elif line.startswith("- "):
                deleted += 1
    return {"lines_added": added, "lines_deleted": deleted, "files_after": len(after)}


def parse_usage(stdout: str) -> dict[str, int]:
    usage: dict[str, int] = {}
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "turn.completed":
            usage = event.get("usage", {})
    return usage


def grade(task_dir: pathlib.Path, workspace: pathlib.Path, timeout: int) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["python3", str(task_dir / "grader.py"), str(workspace)],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False, f"grader timed out after {timeout} seconds"
    output = (result.stdout + result.stderr).strip()
    return result.returncode == 0, output


def run_trial(
    run_root: pathlib.Path,
    tasks_root: pathlib.Path,
    task: str,
    arm: str,
    repeat: int,
    model: str,
    effort: str,
    timeout: int,
    grader_timeout: int,
) -> dict[str, object]:
    task_dir = tasks_root / task
    trial_dir = run_root / f"repeat-{repeat}" / arm / task
    workspace = trial_dir / "workspace"
    workspace.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(task_dir / "workspace", workspace)
    before = source_snapshot(workspace)

    skill_path = SKILLS[arm]
    if skill_path:
        skill_text = skill_path.read_text(encoding="utf-8")
        (workspace / "AGENTS.md").write_text(
            "# Active benchmark skill\n\nFollow these instructions for this task:\n\n" + skill_text,
            encoding="utf-8",
        )

    git_environment = {
        "GIT_AUTHOR_NAME": "Benchmark",
        "GIT_AUTHOR_EMAIL": "benchmark@example.invalid",
        "GIT_COMMITTER_NAME": "Benchmark",
        "GIT_COMMITTER_EMAIL": "benchmark@example.invalid",
    }
    subprocess.run(["git", "init", "-q"], cwd=workspace, check=True)
    subprocess.run(["git", "add", "."], cwd=workspace, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "benchmark fixture"],
        cwd=workspace,
        env={**os.environ, **git_environment},
        check=True,
    )

    prompt = (
        INVOCATIONS[arm]
        + (task_dir / "task.txt").read_text(encoding="utf-8").strip()
        + "\nWork only inside the current workspace. Do not inspect parent directories. "
        + "Do not modify AGENTS.md. Finish the task and report what you verified."
    )
    command = [
        "codex",
        "exec",
        "--ephemeral",
        "--skip-git-repo-check",
        "--approve-for-me",
        "--json",
        "--color",
        "never",
        "--ignore-user-config",
        "--ignore-rules",
        "-m",
        model,
        "-c",
        f'model_reasoning_effort="{effort}"',
        prompt,
    ]

    started = time.monotonic()
    timed_out = False
    try:
        result = subprocess.run(
            command,
            cwd=workspace,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
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
    elapsed = time.monotonic() - started

    (trial_dir / "events.jsonl").write_text(stdout, encoding="utf-8")
    (trial_dir / "stderr.txt").write_text(stderr, encoding="utf-8")
    passed, grader_output = grade(task_dir, workspace, grader_timeout)
    stats = diff_stats(before, workspace)
    stats["lines_added"] = max(0, stats["lines_added"] - (0 if skill_path is None else len((workspace / "AGENTS.md").read_text(encoding="utf-8").splitlines())))
    stats["files_after"] = max(0, stats["files_after"] - (0 if skill_path is None else 1))

    record: dict[str, object] = {
        "task": task,
        "arm": arm,
        "repeat": repeat,
        "model": model,
        "effort": effort,
        "passed": passed,
        "grader_output": grader_output,
        "agent_exit_code": exit_code,
        "timed_out": timed_out,
        "wall_seconds": round(elapsed, 3),
        "usage": parse_usage(stdout),
        **stats,
    }
    (trial_dir / "result.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks-root", type=pathlib.Path, default=DEFAULT_TASKS_ROOT)
    parser.add_argument("--arms", nargs="+", choices=SKILLS, default=list(SKILLS))
    parser.add_argument("--tasks", nargs="+")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--model", default="gpt-5.6-terra")
    parser.add_argument("--effort", choices=("low", "medium", "high"), default="medium")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--grader-timeout", type=int, default=120)
    parser.add_argument("--run-name")
    args = parser.parse_args()
    tasks_root = args.tasks_root.resolve()
    if args.tasks is None:
        args.tasks = sorted(path.name for path in tasks_root.iterdir() if path.is_dir())

    stamp = args.run_name or dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_root = ROOT / "bench" / "runs" / stamp
    run_root.mkdir(parents=True, exist_ok=False)
    manifest = {
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "codex_version": subprocess.run(["codex", "--version"], capture_output=True, text=True, check=False).stdout.strip(),
        "model": args.model,
        "effort": args.effort,
        "arms": args.arms,
        "tasks": args.tasks,
        "tasks_root": str(tasks_root),
        "repeats": args.repeats,
        "grader_timeout": args.grader_timeout,
        "skill_sha256": {name: sha256(path) if path else None for name, path in SKILLS.items()},
        "vendor_commits": {
            name: subprocess.run(["git", "-C", str(ROOT / "bench" / "vendor" / name), "rev-parse", "HEAD"], capture_output=True, text=True, check=False).stdout.strip()
            for name in ("caveman", "ponytail", "adhd")
        },
    }
    (run_root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    records = []
    for repeat in range(1, args.repeats + 1):
        for task in args.tasks:
            for arm in args.arms:
                print(f"RUN repeat={repeat} task={task} arm={arm}", flush=True)
                record = run_trial(
                    run_root, tasks_root, task, arm, repeat, args.model,
                    args.effort, args.timeout, args.grader_timeout,
                )
                records.append(record)
                usage = record.get("usage", {})
                print(f"RESULT pass={record['passed']} output={usage.get('output_tokens', 0)} wall={record['wall_seconds']}", flush=True)

    (run_root / "results.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(run_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
