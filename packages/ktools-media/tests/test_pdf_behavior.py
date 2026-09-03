"""Tests for pdf.merge and pdf.split behaviors."""
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock


class PdfMergeBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        self.pdf1 = self.root / "a.pdf"
        self.pdf1.write_bytes(b"%PDF-1.4 fake")

        self.pdf2 = self.root / "b.pdf"
        self.pdf2.write_bytes(b"%PDF-1.4 fake2")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_missing_input_raises(self):
        from ktools_media.pdf.merge import merge_pdfs
        with self.assertRaises(FileNotFoundError):
            merge_pdfs([self.root / "missing.pdf"], self.root / "out.pdf")

    @patch("ktools_media.pdf.merge.pypdf")
    def test_merge_pdfs_calls_writer(self, mock_pypdf):
        from ktools_media.pdf.merge import merge_pdfs

        mock_writer = MagicMock()
        mock_reader = MagicMock()
        mock_reader.pages = [MagicMock(), MagicMock()]
        mock_pypdf.PdfWriter.return_value = mock_writer
        mock_pypdf.PdfReader.return_value = mock_reader

        def fake_write(f):
            f.write(b"pdf output")

        mock_writer.write.side_effect = fake_write

        out_path = self.root / "merged.pdf"
        result = merge_pdfs([self.pdf1, self.pdf2], out_path)

        self.assertEqual(result, out_path)
        self.assertTrue(out_path.exists())
        self.assertEqual(mock_pypdf.PdfReader.call_count, 2)
        self.assertEqual(mock_writer.add_page.call_count, 4)


class PdfSplitBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        self.pdf = self.root / "big.pdf"
        self.pdf.write_bytes(b"%PDF-1.4 fake big")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_missing_input_raises(self):
        from ktools_media.pdf.split import split_pdf
        with self.assertRaises(FileNotFoundError):
            split_pdf(self.root / "missing.pdf", self.root, 3)

    def test_too_few_parts_raises(self):
        from ktools_media.pdf.split import split_pdf
        with self.assertRaises(ValueError):
            split_pdf(self.pdf, self.root, 1)

    @patch("ktools_media.pdf.split.pypdf")
    def test_split_pdf_creates_parts(self, mock_pypdf):
        from ktools_media.pdf.split import split_pdf

        mock_reader = MagicMock()
        mock_reader.pages = [MagicMock() for _ in range(6)]
        mock_pypdf.PdfReader.return_value = mock_reader

        def create_writer():
            mock_writer = MagicMock()
            def fake_write(f):
                f.write(b"part pdf")
            mock_writer.write.side_effect = fake_write
            return mock_writer

        mock_pypdf.PdfWriter.side_effect = create_writer

        result = split_pdf(self.pdf, self.root, 3)
        self.assertEqual(len(result), 3)
        self.assertEqual(mock_pypdf.PdfWriter.call_count, 3)


if __name__ == "__main__":
    unittest.main()
