from __future__ import annotations

from pathlib import Path
from typing import Sequence

from ktools_core.models import Artifact

from . import writer
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
