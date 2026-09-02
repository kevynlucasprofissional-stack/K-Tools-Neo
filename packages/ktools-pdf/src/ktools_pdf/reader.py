from __future__ import annotations

from pathlib import Path
from typing import Any

from pypdf import PdfReader


class PdfMergeError(RuntimeError):
    """Domain error for PDF merge validation/read/publication failures."""


def validate_pdf_path(path: Path) -> Path:
    pdf_path = Path(path)
    try:
        if not pdf_path.exists():
            raise PdfMergeError(f"PDF not found: {pdf_path}")
        if not pdf_path.is_file():
            raise PdfMergeError(f"PDF path is not a file: {pdf_path}")
    except OSError as exc:
        raise PdfMergeError(f"PDF path could not be inspected: {pdf_path}: {exc}") from exc
    if pdf_path.suffix.lower() != ".pdf":
        raise PdfMergeError(f"Unsupported PDF input extension: {pdf_path}")
    return pdf_path


def close_pdf_reader(reader: Any) -> None:
    stream = getattr(reader, "stream", None)
    close = getattr(stream, "close", None)
    if callable(close):
        try:
            close()
        except Exception:
            pass


def open_pdf_reader_checked(path: Path) -> tuple[PdfReader, int]:
    pdf_path = validate_pdf_path(path)
    try:
        reader = PdfReader(str(pdf_path), strict=False)
    except FileNotFoundError as exc:
        raise PdfMergeError(f"PDF not found: {pdf_path}") from exc
    except PermissionError as exc:
        raise PdfMergeError(f"PDF cannot be opened due to permissions: {pdf_path}") from exc
    except Exception as exc:
        raise PdfMergeError(f"PDF is corrupt, incomplete, or unsupported: {pdf_path}: {exc}") from exc

    try:
        if bool(getattr(reader, "is_encrypted", False)):
            raise PdfMergeError(f"Encrypted/protected PDF is not supported in V1: {pdf_path}")
        try:
            page_count = len(reader.pages)
        except Exception as exc:
            raise PdfMergeError(f"PDF pages are not readable: {pdf_path}: {exc}") from exc
        if page_count <= 0:
            raise PdfMergeError(f"PDF has no readable pages: {pdf_path}")
        return reader, page_count
    except Exception:
        close_pdf_reader(reader)
        raise
