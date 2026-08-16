import tempfile
import unittest
from pathlib import Path

from qwen_bench.release_audit import _validate_markdown_links


class ReleaseAuditTests(unittest.TestCase):
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
