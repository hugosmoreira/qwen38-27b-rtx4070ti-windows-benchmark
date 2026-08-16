import copy
import unittest

from helpers import valid_result
from qwen_bench.mtp_comparison import _first_difference, compare_mtp_pair


def _pair() -> tuple[dict, dict]:
    off = valid_result()
    off["prompt_suite"] = "prompts/phase9.json"
    off["configuration"].update(
        {
            "mtp_enabled": False,
            "speculative_type": "none",
            "speculative_draft_n_max": 0,
            "speculative_draft_n_min": 0,
            "speculative_draft_kv_cache_k_type": "f16",
            "speculative_draft_kv_cache_v_type": "f16",
        }
    )
    on = copy.deepcopy(off)
    on["run_id"] = "test-run-mtp-on"
    on["configuration"].update(
        {
            "mtp_enabled": True,
            "speculative_type": "draft-mtp",
            "speculative_draft_n_max": 2,
        }
    )
    on["runs"][0]["server_measurements"]["timings"].update(
        {"draft_n": 10, "draft_n_accepted": 8}
    )
    on["runs"][0]["validation"]["mtp_activity_matches_configuration"] = True
    on["measured_summary"]["server_draft_acceptance_percent"] = {
        "count": 1,
        "mean": 80.0,
        "sample_standard_deviation": 0.0,
        "coefficient_of_variation_percent": 0.0,
        "minimum": 80.0,
        "maximum": 80.0,
    }
    return off, on


class MtpComparisonTests(unittest.TestCase):
    def test_pair_calculates_acceptance_and_output_equivalence(self) -> None:
        off, on = _pair()
        comparison = compare_mtp_pair(off, on)
        self.assertEqual(comparison["speculation"]["draft_tokens_total"], 10)
        self.assertEqual(comparison["speculation"]["accepted_draft_tokens_total"], 8)
        self.assertEqual(comparison["speculation"]["pooled_token_acceptance_percent"], 80.0)
        self.assertTrue(comparison["output_equivalence"]["all_paired_measured_outputs_match"])

    def test_pair_rejects_control_drift(self) -> None:
        off, on = _pair()
        on["configuration"]["context_size"] = 8192
        with self.assertRaises(ValueError):
            compare_mtp_pair(off, on)

    def test_first_difference_handles_match_character_and_length(self) -> None:
        self.assertIsNone(_first_difference("same", "same"))
        self.assertEqual(_first_difference("abcd", "abXd"), 2)
        self.assertEqual(_first_difference("abc", "abcd"), 3)


if __name__ == "__main__":
    unittest.main()
