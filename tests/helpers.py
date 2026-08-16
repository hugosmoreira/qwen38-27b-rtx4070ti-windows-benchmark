from __future__ import annotations

from typing import Any


def valid_statistics(value: float = 1.0) -> dict[str, float | int]:
    return {
        "count": 1,
        "mean": value,
        "sample_standard_deviation": 0.0,
        "coefficient_of_variation_percent": 0.0,
        "minimum": value,
        "maximum": value,
    }


def valid_result() -> dict[str, Any]:
    statistics = valid_statistics()
    summary = {
        "expected_repetitions": 1,
        "completed_repetitions": 1,
        "time_to_first_content_token_ms": dict(statistics),
        "total_latency_ms": dict(statistics),
        "server_prompt_tokens_per_second": dict(statistics),
        "server_generation_tokens_per_second": dict(statistics),
        "peak_vram_used_mib": dict(statistics),
        "minimum_vram_free_mib": dict(statistics),
        "peak_gpu_utilization_percent": dict(statistics),
        "peak_process_working_set_bytes": dict(statistics),
        "peak_process_private_memory_bytes": dict(statistics),
        "peak_process_cpu_percent_of_machine": dict(statistics),
        "all_expected_runs_completed": True,
    }
    telemetry_summary = {
        "target_interval_milliseconds": 250,
        "sample_count": 1,
        "observed_span_milliseconds": None,
        "observed_mean_interval_milliseconds": None,
        "observed_minimum_interval_milliseconds": None,
        "observed_maximum_interval_milliseconds": None,
        "peak_vram_used_mib": 1.0,
        "minimum_vram_free_mib": 1.0,
        "peak_gpu_utilization_percent": 1.0,
        "peak_gpu_temperature_c": 1.0,
        "peak_gpu_power_draw_w": 1.0,
        "peak_process_working_set_bytes": 1.0,
        "peak_process_private_memory_bytes": 1.0,
        "peak_process_cpu_percent_of_machine": 1.0,
    }
    run = {
        "run_label": "measured-1",
        "warmup": False,
        "repetition": 1,
        "status": "completed",
        "error": None,
        "client_measurements": {
            "response_headers_ms": 1.0,
            "time_to_first_content_token_ms": 1.0,
            "total_latency_ms": 1.0,
        },
        "server_measurements": {
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            "timings": {"cache_n": 0, "prompt_per_second": 1.0, "predicted_per_second": 1.0},
            "system_fingerprint": "test",
        },
        "response": {"finish_reason": "length", "content": "ok", "reasoning_content": None},
        "telemetry_summary": telemetry_summary,
        "telemetry_samples": [
            {
                "timestamp_utc": "2026-08-16T00:00:00Z",
                "monotonic_elapsed_milliseconds": 0.0,
                "target_process_id": 1,
                "process_running": True,
                "gpu": {},
                "process": {},
            }
        ],
        "telemetry_errors": [],
        "validation": {"request_succeeded": True},
    }
    return {
        "schema_version": "benchmark-result-1.0.0",
        "run_id": "test-run",
        "timestamp": "2026-08-16T00:00:00Z",
        "git_commit": "a" * 40,
        "classification": "test",
        "hardware_snapshot": "environment/hardware.json",
        "runtime_record": "environment/runtime.json",
        "model_manifest": "environment/model.json",
        "prompt_suite": "prompts/test.json",
        "benchmark_config": "configs/test.json",
        "python_runtime": {
            "implementation": "CPython",
            "version": "3.13.15",
            "isolated_environment": True,
            "runtime_dependencies": [],
        },
        "runtime": {
            "name": "llama.cpp",
            "release_tag": "b10448",
            "commit": "b" * 40,
            "backend": "CUDA",
            "system_fingerprint": "test",
        },
        "model": {
            "repository": "owner/model",
            "revision": "c" * 40,
            "filename": "model.gguf",
            "quantization": "test",
            "file_size_bytes": 1,
            "sha256": "d" * 64,
            "served_alias": "test",
        },
        "configuration": {"context_size": 4096},
        "methodology": {
            "warmup_runs": 0,
            "measured_repetitions": 1,
            "streaming": True,
            "ttft_definition": "test",
            "total_latency_definition": "test",
            "prompt_cache_disabled": True,
            "telemetry_target_interval_milliseconds": 250,
            "telemetry_scope": "test",
            "inter_run_delay_seconds": 0.0,
        },
        "server_preflight": {
            "status": "passed",
            "checks": {"health_ok": True},
            "served_model_alias": "test",
        },
        "runs": [run],
        "measured_summary": summary,
        "outcome": {"status": "completed", "error_type": None, "error_message": None},
    }
