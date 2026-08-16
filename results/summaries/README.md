# Result Summaries

Comparison tables and charts are stored here together with enough metadata to identify their source raw runs.

Current summary:

- `phase2-smoke-checkpoint.md` compares the two proof-of-life configurations and explicitly limits interpretation before repeated benchmarking and quality evaluation.
- `phase2-quant-triage.md` records the objective ten-task pass@1 checkpoint used to select the two provisional configurations.
- `phase3-native-checkpoint.md` records the pinned official llama.cpp runtime, CUDA/offload proof, native API smoke result, and Phase 4 handoff.
- `phase4-iq2-baseline.md` reports the warm-up policy, three measured repetitions, independent variance checks, telemetry coverage, and strict interpretation boundary for the IQ2 baseline.
- `phase5-python-harness-checkpoint.md` records the isolated Python package, 23-test gate, formal/semantic schemas, and successful end-to-end engineering smoke without treating one short run as a performance baseline.
- `phase6-iq2-vs-q2.md` reports the controlled 4K IQ2-versus-Q2 performance and memory tradeoff, variation, telemetry coverage, separate quality context, and interpretation boundary.
- `phase6-iq2-vs-q2.json` preserves the same comparison in a machine-readable derived record with explicit formulas and source paths.
