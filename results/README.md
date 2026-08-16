# Results

- `raw/` contains append-only run records and raw model responses selected for publication.
- `summaries/` contains derived tables, statistics, and charts.
- `../schemas/benchmark-result.schema.json` is the formal result contract implemented in Phase 5.

Phases 1 through 3 include proof-of-life records for `UD-IQ2_XXS`, `UD-Q2_K_XL`, and the pinned native llama.cpp API. They are explicitly classified as proof-of-life rather than formal benchmarks; repeated measurements begin in Phase 4.

Phase 2 also includes a ten-task objective triage comparison. It supports configuration selection but is explicitly smaller than the planned Phase 8 quality evaluation.

Phase 3 retains both the failed 1/3 parser-configuration run and the corrected 3/3 run. Failed evidence is not deleted when it explains a configuration decision.

Phase 4 adds the first repeated baseline: one excluded warm-up and three measured IQ2 runs with streaming TTFT and continuous telemetry. The first attempt remains available because its configured 250 ms sampler actually ran at 300 ms; the canonical rerun records target and observed cadence separately.

Phase 5 replaces the earlier draft record example with a versioned Draft 2020-12 schema plus a semantic validator. Its short end-to-end smoke result is engineering evidence for the harness, not a replacement performance baseline.

The canonical Phase 5 raw file is `raw/phase5-python-iq2-smoke-20260816T005922932894Z-a280beda.json`; its interpretation checkpoint is `summaries/phase5-python-harness-checkpoint.md`.

Phase 6 adds a controlled IQ2-versus-Q2 pair produced from protocol commit `94a2735`. Both runs used one excluded warm-up, three measured repetitions, and identical 4K controls. Both models placed 66/66 layers on CUDA0; the result is therefore a quantization, speed, and memory comparison rather than a CPU-offload comparison.

The canonical Phase 6 raw files are `raw/phase6-iq2-comparison-20260816T014219897578Z-05ff3bf0.json` and `raw/phase6-q2-comparison-20260816T014417772434Z-91bc350d.json`. Their human and machine-readable interpretations are `summaries/phase6-iq2-vs-q2.md` and `summaries/phase6-iq2-vs-q2.json`.

Every summary value must be reproducible from committed raw data and a documented code version. Large diagnostic logs may remain local, but exclusions must be stated.
