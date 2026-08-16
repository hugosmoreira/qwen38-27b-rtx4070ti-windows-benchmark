# Qwen3.8-27B on an RTX 4070 Ti 12GB: IQ2 vs Q2, 16K context, and MTP

This community report summarizes a reproducible Windows study. The public [GitHub repository](https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark) contains the frozen protocols, raw responses, validation code, and limitations; no model weights are redistributed.

## Summary

On one Windows desktop with an RTX 4070 Ti 12GB, both `UD-IQ2_XXS` and `UD-Q2_K_XL` fit with all 66 model layers on the GPU at 4K context. Across three measured 256-token runs per quant, IQ2 averaged 43.643 generation tok/s and Q2 averaged 38.030 tok/s. Relative to IQ2, Q2 decoded 12.861% slower and used 1,583 MiB more peak VRAM. Expressed in the other direction, IQ2 decoded 14.759% faster. [Performance evidence and calculation direction](https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark/blob/main/results/summaries/phase6-iq2-vs-q2.md)

In a separate 24-task objective pass@1 evaluation, Q2 passed 10 tasks and IQ2 passed 9. Paired outcomes were 7 both-pass, 3 Q2-only, 2 IQ2-only, and 12 neither-pass, with two-sided exact McNemar p = 1.0. The one-task Q2 lead is descriptive and does not show a meaningful general-quality advantage. [Quality evidence and paired analysis](https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark/blob/main/results/summaries/phase8-quality-comparison.md)

In a separate IQ2 context ladder, the tested 16K configuration processed 12,831 prompt tokens plus 128 completion tokens with 11.119-second mean TTFT, 39.201 generation tok/s, and 2,507 MiB minimum sampled VRAM free. All 66 layers remained on the GPU. [Context-ladder evidence and thresholds](https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark/blob/main/results/summaries/phase7-context-sensitivity.md)

An isolated IQ2 `draft-mtp` experiment increased 256-token generation throughput by 47.284% on prose and 92.651% on Python code while adding 554–568 MiB sampled peak VRAM. Code output matched exactly across MTP states, but deterministic prose diverged at generated token 16. MTP therefore remains off by default for this pinned runtime. [MTP evidence, acceptance, and output-equivalence analysis](https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark/blob/main/results/summaries/phase9-mtp-comparison.md)

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
| Performance protocol commit | [`94a2735`](https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark/commit/94a27359f287ac5915f6b90664aa7e47844f3560) |
| Quality protocol / amendment commits | [`ee64b11`](https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark/commit/ee64b11e048bc1a15c063cc41910cccad1e66017) / [`87faba4`](https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark/commit/87faba489917eb2140a4ac6702f94d54b0580543) |
| MTP protocol commit | [`e3c950f`](https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark/commit/e3c950f15407182e45de778071c9ff4c94dac7c6) |

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
- Full methodology and scripts: [GitHub repository](https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark)
- Raw result files: [committed raw evidence](https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark/tree/main/results/raw)
- Reproduction workflow: [clean-clone and hardware instructions](https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark/blob/main/REPRODUCING.md)
- Evidence classification: [`v0.1.0` canonical/superseded manifest](https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark/blob/main/release/v0.1.0-manifest.json)

## Results

| Quant | GPU layers/offload | Peak VRAM | Peak RAM | Prompt tok/s | Generation tok/s | TTFT | Total latency |
|---|---:|---:|---:|---:|---:|---:|---:|
| `UD-IQ2_XXS` | 66/66 GPU | 8,976 MiB | 9.621 GiB private | 943.278 | 43.643 | 91.272 ms | 5,934.130 ms |
| `UD-Q2_K_XL` | 66/66 GPU | 10,559 MiB | 11.167 GiB private | 995.095 | 38.030 | 86.622 ms | 6,791.962 ms |

`UD-Q3_K_XL` and `UD-Q4_K_XL` are deferred; they will not appear as empty benchmark rows unless a later evidence gate justifies those downloads.

Evidence: [Phase 6 derived comparison](https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark/blob/main/results/summaries/phase6-iq2-vs-q2.md), [IQ2 raw record](https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark/blob/main/results/raw/phase6-iq2-comparison-20260816T014219897578Z-05ff3bf0.json), and [Q2 raw record](https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark/blob/main/results/raw/phase6-q2-comparison-20260816T014417772434Z-91bc350d.json).

## IQ2 context sensitivity

Each level used a fresh process, one excluded warm-up, three measured repetitions, and a deterministic public prompt near 78% of the configured window.

| Context | Actual prompt | Output | Prompt tok/s | Generation tok/s | TTFT | Peak VRAM | Minimum free VRAM |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 4K | 3,231 | 128 | 1,202.952 | 41.124 | 2,692.911 ms | 9,028 MiB | 2,967 MiB |
| 8K | 6,423 | 128 | 1,187.733 | 40.522 | 5,418.174 ms | 9,182 MiB | 2,813 MiB |
| 16K | 12,831 | 128 | 1,155.757 | 39.201 | 11,118.874 ms | 9,488 MiB | 2,507 MiB |

The largest sensible tested context is 16K under the precommitted project thresholds. From 4K to 16K, decode throughput declined 4.676% and peak VRAM increased 460 MiB. The test establishes this specific 12,831-plus-128-token workload, not arbitrary full-window prompts or long-context retrieval quality.

