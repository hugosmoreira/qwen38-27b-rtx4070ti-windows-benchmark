# Source Code

`qwen_bench` is a small, standard-library Python package for repeatable local inference measurements. It intentionally has no runtime package dependencies so the code path used for timing and telemetry remains easy to audit.

## Module map

- `client.py` — loopback-only HTTP preflight, OpenAI-compatible streaming requests, and TTFT measurement;
- `config.py` — duplicate-key rejection, controlled-setting validation, and repository-bound path resolution;
- `fixtures.py` — deterministic public synthetic-context expansion plus input byte/hash metadata;
- `runner.py` — warm-up/measured orchestration, validation, provenance, and summary assembly;
- `sse.py` — llama.cpp Server-Sent Events parsing;
- `statistics.py` — mean, sample standard deviation, coefficient of variation, minimum, and maximum;
- `storage.py` — exclusive append-only JSON creation with filename safety checks;
- `telemetry.py` — fixed-target-cadence NVIDIA and Windows process telemetry;
- `result_validation.py` — dependency-free structural and semantic result checks;
- `cli.py` — `run` and `validate` commands.

The formal interoperable schema is [`schemas/benchmark-result.schema.json`](../schemas/benchmark-result.schema.json). The in-package validator adds cross-field rules that JSON Schema alone does not conveniently express, such as matching measured counts and warm-up counts to the actual run array.

Large context inputs are described compactly by a versioned fixture generator. Each result retains the generated user-message byte count and SHA-256 so the exact expanded input can be audited without duplicating tens of thousands of words in the repository.

## Direct invocation

From the repository root:

```powershell
$env:PYTHONPATH = (Resolve-Path .\src).Path
.\.venv\Scripts\python.exe -m qwen_bench --help
```

Use the PowerShell wrappers under `scripts/` for normal setup, tests, and the controlled Phase 5 smoke run.
