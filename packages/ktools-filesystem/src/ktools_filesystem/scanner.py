from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ktools_core.models import Artifact, DataType
from ktools_core.registry import NodeExecutionContext


class FolderScanError(Exception):
    pass


@dataclass
class FolderScanResult:
    files: list[Artifact]
    report: dict[str, Any]


def scan_files(
    root_path: Path,
    recursive: bool = True,
    include_hidden: bool = False,
    extensions: set[str] | None = None,
    context: NodeExecutionContext | None = None,
) -> FolderScanResult:
    expanded = root_path.expanduser()
    
    # No-follow root reparse/symlink check before resolving
    if expanded.is_symlink() or _is_reparse_point(expanded):
        raise FolderScanError(f"Root path is a symlink or reparse point: {expanded}")
        
    root = expanded.resolve()
    if not root.exists():
        raise FolderScanError(f"Directory does not exist: {root}")
    if not root.is_dir():
        raise FolderScanError(f"Path is not a directory: {root}")

    normalized_extensions = _normalize_extensions(extensions)

    artifacts: list[Artifact] = []
    errors: list[dict[str, Any]] = []

    try:
        _walk_directory(
            current_dir=root,
            root_dir=root,
            recursive=recursive,
            include_hidden=include_hidden,
            extensions=normalized_extensions,
            context=context,
            artifacts=artifacts,
            errors=errors,
        )
    except Exception as e:
        errors.append({"path": str(root), "error": str(e)})

    # Deterministic relative-path ordering
    artifacts.sort(key=lambda a: a.metadata["relativePath"].lower())

    report = {
        "root": str(root),
        "fileCount": len(artifacts),
        "errorCount": len(errors),
        "errors": errors,
    }

    return FolderScanResult(files=artifacts, report=report)


def _normalize_extensions(extensions: set[str] | None) -> set[str] | None:
    if not extensions:
        return None
    normalized = set()
    for ext in extensions:
        ext = ext.strip().lower()
        if not ext.startswith("."):
            ext = f".{ext}"
        normalized.add(ext)
    return normalized


def _is_hidden(name: str) -> bool:
    return name.startswith(".")


def _is_reparse_point(path: Path) -> bool:
    if os.name != "nt":
        return False
    try:
        return path.is_junction()
    except AttributeError:
        return False


def _walk_directory(
    current_dir: Path,
    root_dir: Path,
    recursive: bool,
    include_hidden: bool,
    extensions: set[str] | None,
    context: NodeExecutionContext | None,
    artifacts: list[Artifact],
    errors: list[dict[str, Any]],
) -> None:
    try:
        with os.scandir(current_dir) as it:
            entries = list(it)
    except OSError as e:
        errors.append({"path": str(current_dir), "error": str(e)})
        return

    for entry in entries:
        try:
            if not include_hidden and _is_hidden(entry.name):
                continue
            
            entry_path = Path(entry.path)
            
            if entry.is_symlink() or _is_reparse_point(entry_path):
                continue

            if entry.is_dir():
                if recursive:
                    _walk_directory(
                        current_dir=entry_path,
                        root_dir=root_dir,
                        recursive=recursive,
                        include_hidden=include_hidden,
                        extensions=extensions,
                        context=context,
                        artifacts=artifacts,
                        errors=errors,
                    )
            elif entry.is_file():
                if extensions is not None:
                    ext = entry_path.suffix.lower()
                    if ext not in extensions:
                        continue
                
                rel_path = entry_path.relative_to(root_dir).as_posix()
                metadata = {
                    "name": entry.name,
                    "relativePath": rel_path,
                    "size": entry.stat().st_size,
                }
                
                produced_by = None
                if context:
                    produced_by = f"{context.run_id}/{context.node_id}"

                artifact = Artifact.create(
                    type=DataType.FILE,
                    uri=entry_path.as_uri(),
                    produced_by=produced_by,
                    metadata=metadata,
                )
                artifacts.append(artifact)
        except OSError as e:
            errors.append({"path": entry.path, "error": str(e)})
