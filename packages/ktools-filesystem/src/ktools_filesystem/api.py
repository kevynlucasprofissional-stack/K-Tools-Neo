from __future__ import annotations

from pathlib import Path

from .scanner import FolderScanResult, scan_files


def scan_folder_files(
    root_path: Path | str,
    recursive: bool = True,
    include_hidden: bool = False,
    extensions: set[str] | list[str] | tuple[str, ...] | None = None,
) -> FolderScanResult:
    if isinstance(root_path, str):
        root_path = Path(root_path)
        
    if extensions is not None and not isinstance(extensions, set):
        extensions = set(extensions)
        
    return scan_files(
        root_path=root_path,
        recursive=recursive,
        include_hidden=include_hidden,
        extensions=extensions,
        context=None,
    )
