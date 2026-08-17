# Phase 13 IQ4_XS target K/V-cache comparison

This pair isolates target K/V-cache representation at the selected IQ4_XS 45/66 hybrid placement. Q8_0 and Q4_0 used the same model, runtime, 4K context, prompt, sampling, MTP-off state, one excluded warm-up, and three measured 256-token repetitions.

| Metric | Q8_0 K/V | Q4_0 K/V | Q4 change |
|---|---:|---:|---:|
| Generation throughput | 5.977 tok/s | 5.965 tok/s | −0.201% |
| Prompt throughput | 176.522 tok/s | 176.760 tok/s | +0.135% |
| Mean TTFT | 481.603 ms | 477.531 ms | −0.846% |
| Mean total latency | 43,145.679 ms | 43,227.933 ms | +0.191% |
| CPU + CUDA K/V buffers | 136.00 MiB | 72.00 MiB | −64.00 MiB / −47.059% |
| Mean sampled peak VRAM | 10,957 MiB | 10,949.667 MiB | −7.333 MiB |
| Mean minimum sampled VRAM free | 1,038 MiB | 1,045.333 MiB | +7.333 MiB |
| Mean peak process private memory | 11.434 GiB | 11.364 GiB | −71.665 MiB |

Q4_0 did not materially change 4K speed. Its direct cache allocation was 64 MiB smaller, but the point-in-time sampled VRAM difference was only 7.333 MiB because WDDM reservations, background use, and other buffers are not identical across launches. The direct startup buffer values are the cleaner cache-memory comparison.

## Output-equivalence finding

Each state was internally deterministic across its three measured repetitions:

- Q8_0 response SHA-256: `e6f3e81bcc479c31be81eb40f075be469f8e133d515ccd1a383f10c1990d3256`;
- Q4_0 response SHA-256: `875ebd33247652c65ac63518892f6dde19fa5da9b0603ab72dc3907f0e129f69`.

None of the three paired outputs matched, and the first response differed at character index 71. This establishes output non-equivalence for this sampled workload. It does not establish a quality loss because the performance prompt has no correctness grader.

## Decision

Q8_0 remains the conservative short-context default. Q4_0 is the Phase 13 active-context candidate because its direct K/V allocation saving scales with context length and its 4K throughput was essentially unchanged. Larger-context work must separately test retrieval/quality and must not describe the changed output as automatically better or worse.

Sources: [Q8 raw record](../raw/phase13-iq4-xs-4k-q8-20260817T034842157169Z-a0322e7c.json) and [Q4 raw record](../raw/phase13-iq4-xs-4k-q4-kv-20260817T035612020776Z-a4c55979.json).
