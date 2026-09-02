from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from ktools_core.models import Artifact
from ktools_pdf import splitter as pdf_splitter
from ktools_text import splitter as text_splitter


ProgressCallback = Callable[[float, str], None]
SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf"}


class DocumentSplitBatchError(ValueError):
    """Classified error for mixed-document split orchestration."""


@dataclass(frozen=True)
class DocumentSplitBatchResult:
    artifacts: tuple[Artifact, ...]
    errors: tuple[str, ...]
    input_count: int
    output_count: int
    output_folder: Path

    def to_report(self) -> dict[str, object]:
        return {
            "inputCount": self.input_count,
            "outputCount": self.output_count,
            "errorCount": len(self.errors),
            "errors": list(self.errors),
            "outputFolder": str(self.output_folder.resolve()),
        }

    @property
    def report(self) -> dict[str, object]:
        return self.to_report()


def _compatible_files(input_files: Sequence[Path]) -> list[Path]:
    compatible: list[Path] = []
    for raw_path in input_files:
        path = Path(raw_path).expanduser()
        try:
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
                compatible.append(path)
        except OSError:
            continue
    return compatible


def _validate_parts(parts: int) -> int:
    if isinstance(parts, bool) or not isinstance(parts, int):
        raise DocumentSplitBatchError("document split parts must be an integer >= 2")
    if parts < 2:
        raise DocumentSplitBatchError("document split parts must be at least 2")
    return parts


def _prepare_output_dir(output_dir: Path) -> Path:
    destination = Path(output_dir).expanduser()
    try:
        destination.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise DocumentSplitBatchError(
            f"Could not create document split output directory {destination}: {exc}"
        ) from exc
    if not destination.is_dir():
        raise DocumentSplitBatchError(
            f"Document split output path is not a directory: {destination}"
        )
    return destination


def split_documents_into_parts(
    input_files: Sequence[Path],
    output_dir: Path,
    parts: int,
    progress_callback: ProgressCallback | None = None,
    *,
    produced_by: str | None = None,
) -> DocumentSplitBatchResult:
    files = _compatible_files(input_files)
    if not files:
        raise DocumentSplitBatchError(
            "No compatible documents were selected; expected existing .md, .txt or .pdf files"
        )
    requested_parts = _validate_parts(parts)
    destination = _prepare_output_dir(output_dir)

    artifacts: list[Artifact] = []
    errors: list[str] = []
    total_files = len(files)

    for file_index, source in enumerate(files):
        base_progress = file_index / total_files
        span = 1.0 / total_files

        def emit_local(local_value: float, message: str, *, base: float = base_progress, width: float = span) -> None:
            if progress_callback is None:
                return
            clamped = max(0.0, min(1.0, float(local_value)))
            progress_callback(min(1.0, base + clamped * width), message)

        try:
            suffix = source.suffix.lower()
            if suffix == ".pdf":
                child_outputs = pdf_splitter.split_pdf_into_parts(
                    source,
                    destination,
                    requested_parts,
                    lambda value, message: emit_local(value, message),
                    produced_by=produced_by,
                )
            else:
                child_outputs = text_splitter.split_text_file_into_parts(
                    source,
                    destination,
                    requested_parts,
                    lambda index, total, message: emit_local(
                        (float(index) / float(total)) if total else 1.0,
                        message,
                    ),
                    produced_by=produced_by,
                )
            artifacts.extend(child_outputs)
        except Exception as exc:
            errors.append(f"{source.name}: {exc}")

    if not artifacts:
        details = "\n".join(errors[:5]) if errors else "No parts were produced"
        raise DocumentSplitBatchError(f"Could not split the selected documents.\n\n{details}")

    if progress_callback is not None:
        progress_callback(1.0, f"Document split complete: {len(artifacts)} output file(s)")

    return DocumentSplitBatchResult(
        artifacts=tuple(artifacts),
        errors=tuple(errors),
        input_count=total_files,
        output_count=len(artifacts),
        output_folder=destination,
    )
