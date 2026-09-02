from __future__ import annotations

from pathlib import Path
from typing import Sequence

from . import batch
from .batch import DocumentSplitBatchResult, ProgressCallback


def split_document_files_into_parts(
    input_files: Sequence[Path],
    output_dir: Path,
    parts: int,
    progress_callback: ProgressCallback | None = None,
) -> DocumentSplitBatchResult:
    return batch.split_documents_into_parts(
        input_files,
        output_dir,
        parts,
        progress_callback=progress_callback,
    )
