# Phase 2 Quant Triage

Date: 2026-08-15

Classification: small quant-selection checkpoint, not a general quality benchmark.

## Method

Both quants received the same ten committed prompts at 4,096 context with one slot, Q8 K/V cache, flash attention on, temperature 0, seed 42, and thinking, speculative decoding, tools, and vision off. Each task used an exact-answer or semantic flat-JSON validator. The first response was graded as pass@1.

## Results

| Task | UD-IQ2_XXS | UD-Q2_K_XL |
|---|---:|---:|
| Inventory percentage | Fail | Fail |
| One-true-label logic | Pass | Pass |
| Python code trace | Fail | Fail |
| Strict JSON fields | Pass | Pass |
| Binary conversion | Fail | Pass |
| Combined revenue change | Fail | Fail |
| Syllogism | Pass | Pass |
| String transformation | Fail | Fail |
| Sort and middle product | Fail | Fail |
| First unique index | Fail | Pass |
| **Total** | **3/10** | **5/10** |

Q2_K_XL gained two passes and had no regression on a task that IQ2_XXS passed. The difference is 20 percentage points on this ten-task set.

IQ2_XXS reached the 64-token output limit on the combined-revenue and first-unique-index tasks despite instructions to return only the answer. Q2_K_XL stopped normally on all ten tasks. This is an instruction-following observation for this run, not proof of a general behavioral property.

## Tradeoff at this checkpoint

| Item | UD-IQ2_XXS | UD-Q2_K_XL |
|---|---:|---:|
| Triage pass@1 | 3/10 | 5/10 |
| First short engine generation rate | 44.3 tok/s | 38.9 tok/s |
| Loaded VRAM used | 8,958 MiB | 10,542 MiB |
| Loaded VRAM free | 3,037 MiB | 1,453 MiB |

Q2_K_XL showed a small objective advantage at the cost of approximately 12% lower first-observation generation speed and 1,584 MiB more loaded VRAM.

## Limitations

- Ten custom tasks are too few for a broad quality claim.
- There was one attempt per model and no confidence interval or repeat analysis.
- Temperature 0 reduces sampling variation but does not guarantee identical execution across runs.
- Thinking was disabled; enabling it could materially change reasoning-task outcomes and latency.
- Exact-answer tasks emphasize calculation and constraint following rather than conversation, knowledge, or coding usefulness.
- First short engine rates are diagnostic observations, not repeated performance benchmarks.

## Source records

- Prompt suite: `prompts/phase2-quant-triage.json`
- IQ2 result: `results/raw/quant-triage-ud-iq2-xxs-20260815T232512Z.json`
- Q2 result: `results/raw/quant-triage-ud-q2-k-xl-20260815T232426Z.json`
- Both results point to harness commit `4603f0c`.

## Phase 2 decision

- Provisional speed configuration: `UD-IQ2_XXS`
- Provisional quality-oriented configuration: `UD-Q2_K_XL`
- `UD-Q3_K_XL` download: not justified yet

The next phase should pin the native llama.cpp runtime and establish repeated performance baselines for these two selected configurations. The larger Q3 quant remains optional until stronger quality evidence or a specific use case requires it.
