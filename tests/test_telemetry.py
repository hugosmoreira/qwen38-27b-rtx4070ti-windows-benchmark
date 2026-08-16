import time
import unittest

from qwen_bench.telemetry import TelemetryCollector, parse_nvidia_smi_row, summarize_telemetry


class _FakeProcessProbe:
    def __init__(self, process_id: int) -> None:
        self.process_id = process_id

    def sample(self, monotonic_ns: int):
        return True, {
            "working_set_bytes": 100,
            "private_memory_bytes": 200,
            "cpu_total_seconds": 1.0,
            "cpu_percent_of_machine": 2.0,
        }

    def close(self) -> None:
        return


def _fake_gpu():
    return {
        "vram_total_mib": 12000,
        "vram_used_mib": 9000,
        "vram_free_mib": 3000,
        "utilization_percent": 98,
        "temperature_c": 70,
        "power_draw_w": 250.5,
    }


class TelemetryTests(unittest.TestCase):
    def test_parses_nvidia_csv(self) -> None:
        result = parse_nvidia_smi_row("12282, 8987, 3008, 98, 71, 264.10")
        self.assertEqual(result["vram_used_mib"], 8987)
        self.assertEqual(result["power_draw_w"], 264.10)

    def test_summarizes_observed_cadence_and_peaks(self) -> None:
        samples = [
            {
                "monotonic_elapsed_milliseconds": 0.0,
                "gpu": {"vram_used_mib": 10, "vram_free_mib": 90, "utilization_percent": 5,
                        "temperature_c": 40, "power_draw_w": 50},
                "process": {"working_set_bytes": 100, "private_memory_bytes": 200,
                            "cpu_percent_of_machine": None},
            },
            {
                "monotonic_elapsed_milliseconds": 250.5,
                "gpu": {"vram_used_mib": 20, "vram_free_mib": 80, "utilization_percent": 95,
                        "temperature_c": 60, "power_draw_w": 200},
                "process": {"working_set_bytes": 110, "private_memory_bytes": 210,
                            "cpu_percent_of_machine": 3.5},
            },
            {
                "monotonic_elapsed_milliseconds": 501.5,
                "gpu": {"vram_used_mib": 18, "vram_free_mib": 82, "utilization_percent": 90,
                        "temperature_c": 58, "power_draw_w": 190},
                "process": {"working_set_bytes": 105, "private_memory_bytes": 205,
                            "cpu_percent_of_machine": 3.0},
            },
        ]
        summary = summarize_telemetry(samples, 250)
        self.assertEqual(summary["sample_count"], 3)
        self.assertEqual(summary["observed_mean_interval_milliseconds"], 250.75)
        self.assertEqual(summary["peak_vram_used_mib"], 20.0)
        self.assertEqual(summary["minimum_vram_free_mib"], 80.0)

    def test_collector_uses_fixed_target_cadence(self) -> None:
        collector = TelemetryCollector(
            123,
            interval_milliseconds=100,
            gpu_query=_fake_gpu,
            process_probe_factory=_FakeProcessProbe,
        )
        collector.start()
        self.assertTrue(collector.wait_until_ready())
        time.sleep(0.23)
        collector.stop()
        samples = collector.samples
        self.assertGreaterEqual(len(samples), 3)
        summary = summarize_telemetry(samples, 100)
        self.assertLess(summary["observed_mean_interval_milliseconds"], 130)
        self.assertEqual(collector.errors, [])


if __name__ == "__main__":
    unittest.main()
