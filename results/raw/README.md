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

Phase 5's file is a smoke result, not a repeated benchmark. Its short end-to-end rates include local API and orchestration overhead. Phase 4 remains the performance baseline.
