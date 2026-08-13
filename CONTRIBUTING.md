# Contributing

Contributions are welcome when they improve verified task quality or efficiency without weakening safety.

1. Open an issue describing the observed failure mode and a reproducible task.
2. Keep `SKILL.md` concise and avoid task-specific benchmark answers.
3. Run `python3 scripts/validate_skill.py` and `python3 -m unittest discover -s tests -v`.
4. Report both positive and negative benchmark results. Do not tune on a holdout after inspecting its results.
5. Submit focused changes and explain which evidence supports them.

By contributing, you agree that your contribution is licensed under the MIT License.
