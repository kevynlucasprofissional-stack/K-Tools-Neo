from __future__ import annotations

from pathlib import Path
from typing import Sequence

from ktools_core.models import Artifact

from . import writer


def merge_pdf_files(
    input_files: Sequence[Path],
    output_file: Path,
    *,
    produced_by: str | None = None,
) -> Artifact:
    return writer.merge_pdf_files(
        input_files,
        output_file,
        produced_by=produced_by,
    )
