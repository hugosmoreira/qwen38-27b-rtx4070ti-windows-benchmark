# Performance report: Qwen3.8-27B on RTX 4070 Ti 12GB — Q2/Q3/Q4 offload comparison

> **Draft template — no benchmark has been run. Every `TBD` must be replaced with traceable measured data before publication.**

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
| Runtime | TBD |
| CUDA backend | TBD |
| Model repository revision | TBD |
| Quant files | TBD |
| Benchmark code commit | TBD |

## Controlled settings

| Setting | Value |
|---|---|
| Context | TBD |
| Parallel slots | 1 |
| KV cache | TBD |
| Thinking mode / reasoning effort | TBD |
| Preserve Thinking | Off |
| Sampling | TBD |
| Maximum output tokens | TBD |
| MTP | TBD |
| Vision / mmproj | Off for baseline |

## Methodology

- Warm-up runs: TBD
- Measured repetitions: TBD
- Prompt set: TBD
- Telemetry interval: TBD
- Full methodology and scripts: TBD GitHub URL
- Raw result files: TBD GitHub URL

## Results

| Quant | GPU layers/offload | Loaded VRAM | Peak RAM | Prompt tok/s | Generation tok/s | TTFT | Total latency |
|---|---:|---:|---:|---:|---:|---:|---:|
| `UD-IQ2_XXS` | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| `UD-Q2_K_XL` | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| `UD-Q3_K_XL` | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| `UD-Q4_K_XL` | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

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

