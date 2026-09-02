from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Callable, Sequence

from pypdf import PdfWriter

from ktools_core.models import Artifact, DataType

from .reader import PdfMergeError, close_pdf_reader, open_pdf_reader_checked, validate_pdf_path

ProgressCallback = Callable[[float, str], None]


def _path_key(path: Path) -> str:
    try:
        resolved = str(Path(path).expanduser().resolve())
    except Exception:
        resolved = str(Path(path).absolute())
    return os.path.normcase(resolved)


def _normalize_inputs(input_files: Sequence[Path]) -> list[Path]:
    if not input_files:
        raise PdfMergeError("At least one PDF input is required")
    return [validate_pdf_path(Path(path)) for path in input_files]


def _normalize_output(output_file: Path) -> Path:
    output = Path(output_file)
    if output.suffix.lower() != ".pdf":
        output = output.with_suffix(".pdf")
    return output


def _ensure_output_not_in_inputs(output: Path, inputs: Sequence[Path]) -> None:
    output_key = _path_key(output)
    if output_key in {_path_key(path) for path in inputs}:
        raise PdfMergeError("The output PDF cannot replace one of its input PDFs")


def _cleanup(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except TypeError:
        if path.exists():
            path.unlink()
    except OSError:
        pass


def write_pdf_writer_atomic(pdf_writer: PdfWriter, output_file: Path) -> None:
    output = Path(output_file)
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{output.stem}_ktools_",
        suffix=".tmp",
        dir=str(output.parent),
    )
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        with temp_path.open("wb") as handle:
            pdf_writer.write(handle)
        os.replace(str(temp_path), str(output))
    except PdfMergeError:
        _cleanup(temp_path)
        raise
    except Exception as exc:
        _cleanup(temp_path)
        raise PdfMergeError(f"Failed to publish merged PDF {output}: {exc}") from exc


def merge_pdf_files(
    input_files: Sequence[Path],
    output_file: Path,
    progress_callback: ProgressCallback | None = None,
    *,
    produced_by: str | None = None,
) -> Artifact:
    inputs = _normalize_inputs(input_files)
    output = _normalize_output(Path(output_file))
    _ensure_output_not_in_inputs(output, inputs)
    output.parent.mkdir(parents=True, exist_ok=True)

    pdf_writer = PdfWriter()
    total_pages = 0
    total_sources = len(inputs)
    try:
        for source_index, pdf_path in enumerate(inputs, start=1):
            if progress_callback is not None:
                progress_callback(
                    (source_index - 1) / total_sources,
                    f"Merging PDF {source_index} of {total_sources}: {pdf_path.name}",
                )
            reader, page_count = open_pdf_reader_checked(pdf_path)
            try:
                for page in reader.pages:
                    pdf_writer.add_page(page)
            except Exception as exc:
                raise PdfMergeError(f"Failed while copying pages from {pdf_path}: {exc}") from exc
            finally:
                close_pdf_reader(reader)
            total_pages += page_count

        write_pdf_writer_atomic(pdf_writer, output)
    finally:
        close = getattr(pdf_writer, "close", None)
        if callable(close):
            try:
                close()
            except Exception:
                pass

    if progress_callback is not None:
        progress_callback(1.0, f"Merged PDF created successfully ({total_pages} pages)")

    return Artifact.create(
        type=DataType.PDF,
        uri=output.resolve().as_uri(),
        produced_by=produced_by,
        mime_type="application/pdf",
        metadata={
            "sourceCount": total_sources,
            "totalPages": total_pages,
        },
    )
