from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from .errors import PDFMergeError

PDF_EXTENSION = ".pdf"


def validate_pdf_path_or_raise(pdf_path: Path) -> Path:
    path = Path(pdf_path)
    if not path.exists():
        raise PDFMergeError(f"O PDF não existe: {path}")
    if path.is_dir():
        raise PDFMergeError(f"O caminho informado é uma pasta, não um PDF: {path}")
    if not path.is_file():
        raise PDFMergeError(f"O caminho informado não é um arquivo PDF: {path}")
    if path.suffix.lower() != PDF_EXTENSION:
        raise PDFMergeError(f"Arquivo inválido ou incompatível: {path}")
    return path


def open_pdf_reader_checked(pdf_path: Path) -> tuple[PdfReader, int]:
    """Open one readable local PDF and fail closed on protected/corrupt input."""
    path = validate_pdf_path_or_raise(pdf_path)
    try:
        reader = PdfReader(str(path), strict=False)
    except FileNotFoundError as exc:
        raise PDFMergeError(f"O PDF '{path.name}' não foi encontrado.") from exc
    except PermissionError as exc:
        raise PDFMergeError(
            f"Não foi possível abrir o PDF '{path.name}'. Verifique permissões de leitura."
        ) from exc
    except Exception as exc:
        raise PDFMergeError(
            f"Não foi possível abrir o PDF '{path.name}'. O arquivo pode estar corrompido ou incompatível."
        ) from exc

    if getattr(reader, "is_encrypted", False):
        try:
            unlocked = reader.decrypt("")
        except Exception as exc:
            raise PDFMergeError(
                f"O PDF '{path.name}' está protegido/criptografado e requer senha."
            ) from exc
        if not unlocked:
            raise PDFMergeError(
                f"O PDF '{path.name}' está protegido/criptografado e requer senha."
            )

    try:
        page_count = len(reader.pages)
    except Exception as exc:
        raise PDFMergeError(
            f"Não foi possível ler as páginas do PDF '{path.name}'. O arquivo pode estar protegido ou corrompido."
        ) from exc
    if page_count <= 0:
        raise PDFMergeError(f"O PDF '{path.name}' não possui páginas legíveis.")
    return reader, page_count
