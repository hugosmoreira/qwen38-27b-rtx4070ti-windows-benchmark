# Prompts

Prompts are versioned here with stable IDs and grading metadata.

Current suite:

- `phase1-smoke.json` contains three proof-of-life checks for exact text, arithmetic, and strict JSON. It confirms basic local inference and constraint following; it is not a quality benchmark.
- `phase2-quant-triage.json` contains ten objective exact-answer and JSON checks used only to decide whether the first two quants show an obvious pass@1 difference before another large download.
- `phase4-baseline.json` defines the fixed 256-token long-form streaming workload used for one warm-up and repeated IQ2 baseline measurements. It disables prompt caching and is a performance workload, not a quality test.
- `phase5-harness-smoke.json` is a 64-token, thinking-off, cache-off streamed workload used only to prove the Python harness end to end. It is deliberately shorter than the Phase 4 workload and must not be used for a performance comparison.

Each prompt definition should eventually identify:

- task ID and category;
- exact messages/system prompt;
- required thinking mode;
- maximum output tokens;
- grading method;
- fixture or test reference;
- whether the prompt contains public benchmark material.

Do not store private documents, credentials, or proprietary code in this directory.
