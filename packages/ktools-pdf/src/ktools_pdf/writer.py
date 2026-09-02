from pathlib import Path
from typing import Callable, Sequence

from ktools_core.models import Artifact


def merge_pdf_files(
    input_files: Sequence[Path],
    output_file: Path,
    progress_callback: Callable[[float, str], None] | None = None,
    *,
    produced_by: str | None = None,
) -> Artifact:
    raise NotImplementedError("RED: PDF merge writer not implemented yet")
