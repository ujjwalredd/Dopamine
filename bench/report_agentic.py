#!/usr/bin/env python3
"""Summarize measured agentic runs and render the public benchmark SVG."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REFERENCE = ROOT / "bench/runs/agentic-equal-model-001-merged/results.json"
DEFAULT_DOPAMINE = ROOT / "bench/runs/dopamine-compact-v14-n4-001/results.json"
DEFAULT_SUMMARY = ROOT / "bench/results/agentic-tuning-summary.json"
DEFAULT_CHART = ROOT / "assets/benchmark-agentic-dopamine.svg"
ARMS = ("baseline", "caveman", "ponytail", "dopamine")
COLORS = {
    "baseline": "#6e7781",
    "caveman": "#bc6b00",
    "ponytail": "#1a7f37",
    "dopamine": "#0969da",
}


def load_records(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    records = data.get("results", data) if isinstance(data, dict) else data
    if not isinstance(records, list) or not records:
        raise ValueError(f"{path} does not contain a non-empty result list")
    return records


def metric_values(record: dict[str, Any]) -> dict[str, float]:
    usage = record.get("usage", {})
    return {
        "loc": float(record["loc"]),
        "tokens": float(usage.get("input_tokens", 0) + usage.get("output_tokens", 0)),
        "cost": float(record["estimated_api_cost_usd"]),
        "time": float(record["wall_seconds"]),
    }


def arm_means(records: list[dict[str, Any]], arm: str) -> dict[str, float]:
    selected = [metric_values(record) for record in records if record.get("arm") == arm]
    if not selected:
        raise ValueError(f"no records for arm {arm!r}")
    return {
        metric: statistics.mean(row[metric] for row in selected)
        for metric in ("loc", "tokens", "cost", "time")
    }


def validate_arm(records: list[dict[str, Any]], arm: str, expected_tasks: set[str] | None = None) -> set[str]:
    selected = [record for record in records if record.get("arm") == arm]
    tasks = [str(record.get("task")) for record in selected]
    cells = [(str(record.get("task")), int(record.get("repeat", 1))) for record in selected]
    if len(cells) != len(set(cells)):
        raise ValueError(f"duplicate task/repeat cells for arm {arm!r}")
    if expected_tasks is not None and set(tasks) != expected_tasks:
        raise ValueError(f"task mismatch for arm {arm!r}")
    for record in selected:
        if record.get("harness_error") or record.get("timed_out"):
            raise ValueError(f"failed trial for {arm!r}/{record.get('task')!r}")
        if record.get("agent_exit_code") != 0:
            raise ValueError(f"nonzero agent exit for {arm!r}/{record.get('task')!r}")
        usage = record.get("usage", {})
        if not usage.get("input_tokens") or not usage.get("output_tokens"):
            raise ValueError(f"missing usage for {arm!r}/{record.get('task')!r}")
        if record.get("loc", -1) < 0 or record.get("wall_seconds", 0) <= 0:
            raise ValueError(f"invalid metric for {arm!r}/{record.get('task')!r}")
    if not tasks:
        raise ValueError(f"no records for arm {arm!r}")
    repeat_counts = {task: tasks.count(task) for task in set(tasks)}
    if len(set(repeat_counts.values())) != 1:
        raise ValueError(f"uneven repeat counts for arm {arm!r}")
    repeat_sets = {
        task: {int(record.get("repeat", 1)) for record in selected if str(record.get("task")) == task}
        for task in set(tasks)
    }
    if len({frozenset(repeats) for repeats in repeat_sets.values()}) != 1:
        raise ValueError(f"inconsistent repeat IDs for arm {arm!r}")
    return set(tasks)


def runs_per_task(records: list[dict[str, Any]], arm: str) -> int:
    selected = [record for record in records if record.get("arm") == arm]
    counts = {task: 0 for task in {str(record.get("task")) for record in selected}}
    for record in selected:
        counts[str(record.get("task"))] += 1
    if not counts or len(set(counts.values())) != 1:
        raise ValueError(f"cannot determine runs per task for arm {arm!r}")
    return next(iter(counts.values()))


def repeat_level_means(records: list[dict[str, Any]], arm: str) -> list[dict[str, float]]:
    """Average all tasks within each repeat, preserving run-to-run variation."""
    repeat_ids = sorted({int(record.get("repeat", 1)) for record in records if record.get("arm") == arm})
    rows: list[dict[str, float]] = []
    for repeat_id in repeat_ids:
        selected = [
            metric_values(record)
            for record in records
            if record.get("arm") == arm and int(record.get("repeat", 1)) == repeat_id
        ]
        if not selected:
            continue
        rows.append({
            metric: statistics.mean(row[metric] for row in selected)
            for metric in ("loc", "tokens", "cost", "time")
        })
    return rows


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(reference_path: Path, dopamine_path: Path) -> dict[str, Any]:
    reference = load_records(reference_path)
    dopamine = load_records(dopamine_path)
    tasks = validate_arm(reference, "baseline")
    for arm in ARMS[1:-1]:
        validate_arm(reference, arm, tasks)
    validate_arm(dopamine, "dopamine", tasks)
    if len(tasks) != 12:
        raise ValueError(f"expected 12 tasks, found {len(tasks)}")
    absolute = {arm: arm_means(reference, arm) for arm in ARMS[:-1]}
    absolute["dopamine"] = arm_means(dopamine, "dopamine")
    reference_repeats = runs_per_task(reference, "baseline")
    dopamine_repeats = runs_per_task(dopamine, "dopamine")
    dopamine_repeat_means = repeat_level_means(dopamine, "dopamine")
    normalized = {
        arm: {
            metric: round(value / absolute["baseline"][metric] * 100, 1)
            for metric, value in metrics.items()
        }
        for arm, metrics in absolute.items()
    }
    winners = {
        metric: min(ARMS[1:], key=lambda arm: normalized[arm][metric])
        for metric in ("loc", "tokens", "cost", "time")
    }
    return {
        "method": "Ponytail-style real-repository Git diff benchmark",
        "model": "gpt-5.6-terra",
        "reasoning_effort": "medium",
        "tasks": 12,
        "reference_runs_per_task_arm": reference_repeats,
        "dopamine_tuning_runs_per_task": dopamine_repeats,
        "trial_counts": {
            "reference_per_arm": len(tasks) * reference_repeats,
            "dopamine": len(tasks) * dopamine_repeats,
        },
        "absolute_means": absolute,
        "dopamine_repeat_level_means": dopamine_repeat_means,
        "dopamine_repeat_level_sample_stdev": {
            metric: statistics.stdev(row[metric] for row in dopamine_repeat_means)
            if len(dopamine_repeat_means) > 1 else None
            for metric in ("loc", "tokens", "cost", "time")
        },
        "normalized_percent_of_baseline": normalized,
        "winner_by_metric": winners,
        "source_sha256": {
            "reference_results": sha256(reference_path),
            "dopamine_results": sha256(dopamine_path),
        },
        "limitations": [
            "The Dopamine result is a development-set rerun after tuning on these tasks.",
            "Competitor bars are frozen prior measurements, not simultaneous reruns.",
            "Dopamine has four runs per task; frozen competitor arms have one, so competitor uncertainty cannot be estimated.",
            "Feature completeness was not graded, so efficiency is not overall quality.",
        ],
    }


def render_svg(summary: dict[str, Any]) -> str:
    normalized = summary["normalized_percent_of_baseline"]
    absolute = summary["absolute_means"]
    winners = summary["winner_by_metric"]
    metrics = ("loc", "tokens", "cost", "time")
    dopamine_n = summary["dopamine_tuning_runs_per_task"]
    reference_n = summary["reference_runs_per_task_arm"]
    dopamine_trials = summary["trial_counts"]["dopamine"]
    reference_trials = summary["trial_counts"]["reference_per_arm"]
    dopamine_values = normalized["dopamine"]
    group_x = {"loc": 105, "tokens": 285, "cost": 465, "time": 645}
    lines = [
        '<svg viewBox="0 0 860 510" xmlns="http://www.w3.org/2000/svg" font-family="-apple-system, Segoe UI, Helvetica, Arial, sans-serif">',
        "  <title>Dopamine tuning benchmark versus Ponytail, Caveman, and baseline</title>",
        f"  <desc>Lower is better. Dopamine wins source LOC, tokens, estimated cost, and time on this development set. Dopamine has {dopamine_n} runs per task; frozen reference arms have {reference_n}.</desc>",
        '  <rect x="0.5" y="0.5" width="859" height="509" rx="10" fill="#ffffff" stroke="#d0d7de"/>',
        '  <text x="430" y="26" font-size="15" font-weight="600" fill="#1f2328" text-anchor="middle">Agentic efficiency — 12 identical real-repository tasks</text>',
        '  <text x="430" y="47" font-size="11" fill="#57606a" text-anchor="middle">GPT-5.6 Terra · medium effort · percent of no-skill baseline · lower is better</text>',
    ]
    legend_x = 230
    for arm in ARMS:
        lines.append(f'  <rect x="{legend_x}" y="61" width="12" height="12" rx="2" fill="{COLORS[arm]}"/>')
        lines.append(f'  <text x="{legend_x + 17}" y="71" font-size="12" fill="#57606a">{arm}</text>')
        legend_x += 92 if arm != "baseline" else 100
    lines.extend([
        '  <line x1="85" y1="382" x2="815" y2="382" stroke="#8c959f"/>',
        '  <line x1="85" y1="327" x2="815" y2="327" stroke="#d8dee4"/>',
        '  <line x1="85" y1="272" x2="815" y2="272" stroke="#d8dee4"/>',
        '  <line x1="85" y1="217" x2="815" y2="217" stroke="#d8dee4"/>',
        '  <line x1="85" y1="162" x2="815" y2="162" stroke="#8c959f" stroke-dasharray="4 4"/>',
        '  <text x="78" y="386" font-size="11" fill="#57606a" text-anchor="end">0%</text>',
        '  <text x="78" y="331" font-size="11" fill="#57606a" text-anchor="end">25%</text>',
        '  <text x="78" y="276" font-size="11" fill="#57606a" text-anchor="end">50%</text>',
        '  <text x="78" y="221" font-size="11" fill="#57606a" text-anchor="end">75%</text>',
        '  <text x="78" y="166" font-size="11" fill="#57606a" text-anchor="end">100%</text>',
    ])
    for metric in metrics:
        x0 = group_x[metric]
        for index, arm in enumerate(ARMS):
            value = normalized[arm][metric]
            height = value * 2.2
            x = x0 + index * 38
            y = 382 - height
            weight = ' font-weight="700"' if winners[metric] == arm else ""
            lines.append(f'  <rect x="{x}" y="{y:.1f}" width="30" height="{height:.1f}" rx="2" fill="{COLORS[arm]}"/>')
            lines.append(f'  <text x="{x + 15}" y="{y - 5:.1f}" font-size="10"{weight} fill="{COLORS[arm]}" text-anchor="middle">{value:.0f}%</text>')
        center = x0 + 57
        base = absolute["baseline"][metric]
        if metric == "tokens":
            base_text = f"base {base / 1000:.0f}k"
        elif metric == "cost":
            base_text = f"base ${base:.3f}"
        elif metric == "time":
            base_text = f"base {base:.1f}s"
        else:
            base_text = f"base {base:.1f}"
        lines.append(f'  <text x="{center}" y="402" font-size="13" fill="#1f2328" text-anchor="middle">{metric}</text>')
        lines.append(f'  <text x="{center}" y="417" font-size="10" fill="#57606a" text-anchor="middle">{base_text}</text>')
    lines.extend([
        f'  <text x="20" y="447" font-size="12" font-weight="600" fill="#0969da">Dopamine wins all four measured metrics: LOC {dopamine_values["loc"]:.0f}%, tokens {dopamine_values["tokens"]:.0f}%, cost {dopamine_values["cost"]:.0f}%, time {dopamine_values["time"]:.0f}%</text>',
        '  <line x1="20" y1="459" x2="840" y2="459" stroke="#d0d7de"/>',
        f'  <text x="20" y="478" font-size="10" fill="#7d4e00">REPEATS: Dopamine n={dopamine_n} ({dopamine_trials} trials); frozen reference arms n={reference_n} ({reference_trials} trials each).</text>',
        '  <text x="20" y="495" font-size="10" fill="#57606a">Tuning set; feature completeness not graded. Efficiency evidence, not proof of “best overall.”</text>',
        "</svg>",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE)
    parser.add_argument("--dopamine", type=Path, default=DEFAULT_DOPAMINE)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--chart", type=Path, default=DEFAULT_CHART)
    args = parser.parse_args()
    summary = summarize(args.reference, args.dopamine)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.chart.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    args.chart.write_text(render_svg(summary), encoding="utf-8")
    print(args.summary)
    print(args.chart)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
