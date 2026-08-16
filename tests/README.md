# Tests

The test suite validates our benchmark software, not the language model. It uses Python's standard `unittest` runner and requires no downloaded packages.

Current coverage includes:

- controlled configuration and path validation;
- duplicate JSON key rejection;
- loopback-only client safety;
- local HTTP preflight and streamed SSE parsing;
- TTFT/usage/timing extraction;
- summary statistics and missing-value behavior;
- NVIDIA CSV and telemetry cadence calculations;
- the collector thread with injected deterministic probes;
- append-only result creation and filename traversal prevention;
- structural and cross-field result validation;
- formal schema presence and versioning.

Run all tests with:

```powershell
.\scripts\run_python_tests.ps1
```

GPU performance is intentionally excluded from ordinary tests. The loopback HTTP test uses a temporary local server, and the collector unit test uses fake probes, so CI must not claim to reproduce RTX 4070 Ti performance.
