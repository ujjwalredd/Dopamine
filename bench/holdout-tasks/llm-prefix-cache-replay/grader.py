import json, pathlib, sys
workspace = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, '/Users/ujjwalreddyks/Desktop/Dopamine/bench/vendor/skillsbench/tasks/llm-prefix-cache-replay/verifier')
from oracle_helpers import load_trace, simulate
cfg = json.loads((workspace / "config.json").read_text())
trace = load_trace(workspace / "trace.jsonl")
s3 = cfg["s3fifo"]
expected = simulate(trace, cfg["block_size"], cfg["cache_capacity_blocks"], s3["small_ratio"], s3["max_freq"])
actual = json.loads((workspace / "report.json").read_text())
for key in ("total_requests", "total_prompt_tokens", "total_hit_tokens", "final_cache_blocks"):
    assert actual[key] == expected[key], (key, actual[key], expected[key])
assert abs(actual["overall_hit_rate"] - expected["overall_hit_rate"]) < 1e-6
assert len(actual["per_request"]) == len(expected["per_request"])
for idx in (133, 601, 968, 1459, 1999):
    assert actual["per_request"][idx] == expected["per_request"][idx]
assert sum(row["hit_tokens"] for row in actual["per_request"]) == actual["total_hit_tokens"]
assert sum(row["prompt_tokens"] for row in actual["per_request"]) == actual["total_prompt_tokens"]
print("PASS")
