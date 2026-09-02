from __future__ import annotations

from pathlib import Path
from typing import Callable, Sequence

from ktools_core.models import Artifact

ProgressCallback = Callable[[float, str], None]


def merge_pdf_files(
    input_files: Sequence[Path],
    output_file: Path,
    progress_callback: ProgressCallback | None = None,
    *,
    produced_by: str | None = None,
) -> Artifact:
    raise NotImplementedError("PDF merge characterization RED: writer not implemented yet")
