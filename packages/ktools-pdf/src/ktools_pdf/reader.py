from __future__ import annotations


class PdfMergeError(RuntimeError):
    """Domain error for PDF merge validation/publication failures."""


def open_pdf_reader_checked(path):
    raise NotImplementedError("PDF merge characterization RED: checked reader not implemented yet")
