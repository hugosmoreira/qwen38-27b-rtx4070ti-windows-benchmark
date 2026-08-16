"""Structural and cross-field validation for quality-evaluation records."""

from __future__ import annotations

import re
from typing import Any

from qwen_bench.quality_grading import GradeResult, grade_response
from qwen_bench.result_validation import ValidationIssue


_COMMIT = re.compile(r"^[0-9a-f]{40}$")


def validate_quality_result(
    record: Any, suite: dict[str, Any] | None = None
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not isinstance(record, dict):
        return [ValidationIssue("$", "quality result must be a JSON object")]
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
        "quality_config",
        "python_runtime",
        "runtime",
        "model",
        "configuration",
        "methodology",
        "server_preflight",
        "tasks",
        "summary",
        "outcome",
    }
    _require_keys(record, required, "$", issues)
    if record.get("schema_version") != "quality-evaluation-result-1.0.0":
        issues.append(ValidationIssue("$.schema_version", "unsupported quality schema version"))
    for key in ("run_id", "timestamp", "classification"):
        _nonempty(record.get(key), f"$.{key}", issues)
    if not isinstance(record.get("git_commit"), str) or not _COMMIT.fullmatch(record["git_commit"]):
        issues.append(ValidationIssue("$.git_commit", "must be a lowercase 40-character Git commit"))
    for key in ("hardware_snapshot", "runtime_record", "model_manifest", "prompt_suite", "quality_config"):
        _relative_reference(record.get(key), f"$.{key}", issues)
    for key in ("python_runtime", "runtime", "model", "configuration", "methodology"):
        if not isinstance(record.get(key), dict):
            issues.append(ValidationIssue(f"$.{key}", "must be an object"))

    preflight = record.get("server_preflight")
    if not isinstance(preflight, dict) or preflight.get("status") not in {"passed", "failed"}:
        issues.append(ValidationIssue("$.server_preflight", "must contain passed or failed status"))

    tasks = record.get("tasks")
    if not isinstance(tasks, list):
        issues.append(ValidationIssue("$.tasks", "must be an array"))
        tasks = []
    seen: set[str] = set()
    for index, task in enumerate(tasks):
        _validate_task(task, index, seen, issues)

    summary = record.get("summary")
    methodology = record.get("methodology")
    _validate_summary(summary, tasks, methodology, issues)
    _validate_outcome(record.get("outcome"), preflight, summary, issues)
    if suite is not None:
        _validate_against_suite(record, suite, tasks, issues)
    return issues


def require_valid_quality_result(record: Any, suite: dict[str, Any] | None = None) -> None:
    issues = validate_quality_result(record, suite)
    if issues:
        detail = "\n".join(str(issue) for issue in issues[:20])
        raise ValueError(f"Quality result failed validation:\n{detail}")


def _validate_task(
    task: Any,
    index: int,
    seen: set[str],
    issues: list[ValidationIssue],
) -> None:
    path = f"$.tasks[{index}]"
    if not isinstance(task, dict):
        issues.append(ValidationIssue(path, "must be an object"))
        return
    required = {
        "sequence",
        "task_id",
        "category",
        "validator_type",
        "status",
        "passed",
        "grade",
        "error",
        "client_measurements",
        "finish_reason",
        "content",
        "reasoning_content",
        "usage",
        "timings",
        "system_fingerprint",
        "validation",
    }
    _require_keys(task, required, path, issues)
    if task.get("sequence") != index + 1:
        issues.append(ValidationIssue(f"{path}.sequence", "must match one-based array order"))
    task_id = task.get("task_id")
    _nonempty(task_id, f"{path}.task_id", issues)
    if isinstance(task_id, str):
        if task_id in seen:
            issues.append(ValidationIssue(f"{path}.task_id", "must be unique"))
        seen.add(task_id)
    for key in ("category", "validator_type"):
        _nonempty(task.get(key), f"{path}.{key}", issues)
    if task.get("status") not in {"completed", "failed_request"}:
        issues.append(ValidationIssue(f"{path}.status", "has unsupported task status"))
    if not isinstance(task.get("passed"), bool):
        issues.append(ValidationIssue(f"{path}.passed", "must be boolean"))
    grade = task.get("grade")
    if not isinstance(grade, dict):
        issues.append(ValidationIssue(f"{path}.grade", "must be an object"))
    else:
        if not isinstance(grade.get("passed"), bool):
            issues.append(ValidationIssue(f"{path}.grade.passed", "must be boolean"))
        _nonempty(grade.get("reason"), f"{path}.grade.reason", issues)
        if task.get("passed") != grade.get("passed"):
            issues.append(ValidationIssue(f"{path}.passed", "must agree with grade.passed"))
    validation = task.get("validation")
    if not isinstance(validation, dict) or not validation:
        issues.append(ValidationIssue(f"{path}.validation", "must be a non-empty object"))
    else:
        if any(not isinstance(value, bool) for value in validation.values()):
            issues.append(ValidationIssue(f"{path}.validation", "all values must be boolean"))
        validation_passed = all(value is True for value in validation.values())
        if (task.get("status") == "completed") != validation_passed:
            issues.append(ValidationIssue(f"{path}.status", "must agree with validation booleans"))
    if task.get("status") != "completed" and task.get("passed") is True:
        issues.append(ValidationIssue(f"{path}.passed", "failed requests cannot pass grading"))
    if not isinstance(task.get("content"), str):
        issues.append(ValidationIssue(f"{path}.content", "must be a string"))


