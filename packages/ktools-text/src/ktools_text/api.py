from __future__ import annotations

from pathlib import Path
from typing import Sequence

from ktools_core.models import Artifact

from . import writer


def merge_text_files(
    input_files: Sequence[str | Path],
    output_file: str | Path,
    separator_mode: str = "completo",
) -> Artifact:
    return writer.merge_text_files(
        [Path(path) for path in input_files],
        Path(output_file),
        separator_mode,
    )
