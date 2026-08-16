import copy
import unittest

from helpers import valid_result
from qwen_bench.result_validation import validate_result


class ResultValidationTests(unittest.TestCase):
    def test_valid_result_has_no_issues(self) -> None:
        self.assertEqual(validate_result(valid_result()), [])

    def test_missing_required_property_is_reported(self) -> None:
        record = valid_result()
        del record["model_manifest"]
        issues = validate_result(record)
        self.assertTrue(any(issue.path == "$.model_manifest" for issue in issues))

    def test_completed_status_must_match_validation(self) -> None:
        record = valid_result()
        record["runs"][0]["validation"]["request_succeeded"] = False
        issues = validate_result(record)
        self.assertTrue(any(issue.path == "$.runs[0].status" for issue in issues))

    def test_summary_count_must_match_measured_runs(self) -> None:
        record = copy.deepcopy(valid_result())
        record["measured_summary"]["completed_repetitions"] = 0
        issues = validate_result(record)
        self.assertTrue(any(issue.path.endswith("completed_repetitions") for issue in issues))

    def test_all_expected_requires_declared_warmups(self) -> None:
        record = valid_result()
        record["methodology"]["warmup_runs"] = 1
        issues = validate_result(record)
        self.assertTrue(any(issue.path.endswith("all_expected_runs_completed") for issue in issues))


if __name__ == "__main__":
    unittest.main()
