import tempfile
import unittest
from pathlib import Path

from qwen_bench.release_audit import _maximum_size_for_path, _validate_markdown_links


class ReleaseAuditTests(unittest.TestCase):
    def test_raw_json_size_override_is_narrowly_scoped(self) -> None:
        policy = {
            "maximum_tracked_file_bytes": 1_048_576,
            "maximum_raw_result_file_bytes": 5_242_880,
        }
        self.assertEqual(
            _maximum_size_for_path("results/raw/benchmark.json", policy), 5_242_880
        )
        self.assertEqual(
            _maximum_size_for_path("results/summaries/benchmark.json", policy),
            1_048_576,
        )
        self.assertEqual(
            _maximum_size_for_path("results/raw/archive.zip", policy), 1_048_576
        )

    def test_raw_json_size_override_accepts_windows_separators(self) -> None:
        policy = {
            "maximum_tracked_file_bytes": 1_048_576,
            "maximum_raw_result_file_bytes": 5_242_880,
        }
        self.assertEqual(
            _maximum_size_for_path("results\\raw\\benchmark.json", policy), 5_242_880
        )

    def test_unresolved_repository_root_is_normalized(self) -> None:
        working_directory = Path.cwd().resolve()
        with tempfile.TemporaryDirectory(dir=working_directory) as directory:
            resolved_root = Path(directory).resolve()
            relative_root = resolved_root.relative_to(working_directory)
            (resolved_root / "target.md").write_text("# Target\n", encoding="utf-8")
            (resolved_root / "source.md").write_text(
                "[target](target.md)\n", encoding="utf-8"
            )
            self.assertEqual(
                _validate_markdown_links(relative_root, ["source.md", "target.md"]), []
            )

    def test_relative_markdown_links_are_resolved_from_the_source_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            (root / "target.md").write_text("# Target\n", encoding="utf-8")
            (root / "docs" / "source.md").write_text(
                "[target](../target.md#target)\n[external](https://example.com)\n",
                encoding="utf-8",
            )
            self.assertEqual(
                _validate_markdown_links(root, ["docs/source.md", "target.md"]), []
            )

    def test_missing_or_escaping_markdown_links_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "source.md").write_text(
                "[missing](missing.md)\n[escape](../outside.md)\n", encoding="utf-8"
            )
            issues = _validate_markdown_links(root, ["source.md"])
            self.assertEqual(len(issues), 2)
            self.assertTrue(any("broken" in issue for issue in issues))
            self.assertTrue(any("escapes" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
