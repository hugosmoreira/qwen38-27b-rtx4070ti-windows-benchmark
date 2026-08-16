import unittest

from qwen_bench.quality_grading import grade_response


class QualityGradingTests(unittest.TestCase):
    def test_exact_ignores_outer_whitespace_but_is_case_sensitive(self) -> None:
        validator = {"type": "exact", "expected": "Alpha"}
        self.assertTrue(grade_response(validator, "\n Alpha \t").passed)
        self.assertFalse(grade_response(validator, "alpha").passed)

    def test_json_object_key_order_is_ignored(self) -> None:
        validator = {"type": "json_exact", "expected": {"a": 1, "b": [True, 2]}}
        self.assertTrue(grade_response(validator, '{"b":[true,2],"a":1}').passed)

    def test_json_array_order_and_boolean_type_are_strict(self) -> None:
        array_validator = {"type": "json_exact", "expected": [1, 2]}
        bool_validator = {"type": "json_exact", "expected": {"value": True}}
        self.assertFalse(grade_response(array_validator, "[2,1]").passed)
        self.assertFalse(grade_response(bool_validator, '{"value":1}').passed)

    def test_json_rejects_markdown_and_duplicate_keys(self) -> None:
        validator = {"type": "json_exact", "expected": {"a": 2}}
        self.assertFalse(grade_response(validator, '```json\n{"a":2}\n```').passed)
        result = grade_response(validator, '{"a":1,"a":2}')
        self.assertFalse(result.passed)
        self.assertEqual(result.reason, "invalid_or_duplicate_key_json")

    def test_json_rejects_nonstandard_numeric_constants(self) -> None:
        validator = {"type": "json_exact", "expected": {"value": 1}}
        self.assertFalse(grade_response(validator, '{"value": NaN}').passed)
        self.assertFalse(grade_response(validator, '{"value": Infinity}').passed)


if __name__ == "__main__":
    unittest.main()
