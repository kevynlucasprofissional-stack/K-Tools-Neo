from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ktools_core.models import Artifact, DataType
from ktools_text.capability import TextMergeError
from ktools_text.writer import merge_text_files, read_text_with_fallback


class TextWriterCharacterizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_decoding_preserves_utf8_sig_utf8_and_latin1_legacy_order(self) -> None:
        bom = self.root / "bom.md"
        utf8 = self.root / "utf8.txt"
        latin1 = self.root / "latin1.txt"
        bom.write_bytes(b"\xef\xbb\xbfCom BOM")
        utf8.write_text("ação ✓", encoding="utf-8")
        latin1.write_bytes("ação".encode("latin-1"))

        self.assertEqual(read_text_with_fallback(bom), "Com BOM")
        self.assertEqual(read_text_with_fallback(utf8), "ação ✓")
        self.assertEqual(read_text_with_fallback(latin1), "ação")

    def test_merge_preserves_input_order_normalizes_suffix_and_returns_artifact(self) -> None:
        first = self.root / "first.md"
        second = self.root / "second.txt"
        first.write_text("FIRST", encoding="utf-8")
        second.write_text("SECOND", encoding="utf-8")
        requested = self.root / "nested" / "merged.log"

        artifact = merge_text_files(
            [second, first],
            requested,
            "nenhum",
            produced_by="run_x/node_x",
        )

        output = self.root / "nested" / "merged.md"
        self.assertTrue(output.exists())
        self.assertEqual(output.read_text(encoding="utf-8"), "SECOND\n\nFIRST\n\n")
        self.assertIsInstance(artifact, Artifact)
        self.assertIs(artifact.type, DataType.FILE)
        self.assertEqual(artifact.uri, output.resolve().as_uri())
        self.assertEqual(artifact.produced_by, "run_x/node_x")

    def test_empty_missing_directory_and_unsupported_inputs_are_rejected(self) -> None:
        with self.assertRaises(TextMergeError):
            merge_text_files([], self.root / "out.md")
        with self.assertRaises(TextMergeError):
            merge_text_files([self.root / "missing.md"], self.root / "out.md")
        folder = self.root / "folder.md"
        folder.mkdir()
        with self.assertRaises(TextMergeError):
            merge_text_files([folder], self.root / "out.md")
        bad = self.root / "bad.rtf"
        bad.write_text("bad", encoding="utf-8")
        with self.assertRaises(TextMergeError):
            merge_text_files([bad], self.root / "out.md")

    def test_output_cannot_replace_an_input(self) -> None:
        source = self.root / "same.md"
        source.write_text("keep", encoding="utf-8")
        with self.assertRaises(TextMergeError):
            merge_text_files([source], source, "nenhum")
        self.assertEqual(source.read_text(encoding="utf-8"), "keep")

    def test_existing_destination_is_replaced_after_success(self) -> None:
        source = self.root / "source.md"
        output = self.root / "merged.md"
        source.write_text("new", encoding="utf-8")
        output.write_text("old", encoding="utf-8")
        merge_text_files([source], output, "nenhum")
        self.assertEqual(output.read_text(encoding="utf-8"), "new\n\n")

    def test_failure_during_second_file_keeps_existing_destination_and_cleans_temp(self) -> None:
        first = self.root / "first.md"
        second = self.root / "second.md"
        output = self.root / "merged.md"
        first.write_text("first", encoding="utf-8")
        second.write_text("second", encoding="utf-8")
        output.write_text("ORIGINAL", encoding="utf-8")

        def fail_on_second(index: int, _total: int, _message: str) -> None:
            if index == 2:
                raise RuntimeError("synthetic progress failure")

        with self.assertRaises(RuntimeError):
            merge_text_files([first, second], output, "nenhum", fail_on_second)

        self.assertEqual(output.read_text(encoding="utf-8"), "ORIGINAL")
        self.assertEqual(list(self.root.glob(".merged_ktools_*")), [])


if __name__ == "__main__":
    unittest.main()
