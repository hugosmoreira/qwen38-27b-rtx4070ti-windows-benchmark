# Schemas

`benchmark-result.schema.json` is the formal JSON Schema Draft 2020-12 contract for Python harness result files.

`quality-evaluation-result.schema.json` is the separate Draft 2020-12 contract for Phase 8 pass@1 records. It retains every task response, grade, request validation, usage object, and llama.cpp timing object without treating those timings as a performance benchmark.

The result summary permits optional prompt-token, completion-token, and MTP draft/acceptance aggregates while remaining compatible with earlier Phase 5 and Phase 6 records.

The Python package also applies semantic checks that span multiple fields, including:

- completed run status agrees with all per-run validation booleans;
- completed repetition counts agree with the run array;
- warm-up and measured counts agree with methodology;
- a completed outcome requires all expected runs;
- public provenance references are repository-relative paths.

Validate a result with:

```powershell
$env:PYTHONPATH = (Resolve-Path .\src).Path
.\.venv\Scripts\python.exe -m qwen_bench validate .\results\raw\RESULT.json
```

Quality validation also reloads the repository-relative committed suite and independently re-grades every saved response:

```powershell
$env:PYTHONPATH = (Resolve-Path .\src).Path
.\.venv\Scripts\python.exe -m qwen_bench quality-validate .\results\raw\QUALITY_RESULT.json
```