Evidence: [Phase 7 derived comparison](https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark/blob/main/results/summaries/phase7-context-sensitivity.md) and the [4K](https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark/blob/main/results/raw/phase7-iq2-context-4k-20260816T022507577973Z-623ca28d.json), [8K](https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark/blob/main/results/raw/phase7-iq2-context-8k-20260816T022627198977Z-5778e8f6.json), and [16K](https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark/blob/main/results/raw/phase7-iq2-context-16k-20260816T022758735205Z-51fce8fc.json) raw records.

## Objective quality evaluation

The quality suite contains 24 new inspectable tasks across arithmetic, logic, Python tracing, structured output, and text/data transformations. Each quant received one deterministic attempt in the same order from a fresh 4K server. Temperature was 0.0, seed was 42, prompt caching and thinking were disabled, and every saved response was independently re-graded against the committed suite. Exact grading gives no partial credit and measures both answer correctness and required-format adherence.

| Quant | Overall | Arithmetic | Logic | Python trace | Structured output | Text/data |
|---|---:|---:|---:|---:|---:|---:|
| `UD-Q2_K_XL` | 10/24 | 0/5 | 2/5 | 1/5 | 5/5 | 2/4 |
| `UD-IQ2_XXS` | 9/24 | 0/5 | 2/5 | 1/5 | 4/5 | 2/4 |

Q2 led by one task, or 4.167 percentage points. Only five pairs were discordant: three favored Q2 and two favored IQ2. The two-sided exact McNemar p-value was 1.0. This custom suite is not a random or validated benchmark population, so the result should not be generalized beyond the tested prompts.

The first Q2 attempt exposed a pre-write preservation bug when one request completed with an empty answer. The server log showed 24/24 requests completed, but the validator disagreed with the runner's failure-reason label and no raw score was written. A public protocol amendment hashes that local log and freezes a narrow correction: a received empty answer is a completed request with zero quality credit. No prompt, expected answer, grader, or inference control changed. The model is stateless and caches were disabled, but the repeated Q2 prompt exposure remains disclosed as a limitation.

Evidence: [Phase 8 derived comparison](https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark/blob/main/results/summaries/phase8-quality-comparison.md), [Q2 raw record](https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark/blob/main/results/raw/phase8-quality-q2-20260816T033656385280Z-2359f380.json), and [IQ2 raw record](https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark/blob/main/results/raw/phase8-quality-iq2-20260816T033811840476Z-8c67331b.json).

## IQ2 in-model MTP experiment

The MTP comparison used the same IQ2 GGUF at 4K with one slot and all 66 target layers on CUDA0. Both workload pairs used greedy decoding, seed 42, 256 output tokens, one excluded warm-up, and five measured repetitions per state from fresh processes. MTP activated the embedded NextN layer with `draft-mtp`, `n_max = 2`, `n_min = 0`, and an F16 draft K/V cache.

| Workload | Off tok/s | On tok/s | Speed change | Draft acceptance | Peak VRAM change | Exact output match |
|---|---:|---:|---:|---:|---:|---:|
| Prose | 42.152 | 62.083 | +47.284% | 55.187% | +568 MiB | 0/5 |
| Python code | 42.414 | 81.711 | +92.651% | 90.110% | +554 MiB | 5/5 |

Every response was internally deterministic within its own state. The code hashes matched across both states. The prose hashes did not, and the first difference appeared at zero-based generated token 16 even though both responses contained 256 tokens. These prompts were not quality-graded, so this is evidence of output non-equivalence, not evidence that either prose response was better. The workload-specific speeds are not pooled.

Evidence: [Phase 9 derived comparison](https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark/blob/main/results/summaries/phase9-mtp-comparison.md) and the four classified MTP records in the [raw-evidence directory](https://github.com/hugosmoreira/qwen38-27b-rtx4070ti-windows-benchmark/tree/main/results/raw).

## Failed configurations

Neither Phase 6 configuration failed or ran out of memory. Both fully offloaded 66/66 layers to CUDA0. Failed and superseded configurations from earlier phases remain preserved in the repository, but they were not part of this controlled pair.

## Interpretation

IQ2 is the practical default for this setup: it decoded 14.759% faster than Q2, left approximately 1.55 GiB more VRAM headroom, and finished only one task behind Q2 in the separate 24-task evaluation. Q2 processed the performance prompt and reached the first content token slightly faster, but decode dominated the 256-token response and increased mean total latency by 857.832 ms.

Q2's perfect 5/5 structured-output score makes it an optional candidate for strict-output experiments, but its 10/24 versus 9/24 overall result does not justify calling it generally higher quality. Because both models fit fully on the GPU, these measurements also do not support a GPU-versus-CPU layer-offload claim.

MTP remains off by default because it did not preserve output across both deterministic workloads. The large code speedup makes it a useful opt-in candidate only after application-specific correctness and output regression tests.

## Limitations

- One Windows desktop and one GPU.
- Windows display activity shares VRAM with inference.
- The 24-task custom quality suite cannot establish general model quality, and pass@1 exact grading combines correctness with format adherence.
- The first Q2 task exposure was superseded after a disclosed pre-write preservation bug; the corrected raw comparison restarted Q2 from a fresh process.
- The 16K context result used 12,831 prompt tokens and 128 completion tokens; it is not a full-window capacity or retrieval-quality claim.
- Results depend on runtime, model revision, context, cache precision, sampling, and offload.
- The MTP experiment used two synthetic workloads and draft depth two; one prose mismatch prevents treating MTP as a transparent optimization in this build.
- This is a community benchmark, not an official Qwen or Unsloth evaluation.
