import json
import tempfile
import unittest
from pathlib import Path

from qwen_bench.storage import ResultExistsError, write_result_exclusive


class StorageTests(unittest.TestCase):
    def test_result_write_is_exclusive_and_valid_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            path = write_result_exclusive(output, "run-1", {"answer": 42})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"answer": 42})
            with self.assertRaises(ResultExistsError):
                write_result_exclusive(output, "run-1", {"answer": 43})

    def test_run_id_cannot_escape_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                write_result_exclusive(Path(directory), "../escape", {"answer": 42})


if __name__ == "__main__":
    unittest.main()
