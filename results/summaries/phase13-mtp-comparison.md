# Phase 13 — IQ4_XS in-model MTP

## Decision

Keep MTP **off by default** for IQ4_XS on this machine. It produced almost no prose improvement, changed deterministic output in both tested workloads, and consumed about another 490–496 MiB of sampled peak VRAM. A coding-specific opt-in profile is reasonable only after application-level correctness tests.

## Controlled result

Every state used the pinned IQ4_XS artifact, llama.cpp `b10448`, 4K context, one slot, 40/66 GPU layers, Q4_0 target K/V, cache off, thinking off, greedy decoding, and seed 42. MTP used the embedded NextN layer through `draft-mtp`, draft depth two, and F16 draft K/V. Each state had one excluded warm-up and five measured 256-token repetitions from a fresh server.

| Workload | MTP off tok/s | MTP on tok/s | Speed change | Draft acceptance | Latency change | Peak VRAM change | Exact output match |
|---|---:|---:|---:|---:|---:|---:|---:|
| Prose | 5.005 | 5.031 | +0.519% | 68.372% | -0.464% | +496.2 MiB | 0/5 |
| Python code | 4.994 | 5.741 | +14.958% | 85.106% | -12.799% | +489.8 MiB | 0/5 |

MTP increased mean TTFT by 4.601% for prose and 5.297% for code. The code workload accepted 800 of 940 drafted tokens and saved about 6.61 seconds over a 256-token response; prose accepted 735 of 1,075 and saved only 0.24 seconds.

## Output behavior

Each state was internally deterministic, but neither off/on pair matched. Prose first differed at zero-based character 329; code first differed at character 86. This establishes that MTP was not transparent under the frozen controls. It does not establish which response was better because these two long outputs were not correctness-graded.

## Practical profile

- Daily/default profile: MTP off.
- Optional coding experiment: MTP on only when approximately 15% measured acceleration matters and the application has its own regression tests.
- Do not quote a pooled MTP speedup: acceptance and benefit were workload-specific.

The [machine-readable comparison](phase13-mtp-comparison.json) records raw hashes, formulas, output hashes, and limitations.
