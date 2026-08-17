"""Configuration loading for objective pass@1 quality evaluations."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qwen_bench.client import require_loopback_uri
from qwen_bench.config import (
    ConfigurationError,
    load_json_object,
    resolve_repository_path,
)
from qwen_bench.fixtures import NEEDLE_RECORDS_GENERATOR


_CATEGORIES = {
    "arithmetic",
    "logic",
    "python_trace",
    "structured_output",
    "text_data",
}
_RETRIEVAL_CATEGORIES = {"retrieval_early", "retrieval_middle", "retrieval_late"}


@dataclass(frozen=True)
class QualityConfig:
    repository_root: Path
    source_path: Path
    data: dict[str, Any]
    suite: dict[str, Any]
    model_manifest: dict[str, Any]
    runtime_record: dict[str, Any]
    suite_path: Path
    model_manifest_path: Path
    runtime_record_path: Path
    output_directory: Path

    @property
    def base_uri(self) -> str:
        return str(self.data["server"]["base_uri"])

    @property
    def model_alias(self) -> str:
        return str(self.data["server"]["model_alias"])

    @property
    def expected_model_path(self) -> Path:
        return resolve_repository_path(
            self.repository_root,
            str(self.model_manifest["relative_local_path"]),
            must_exist=True,
        )


def load_quality_config(repository_root: Path, config_path: Path) -> QualityConfig:
    root = repository_root.resolve()
    source = resolve_repository_path(root, str(config_path), must_exist=True)
    data = load_json_object(source)
    _exact(data, "schema_version", "quality-config-1.0")
    for section in ("run", "server", "inputs", "runtime", "model", "configuration"):
        if not isinstance(data.get(section), dict):
            raise ConfigurationError(f"Quality configuration section '{section}' must be an object.")

    run = data["run"]
    classification = _string(run, "classification")
    result_prefix = _string(run, "result_prefix")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_]{0,119}", classification):
        raise ConfigurationError("Quality classification has unsupported characters.")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", result_prefix):
        raise ConfigurationError("Quality result prefix has unsupported characters.")
    delay = run.get("inter_task_delay_seconds")
    if not _number(delay) or not 0 <= float(delay) <= 30:
        raise ConfigurationError("Inter-task delay must be between 0 and 30 seconds.")

    server = data["server"]
    require_loopback_uri(_string(server, "base_uri"))
    _string(server, "model_alias")
    _integer(server, "expected_context_size", minimum=128)
    _integer(server, "expected_parallel_slots", minimum=1, maximum=32)

    inputs = data["inputs"]
    suite_path = resolve_repository_path(root, _string(inputs, "prompt_suite"), must_exist=True)
    manifest_path = resolve_repository_path(root, _string(inputs, "model_manifest"), must_exist=True)
    runtime_path = resolve_repository_path(root, _string(inputs, "runtime_record"), must_exist=True)
    output_directory = resolve_repository_path(root, _string(run, "output_directory"))
    suite = load_json_object(suite_path)
    manifest = load_json_object(manifest_path)
    runtime_record = load_json_object(runtime_path)
    validate_quality_suite(suite)
    _validate_manifest(manifest)

    runtime = data["runtime"]
    for key in ("name", "release_tag", "backend"):
        _string(runtime, key)
    commit = _string(runtime, "commit")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ConfigurationError("Quality runtime commit must be a lowercase 40-character Git commit.")

    configuration = data["configuration"]
    if configuration.get("context_size") != server["expected_context_size"]:
        raise ConfigurationError("Quality configuration and server context sizes disagree.")
    if configuration.get("parallel_slots") != server["expected_parallel_slots"]:
        raise ConfigurationError("Quality configuration and server slot counts disagree.")
    for disabled in (
        "thinking_mode",
        "preserve_thinking",
        "mtp_enabled",
        "tools_enabled",
        "mcp_enabled",
        "vision_enabled",
    ):
        if configuration.get(disabled) is not False:
            raise ConfigurationError(f"Quality setting '{disabled}' must be false.")
    _string(data["model"], "quantization")

    return QualityConfig(
        repository_root=root,
        source_path=source,
        data=data,
        suite=suite,
        model_manifest=manifest,
        runtime_record=runtime_record,
        suite_path=suite_path,
        model_manifest_path=manifest_path,
        runtime_record_path=runtime_path,
        output_directory=output_directory,
    )


def validate_quality_suite(suite: dict[str, Any]) -> None:
    _exact(suite, "schema_version", "quality-suite-1.0")
    _string(suite, "suite_id")
    _string(suite, "purpose")
    settings = suite.get("settings")
    tasks = suite.get("tasks")
    if not isinstance(settings, dict) or not isinstance(tasks, list):
        raise ConfigurationError("Quality settings must be an object and tasks must be an array.")
    suite_type = suite.get("suite_type", "objective_quality")
    if suite_type == "objective_quality":
        allowed_categories = _CATEGORIES
        if not 15 <= len(tasks) <= 30:
            raise ConfigurationError("Objective quality suite must contain between 15 and 30 tasks.")
    elif suite_type == "retrieval":
        allowed_categories = _RETRIEVAL_CATEGORIES
        if not 3 <= len(tasks) <= 12:
            raise ConfigurationError("Retrieval suite must contain between 3 and 12 tasks.")
    else:
        raise ConfigurationError("Unsupported quality suite type.")
    _integer(settings, "max_tokens", minimum=1, maximum=1024)
    _number_in_range(settings, "temperature", minimum=0, maximum=2)
    _number_in_range(settings, "top_p", minimum=0, maximum=1)
    _number_in_range(settings, "min_p", minimum=0, maximum=1)
    _integer(settings, "top_k", minimum=0)
    _integer(settings, "seed", minimum=0)
    if settings.get("stream") is not True:
        raise ConfigurationError("Quality requests must stream.")
    for key in ("cache_prompt", "thinking", "preserve_thinking"):
        if settings.get(key) is not False:
            raise ConfigurationError(f"Quality setting '{key}' must be false.")

    task_ids: set[str] = set()
    category_counts = {category: 0 for category in allowed_categories}
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            raise ConfigurationError(f"Quality task {index} must be an object.")
        task_id = _string(task, "task_id")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", task_id):
            raise ConfigurationError(f"Quality task ID '{task_id}' has unsupported characters.")
        if task_id in task_ids:
            raise ConfigurationError(f"Duplicate quality task ID '{task_id}'.")
        task_ids.add(task_id)
        category = _string(task, "category")
        if category not in allowed_categories:
            raise ConfigurationError(f"Unsupported quality category '{category}'.")
        category_counts[category] += 1
        for key in ("system", "user", "grading_notes"):
            _string(task, key)
        validator = task.get("validator")
        if not isinstance(validator, dict):
            raise ConfigurationError(f"Quality task '{task_id}' requires a validator object.")
        validator_type = _string(validator, "type")
        if set(validator) != {"type", "expected"}:
            raise ConfigurationError(f"Quality task '{task_id}' validator has unknown fields.")
        if validator_type == "exact":
            _string(validator, "expected")
        elif validator_type == "json_exact":
            if not isinstance(validator.get("expected"), (dict, list)):
                raise ConfigurationError("json_exact expected value must be an object or array.")
        else:
            raise ConfigurationError(f"Unsupported quality validator '{validator_type}'.")
        if suite_type == "retrieval":
            _validate_retrieval_task(task, task_id)
    if any(count == 0 for count in category_counts.values()):
        raise ConfigurationError("Every declared quality category must contain at least one task.")


def _validate_retrieval_task(task: dict[str, Any], task_id: str) -> None:
    fixture = task.get("synthetic_context")
    if not isinstance(fixture, dict):
        raise ConfigurationError(f"Retrieval task '{task_id}' requires synthetic_context.")
    expected_fields = {
        "generator",
        "record_count",
        "needle_record",
        "needle_key",
        "needle_value",
    }
    if set(fixture) != expected_fields:
        raise ConfigurationError(f"Retrieval task '{task_id}' has invalid fixture fields.")
    _exact(fixture, "generator", NEEDLE_RECORDS_GENERATOR)
    record_count = _integer(fixture, "record_count", minimum=3, maximum=100_000)
    _integer(fixture, "needle_record", minimum=1, maximum=record_count)
    for key in ("needle_key", "needle_value"):
        value = _string(fixture, key)
        if not re.fullmatch(r"[A-Z0-9-]{4,40}", value):
            raise ConfigurationError(f"Retrieval fixture '{key}' has unsupported characters.")
    acceptance = task.get("acceptance")
    if not isinstance(acceptance, dict) or set(acceptance) != {
        "minimum_prompt_tokens",
        "maximum_prompt_tokens",
    }:
        raise ConfigurationError(f"Retrieval task '{task_id}' requires prompt-token bounds.")
    minimum = _integer(acceptance, "minimum_prompt_tokens", minimum=1)
    _integer(acceptance, "maximum_prompt_tokens", minimum=minimum)


def _validate_manifest(manifest: dict[str, Any]) -> None:
    for key in ("repository", "repository_commit", "filename", "relative_local_path", "sha256"):
        _string(manifest, key)
    _integer(manifest, "size_bytes", minimum=1)
    if not re.fullmatch(r"[0-9a-f]{64}", str(manifest["sha256"])):
        raise ConfigurationError("Quality model SHA-256 must be 64 lowercase hexadecimal characters.")


def _exact(data: dict[str, Any], key: str, expected: Any) -> None:
    if data.get(key) != expected:
        raise ConfigurationError(f"'{key}' must equal {expected!r}.")


def _string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"'{key}' must be a non-empty string.")
    return value


def _integer(
    data: dict[str, Any], key: str, *, minimum: int | None = None, maximum: int | None = None
) -> int:
    value = data.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ConfigurationError(f"'{key}' must be an integer.")
    if minimum is not None and value < minimum:
        raise ConfigurationError(f"'{key}' must be at least {minimum}.")
    if maximum is not None and value > maximum:
        raise ConfigurationError(f"'{key}' must be at most {maximum}.")
    return value


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _number_in_range(
    data: dict[str, Any], key: str, *, minimum: float, maximum: float
) -> float:
    value = data.get(key)
    if not _number(value) or not minimum <= float(value) <= maximum:
        raise ConfigurationError(f"'{key}' must be between {minimum} and {maximum}.")
    return float(value)
