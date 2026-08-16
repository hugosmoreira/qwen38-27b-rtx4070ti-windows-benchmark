# Benchmark Configurations

Configuration files bind a run classification to one server, model manifest, runtime record, prompt suite, and controlled settings. Paths must stay inside the repository, and the Python client refuses non-loopback server URIs.

`phase5-iq2-smoke.json` is an engineering validation with zero warm-ups and one measured 64-token request. It proves the harness works end to end; its timing is not a performance baseline and must not replace the repeated Phase 4 result.
