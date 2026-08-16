# Phase 5 Python Harness Checkpoint

## Outcome

Phase 5 is complete. The repository now contains a tested Python benchmark package, an isolated environment workflow, a formal result schema, cross-field semantic validation, and a successful end-to-end model run whose raw output is retained.

The canonical smoke result was generated from committed harness revision `b0481d479b1a73d82f3539d93f80b6c0803bf2a0` and passes all twelve run-level validation checks.

## Software verification

| Check | Result |
|---|---:|
| Python | CPython 3.13.15 in ignored `.venv` |
| Runtime package dependencies | 0 |
| Offline unit/loopback-integration tests | 23 passed, 0 failed |
| Source compile/import check | Passed |
| Formal contract | JSON Schema Draft 2020-12 |
| Semantic result validation | Passed |
| Append-only collision/traversal tests | Passed |

The test suite covers configuration boundaries, duplicate JSON keys, loopback restrictions, local HTTP preflight, streamed SSE parsing, statistics, telemetry cadence, exclusive writes, filename safety, and cross-field result rules. The tests validate the harness rather than the model or GPU performance.

## Canonical engineering smoke

| Field | Observed value |
|---|---:|
| Warm-ups / measured repetitions | 0 / 1 |
| Prompt / completion tokens | 68 / 64 |
| Finish reason | `length` |
| Prompt cache tokens | 0 |
| Reasoning content | `null` |
| Response headers | 2.525 ms |
| TTFT | 87.340 ms |
| Total client latency | 1,536.353 ms |
| Server prompt throughput | 802.171 tok/s |
| Server generation throughput | 43.479 tok/s |
| Telemetry samples | 7 |
| Target / observed mean cadence | 250 / 255.471 ms |
| Peak VRAM / minimum free VRAM | 8,986 / 3,009 MiB |
| Peak sampled GPU utilization | 99% |
| Peak sampled temperature / power | 62°C / 258.84 W |

The exact response, timings, process memory, GPU samples, configuration, Python version, and provenance are retained in [`phase5-python-iq2-smoke-20260816T005922932894Z-a280beda.json`](../raw/phase5-python-iq2-smoke-20260816T005922932894Z-a280beda.json).

## Interpretation boundary

This was a single short engineering smoke run with no warm-up. Its purpose was to exercise the complete software path from preflight through append-only storage. The 43.479 tok/s observation is not a new baseline, has no variance estimate, and must not be compared directly with the repeated 256-token Phase 4 workload.

Phase 4 remains the current IQ2 performance baseline. Phase 6 will use the committed Python package with identical workloads and settings for the controlled IQ2-versus-Q2 comparison.
