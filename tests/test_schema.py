import json
import unittest
from pathlib import Path


class FormalSchemaTests(unittest.TestCase):
    def test_schema_is_draft_2020_12_and_covers_root_fields(self) -> None:
        root = Path(__file__).resolve().parents[1]
        schema = json.loads((root / "schemas/benchmark-result.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertFalse(schema["additionalProperties"])
        self.assertIn("runs", schema["required"])
        self.assertIn("measured_summary", schema["required"])
        self.assertIn("run", schema["$defs"])
        self.assertIn("statistics", schema["$defs"])


if __name__ == "__main__":
    unittest.main()
