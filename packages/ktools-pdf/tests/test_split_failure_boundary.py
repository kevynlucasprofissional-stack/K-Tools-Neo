from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pypdf import PdfWriter

from ktools_pdf import PdfMergeError, splitter


def make_pdf(path: Path, page_count: int) -> None:
    writer = PdfWriter()
    try:
        for index in range(page_count):
            writer.add_blank_page(width=100 + index, height=200 + index)
        with path.open("wb") as handle:
            writer.write(handle)
    finally:
        close = getattr(writer, "close", None)
        if callable(close):
            close()


class PdfSplitFailureBoundaryTests(unittest.TestCase):
    def test_later_part_failure_keeps_earlier_atomic_part_without_claiming_failed_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.pdf"
            output_dir = root / "parts"
            make_pdf(source, 4)

            original_publish = splitter.write_pdf_writer_atomic
            calls = {"count": 0}

            def fail_second_publish(pdf_writer, output_path):
                calls["count"] += 1
                if calls["count"] == 2:
                    raise PdfMergeError("forced second-part publication failure")
                return original_publish(pdf_writer, output_path)

            with patch.object(splitter, "write_pdf_writer_atomic", side_effect=fail_second_publish):
                with self.assertRaises(PdfMergeError):
                    splitter.split_pdf_into_parts(source, output_dir, 2)

            first = output_dir / "source_parte_01_de_02.pdf"
            second = output_dir / "source_parte_02_de_02.pdf"
            self.assertTrue(first.exists())
            self.assertFalse(second.exists())
            self.assertFalse(list(output_dir.glob(".*_ktools_*.tmp")))


if __name__ == "__main__":
    unittest.main()
