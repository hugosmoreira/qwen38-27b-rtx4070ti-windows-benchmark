# Changelog

All notable repository changes are documented here. Versions follow semantic versioning for the benchmark software and publication bundle, not for the upstream Qwen model or llama.cpp runtime.

## [Unreleased]

- Publish the repository to GitHub and verify the Windows Python 3.11/3.14 CI matrix.
- Publish the evidence-linked report as `unsloth/Qwen3.8-27B-GGUF` Community Discussion `#65` without uploading model weights or runtime artifacts.
- Prepare evidence-checked Phase 12 LinkedIn and X drafts plus a reusable benchmark card.
- Start a separately scoped Phase 13 IQ4_XS hybrid-offload study with an immutable artifact manifest, storage preflight, frozen protocol, parameterized native launcher, safe resumable downloader, and practical layer-frontier probe.
- Select 45/66 GPU layers for the Phase 13 repeated baseline after seven successful IQ4_XS placement probes; 46/66 was operational but missed the frozen 1,024 MiB VRAM-headroom gate.
- Complete the repeated IQ4_XS 4K/Q8 baseline at 5.977 generation tok/s and document that the existing full-GPU IQ2 operating point was 7.302× faster under the shared workload.
- Isolate Q4_0 target K/V at fixed 45/66 placement: direct K/V buffers fell 47.059%, 4K generation changed −0.201%, and deterministic output was not equivalent to Q8_0.
- Select 40/66 layers for a fixed-placement Q4_0 active-context ladder after a separate 64K-capacity diagnostic; require at least 60,000 actual prompt tokens for the near-64K level.
- Complete the fixed 4K/16K/32K/64K IQ4_XS active-context ladder. The 64K level ingested 60,015 prompt tokens in every repetition at 1.569 generation tok/s and 301.27 s TTFT, with 1,033–1,041 MiB measured free VRAM and a 994 MiB excluded-warm-up minimum.
- Add a tested artifact-size policy that keeps the ordinary 1 MiB ceiling while permitting validated raw benchmark JSON up to 5 MiB, allowing full long-run telemetry to remain public.
- Freeze Stage 13F with IQ4_XS MTP off/on pairs plus deterministic early/middle/late retrieval fixtures at paired 16K Q8_0/Q4_0 and near-64K Q4_0; add launch guards and token-range validation before measurement.
- Tag creation, GitHub Release publication, and final social submissions remain separate actions.
- Normalize Windows repository roots before Markdown-link containment checks, including short-path and relative-path representations used by hosted runners.

## [0.1.0] — Release candidate

### Added

- Windows and RTX 4070 Ti environment capture.
- Unsloth Desktop and native llama.cpp proof-of-life records.
- Standard-library Python benchmark harness with streaming TTFT and telemetry.
- Controlled IQ2-versus-Q2 performance comparison.
- IQ2 4K/8K/16K context-sensitivity ladder.
- Paired 24-task objective quality evaluation with independent re-grading.
- IQ2 in-model MTP off/on experiment with acceptance and output-equivalence checks.
- Formal performance and quality result schemas.
- Canonical-evidence manifest, release audit, Windows CI, and public contribution templates.

### Decisions

- Keep `UD-IQ2_XXS` as the practical default on this 12 GB GPU.
- Treat 16K as the largest sensible tested IQ2 context for the declared workload and thresholds.
- Keep MTP off by default because deterministic prose output was not equivalent across states.
- Defer Q3, Q4, vision, and runtime-convenience comparisons.

### Known limitations

- One Windows desktop and one GPU.
- Custom convenience-sample quality tasks rather than a validated benchmark population.
- Windows display activity shares VRAM with inference.
- No claim about arbitrary full-window prompts or long-context retrieval quality.
