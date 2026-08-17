# X thread draft

> **Status:** Phase 12 draft. Do not publish until the account, complete thread order, attached graphic, and final submit action receive explicit approval.

## 1/8

I tested whether Qwen3.8-27B is genuinely practical on a Windows desktop with an RTX 4070 Ti 12GB—not just whether it can load. The result is a reproducible IQ2 vs Q2, 16K-context, and MTP study. 🧵

## 2/8

Test system: Intel i7-14700K, 64GB RAM, Windows, RTX 4070 Ti 12GB, and pinned llama.cpp b10448. Both UD-IQ2_XXS and UD-Q2_K_XL fully offloaded all 66 layers at 4K context.

## 3/8

Controlled 256-token comparison: IQ2 averaged 43.643 tok/s vs 38.030 for Q2. IQ2 was 14.759% faster and used 1,583 MiB less sampled peak VRAM, making IQ2 the practical default on this GPU.

## 4/8

Quality stayed separate from speed: Q2 passed 10/24 objective tasks vs 9/24 for IQ2. With only five discordant pairs and exact McNemar p=1.0, this did not support a meaningful general-quality advantage.

## 5/8

The tested IQ2 16K setup processed a 12,831-token prompt plus 128 output tokens at 39.201 tok/s. Mean TTFT was 11.119s, with 2,507 MiB minimum sampled VRAM free. This is a tested workload—not a universal 16K claim.

## 6/8

MTP was fast but not transparent: +47.284% throughput for prose and +92.651% for Python code. Code matched exactly, but deterministic prose diverged at generated token 16. MTP stays off by default.

## 7/8

The engineering work mattered as much as the headline speeds: pinned revisions, checksums, append-only raw JSON, telemetry, objective graders, 61 offline tests, Windows CI, and a strict public-evidence audit.

## 8/8

Repository and reproducible evidence:
https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark

Hugging Face report:
https://huggingface.co/unsloth/Qwen3.8-27B-GGUF/discussions/65

Methodology feedback is welcome.

## Publication notes

- Attach `assets/phase12-benchmark-card.jpg` to post 1/8.
- Publish in the declared order without merging claims across posts.
- The verified draft character counts for posts 1–8 are 198, 171, 188, 202, 214, 197, 208, and 227 against the standard 280-character limit; recheck before submission.
- Confirm the X account and the complete rendered thread immediately before publishing.
