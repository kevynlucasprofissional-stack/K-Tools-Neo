from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from ktools_core.models import Artifact, DataType
from ktools_pdf import PdfMergeError, merge_pdf_files


def make_pdf(path: Path, sizes: list[tuple[float, float]]) -> None:
    writer = PdfWriter()
    try:
        for width, height in sizes:
            writer.add_blank_page(width=width, height=height)
        with path.open("wb") as handle:
            writer.write(handle)
    finally:
        close = getattr(writer, "close", None)
        if callable(close):
            close()


def dimensions(path: Path) -> list[tuple[float, float]]:
    reader = PdfReader(str(path), strict=False)
    try:
        return [
            (float(page.mediabox.width), float(page.mediabox.height))
            for page in reader.pages
        ]
    finally:
        stream = getattr(reader, "stream", None)
        close = getattr(stream, "close", None)
        if callable(close):
            close()


class PdfMergeWriterCharacterizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_merge_preserves_file_then_page_order_and_normalizes_suffix(self) -> None:
        first = self.root / "first.pdf"
        second = self.root / "second.pdf"
        make_pdf(first, [(101, 201), (102, 202)])
        make_pdf(second, [(301, 401)])

        artifact = merge_pdf_files([first, second], self.root / "merged.bin")
        output = self.root / "merged.pdf"

        self.assertIsInstance(artifact, Artifact)
        self.assertIs(artifact.type, DataType.PDF)
        self.assertEqual(artifact.uri, output.resolve().as_uri())
        self.assertEqual(artifact.mime_type, "application/pdf")
        self.assertEqual(artifact.metadata["sourceCount"], 2)
        self.assertEqual(artifact.metadata["totalPages"], 3)
        self.assertEqual(dimensions(output), [(101.0, 201.0), (102.0, 202.0), (301.0, 401.0)])

    def test_progress_callback_is_preserved_by_direct_api(self) -> None:
        first = self.root / "first.pdf"
        second = self.root / "second.pdf"
        make_pdf(first, [(101, 201)])
        make_pdf(second, [(301, 401)])
        events: list[tuple[float, str]] = []

        merge_pdf_files([first, second], self.root / "merged.pdf", lambda value, message: events.append((value, message)))

        self.assertGreaterEqual(len(events), 3)
        self.assertEqual(events[0][0], 0.0)
        self.assertEqual(events[-1][0], 1.0)
        self.assertIn("first.pdf", events[0][1])
        self.assertIn("2 pages", events[-1][1])

    def test_single_path_is_not_silently_treated_as_a_path_sequence(self) -> None:
        source = self.root / "source.pdf"
        make_pdf(source, [(100, 100)])
        with self.assertRaises(PdfMergeError):
            merge_pdf_files(source, self.root / "out.pdf")  # type: ignore[arg-type]

    def test_empty_missing_directory_and_non_pdf_inputs_are_rejected(self) -> None:
        directory = self.root / "folder"
        directory.mkdir()
        text_file = self.root / "notes.txt"
        text_file.write_text("not pdf", encoding="utf-8")
        cases = [
            [],
            [self.root / "missing.pdf"],
            [directory],
            [text_file],
        ]
        for case in cases:
            with self.subTest(case=case):
                with self.assertRaises(PdfMergeError):
                    merge_pdf_files(case, self.root / "out.pdf")

    def test_output_may_not_be_one_of_the_inputs(self) -> None:
        source = self.root / "source.pdf"
        make_pdf(source, [(100, 100)])
        with self.assertRaises(PdfMergeError):
            merge_pdf_files([source], source)

    def test_empty_and_encrypted_pdfs_fail_closed(self) -> None:
        empty = self.root / "empty.pdf"
        writer = PdfWriter()
        with empty.open("wb") as handle:
            writer.write(handle)
        close = getattr(writer, "close", None)
        if callable(close):
            close()

        encrypted = self.root / "encrypted.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.encrypt("secret", algorithm="RC4-40")
        with encrypted.open("wb") as handle:
            writer.write(handle)
        close = getattr(writer, "close", None)
        if callable(close):
            close()

        for path in (empty, encrypted):
            with self.subTest(path=path.name):
                with self.assertRaises(PdfMergeError):
                    merge_pdf_files([path], self.root / f"{path.stem}-out.pdf")

    def test_existing_destination_survives_failure_before_publication(self) -> None:
        valid = self.root / "valid.pdf"
        broken = self.root / "broken.pdf"
        output = self.root / "merged.pdf"
        make_pdf(valid, [(110, 210)])
        broken.write_bytes(b"this is not a pdf")
        make_pdf(output, [(777, 888)])
        before = output.read_bytes()

        with self.assertRaises(PdfMergeError):
            merge_pdf_files([valid, broken], output)

        self.assertEqual(output.read_bytes(), before)
        self.assertEqual(dimensions(output), [(777.0, 888.0)])

    def test_existing_non_input_destination_is_replaced_on_success(self) -> None:
        source = self.root / "source.pdf"
        output = self.root / "merged.pdf"
        make_pdf(source, [(120, 220), (121, 221)])
        make_pdf(output, [(999, 999)])

        merge_pdf_files([source], output)

        self.assertEqual(dimensions(output), [(120.0, 220.0), (121.0, 221.0)])


if __name__ == "__main__":
    unittest.main()
