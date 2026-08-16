"""End-to-end benchmark orchestration."""

from __future__ import annotations

import os
import platform
import secrets
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from qwen_bench.client import LlamaCppClient, StreamResult
from qwen_bench.config import BenchmarkConfig, repository_relative
from qwen_bench.fixtures import build_user_content, synthetic_context_metadata
from qwen_bench.statistics import descriptive_statistics
from qwen_bench.telemetry import TelemetryCollector, summarize_telemetry


def execute_benchmark(config: BenchmarkConfig, server_process_id: int) -> dict[str, Any]:
    if server_process_id <= 0:
        raise ValueError("Server process ID must be positive.")

    started = datetime.now(timezone.utc)
    run_id = _create_run_id(str(config.data["run"]["result_prefix"]), started)
    record = _base_record(config, run_id, started)
    client = LlamaCppClient(config.base_uri)

    try:
        record["server_preflight"] = client.validate_server(
            model_alias=config.model_alias,
            expected_context_size=int(config.data["server"]["expected_context_size"]),
            expected_parallel_slots=int(config.data["server"]["expected_parallel_slots"]),
            expected_model_path=str(config.expected_model_path),
        )
    except Exception as error:
        record["server_preflight"] = {"status": "failed", "checks": None, "served_model_alias": None}
        record["measured_summary"] = _measured_summary([], int(config.data["run"]["measured_repetitions"]), False)
        record["outcome"] = {
            "status": "failed_preflight",
            "error_type": type(error).__name__,
            "error_message": _safe_error(error),
        }
        return record

    warmups = int(config.data["run"]["warmup_runs"])
    repetitions = int(config.data["run"]["measured_repetitions"])
    total_runs = warmups + repetitions
    inter_run_delay = float(config.data["run"]["inter_run_delay_seconds"])
    runs: list[dict[str, Any]] = []

    for index in range(total_runs):
        warmup = index < warmups
        repetition = index + 1 if warmup else index - warmups + 1
        label = f"warmup-{repetition}" if warmup else f"measured-{repetition}"
        run = _execute_one(config, client, server_process_id, label, warmup, repetition)
        runs.append(run)
        if run["status"] != "completed":
            break
        if index < total_runs - 1 and inter_run_delay > 0:
            time.sleep(inter_run_delay)

    record["runs"] = runs
    completed_measured = [run for run in runs if not run["warmup"] and run["status"] == "completed"]
    all_expected = len(runs) == total_runs and all(run["status"] == "completed" for run in runs)
    record["measured_summary"] = _measured_summary(completed_measured, repetitions, all_expected)
    fingerprints = [
        run["server_measurements"].get("system_fingerprint")
        for run in runs
        if run.get("server_measurements")
    ]
    if any(fingerprints):
        record["runtime"]["system_fingerprint"] = next(value for value in reversed(fingerprints) if value)
    record["outcome"] = {
        "status": "completed" if all_expected else "failed_run",
        "error_type": None if all_expected else "RunValidationError",
        "error_message": None if all_expected else "One or more expected runs did not complete validation.",
    }
    return record


