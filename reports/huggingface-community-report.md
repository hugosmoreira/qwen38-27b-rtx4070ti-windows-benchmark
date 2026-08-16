# Performance report: Qwen3.8-27B on RTX 4070 Ti 12GB — IQ2 versus Q2

> **Draft — the controlled comparison is complete. Do not publish until the GitHub repository URLs are available and the complete report receives final review.**

## Summary

On one Windows desktop with an RTX 4070 Ti 12GB, both `UD-IQ2_XXS` and `UD-Q2_K_XL` fit with all 66 model layers on the GPU at 4K context. Across three measured 256-token runs per quant, IQ2 averaged 43.643 generation tok/s and Q2 averaged 38.030 tok/s. Relative to IQ2, Q2 decoded 12.861% slower and used 1,583 MiB more peak VRAM. Expressed in the other direction, IQ2 decoded 14.759% faster.

Q2 retains a small, separate quality signal from the earlier ten-task triage, where it passed 5/10 tasks versus IQ2's 3/10. This is candidate-selection evidence, not a broad model-quality estimate.

## Hardware

| Component | Value |
|---|---|
| GPU | NVIDIA GeForce RTX 4070 Ti, 12,282 MiB VRAM |
| CPU | Intel Core i7-14700K |
| RAM | 63.77 GB |
| OS | Windows 25H2, build 26200.9168 |
| NVIDIA driver | 610.88 |

## Software and models

| Item | Exact version/revision |
|---|---|
| Runtime | Official llama.cpp `b10448`, commit `ad1de39e0` |
| CUDA backend | Official Windows x64 CUDA 13.3 archive; NVIDIA driver 610.88 |
| Model repository revision | `1cff334a4a228324d4ee1f76d55d372588f0d556` |
| Quant files | `UD-IQ2_XXS` and `UD-Q2_K_XL` |
| Benchmark protocol commit | `94a27359f287ac5915f6b90664aa7e47844f3560` |

## Controlled settings

| Setting | Value |
|---|---|
| Context | 4,096 tokens |
| Parallel slots | 1 |
| KV cache | Q8 K and V |
| Thinking mode / reasoning effort | Off / not applicable |
| Preserve Thinking | Off |
| Sampling | temperature 0.6, top-p 0.95, top-k 20, min-p 0.0, seed 42 |
| Maximum output tokens | 256 |
| MTP | Off for the controlled comparison |
| Vision / mmproj | Off for the controlled comparison |

## Methodology

- Warm-up runs: 1 per quant, excluded from statistics
- Measured repetitions: 3 per quant
- Benchmark automation: `qwen_bench` 0.1.0 passed 25 offline tests before measurement
- Prompt set: `phase4-iq2-baseline-v1`; one fixed 84-token prompt and 256-token output
- Telemetry interval: 250 ms target; 253.350 ms observed mean cadence for IQ2 and 253.261 ms for Q2
- Full methodology and scripts: TBD GitHub URL
- Raw result files: TBD GitHub URL

## Results

| Quant | GPU layers/offload | Peak VRAM | Peak RAM | Prompt tok/s | Generation tok/s | TTFT | Total latency |
|---|---:|---:|---:|---:|---:|---:|---:|
| `UD-IQ2_XXS` | 66/66 GPU | 8,976 MiB | 9.621 GiB private | 943.278 | 43.643 | 91.272 ms | 5,934.130 ms |
| `UD-Q2_K_XL` | 66/66 GPU | 10,559 MiB | 11.167 GiB private | 995.095 | 38.030 | 86.622 ms | 6,791.962 ms |

`UD-Q3_K_XL` and `UD-Q4_K_XL` are deferred; they will not appear as empty benchmark rows unless a later evidence gate justifies those downloads.

## Quality checks

The earlier Phase 2 pass@1 triage used ten identical objective tasks. IQ2 passed 3/10 and Q2 passed 5/10. Q2's two unique wins support retaining it as the quality-oriented candidate, but ten tasks cannot establish general quality. The Phase 6 long-form response was not graded and adds no quality evidence.

## Failed configurations

Neither Phase 6 configuration failed or ran out of memory. Both fully offloaded 66/66 layers to CUDA0. Failed and superseded configurations from earlier phases remain preserved in the repository, but they were not part of this controlled pair.

## Interpretation

IQ2 is the practical speed default for this fixed 4K workload: it decoded 14.759% faster than Q2 and left approximately 1.55 GiB more VRAM headroom. Q2 processed the prompt and reached the first content token slightly faster, but decode dominated the 256-token response and increased mean total latency by 857.832 ms.

Q2 remains useful when its small Phase 2 quality signal matters more than the decode and memory cost. Because both models fit fully on the GPU, these measurements do not support a GPU-versus-CPU layer-offload claim.

## Limitations

- One Windows desktop and one GPU.
- Windows display activity shares VRAM with inference.
- A small quality benchmark cannot establish general model quality.
- Results depend on runtime, model revision, context, cache precision, sampling, and offload.
- This is a community benchmark, not an official Qwen or Unsloth evaluation.
