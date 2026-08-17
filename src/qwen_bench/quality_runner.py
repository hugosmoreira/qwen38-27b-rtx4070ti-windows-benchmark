"""Pass@1 orchestration for the Phase 8 objective quality suite."""

from __future__ import annotations

import os
import platform
import secrets
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from qwen_bench.client import LlamaCppClient, StreamResult
from qwen_bench.config import repository_relative
from qwen_bench.fixtures import build_user_content
from qwen_bench.quality_config import QualityConfig
from qwen_bench.quality_grading import GradeResult, grade_response


_REQUEST_COMPLETION_CHECKS = (
    "request_succeeded",
    "usage_observed",
    "timings_observed",
    "prompt_cache_disabled",
    "reasoning_empty",
)


def execute_quality_evaluation(config: QualityConfig, server_process_id: int) -> dict[str, Any]:
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
        record["server_preflight"] = {
            "status": "failed",
            "checks": None,
            "served_model_alias": None,
        }
        record["summary"] = _summarize([], config.suite["tasks"])
        record["outcome"] = {
            "status": "failed_preflight",
            "error_type": type(error).__name__,
            "error_message": _safe_error(error),
        }
        return record

    results: list[dict[str, Any]] = []
    delay = float(config.data["run"]["inter_task_delay_seconds"])
    tasks = config.suite["tasks"]
    for index, task in enumerate(tasks):
        results.append(_execute_task(config, client, task, index + 1))
        if index < len(tasks) - 1 and delay > 0:
            time.sleep(delay)
    record["tasks"] = results
    record["summary"] = _summarize(results, tasks)
    all_requests_completed = all(result["status"] == "completed" for result in results)
    record["outcome"] = {
        "status": "completed" if all_requests_completed else "failed_run",
        "error_type": None if all_requests_completed else "QualityRequestError",
        "error_message": None if all_requests_completed else "One or more task requests failed validation.",
    }
    fingerprints = [result["system_fingerprint"] for result in results if result["system_fingerprint"]]
    if fingerprints:
        record["runtime"]["system_fingerprint"] = fingerprints[-1]
    return record


def _execute_task(
    config: QualityConfig,
    client: LlamaCppClient,
    task: dict[str, Any],
    sequence: int,
) -> dict[str, Any]:
    stream_result: StreamResult | None = None
    error: Exception | None = None
    try:
        stream_result = client.stream_chat(_request_body(config, task))
    except Exception as caught:
        error = caught
    usage = stream_result.usage if stream_result else None
    timings = stream_result.timings if stream_result else None
    content = stream_result.content if stream_result else ""
    grade = grade_response(task["validator"], content) if stream_result else GradeResult(False, "no_response")
    validation = {
        "request_succeeded": error is None and stream_result is not None,
        "content_observed": bool(content),
        "usage_observed": isinstance(usage, dict),
        "timings_observed": isinstance(timings, dict),
        "prompt_cache_disabled": isinstance(timings, dict) and timings.get("cache_n") == 0,
        "reasoning_empty": stream_result is not None and stream_result.reasoning_content is None,
    }
    acceptance = task.get("acceptance")
    if isinstance(acceptance, dict):
        prompt_tokens = usage.get("prompt_tokens") if isinstance(usage, dict) else None
        validation["prompt_tokens_in_expected_range"] = (
            isinstance(prompt_tokens, int)
            and not isinstance(prompt_tokens, bool)
            and int(acceptance["minimum_prompt_tokens"])
            <= prompt_tokens
            <= int(acceptance["maximum_prompt_tokens"])
        )
    completed = _request_completed(validation)
    return {
        "sequence": sequence,
        "task_id": str(task["task_id"]),
        "category": str(task["category"]),
        "validator_type": str(task["validator"]["type"]),
        "status": "completed" if completed else "failed_request",
        "passed": completed and grade.passed,
        "grade": {"passed": completed and grade.passed, "reason": grade.reason},
        "error": None if error is None else {"type": type(error).__name__, "message": _safe_error(error)},
        "client_measurements": {
            "response_headers_ms": stream_result.response_headers_ms if stream_result else None,
            "time_to_first_content_token_ms": (
                stream_result.time_to_first_content_token_ms if stream_result else None
            ),
            "total_latency_ms": stream_result.total_latency_ms if stream_result else None,
        },
        "finish_reason": stream_result.finish_reason if stream_result else None,
        "content": content,
        "reasoning_content": stream_result.reasoning_content if stream_result else None,
        "usage": usage,
        "timings": timings,
        "system_fingerprint": stream_result.system_fingerprint if stream_result else None,
        "validation": validation,
    }


