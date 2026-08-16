# Qwen3.8-27B on an RTX 4070 Ti 12GB

> A reproducible Windows study of low-bit GPU-resident inference versus higher-quality CPU/RAM-offloaded inference.

## Status

**Phase 4 completed locally on 2026-08-15 — the pinned IQ2 configuration now has a repeated streaming baseline.** After one excluded warm-up, three measured 256-token runs averaged 43.171 generation tok/s with 0.096% CV; TTFT averaged 94.950 ms with 1.608% CV.

This is a trustworthy baseline for one fixed prompt, not yet the final comparative study. It includes warm-up handling, streaming TTFT, repeated trials, continuous telemetry, and variance analysis, but Q2 comparison, broader workloads, and quality evaluation remain incomplete.

## Phase 1 proof of life

| Item | Observed value |
|---|---:|
| Model | `Qwen3.8-27B-UD-IQ2_XXS.gguf` |
| Model SHA-256 | `8d1b37297d6cf98303cd396896f35e01089ddcc904053a9c6997f7a1c35b8524` |
| Context | 4,096 tokens |
| Model layers | 65, launched with llama.cpp `-ngl -1` |
| KV cache | Q8 for K and V |
| Parallel slots | 1 |
| Flash attention | Enabled |
| Speculative decoding / MTP | Disabled |
| Thinking / tools / vision | Disabled for the smoke requests |
| Loaded VRAM snapshot | 8,958 MiB used; 3,037 MiB free |
| Server-side load time | 7,125.47 ms |
| Smoke checks | 3/3 passed |

The first short generation reported 44.3 generation tokens/s and 364.9 prompt tokens/s in Unsloth's engine log. These are diagnostic observations, not headline benchmark claims. See the [runtime record](environment/phase1-unsloth-runtime-2026-08-15.json) and [canonical raw smoke result](results/raw/phase1-smoke-20260815T225920Z.json).

## Research question

> Can Qwen3.8-27B be used practically on a 12 GB RTX 4070 Ti under Windows, and when is a low-bit quant kept on the GPU preferable to a higher-quality quant that partially spills into system RAM?

This is deliberately different from an RTX 4090 showcase. The 12 GB VRAM limit creates an engineering tradeoff between:

- quantization level and potential quality;
- GPU residency and CPU/RAM offload;
- context length and KV-cache memory;
- generation speed and response quality.

## Starting hardware

| Component | Verified value |
|---|---|
| GPU | NVIDIA GeForce RTX 4070 Ti |
| VRAM | 12,282 MiB total; approximately 11,612 MiB free during inspection |
| CPU | Intel Core i7-14700K; 28 logical processors |
| RAM | 63.77 GB usable |
| OS | Windows, version 25H2, build 26200.9168 |
| NVIDIA driver | 610.88 |
| Driver CUDA runtime | 13.3 |
| Model/result drive | `E:` with approximately 1.53 TB free at inspection |

## Planned model configurations

| Configuration | File size | Intended role |
|---|---:|---|
| `UD-IQ2_XXS` | 8.39 GiB | Phase 1 proof of life completed; speed candidate |
| `UD-Q2_K_XL` | 9.94 GiB | Higher-quality 2-bit candidate with tight VRAM headroom |
| `UD-Q3_K_XL` | 12.52 GiB | Main partial-offload candidate |
| `UD-Q4_K_XL` | 16.69 GiB | Higher-quality, heavier-offload candidate |

Only one quant will be downloaded at a time, beginning after Phase 0 review.

## Repository map

```text
.
├── README.md
├── PROJECT.md
├── environment/
├── prompts/
├── reports/
├── results/
│   ├── raw/
│   └── summaries/
├── scripts/
├── src/
└── tests/
```

- [PROJECT.md](PROJECT.md) — phase gates, scope, methodology, and publication plan.
- `environment/` — machine snapshots and environment collection notes.
- `prompts/` — version-controlled benchmark prompts.
- `results/raw/` — append-only machine-readable run data.
- `results/summaries/` — derived tables and charts.
- `reports/` — GitHub, Hugging Face, and social-report drafts.
- `scripts/` — repeatable PowerShell entry points.
- `src/` — benchmark client and telemetry code.
- `tests/` — tests for our code, schemas, and calculations.

## Reproduce the Phase 1 smoke check

With Unsloth Desktop running and the pinned model already loaded using the Phase 1 settings:

```powershell
.\scripts\run_phase1_smoke.ps1
```

The script authenticates only through Unsloth Desktop's local secret, verifies the active model and configuration, disables thinking and tools in every request, and creates a unique non-overwriting JSON record under `results/raw/`. It never writes a password, token, or local username to the result.

## Reproducibility commitments

- Pin model filename and repository revision.
- Pin the llama.cpp or Unsloth Desktop version.
- Record context, KV-cache type, GPU offload, thinking mode, sampling, MTP, and vision state.
- Run warm-ups and repeated measured trials.
- Preserve failed and out-of-memory runs.
- Use `null`, never invented zeroes, for unavailable metrics.
- Do not commit GGUF model weights, caches, secrets, or unreviewed private prompt data.

