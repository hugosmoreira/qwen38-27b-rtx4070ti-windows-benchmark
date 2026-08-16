import unittest

from qwen_bench.quality_runner import _summarize


class QualityRunnerTests(unittest.TestCase):
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