def _execute_one(
    config: BenchmarkConfig,
    client: LlamaCppClient,
    server_process_id: int,
    label: str,
    warmup: bool,
    repetition: int,
) -> dict[str, Any]:
    interval = int(config.data["telemetry"]["interval_milliseconds"])
    collector: TelemetryCollector | None = None
    stream_result: StreamResult | None = None
    error: Exception | None = None
    stop_error: Exception | None = None

    try:
        collector = TelemetryCollector(server_process_id, interval)
        collector.start()
        if not collector.wait_until_ready(5.0):
            raise RuntimeError("Telemetry collector did not produce an initial sample.")
        stream_result = client.stream_chat(_request_body(config))
    except Exception as caught:
        error = caught
    finally:
        if collector is not None:
            try:
                collector.stop()
            except Exception as caught:
                stop_error = caught

    samples = collector.samples if collector is not None else []
    collector_errors = collector.errors if collector is not None else []
    telemetry_summary = summarize_telemetry(samples, interval)
    if stop_error is not None and error is None:
        error = stop_error

    usage = stream_result.usage if stream_result is not None else None
    timings = stream_result.timings if stream_result is not None else None
    acceptance = config.prompt["workload"]["acceptance"]
    validation = {
        "request_succeeded": error is None and stream_result is not None,
        "first_content_observed": stream_result is not None
        and stream_result.time_to_first_content_token_ms is not None,
        "usage_observed": isinstance(usage, dict),
        "timings_observed": isinstance(timings, dict),
        "prompt_cache_disabled": isinstance(timings, dict) and timings.get("cache_n") == 0,
        "minimum_completion_tokens_met": isinstance(usage, dict)
        and int(usage.get("completion_tokens", -1)) >= int(acceptance["minimum_completion_tokens"]),
        "expected_finish_reason": stream_result is not None
        and stream_result.finish_reason == acceptance["expected_finish_reason"],
        "reasoning_empty": stream_result is not None and stream_result.reasoning_content is None,
        "telemetry_observed": len(samples) > 0,
        "gpu_telemetry_observed": any(isinstance(sample.get("gpu"), dict) for sample in samples),
        "process_telemetry_observed": any(isinstance(sample.get("process"), dict) for sample in samples),
        "telemetry_error_free": not collector_errors,
        "mtp_activity_matches_configuration": _mtp_activity_matches(
            timings, bool(config.data["configuration"]["mtp_enabled"])
        ),
    }
    if "minimum_prompt_tokens" in acceptance:
        prompt_tokens = usage.get("prompt_tokens") if isinstance(usage, dict) else None
        validation["prompt_tokens_in_expected_range"] = (
            isinstance(prompt_tokens, int)
            and int(acceptance["minimum_prompt_tokens"])
            <= prompt_tokens
            <= int(acceptance["maximum_prompt_tokens"])
        )
        completion_tokens = usage.get("completion_tokens") if isinstance(usage, dict) else None
        validation["context_budget_respected"] = (
            isinstance(prompt_tokens, int)
            and isinstance(completion_tokens, int)
            and prompt_tokens + completion_tokens
            <= int(config.data["configuration"]["context_size"])
        )
    completed = all(validation.values())
    return {
        "run_label": label,
        "warmup": warmup,
        "repetition": repetition,
        "status": "completed" if completed else "failed_validation",
        "error": None if error is None else {"type": type(error).__name__, "message": _safe_error(error)},
        "client_measurements": {
            "response_headers_ms": stream_result.response_headers_ms if stream_result else None,
            "time_to_first_content_token_ms": (
                stream_result.time_to_first_content_token_ms if stream_result else None
            ),
            "total_latency_ms": stream_result.total_latency_ms if stream_result else None,
        },
        "server_measurements": {
            "usage": usage,
            "timings": timings,
            "system_fingerprint": stream_result.system_fingerprint if stream_result else None,
        },
        "response": {
            "finish_reason": stream_result.finish_reason if stream_result else None,
            "content": stream_result.content if stream_result else "",
            "reasoning_content": stream_result.reasoning_content if stream_result else None,
        },
        "telemetry_summary": telemetry_summary,
        "telemetry_samples": samples,
        "telemetry_errors": collector_errors,
        "validation": validation,
    }