## Phase 2 preliminary proof of life

The approved `UD-Q2_K_XL` candidate was downloaded, checksum-validated, and loaded with the same controls as Phase 1:

| Item | Observed value |
|---|---|
| File | `Qwen3.8-27B-UD-Q2_K_XL.gguf` |
| Pinned repository commit | `1cff334a4a228324d4ee1f76d55d372588f0d556` |
| Size | 10,676,423,744 bytes / 9.94 GiB |
| SHA-256 | `46151b52a5cad673d90a00222103254864326c251130b8fc4381d6f34386b3c8` |
| Local location | `models/Qwen3.8-27B-GGUF/Qwen3.8-27B-UD-Q2_K_XL.gguf` |
| Model layers | 65, launched with llama.cpp `-ngl -1`; no CPU fallback |
| Context / KV cache / slots | 4,096 / Q8 K+V / 1 |
| Loaded VRAM snapshot | 10,542 MiB used / 1,453 MiB free |
| Server-side load time | 8,781.03 ms |
| First short engine observation | 38.9 generation tok/s; 418.6 prompt tok/s |
| Canonical smoke checks | 3/3 passed |

The original used-memory projection was within 5.18 MiB, but its free-memory calculation incorrectly used total minus used VRAM. WDDM left about 287 MiB reserved or otherwise unavailable, so the correct projection was 1,447.82 MiB free—close to the 1,453 MiB observation. The [runtime record](environment/phase2-q2-k-xl-runtime-2026-08-15.json) preserves the correction.

The [canonical Q2_K_XL smoke record](results/raw/quant-smoke-ud-q2-k-xl-20260815T232000Z.json) passed 3/3 checks from committed harness revision `d21abea`. The [Phase 2 smoke checkpoint](results/summaries/phase2-smoke-checkpoint.md) compares both quants without presenting the tiny runs as a formal benchmark.

Phase 2 quant triage is complete. On ten identical objective pass@1 tasks, `UD-IQ2_XXS` passed 3/10 and `UD-Q2_K_XL` passed 5/10. Q2 uniquely passed binary conversion and first-unique-character tasks, while IQ2 had no unique wins. See the [quant-triage summary](results/summaries/phase2-quant-triage.md) and its raw source records.

Decision: retain `UD-IQ2_XXS` as the provisional speed configuration and `UD-Q2_K_XL` as the provisional quality-oriented configuration. This small result does not establish general model quality, but it is enough to defer the 12.52 GiB `UD-Q3_K_XL` download. Phase 3 has now pinned the native runtime; the next gate is a repeated baseline for the two selected models.

## Phase 3 pinned native runtime

| Item | Observed value |
|---|---|
| Runtime | Official llama.cpp `b10448`, commit `ad1de39e0` |
| Binary target | Windows x64, CUDA 13.3 |
| Release archive validation | 537,670,077 bytes total; both SHA-256 values matched |
| Device | `CUDA0` — NVIDIA GeForce RTX 4070 Ti |
| Layer placement | 66/66 layers offloaded to GPU |
| Context / slots | 4,096 / 1 |
| KV cache | Q8 K and V; 136.00 MiB CUDA buffer |
| CUDA model / recurrent / compute buffers | 7,974.14 / 149.62 / 37.27 MiB |
| Loaded VRAM snapshot | 8,944 MiB used / 3,051 MiB free |
| Network scope | `127.0.0.1:8090`, localhost-only CORS |
| Native smoke checks | 3/3 passed |

See the [release manifest](environment/llama-cpp-b10448-manifest.json), [runtime record](environment/phase3-native-runtime-2026-08-15.json), [canonical raw result](results/raw/native-smoke-iq2-xxs-20260815T234835Z.json), and [Phase 3 checkpoint](results/summaries/phase3-native-checkpoint.md). The server-reported 37.57–43.81 tok/s values came from tiny smoke requests and are not a repeated baseline.

## Phase 4 repeated IQ2 baseline

| Metric | Mean | Sample SD | CV | Range |
|---|---:|---:|---:|---:|
| TTFT | 94.950 ms | 1.527 ms | 1.608% | 93.935–96.706 ms |
| Total latency | 6,001.517 ms | 6.525 ms | 0.109% | 5,996.504–6,008.894 ms |
| Prompt throughput | 935.648 tok/s | 0.441 | 0.047% | 935.266–936.131 |
| Generation throughput | 43.171 tok/s | 0.041 | 0.096% | 43.124–43.203 |

All three measured runs used 84 prompt tokens, generated 256 tokens with prompt caching disabled, reached 98% sampled GPU utilization, and peaked at 8,987 MiB VRAM used. Telemetry targeted 250 ms and achieved a 256.151 ms observed mean cadence.

See the [Phase 4 environment record](environment/phase4-iq2-baseline-2026-08-15.json), [raw result](results/raw/phase4-iq2-baseline-20260816T001913Z.json), and [interpretation checkpoint](results/summaries/phase4-iq2-baseline.md). The values apply only to this fixed workload and are not a Q2 comparison or quality result.
