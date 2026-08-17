# Changelog

All notable repository changes are documented here. Versions follow semantic versioning for the benchmark software and publication bundle, not for the upstream Qwen model or llama.cpp runtime.

## [Unreleased]

## [0.1.0] — 2026-08-17

### Added

- Reproducible Windows and RTX 4070 Ti environment capture.
- Unsloth Desktop and pinned native llama.cpp proof-of-life records.
- Standard-library Python benchmark harness with streaming TTFT, telemetry, formal schemas, semantic validation, and Windows CI.
- Controlled IQ2-versus-Q2 performance comparison, IQ2 4K/8K/16K context ladder, paired 24-task objective-quality evaluation, and IQ2 in-model MTP experiment.
- IQ4_XS checksum/storage preflight, hybrid-offload frontiers, repeated 4K baseline, Q8_0/Q4_0 K/V comparison, fixed 4K–64K active-context ladder, MTP pairs, exact retrieval, and objective-quality evaluation.
- Canonical/superseded evidence manifest, strict release audit, reproducibility guide, contribution templates, citation metadata, Hugging Face community report, and evidence-checked social drafts.
- Narrow validated-raw-JSON size policy that retains multi-megabyte long-run telemetry without weakening the ordinary 1 MiB repository limit.

### Results and decisions

- Keep `UD-IQ2_XXS` as the interactive default: 43.643 generation tok/s in the controlled 4K comparison.
- Use IQ4_XS at 45/66 layers with Q8_0 K/V as a selective quality-oriented profile: 5.977 generation tok/s and 13/24 objective tasks, versus Q2 at 10/24 and IQ2 at 9/24. Paired tests did not establish a general advantage.
- Use IQ4_XS at 40/66 layers with Q4_0 K/V only as a long-context profile. Exact retrieval passed 3/3 at matched 16K Q4_0/Q8_0 and 3/3 at 60,015–60,016 prompt tokens with Q4_0.
- Classify near-64K as research capacity rather than an interactive default: approximately 301-second TTFT, 1.57 tok/s decode, and tight VRAM margin.
- Keep MTP off by default. IQ2 MTP produced large workload-specific acceleration but changed prose output; IQ4_XS MTP changed both tested outputs and provided only +0.519% prose and +14.958% code speed.
- Preserve failed and superseded attempts, including the first near-64K retrieval run that answered correctly but missed the frozen 60,000-token gate.
- Defer `UD-Q3_K_XL`, `UD-Q4_K_XL`, vision, and runtime-convenience comparisons; IQ4_XS is a distinct tested artifact.

### Publication

- Published the repository and verified the Windows Python 3.11/3.14 CI matrix.
- Published the evidence-linked report as `unsloth/Qwen3.8-27B-GGUF` Community Discussion `#65` without uploading model weights or runtime artifacts.
- Published final GitHub Release `v0.1.0` on 2026-08-17 at commit `d1a6056` with no binary/model assets.
- Published a Phase 13 IQ4_XS follow-up to Hugging Face Community Discussion `#65`, linking the final release and focused objective-quality, retrieval, and MTP summaries.

### Known limitations

- One Windows desktop and one GPU.
- Custom convenience-sample quality and retrieval tasks rather than validated benchmark populations.
- Windows display activity shares VRAM with inference.
- Complete operating-point comparisons may change quantization and layer placement together.
- Results depend on pinned runtime, model revision, context, cache precision, sampling, and offload settings.
