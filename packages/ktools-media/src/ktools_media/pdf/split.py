"""PDF split capability using pypdf."""
from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

try:
    import pypdf
except ImportError:  # pragma: no cover
    pypdf = None  # type: ignore[assignment]


def split_pdf(
    input_path: Path,
    output_dir: Path,
    parts: int,
) -> list[Path]:
    """
    Splits a PDF into `parts` roughly equal sections.
    Each part is written atomically.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input PDF not found: {input_path}")

    if parts < 2:
        raise ValueError("Parts must be at least 2.")

    if pypdf is None:
        raise RuntimeError("pypdf is required for PDF split. Install with: pip install pypdf")

    output_dir.mkdir(parents=True, exist_ok=True)

    reader = pypdf.PdfReader(str(input_path))
    total_pages = len(reader.pages)
    # Cap parts to total pages
    parts = min(parts, total_pages)

    outputs: list[Path] = []
    start_page = 0

    for index in range(1, parts + 1):
        remaining_pages = total_pages - start_page
        remaining_parts = parts - index + 1
        count = (remaining_pages + remaining_parts - 1) // remaining_parts
        end_page = min(total_pages, start_page + count)

        target_name = f"{input_path.stem}_part_{index:02d}_of_{parts:02d}.pdf"
        target_path = output_dir / target_name
        tmp_out = target_path.with_name(f"{target_path.name}.{uuid4().hex}.tmp")

        try:
            writer = pypdf.PdfWriter()
            for page_index in range(start_page, end_page):
                writer.add_page(reader.pages[page_index])

            with open(str(tmp_out), "wb") as f:
                writer.write(f)

            os.replace(tmp_out, target_path)
            outputs.append(target_path)
        finally:
            if tmp_out.exists():
                try:
                    tmp_out.unlink()
                except OSError:
                    pass

        start_page = end_page

    return outputs
