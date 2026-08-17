# Phase 13 — IQ4_XS objective quality

## Decision

IQ4_XS is a credible **quality-oriented option**, but IQ2 remains the daily default. IQ4_XS passed 13 of 24 frozen objective tasks versus 10 for Q2 and 9 for IQ2. The lead is promising directionally, yet neither paired comparison was statistically significant and IQ4_XS's controlled 4K decode was 7.302 times slower than the full-GPU IQ2 operating point.

## Frozen pass@1 result

The IQ4_XS run reused the exact Phase 8 task text, order, graders, greedy sampling, seed, 4K context, Q8_0 target K/V, MTP-off state, and one-pass policy. All 24 requests completed with `stop` and the saved record passed independent suite-backed re-grading.

| Operating point | GPU layers | Passes | Pass rate |
|---|---:|---:|---:|
| IQ4_XS | 45/66 | 13/24 | 54.167% |
| UD-Q2_K_XL | 66/66 | 10/24 | 41.667% |
| UD-IQ2_XXS | 66/66 | 9/24 | 37.500% |

IQ4_XS category scores were 2/5 arithmetic, 3/5 logic, 2/5 Python trace, 4/5 structured output, and 2/4 text/data.

## Paired interpretation

Against Q2, 9 tasks passed for both, 4 passed only for IQ4_XS, 1 passed only for Q2, and 10 failed for both. The two-sided exact McNemar p-value was 0.375.

Against IQ2, 7 passed for both, 6 passed only for IQ4_XS, 2 passed only for IQ2, and 9 failed for both. The p-value was 0.289062.

These results support “IQ4_XS led on this small suite,” not “IQ4_XS is generally better.” The three operating points differ in both quantization and GPU residency, so this is not a quantization-only causal comparison.

## Practical choice

- Choose IQ2 for interactive daily work: the controlled repeated baseline was 43.643 tok/s versus 5.977 tok/s for IQ4_XS.
- Choose IQ4_XS selectively when a possible quality improvement is worth approximately 6 tok/s at 4K and hybrid CPU/GPU execution.
- Repeat with a larger external benchmark before making a general quality claim.

The [machine-readable summary](phase13-objective-quality.json) preserves raw hashes, category scores, paired counts, statistics, and limitations.
