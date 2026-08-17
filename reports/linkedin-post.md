# LinkedIn post draft

> **Status:** Phase 12 draft. Do not publish until the account, rendered text, attached graphic, and final submit action receive explicit approval.

## Post copy

I wanted to know whether a 27B local model could be genuinely practical on a Windows desktop with only 12 GB of VRAM—not just whether it could load.

So I adapted an RTX 4090 benchmarking plan for my Intel i7-14700K and RTX 4070 Ti, then turned it into a reproducible engineering study of Qwen3.8-27B GGUF inference.

Key findings:

• Both `UD-IQ2_XXS` and `UD-Q2_K_XL` fully offloaded all 66 layers at 4K context.

• IQ2 averaged 43.643 generation tok/s versus 38.030 for Q2. IQ2 was 14.759% faster and used 1,583 MiB less sampled peak VRAM.

• On a separate 24-task objective evaluation, Q2 passed 10 and IQ2 passed 9. The paired result did not support a meaningful general-quality advantage, so IQ2 remained the practical default.

• The tested IQ2 16K configuration handled a 12,831-token prompt plus 128 output tokens at 39.201 tok/s, with 11.119-second mean TTFT and 2,507 MiB minimum sampled VRAM free.

• In-model MTP increased throughput by 47.284% for prose and 92.651% for Python code. However, deterministic prose changed at generated token 16, so I kept MTP off by default rather than presenting it as a transparent optimization.

The project includes pinned model and runtime revisions, checksum validation, append-only raw JSON, GPU/process telemetry, objective graders, 61 offline tests, Windows CI, a strict release audit, and a public Hugging Face report.

My biggest takeaway: running a model is only the beginning. A credible local-AI project needs controlled variables, failure preservation, reproducible evidence, and conclusions that stay inside what the experiment actually measured.

GitHub: https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark

Hugging Face report: https://huggingface.co/unsloth/Qwen3.8-27B-GGUF/discussions/65

I would value feedback on the methodology and on which workload should be tested next.

#LocalLLM #AIEngineering #MachineLearning #OpenSource #NVIDIA

## Publication notes

- Attach `assets/phase12-benchmark-card.jpg`.
- Preserve the exact numerical precision above.
- Do not add a claim that Q2 is generally higher quality or that arbitrary 16K prompts are proven.
- Confirm the LinkedIn account and preview immediately before publishing.
