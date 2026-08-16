import unittest

from qwen_bench.runner import _draft_acceptance_percent, _mtp_activity_matches


class MtpTimingTests(unittest.TestCase):
    def test_enabled_mtp_requires_consistent_positive_draft_counters(self) -> None:
        timings = {"draft_n": 52, "draft_n_accepted": 36}
        self.assertTrue(_mtp_activity_matches(timings, True))
        self.assertAlmostEqual(_draft_acceptance_percent(timings), 69.2307692308)
        self.assertFalse(_mtp_activity_matches({"draft_n": 0, "draft_n_accepted": 0}, True))
        self.assertFalse(_mtp_activity_matches({"draft_n": 3, "draft_n_accepted": 4}, True))

    def test_disabled_mtp_rejects_draft_activity(self) -> None:
        self.assertTrue(_mtp_activity_matches({"cache_n": 0}, False))
        self.assertTrue(_mtp_activity_matches({"draft_n": 0, "draft_n_accepted": 0}, False))
        self.assertFalse(_mtp_activity_matches({"draft_n": 2, "draft_n_accepted": 1}, False))
        self.assertIsNone(_draft_acceptance_percent({"cache_n": 0}))


if __name__ == "__main__":
    unittest.main()
