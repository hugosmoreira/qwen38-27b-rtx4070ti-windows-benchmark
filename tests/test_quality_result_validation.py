import unittest

from qwen_bench.quality_result_validation import validate_quality_result


def valid_quality_result() -> dict:
    task = {
        "sequence": 1,
        "task_id": "task-one",
        "category": "arithmetic",
        "validator_type": "exact",
        "status": "completed",
        "passed": True,
        "grade": {"passed": True, "reason": "exact_match"},
        "error": None,
        "client_measurements": {
            "response_headers_ms": 1.0,
            "time_to_first_content_token_ms": 2.0,
            "total_latency_ms": 3.0,
        },
        "finish_reason": "stop",
        "content": "answer",
        "reasoning_content": None,
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        "timings": {"cache_n": 0},
        "system_fingerprint": "test",
        "validation": {"request_succeeded": True},
    }
    return {
        "schema_version": "quality-evaluation-result-1.0.0",
        "run_id": "quality-test",
        "timestamp": "2026-08-16T00:00:00Z",
        "git_commit": "a" * 40,
        "classification": "quality_test",
        "hardware_snapshot": "environment/hardware.json",
        "runtime_record": "environment/runtime.json",
        "model_manifest": "environment/model.json",
        "prompt_suite": "prompts/quality.json",
        "quality_config": "configs/quality.json",
        "python_runtime": {"implementation": "CPython"},
        "runtime": {"name": "llama.cpp"},
        "model": {"quantization": "test"},
        "configuration": {"context_size": 4096},
        "methodology": {"expected_tasks": 1},
        "server_preflight": {
            "status": "passed",
            "checks": {"health_ok": True},
            "served_model_alias": "test",
        },
        "tasks": [task],
        "summary": {
            "tasks_expected": 1,
            "tasks_attempted": 1,
            "requests_completed": 1,
            "tasks_passed": 1,
            "pass_rate_percent": 100.0,
            "category_results": {
                "arithmetic": {
                    "attempted": 1,
                    "expected": 1,
                    "passed": 1,
                    "pass_rate_percent": 100.0,
                }
            },
            "finish_reason_counts": {"stop": 1},
            "all_expected_requests_completed": True,
        },
        "outcome": {"status": "completed", "error_type": None, "error_message": None},
    }


class QualityResultValidationTests(unittest.TestCase):
    def test_valid_result_has_no_issues(self) -> None:
        self.assertEqual(validate_quality_result(valid_quality_result()), [])

    def test_pass_count_mismatch_is_reported(self) -> None:
        record = valid_quality_result()
        record["summary"]["tasks_passed"] = 0
        issues = validate_quality_result(record)
        self.assertTrue(any(issue.path.endswith("tasks_passed") for issue in issues))

    def test_failed_request_cannot_pass(self) -> None:
        record = valid_quality_result()
        record["tasks"][0]["status"] = "failed_request"
        record["tasks"][0]["validation"]["request_succeeded"] = False
        issues = validate_quality_result(record)
        self.assertTrue(any(issue.path.endswith("passed") for issue in issues))

    def test_category_rate_and_finish_counts_are_recomputed(self) -> None:
        record = valid_quality_result()
        record["summary"]["category_results"]["arithmetic"]["pass_rate_percent"] = 0.0
        record["summary"]["finish_reason_counts"] = {}
        issues = validate_quality_result(record)
        paths = {issue.path for issue in issues}
        self.assertIn("$.summary.category_results.arithmetic.pass_rate_percent", paths)
        self.assertIn("$.summary.finish_reason_counts", paths)

    def test_suite_validation_regrades_raw_content(self) -> None:
        record = valid_quality_result()
        record["tasks"][0]["content"] = "wrong"
        suite = {
            "tasks": [
                {
                    "task_id": "task-one",
                    "category": "arithmetic",
                    "validator": {"type": "exact", "expected": "answer"},
                }
            ]
        }
        issues = validate_quality_result(record, suite)
        self.assertTrue(any("independent re-grade" in issue.message for issue in issues))


if __name__ == "__main__":
    unittest.main()
