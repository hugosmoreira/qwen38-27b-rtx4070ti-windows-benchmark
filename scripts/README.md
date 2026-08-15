# Scripts

PowerShell entry points used to reproduce setup, launches, and benchmark runs will live here.

Current scripts:

```powershell
.\scripts\collect_environment.ps1
.\scripts\run_phase1_smoke.ps1
.\scripts\run_quant_smoke.ps1 -ManifestPath .\environment\phase2-q2-k-xl-download-manifest.json `
    -RuntimeRecord environment/phase2-q2-k-xl-runtime-2026-08-15.json
```

`collect_environment.ps1` performs read-only inspection and prints JSON to standard output. Saving a new snapshot should be an explicit action so existing environment records are never overwritten silently.

`run_phase1_smoke.ps1` requires Unsloth Desktop and the pinned Phase 1 model to be running. It verifies the active model and settings before sending three tools-off, thinking-off prompts. Each invocation writes a uniquely named JSON record and refuses to overwrite an existing result.

`run_quant_smoke.ps1` applies the same checks to any downloaded quant described by a compatible manifest. The model must already be loaded with the controlled 4K configuration. It records the current Git commit, exact model provenance, effective settings, responses, usage, and point-in-time GPU snapshots without storing the local authentication secret.
