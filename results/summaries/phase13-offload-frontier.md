# Phase 13 IQ4_XS 4K offload frontier

The pinned IQ4_XS artifact completed seven fresh-process placement probes under llama.cpp `b10448`, 4K context, Q8 target K/V, one slot, MTP off, and automatic fit disabled. Every probe started, completed the same short 64-token request, and reported exactly the requested layer placement. No probe failed or ran out of memory.

The frozen practical definition additionally required at least 1,024 MiB VRAM free after the request. Under that local rule, **45/66 GPU layers is the largest practical placement** and **46/66 is the first non-practical placement**.

| Probe order | GPU layers | CPU-mapped model buffer | CUDA model buffer | VRAM used after request | VRAM free after request | Short-request decode | Practical |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 25/66 | 9,038.99 MiB | 5,675.26 MiB | 6,806 MiB | 5,189 MiB | 3.45 tok/s | Yes |
| 2 | 33/66 | 7,409.29 MiB | 7,304.96 MiB | 8,517 MiB | 3,478 MiB | 4.16 tok/s | Yes |
| 3 | 41/66 | 5,779.60 MiB | 8,934.66 MiB | 10,187 MiB | 1,808 MiB | 5.25 tok/s | Yes |
| 4 | 49/66 | 4,149.90 MiB | 10,564.35 MiB | 11,760 MiB | 235 MiB | 7.08 tok/s | No—headroom |
| 5 | 45/66 | 4,964.75 MiB | 9,749.51 MiB | 10,924 MiB | 1,071 MiB | 6.03 tok/s | Yes |
| 6 | 47/66 | 4,566.86 MiB | 10,147.40 MiB | 11,337 MiB | 658 MiB | 6.50 tok/s | No—headroom |
| 7 | 46/66 | 4,756.27 MiB | 9,957.98 MiB | 11,139 MiB | 856 MiB | 6.27 tok/s | No—headroom |

## Interpretation boundary

The layer trend is internally coherent: moving more model data to CUDA reduced the CPU-mapped buffer and increased short-request decode speed, while consuming VRAM. However, these values come from one short capability request per placement. They are not repeated throughput benchmarks and must not be compared directly with the Phase 6 or community headline rates.

Forty-six, 47, and 49 layers were operational but missed the predeclared safety margin; they are not OOM failures. The selected 45-layer placement receives the later excluded warm-up plus three-repetition Phase 13 baseline. The frontier is local to this RTX 4070 Ti, driver `610.88`, WDDM/background state, IQ4_XS revision, runtime build, 4K context, and Q8 K/V cache.

Source: [`phase13-iq4-offload-frontier-20260817T034550433Z.json`](../raw/phase13-iq4-offload-frontier-20260817T034550433Z.json), SHA-256 `3567f53529e9693129a6c83e692c2e41c8c7849ce2ad187cfada9771ad5c2ee7`.
