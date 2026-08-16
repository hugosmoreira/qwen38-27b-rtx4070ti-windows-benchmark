# Community report: Qwen3.8-27B on RTX 4070 Ti 12GB — IQ2 versus Q2

> **Draft — the controlled comparison is complete. Do not publish until the GitHub repository URLs are available and the complete report receives final review.**

## Summary

On one Windows desktop with an RTX 4070 Ti 12GB, both `UD-IQ2_XXS` and `UD-Q2_K_XL` fit with all 66 model layers on the GPU at 4K context. Across three measured 256-token runs per quant, IQ2 averaged 43.643 generation tok/s and Q2 averaged 38.030 tok/s. Relative to IQ2, Q2 decoded 12.861% slower and used 1,583 MiB more peak VRAM. Expressed in the other direction, IQ2 decoded 14.759% faster.

In a separate 24-task objective pass@1 evaluation, Q2 passed 10 tasks and IQ2 passed 9. Paired outcomes were 7 both-pass, 3 Q2-only, 2 IQ2-only, and 12 neither-pass, with two-sided exact McNemar p = 1.0. The one-task Q2 lead is descriptive and does not show a meaningful general-quality advantage.

In a separate IQ2 context ladder, the tested 16K configuration processed 12,831 prompt tokens plus 128 completion tokens with 11.119-second mean TTFT, 39.201 generation tok/s, and 2,507 MiB minimum sampled VRAM free. All 66 layers remained on the GPU.

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
| Performance protocol commit | `94a27359f287ac5915f6b90664aa7e47844f3560` |
| Quality protocol / amendment commits | `ee64b11e048bc1a15c063cc41910cccad1e66017` / `87faba489917eb2140a4ac6702f94d54b0580543` |

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

## IQ2 context sensitivity

Each level used a fresh process, one excluded warm-up, three measured repetitions, and a deterministic public prompt near 78% of the configured window.

| Context | Actual prompt | Output | Prompt tok/s | Generation tok/s | TTFT | Peak VRAM | Minimum free VRAM |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 4K | 3,231 | 128 | 1,202.952 | 41.124 | 2,692.911 ms | 9,028 MiB | 2,967 MiB |
| 8K | 6,423 | 128 | 1,187.733 | 40.522 | 5,418.174 ms | 9,182 MiB | 2,813 MiB |
| 16K | 12,831 | 128 | 1,155.757 | 39.201 | 11,118.874 ms | 9,488 MiB | 2,507 MiB |

The largest sensible tested context is 16K under the precommitted project thresholds. From 4K to 16K, decode throughput declined 4.676% and peak VRAM increased 460 MiB. The test establishes this specific 12,831-plus-128-token workload, not arbitrary full-window prompts or long-context retrieval quality.

## Objective quality evaluation

The quality suite contains 24 new inspectable tasks across arithmetic, logic, Python tracing, structured output, and text/data transformations. Each quant received one deterministic attempt in the same order from a fresh 4K server. Temperature was 0.0, seed was 42, prompt caching and thinking were disabled, and every saved response was independently re-graded against the committed suite. Exact grading gives no partial credit and measures both answer correctness and required-format adherence.

| Quant | Overall | Arithmetic | Logic | Python trace | Structured output | Text/data |
|---|---:|---:|---:|---:|---:|---:|
| `UD-Q2_K_XL` | 10/24 | 0/5 | 2/5 | 1/5 | 5/5 | 2/4 |
| `UD-IQ2_XXS` | 9/24 | 0/5 | 2/5 | 1/5 | 4/5 | 2/4 |

Q2 led by one task, or 4.167 percentage points. Only five pairs were discordant: three favored Q2 and two favored IQ2. The two-sided exact McNemar p-value was 1.0. This custom suite is not a random or validated benchmark population, so the result should not be generalized beyond the tested prompts.

The first Q2 attempt exposed a pre-write preservation bug when one request completed with an empty answer. The server log showed 24/24 requests completed, but the validator disagreed with the runner's failure-reason label and no raw score was written. A public protocol amendment hashes that local log and freezes a narrow correction: a received empty answer is a completed request with zero quality credit. No prompt, expected answer, grader, or inference control changed. The model is stateless and caches were disabled, but the repeated Q2 prompt exposure remains disclosed as a limitation.

## Failed configurations

Neither Phase 6 configuration failed or ran out of memory. Both fully offloaded 66/66 layers to CUDA0. Failed and superseded configurations from earlier phases remain preserved in the repository, but they were not part of this controlled pair.

## Interpretation

IQ2 is the practical default for this setup: it decoded 14.759% faster than Q2, left approximately 1.55 GiB more VRAM headroom, and finished only one task behind Q2 in the separate 24-task evaluation. Q2 processed the performance prompt and reached the first content token slightly faster, but decode dominated the 256-token response and increased mean total latency by 857.832 ms.

Q2's perfect 5/5 structured-output score makes it an optional candidate for strict-output experiments, but its 10/24 versus 9/24 overall result does not justify calling it generally higher quality. Because both models fit fully on the GPU, these measurements also do not support a GPU-versus-CPU layer-offload claim.

## Limitations

- One Windows desktop and one GPU.
- Windows display activity shares VRAM with inference.
- The 24-task custom quality suite cannot establish general model quality, and pass@1 exact grading combines correctness with format adherence.
- The first Q2 task exposure was superseded after a disclosed pre-write preservation bug; the corrected raw comparison restarted Q2 from a fresh process.
- The 16K context result used 12,831 prompt tokens and 128 completion tokens; it is not a full-window capacity or retrieval-quality claim.
- Results depend on runtime, model revision, context, cache precision, sampling, and offload.
- This is a community benchmark, not an official Qwen or Unsloth evaluation.
