# Raw Results

Raw benchmark records will be written here using unique, non-overwriting run IDs.

Current records:

- `phase1-smoke-20260815T225505Z.json` — development smoke run created while the harness was still an uncommitted worktree change; 3/3 checks passed.
- `phase1-smoke-20260815T225920Z.json` — canonical Phase 1 smoke run from committed harness revision `638d88c`; 3/3 checks passed.
- `quant-smoke-ud-q2-k-xl-20260815T232000Z.json` — canonical Phase 2 Q2_K_XL smoke run from committed harness revision `d21abea`; 3/3 checks passed.
- `quant-triage-ud-q2-k-xl-20260815T232426Z.json` — Q2_K_XL pass@1 result on the ten-task Phase 2 triage suite; 5/10 passed.
- `quant-triage-ud-iq2-xxs-20260815T232512Z.json` — IQ2_XXS pass@1 result on the identical triage suite; 3/10 passed.
- `native-smoke-iq2-xxs-20260815T234723Z.json` — preserved Phase 3 native run from revision `37b844a`; 1/3 passed because the initial parser setting left empty reasoning tags in strict answer content.
- `native-smoke-iq2-xxs-20260815T234835Z.json` — canonical Phase 3 native OpenAI-compatible smoke run from revision `924554a`; 3/3 passed.
- `phase4-iq2-baseline-20260816T001639Z.json` — preserved Phase 4 attempt from revision `d89fd0d`; performance data completed, but the nominal 250 ms telemetry interval was actually 300 ms and the record is superseded.
- `phase4-iq2-baseline-20260816T001913Z.json` — canonical Phase 4 IQ2 baseline from corrected revision `25e51a0`; one warm-up and three measured repetitions completed with observed telemetry cadence recorded.
- `phase5-python-iq2-smoke-20260816T005922932894Z-a280beda.json` — canonical Phase 5 Python-harness smoke from revision `b0481d4`; one short measured run passed all structural, semantic, streaming, cache, reasoning, and telemetry checks.
- `phase6-iq2-comparison-20260816T014219897578Z-05ff3bf0.json` — canonical Phase 6 IQ2 record from frozen protocol revision `94a2735`; one excluded warm-up and three measured 256-token runs completed and passed semantic validation.
- `phase6-q2-comparison-20260816T014417772434Z-91bc350d.json` — canonical Phase 6 Q2 record from the same protocol revision and controls; one excluded warm-up and three measured 256-token runs completed and passed semantic validation.
- `phase7-iq2-context-4k-20260816T022507577973Z-623ca28d.json` — canonical Phase 7 4K IQ2 record from protocol revision `e0230f3`; all runs used 3,231 prompt and 128 completion tokens.
- `phase7-iq2-context-8k-20260816T022627198977Z-5778e8f6.json` — canonical Phase 7 8K IQ2 record from the same protocol; all runs used 6,423 prompt and 128 completion tokens.
- `phase7-iq2-context-16k-20260816T022758735205Z-51fce8fc.json` — canonical Phase 7 16K IQ2 record; all runs used 12,831 prompt and 128 completion tokens and retained 2,507 MiB minimum sampled VRAM free.
- `phase8-quality-q2-20260816T033656385280Z-2359f380.json` — canonical Phase 8 Q2 record; 24/24 requests completed and 10/24 passed independent suite-backed re-grading.
- `phase8-quality-iq2-20260816T033811840476Z-8c67331b.json` — canonical Phase 8 IQ2 record; 24/24 requests completed and 9/24 passed independent suite-backed re-grading.
- `phase9-mtp-off-prose-20260816T041445808671Z-76083f38.json` — canonical Phase 9 prose MTP-off control with five measured repetitions.
- `phase9-mtp-on-prose-20260816T041603771264Z-9c3f8aca.json` — canonical Phase 9 prose MTP-on record; 55.187% draft acceptance and non-equivalent output.
- `phase9-mtp-on-code-20260816T041709353404Z-221a5138.json` — canonical Phase 9 code MTP-on record; 90.110% draft acceptance and output-equivalent acceleration.
- `phase9-mtp-off-code-20260816T041809117916Z-bdba6559.json` — canonical Phase 9 code MTP-off control with five measured repetitions.
- `phase13-iq4-xs-context-4k-q4-20260817T040950110012Z-6ac3ebe8.json` — canonical 40/66-layer Q4_0 active-context record with 3,231 prompt tokens.
- `phase13-iq4-xs-context-16k-q4-20260817T041351163881Z-550fffc2.json` — canonical fixed-placement record with 12,831 prompt tokens.
- `phase13-iq4-xs-context-32k-q4-20260817T042130693295Z-644d82c6.json` — canonical fixed-placement record with 25,623 prompt tokens.
- `phase13-iq4-xs-context-64k-q4-20260817T043450807771Z-ad9ffd86.json` — canonical near-window record with 60,015 prompt tokens, three completed measured repetitions, and continuous telemetry.

Phase 5's file is a smoke result, not a repeated benchmark. Its short end-to-end rates include local API and orchestration overhead. The Phase 6 pair supersedes Phase 4 for the controlled quant comparison while Phase 4 remains the earlier standalone IQ2 baseline.

Each Phase 7 record contains one excluded warm-up plus three measured repetitions, the deterministic fixture hash and byte count, actual prompt/completion aggregates, per-run context-budget validation, and continuous telemetry.

The authoritative release classification is `release/v0.1.0-manifest.json`. It labels every tracked raw JSON record as canonical, superseded, or diagnostic so retained failed evidence cannot be mistaken for a current result. Ordinary tracked files remain limited to 1 MiB; validated raw benchmark JSON has a separate 5 MiB ceiling to retain long-context telemetry.
