# Benchmark Configurations

Configuration files bind a run classification to one server, model manifest, runtime record, prompt suite, and controlled settings. Paths must stay inside the repository, and the Python client refuses non-loopback server URIs.

`phase5-iq2-smoke.json` is an engineering validation with zero warm-ups and one measured 64-token request. It proves the harness works end to end; its timing is not a performance baseline and must not replace the repeated Phase 4 result.

`phase6-iq2-comparison.json` and `phase6-q2-comparison.json` form one controlled pair. A test removes only the declared model-identity fields and requires the remaining JSON objects to be exactly equal. Both reuse the Phase 4 256-token workload with one warm-up and three measured repetitions.

`phase7-iq2-context-4k.json`, `phase7-iq2-context-8k.json`, and `phase7-iq2-context-16k.json` define the ascending IQ2 context ladder. They keep the runtime and inference controls fixed while scaling a deterministic public synthetic prompt to approximately 78% of each configured window. Each level reserves 128 output tokens and enforces an expected actual prompt-token range.

`phase8-quality-q2.json` and `phase8-quality-iq2.json` form a paired objective quality evaluation. A test permits only model-identity fields to differ. Each model receives the same 24 tasks once, in the same order, with a fresh 4K one-slot server, deterministic sampling, prompt caching off, and thinking, MTP, tools, MCP, and vision disabled.

The four `phase9-mtp-*.json` files form two controlled IQ2 pairs: MTP off versus in-model `draft-mtp` for prose and Python code. Each pair differs only in its run identity and declared MTP controls. Both use greedy decoding, one excluded warm-up, five measured repetitions, and response-level checks that draft activity matches the selected state.

`phase13-iq4-xs-4k-q8.json` freezes the first repeated hybrid-offload baseline after the separate frontier selected 45 requested/observed GPU layers under the 1,024 MiB headroom rule. It reuses the Phase 4 256-token workload, Q8 target K/V, MTP off, one excluded warm-up, and three measured repetitions. Its result may be compared with Phase 6 IQ2 only as a complete operating-point comparison because quantization and layer placement both differ.
