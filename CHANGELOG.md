# Changelog

All notable repository changes are documented here. Versions follow semantic versioning for the benchmark software and publication bundle, not for the upstream Qwen model or llama.cpp runtime.

## [Unreleased]

- Public citation identity and final GitHub URLs remain pending.

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