def _validate_summary(
    summary: Any,
    tasks: list[Any],
    methodology: Any,
    issues: list[ValidationIssue],
) -> None:
    path = "$.summary"
    if not isinstance(summary, dict):
        issues.append(ValidationIssue(path, "must be an object"))
        return
    required = {
        "tasks_expected",
        "tasks_attempted",
        "requests_completed",
        "tasks_passed",
        "pass_rate_percent",
        "category_results",
        "finish_reason_counts",
        "all_expected_requests_completed",
    }
    _require_keys(summary, required, path, issues)
    expected = summary.get("tasks_expected")
    declared = methodology.get("expected_tasks") if isinstance(methodology, dict) else None
    if not isinstance(expected, int) or isinstance(expected, bool) or expected < 1:
        issues.append(ValidationIssue(f"{path}.tasks_expected", "must be a positive integer"))
    if expected != declared:
        issues.append(ValidationIssue(f"{path}.tasks_expected", "must match methodology"))
    attempted = len(tasks)
    completed = sum(1 for task in tasks if isinstance(task, dict) and task.get("status") == "completed")
    passed = sum(1 for task in tasks if isinstance(task, dict) and task.get("passed") is True)
    if summary.get("tasks_attempted") != attempted:
        issues.append(ValidationIssue(f"{path}.tasks_attempted", "must match task array"))
    if summary.get("requests_completed") != completed:
        issues.append(ValidationIssue(f"{path}.requests_completed", "must match completed tasks"))
    if summary.get("tasks_passed") != passed:
        issues.append(ValidationIssue(f"{path}.tasks_passed", "must match passing tasks"))
    if isinstance(expected, int):
        rate = round((passed / expected) * 100, 3)
        if summary.get("pass_rate_percent") != rate:
            issues.append(ValidationIssue(f"{path}.pass_rate_percent", "must match pass count"))
        all_expected = attempted == expected and completed == expected
        if summary.get("all_expected_requests_completed") != all_expected:
            issues.append(
                ValidationIssue(
                    f"{path}.all_expected_requests_completed",
                    "is inconsistent with expected and completed tasks",
                )
            )
    category_results = summary.get("category_results")
    if not isinstance(category_results, dict):
        issues.append(ValidationIssue(f"{path}.category_results", "must be an object"))
    else:
        expected_by_category = 0
        attempted_by_category = 0
        passed_by_category = 0
        for category, values in category_results.items():
            if not isinstance(values, dict):
                issues.append(ValidationIssue(f"{path}.category_results.{category}", "must be an object"))
                continue
            category_tasks = [task for task in tasks if isinstance(task, dict) and task.get("category") == category]
            category_expected = values.get("expected")
            category_passed = sum(1 for task in category_tasks if task.get("passed") is True)
            if values.get("attempted") != len(category_tasks):
                issues.append(ValidationIssue(f"{path}.category_results.{category}.attempted", "must match tasks"))
            if values.get("passed") != category_passed:
                issues.append(ValidationIssue(f"{path}.category_results.{category}.passed", "must match tasks"))
            if not isinstance(category_expected, int) or isinstance(category_expected, bool) or category_expected < 1:
                issues.append(ValidationIssue(f"{path}.category_results.{category}.expected", "must be positive"))
                continue
            expected_by_category += category_expected
            attempted_by_category += len(category_tasks)
            passed_by_category += category_passed
            category_rate = round((category_passed / category_expected) * 100, 3)
            if values.get("pass_rate_percent") != category_rate:
                issues.append(
                    ValidationIssue(
                        f"{path}.category_results.{category}.pass_rate_percent",
                        "must match the category pass count and declared denominator",
                    )
                )
        if expected_by_category != expected:
            issues.append(ValidationIssue(f"{path}.category_results", "expected counts must sum to total"))
        if attempted_by_category != attempted:
            issues.append(ValidationIssue(f"{path}.category_results", "attempted counts must cover all tasks"))
        if passed_by_category != passed:
            issues.append(ValidationIssue(f"{path}.category_results", "pass counts must cover all tasks"))
    finish_reason_counts = summary.get("finish_reason_counts")
    observed_finish_reasons: dict[str, int] = {}
    for task in tasks:
        if isinstance(task, dict) and task.get("finish_reason") is not None:
            reason = str(task["finish_reason"])
            observed_finish_reasons[reason] = observed_finish_reasons.get(reason, 0) + 1
    if finish_reason_counts != dict(sorted(observed_finish_reasons.items())):
        issues.append(ValidationIssue(f"{path}.finish_reason_counts", "must match task finish reasons"))