def _base_record(config: BenchmarkConfig, run_id: str, started: datetime) -> dict[str, Any]:
    manifest = config.model_manifest
    runtime = config.data["runtime"]
    settings = config.prompt["settings"]
    controlled_configuration = dict(config.data["configuration"])
    controlled_configuration.update(
        {
            "max_output_tokens": int(settings["max_tokens"]),
            "temperature": float(settings["temperature"]),
            "top_p": float(settings["top_p"]),
            "top_k": int(settings["top_k"]),
            "min_p": float(settings["min_p"]),
            "seed": int(settings["seed"]),
            "prompt_cache": False,
        }
    )
    controlled_configuration.update(synthetic_context_metadata(config.prompt["workload"]))
    return {
        "schema_version": "benchmark-result-1.0.0",
        "run_id": run_id,
        "timestamp": started.isoformat().replace("+00:00", "Z"),
        "git_commit": _git_commit(config.repository_root),
        "classification": str(config.data["run"]["classification"]),
        "hardware_snapshot": "environment/machine-snapshot-2026-08-15.json",
        "runtime_record": repository_relative(config.repository_root, config.runtime_record_path),
        "model_manifest": repository_relative(config.repository_root, config.model_manifest_path),
        "prompt_suite": repository_relative(config.repository_root, config.prompt_path),
        "benchmark_config": repository_relative(config.repository_root, config.source_path),
        "python_runtime": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "isolated_environment": sys.prefix != sys.base_prefix,
            "runtime_dependencies": [],
        },
        "runtime": {
            "name": str(runtime["name"]),
            "release_tag": str(runtime["release_tag"]),
            "commit": str(runtime["commit"]),
            "backend": str(runtime["backend"]),
            "system_fingerprint": None,
        },
        "model": {
            "repository": str(manifest["repository"]),
            "revision": str(manifest["repository_commit"]),
            "filename": str(manifest["filename"]),
            "quantization": str(config.data["model"]["quantization"]),
            "file_size_bytes": int(manifest["size_bytes"]),
            "sha256": str(manifest["sha256"]),
            "served_alias": config.model_alias,
        },
        "configuration": controlled_configuration,
        "methodology": {
            "warmup_runs": int(config.data["run"]["warmup_runs"]),
            "measured_repetitions": int(config.data["run"]["measured_repetitions"]),
            "streaming": True,
            "ttft_definition": "Elapsed wall time from HTTP send until the first non-empty assistant content delta was read.",
            "total_latency_definition": "Elapsed wall time from HTTP send through the SSE done marker.",
            "prompt_cache_disabled": True,
            "telemetry_target_interval_milliseconds": int(
                config.data["telemetry"]["interval_milliseconds"]
            ),
            "telemetry_scope": "NVIDIA GPU 0 plus the selected llama-server process",
            "inter_run_delay_seconds": float(config.data["run"]["inter_run_delay_seconds"]),
        },
        "server_preflight": None,
        "runs": [],
        "measured_summary": None,
        "outcome": None,
    }


def _request_body(config: BenchmarkConfig) -> dict[str, Any]:
    settings = config.prompt["settings"]
    workload = config.prompt["workload"]
    return {
        "model": config.model_alias,
        "messages": [
            {"role": "system", "content": str(workload["system"])},
            {"role": "user", "content": build_user_content(workload)},
        ],
        "stream": True,
        "stream_options": {"include_usage": True},
        "max_tokens": int(settings["max_tokens"]),
        "temperature": float(settings["temperature"]),
        "top_p": float(settings["top_p"]),
        "top_k": int(settings["top_k"]),
        "min_p": float(settings["min_p"]),
        "seed": int(settings["seed"]),
        "cache_prompt": False,
        "chat_template_kwargs": {"enable_thinking": False, "preserve_thinking": False},
    }


