# Dopamine agentic efficiency benchmark

Date: 2026-08-12 (America/Indiana/Indianapolis)

## Result

The measured Dopamine v14 candidate wins all four efficiency metrics against the recorded Ponytail result on this development set.

| Metric (mean per task; lower is better) | Baseline | Caveman | Ponytail | Dopamine v14 | Winner |
|---|---:|---:|---:|---:|---|
| Added source LOC | 138.5 | 98.3 | 52.1 | **50.2** | Dopamine |
| Processed tokens | 222,256 | 190,097 | 184,212 | **156,277** | Dopamine |
| Estimated API-equivalent cost | $0.1447 | $0.1198 | $0.1183 | **$0.1044** | Dopamine |
| Wall time | 87.2 s | 66.3 s | 64.9 s | **60.1 s** | Dopamine |

Normalized to the no-skill baseline, Dopamine measured 36.2% LOC, 70.3% tokens, 72.1% estimated cost, and 68.9% time. Ponytail measured 37.6%, 82.9%, 81.7%, and 74.4% respectively. Dopamine's four repeat-level means had sample standard deviations of 3.77 LOC, 14,307 tokens, $0.0083 estimated cost, and 3.41 seconds.

## What was measured

- Repository: `tiangolo/full-stack-fastapi-template`
- Fixture commit: `cd83fc10ca20393e9ee50e3005e170c6929e047e`
- Codex: `codex-cli 0.147.0`
- Model: `gpt-5.6-terra`
- Reasoning effort: `medium`
- Tasks: 12 identical frontend and backend feature tickets
- Repeats: four per Dopamine task; one per frozen reference-arm task
- LOC: added source lines from staged Git numstat, excluding tests, lock files, generated files, and non-code extensions
- Tokens: input plus output tokens from the final `turn.completed` event
- Time: process wall-clock seconds
- Cost: API-equivalent estimate, not observed subscription billing

The pricing snapshot recorded by the harness was $2.00 per million fresh input tokens, $0.20 per million cached input tokens, and $12.00 per million output tokens. Its source is the official GPT-5.6 Terra model page recorded in the manifests.

## Inputs and integrity

Published raw data:

- `bench/runs/agentic-equal-model-001-merged/results.json` — SHA-256 `6ca53e0f7b4c08297e1626d6e508b7e9b2e05b2afbcd839b89bb13772447cafb`
- `bench/runs/dopamine-compact-v14-n4-001/results.json` — SHA-256 `df511691abdae5d0a84e7d2ef3a4846b85b29daed842816df9897cc0898c4b2b`
- Dopamine v14 `SKILL.md` — SHA-256 `cf1d03db066527fe1f1aad927720a68dc27b35fa4179760cf948d191452b7720`

Pinned competitor skill hashes are recorded in the reference manifest. The reference run completed all 48 cells with no reported timeout or harness error. Its first eight-worker attempt stalled on five cells; those exact missing cells were rerun at one or two workers and merged. The v14 Dopamine n=4 run completed all 48 trials at eight workers with zero timeouts, zero nonzero exits, and a nonzero source diff in every trial.

Several experimental candidates were rejected or superseded, including:

- v8 completed but regressed to 66.9 LOC and 63.7 seconds per task.
- v9 produced no completed cells during an execution stall and was excluded entirely.
- v11 and v13 regressed on targeted high-LOC tasks.
- v12 reached 53.25 LOC per task before v14 reduced it to 48.58.

## Interpretation limits

This is development-set evidence, not a final unbiased leaderboard:

1. Dopamine was changed after inspecting results on these 12 tasks, then rerun on the same tasks.
2. Competitor results are frozen earlier measurements rather than simultaneous reruns with v14.
3. Dopamine has four repeats, but each competitor cell has only one. This estimates Dopamine's run-to-run dispersion but cannot estimate competitor uncertainty or a between-arm confidence interval.
4. The tickets do not have feature-completeness graders. A smaller diff can reflect either elegance or omitted behavior.
5. LOC, tokens, cost, and time measure efficiency, not security, maintainability, usability, or correctness.

Two executable development regression tasks were run against the older v7 candidate. The lab-unit task passed 30/48 checks, and the manufacturing normalization task passed 13/16. Both failed their overall graders. The machine-readable record is `bench/results/correctness-regressions.json`. v14 has not been rerun on these graders, so it has no correctness-complete evidence.

Therefore the defensible claim is: “On this 12-task tuning set, Dopamine v14 measured lower source LOC, tokens, estimated cost, and wall time than the recorded Ponytail run.” The data do not prove “Dopamine is best overall.”

## Reproduce the report

Generate the summary and SVG from the two raw result files:

```sh
python3 bench/report_agentic.py
```

Validate the repository:

```sh
python3 scripts/validate_skill.py
python3 -m unittest discover -s tests -v
```

Run Dopamine on the same task set:

```sh
python3 bench/run_agentic_metrics.py \
  --arms dopamine \
  --repeats 4 \
  --workers 8 \
  --model gpt-5.6-terra \
  --effort medium
```

## Protocol required for an overall claim

Freeze the skill hash, pre-register unseen tasks and executable correctness graders, run every arm in randomized or interleaved order with at least three repeats, report medians and uncertainty, and require every solution to pass the same correctness threshold before comparing efficiency. Do not modify the skill after viewing holdout results.
