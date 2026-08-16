import copy
import tempfile
import unittest
from pathlib import Path

from qwen_bench.config import (
    ConfigurationError,
    load_benchmark_config,
    load_json_object,
    resolve_repository_path,
)


class ConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository_root = Path(__file__).resolve().parents[1]

    def test_phase5_configuration_loads(self) -> None:
        config = load_benchmark_config(self.repository_root, Path("configs/phase5-iq2-smoke.json"))
        self.assertEqual(config.model_alias, "Qwen3.8-27B-UD-IQ2_XXS")
        self.assertEqual(config.prompt["settings"]["max_tokens"], 64)

    def test_phase6_configurations_load_and_share_the_phase4_workload(self) -> None:
        iq2 = load_benchmark_config(self.repository_root, Path("configs/phase6-iq2-comparison.json"))
        q2 = load_benchmark_config(self.repository_root, Path("configs/phase6-q2-comparison.json"))
        self.assertEqual(iq2.prompt_path, q2.prompt_path)
        self.assertEqual(iq2.prompt["suite_id"], "phase4-iq2-baseline-v1")
        self.assertEqual(iq2.data["run"]["warmup_runs"], 1)
        self.assertEqual(q2.data["run"]["measured_repetitions"], 3)

    def test_phase6_configs_differ_only_by_model_identity(self) -> None:
        iq2 = load_benchmark_config(self.repository_root, Path("configs/phase6-iq2-comparison.json"))
        q2 = load_benchmark_config(self.repository_root, Path("configs/phase6-q2-comparison.json"))
        iq2_data = copy.deepcopy(iq2.data)
        q2_data = copy.deepcopy(q2.data)
        for data in (iq2_data, q2_data):
            data["run"].pop("classification")
            data["run"].pop("result_prefix")
            data["server"].pop("model_alias")
            data["inputs"].pop("model_manifest")
            data["model"].pop("quantization")
        self.assertEqual(iq2_data, q2_data)

    def test_repository_path_cannot_escape(self) -> None:
        with self.assertRaises(ConfigurationError):
            resolve_repository_path(self.repository_root, "../outside.json")

    def test_duplicate_json_keys_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"same": 1, "same": 2}', encoding="utf-8")
            with self.assertRaises(ConfigurationError):
                load_json_object(path)


if __name__ == "__main__":
    unittest.main()
