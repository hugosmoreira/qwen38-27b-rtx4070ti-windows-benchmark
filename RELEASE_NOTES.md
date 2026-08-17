# v0.1.0

This release packages an auditable Windows study of Qwen3.8-27B GGUF inference on an RTX 4070 Ti 12 GB. It includes the benchmark software, frozen protocols, prompts and graders, machine-readable environment records, canonical raw responses, derived comparisons, and explicit superseded evidence. Model weights and runtime archives are not included.

## Headline findings

- Both `UD-IQ2_XXS` and `UD-Q2_K_XL` fully offloaded 66/66 layers at 4K context.
- IQ2 averaged 43.643 generation tok/s versus 38.030 for Q2 and used 1,583 MiB less sampled peak VRAM.
- On 24 paired objective tasks, Q2 passed 10 and IQ2 passed 9; exact McNemar `p = 1.0` did not support a directional quality claim.
- IQ2 completed the tested 16K configuration with a 12,831-token prompt plus 128 generated tokens, 39.201 generation tok/s, and 2,507 MiB minimum sampled free VRAM.
- MTP increased throughput 47.284% for prose and 92.651% for code, but prose output diverged at generated token 16. MTP remains off by default.
- Hybrid IQ4_XS completed at 5.977 tok/s with 45/66 GPU layers at 4K/Q8; the matched full-GPU IQ2 operating point was 7.302 times faster.
- IQ4_XS passed 3/3 exact retrieval tasks at matched 16K Q4_0 and Q8_0 profiles, then 3/3 at 60,015–60,016 prompt tokens with Q4_0.
- IQ4_XS passed 13/24 objective tasks versus Q2 at 10/24 and IQ2 at 9/24. Exact paired p-values of 0.375 and 0.289 make this a descriptive lead, not proof of general superiority.
- IQ4_XS MTP changed outputs in both workloads, added about 490–496 MiB peak VRAM, and improved decode by only 0.519% for prose and 14.958% for code; it remains off by default.

## Reproduce and inspect

No GPU or model download is required to run the 71-test software suite, validate canonical records, check public links, and audit release boundaries. See the [reproduction guide](https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark/blob/v0.1.0/REPRODUCING.md).

## Publication state

Final GitHub Release [`v0.1.0`](https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark/releases/tag/v0.1.0) was published on 2026-08-17 at commit `d1a6056`. Its Windows CI matrix passes on Python 3.11 and 3.14. The Phase 11 report is public as [Hugging Face Community Discussion #65](https://huggingface.co/unsloth/Qwen3.8-27B-GGUF/discussions/65), with this repository retained as the evidence system of record.

## Interpretation boundary

The results apply to one declared Windows machine, pinned model files, llama.cpp `b10448`, and the committed workloads. They do not establish general model quality, universal context capacity, or performance on other systems. IQ4_XS is tested, while the differently named `UD-Q3_K_XL`, `UD-Q4_K_XL`, vision, and Unsloth-versus-native convenience comparisons remain deferred.
