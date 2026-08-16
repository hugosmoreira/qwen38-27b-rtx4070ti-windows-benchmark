"""Configuration loading with repository-bound path and workload validation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qwen_bench.client import require_loopback_uri
from qwen_bench.fixtures import NUMBERED_RECORDS_GENERATOR


class ConfigurationError(ValueError):
    """Raised when benchmark configuration is incomplete or unsafe."""


@dataclass(frozen=True)
class BenchmarkConfig:
    repository_root: Path
    source_path: Path
    data: dict[str, Any]
    prompt: dict[str, Any]
    model_manifest: dict[str, Any]
    runtime_record: dict[str, Any]
    prompt_path: Path
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


def load_benchmark_config(repository_root: Path, config_path: Path) -> BenchmarkConfig:
    root = repository_root.resolve()
    source = resolve_repository_path(root, str(config_path), must_exist=True)
    data = load_json_object(source)
    _require_exact_value(data, "schema_version", "benchmark-config-1.0")

    for section in ("run", "server", "inputs", "runtime", "model", "configuration", "telemetry"):
        if not isinstance(data.get(section), dict):
            raise ConfigurationError(f"Configuration section '{section}' must be an object.")

    run = data["run"]
    classification = _require_nonempty_string(run, "classification")
    result_prefix = _require_nonempty_string(run, "result_prefix")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_]{0,119}", classification):
        raise ConfigurationError("Run classification may contain only lowercase letters, digits, and underscores.")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", result_prefix):
        raise ConfigurationError("Result prefix may contain only lowercase letters, digits, and hyphens.")
    _require_integer(run, "warmup_runs", minimum=0, maximum=5)
    _require_integer(run, "measured_repetitions", minimum=1, maximum=20)
    _require_number(run, "inter_run_delay_seconds", minimum=0, maximum=30)

    server = data["server"]
    require_loopback_uri(_require_nonempty_string(server, "base_uri"))
    _require_nonempty_string(server, "model_alias")
    _require_integer(server, "expected_context_size", minimum=128)
    _require_integer(server, "expected_parallel_slots", minimum=1, maximum=32)

    inputs = data["inputs"]
    prompt_path = resolve_repository_path(root, _require_nonempty_string(inputs, "prompt_suite"), must_exist=True)
    manifest_path = resolve_repository_path(root, _require_nonempty_string(inputs, "model_manifest"), must_exist=True)
    runtime_path = resolve_repository_path(root, _require_nonempty_string(inputs, "runtime_record"), must_exist=True)
    output_directory = resolve_repository_path(root, _require_nonempty_string(run, "output_directory"))

    prompt = load_json_object(prompt_path)
    manifest = load_json_object(manifest_path)
    runtime_record = load_json_object(runtime_path)
    _validate_prompt(prompt)
    _validate_manifest(manifest)

    acceptance = prompt["workload"]["acceptance"]
    maximum_prompt_tokens = acceptance.get("maximum_prompt_tokens")
    if maximum_prompt_tokens is not None:
        reserved = int(prompt["settings"]["max_tokens"])
        if maximum_prompt_tokens + reserved > int(server["expected_context_size"]):
            raise ConfigurationError(
                "Maximum accepted prompt tokens plus output reservation exceed the server context."
            )

    runtime = data["runtime"]
    for key in ("name", "release_tag", "backend"):
        _require_nonempty_string(runtime, key)
    commit = _require_nonempty_string(runtime, "commit")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ConfigurationError("Runtime commit must be a 40-character lowercase Git commit.")

    configuration = data["configuration"]
    if configuration.get("context_size") != server["expected_context_size"]:
        raise ConfigurationError("Configuration and server context sizes disagree.")
    if configuration.get("parallel_slots") != server["expected_parallel_slots"]:
        raise ConfigurationError("Configuration and server slot counts disagree.")
    for disabled in ("thinking_mode", "preserve_thinking", "mtp_enabled", "tools_enabled", "vision_enabled"):
        if configuration.get(disabled) is not False:
            raise ConfigurationError(f"Controlled smoke requires '{disabled}' to be false.")

    telemetry = data["telemetry"]
    _require_integer(telemetry, "interval_milliseconds", minimum=100, maximum=5_000)
    if telemetry.get("gpu_index") != 0:
        raise ConfigurationError("Phase 5 telemetry is pinned to NVIDIA GPU index 0.")
    _require_nonempty_string(data["model"], "quantization")

    return BenchmarkConfig(
        repository_root=root,
        source_path=source,
        data=data,
        prompt=prompt,
        model_manifest=manifest,
        runtime_record=runtime_record,
        prompt_path=prompt_path,
        model_manifest_path=manifest_path,
        runtime_record_path=runtime_path,
        output_directory=output_directory,
    )


def load_json_object(path: Path) -> dict[str, Any]:
    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ConfigurationError(f"Duplicate JSON key '{key}' in {path.name}.")
            result[key] = value
        return result

    try:
        with path.open("r", encoding="utf-8") as stream:
            value = json.load(stream, object_pairs_hook=reject_duplicate_keys)
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigurationError(f"Could not read valid JSON from {path.name}.") from error
    if not isinstance(value, dict):
        raise ConfigurationError(f"{path.name} must contain one JSON object.")
    return value


def resolve_repository_path(root: Path, value: str, must_exist: bool = False) -> Path:
    candidate = Path(value)
    resolved = (candidate if candidate.is_absolute() else root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ConfigurationError("Configuration paths must stay inside the repository.") from error
    if must_exist and not resolved.is_file():
        raise ConfigurationError(f"Required repository file does not exist: {value}")
    return resolved


def repository_relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _validate_prompt(prompt: dict[str, Any]) -> None:
    _require_exact_value(prompt, "schema_version", "1.0")
    _require_nonempty_string(prompt, "suite_id")
    settings = prompt.get("settings")
    workload = prompt.get("workload")
    if not isinstance(settings, dict) or not isinstance(workload, dict):
        raise ConfigurationError("Prompt settings and workload must be objects.")
    _require_integer(settings, "max_tokens", minimum=1, maximum=16_384)
    _require_number(settings, "temperature", minimum=0, maximum=2)
    _require_number(settings, "top_p", minimum=0, maximum=1)
    _require_integer(settings, "top_k", minimum=0)
    _require_number(settings, "min_p", minimum=0, maximum=1)
    _require_integer(settings, "seed", minimum=0)
    for required_false in ("cache_prompt", "thinking", "preserve_thinking"):
        if settings.get(required_false) is not False:
            raise ConfigurationError(f"Controlled prompt setting '{required_false}' must be false.")
    if settings.get("stream") is not True:
        raise ConfigurationError("Controlled prompt setting 'stream' must be true.")
    _require_nonempty_string(workload, "task_id")
    _require_nonempty_string(workload, "system")
    _require_nonempty_string(workload, "user")
    acceptance = workload.get("acceptance")
    if not isinstance(acceptance, dict):
        raise ConfigurationError("Prompt acceptance must be an object.")
    minimum = _require_integer(acceptance, "minimum_completion_tokens", minimum=1)
    if minimum > settings["max_tokens"]:
        raise ConfigurationError("Minimum completion tokens exceed max_tokens.")
    _require_nonempty_string(acceptance, "expected_finish_reason")
    minimum_prompt_tokens = acceptance.get("minimum_prompt_tokens")
    maximum_prompt_tokens = acceptance.get("maximum_prompt_tokens")
    if (minimum_prompt_tokens is None) != (maximum_prompt_tokens is None):
        raise ConfigurationError("Prompt-token acceptance bounds must be supplied together.")
    if minimum_prompt_tokens is not None:
        minimum_prompt_tokens = _require_integer(
            acceptance, "minimum_prompt_tokens", minimum=1
        )
        maximum_prompt_tokens = _require_integer(
            acceptance, "maximum_prompt_tokens", minimum=minimum_prompt_tokens
        )

    synthetic_context = workload.get("synthetic_context")
    if synthetic_context is not None:
        if not isinstance(synthetic_context, dict):
            raise ConfigurationError("Synthetic context must be an object.")
        if set(synthetic_context) != {"generator", "record_count"}:
            raise ConfigurationError(
                "Synthetic context must contain only generator and record_count."
            )
        _require_exact_value(
            synthetic_context, "generator", NUMBERED_RECORDS_GENERATOR
        )
        _require_integer(synthetic_context, "record_count", minimum=1, maximum=100_000)


def _validate_manifest(manifest: dict[str, Any]) -> None:
    for key in ("repository", "repository_commit", "filename", "relative_local_path", "sha256"):
        _require_nonempty_string(manifest, key)
    _require_integer(manifest, "size_bytes", minimum=1)
    if len(str(manifest["sha256"])) != 64:
        raise ConfigurationError("Model SHA-256 must contain 64 hexadecimal characters.")


def _require_exact_value(data: dict[str, Any], key: str, expected: Any) -> None:
    if data.get(key) != expected:
        raise ConfigurationError(f"'{key}' must equal {expected!r}.")


def _require_nonempty_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"'{key}' must be a non-empty string.")
    return value


def _require_integer(
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


def _require_number(
    data: dict[str, Any], key: str, *, minimum: float | None = None, maximum: float | None = None
) -> float:
    value = data.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ConfigurationError(f"'{key}' must be numeric.")
    number = float(value)
    if minimum is not None and number < minimum:
        raise ConfigurationError(f"'{key}' must be at least {minimum}.")
    if maximum is not None and number > maximum:
        raise ConfigurationError(f"'{key}' must be at most {maximum}.")
    return number
