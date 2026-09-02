from __future__ import annotations

from pathlib import Path
from typing import Sequence

from ktools_core.local_files import path_from_file_uri
from ktools_core.models import Artifact

from . import splitter, writer
from .writer import ProgressCallback


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


def split_text_file_into_parts(
    input_file: str | Path,
    output_dir: str | Path,
    parts: int,
    progress_callback: ProgressCallback | None = None,
) -> list[Path]:
    artifacts = splitter.split_text_file_into_parts(
        Path(input_file),
        Path(output_dir),
        parts,
        progress_callback=progress_callback,
    )
    return [path_from_file_uri(artifact.uri) for artifact in artifacts]
