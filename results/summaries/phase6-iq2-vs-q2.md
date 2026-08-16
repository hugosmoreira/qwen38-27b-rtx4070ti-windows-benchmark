# Phase 6 IQ2 versus Q2 Comparison

## Outcome

Under the frozen 4K configuration, `UD-IQ2_XXS` decoded 14.759% faster than `UD-Q2_K_XL` and used 1,583 MiB less peak VRAM. Expressed with IQ2 as the protocol denominator, Q2 generation throughput was 12.861% lower and peak VRAM was 17.636% higher.

Both models reported 66/66 layers offloaded to CUDA0. This is therefore a quantization, speed, and memory comparison—not a GPU-resident versus CPU-layer-offloaded comparison.

## Controlled results

| Metric | IQ2 mean | Q2 mean | Q2 change vs IQ2 |
|---|---:|---:|---:|
| Generation throughput | 43.643 tok/s | 38.030 tok/s | **−12.861%** |
| Prompt throughput | 943.278 tok/s | 995.095 tok/s | +5.493% |
| TTFT | 91.272 ms | 86.622 ms | −5.095% |
| Total latency, 256 tokens | 5,934.130 ms | 6,791.962 ms | **+14.456%** |
| Peak VRAM used | 8,976 MiB | 10,559 MiB | **+17.636% / +1,583 MiB** |
| Minimum VRAM free | 3,019 MiB | 1,436 MiB | −52.435% / −1,583 MiB |
| Peak process working set | 8.392 GiB | 9.935 GiB | +18.389% |
| Peak process private memory | 9.621 GiB | 11.167 GiB | +16.066% |
| Peak sampled GPU utilization | 99% | 99% | 0% |

Q2 processed the prompt and reached its first content token slightly faster, but decode dominates the 256-token workload. Its mean total latency was 857.832 ms longer.

## Variation and telemetry

| Metric | IQ2 sample SD / CV | Q2 sample SD / CV |
|---|---:|---:|
| Generation throughput | 0.004 / 0.009% | 0.017 / 0.045% |
| TTFT | 0.134 ms / 0.147% | 0.416 ms / 0.480% |
| Total latency | 0.535 ms / 0.009% | 3.112 ms / 0.046% |

Each quant used one excluded warm-up plus three measured repetitions. IQ2 retained 24 telemetry samples per measured run at a 253.350 ms observed mean cadence. Q2 retained 27–28 samples at 253.261 ms. Both reached 71°C; peak sampled power was 265.16 W for IQ2 and 257.98 W for Q2.

## Quality context remains separate

The earlier ten-task Phase 2 triage produced 3/10 for IQ2 and 5/10 for Q2. That two-task Q2 advantage is the reason Q2 remains the quality-oriented candidate, but it is a small selection signal rather than a general-quality estimate. The Phase 6 long-form response is not graded and adds no new quality evidence.

## Decision

- Keep `UD-IQ2_XXS` as the speed-oriented default. It offers faster long-form decode and approximately 1.55 GiB more VRAM headroom.
- Keep `UD-Q2_K_XL` as the quality-oriented candidate when the small Phase 2 signal matters more than its 12.861% decode-throughput loss and 1,583 MiB peak-VRAM cost.
- Do not claim a CPU-offload tradeoff from these results. Both selected quants fit fully on this 12 GB GPU at 4K with Q8 KV cache.

## Sources and limitations

- IQ2 raw result: [`phase6-iq2-comparison-20260816T014219897578Z-05ff3bf0.json`](../raw/phase6-iq2-comparison-20260816T014219897578Z-05ff3bf0.json)
- Q2 raw result: [`phase6-q2-comparison-20260816T014417772434Z-91bc350d.json`](../raw/phase6-q2-comparison-20260816T014417772434Z-91bc350d.json)
- Machine-readable derived comparison: [`phase6-iq2-vs-q2.json`](phase6-iq2-vs-q2.json)
- Frozen protocol: [`phase6-comparison-protocol-2026-08-15.json`](../../environment/phase6-comparison-protocol-2026-08-15.json)

These results cover one deterministic long-form workload, one desktop, one fixed measurement order, 4K context, and three measured repetitions per quant. They do not establish cold-start behavior, larger-context behavior, multi-user throughput, broad quality, or CPU-offload performance.
