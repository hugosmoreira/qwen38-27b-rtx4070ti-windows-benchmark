# Phase 13 — IQ4_XS long-context retrieval

## Decision

Q4_0 target K/V is a validated **long-context candidate** for this pinned IQ4_XS setup. It matched Q8_0 at 16K on all three frozen exact-retrieval tasks and passed all three near-64K tasks. The evidence is strong enough for a practical profile recommendation, but not for a claim that Q4 and Q8 caches have equal quality.

## Objective result

All runs used IQ4_XS at 40/66 GPU layers, one slot, MTP off, thinking off, prompt cache off, greedy decoding, and the same exact-match grading.

| Profile | Actual prompt tokens | Exact retrieval | Mean TTFT | Mean prompt tok/s | Mean decode tok/s |
|---|---|---:|---:|---:|---:|
| 16K / Q4_0 KV | 12,806–12,809 | 3/3 | 61.043 s | 209.879 | 3.628 |
| 16K / Q8_0 KV | 12,806–12,809 | 3/3 | 61.163 s | 209.440 | 3.591 |
| 64K / Q4_0 KV | 60,015–60,016 | 3/3 | 301.024 s | 199.395 | 1.571 |

The needles appeared at early, middle, and late positions. The exact answers were `COBALT-731`, `MARBLE-482`, and `ZEPHYR-915` at 16K, and `TOPAZ-164`, `ONYX-583`, and `SAFFRON-927` near 64K.

## Preserved protocol incident

The first near-64K attempt returned all three correct answers but contained only 59,991–59,992 tokenizer-observed prompt tokens, below the precommitted 60,000-token gate. That record remains classified as superseded. A committed amendment added exactly one deterministic filler record, changed no needle, grader, or runtime control, and a fresh run produced 60,015–60,016 tokens.

## Interpretation boundary

Nine exact-retrieval requests cannot establish broad long-context quality. The suite does not test multi-hop synthesis, realistic documents, adversarial distractors, or stochastic variance. Near-64K also required roughly five minutes before the first answer token, so it remains a capacity/research profile rather than an interactive default.

The [machine-readable summary](phase13-retrieval-quality.json) records hashes, timings, exact answers, and the amendment boundary.
