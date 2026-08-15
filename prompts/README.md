# Prompts

Prompts are versioned here with stable IDs and grading metadata.

Current suite:

- `phase1-smoke.json` contains three proof-of-life checks for exact text, arithmetic, and strict JSON. It confirms basic local inference and constraint following; it is not a quality benchmark.

Each prompt definition should eventually identify:

- task ID and category;
- exact messages/system prompt;
- required thinking mode;
- maximum output tokens;
- grading method;
- fixture or test reference;
- whether the prompt contains public benchmark material.

Do not store private documents, credentials, or proprietary code in this directory.
