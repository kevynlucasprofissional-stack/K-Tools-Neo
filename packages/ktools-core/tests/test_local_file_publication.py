from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ktools_core.local_files import cleanup_local_path, replace_temp_output, same_local_path, temporary_sibling_path


class LocalFilePublicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_same_local_path_uses_resolved_identity(self) -> None:
        target = self.root / "target.txt"
        self.assertTrue(same_local_path(target, self.root / "." / "target.txt"))
        self.assertFalse(same_local_path(target, self.root / "other.txt"))

    def test_temporary_sibling_uses_destination_directory_and_requested_suffix(self) -> None:
        output = self.root / "nested" / "result.pdf"
        temp = temporary_sibling_path(output, suffix=".tmp")
        try:
            self.assertEqual(temp.parent, output.parent)
            self.assertEqual(temp.suffix, ".tmp")
            self.assertTrue(temp.name.startswith(".result_ktools_"))
            self.assertTrue(temp.exists())
        finally:
            cleanup_local_path(temp)

    def test_replace_temp_output_replaces_existing_destination(self) -> None:
        output = self.root / "result.txt"
        output.write_text("old", encoding="utf-8")
        temp = temporary_sibling_path(output)
        temp.write_text("new", encoding="utf-8")
        replace_temp_output(temp, output)
        self.assertEqual(output.read_text(encoding="utf-8"), "new")
        self.assertFalse(temp.exists())

    def test_cleanup_is_idempotent(self) -> None:
        path = self.root / "temp.bin"
        path.write_bytes(b"x")
        cleanup_local_path(path)
        cleanup_local_path(path)
        self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
