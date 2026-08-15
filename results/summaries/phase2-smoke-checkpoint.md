# Phase 2 Smoke Checkpoint

Date: 2026-08-15

Classification: proof of life, not a formal benchmark or quality evaluation.

## Controlled configuration

Both models used Unsloth Desktop's bundled llama.cpp runtime with 4,096 context, one parallel slot, Q8 K/V cache, batch 512, micro-batch 128, flash attention on, automatic GPU placement, and speculative decoding, thinking, tools, and vision off.

## Observations

| Observation | UD-IQ2_XXS | UD-Q2_K_XL | Q2 change |
|---|---:|---:|---:|
| GGUF file size | 8.39 GiB | 9.94 GiB | +1.55 GiB |
| Loaded VRAM used | 8,958 MiB | 10,542 MiB | +1,584 MiB |
| Loaded VRAM free | 3,037 MiB | 1,453 MiB | -1,584 MiB |
| Server-side load time | 7,125.47 ms | 8,781.03 ms | +23.2% |
| Auto-fit maximum context estimate | 41,728 | 12,544 | -29,184 |
| First short engine generation rate | 44.3 tok/s | 38.9 tok/s | -12.2% |
| First short engine prompt rate | 364.9 tok/s | 418.6 tok/s | +14.7% |
| Canonical smoke checks | 3/3 | 3/3 | no separation |

## Interpretation

`UD-Q2_K_XL` fits fully enough for the runtime to launch all 65 model layers with `-ngl -1` and no reported CPU fallback at 4K context. It consumes 1,584 MiB more VRAM and leaves only about 1.45 GiB free in the loaded snapshot.

The first short generation observation is approximately 12% slower than `UD-IQ2_XXS`. The three smoke checks cannot establish whether Q2_K_XL has better practical quality because both quants passed every basic constraint.

The prompt-rate difference and auto-fit context values must not be treated as benchmark conclusions. The requests are tiny, there are no repetitions, prompt caching and fixed overhead can dominate, and the auto-fit context is an estimate rather than a completed long-context run.

## Source records

- IQ2 runtime: `environment/phase1-unsloth-runtime-2026-08-15.json`
- IQ2 canonical smoke: `results/raw/phase1-smoke-20260815T225920Z.json`
- Q2 runtime: `environment/phase2-q2-k-xl-runtime-2026-08-15.json`
- Q2 canonical smoke: `results/raw/quant-smoke-ud-q2-k-xl-20260815T232000Z.json`
- Controlled prompts: `prompts/phase1-smoke.json`

Percentage change is `(Q2 / IQ2 - 1) × 100`. Memory and context changes are `Q2 - IQ2`.

## Decision

Keep `UD-IQ2_XXS` as the provisional speed configuration. Retain `UD-Q2_K_XL` as the provisional quality candidate, but do not claim a quality advantage until a small discriminating task suite is run with the same settings.
