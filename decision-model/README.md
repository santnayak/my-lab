# Lab #001 — Understanding decision models

October 5, 2026

I wanted to understand what changes when I ask the same question with Noul or Choice.

Started small: Ollama, `nimble`, and a question about rain in Berlin. Tried four states: no weather evidence, rain, dry weather, and conflicting forecasts.

Noul returned a probability of YES. Choice split its probabilities across YES, NO, and UNKNOWN. Both handled the clear forecasts well. The conflicting one surprised me: Noul still leaned strongly toward YES. Choice gave UNKNOWN more room, but YES still won.

I expected missing or conflicting evidence to make UNKNOWN useful. Giving the model that option didn't guarantee it would choose it. That's the next thing to explore.

With Ollama running and `nimble` available, run from this folder:

```sh
uv run 01_compare_noul_and_choice.py
```

The script saves the raw responses in `01_experiment_results.json` and a table in `01_experiment_results.md`. Each run replaces them.
