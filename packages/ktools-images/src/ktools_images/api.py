from __future__ import annotations

from pathlib import Path
from typing import Sequence

from ktools_core.models import Artifact

from . import converter, pdf_writer
from .converter import ProgressCallback


def convert_webp_to_png(
    input_files: Sequence[Path],
    output_dir: Path,
    progress_callback: ProgressCallback | None = None,
) -> list[Artifact]:
    return converter.convert_webp_files_to_png(
        input_files,
        output_dir,
        progress_callback=progress_callback,
    )


def images_to_pdf(
    input_files: Sequence[Path],
    output_file: Path,
    progress_callback: ProgressCallback | None = None,
) -> Artifact:
    return pdf_writer.images_to_pdf(
        input_files,
        output_file,
        progress_callback=progress_callback,
    )
