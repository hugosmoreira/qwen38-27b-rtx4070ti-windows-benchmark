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
```

`collect_environment.ps1` performs read-only inspection and prints JSON to standard output. Saving a new snapshot should be an explicit action so existing environment records are never overwritten silently.

`run_phase1_smoke.ps1` requires Unsloth Desktop and the pinned Phase 1 model to be running. It verifies the active model and settings before sending three tools-off, thinking-off prompts. Each invocation writes a uniquely named JSON record and refuses to overwrite an existing result.

`run_quant_smoke.ps1` applies the same checks to any downloaded quant described by a compatible manifest. The model must already be loaded with the controlled 4K configuration. It records the current Git commit, exact model provenance, effective settings, responses, usage, and point-in-time GPU snapshots without storing the local authentication secret.

`start_native_llama_server.ps1` validates the pinned IQ2 model by size and SHA-256, verifies the official `b10448` executable and `CUDA0` device probe, and starts a hidden loopback-only server on port 8090. It creates non-overwriting logs and a launch record under the ignored `runtimes/` tree. Pass `-SkipModelHashValidation` only for later routine restarts after the canonical validation has been recorded.

`run_native_smoke.ps1` calls the native server's OpenAI-compatible `/v1/chat/completions` endpoint with thinking, built-in tools, MCP, and vision disabled. It writes a unique Phase 3 proof-of-life record; this is not the repeated Phase 4 baseline.

For the Phase 2 quant-triage suite, add:

```powershell
-PromptFile .\prompts\phase2-quant-triage.json `
-RunKind quant-triage `
-Classification phase2_quant_triage_not_formal_quality_benchmark
```
