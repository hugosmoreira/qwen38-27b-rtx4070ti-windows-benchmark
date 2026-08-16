"""Command-line interface for running and validating benchmark records."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from qwen_bench import __version__
from qwen_bench.config import (
    ConfigurationError,
    load_benchmark_config,
    load_json_object,
    resolve_repository_path,
)
from qwen_bench.quality_config import load_quality_config
from qwen_bench.quality_comparison import compare_quality_results
from qwen_bench.quality_result_validation import (
    require_valid_quality_result,
    validate_quality_result,
)
from qwen_bench.quality_runner import execute_quality_evaluation
from qwen_bench.release_audit import audit_repository
from qwen_bench.mtp_comparison import compare_mtp_results
from qwen_bench.result_validation import require_valid_result, validate_result
from qwen_bench.runner import execute_benchmark
from qwen_bench.storage import write_result_exclusive


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qwen-bench",
        description="Run and validate the local Qwen3.8 Windows benchmark harness.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="run one configured benchmark experiment")
    run.add_argument(
        "--config",
        default="configs/phase5-iq2-smoke.json",
        help="repository-relative benchmark configuration JSON",
    )
    run.add_argument("--server-pid", required=True, type=int, help="PID of the active llama-server process")
    run.add_argument("--repository-root", type=Path, default=_default_repository_root())

    validate = subparsers.add_parser("validate", help="validate an existing result JSON")
    validate.add_argument("result", type=Path)

    quality_run = subparsers.add_parser("quality-run", help="run one objective pass@1 quality evaluation")
    quality_run.add_argument("--config", required=True, help="repository-relative quality configuration JSON")
    quality_run.add_argument("--server-pid", required=True, type=int)
    quality_run.add_argument("--repository-root", type=Path, default=_default_repository_root())

    quality_validate = subparsers.add_parser(
        "quality-validate", help="validate an existing objective quality result"
    )
    quality_validate.add_argument("result", type=Path)
    quality_validate.add_argument("--repository-root", type=Path, default=_default_repository_root())

    quality_compare = subparsers.add_parser(
        "quality-compare", help="derive a paired Q2-versus-IQ2 quality comparison"
    )
    quality_compare.add_argument("q2_result", type=Path)
    quality_compare.add_argument("iq2_result", type=Path)
    quality_compare.add_argument("--repository-root", type=Path, default=_default_repository_root())

    mtp_compare = subparsers.add_parser(
        "mtp-compare", help="derive the controlled Phase 9 MTP comparison"
    )
    mtp_compare.add_argument("prose_off", type=Path)
    mtp_compare.add_argument("prose_on", type=Path)
    mtp_compare.add_argument("code_off", type=Path)
    mtp_compare.add_argument("code_on", type=Path)

    release_audit = subparsers.add_parser(
        "release-audit", help="audit the local public release candidate"
    )
    release_audit.add_argument("--repository-root", type=Path, default=_default_repository_root())
    release_audit.add_argument(
        "--strict",
        action="store_true",
        help="also require owner-selected license, citation identity, and publication URLs",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "validate":
            return _validate_command(arguments.result)
        if arguments.command == "quality-validate":
            return _quality_validate_command(arguments.repository_root, arguments.result)
        if arguments.command == "quality-compare":
            return _quality_compare_command(
                arguments.repository_root, arguments.q2_result, arguments.iq2_result
            )
        if arguments.command == "mtp-compare":
            return _mtp_compare_command(
                arguments.prose_off,
                arguments.prose_on,
                arguments.code_off,
                arguments.code_on,
            )
        if arguments.command == "release-audit":
            return _release_audit_command(arguments.repository_root, arguments.strict)
        if arguments.command == "quality-run":
            return _quality_run_command(
                arguments.repository_root,
                Path(arguments.config),
                arguments.server_pid,
            )
        return _run_command(arguments.repository_root, Path(arguments.config), arguments.server_pid)
    except (ConfigurationError, ValueError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


def _run_command(repository_root: Path, config_path: Path, server_pid: int) -> int:
    config = load_benchmark_config(repository_root, config_path)
    record = execute_benchmark(config, server_pid)
    require_valid_result(record)
    output_path = write_result_exclusive(config.output_directory, str(record["run_id"]), record)
    summary = record["measured_summary"]
    terminal_record = {
        "result_path": str(output_path),
        "run_id": record["run_id"],
        "outcome": record["outcome"]["status"],
        "all_expected_runs_completed": summary["all_expected_runs_completed"],
        "completed_repetitions": summary["completed_repetitions"],
        "generation_tokens_per_second": summary["server_generation_tokens_per_second"],
        "time_to_first_content_token_ms": summary["time_to_first_content_token_ms"],
    }
    print(json.dumps(terminal_record, indent=2))
    return 0 if record["outcome"]["status"] == "completed" else 1


def _validate_command(result_path: Path) -> int:
    record = load_json_object(result_path.resolve())
    issues = validate_result(record)
    if issues:
        print(json.dumps({"valid": False, "issues": [str(issue) for issue in issues]}, indent=2))
        return 1
    print(json.dumps({"valid": True, "result_path": str(result_path.resolve())}, indent=2))
    return 0


def _quality_run_command(repository_root: Path, config_path: Path, server_pid: int) -> int:
    config = load_quality_config(repository_root, config_path)
    record = execute_quality_evaluation(config, server_pid)
    require_valid_quality_result(record, config.suite)
    output_path = write_result_exclusive(config.output_directory, str(record["run_id"]), record)
    summary = record["summary"]
    print(
        json.dumps(
            {
                "result_path": str(output_path),
                "run_id": record["run_id"],
                "outcome": record["outcome"]["status"],
                "tasks_attempted": summary["tasks_attempted"],
                "tasks_passed": summary["tasks_passed"],
                "pass_rate_percent": summary["pass_rate_percent"],
                "all_expected_requests_completed": summary["all_expected_requests_completed"],
            },
            indent=2,
        )
    )
    return 0 if record["outcome"]["status"] == "completed" else 1


def _quality_validate_command(repository_root: Path, result_path: Path) -> int:
    record = load_json_object(result_path.resolve())
    suite = _quality_suite_for_result(repository_root, record)
    issues = validate_quality_result(record, suite)
    if issues:
        print(json.dumps({"valid": False, "issues": [str(issue) for issue in issues]}, indent=2))
        return 1
    print(json.dumps({"valid": True, "result_path": str(result_path.resolve())}, indent=2))
    return 0


def _quality_compare_command(repository_root: Path, q2_path: Path, iq2_path: Path) -> int:
    q2 = load_json_object(q2_path.resolve())
    iq2 = load_json_object(iq2_path.resolve())
    q2_suite = _quality_suite_for_result(repository_root, q2)
    iq2_suite = _quality_suite_for_result(repository_root, iq2)
    require_valid_quality_result(q2, q2_suite)
    require_valid_quality_result(iq2, iq2_suite)
    print(json.dumps(compare_quality_results(q2, iq2), indent=2))
    return 0


def _quality_suite_for_result(repository_root: Path, record: dict) -> dict:
    root = repository_root.resolve()
    suite_path = resolve_repository_path(root, str(record.get("prompt_suite", "")), must_exist=True)
    return load_json_object(suite_path)


def _mtp_compare_command(
    prose_off_path: Path,
    prose_on_path: Path,
    code_off_path: Path,
    code_on_path: Path,
) -> int:
    records = [
        load_json_object(path.resolve())
        for path in (prose_off_path, prose_on_path, code_off_path, code_on_path)
    ]
    print(json.dumps(compare_mtp_results(*records), indent=2))
    return 0


def _release_audit_command(repository_root: Path, strict: bool) -> int:
    result = audit_repository(repository_root, strict=strict)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 1


def _default_repository_root() -> Path:
    return Path(__file__).resolve().parents[2]
