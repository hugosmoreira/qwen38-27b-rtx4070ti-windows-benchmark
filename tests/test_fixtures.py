import hashlib
import unittest

from qwen_bench.fixtures import build_user_content, synthetic_context_metadata


class SyntheticContextFixtureTests(unittest.TestCase):
    def test_plain_workload_is_unchanged(self) -> None:
        self.assertEqual(build_user_content({"user": "plain input"}), "plain input")

    def test_numbered_records_are_deterministic_and_one_based(self) -> None:
        workload = {
            "user": "Final instruction.",
            "synthetic_context": {
                "generator": "numbered-records-v1",
                "record_count": 2,
            },
        }
        content = build_user_content(workload)
        self.assertTrue(content.startswith("Record 00001:"))
        self.assertIn("\nRecord 00002:", content)
        self.assertTrue(content.endswith("\n\nFinal instruction."))
        self.assertEqual(content.count("Record "), 2)

        metadata = synthetic_context_metadata(workload)
        encoded = content.encode("utf-8")
        self.assertEqual(metadata["synthetic_context_record_count"], 2)
        self.assertEqual(metadata["synthetic_context_utf8_bytes"], len(encoded))
        self.assertEqual(
            metadata["synthetic_context_user_sha256"],
            hashlib.sha256(encoded).hexdigest(),
        )

    def test_unknown_generator_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_user_content(
                {
                    "user": "instruction",
                    "synthetic_context": {"generator": "unknown", "record_count": 1},
                }
                )

    def test_needle_fixture_inserts_one_exact_record_deterministically(self) -> None:
        workload = {
            "user": "Return only the value for KEY-9.",
            "synthetic_context": {
                "generator": "needle-records-v1",
                "record_count": 5,
                "needle_record": 3,
                "needle_key": "KEY-9",
                "needle_value": "VALUE-7",
            },
        }
        content = build_user_content(workload)
        self.assertEqual(content.count("retrieval key KEY-9 has value VALUE-7"), 1)
        self.assertIn("Record 00003: retrieval key KEY-9 has value VALUE-7.", content)
        self.assertEqual(synthetic_context_metadata(workload), synthetic_context_metadata(workload))


if __name__ == "__main__":
    unittest.main()
