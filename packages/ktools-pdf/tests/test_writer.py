from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pypdf import PdfReader, PdfWriter

from ktools_pdf import PDFMergeError, api


class PdfMergeCharacterizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _pdf(self, name: str, widths: list[float]) -> Path:
        path = self.root / name
        writer = PdfWriter()
        for width in widths:
            writer.add_blank_page(width=width, height=300)
        with path.open("wb") as handle:
            writer.write(handle)
        writer.close()
        return path

    @staticmethod
    def _widths(path: Path) -> list[int]:
        reader = PdfReader(str(path), strict=False)
        return [round(float(page.mediabox.width)) for page in reader.pages]

    def test_merge_preserves_file_then_page_order(self) -> None:
        first = self._pdf("first.pdf", [101, 102])
        second = self._pdf("second.pdf", [201])
        output = self.root / "merged.pdf"
        artifact = api.merge_pdf_files([first, second], output)
        self.assertTrue(output.exists())
        self.assertEqual(self._widths(output), [101, 102, 201])
        self.assertEqual(artifact.metadata["sourceCount"], 2)
        self.assertEqual(artifact.metadata["totalPages"], 3)

    def test_non_pdf_output_suffix_is_normalized(self) -> None:
        source = self._pdf("source.pdf", [100])
        artifact = api.merge_pdf_files([source], self.root / "result.tmp")
        self.assertTrue((self.root / "result.pdf").exists())
        self.assertTrue(artifact.uri.endswith("result.pdf"))

    def test_empty_missing_non_file_and_non_pdf_inputs_are_rejected(self) -> None:
        with self.assertRaises(PDFMergeError):
            api.merge_pdf_files([], self.root / "out.pdf")
        with self.assertRaises(PDFMergeError):
            api.merge_pdf_files([self.root / "missing.pdf"], self.root / "out.pdf")
        folder = self.root / "folder.pdf"
        folder.mkdir()
        with self.assertRaises(PDFMergeError):
            api.merge_pdf_files([folder], self.root / "out.pdf")
        text = self.root / "not-pdf.txt"
        text.write_text("x", encoding="utf-8")
        with self.assertRaises(PDFMergeError):
            api.merge_pdf_files([text], self.root / "out.pdf")

    def test_output_cannot_be_an_input(self) -> None:
        source = self._pdf("source.pdf", [100])
        with self.assertRaises(PDFMergeError):
            api.merge_pdf_files([source], source)

    def test_encrypted_pdf_fails_closed(self) -> None:
        path = self.root / "secret.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.encrypt("secret")
        with path.open("wb") as handle:
            writer.write(handle)
        writer.close()
        with self.assertRaisesRegex(PDFMergeError, "(?i)proteg|criptograf|senha"):
            api.merge_pdf_files([path], self.root / "out.pdf")

    def test_corrupt_pdf_fails_with_classified_error(self) -> None:
        path = self.root / "broken.pdf"
        path.write_bytes(b"not-a-pdf")
        with self.assertRaises(PDFMergeError):
            api.merge_pdf_files([path], self.root / "out.pdf")

    def test_failure_before_replace_preserves_existing_destination(self) -> None:
        source = self._pdf("source.pdf", [100])
        output = self._pdf("existing.pdf", [777])
        before = output.read_bytes()
        with patch("ktools_pdf.writer.replace_temp_output", side_effect=OSError("forced replace failure")):
            with self.assertRaises(PDFMergeError):
                api.merge_pdf_files([source], output)
        self.assertEqual(output.read_bytes(), before)
        self.assertEqual(list(self.root.glob(".*_ktools_*")), [])


if __name__ == "__main__":
    unittest.main()
