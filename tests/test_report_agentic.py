from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bench.report_agentic import arm_means, load_records, render_svg, summarize, validate_arm


class ReportAgenticTests(unittest.TestCase):
    def test_arm_means_counts_input_and_output_tokens(self) -> None:
        rows = [
            {"arm": "x", "loc": 2, "usage": {"input_tokens": 3, "output_tokens": 5}, "estimated_api_cost_usd": 0.1, "wall_seconds": 7},
            {"arm": "x", "loc": 4, "usage": {"input_tokens": 5, "output_tokens": 7}, "estimated_api_cost_usd": 0.3, "wall_seconds": 9},
        ]
        self.assertEqual(arm_means(rows, "x"), {"loc": 3.0, "tokens": 10.0, "cost": 0.2, "time": 8.0})

    def test_load_records_rejects_empty_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.json"
            path.write_text("[]", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_records(path)

    def test_validate_arm_rejects_failed_trial(self) -> None:
        row = {
            "arm": "x", "task": "a", "loc": 1, "wall_seconds": 1,
            "agent_exit_code": 124, "timed_out": True,
            "usage": {"input_tokens": 1, "output_tokens": 1},
        }
        with self.assertRaises(ValueError):
            validate_arm([row], "x")

    def test_validate_arm_accepts_balanced_repeats(self) -> None:
        rows = [
            {
                "arm": "x", "task": task, "repeat": repeat, "loc": 1,
                "wall_seconds": 1, "agent_exit_code": 0, "timed_out": False,
                "usage": {"input_tokens": 1, "output_tokens": 1},
            }
            for task in ("a", "b") for repeat in (1, 2)
        ]
        self.assertEqual(validate_arm(rows, "x"), {"a", "b"})

    def test_validate_arm_rejects_duplicate_repeat_cell(self) -> None:
        row = {
            "arm": "x", "task": "a", "repeat": 1, "loc": 1,
            "wall_seconds": 1, "agent_exit_code": 0, "timed_out": False,
            "usage": {"input_tokens": 1, "output_tokens": 1},
        }
        with self.assertRaisesRegex(ValueError, "duplicate task/repeat"):
            validate_arm([row, dict(row)], "x")

    def test_validate_arm_rejects_inconsistent_repeat_ids(self) -> None:
        rows = [
            {
                "arm": "x", "task": task, "repeat": repeat, "loc": 1,
                "wall_seconds": 1, "agent_exit_code": 0, "timed_out": False,
                "usage": {"input_tokens": 1, "output_tokens": 1},
            }
            for task, repeat in (("a", 1), ("a", 2), ("b", 1), ("b", 3))
        ]
        with self.assertRaisesRegex(ValueError, "inconsistent repeat IDs"):
            validate_arm(rows, "x")

    def test_repository_results_render_expected_winners(self) -> None:
        root = Path(__file__).resolve().parents[1]
        summary = summarize(
            root / "bench/runs/agentic-equal-model-001-merged/results.json",
            root / "bench/runs/dopamine-compact-v14-n4-001/results.json",
        )
        self.assertEqual(summary["winner_by_metric"]["loc"], "dopamine")
        self.assertEqual(summary["winner_by_metric"]["tokens"], "dopamine")
        self.assertEqual(summary["winner_by_metric"]["cost"], "dopamine")
        self.assertEqual(summary["winner_by_metric"]["time"], "dopamine")
        svg = render_svg(summary)
        self.assertEqual(summary["dopamine_tuning_runs_per_task"], 4)
        self.assertEqual(summary["trial_counts"]["dopamine"], 48)
        self.assertIn("Dopamine n=4 (48 trials)", svg)
        self.assertIn("not proof of “best overall.”", svg)


if __name__ == "__main__":
    unittest.main()
