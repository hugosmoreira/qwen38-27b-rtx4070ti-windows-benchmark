import math
import unittest

from qwen_bench.statistics import descriptive_statistics


class DescriptiveStatisticsTests(unittest.TestCase):
    def test_sample_statistics_and_missing_values(self) -> None:
        result = descriptive_statistics([1, 2, None, 3])
        self.assertEqual(result["count"], 3)
        self.assertEqual(result["mean"], 2.0)
        self.assertEqual(result["sample_standard_deviation"], 1.0)
        self.assertEqual(result["coefficient_of_variation_percent"], 50.0)

    def test_single_value_has_zero_sample_sd(self) -> None:
        result = descriptive_statistics([42])
        self.assertEqual(result["sample_standard_deviation"], 0.0)
        self.assertEqual(result["coefficient_of_variation_percent"], 0.0)

    def test_zero_mean_has_undefined_cv(self) -> None:
        result = descriptive_statistics([-1, 1])
        self.assertTrue(math.isclose(result["sample_standard_deviation"], 1.414, abs_tol=0.001))
        self.assertIsNone(result["coefficient_of_variation_percent"])

    def test_empty_values_return_none(self) -> None:
        self.assertIsNone(descriptive_statistics([None, None]))


if __name__ == "__main__":
    unittest.main()
