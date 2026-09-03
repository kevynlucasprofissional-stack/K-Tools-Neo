import csv
import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from ktools_filesystem.drive_scanner import stream_scan_directory


class FilesystemDriveScannerBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        # Create nested test folder structure
        self.d1 = self.root / "CloudDrive"
        self.d1.mkdir()
        self.sub = self.d1 / "Submodule"
        self.sub.mkdir()

        (self.d1 / "file_local.txt").write_bytes(b"local_bytes")
        (self.sub / "file_cloud.pdf").write_bytes(b"pdf_bytes")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_missing_root_raises(self):
        with self.assertRaises(FileNotFoundError):
            stream_scan_directory(self.root / "nonexistent", self.root)

    def test_stream_scan_creates_sqlite_and_csv_reports(self):
        out_dir = self.root / "outputs"
        db_path, csv_path, report = stream_scan_directory(
            root_dir=self.d1,
            output_dir=out_dir,
            base_name="test_scan",
            include_files=True,
            include_hidden=False,
            verify_stability=False,
        )

        self.assertTrue(db_path.exists())
        self.assertTrue(csv_path.exists())

        # Verify SQLite DB
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM files")
        file_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM directories")
        dir_count = cur.fetchone()[0]
        conn.close()

        self.assertEqual(file_count, 2)
        self.assertEqual(dir_count, 2)  # root + Submodule

        # Verify CSV
        with open(csv_path, "r", encoding="utf-8") as f:
            rows = list(csv.reader(f))
            self.assertGreater(len(rows), 2)

        # Verify Report
        self.assertEqual(report["total_files"], 2)
        self.assertEqual(report["total_directories"], 1)


if __name__ == "__main__":
    unittest.main()
