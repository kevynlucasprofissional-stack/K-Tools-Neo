from __future__ import annotations

from pathlib import Path
from typing import Callable, Sequence

from ktools_core.models import Artifact


ProgressCallback = Callable[[int, int, str], None]


def read_text_with_fallback(path: Path) -> str:
    raise NotImplementedError("RED: text decoding is not implemented yet")


def merge_text_files(
    input_files: Sequence[Path],
    output_file: Path,
    separator_mode: str = "completo",
    progress_callback: ProgressCallback | None = None,
    *,
    produced_by: str | None = None,
) -> Artifact:
    raise NotImplementedError("RED: text file publication is not implemented yet")
