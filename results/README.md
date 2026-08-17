# Results

- `raw/` contains append-only run records and raw model responses selected for publication.
- `summaries/` contains derived tables, statistics, and charts.
- `../schemas/benchmark-result.schema.json` and `../schemas/quality-evaluation-result.schema.json` are the formal performance and objective-quality result contracts.

Phases 1 through 3 include proof-of-life records for `UD-IQ2_XXS`, `UD-Q2_K_XL`, and the pinned native llama.cpp API. They are explicitly classified as proof-of-life rather than formal benchmarks; repeated measurements begin in Phase 4.

Phase 2 also includes a ten-task objective triage comparison. It supports configuration selection but is explicitly smaller than the planned Phase 8 quality evaluation.

Phase 3 retains both the failed 1/3 parser-configuration run and the corrected 3/3 run. Failed evidence is not deleted when it explains a configuration decision.

Phase 4 adds the first repeated baseline: one excluded warm-up and three measured IQ2 runs with streaming TTFT and continuous telemetry. The first attempt remains available because its configured 250 ms sampler actually ran at 300 ms; the canonical rerun records target and observed cadence separately.

Phase 5 replaces the earlier draft record example with a versioned Draft 2020-12 schema plus a semantic validator. Its short end-to-end smoke result is engineering evidence for the harness, not a replacement performance baseline.

The canonical Phase 5 raw file is `raw/phase5-python-iq2-smoke-20260816T005922932894Z-a280beda.json`; its interpretation checkpoint is `summaries/phase5-python-harness-checkpoint.md`.

Phase 6 adds a controlled IQ2-versus-Q2 pair produced from protocol commit `94a2735`. Both runs used one excluded warm-up, three measured repetitions, and identical 4K controls. Both models placed 66/66 layers on CUDA0; the result is therefore a quantization, speed, and memory comparison rather than a CPU-offload comparison.

The canonical Phase 6 raw files are `raw/phase6-iq2-comparison-20260816T014219897578Z-05ff3bf0.json` and `raw/phase6-q2-comparison-20260816T014417772434Z-91bc350d.json`. Their human and machine-readable interpretations are `summaries/phase6-iq2-vs-q2.md` and `summaries/phase6-iq2-vs-q2.json`.

Phase 7 adds three controlled IQ2 context levels. Each uses a fresh server and a proportionally scaled deterministic fixture so the actual prompt—not only the allocated KV cache—exercises 4K, 8K, or 16K behavior. All three canonical results passed; the 16K workload is the largest sensible tested context under the frozen study-specific thresholds.

The canonical Phase 7 records are `raw/phase7-iq2-context-4k-20260816T022507577973Z-623ca28d.json`, `raw/phase7-iq2-context-8k-20260816T022627198977Z-5778e8f6.json`, and `raw/phase7-iq2-context-16k-20260816T022758735205Z-51fce8fc.json`. Their interpretations are `summaries/phase7-context-sensitivity.md` and `summaries/phase7-context-sensitivity.json`.

Phase 8 adds a paired 24-task objective quality evaluation. Q2 passed 10 tasks and IQ2 passed 9; the exact paired McNemar p-value is 1.0, so the one-task difference is descriptive only. The first Q2 attempt is disclosed in the protocol amendment but has no raw score because a pre-write preservation check rejected it. The corrected canonical records both reference amendment commit `87faba4` and pass independent suite-backed re-grading.

The canonical Phase 8 files are `raw/phase8-quality-q2-20260816T033656385280Z-2359f380.json` and `raw/phase8-quality-iq2-20260816T033811840476Z-8c67331b.json`. Their interpretations are `summaries/phase8-quality-comparison.md` and `summaries/phase8-quality-comparison.json`.

Phase 9 adds two IQ2 MTP off/on workload pairs. MTP accelerated both fixed-length workloads but changed the deterministic prose output, so it remains an opt-in experimental mode rather than the default. The canonical raw records and their classification are listed in `release/v0.1.0-manifest.json`; the interpretations are `summaries/phase9-mtp-comparison.md` and `summaries/phase9-mtp-comparison.json`.

Phase 13 begins with a noncanonical IQ4_XS offload-frontier diagnostic. Seven fresh-process short probes selected 45/66 GPU layers under a frozen 1,024 MiB VRAM-headroom rule. The raw diagnostic is classified separately from repeated performance evidence; its bounded interpretation is `summaries/phase13-offload-frontier.md`.

The selected 45/66 IQ4_XS configuration then completed one excluded warm-up and three measured 256-token repetitions at 5.977 generation tok/s with 0.098% CV. The canonical raw record is classified in the release manifest; `summaries/phase13-iq4-xs-4k-baseline.md` compares the complete hybrid operating point with the earlier full-GPU IQ2 evidence without calling it a quantization-only effect.

Stage 13D changes only the target K/V representation. Q4_0 reduced the direct combined CPU/CUDA K/V buffers from 136 to 72 MiB at 4K while generation changed by −0.201%. Its deterministic output did not match Q8_0, so `summaries/phase13-iq4-xs-kv-cache.md` selects it only as the active-context candidate with later retrieval validation.

The separate 64K/Q4_0 capacity frontier used only 38 prompt tokens and therefore remains diagnostic. It selected 40/66 layers with 1,143 MiB post-request VRAM free; `summaries/phase13-active-context-capacity.md` explains why this allocation result is not a 64K active-prompt claim.

Every summary value must be reproducible from committed raw data and a documented code version. Large diagnostic logs may remain local, but exclusions must be stated.
