# Qwen3.8-27B on an RTX 4070 Ti 12GB

> A reproducible Windows study of low-bit GPU-resident inference versus higher-quality CPU/RAM-offloaded inference.

## Status

**Phase 0 completed on 2026-08-15 — local repository and learning setup.** No model weights have been downloaded and no performance measurements exist yet.

Never treat placeholder fields or plans in this repository as measured results. Published numbers must trace back to saved raw runs on this machine.

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
| `UD-IQ2_XXS` | 8.39 GiB | Safest first run and GPU-resident speed candidate |
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

## Reproducibility commitments

- Pin model filename and repository revision.
- Pin the llama.cpp or Unsloth Desktop version.
- Record context, KV-cache type, GPU offload, thinking mode, sampling, MTP, and vision state.
- Run warm-ups and repeated measured trials.
- Preserve failed and out-of-memory runs.
- Use `null`, never invented zeroes, for unavailable metrics.
- Do not commit GGUF model weights, caches, secrets, or unreviewed private prompt data.

## Next gate

Review Phase 0, choose the exact `E:` model directory, and approve or reject the proposed first large download:

```text
Repository: unsloth/Qwen3.8-27B-GGUF
File: Qwen3.8-27B-UD-IQ2_XXS.gguf
Size: approximately 9.01 GB decimal / 8.39 GiB
Destination: an explicit model directory on E:
```

The download must be approved separately after its destination and available disk space are rechecked.
