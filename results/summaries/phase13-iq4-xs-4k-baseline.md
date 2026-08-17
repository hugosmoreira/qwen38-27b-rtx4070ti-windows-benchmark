# Phase 13 IQ4_XS 4K hybrid baseline

The selected IQ4_XS configuration completed one excluded warm-up and three measured 256-token repetitions under llama.cpp `b10448`, 4K context, Q8 target K/V, MTP off, and exactly 45/66 layers on CUDA0. All structural and semantic validation flags passed.

| Metric | Full-GPU `UD-IQ2_XXS` | Hybrid `IQ4_XS` | IQ4_XS change |
|---|---:|---:|---:|
| GPU layers | 66/66 | 45/66 | 21 layers remain CPU-mapped |
| Prompt throughput | 943.278 tok/s | 176.522 tok/s | −81.286% |
| Generation throughput | 43.643 tok/s | 5.977 tok/s | −86.305% |
| Mean TTFT | 91.272 ms | 481.603 ms | +427.657% |
| Mean total latency | 5,934.130 ms | 43,145.679 ms | +627.077% |
| Mean sampled peak VRAM | 8,976 MiB | 10,957 MiB | +1,981 MiB |
| Mean minimum sampled VRAM free | 3,019 MiB | 1,038 MiB | −1,981 MiB |
| Mean peak process private memory | 9.621 GiB | 11.434 GiB | +1.813 GiB |
| Mean peak process CPU share | 3.884% | 7.553% | +3.669 points |

IQ2 decoded **7.302× faster** for this fixed workload. The IQ4_XS result was highly repeatable—5.977 tok/s mean, 0.006 sample SD, and 0.098% CV—so the large difference is not explained by run-to-run noise.

## Placement and memory evidence

The hash-validated canonical launch reported:

- 45/66 layers offloaded to CUDA0;
- 4,964.75 MiB CPU-mapped model buffer;
- 9,749.51 MiB CUDA model buffer;
- 42.50 MiB CPU and 93.50 MiB CUDA K/V buffers;
- 101.28 MiB CUDA and 8.89 MiB CUDA-host compute buffers.

The measured requests each used 84 prompt tokens and generated 256 tokens. Mean prompt throughput was 176.522 tok/s, mean total latency was 43.146 seconds, and sampled minimum free VRAM ranged from 1,028 to 1,043 MiB. The server was stopped after validation; zero pinned llama-server processes remained.

## Interpretation boundary

This is a comparison of two complete practical configurations, not the causal effect of quantization alone. IQ2 fully offloads 66/66 layers, while IQ4_XS uses hybrid CPU/GPU placement. The runtime, prompt, context, Q8 K/V, sampling, MTP-off state, and repetition structure match, but both weight quantization and placement differ.

The result establishes a substantial performance cost for IQ4_XS on this 12GB GPU. It does not yet establish whether IQ4_XS delivers enough objective quality benefit to justify that cost. Q4_0 K/V, active long-context, MTP, and quality stages remain separate experiments.

Sources: [IQ4_XS raw record](../raw/phase13-iq4-xs-4k-q8-20260817T034842157169Z-a0322e7c.json) and [Phase 6 IQ2 raw record](../raw/phase6-iq2-comparison-20260816T014219897578Z-05ff3bf0.json).
