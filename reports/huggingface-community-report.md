# Performance report: Qwen3.8-27B on RTX 4070 Ti 12GB — IQ2 versus Q2

> **Draft template — only setup and proof-of-life runs exist. Every performance `TBD` must be replaced with repeated Phase 4+ data before publication.**

## Summary

TBD after measurements.

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
| Benchmark code commit | `25e51a01be6bcda5efbcb852ad77c32064290e5c` for the IQ2 baseline |

## Controlled settings

| Setting | Value |
|---|---|
| Context | 4,096 tokens |
| Parallel slots | 1 |
| KV cache | Q8 K and V |
| Thinking mode / reasoning effort | Off / not applicable |
| Preserve Thinking | Off |
| Sampling | temperature 0.6, top-p 0.95, top-k 20, min-p 0.0, seed 42 |
| Maximum output tokens | 128 for smoke; final benchmark value TBD |
| MTP | Off for baseline |
| Vision / mmproj | Off for baseline |

## Methodology

- Warm-up runs: 1, excluded from IQ2 statistics
- Measured repetitions: 3 for the current IQ2 baseline
- Prompt set: `phase4-iq2-baseline-v1`; one fixed 84-token prompt and 256-token output
- Telemetry interval: 250 ms target; 256.151 ms observed mean cadence
- Full methodology and scripts: TBD GitHub URL
- Raw result files: TBD GitHub URL

## Results

| Quant | GPU layers/offload | Loaded VRAM | Peak RAM | Prompt tok/s | Generation tok/s | TTFT | Total latency |
|---|---:|---:|---:|---:|---:|---:|---:|
| `UD-IQ2_XXS` | 66/66 GPU | 8,987 MiB | 9.629 GiB private | 935.648 | 43.171 | 94.950 ms | 6,001.517 ms |
| `UD-Q2_K_XL` | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

`UD-Q3_K_XL` and `UD-Q4_K_XL` are deferred; they will not appear as empty benchmark rows unless a later evidence gate justifies those downloads.

## Quality checks

TBD. Speed results alone will not be described as model-quality results.

## Failed configurations

TBD, including OOMs and settings that required adjustment.

## Interpretation

TBD after the raw results are reviewed.

## Limitations

- One Windows desktop and one GPU.
- Windows display activity shares VRAM with inference.
- A small quality benchmark cannot establish general model quality.
- Results depend on runtime, model revision, context, cache precision, sampling, and offload.
- This is a community benchmark, not an official Qwen or Unsloth evaluation.
