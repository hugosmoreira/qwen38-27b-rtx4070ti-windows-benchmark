# Phase 13 active-context ladder

## Outcome

`IQ4_XS` completed the frozen 4K, 16K, 32K, and 64K ladder at one fixed 40/66-layer placement with Q4_0 K/V cache. The largest request actually ingested 60,015 prompt tokens and generated 128 tokens in all three measured repetitions. This is evidence of near-window active-context operation, not merely successful `-c 65536` allocation.

The tradeoff is severe enough to matter: 64K averaged 301.27 seconds to first content and 1.569 generation tok/s. It is a successful capacity/research profile, not a comfortable interactive default.

## Fixed controls

- Model: `Qwen3.8-27B-IQ4_XS.gguf`, SHA-256 `9fd40d70…ace666`
- Runtime: llama.cpp `b10448`, commit `ad1de39e0…`
- Placement: 40/66 layers on CUDA0 at every level
- K/V cache: Q4_0 for both K and V
- One slot, flash attention on, prompt cache off, MTP off, thinking off
- One excluded warm-up and three measured repetitions per level
- 128 generated tokens per request

The 64K/Q4_0 allocation frontier selected 40 layers before these prompts were frozen. The frontier itself used a short request and remains diagnostic; only the ladder below supports active-prompt claims.

## Results

| Configured context | Actual prompt | Window used | Prompt tok/s | TTFT | Generation tok/s | Peak VRAM | Minimum free VRAM |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 4,096 | 3,231 | 78.882% | 167.255 | 19.322 s | 4.593 | 9,969.667 MiB | 2,025.333 MiB |
| 16,384 | 12,831 | 78.314% | 194.435 | 66.002 s | 3.591 | 10,164.000 MiB | 1,831.000 MiB |
| 32,768 | 25,623 | 78.195% | 199.199 | 128.647 s | 2.695 | 10,410.667 MiB | 1,584.333 MiB |
| 65,536 | 60,015 | 91.576% | 199.230 | 301.272 s | 1.569 | 10,958.667 MiB | 1,036.333 MiB |

All means use three measured repetitions. Decode CV ranged from 0.120% to 0.759%; 64K TTFT CV was 0.084%. The repeated results were stable even though the operating point became progressively slower.

Prompt throughput rises from 4K to the larger batches, while decode throughput falls as the active sequence grows. Relative to 4K, generation was 21.816% slower at 16K, 41.324% slower at 32K, and 65.839% slower at 64K. TTFT increased 241.590%, 565.806%, and 1,459.224%, respectively.

## Memory boundary

The measured 64K repetitions had 1,033–1,041 MiB minimum free VRAM, averaging 1,036.333 MiB. The excluded warm-up briefly reached 994 MiB free. This makes 40/66 a tight local boundary rather than a universal safe setting; background GPU use, another driver, or a different runtime build can erase the margin.

Startup logs separately recorded the expected cache scaling:

| Context | CPU K/V | CUDA K/V | CUDA compute |
|---:|---:|---:|---:|
| 4K | 27 MiB | 45 MiB | 95.03 MiB |
| 16K | 108 MiB | 180 MiB | 125.66 MiB |
| 32K | 216 MiB | 360 MiB | 207.66 MiB |
| 64K | 432 MiB | 720 MiB | 389.66 MiB |

Each startup log explicitly reported 40/66 layers offloaded, a 5,988.08 MiB CPU-mapped model buffer, and an 8,726.18 MiB CUDA model buffer.

## Recommendation

Keep full-GPU IQ2 as the everyday configuration. Use this IQ4_XS/Q4_0/40-layer profile when the research question specifically needs the higher-bit artifact or much larger active context and the latency is acceptable.

- 4K–16K: operational, but substantially slower than the IQ2 default.
- 32K: demonstrated and stable, with roughly 2.1 minutes to first content.
- Near 64K: demonstrated at 60,015 active prompt tokens, but approximately 5.0 minutes to first content and only ~1.0 GiB measured VRAM margin.

Do not infer long-context retrieval quality from this synthetic numbered-record fixture. Stage 13F must test retrieval and objective response quality, and separately determine whether MTP can improve the CPU-bound decode without unacceptable output changes.

## Evidence

- [Frozen protocol](../../environment/phase13-active-context-protocol-2026-08-16.json)
- [4K raw record](../raw/phase13-iq4-xs-context-4k-q4-20260817T040950110012Z-6ac3ebe8.json)
- [16K raw record](../raw/phase13-iq4-xs-context-16k-q4-20260817T041351163881Z-550fffc2.json)
- [32K raw record](../raw/phase13-iq4-xs-context-32k-q4-20260817T042130693295Z-644d82c6.json)
- [64K raw record](../raw/phase13-iq4-xs-context-64k-q4-20260817T043450807771Z-ad9ffd86.json)
- [Machine-readable summary](phase13-active-context.json)

The raw records include the complete generated responses and 250 ms telemetry. Ordinary tracked files remain capped at 1 MiB; validated raw benchmark JSON has a separate 5 MiB cap so the long-run evidence can remain public without permitting large arbitrary artifacts.