def _request_body(config: QualityConfig, task: dict[str, Any]) -> dict[str, Any]:
    settings = config.suite["settings"]
    return {
        "model": config.model_alias,
        "messages": [
            {"role": "system", "content": str(task["system"])},
            {"role": "user", "content": build_user_content(task)},
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


def _request_completed(validation: dict[str, bool]) -> bool:
    """Return whether transport/control evidence is complete, independent of answer quality."""
    required = list(_REQUEST_COMPLETION_CHECKS)
    if "prompt_tokens_in_expected_range" in validation:
        required.append("prompt_tokens_in_expected_range")
    return all(validation.get(check) is True for check in required)


def _summarize(results: list[dict[str, Any]], declared_tasks: list[dict[str, Any]]) -> dict[str, Any]:
    category_order = list(dict.fromkeys(str(task["category"]) for task in declared_tasks))
    categories: dict[str, dict[str, int | float]] = {}
    for category in category_order:
        category_results = [result for result in results if result["category"] == category]
        declared = sum(1 for task in declared_tasks if task["category"] == category)
        passed = sum(1 for result in category_results if result["passed"])
        categories[category] = {
            "attempted": len(category_results),
            "expected": declared,
            "passed": passed,
            "pass_rate_percent": round((passed / declared) * 100, 3) if declared else 0.0,
        }
    passed = sum(1 for result in results if result["passed"])
    expected = len(declared_tasks)
    finish_reasons = Counter(
        str(result["finish_reason"]) for result in results if result["finish_reason"] is not None
    )
    return {
        "tasks_expected": expected,
        "tasks_attempted": len(results),
        "requests_completed": sum(1 for result in results if result["status"] == "completed"),
        "tasks_passed": passed,
        "pass_rate_percent": round((passed / expected) * 100, 3) if expected else 0.0,
        "category_results": categories,
        "finish_reason_counts": dict(sorted(finish_reasons.items())),
        "all_expected_requests_completed": len(results) == expected
        and all(result["status"] == "completed" for result in results),
    }


def _base_record(config: QualityConfig, run_id: str, started: datetime) -> dict[str, Any]:
    manifest = config.model_manifest
    runtime = config.data["runtime"]
    settings = config.suite["settings"]
    controlled = dict(config.data["configuration"])
    controlled.update(
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
    return {
        "schema_version": "quality-evaluation-result-1.0.0",
        "run_id": run_id,
        "timestamp": started.isoformat().replace("+00:00", "Z"),
        "git_commit": _git_commit(config.repository_root),
        "classification": str(config.data["run"]["classification"]),
        "hardware_snapshot": "environment/machine-snapshot-2026-08-15.json",
        "runtime_record": repository_relative(config.repository_root, config.runtime_record_path),
        "model_manifest": repository_relative(config.repository_root, config.model_manifest_path),
        "prompt_suite": repository_relative(config.repository_root, config.suite_path),
        "quality_config": repository_relative(config.repository_root, config.source_path),
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
        "configuration": controlled,
        "methodology": {
            "pass_definition": "First response passes its committed deterministic validator.",
            "attempts_per_task": 1,
            "task_order_randomized": False,
            "prompt_cache_disabled": True,
            "thinking_disabled": True,
            "tools_disabled": True,
            "inter_task_delay_seconds": float(config.data["run"]["inter_task_delay_seconds"]),
            "expected_tasks": len(config.suite["tasks"]),
        },
        "server_preflight": None,
        "tasks": [],
        "summary": None,
        "outcome": None,
    }


def _create_run_id(prefix: str, started: datetime) -> str:
    return f"{prefix}-{started.strftime('%Y%m%dT%H%M%S%fZ')}-{secrets.token_hex(4)}"


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
