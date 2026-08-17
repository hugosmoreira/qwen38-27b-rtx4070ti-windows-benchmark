# Scripts

PowerShell entry points used to reproduce setup, launches, and benchmark runs will live here.

Current scripts:

```powershell
.\scripts\collect_environment.ps1
.\scripts\run_phase1_smoke.ps1
.\scripts\run_quant_smoke.ps1 -ManifestPath .\environment\phase2-q2-k-xl-download-manifest.json `
    -RuntimeRecord environment/phase2-q2-k-xl-runtime-2026-08-15.json
.\scripts\start_native_llama_server.ps1
.\scripts\run_native_smoke.ps1
.\scripts\run_phase4_baseline.ps1
.\scripts\setup_python.ps1
.\scripts\run_python_tests.ps1
.\scripts\run_phase5_harness.ps1
.\scripts\run_phase6_measurement.ps1 -Config configs/phase6-iq2-comparison.json
.\scripts\run_phase7_measurement.ps1 -Config configs/phase7-iq2-context-4k.json
.\scripts\run_phase8_quality.ps1 -Config configs/phase8-quality-q2.json
.\scripts\run_phase9_measurement.ps1 -Config configs/phase9-mtp-on-prose.json
.\scripts\download_phase13_iq4_xs.ps1 -PreflightOnly
.\scripts\run_phase13_offload_frontier.ps1
.\scripts\run_phase13_measurement.ps1 -Config configs/phase13-iq4-xs-4k-q8.json
.\scripts\run_phase13_mtp_measurement.ps1 -Config configs/phase13-iq4-xs-mtp-off-prose.json
.\scripts\run_phase13_retrieval.ps1 -Config configs/phase13-iq4-xs-retrieval-16k-q4.json
.\scripts\run_phase13_objective_quality.ps1
```

`collect_environment.ps1` performs read-only inspection and prints JSON to standard output. Saving a new snapshot should be an explicit action so existing environment records are never overwritten silently.

`run_phase1_smoke.ps1` requires Unsloth Desktop and the pinned Phase 1 model to be running. It verifies the active model and settings before sending three tools-off, thinking-off prompts. Each invocation writes a uniquely named JSON record and refuses to overwrite an existing result.

`run_quant_smoke.ps1` applies the same checks to any downloaded quant described by a compatible manifest. The model must already be loaded with the controlled 4K configuration. It records the current Git commit, exact model provenance, effective settings, responses, usage, and point-in-time GPU snapshots without storing the local authentication secret.

`start_native_llama_server.ps1` validates the pinned IQ2 model by size and SHA-256, verifies the official `b10448` executable and `CUDA0` device probe, and starts a hidden loopback-only server on port 8090 with localhost-only CORS. Trace-level startup logging retains CUDA allocation and layer-offload evidence. It creates non-overwriting logs and a launch record under the ignored `runtimes/` tree. Pass `-SkipModelHashValidation` only for later routine restarts after the canonical validation has been recorded.

`run_native_smoke.ps1` calls the native server's OpenAI-compatible `/v1/chat/completions` endpoint with thinking, built-in tools, MCP, and vision disabled. The server uses the `deepseek` reasoning parser only to keep Qwen's empty `<think>` wrapper out of answer content; it does not enable reasoning generation. The script writes a unique Phase 3 proof-of-life record; this is not the repeated Phase 4 baseline.

`run_phase4_baseline.ps1` verifies the active model and material Phase 3 launch arguments, then runs the committed long-form workload once as warm-up and three times as measured repetitions. It uses streaming SSE to measure time to first non-empty content token, retains llama.cpp's prompt/decode timings, disables prompt caching, and starts `collect_run_telemetry.ps1` in a hidden helper process targeting a 250 ms cadence for GPU, VRAM, llama-server CPU, and process RAM. Every run records both the target and observed cadence. Raw output is unique and append-only.

`setup_python.ps1` accepts CPython 3.11 through 3.14, creates the ignored `.venv`, and verifies the source package. The harness has no runtime package dependencies.

`run_python_tests.ps1` executes the offline `unittest` suite from the isolated environment. Its local mock HTTP server and injected telemetry probes test our code without making model-performance claims.

`run_phase5_harness.ps1` finds exactly one pinned llama.cpp `b10448` process, passes its PID to the Python CLI, and executes `configs/phase5-iq2-smoke.json`. The Python preflight independently verifies loopback scope, model alias, context, slots, and manifest model path before sending the request. A result is created exclusively under `results/raw/`; existing files are never overwritten.

`run_phase6_measurement.ps1` accepts only one of the two frozen Phase 6 configurations, verifies the selected PID belongs to the pinned native server, and delegates the repeated measurement to the tested Python package. Model switching remains an explicit operator action so a failed launch cannot silently benchmark the wrong quant.

`run_phase7_measurement.ps1` accepts only one of the frozen 4K, 8K, or 16K IQ2 configurations. A fresh server with the matching context must already be running. Python preflight rejects an alias, path, slot count, or context mismatch before a canonical request is sent.

`run_phase8_quality.ps1` accepts only the frozen Q2 or IQ2 quality configuration and requires the pinned native server executable. The Python runner performs server preflight, attempts every committed task once, retains each raw response and deterministic grade, independently re-grades the record against the suite, and writes one unique append-only result.

`start_native_llama_server.ps1` additionally accepts `-SpeculativeType draft-mtp` with bounded draft-token controls. `run_phase9_measurement.ps1` accepts only the four frozen MTP configurations, matches the selected PID to one ignored launch record, verifies the expected MTP mode and F16 draft-cache controls, and then delegates to the Python harness. Every response must contain draft counters when MTP is on and no draft activity when it is off.

For Phase 13, `start_native_llama_server.ps1` also accepts explicit `-GpuLayers`, `-KvCacheKType`, and `-KvCacheVType` controls while preserving the Phase 3-9 defaults. `download_phase13_iq4_xs.ps1` enforces the pinned revision, exact byte count, SHA-256, repository-bound ignored destination, conservative free-space gate, resumable `.partial` transfer, and validate-before-move sequence. `run_phase13_offload_frontier.ps1` refuses to run beside an existing pinned server, validates the model once, probes fresh processes, retains failures, and selects the largest layer request that passes the frozen 1,024 MiB VRAM-headroom gate. Its explicit `-ContextSize` and `-KvCacheType` controls permit a separate capacity frontier without silently reusing the 4K/Q8 result.

`run_phase13_measurement.ps1` accepts only the frozen Phase 13 baseline, cache-pair, and active-context configurations. It verifies the selected process belongs to the pinned runtime, binds it to one ignored launch record, requires a hash-validated IQ4_XS load, and dynamically requires the config's exact context, MTP-off state, K/V types, requested layers, and observed startup placement before delegating to the Python harness.

`run_phase13_mtp_measurement.ps1` accepts only the four frozen IQ4_XS MTP configs and proves exact model, context, 40/66 placement, Q4_0 K/V, and off/on draft controls before measurement. `run_phase13_retrieval.ps1` applies the same launch binding to the frozen 16K Q8_0/Q4_0 and 64K Q4_0 retrieval configs before objective pass@1 grading.

`run_phase13_objective_quality.ps1` accepts only the 4K/Q8_0/45-layer IQ4_XS quality config, requires matching startup evidence, and runs the unchanged 24-task Phase 8 objective suite once.

The `qwen-bench mtp-compare` command accepts the prose-off, prose-on, code-off, and code-on raw records in that order. It independently validates every record, rejects pairwise control drift or invalid draft counters, calculates per-workload changes and acceptance, and compares SHA-256 hashes of every measured response.

For the Phase 2 quant-triage suite, add:

```powershell
-PromptFile .\prompts\phase2-quant-triage.json `
-RunKind quant-triage `
-Classification phase2_quant_triage_not_formal_quality_benchmark
```
