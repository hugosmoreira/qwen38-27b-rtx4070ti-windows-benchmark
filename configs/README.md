# Benchmark Configurations

Configuration files bind a run classification to one server, model manifest, runtime record, prompt suite, and controlled settings. Paths must stay inside the repository, and the Python client refuses non-loopback server URIs.

`phase5-iq2-smoke.json` is an engineering validation with zero warm-ups and one measured 64-token request. It proves the harness works end to end; its timing is not a performance baseline and must not replace the repeated Phase 4 result.

`phase6-iq2-comparison.json` and `phase6-q2-comparison.json` form one controlled pair. A test removes only the declared model-identity fields and requires the remaining JSON objects to be exactly equal. Both reuse the Phase 4 256-token workload with one warm-up and three measured repetitions.
