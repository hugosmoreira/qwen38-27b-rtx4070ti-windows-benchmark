# Phase 4 IQ2 repeated baseline

Phase 4 establishes a repeatable performance baseline for the selected speed configuration, `UD-IQ2_XXS`, on the pinned native llama.cpp runtime. It does not compare quants or evaluate response quality.

## Controlled method

| Control | Value |
|---|---|
| Runtime | llama.cpp `b10448`, commit `ad1de39e0` |
| Harness revision | `25e51a0` |
| Model | `Qwen3.8-27B-UD-IQ2_XXS.gguf` |
| Context / parallel slots | 4,096 / 1 |
| GPU placement | CUDA0, 66/66 layers offloaded |
| KV cache / Flash Attention | Q8 K+V / on |
| Thinking / MTP / tools / vision | off / off / off / off |
| Workload | fixed 84-token database-transaction prompt |
| Output | 256 tokens, `finish_reason = length` |
| Prompt cache | disabled; `cache_n = 0` in every run |
| Warm-up | one excluded run in an already-loaded server session |
| Measured repetitions | three |
| Telemetry | 250 ms target; 256.151 ms observed mean cadence |

TTFT is client wall time from sending the HTTP request until the first non-empty assistant content delta arrives over SSE. Total latency runs through the SSE done marker. Server prompt/decode rates come from llama.cpp's final timing object.

## Measured runs

| Run | TTFT (ms) | Total latency (ms) | Prompt tok/s | Generation tok/s | Peak VRAM (MiB) | Peak GPU |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 96.706 | 6,008.894 | 936.131 | 43.124 | 8,987 | 98% |
| 2 | 94.209 | 5,999.153 | 935.547 | 43.185 | 8,987 | 98% |
| 3 | 93.935 | 5,996.504 | 935.266 | 43.203 | 8,987 | 98% |

## Aggregate statistics

| Metric | Mean | Sample SD | CV | Minimum | Maximum |
|---|---:|---:|---:|---:|---:|
| TTFT (ms) | 94.950 | 1.527 | 1.608% | 93.935 | 96.706 |
| Total latency (ms) | 6,001.517 | 6.525 | 0.109% | 5,996.504 | 6,008.894 |
| Prompt tok/s | 935.648 | 0.441 | 0.047% | 935.266 | 936.131 |
| Generation tok/s | 43.171 | 0.041 | 0.096% | 43.124 | 43.203 |

Generation throughput and total latency are highly stable for this workload. TTFT has the largest CV, but its full measured range is only 2.771 ms. The excluded warm-up TTFT was 113.360 ms, which supports keeping a warm-up policy even though model weights were already loaded.

## Telemetry checkpoint

- Each measured run retained 25 samples across the complete six-second response.
- Observed cadence ranged from 250.458 to 275.010 ms, averaging 256.151 ms across runs.
- Peak VRAM was 8,987 MiB used with 3,008 MiB free.
- Peak GPU utilization was 98% in every measured repetition.
- The highest sampled GPU temperature was 71°C and power draw was 264.10 W.
- Mean peak llama-server working set was 8.395 GiB; mean peak private memory was 9.629 GiB. These are different Windows memory views and must not be added.
- Mean sampled peak process CPU was 3.975% of the 28-logical-processor machine, equivalent to roughly 1.113 fully occupied logical cores.

## Superseded attempt

The earlier [raw attempt](../raw/phase4-iq2-baseline-20260816T001639Z.json) is preserved. Its performance values were valid, but its helper slept 250 ms after collection work, creating a 300 ms actual cadence while labeling the interval as 250 ms. The canonical [raw result](../raw/phase4-iq2-baseline-20260816T001913Z.json) comes from the corrected sampler and records both target and observed cadence.

## Interpretation boundary

This result supports a narrow statement: on this machine and configuration, one fixed 84-token prompt followed by a 256-token decode runs at about 43.17 generation tok/s with very low repetition variance.

It does not establish cold-start speed, general prompt performance, model quality, larger-context behavior, multi-user throughput, or the tradeoff against `UD-Q2_K_XL`. Those remain later controlled phases.
