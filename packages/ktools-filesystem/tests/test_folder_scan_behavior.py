from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from ktools_core.models import DataType
from ktools_filesystem.api import scan_folder_files


class FolderScanBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_recursive_scan_and_ordering(self) -> None:
        (self.root / "b").mkdir()
        (self.root / "a").mkdir()
        (self.root / "b" / "z.txt").write_text("z")
        (self.root / "a" / "y.txt").write_text("y")
        (self.root / "x.txt").write_text("x")

        res = scan_folder_files(self.root, recursive=True)
        self.assertEqual(len(res.files), 3)
        self.assertEqual(res.report["fileCount"], 3)
        self.assertEqual(res.report["errorCount"], 0)

        # Alphabetical ordering of relative path
        paths = [f.metadata["relativePath"] for f in res.files]
        self.assertEqual(paths, ["a/y.txt", "b/z.txt", "x.txt"])

        res_non_rec = scan_folder_files(self.root, recursive=False)
        self.assertEqual(len(res_non_rec.files), 1)
        self.assertEqual(res_non_rec.files[0].metadata["relativePath"], "x.txt")

    def test_hidden_semantics(self) -> None:
        (self.root / ".hidden_dir").mkdir()
        (self.root / ".hidden_dir" / "a.txt").write_text("a")
        (self.root / "visible_dir").mkdir()
        (self.root / "visible_dir" / ".hidden.txt").write_text("h")
        (self.root / "visible_dir" / "visible.txt").write_text("v")

        # Exclude hidden
        res1 = scan_folder_files(self.root, include_hidden=False)
        self.assertEqual(len(res1.files), 1)
        self.assertEqual(res1.files[0].metadata["name"], "visible.txt")

        # Include hidden
        res2 = scan_folder_files(self.root, include_hidden=True)
        self.assertEqual(len(res2.files), 3)
        paths = {f.metadata["name"] for f in res2.files}
        self.assertEqual(paths, {"a.txt", ".hidden.txt", "visible.txt"})

    def test_extensions_filtering(self) -> None:
        (self.root / "a.TXT").write_text("a")
        (self.root / "b.txt").write_text("b")
        (self.root / "c.md").write_text("c")
        (self.root / "d.PDF").write_text("d")
        (self.root / "noext").write_text("no")

        res = scan_folder_files(self.root, extensions={".txt", "md"})
        self.assertEqual(len(res.files), 3)
        names = {f.metadata["name"] for f in res.files}
        self.assertEqual(names, {"a.TXT", "b.txt", "c.md"})

    def test_symlink_rejection_at_root(self) -> None:
        target = self.root / "target"
        target.mkdir()
        link = self.root / "link"
        try:
            os.symlink(target, link)
        except OSError:
            self.skipTest("Symlinks not supported on this environment")
            
        with self.assertRaises(Exception) as ctx:
            scan_folder_files(link)
        self.assertIn("symlink or reparse point", str(ctx.exception))

    def test_symlink_skipping_nested(self) -> None:
        target = self.root / "target"
        target.mkdir()
        (target / "a.txt").write_text("a")
        
        link = self.root / "link"
        try:
            os.symlink(target, link)
        except OSError:
            self.skipTest("Symlinks not supported on this environment")
            
        (self.root / "b.txt").write_text("b")

        # scan self.root, should skip 'link' completely but find 'target/a.txt' and 'b.txt'
        res = scan_folder_files(self.root)
        names = {f.metadata["relativePath"] for f in res.files}
        self.assertEqual(names, {"b.txt", "target/a.txt"})


if __name__ == "__main__":
    unittest.main()
