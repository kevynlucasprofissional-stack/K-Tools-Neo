from __future__ import annotations

from pathlib import Path
from typing import Sequence

from ktools_core.local_files import path_from_file_uri
from ktools_core.models import Artifact

from . import splitter, writer
from .writer import ProgressCallback


def merge_pdf_files(
    input_files: Sequence[Path],
    output_file: Path,
    progress_callback: ProgressCallback | None = None,
    *,
    produced_by: str | None = None,
) -> Artifact:
    return writer.merge_pdf_files(
        input_files,
        output_file,
        progress_callback=progress_callback,
        produced_by=produced_by,
    )


def split_pdf_into_parts(
    input_pdf: Path,
    output_dir: Path,
    parts: int,
    progress_callback: ProgressCallback | None = None,
) -> list[Path]:
    artifacts = splitter.split_pdf_into_parts(
        input_pdf,
        output_dir,
        parts,
        progress_callback=progress_callback,
    )
    return [path_from_file_uri(artifact.uri) for artifact in artifacts]
