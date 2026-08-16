# Phase 8 objective quality comparison

Phase 8 compares `UD-Q2_K_XL` and `UD-IQ2_XXS` on 24 new, inspectable tasks under the same 4K llama.cpp configuration. Every task received one deterministic pass@1 attempt. Raw answers were graded by committed exact-text or semantic-JSON validators and independently re-graded from the saved files.

## Result

| Quant | Passed | Pass rate | Arithmetic | Logic | Python trace | Structured output | Text/data |
|---|---:|---:|---:|---:|---:|---:|---:|
| `UD-Q2_K_XL` | 10/24 | 41.667% | 0/5 | 2/5 | 1/5 | 5/5 | 2/4 |
| `UD-IQ2_XXS` | 9/24 | 37.500% | 0/5 | 2/5 | 1/5 | 4/5 | 2/4 |

Q2 led by one task, or 4.167 percentage points. Its only category-count advantage was structured output, where Q2 passed 5/5 and IQ2 passed 4/5.

## Paired outcomes

| Outcome | Tasks |
|---|---:|
| Both passed | 7 |
| Q2 only | 3 |
| IQ2 only | 2 |
| Neither passed | 12 |
| Discordant total | 5 |

The two-sided exact McNemar p-value is **1.0**. On this small custom suite, the three Q2-only versus two IQ2-only split supplies no evidence of a general quality difference. The one-task lead is descriptive only.

Q2-only tasks were the unique logic order, nested JSON object, and run-length encoding. IQ2-only tasks were the syllogism and matrix rotation. The remaining seven shared passes and twelve shared failures are enumerated in the machine-readable comparison.

## What pass@1 measured

Exact grading intentionally combines correctness with instruction following. A conceptually useful answer can fail if it adds prose, changes required decimal formatting, or wraps JSON in Markdown. There is no partial credit and no human override. This makes the score reproducible, but it is not the same as a human preference study.

Every saved request completed with `cache_n = 0`, usage and timings present, and no reasoning content. Both records use harness commit `87faba489917eb2140a4ac6702f94d54b0580543` and passed independent suite-backed re-grading.

## Protocol incident

The first Q2 attempt exposed a pre-write preservation bug when task 22 returned no final answer text. The server log showed all 24 requests completed, but the validator disagreed with the runner's failure-reason label and prevented the raw file from being written. That attempt has no usable score.

The public amendment records the local log hash and freezes a narrow correction: a successfully received empty answer is a completed request that earns zero quality credit; `no_response` is reserved for a request exception. No prompt, expected answer, grader, model setting, or comparison rule changed. Two regression tests were added, 50/50 tests passed, the correction was committed, and Q2 was restarted from a fresh hash-validated process. Because the prompts were repeated to Q2, this remains a disclosed limitation even though the model is stateless and caches were disabled.

## Decision

Keep `UD-IQ2_XXS` as the practical default. Phase 6 measured IQ2 decoding 14.759% faster than Q2 while using 1,583 MiB less peak VRAM, and Phase 8 does not show a meaningful quality advantage for Q2. Q2 can remain an optional strict-structured-output candidate, but this evidence does not justify calling it generally better.

## Evidence and limits

- Original protocol: `environment/phase8-quality-protocol-2026-08-15.json`, commit `ee64b11e048bc1a15c063cc41910cccad1e66017`
- Amendment: `environment/phase8-quality-protocol-amendment-2026-08-15.json`, commit `87faba489917eb2140a4ac6702f94d54b0580543`
- Q2 raw result: `results/raw/phase8-quality-q2-20260816T033656385280Z-2359f380.json`
- IQ2 raw result: `results/raw/phase8-quality-iq2-20260816T033811840476Z-8c67331b.json`
- Machine-readable derivation: `results/summaries/phase8-quality-comparison.json`

The result covers one desktop, two low-bit files, one runtime, one fixed order, and 24 custom tasks. It is not an official Qwen or Unsloth benchmark, does not estimate repeated-sampling variance, and must remain separate from the Phase 6 performance measurements.
