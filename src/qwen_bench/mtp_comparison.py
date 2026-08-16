"""Derived comparison helpers for the isolated Phase 9 MTP experiment."""

from __future__ import annotations

import copy
import hashlib
from typing import Any

from qwen_bench.result_validation import require_valid_result


_MTP_IDENTITY_FIELDS = {
    "mtp_enabled",
    "speculative_type",
    "speculative_draft_n_max",
}


def compare_mtp_results(
    prose_off: dict[str, Any],
    prose_on: dict[str, Any],
    code_off: dict[str, Any],
    code_on: dict[str, Any],
) -> dict[str, Any]:
    pairs = {
        "prose": compare_mtp_pair(prose_off, prose_on),
        "code": compare_mtp_pair(code_off, code_on),
    }
    commits = {
        record["git_commit"] for record in (prose_off, prose_on, code_off, code_on)
    }
    if len(commits) != 1:
        raise ValueError("All Phase 9 records must share one frozen Git commit.")
    return {
        "schema_version": "phase9-mtp-comparison-1.0",
        "protocol_commit": next(iter(commits)),
        "pairs": pairs,
        "all_workloads_output_equivalent": all(
            pair["output_equivalence"]["all_paired_measured_outputs_match"]
            for pair in pairs.values()
        ),
        "interpretation": {
            "speed_claims_are_workload_specific": True,
            "pooled_speed_claim_prohibited": True,
            "default_enablement_supported": all(
                pair["output_equivalence"]["all_paired_measured_outputs_match"]
                for pair in pairs.values()
            ),
        },
    }


def compare_mtp_pair(off: dict[str, Any], on: dict[str, Any]) -> dict[str, Any]:
    require_valid_result(off)
    require_valid_result(on)
    _require_controlled_pair(off, on)
    off_runs = _measured_runs(off)
    on_runs = _measured_runs(on)
    if len(off_runs) != len(on_runs):
        raise ValueError("MTP pair has unequal measured repetition counts.")

    off_hashes = [_response_hash(run) for run in off_runs]
    on_hashes = [_response_hash(run) for run in on_runs]
    paired_matches = [left == right for left, right in zip(off_hashes, on_hashes, strict=True)]
    off_first = str(off_runs[0]["response"]["content"])
    on_first = str(on_runs[0]["response"]["content"])

    draft_total = sum(int(run["server_measurements"]["timings"]["draft_n"]) for run in on_runs)
    accepted_total = sum(
        int(run["server_measurements"]["timings"]["draft_n_accepted"]) for run in on_runs
    )
    if draft_total <= 0 or not 0 <= accepted_total <= draft_total:
        raise ValueError("MTP-on draft counters are not internally consistent.")

    return {
        "prompt_suite": off["prompt_suite"],
        "mtp_off_run_id": off["run_id"],
        "mtp_on_run_id": on["run_id"],
        "measured_repetitions_per_state": len(off_runs),
        "metrics": {
            "generation_tokens_per_second": _metric_change(
                off, on, "server_generation_tokens_per_second"
            ),
            "total_latency_ms": _metric_change(off, on, "total_latency_ms"),
            "time_to_first_content_token_ms": _metric_change(
                off, on, "time_to_first_content_token_ms"
            ),
            "peak_vram_used_mib": _metric_change(off, on, "peak_vram_used_mib"),
            "minimum_vram_free_mib": _metric_change(off, on, "minimum_vram_free_mib"),
            "peak_process_private_memory_bytes": _metric_change(
                off, on, "peak_process_private_memory_bytes"
            ),
        },
        "speculation": {
            "draft_tokens_total": draft_total,
            "accepted_draft_tokens_total": accepted_total,
            "pooled_token_acceptance_percent": accepted_total / draft_total * 100.0,
            "mean_per_run_acceptance_percent": on["measured_summary"][
                "server_draft_acceptance_percent"
            ]["mean"],
        },
        "output_equivalence": {
            "mtp_off_unique_measured_hashes": sorted(set(off_hashes)),
            "mtp_on_unique_measured_hashes": sorted(set(on_hashes)),
            "paired_measured_outputs_matching": sum(paired_matches),
            "paired_measured_outputs_total": len(paired_matches),
            "all_paired_measured_outputs_match": all(paired_matches),
            "first_different_character_index": _first_difference(off_first, on_first),
            "mtp_off_first_response_utf8_sha256": off_hashes[0],
            "mtp_on_first_response_utf8_sha256": on_hashes[0],
        },
    }


def _require_controlled_pair(off: dict[str, Any], on: dict[str, Any]) -> None:
    for key in ("model", "runtime", "methodology", "prompt_suite"):
        if off.get(key) != on.get(key):
            raise ValueError(f"MTP pair differs in controlled field '{key}'.")
    off_configuration = copy.deepcopy(off.get("configuration"))
    on_configuration = copy.deepcopy(on.get("configuration"))
    if not isinstance(off_configuration, dict) or not isinstance(on_configuration, dict):
        raise ValueError("MTP pair configurations must be objects.")
    if (
        off_configuration.get("mtp_enabled") is not False
        or off_configuration.get("speculative_type") != "none"
        or off_configuration.get("speculative_draft_n_max") != 0
    ):
        raise ValueError("The MTP-off record does not declare the frozen off controls.")
    if (
        on_configuration.get("mtp_enabled") is not True
        or on_configuration.get("speculative_type") != "draft-mtp"
        or on_configuration.get("speculative_draft_n_max") != 2
    ):
        raise ValueError("The MTP-on record does not declare the frozen on controls.")
    for configuration in (off_configuration, on_configuration):
        for key in _MTP_IDENTITY_FIELDS:
            configuration.pop(key, None)
    if off_configuration != on_configuration:
        raise ValueError("MTP pair differs outside the declared MTP identity fields.")

    for run in _measured_runs(off):
        timings = run["server_measurements"]["timings"]
        if timings.get("draft_n") not in {None, 0} or timings.get("draft_n_accepted") not in {
            None,
            0,
        }:
            raise ValueError("The MTP-off record contains draft activity.")
    for run in _measured_runs(on):
        timings = run["server_measurements"]["timings"]
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
            raise ValueError("The MTP-on record lacks valid draft activity.")


def _metric_change(off: dict[str, Any], on: dict[str, Any], key: str) -> dict[str, float]:
    off_mean = float(off["measured_summary"][key]["mean"])
    on_mean = float(on["measured_summary"][key]["mean"])
    return {
        "mtp_off_mean": off_mean,
        "mtp_on_mean": on_mean,
        "absolute_change": on_mean - off_mean,
        "relative_change_percent_vs_off": (on_mean - off_mean) / off_mean * 100.0,
    }


def _measured_runs(record: dict[str, Any]) -> list[dict[str, Any]]:
    return [run for run in record["runs"] if not run["warmup"] and run["status"] == "completed"]


def _response_hash(run: dict[str, Any]) -> str:
    content = str(run["response"]["content"])
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _first_difference(left: str, right: str) -> int | None:
    for index, (left_character, right_character) in enumerate(zip(left, right, strict=False)):
        if left_character != right_character:
            return index
    if len(left) != len(right):
        return min(len(left), len(right))
    return None
