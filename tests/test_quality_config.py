import copy
import unittest
from pathlib import Path

from qwen_bench.config import load_json_object
from qwen_bench.quality_config import load_quality_config


class QualityConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]

    def test_phase8_pair_loads_and_differs_only_by_model_identity(self) -> None:
        iq2 = load_quality_config(self.root, Path("configs/phase8-quality-iq2.json"))
        q2 = load_quality_config(self.root, Path("configs/phase8-quality-q2.json"))
        self.assertEqual(iq2.suite_path, q2.suite_path)
        self.assertEqual(len(iq2.suite["tasks"]), 24)
        iq2_data = copy.deepcopy(iq2.data)
        q2_data = copy.deepcopy(q2.data)
        for data in (iq2_data, q2_data):
            data["run"].pop("classification")
            data["run"].pop("result_prefix")
            data["server"].pop("model_alias")
            data["inputs"].pop("model_manifest")
            data["model"].pop("quantization")
        self.assertEqual(iq2_data, q2_data)

    def test_phase8_suite_categories_ids_and_phase2_independence(self) -> None:
        suite = load_json_object(self.root / "prompts/phase8-quality-evaluation.json")
        phase2 = load_json_object(self.root / "prompts/phase2-quant-triage.json")
        ids = [task["task_id"] for task in suite["tasks"]]
        old_ids = {task["task_id"] for task in phase2["prompts"]}
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(set(ids).isdisjoint(old_ids))
        counts = {
            category: sum(1 for task in suite["tasks"] if task["category"] == category)
            for category in {task["category"] for task in suite["tasks"]}
        }
        self.assertEqual(
            counts,
            {
                "arithmetic": 5,
                "logic": 5,
                "python_trace": 5,
                "structured_output": 5,
                "text_data": 4,
            },
        )
        self.assertTrue(all(task["grading_notes"].strip() for task in suite["tasks"]))

    def test_phase13_retrieval_pair_loads_and_differs_only_by_cache_identity(self) -> None:
        q8 = load_quality_config(
            self.root, Path("configs/phase13-iq4-xs-retrieval-16k-q8.json")
        )
        q4 = load_quality_config(
            self.root, Path("configs/phase13-iq4-xs-retrieval-16k-q4.json")
        )
        self.assertEqual(q8.suite["suite_type"], "retrieval")
        self.assertEqual(len(q8.suite["tasks"]), 3)
        self.assertEqual(q8.suite_path, q4.suite_path)
        q8_data = copy.deepcopy(q8.data)
        q4_data = copy.deepcopy(q4.data)
        for data in (q8_data, q4_data):
            data["run"].pop("classification")
            data["run"].pop("result_prefix")
            data["configuration"].pop("kv_cache_k_type")
            data["configuration"].pop("kv_cache_v_type")
        self.assertEqual(q8_data, q4_data)

    def test_phase13_near_window_retrieval_has_three_needle_positions(self) -> None:
        config = load_quality_config(
            self.root, Path("configs/phase13-iq4-xs-retrieval-64k-q4.json")
        )
        tasks = config.suite["tasks"]
        self.assertEqual(
            [task["synthetic_context"]["needle_record"] for task in tasks],
            [25, 1249, 2475],
        )
        self.assertTrue(
            all(task["acceptance"]["minimum_prompt_tokens"] >= 60000 for task in tasks)
        )

    def test_phase13_objective_quality_reuses_phase8_suite_and_controls(self) -> None:
        iq4 = load_quality_config(
            self.root, Path("configs/phase13-iq4-xs-quality-4k-q8.json")
        )
        iq2 = load_quality_config(self.root, Path("configs/phase8-quality-iq2.json"))
        self.assertEqual(iq4.suite_path, iq2.suite_path)
        self.assertEqual(len(iq4.suite["tasks"]), 24)
        self.assertEqual(iq4.data["configuration"]["gpu_layers"], 45)
        self.assertEqual(iq4.data["configuration"]["kv_cache_k_type"], "q8_0")
        for key in (
            "context_size",
            "parallel_slots",
            "flash_attention",
            "prompt_batch_size",
            "prompt_micro_batch_size",
            "threads",
            "threads_batch",
            "kv_cache_k_type",
            "kv_cache_v_type",
            "thinking_mode",
            "mtp_enabled",
        ):
            self.assertEqual(iq4.data["configuration"][key], iq2.data["configuration"][key])


if __name__ == "__main__":
    unittest.main()
