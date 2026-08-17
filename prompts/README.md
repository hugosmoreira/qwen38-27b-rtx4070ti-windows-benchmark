# Prompts

Prompts are versioned here with stable IDs and grading metadata.

Current suite:

- `phase1-smoke.json` contains three proof-of-life checks for exact text, arithmetic, and strict JSON. It confirms basic local inference and constraint following; it is not a quality benchmark.
- `phase2-quant-triage.json` contains ten objective exact-answer and JSON checks used only to decide whether the first two quants show an obvious pass@1 difference before another large download.
- `phase4-baseline.json` defines the fixed 256-token long-form streaming workload used for one warm-up and repeated IQ2 baseline measurements. It disables prompt caching and is a performance workload, not a quality test.
- `phase5-harness-smoke.json` is a 64-token, thinking-off, cache-off streamed workload used only to prove the Python harness end to end. It is deliberately shorter than the Phase 4 workload and must not be used for a performance comparison.
- `phase7-context-4k.json`, `phase7-context-8k.json`, and `phase7-context-16k.json` use the compact `numbered-records-v1` generator to create exact, hashable, public synthetic inputs near 78% of each window. The same final instruction and 128-token output reservation are used at every level. These prompts measure context sensitivity, not retrieval quality.
- `phase8-quality-evaluation.json` freezes 24 previously unseen, inspectable pass@1 tasks across arithmetic, logic, Python tracing, structured output, and text/data transformation. Exact and semantic JSON validators are committed with public grading notes; no partial credit or human override is allowed.
- `phase9-mtp-prose.json` and `phase9-mtp-code.json` provide two fixed 256-token greedy workloads for measuring MTP acceptance and speed. They share identical sampling settings and are performance workloads, not quality tests.
- `phase13-context-32k.json` and `phase13-context-64k-near-window.json` extend the same public numbered-record fixture at the fixed Phase 13 placement. The 64K fixture requires at least 60,000 actual prompt tokens; configured capacity alone does not satisfy its acceptance gate.
- `phase13-retrieval-16k.json` and `phase13-retrieval-64k.json` use deterministic `needle-records-v1` fixtures with exact planted values at early, middle, and late positions. The 16K suite pairs Q8_0 and Q4_0 target K/V; the 64K suite requires at least 60,000 observed prompt tokens for every task.

Each prompt definition should eventually identify:

- task ID and category;
- exact messages/system prompt;
- required thinking mode;
- maximum output tokens;
- grading method;
- fixture or test reference;
- whether the prompt contains public benchmark material.

Do not store private documents, credentials, or proprietary code in this directory.
