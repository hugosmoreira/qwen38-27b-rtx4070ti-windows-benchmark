# Phase 7 IQ2 Context Sensitivity

## Outcome

`UD-IQ2_XXS` met every predeclared technical and sensible-use criterion at 4K, 8K, and 16K. The largest sensible tested configuration is therefore 16K for this study. Its actual canonical workload contained 12,831 prompt tokens plus 128 generated tokens; this is not a claim that every full-window input or a larger context will behave the same way.

All three fresh servers reported 66/66 layers on CUDA0. No canonical request failed or ran out of memory.

## Controlled results

| Metric | 4K | 8K | 16K | 16K change vs 4K |
|---|---:|---:|---:|---:|
| Actual prompt tokens | 3,231 | 6,423 | 12,831 | +297.122% |
| Prompt-window utilization | 78.882% | 78.406% | 78.314% | — |
| Prompt throughput | 1,202.952 tok/s | 1,187.733 tok/s | 1,155.757 tok/s | −3.923% |
| TTFT | 2,692.911 ms | 5,418.174 ms | 11,118.874 ms | +312.894% |
| Generation throughput | 41.124 tok/s | 40.522 tok/s | 39.201 tok/s | −4.676% |
| Total latency, 128 output tokens | 5,781.308 ms | 8,552.468 ms | 14,358.732 ms | +148.365% |
| Peak VRAM used | 9,028 MiB | 9,182 MiB | 9,488 MiB | +460 MiB / +5.095% |
| Minimum VRAM free | 2,967 MiB | 2,813 MiB | 2,507 MiB | −460 MiB / −15.504% |
| Peak process private memory | 9.691 GiB | 9.842 GiB | 10.146 GiB | +4.703% |

The 16K workload used nearly four times as many prompt tokens as 4K. TTFT consequently rose from 2.693 to 11.119 seconds. Engine prompt throughput declined only 3.923%, while per-token decode throughput declined 4.676% as the active history grew.

## Memory allocation

| CUDA allocation | 4K | 8K | 16K |
|---|---:|---:|---:|
| Model buffer | 7,974.14 MiB | 7,974.14 MiB | 7,974.14 MiB |
| Q8 K/V cache | 136.00 MiB | 272.00 MiB | 544.00 MiB |
| Compute buffer | 37.27 MiB | 54.27 MiB | 88.27 MiB |

From 4K to 16K, the KV allocation increased by 408 MiB and the compute buffer by 51 MiB. Their 459 MiB combined increase closely explains the 460 MiB increase in both startup and sampled peak VRAM use.

## Frozen sensible-use gate

| Criterion | Required | 4K | 8K | 16K |
|---|---:|---:|---:|---:|
| All runs pass; 66/66 GPU layers | Yes | Pass | Pass | Pass |
| Minimum VRAM free | ≥1,024 MiB | 2,967 | 2,813 | 2,507 |
| Mean TTFT | ≤30,000 ms | 2,692.911 | 5,418.174 | 11,118.874 |
| Mean generation throughput | ≥30 tok/s | 41.124 | 40.522 | 39.201 |

The thresholds were committed before canonical measurement in protocol revision `e0230f3`.

## Variation and telemetry

Generation-throughput CV was 0.489% at 4K, 0.165% at 8K, and 0.018% at 16K. TTFT CV remained at or below 0.115%. The measured telemetry cadence remained close to the 250 ms target: 253.614 ms at 4K, 253.175 ms at 8K, and 253.402 ms at 16K.

Peak sampled temperature rose from 72°C to 77°C to 80°C, while peak sampled power rose from 274.59 W to 277.26 W to 279.36 W. Because the order was fixed and ascending, context size and accumulated thermal state are correlated.

## Sources and limitations

- 4K raw result: [`phase7-iq2-context-4k-20260816T022507577973Z-623ca28d.json`](../raw/phase7-iq2-context-4k-20260816T022507577973Z-623ca28d.json)
- 8K raw result: [`phase7-iq2-context-8k-20260816T022627198977Z-5778e8f6.json`](../raw/phase7-iq2-context-8k-20260816T022627198977Z-5778e8f6.json)
- 16K raw result: [`phase7-iq2-context-16k-20260816T022758735205Z-51fce8fc.json`](../raw/phase7-iq2-context-16k-20260816T022758735205Z-51fce8fc.json)
- Machine-readable comparison: [`phase7-context-sensitivity.json`](phase7-context-sensitivity.json)
- Frozen protocol: [`phase7-context-protocol-2026-08-15.json`](../../environment/phase7-context-protocol-2026-08-15.json)

The synthetic fixture measures prefill, TTFT, decode, and memory behavior. It does not evaluate long-context recall or response quality. Results cover one quant, one slot, one fixed order, one runtime, and one Windows desktop.
