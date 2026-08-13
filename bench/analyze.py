#!/usr/bin/env python3
"""Summarize a benchmark run without hiding failed or missing trials."""

from __future__ import annotations

import argparse
import json
import pathlib
import statistics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=pathlib.Path)
    args = parser.parse_args()
    records = json.loads((args.run / "results.json").read_text(encoding="utf-8"))
    arms = sorted({record["arm"] for record in records})
    summary = {}
    for arm in arms:
        rows = [record for record in records if record["arm"] == arm]
        passed = [record for record in rows if record["passed"]]
        total_tokens = [
            record.get("usage", {}).get("input_tokens", 0)
            + record.get("usage", {}).get("output_tokens", 0)
            for record in rows
        ]
        input_tokens = [record.get("usage", {}).get("input_tokens", 0) for record in rows]
        cached_tokens = [record.get("usage", {}).get("cached_input_tokens", 0) for record in rows]
        fresh_tokens = [value - cached for value, cached in zip(input_tokens, cached_tokens)]
        output_tokens = [record.get("usage", {}).get("output_tokens", 0) for record in rows]
        summary[arm] = {
            "trials": len(rows),
            "passes": len(passed),
            "resolution_rate": len(passed) / len(rows) if rows else 0,
            "total_tokens": sum(total_tokens),
            "input_tokens": sum(input_tokens),
            "cached_input_tokens": sum(cached_tokens),
            "fresh_input_tokens": sum(fresh_tokens),
            "tokens_per_trial": statistics.mean(total_tokens) if rows else 0,
            "tokens_per_verified_solution": sum(total_tokens) / len(passed) if passed else None,
            "output_tokens": sum(output_tokens),
            "mean_wall_seconds": statistics.mean(record["wall_seconds"] for record in rows) if rows else 0,
            "mean_lines_added": statistics.mean(record["lines_added"] for record in rows) if rows else 0,
        }
    output = {"summary": summary, "claims": []}
    baseline = summary.get("baseline")
    dopamine = summary.get("dopamine")
    comparable = (
        baseline
        and dopamine
        and baseline["passes"] > 0
        and dopamine["passes"] > 0
        and dopamine["resolution_rate"] >= baseline["resolution_rate"]
    )
    if comparable:
        delta = (
            dopamine["tokens_per_verified_solution"]
            / baseline["tokens_per_verified_solution"]
            - 1
        )
        output["claims"].append(
            {
                "comparison": "dopamine_vs_baseline",
                "verified_resolution_non_decreasing": True,
                "token_delta_per_verified_solution": delta,
            }
        )
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