def _measured_summary(
    runs: list[dict[str, Any]], expected_repetitions: int, all_expected: bool
) -> dict[str, Any]:
    return {
        "expected_repetitions": expected_repetitions,
        "completed_repetitions": len(runs),
        "time_to_first_content_token_ms": descriptive_statistics(
            run["client_measurements"]["time_to_first_content_token_ms"] for run in runs
        ),
        "total_latency_ms": descriptive_statistics(
            run["client_measurements"]["total_latency_ms"] for run in runs
        ),
        "server_prompt_tokens_per_second": descriptive_statistics(
            _nested(run, "server_measurements", "timings", "prompt_per_second") for run in runs
        ),
        "server_generation_tokens_per_second": descriptive_statistics(
            _nested(run, "server_measurements", "timings", "predicted_per_second") for run in runs
        ),
        "server_draft_tokens": descriptive_statistics(
            _nested(run, "server_measurements", "timings", "draft_n") for run in runs
        ),
        "server_accepted_draft_tokens": descriptive_statistics(
            _nested(run, "server_measurements", "timings", "draft_n_accepted") for run in runs
        ),
        "server_draft_acceptance_percent": descriptive_statistics(
            _draft_acceptance_percent(_nested(run, "server_measurements", "timings"))
            for run in runs
        ),
        "peak_vram_used_mib": descriptive_statistics(
            run["telemetry_summary"]["peak_vram_used_mib"] for run in runs
        ),
        "minimum_vram_free_mib": descriptive_statistics(
            run["telemetry_summary"]["minimum_vram_free_mib"] for run in runs
        ),
        "peak_gpu_utilization_percent": descriptive_statistics(
            run["telemetry_summary"]["peak_gpu_utilization_percent"] for run in runs
        ),
        "peak_process_working_set_bytes": descriptive_statistics(
            run["telemetry_summary"]["peak_process_working_set_bytes"] for run in runs
        ),
        "peak_process_private_memory_bytes": descriptive_statistics(
            run["telemetry_summary"]["peak_process_private_memory_bytes"] for run in runs
        ),
        "peak_process_cpu_percent_of_machine": descriptive_statistics(
            run["telemetry_summary"]["peak_process_cpu_percent_of_machine"] for run in runs
        ),
        "prompt_tokens": descriptive_statistics(
            _nested(run, "server_measurements", "usage", "prompt_tokens") for run in runs
        ),
        "completion_tokens": descriptive_statistics(
            _nested(run, "server_measurements", "usage", "completion_tokens") for run in runs
        ),
        "all_expected_runs_completed": all_expected,
    }


def _nested(record: dict[str, Any], *keys: str) -> Any:
    value: Any = record
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _mtp_activity_matches(timings: Any, enabled: bool) -> bool:
    if not isinstance(timings, dict):
        return False
    draft = timings.get("draft_n")
    accepted = timings.get("draft_n_accepted")
    if enabled:
        return (
            isinstance(draft, int)
            and not isinstance(draft, bool)
            and draft > 0
            and isinstance(accepted, int)
            and not isinstance(accepted, bool)
            and 0 <= accepted <= draft
        )
    return draft in {None, 0} and accepted in {None, 0}


def _draft_acceptance_percent(timings: Any) -> float | None:
    if not isinstance(timings, dict):
        return None
    draft = timings.get("draft_n")
    accepted = timings.get("draft_n_accepted")
    if (
        not isinstance(draft, int)
        or isinstance(draft, bool)
        or draft <= 0
        or not isinstance(accepted, int)
        or isinstance(accepted, bool)
        or not 0 <= accepted <= draft
    ):
        return None
    return accepted / draft * 100.0


def _create_run_id(prefix: str, started: datetime) -> str:
    stamp = started.strftime("%Y%m%dT%H%M%S%fZ")
    return f"{prefix}-{stamp}-{secrets.token_hex(4)}"


def _git_commit(repository_root: Path) -> str:
    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    completed = subprocess.run(
        ["git", "-c", f"safe.directory={repository_root.as_posix()}", "rev-parse", "HEAD"],
        cwd=repository_root,
        capture_output=True,
        text=True,
        check=True,
        timeout=10.0,
        creationflags=creation_flags,
    )
    return completed.stdout.strip()


def _safe_error(error: Exception) -> str:
    message = str(error).replace("\r", " ").replace("\n", " ").strip()
    return message[:500] or type(error).__name__
