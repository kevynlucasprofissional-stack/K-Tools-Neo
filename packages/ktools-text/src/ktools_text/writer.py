from __future__ import annotations

from pathlib import Path
from typing import Callable, Sequence

from ktools_core.local_files import cleanup_local_path, replace_temp_output, same_local_path, temporary_sibling_path
from ktools_core.models import Artifact, DataType

from .capability import TextDocument, TextMergeError, VALID_SEPARATOR_MODES, render_document_block


ProgressCallback = Callable[[int, int, str], None]
TEXT_EXTENSIONS = frozenset({".md", ".txt"})


def read_text_with_fallback(path: Path) -> str:
    """Preserve the stable legacy decoding order for Windows/Obsidian exports."""
    path = Path(path)
    last_error: UnicodeDecodeError | None = None
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    return path.read_text(encoding="utf-8")


def _normalize_inputs(input_files: Sequence[Path]) -> list[Path]:
    if not input_files:
        raise TextMergeError("Nenhum arquivo .md ou .txt foi selecionado.")

    normalized: list[Path] = []
    for raw_path in input_files:
        path = Path(raw_path)
        if not path.exists():
            raise TextMergeError(f"Arquivo não encontrado: {path}")
        if not path.is_file():
            raise TextMergeError(f"O caminho não é um arquivo: {path}")
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            raise TextMergeError(f"Arquivo inválido ou incompatível: {path}")
        normalized.append(path)
    return normalized


def _normalize_output(output_file: Path) -> Path:
    output = Path(output_file)
    if output.suffix.lower() not in TEXT_EXTENSIONS:
        output = output.with_suffix(".md")
    return output


def _ensure_output_not_in_inputs(output: Path, inputs: Sequence[Path]) -> None:
    if any(same_local_path(output, item) for item in inputs):
        raise TextMergeError(
            "O arquivo final não pode ser um dos arquivos de entrada. "
            "Escolha outro nome ou outra pasta de saída."
        )


def merge_text_files(
    input_files: Sequence[Path],
    output_file: Path,
    separator_mode: str = "completo",
    progress_callback: ProgressCallback | None = None,
    *,
    produced_by: str | None = None,
) -> Artifact:
    """Merge text files with legacy-compatible bytes and atomic final publication."""
    if separator_mode not in VALID_SEPARATOR_MODES:
        raise TextMergeError(
            f"separator_mode must be one of {sorted(VALID_SEPARATOR_MODES)}, got {separator_mode!r}"
        )
    inputs = _normalize_inputs(input_files)
    output = _normalize_output(Path(output_file))
    _ensure_output_not_in_inputs(output, inputs)
    output.parent.mkdir(parents=True, exist_ok=True)

    temp_output = temporary_sibling_path(output)
    total = len(inputs)
    try:
        with temp_output.open("w", encoding="utf-8", newline="\n") as handle:
            for index, path in enumerate(inputs, start=1):
                if progress_callback is not None:
                    progress_callback(
                        index,
                        total,
                        f"Unindo arquivo {index} de {total}: {path.name}",
                    )
                text = read_text_with_fallback(path)
                handle.write(
                    render_document_block(
                        TextDocument(name=path.name, text=text),
                        separator_mode,
                    )
                )
        replace_temp_output(temp_output, output)
    except Exception:
        cleanup_local_path(temp_output)
        raise

    mime_type = "text/markdown" if output.suffix.lower() == ".md" else "text/plain"
    return Artifact.create(
        type=DataType.FILE,
        uri=output.resolve().as_uri(),
        produced_by=produced_by,
        mime_type=mime_type,
        metadata={
            "sourceCount": len(inputs),
            "separatorMode": separator_mode,
            "format": output.suffix.lower().lstrip("."),
        },
    )
