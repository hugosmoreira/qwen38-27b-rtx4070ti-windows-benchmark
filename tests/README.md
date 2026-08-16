# Tests

The test suite validates our benchmark software, not the language model. It uses Python's standard `unittest` runner and requires no downloaded packages.

Current coverage includes:

- controlled configuration and path validation;
- deterministic synthetic-context expansion and context-budget validation;
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
- Phase 8 paired-config normalization and task independence from Phase 2;
- exact/JSON grading, including duplicate keys and non-standard numeric constants;
- quality-record count, category, finish-reason, and independent re-grade checks;
- paired contingency counts and known-value exact McNemar calculations.

Run all tests with:

```powershell
.\scripts\run_python_tests.ps1
```

GPU performance is intentionally excluded from ordinary tests. The loopback HTTP test uses a temporary local server, and the collector unit test uses fake probes, so CI must not claim to reproduce RTX 4070 Ti performance.
