import csv
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from ktools_filesystem.reports import generate_structure_report


class FilesystemReportBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        # Create nested test folder structure
        self.d1 = self.root / "docs"
        self.d2 = self.root / "images"
        self.d1.mkdir()
        self.d2.mkdir()

        (self.d1 / "notes.txt").write_text("hello notes", encoding="utf-8")
        (self.d1 / "readme.md").write_text("hello readme", encoding="utf-8")
        (self.d2 / "photo.png").write_bytes(b"png_bytes_123")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_missing_root_raises(self):
        with self.assertRaises(FileNotFoundError):
            generate_structure_report(self.root / "missing", self.root)

    def test_generate_structure_report_outputs(self):
        out_dir = self.root / "reports"
        csv_path, txt_path, json_data = generate_structure_report(
            root_dir=self.root,
            output_dir=out_dir,
            base_name="inventory",
        )

        self.assertTrue(csv_path.exists())
        self.assertTrue(txt_path.exists())

        # Verify CSV
        with open(csv_path, "r", encoding="utf-8") as f:
            rows = list(csv.reader(f))
            header = rows[0]
            self.assertIn("relative_path", header)
            self.assertIn("type", header)
            self.assertIn("size_bytes", header)
            self.assertGreater(len(rows), 3)

        # Verify TXT Tree
        txt_content = txt_path.read_text(encoding="utf-8")
        self.assertIn("docs", txt_content)
        self.assertIn("images", txt_content)
        self.assertIn("notes.txt", txt_content)

        # Verify JSON
        self.assertEqual(json_data["total_files"], 3)
        self.assertEqual(json_data["total_directories"], 2)


if __name__ == "__main__":
    unittest.main()
