# Reproducing the study

This repository supports two different forms of reproduction:

1. **Evidence verification** checks the software, links, schemas, calculations, and committed raw records. It needs Python and Git but no GPU or model weights.
2. **Hardware reproduction** reruns inference on a local Windows machine. It needs the pinned GGUF files, llama.cpp build, NVIDIA GPU environment, and deliberate operator control.

Do not interpret CI as a reproduction of RTX 4070 Ti performance. CI verifies only the software and public evidence bundle.

## Evidence verification without a model

### Requirements

- Windows PowerShell;
- Git;
- CPython 3.11 through 3.14.

From the repository root:

```powershell
.\scripts\setup_python.ps1
.\scripts\run_python_tests.ps1
$env:PYTHONPATH = (Resolve-Path .\src).Path
.\.venv\Scripts\python.exe -m qwen_bench release-audit --repository-root .
```

The ordinary release audit validates the technical public boundary while Phase 10 is in progress. The final release gate is stricter:

```powershell
.\.venv\Scripts\python.exe -m qwen_bench release-audit --repository-root . --strict
```

Strict mode intentionally fails until the citation identity, Code of Conduct contact, and final GitHub URLs are present. Apache-2.0 is already selected.

## Canonical result validation

The release manifest classifies every tracked raw record. Current-schema performance records can be validated individually:

```powershell
.\.venv\Scripts\python.exe -m qwen_bench validate `
    .\results\raw\phase9-mtp-on-code-20260816T041709353404Z-221a5138.json
```

Phase 8 validation reloads the committed task suite and independently re-grades every response:

```powershell
.\.venv\Scripts\python.exe -m qwen_bench quality-validate `
    --repository-root . `
    .\results\raw\phase8-quality-q2-20260816T033656385280Z-2359f380.json
```

Recompute the Phase 9 comparison directly from four raw records:

```powershell
.\.venv\Scripts\python.exe -m qwen_bench mtp-compare `
    .\results\raw\phase9-mtp-off-prose-20260816T041445808671Z-76083f38.json `
    .\results\raw\phase9-mtp-on-prose-20260816T041603771264Z-9c3f8aca.json `
    .\results\raw\phase9-mtp-off-code-20260816T041809117916Z-bdba6559.json `
    .\results\raw\phase9-mtp-on-code-20260816T041709353404Z-221a5138.json
```

## Hardware reproduction

### Reference environment

- NVIDIA GeForce RTX 4070 Ti with 12,282 MiB reported VRAM;
- Intel Core i7-14700K and 64 GB RAM;
- Windows 25H2;
- NVIDIA driver 610.88;
- official llama.cpp `b10448`, commit `ad1de39e0708e3ced9c71bb3c82d93a2c046a73f`;
- CUDA 13.3 Windows runtime bundle recorded in `environment/llama-cpp-b10448-manifest.json`.

Comparable hardware can still produce useful reproduction evidence, but every deviation must be disclosed. Do not present a changed GPU, driver, runtime, model revision, context, or sampling configuration as an exact replication.

### Model artifacts

Model weights are intentionally excluded. Obtain the required files from the repository and revisions pinned in:

- `environment/model-download-manifest.json` for `UD-IQ2_XXS`;
- `environment/phase2-q2-k-xl-download-manifest.json` for `UD-Q2_K_XL`.

Place files at the repository-relative paths declared by those manifests. Validate filename, byte size, and SHA-256 before measurement. The launch wrapper performs hash validation by default.

### Native runtime

The official runtime archives and checksums are recorded in `environment/llama-cpp-b10448-manifest.json`. Extract them under the ignored layout expected by the scripts:

```text
runtimes/llama.cpp/b10448/
├── bin/
└── cuda-13.3/
```

Start the default IQ2 4K MTP-off server:

```powershell
.\scripts\start_native_llama_server.ps1
```

The wrapper verifies the executable build, CUDA0 device, model size and hash, loopback port availability, and healthy startup. It retains ignored local launch records and logs under `runtimes/`.

## Phase-specific measurements

The scripts do not silently switch models. Start a fresh server with the manifest, context, alias, and MTP state required by the selected committed configuration, inspect its startup log, then run the matching wrapper.

### Controlled quant comparison

```powershell
.\scripts\run_phase6_measurement.ps1 -Config configs/phase6-iq2-comparison.json
.\scripts\run_phase6_measurement.ps1 -Config configs/phase6-q2-comparison.json
```

Each model needs a fresh matching server process. See `environment/phase6-comparison-protocol-2026-08-15.json` for the frozen order and controls.

### Context ladder

```powershell
.\scripts\run_phase7_measurement.ps1 -Config configs/phase7-iq2-context-4k.json
.\scripts\run_phase7_measurement.ps1 -Config configs/phase7-iq2-context-8k.json
.\scripts\run_phase7_measurement.ps1 -Config configs/phase7-iq2-context-16k.json
```

Restart the server with the matching `-ContextSize` before each configuration.

### Objective quality evaluation

```powershell
.\scripts\run_phase8_quality.ps1 -Config configs/phase8-quality-q2.json
.\scripts\run_phase8_quality.ps1 -Config configs/phase8-quality-iq2.json
```

Run Q2 then IQ2 from fresh processes as frozen in the Phase 8 protocol. Do not edit tasks, expected answers, or graders after observing responses.

### MTP experiment

Start the appropriate state before every configuration:

```powershell
.\scripts\start_native_llama_server.ps1 -SpeculativeType none
.\scripts\start_native_llama_server.ps1 `
    -SpeculativeType draft-mtp `
    -SpeculativeDraftMaximum 2 `
    -SpeculativeDraftMinimum 0
```

Then run the counterbalanced sequence from the committed protocol:

```powershell
.\scripts\run_phase9_measurement.ps1 -Config configs/phase9-mtp-off-prose.json
.\scripts\run_phase9_measurement.ps1 -Config configs/phase9-mtp-on-prose.json
.\scripts\run_phase9_measurement.ps1 -Config configs/phase9-mtp-on-code.json
.\scripts\run_phase9_measurement.ps1 -Config configs/phase9-mtp-off-code.json
```

Use a fresh process for every line. Response-level validation requires positive draft counters when MTP is on and zero or absent draft activity when it is off.

## Reporting a reproduction

Retain raw JSON, exact prompts, runtime and model revisions, launch flags, startup layer placement, hash checks, failed attempts, telemetry cadence, and interpretation limits. Report measured facts separately from estimates. If you change a controlled input, call the result a related experiment rather than an exact reproduction.

Never commit model weights, runtime archives, desktop secrets, local user paths, proprietary prompt data, or the private learning files.
