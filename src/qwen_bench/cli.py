"""Command-line interface for running and validating benchmark records."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from qwen_bench import __version__
from qwen_bench.config import ConfigurationError, load_benchmark_config, load_json_object
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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "validate":
            return _validate_command(arguments.result)
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


def _default_repository_root() -> Path:
    return Path(__file__).resolve().parents[2]
