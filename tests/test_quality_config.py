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


if __name__ == "__main__":
    unittest.main()
