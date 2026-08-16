import unittest

from qwen_bench.quality_comparison import compare_quality_results, exact_mcnemar_two_sided


def record(passes: list[bool]) -> dict:
    return {
        "prompt_suite": "prompts/quality.json",
        "tasks": [
            {
                "task_id": f"task-{index}",
                "category": "test",
                "validator_type": "exact",
                "passed": passed,
            }
            for index, passed in enumerate(passes, start=1)
        ]
    }


class QualityComparisonTests(unittest.TestCase):
    def test_paired_counts_and_difference(self) -> None:
        comparison = compare_quality_results(
            record([True, True, False, False]),
            record([True, False, True, False]),
        )
        self.assertEqual(
            comparison["paired_contingency"],
            {"both_pass": 1, "q2_only": 1, "iq2_only": 1, "neither_pass": 1},
        )
        self.assertEqual(comparison["q2_minus_iq2_passes"], 0)
        self.assertEqual(comparison["two_sided_exact_mcnemar_p"], 1.0)

    def test_exact_mcnemar_known_values(self) -> None:
        self.assertEqual(exact_mcnemar_two_sided(0, 0), 1.0)
        self.assertEqual(exact_mcnemar_two_sided(4, 0), 0.125)
        self.assertEqual(exact_mcnemar_two_sided(5, 1), 0.21875)

    def test_task_order_must_match(self) -> None:
        left = record([True, False])
        right = record([True, False])
        right["tasks"].reverse()
        with self.assertRaises(ValueError):
            compare_quality_results(left, right)

    def test_task_metadata_must_match(self) -> None:
        left = record([True])
        right = record([True])
        right["tasks"][0]["category"] = "different"
        with self.assertRaises(ValueError):
            compare_quality_results(left, right)


if __name__ == "__main__":
    unittest.main()
