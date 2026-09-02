from pathlib import Path
from typing import Callable, Sequence

from ktools_core.models import Artifact

from . import writer


def merge_pdf_files(
    input_files: Sequence[Path],
    output_file: Path,
    progress_callback: Callable[[float, str], None] | None = None,
) -> Artifact:
    return writer.merge_pdf_files(input_files, output_file, progress_callback)
