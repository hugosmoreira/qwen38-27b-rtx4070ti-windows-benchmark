# Qwen3.8-27B on an RTX 4070 Ti 12GB

> A reproducible Windows study of low-bit GPU-resident inference versus higher-quality CPU/RAM-offloaded inference.

## Status

**Phase 1 completed locally on 2026-08-15 — Qwen3.8-27B runs successfully on the RTX 4070 Ti.** The pinned `UD-IQ2_XXS` GGUF passed checksum validation, loaded through Unsloth Desktop's bundled llama.cpp backend, and passed a three-prompt proof-of-life suite.

This is not yet a formal benchmark. Short smoke-test rates include API overhead, and Phase 4 will add warm-up handling, repeated trials, continuous telemetry, and variance analysis. Never treat a proof-of-life number or placeholder field as a publication-ready result.

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

The first short generation reported 44.3 generation tokens/s and 364.9 prompt tokens/s in Unsloth's engine log. These are diagnostic observations, not headline benchmark claims. See the [runtime record](environment/phase1-unsloth-runtime-2026-08-15.json) and [raw smoke result](results/raw/phase1-smoke-20260815T225505Z.json).

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

## Next gate

Phase 2 evaluates whether a larger quant improves practical response quality enough to justify its memory and speed cost. Before another multi-gigabyte download, its exact filename, byte size, checksum availability, destination, and expected VRAM/offload behavior must be reviewed. No additional model is downloaded automatically.
