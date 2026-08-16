"""Dependency-free structural and semantic validation for benchmark results."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
_RUN_STATUS = {"completed", "failed_validation"}
_OUTCOME_STATUS = {"completed", "failed_preflight", "failed_run"}


def validate_result(record: Any) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not isinstance(record, dict):
        return [ValidationIssue("$", "result must be a JSON object")]

    required = {
        "schema_version",
        "run_id",
        "timestamp",
        "git_commit",
        "classification",
        "hardware_snapshot",
        "runtime_record",
        "model_manifest",
        "prompt_suite",
        "benchmark_config",
        "python_runtime",
        "runtime",
        "model",
        "configuration",
        "methodology",
        "server_preflight",
        "runs",
        "measured_summary",
        "outcome",
    }
    _require_keys(record, required, "$", issues)
    if record.get("schema_version") != "benchmark-result-1.0.0":
        issues.append(ValidationIssue("$.schema_version", "unsupported schema version"))
    _nonempty_string(record.get("run_id"), "$.run_id", issues)
    _nonempty_string(record.get("timestamp"), "$.timestamp", issues)
    _nonempty_string(record.get("classification"), "$.classification", issues)
    if not isinstance(record.get("git_commit"), str) or not _COMMIT_PATTERN.fullmatch(record["git_commit"]):
        issues.append(ValidationIssue("$.git_commit", "must be a 40-character lowercase Git commit"))
    for key in ("hardware_snapshot", "runtime_record", "model_manifest", "prompt_suite", "benchmark_config"):
        _relative_reference(record.get(key), f"$.{key}", issues)

    python_runtime = record.get("python_runtime")
    if isinstance(python_runtime, dict):
        _require_keys(
            python_runtime,
            {"implementation", "version", "isolated_environment", "runtime_dependencies"},
            "$.python_runtime",
            issues,
        )
        if not isinstance(python_runtime.get("isolated_environment"), bool):
            issues.append(ValidationIssue("$.python_runtime.isolated_environment", "must be boolean"))
        if not isinstance(python_runtime.get("runtime_dependencies"), list):
            issues.append(ValidationIssue("$.python_runtime.runtime_dependencies", "must be an array"))
    else:
        issues.append(ValidationIssue("$.python_runtime", "must be an object"))

    for key in ("runtime", "model", "configuration", "methodology"):
        if not isinstance(record.get(key), dict):
            issues.append(ValidationIssue(f"$.{key}", "must be an object"))

    preflight = record.get("server_preflight")
    if not isinstance(preflight, dict) or preflight.get("status") not in {"passed", "failed"}:
        issues.append(ValidationIssue("$.server_preflight", "must contain status 'passed' or 'failed'"))

    runs = record.get("runs")
    if not isinstance(runs, list):
        issues.append(ValidationIssue("$.runs", "must be an array"))
        runs = []
    for index, run in enumerate(runs):
        _validate_run(run, index, issues)

    summary = record.get("measured_summary")
    _validate_summary(summary, runs, record.get("methodology"), issues)
    outcome = record.get("outcome")
    _validate_outcome(outcome, preflight, summary, issues)
    return issues


def require_valid_result(record: Any) -> None:
    issues = validate_result(record)
    if issues:
        detail = "\n".join(str(issue) for issue in issues[:20])
        raise ValueError(f"Benchmark result failed validation:\n{detail}")


def _validate_run(run: Any, index: int, issues: list[ValidationIssue]) -> None:
    path = f"$.runs[{index}]"
    if not isinstance(run, dict):
        issues.append(ValidationIssue(path, "must be an object"))
        return
    _require_keys(
        run,
        {
            "run_label",
            "warmup",
            "repetition",
            "status",
            "error",
            "client_measurements",
            "server_measurements",
            "response",
            "telemetry_summary",
            "telemetry_samples",
            "telemetry_errors",
            "validation",
        },
        path,
        issues,
    )
    _nonempty_string(run.get("run_label"), f"{path}.run_label", issues)
    if not isinstance(run.get("warmup"), bool):
        issues.append(ValidationIssue(f"{path}.warmup", "must be boolean"))
    if not isinstance(run.get("repetition"), int) or isinstance(run.get("repetition"), bool) or run["repetition"] < 1:
        issues.append(ValidationIssue(f"{path}.repetition", "must be a positive integer"))
    if run.get("status") not in _RUN_STATUS:
        issues.append(ValidationIssue(f"{path}.status", "has an unsupported run status"))
    for key in ("client_measurements", "server_measurements", "response", "telemetry_summary", "validation"):
        if not isinstance(run.get(key), dict):
            issues.append(ValidationIssue(f"{path}.{key}", "must be an object"))
    if not isinstance(run.get("telemetry_samples"), list):
        issues.append(ValidationIssue(f"{path}.telemetry_samples", "must be an array"))
    if not isinstance(run.get("telemetry_errors"), list):
        issues.append(ValidationIssue(f"{path}.telemetry_errors", "must be an array"))

    validation = run.get("validation")
    if isinstance(validation, dict):
        if not validation:
            issues.append(ValidationIssue(f"{path}.validation", "must not be empty"))
        non_boolean = [key for key, value in validation.items() if not isinstance(value, bool)]
        if non_boolean:
            issues.append(ValidationIssue(f"{path}.validation", "all validation values must be boolean"))
        all_passed = bool(validation) and all(value is True for value in validation.values())
        if (run.get("status") == "completed") != all_passed:
            issues.append(ValidationIssue(f"{path}.status", "must agree with the validation booleans"))


def _validate_summary(
    summary: Any, runs: list[Any], methodology: Any, issues: list[ValidationIssue]
) -> None:
    path = "$.measured_summary"
    if not isinstance(summary, dict):
        issues.append(ValidationIssue(path, "must be an object"))
        return
    required = {
        "expected_repetitions",
        "completed_repetitions",
        "time_to_first_content_token_ms",
        "total_latency_ms",
        "server_prompt_tokens_per_second",
        "server_generation_tokens_per_second",
        "peak_vram_used_mib",
        "minimum_vram_free_mib",
        "peak_gpu_utilization_percent",
        "peak_process_working_set_bytes",
        "peak_process_private_memory_bytes",
        "peak_process_cpu_percent_of_machine",
        "all_expected_runs_completed",
    }
    _require_keys(summary, required, path, issues)
    expected = summary.get("expected_repetitions")
    completed = summary.get("completed_repetitions")
    if not isinstance(expected, int) or isinstance(expected, bool) or expected < 1:
        issues.append(ValidationIssue(f"{path}.expected_repetitions", "must be a positive integer"))
    measured_completed = sum(
        1 for run in runs if isinstance(run, dict) and not run.get("warmup") and run.get("status") == "completed"
    )
    if completed != measured_completed:
        issues.append(ValidationIssue(f"{path}.completed_repetitions", "does not match completed measured runs"))
    warmup_expected = methodology.get("warmup_runs") if isinstance(methodology, dict) else None
    measured_expected = methodology.get("measured_repetitions") if isinstance(methodology, dict) else None
    if isinstance(measured_expected, int) and expected != measured_expected:
        issues.append(ValidationIssue(f"{path}.expected_repetitions", "does not match methodology"))
    all_expected = summary.get("all_expected_runs_completed")
    if not isinstance(all_expected, bool):
        issues.append(ValidationIssue(f"{path}.all_expected_runs_completed", "must be boolean"))
    elif isinstance(expected, int) and isinstance(warmup_expected, int) and all_expected != (
        measured_completed == expected
        and len(runs) == warmup_expected + expected
        and sum(1 for run in runs if isinstance(run, dict) and run.get("warmup")) == warmup_expected
        and all(isinstance(run, dict) and run.get("status") == "completed" for run in runs)
    ):
        issues.append(ValidationIssue(f"{path}.all_expected_runs_completed", "is semantically inconsistent"))

    for key in required - {"expected_repetitions", "completed_repetitions", "all_expected_runs_completed"}:
        value = summary.get(key)
        if value is not None:
            _validate_statistics(value, f"{path}.{key}", completed, issues)


def _validate_statistics(value: Any, path: str, completed: Any, issues: list[ValidationIssue]) -> None:
    if not isinstance(value, dict):
        issues.append(ValidationIssue(path, "must be null or a statistics object"))
        return
    required = {
        "count",
        "mean",
        "sample_standard_deviation",
        "coefficient_of_variation_percent",
        "minimum",
        "maximum",
    }
    _require_keys(value, required, path, issues)
    if value.get("count") != completed:
        issues.append(ValidationIssue(f"{path}.count", "must equal completed repetitions"))
    for key in required - {"count", "coefficient_of_variation_percent"}:
        if not _is_number(value.get(key)):
            issues.append(ValidationIssue(f"{path}.{key}", "must be numeric"))
    if value.get("coefficient_of_variation_percent") is not None and not _is_number(
        value.get("coefficient_of_variation_percent")
    ):
        issues.append(ValidationIssue(f"{path}.coefficient_of_variation_percent", "must be numeric or null"))


def _validate_outcome(
    outcome: Any, preflight: Any, summary: Any, issues: list[ValidationIssue]
) -> None:
    if not isinstance(outcome, dict):
        issues.append(ValidationIssue("$.outcome", "must be an object"))
        return
    _require_keys(outcome, {"status", "error_type", "error_message"}, "$.outcome", issues)
    if outcome.get("status") not in _OUTCOME_STATUS:
        issues.append(ValidationIssue("$.outcome.status", "has an unsupported outcome status"))
        return
    all_expected = summary.get("all_expected_runs_completed") if isinstance(summary, dict) else False
    if outcome.get("status") == "completed" and not all_expected:
        issues.append(ValidationIssue("$.outcome.status", "completed outcome requires all expected runs"))
    if outcome.get("status") == "failed_preflight" and isinstance(preflight, dict) and preflight.get("status") != "failed":
        issues.append(ValidationIssue("$.outcome.status", "failed_preflight requires failed preflight"))
    if outcome.get("status") == "completed" and (outcome.get("error_type") is not None or outcome.get("error_message") is not None):
        issues.append(ValidationIssue("$.outcome", "completed outcome cannot contain an error"))


def _require_keys(data: dict[str, Any], keys: set[str], path: str, issues: list[ValidationIssue]) -> None:
    for key in sorted(keys - data.keys()):
        issues.append(ValidationIssue(f"{path}.{key}", "required property is missing"))


def _relative_reference(value: Any, path: str, issues: list[ValidationIssue]) -> None:
    if not isinstance(value, str) or not value or "\\" in value or value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        issues.append(ValidationIssue(path, "must be a non-empty repository-relative POSIX path"))


def _nonempty_string(value: Any, path: str, issues: list[ValidationIssue]) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(ValidationIssue(path, "must be a non-empty string"))


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)