def _validate_outcome(
    outcome: Any,
    preflight: Any,
    summary: Any,
    issues: list[ValidationIssue],
) -> None:
    if not isinstance(outcome, dict):
        issues.append(ValidationIssue("$.outcome", "must be an object"))
        return
    _require_keys(outcome, {"status", "error_type", "error_message"}, "$.outcome", issues)
    status = outcome.get("status")
    if status not in {"completed", "failed_preflight", "failed_run"}:
        issues.append(ValidationIssue("$.outcome.status", "has unsupported outcome status"))
        return
    all_expected = summary.get("all_expected_requests_completed") if isinstance(summary, dict) else False
    if status == "completed" and not all_expected:
        issues.append(ValidationIssue("$.outcome.status", "completed outcome requires every request"))
    if status == "completed" and isinstance(preflight, dict) and preflight.get("status") != "passed":
        issues.append(ValidationIssue("$.outcome.status", "completed outcome requires passed preflight"))
    if status == "failed_preflight" and isinstance(preflight, dict) and preflight.get("status") != "failed":
        issues.append(ValidationIssue("$.outcome.status", "failed_preflight requires failed preflight"))
    if status == "completed" and (outcome.get("error_type") is not None or outcome.get("error_message") is not None):
        issues.append(ValidationIssue("$.outcome", "completed outcome cannot contain an error"))


def _validate_against_suite(
    record: dict[str, Any],
    suite: dict[str, Any],
    tasks: list[Any],
    issues: list[ValidationIssue],
) -> None:
    declared_tasks = suite.get("tasks")
    if not isinstance(declared_tasks, list):
        issues.append(ValidationIssue("$.prompt_suite", "referenced suite must contain a task array"))
        return
    outcome = record.get("outcome")
    if not tasks and isinstance(outcome, dict) and outcome.get("status") == "failed_preflight":
        return
    if len(tasks) != len(declared_tasks):
        issues.append(ValidationIssue("$.tasks", "must contain every task from the referenced suite"))
    for index, (task, declared) in enumerate(zip(tasks, declared_tasks)):
        if not isinstance(task, dict) or not isinstance(declared, dict):
            continue
        path = f"$.tasks[{index}]"
        declared_validator = declared.get("validator")
        expected_metadata = {
            "task_id": declared.get("task_id"),
            "category": declared.get("category"),
            "validator_type": (
                declared_validator.get("type") if isinstance(declared_validator, dict) else None
            ),
        }
        for key, expected_value in expected_metadata.items():
            if task.get(key) != expected_value:
                issues.append(ValidationIssue(f"{path}.{key}", "must match the referenced suite"))
        if not isinstance(declared_validator, dict) or not isinstance(task.get("content"), str):
            continue
        if task.get("status") == "failed_request" and not task["content"]:
            regrade = GradeResult(False, "no_response")
        else:
            regrade = grade_response(declared_validator, task["content"])
        expected_pass = task.get("status") == "completed" and regrade.passed
        grade = task.get("grade")
        if task.get("passed") != expected_pass:
            issues.append(ValidationIssue(f"{path}.passed", "must match an independent re-grade"))
        if isinstance(grade, dict):
            if grade.get("passed") != expected_pass:
                issues.append(ValidationIssue(f"{path}.grade.passed", "must match an independent re-grade"))
            if grade.get("reason") != regrade.reason:
                issues.append(ValidationIssue(f"{path}.grade.reason", "must match an independent re-grade"))


def _require_keys(
    data: dict[str, Any],
    keys: set[str],
    path: str,
    issues: list[ValidationIssue],
) -> None:
    for key in sorted(keys - data.keys()):
        issues.append(ValidationIssue(f"{path}.{key}", "required property is missing"))


def _relative_reference(value: Any, path: str, issues: list[ValidationIssue]) -> None:
    if (
        not isinstance(value, str)
        or not value
        or "\\" in value
        or value.startswith("/")
        or re.match(r"^[A-Za-z]:", value)
    ):
        issues.append(ValidationIssue(path, "must be a repository-relative POSIX path"))


def _nonempty(value: Any, path: str, issues: list[ValidationIssue]) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(ValidationIssue(path, "must be a non-empty string"))
