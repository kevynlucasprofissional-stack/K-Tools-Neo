from __future__ import annotations

from pathlib import Path
from typing import Sequence

from ktools_core.models import Artifact, DataType

from .reader import PdfMergeError, close_pdf_reader, open_pdf_reader_checked, validate_pdf_path
from .writer import ProgressCallback, write_pdf_writer_atomic


def _validate_parts(parts: int) -> int:
    if isinstance(parts, bool) or not isinstance(parts, int):
        raise PdfMergeError("PDF split parts must be an integer >= 2")
    if parts < 2:
        raise PdfMergeError("PDF split parts must be at least 2")
    return parts


def _prepare_output_dir(output_dir: Path) -> Path:
    dest = Path(output_dir).expanduser()
    try:
        dest.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise PdfMergeError(f"Could not create PDF split output directory {dest}: {exc}") from exc
    if not dest.is_dir():
        raise PdfMergeError(f"PDF split output path is not a directory: {dest}")
    return dest


def _candidate_key(path: Path) -> str:
    try:
        value = str(path.resolve())
    except Exception:
        value = str(path.absolute())
    return value.lower()


def _safe_unique_path(path: Path, reserved: set[str]) -> Path:
    candidate = Path(path)
    index = 1
    while True:
        key = _candidate_key(candidate)
        if key not in reserved and not candidate.exists():
            reserved.add(key)
            return candidate
        candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
        index += 1


def _close_writer(pdf_writer: object) -> None:
    close = getattr(pdf_writer, "close", None)
    if callable(close):
        try:
            close()
        except Exception:
            pass


def split_pdf_into_parts(
    input_pdf: Path,
    output_dir: Path,
    parts: int,
    progress_callback: ProgressCallback | None = None,
    *,
    produced_by: str | None = None,
) -> list[Artifact]:
    source = validate_pdf_path(Path(input_pdf))
    requested_parts = _validate_parts(parts)
    dest = _prepare_output_dir(Path(output_dir))
    reader, total_pages = open_pdf_reader_checked(source)
    actual_parts = min(requested_parts, total_pages)
    reserved: set[str] = set()
    outputs: list[Artifact] = []
    start_page = 0

    try:
        from pypdf import PdfWriter

        for index in range(1, actual_parts + 1):
            remaining_pages = total_pages - start_page
            remaining_parts = actual_parts - index + 1
            page_count = (remaining_pages + remaining_parts - 1) // remaining_parts
            end_page = min(total_pages, start_page + page_count)

            if progress_callback is not None:
                progress_callback(
                    (index - 1) / actual_parts,
                    f"Generating PDF part {index} of {actual_parts} — pages {start_page + 1} to {end_page}",
                )

            pdf_writer = PdfWriter()
            try:
                try:
                    for page_index in range(start_page, end_page):
                        pdf_writer.add_page(reader.pages[page_index])
                except Exception as exc:
                    raise PdfMergeError(
                        f"Failed while copying pages for PDF part {index} from {source}: {exc}"
                    ) from exc

                clean_path = dest / f"{source.stem}_parte_{index:02d}_de_{actual_parts:02d}.pdf"
                output = _safe_unique_path(clean_path, reserved)
                write_pdf_writer_atomic(pdf_writer, output)
            finally:
                _close_writer(pdf_writer)

            outputs.append(
                Artifact.create(
                    type=DataType.PDF,
                    uri=output.resolve().as_uri(),
                    produced_by=produced_by,
                    mime_type="application/pdf",
                    metadata={
                        "sourceName": source.name,
                        "partIndex": index,
                        "partCount": actual_parts,
                        "pageStart": start_page + 1,
                        "pageEnd": end_page,
                        "pageCount": end_page - start_page,
                    },
                )
            )
            start_page = end_page
    finally:
        close_pdf_reader(reader)

    if progress_callback is not None:
        progress_callback(1.0, f"PDF split into {len(outputs)} part(s)")
    return outputs
