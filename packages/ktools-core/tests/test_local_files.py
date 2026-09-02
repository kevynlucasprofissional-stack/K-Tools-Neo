from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ktools_core.local_files import LocalFileUriError, path_from_file_uri


class LocalFileUriTests(unittest.TestCase):
    def test_round_trips_local_path_uri(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = (Path(temp_dir) / "arquivo com espaço.md").resolve()
            path.write_text("x", encoding="utf-8")
            self.assertEqual(path_from_file_uri(path.as_uri()), path)

    def test_localhost_authority_is_accepted_as_local(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = (Path(temp_dir) / "x.txt").resolve()
            uri = path.as_uri().replace("file://", "file://localhost", 1)
            self.assertEqual(path_from_file_uri(uri), path)

    def test_non_file_and_network_authority_fail_closed(self) -> None:
        with self.assertRaises(LocalFileUriError):
            path_from_file_uri("https://example.test/file.txt")
        with self.assertRaises(LocalFileUriError):
            path_from_file_uri("file://server/share/file.txt")


if __name__ == "__main__":
    unittest.main()
