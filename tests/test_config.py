import copy
import json
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

    def test_phase7_context_ladder_loads_with_scaled_public_fixtures(self) -> None:
        expected = {
            4096: ("configs/phase7-iq2-context-4k.json", 131),
            8192: ("configs/phase7-iq2-context-8k.json", 264),
            16384: ("configs/phase7-iq2-context-16k.json", 531),
        }
        loaded = []
        for context_size, (path, record_count) in expected.items():
            config = load_benchmark_config(self.repository_root, Path(path))
            loaded.append(config)
            self.assertEqual(config.data["configuration"]["context_size"], context_size)
            self.assertEqual(config.data["model"]["quantization"], "UD-IQ2_XXS")
            self.assertEqual(
                config.prompt["workload"]["synthetic_context"]["record_count"],
                record_count,
            )
            acceptance = config.prompt["workload"]["acceptance"]
            self.assertLessEqual(
                acceptance["maximum_prompt_tokens"] + config.prompt["settings"]["max_tokens"],
                context_size,
            )

        settings = [config.prompt["settings"] for config in loaded]
        self.assertTrue(all(value == settings[0] for value in settings[1:]))
        instructions = [config.prompt["workload"]["user"] for config in loaded]
        self.assertEqual(len(set(instructions)), 1)

    def test_phase7_rejects_prompt_budget_that_exceeds_context(self) -> None:
        config_path = Path("configs/phase7-iq2-context-4k.json")
        source = load_json_object(self.repository_root / config_path)
        prompt_path = self.repository_root / source["inputs"]["prompt_suite"]
        prompt = load_json_object(prompt_path)
        prompt["workload"]["acceptance"]["maximum_prompt_tokens"] = 4000
        with tempfile.TemporaryDirectory(dir=self.repository_root) as directory:
            directory_path = Path(directory)
            temporary_prompt = directory_path / "prompt.json"
            temporary_config = directory_path / "config.json"
            temporary_prompt.write_text(json.dumps(prompt), encoding="utf-8")
            source["inputs"]["prompt_suite"] = temporary_prompt.relative_to(self.repository_root).as_posix()
            source["inputs"]["runtime_record"] = "environment/phase7-context-protocol-2026-08-15.json"
            temporary_config.write_text(json.dumps(source), encoding="utf-8")
            with self.assertRaises(ConfigurationError):
                load_benchmark_config(self.repository_root, temporary_config.relative_to(self.repository_root))

    def test_phase9_mtp_pairs_differ_only_by_declared_mtp_identity(self) -> None:
        for workload in ("prose", "code"):
            off = load_benchmark_config(
                self.repository_root, Path(f"configs/phase9-mtp-off-{workload}.json")
            )
            on = load_benchmark_config(
                self.repository_root, Path(f"configs/phase9-mtp-on-{workload}.json")
            )
            self.assertEqual(off.prompt_path, on.prompt_path)
            self.assertEqual(off.expected_speculative_types, "none")
            self.assertEqual(on.expected_speculative_types, "draft-mtp")
            off_data = copy.deepcopy(off.data)
            on_data = copy.deepcopy(on.data)
            for data in (off_data, on_data):
                data["run"].pop("classification")
                data["run"].pop("result_prefix")
                for key in (
                    "mtp_enabled",
                    "speculative_type",
                    "speculative_draft_n_max",
                ):
                    data["configuration"].pop(key)
            self.assertEqual(off_data, on_data)

    def test_phase9_workloads_share_identical_sampling_settings(self) -> None:
        prose = load_benchmark_config(
            self.repository_root, Path("configs/phase9-mtp-off-prose.json")
        )
        code = load_benchmark_config(
            self.repository_root, Path("configs/phase9-mtp-off-code.json")
        )
        self.assertEqual(prose.prompt["settings"], code.prompt["settings"])
        self.assertEqual(prose.prompt["settings"]["temperature"], 0.0)
        self.assertEqual(prose.data["run"]["measured_repetitions"], 5)

    def test_phase9_rejects_mtp_flag_and_type_disagreement(self) -> None:
        source = load_json_object(self.repository_root / "configs/phase9-mtp-on-prose.json")
        source["configuration"]["speculative_type"] = "none"
        with tempfile.TemporaryDirectory(dir=self.repository_root) as directory:
            temporary_config = Path(directory) / "config.json"
            temporary_config.write_text(json.dumps(source), encoding="utf-8")
            with self.assertRaises(ConfigurationError):
                load_benchmark_config(
                    self.repository_root, temporary_config.relative_to(self.repository_root)
                )

    def test_phase13_iq4_baseline_loads_with_selected_frontier_controls(self) -> None:
        config = load_benchmark_config(
            self.repository_root, Path("configs/phase13-iq4-xs-4k-q8.json")
        )
        self.assertEqual(config.model_alias, "Qwen3.8-27B-IQ4_XS")
        self.assertEqual(config.data["model"]["quantization"], "IQ4_XS")
        self.assertEqual(config.data["configuration"]["gpu_layers"], 45)
        self.assertEqual(config.data["configuration"]["kv_cache_k_type"], "q8_0")
        self.assertEqual(config.data["configuration"]["kv_cache_v_type"], "q8_0")
        self.assertEqual(config.expected_speculative_types, "none")
        self.assertEqual(config.prompt["suite_id"], "phase4-iq2-baseline-v1")
        self.assertEqual(config.data["run"]["warmup_runs"], 1)
        self.assertEqual(config.data["run"]["measured_repetitions"], 3)

    def test_phase13_kv_pair_differs_only_by_run_and_cache_identity(self) -> None:
        q8 = load_benchmark_config(
            self.repository_root, Path("configs/phase13-iq4-xs-4k-q8.json")
        )
        q4 = load_benchmark_config(
            self.repository_root, Path("configs/phase13-iq4-xs-4k-q4-kv.json")
        )
        self.assertEqual(q8.prompt_path, q4.prompt_path)
        self.assertEqual(q8.data["configuration"]["kv_cache_k_type"], "q8_0")
        self.assertEqual(q4.data["configuration"]["kv_cache_k_type"], "q4_0")
        q8_data = copy.deepcopy(q8.data)
        q4_data = copy.deepcopy(q4.data)
        for data in (q8_data, q4_data):
            data["run"].pop("classification")
            data["run"].pop("result_prefix")
            data["configuration"].pop("kv_cache_k_type")
            data["configuration"].pop("kv_cache_v_type")
        self.assertEqual(q8_data, q4_data)

    def test_phase13_active_context_ladder_uses_fixed_placement(self) -> None:
        expected = {
            4096: ("configs/phase13-iq4-xs-context-4k-q4.json", 131),
            16384: ("configs/phase13-iq4-xs-context-16k-q4.json", 531),
            32768: ("configs/phase13-iq4-xs-context-32k-q4.json", 1064),
            65536: ("configs/phase13-iq4-xs-context-64k-q4.json", 2497),
        }
        for context_size, (path, record_count) in expected.items():
            config = load_benchmark_config(self.repository_root, Path(path))
            self.assertEqual(config.data["configuration"]["context_size"], context_size)
            self.assertEqual(config.data["configuration"]["gpu_layers"], 40)
            self.assertEqual(config.data["configuration"]["kv_cache_k_type"], "q4_0")
            self.assertEqual(config.data["configuration"]["kv_cache_v_type"], "q4_0")
            self.assertEqual(
                config.prompt["workload"]["synthetic_context"]["record_count"],
                record_count,
            )
            acceptance = config.prompt["workload"]["acceptance"]
            self.assertLessEqual(
                acceptance["maximum_prompt_tokens"] + config.prompt["settings"]["max_tokens"],
                context_size,
            )
        near_window = load_benchmark_config(
            self.repository_root, Path("configs/phase13-iq4-xs-context-64k-q4.json")
        )
        self.assertGreaterEqual(
            near_window.prompt["workload"]["acceptance"]["minimum_prompt_tokens"], 60000
        )

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
