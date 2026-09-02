from __future__ import annotations

from pathlib import Path
from typing import Callable, Sequence

from pypdf import PdfWriter

from ktools_core.local_files import cleanup_local_path, replace_temp_output, same_local_path, temporary_sibling_path
from ktools_core.models import Artifact, DataType

from .errors import PDFMergeError
from .reader import open_pdf_reader_checked, validate_pdf_path_or_raise

ProgressCallback = Callable[[float, str], None]


def ensure_pdf_extension(path: Path) -> Path:
    output = Path(path)
    return output.with_suffix(".pdf") if output.suffix.lower() != ".pdf" else output


def _normalize_inputs(input_files: Sequence[Path]) -> list[Path]:
    if not input_files:
        raise PDFMergeError("Nenhum PDF foi selecionado.")
    return [validate_pdf_path_or_raise(Path(path)) for path in input_files]


def _ensure_output_not_in_inputs(output: Path, inputs: Sequence[Path]) -> None:
    if any(same_local_path(output, path) for path in inputs):
        raise PDFMergeError(
            "O PDF final não pode ser um dos arquivos de entrada. Escolha outro nome ou outra pasta de saída."
        )


def _write_pdf_writer_atomic(pdf_writer: PdfWriter, output_file: Path) -> None:
    output = Path(output_file)
    temp_path = temporary_sibling_path(output, suffix=".tmp")
    try:
        with temp_path.open("wb") as handle:
            pdf_writer.write(handle)
        replace_temp_output(temp_path, output)
    except Exception:
        cleanup_local_path(temp_path)
        raise


def merge_pdf_files(
    input_files: Sequence[Path],
    output_file: Path,
    progress_callback: ProgressCallback | None = None,
    *,
    produced_by: str | None = None,
) -> Artifact:
    """Merge ordered PDFs and publish the final file only after a complete write."""
    inputs = _normalize_inputs(input_files)
    output = ensure_pdf_extension(Path(output_file))
    output.parent.mkdir(parents=True, exist_ok=True)
    _ensure_output_not_in_inputs(output, inputs)

    pdf_writer = PdfWriter()
    total_pages = 0
    total_sources = len(inputs)
    try:
        for index, pdf_path in enumerate(inputs, start=1):
            if progress_callback is not None:
                progress_callback(
                    (index - 1) / max(total_sources, 1),
                    f"Validando PDF {index} de {total_sources}: {pdf_path.name}",
                )
            reader, page_count = open_pdf_reader_checked(pdf_path)
            for page_number, page in enumerate(reader.pages, start=1):
                try:
                    pdf_writer.add_page(page)
                except Exception as exc:
                    raise PDFMergeError(
                        f"Não foi possível copiar a página {page_number} do PDF '{pdf_path.name}'."
                    ) from exc
            total_pages += page_count

        _write_pdf_writer_atomic(pdf_writer, output)
    except PDFMergeError:
        raise
    except Exception as exc:
        raise PDFMergeError(f"Não foi possível gerar o PDF final: {exc}") from exc
    finally:
        try:
            pdf_writer.close()
        except Exception:
            pass

    if progress_callback is not None:
        progress_callback(1.0, f"PDF final gerado com sucesso ({total_pages} página(s)).")

    return Artifact.create(
        type=DataType.PDF,
        uri=output.resolve().as_uri(),
        produced_by=produced_by,
        mime_type="application/pdf",
        metadata={"sourceCount": total_sources, "totalPages": total_pages},
    )
