import unittest

from qwen_bench.quality_runner import _request_completed, _summarize


class QualityRunnerTests(unittest.TestCase):
    def test_empty_answer_does_not_turn_a_completed_request_into_transport_failure(self) -> None:
        validation = {
            "request_succeeded": True,
            "content_observed": False,
            "usage_observed": True,
            "timings_observed": True,
            "prompt_cache_disabled": True,
            "reasoning_empty": True,
        }
        self.assertTrue(_request_completed(validation))

    def test_summary_uses_declared_denominators_and_categories(self) -> None:
        declared = [
            {"task_id": "a", "category": "arithmetic"},
            {"task_id": "b", "category": "logic"},
        ]
        results = [
            {"category": "arithmetic", "passed": True, "status": "completed", "finish_reason": "stop"},
            {"category": "logic", "passed": False, "status": "completed", "finish_reason": "length"},
        ]
        summary = _summarize(results, declared)
        self.assertEqual(summary["tasks_passed"], 1)
        self.assertEqual(summary["pass_rate_percent"], 50.0)
        self.assertEqual(summary["category_results"]["logic"]["passed"], 0)
        self.assertEqual(summary["finish_reason_counts"], {"length": 1, "stop": 1})
        self.assertTrue(summary["all_expected_requests_completed"])


if __name__ == "__main__":
    unittest.main()
