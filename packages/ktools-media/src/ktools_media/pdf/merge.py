"""PDF merge capability using pypdf."""
from __future__ import annotations

from pathlib import Path
from typing import Sequence
from uuid import uuid4

try:
    import pypdf
except ImportError:  # pragma: no cover
    pypdf = None  # type: ignore[assignment]


def merge_pdfs(
    input_paths: Sequence[Path],
    output_path: Path,
) -> Path:
    """
    Merges multiple PDF files into a single output PDF.
    Uses pypdf. Writes atomically via a .tmp file.
    """
    if len(input_paths) < 1:
        raise ValueError("At least 1 PDF file is required for merge.")

    for p in input_paths:
        if not p.exists():
            raise FileNotFoundError(f"Input PDF not found: {p}")

    if pypdf is None:
        raise RuntimeError("pypdf is required for PDF merge. Install with: pip install pypdf")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_out = output_path.with_name(f"{output_path.name}.{uuid4().hex}.tmp")

    try:
        writer = pypdf.PdfWriter()
        for pdf_path in input_paths:
            reader = pypdf.PdfReader(str(pdf_path))
            for page in reader.pages:
                writer.add_page(page)

        with open(str(tmp_out), "wb") as f:
            writer.write(f)

        import os
        os.replace(tmp_out, output_path)
    finally:
        if tmp_out.exists():
            try:
                tmp_out.unlink()
            except OSError:
                pass

    return output_path
