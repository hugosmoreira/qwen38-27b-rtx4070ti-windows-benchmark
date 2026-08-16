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
- `quality_config.py` — paired quality-suite and controlled-setting validation;
- `quality_grading.py` — exact text and duplicate-key-free semantic JSON grading;
- `quality_runner.py` — one-attempt-per-task orchestration and raw-response retention;
- `quality_result_validation.py` — cross-field checks plus independent re-grading against the committed suite;
- `quality_comparison.py` — paired contingency counts and two-sided exact McNemar calculation;
- `cli.py` — performance run/validation and quality run/validation/comparison commands.

The formal interoperable schemas are [`schemas/benchmark-result.schema.json`](../schemas/benchmark-result.schema.json) and [`schemas/quality-evaluation-result.schema.json`](../schemas/quality-evaluation-result.schema.json). The in-package validators add cross-field rules that JSON Schema alone does not conveniently express, including count reconciliation and re-grading saved Phase 8 responses from the committed validators.

For quality runs, transport completion and answer quality are separate. A successfully received empty answer remains a completed request, is preserved verbatim, and receives zero credit from its task validator. A request exception with no response is recorded as `no_response`.

Large context inputs are described compactly by a versioned fixture generator. Each result retains the generated user-message byte count and SHA-256 so the exact expanded input can be audited without duplicating tens of thousands of words in the repository.

## Direct invocation

From the repository root:

```powershell
$env:PYTHONPATH = (Resolve-Path .\src).Path
.\.venv\Scripts\python.exe -m qwen_bench --help
```

Use the PowerShell wrappers under `scripts/` for normal setup, tests, and the controlled Phase 5 smoke run.
